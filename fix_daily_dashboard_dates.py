#!/usr/bin/env python3
"""Fix for Daily Dashboard date issue in portable EXE.

The issue: Dates in the database still have timezone information which causes
SQLite's DATE() function to shift dates when converting to UTC.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_data_directory, DB_FILE_NAME

def fix_daily_dashboard_dates():
    """Fix dates by removing timezone information from all date columns."""
    # Get database path
    data_dir = get_data_directory()
    db_path = Path(data_dir) / DB_FILE_NAME
    
    if not db_path.exists():
        print(f"ERROR: Database does not exist at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("Fixing Daily Dashboard Date Issue")
    print("=" * 80)
    
    try:
        # First, check how many records need fixing
        print("\n1. Checking for dates with timezone information...")
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE LENGTH(startDate) > 19
        """)
        count = cursor.fetchone()[0]
        print(f"Found {count} records with timezone information")
        
        if count == 0:
            print("No records need fixing!")
            return
        
        # Create backup table
        print("\n2. Creating backup table...")
        cursor.execute("DROP TABLE IF EXISTS health_records_date_backup")
        cursor.execute("""
            CREATE TABLE health_records_date_backup AS 
            SELECT * FROM health_records
        """)
        print("Backup created")
        
        # Fix dates by removing timezone information
        print("\n3. Fixing date formats...")
        
        # For dates with timezone, extract just the datetime part before timezone
        cursor.execute("""
            UPDATE health_records
            SET startDate = SUBSTR(startDate, 1, 19),
                endDate = SUBSTR(endDate, 1, 19),
                creationDate = SUBSTR(creationDate, 1, 19)
            WHERE LENGTH(startDate) > 19 OR LENGTH(endDate) > 19 OR LENGTH(creationDate) > 19
        """)
        
        rows_updated = cursor.rowcount
        print(f"Updated {rows_updated} records")
        
        # Verify the fix
        print("\n4. Verifying fix...")
        cursor.execute("""
            SELECT startDate, DATE(startDate) as date_result
            FROM health_records
            WHERE type LIKE '%StepCount%'
            ORDER BY startDate DESC
            LIMIT 5
        """)
        
        print("Sample records after fix:")
        for row in cursor.fetchall():
            print(f"  startDate: {row[0]!r}, DATE(): {row[1]!r}")
        
        # Test a specific date query
        test_date = '2025-04-21'
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE type LIKE '%StepCount%'
            AND DATE(startDate) = ?
        """, (test_date,))
        
        count = cursor.fetchone()[0]
        print(f"\nTest query for {test_date}: Found {count} records")
        
        conn.commit()
        print("\nDate issue fixed successfully!")
        print("The Daily tab should now show data correctly.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("This script will fix the Daily Dashboard date issue.")
    print("It will create a backup table before making changes.")
    response = input("\nDo you want to proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        fix_daily_dashboard_dates()
    else:
        print("Operation cancelled.")