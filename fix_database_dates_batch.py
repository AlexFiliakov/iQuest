#!/usr/bin/env python3
"""Batch fix for existing date formats in the Apple Health Monitor database.

This script fixes the date format issue where XML imports stored dates with 
timezone information, making them incompatible with SQLite's DATE() function.
"""

import sqlite3
import os
from pathlib import Path
import sys
import time

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_data_directory, DB_FILE_NAME


def fix_database_dates_batch():
    """Fix existing dates in the database using batch updates."""
    # Get database path
    data_dir = get_data_directory()
    db_path = Path(data_dir) / DB_FILE_NAME
    
    if not db_path.exists():
        print(f"ERROR: Database does not exist at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("Fixing date formats in existing database...")
    
    try:
        # Enable WAL mode for better performance
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # First, check how many records need fixing
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE startDate LIKE '% -%' OR startDate LIKE '% +%'
        """)
        total_count = cursor.fetchone()[0]
        print(f"Found {total_count} records with timezone information to fix")
        
        if total_count == 0:
            print("No records need fixing!")
            return
        
        # Create indexes if they don't exist to speed up the update
        print("Creating temporary index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_temp_startdate_tz 
            ON health_records(startDate) 
            WHERE startDate LIKE '% -%' OR startDate LIKE '% +%'
        """)
        
        # Process in batches
        batch_size = 10000
        processed = 0
        start_time = time.time()
        
        print(f"Processing {total_count} records in batches of {batch_size}...")
        
        while processed < total_count:
            # Update a batch of records
            cursor.execute("""
                UPDATE health_records
                SET startDate = substr(startDate, 1, 19),
                    endDate = substr(endDate, 1, 19),
                    creationDate = substr(creationDate, 1, 19)
                WHERE rowid IN (
                    SELECT rowid FROM health_records
                    WHERE startDate LIKE '% -%' OR startDate LIKE '% +%'
                    LIMIT ?
                )
            """, (batch_size,))
            
            batch_updated = cursor.rowcount
            processed += batch_updated
            
            # Commit after each batch
            conn.commit()
            
            # Progress update
            progress = (processed / total_count) * 100
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total_count - processed) / rate if rate > 0 else 0
            
            print(f"Progress: {processed:,}/{total_count:,} ({progress:.1f}%) - "
                  f"Rate: {rate:.0f} records/sec - ETA: {eta:.0f}s", end='\r')
            
            if batch_updated == 0:
                break
        
        print(f"\nUpdated {processed} records in {time.time() - start_time:.1f} seconds")
        
        # Drop temporary index
        print("Cleaning up temporary index...")
        cursor.execute("DROP INDEX IF EXISTS idx_temp_startdate_tz")
        
        # Verify the fix
        cursor.execute("""
            SELECT startDate, DATE(startDate) as date_result
            FROM health_records
            LIMIT 5
        """)
        
        print("\nVerifying date conversion:")
        for row in cursor.fetchall():
            print(f"  startDate: {row[0]!r}, DATE(): {row[1]!r}")
        
        # Test a query like the Daily tab uses
        test_date = '2025-05-24'
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE DATE(startDate) = ?
        """, (test_date,))
        
        count = cursor.fetchone()[0]
        print(f"\nTest query for {test_date}: Found {count} records")
        
        # Vacuum to optimize database
        print("\nOptimizing database...")
        cursor.execute("VACUUM")
        
        print("\nDatabase dates fixed successfully!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Apple Health Monitor - Batch Date Format Fix")
    print("=" * 80)
    
    response = input("This will update all dates in your database. Continue? (y/n): ")
    if response.lower() == 'y':
        fix_database_dates_batch()
    else:
        print("Operation cancelled.")