#!/usr/bin/env python3
"""Fix for XML date format issue in Apple Health Monitor.

This script demonstrates two approaches:
1. A patch for the XML streaming processor to store dates in SQLite-compatible format
2. A database migration to fix existing data

The issue: XML import stores dates with timezone (e.g., '2025-05-24 20:38:08 -0400')
which causes SQLite's DATE() function to return NULL, breaking the Daily tab queries.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_data_directory, DB_FILE_NAME


def fix_database_dates():
    """Fix existing dates in the database by converting to SQLite-compatible format."""
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
        # First, let's check how many records need fixing
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE startDate LIKE '% -%' OR startDate LIKE '% +%'
        """)
        count = cursor.fetchone()[0]
        print(f"Found {count} records with timezone information to fix")
        
        if count == 0:
            print("No records need fixing!")
            return
        
        # Create backup of original data
        print("Creating backup table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_records_backup AS 
            SELECT * FROM health_records
        """)
        
        # Fix dates by using SQLite's datetime function to parse and reformat
        print("Converting date formats...")
        cursor.execute("""
            UPDATE health_records
            SET startDate = datetime(substr(startDate, 1, 19)),
                endDate = datetime(substr(endDate, 1, 19)),
                creationDate = datetime(substr(creationDate, 1, 19))
            WHERE startDate LIKE '% -%' OR startDate LIKE '% +%'
        """)
        
        rows_updated = cursor.rowcount
        print(f"Updated {rows_updated} records")
        
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
        
        conn.commit()
        print("\nDatabase dates fixed successfully!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def create_xml_processor_patch():
    """Create a patched version of the XML processor that handles dates correctly."""
    patch_content = '''
# Patch for xml_streaming_processor.py
# Add this method to the AppleHealthHandler class:

def _parse_date(self, date_str: str) -> str:
    """Parse Apple Health date format and convert to SQLite-compatible format.
    
    Apple Health exports dates with timezone like: '2025-05-24 20:38:08 -0400'
    SQLite DATE() function needs: '2025-05-24 20:38:08'
    
    Args:
        date_str: Date string from Apple Health XML
        
    Returns:
        Date string without timezone offset
    """
    if not date_str:
        return date_str
    
    # Remove timezone offset if present
    if ' -' in date_str or ' +' in date_str:
        # Find the last space which precedes the timezone
        parts = date_str.rsplit(' ', 1)
        if len(parts) == 2:
            return parts[0]
    
    return date_str

# Then modify the _clean_record method to use it:
# Change these lines:
    'creationDate': record.get('creationDate', ''),
    'startDate': record.get('startDate', ''),
    'endDate': record.get('endDate', ''),

# To:
    'creationDate': self._parse_date(record.get('creationDate', '')),
    'startDate': self._parse_date(record.get('startDate', '')),
    'endDate': self._parse_date(record.get('endDate', '')),
'''
    
    print("XML Processor Patch:")
    print("=" * 80)
    print(patch_content)
    print("=" * 80)
    
    # Save patch to file
    patch_file = "xml_date_format_patch.txt"
    with open(patch_file, 'w') as f:
        f.write(patch_content)
    print(f"\nPatch saved to: {patch_file}")


if __name__ == "__main__":
    print("Apple Health Monitor - Date Format Fix")
    print("=" * 80)
    
    # Show the patch for the XML processor
    create_xml_processor_patch()
    
    print("\nWould you like to:")
    print("1. Fix existing database dates")
    print("2. Show patch only (already shown above)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\nFixing database dates...")
        fix_database_dates()
    elif choice == "2":
        print("\nPatch already shown above.")
    else:
        print("\nExiting...")