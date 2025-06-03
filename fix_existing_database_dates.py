#!/usr/bin/env python3
"""
Fix existing database dates by removing timezone information.

This script updates all date fields in the health_records table to remove
timezone offsets, making them compatible with SQLite's DATE() function.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def get_database_path():
    """Get the database path from the config."""
    # This matches the logic in config.py
    current_path = os.path.abspath(os.path.dirname(__file__))
    
    # Detect if we're in WSL accessing Windows filesystem
    if current_path.startswith('/mnt/c/') or current_path.startswith('/mnt/d/'):
        # Running in WSL but on Windows filesystem
        drive_letter = current_path[5]  # Get drive letter from /mnt/X/
        windows_user_path = current_path.split('Users/')[1].split('/')[0] if 'Users/' in current_path else None
        
        if windows_user_path:
            # Construct Windows AppData path
            windows_appdata_path = f"/mnt/{drive_letter}/Users/{windows_user_path}/AppData/Local/AppleHealthMonitor"
            return os.path.join(windows_appdata_path, "health_monitor.db")
    
    # Default path
    return os.path.join(os.path.expanduser("~"), ".local", "share", "AppleHealthMonitor", "health_monitor.db")

def strip_timezone(date_str):
    """Remove timezone offset from date string."""
    if not date_str:
        return date_str
    
    # Remove timezone offset if present
    if ' -' in date_str or ' +' in date_str:
        # Find the last space which precedes the timezone
        parts = date_str.rsplit(' ', 1)
        if len(parts) == 2:
            return parts[0]
    
    return date_str

def fix_database_dates():
    """Fix all date fields in the database."""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Fixing dates in database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, check how many records have timezone offsets
        print("\nChecking for dates with timezone offsets...")
        
        date_fields = ['creationDate', 'startDate', 'endDate']
        
        for field in date_fields:
            cursor.execute(f"""
                SELECT COUNT(*) FROM health_records 
                WHERE {field} LIKE '% -%' OR {field} LIKE '% +%'
            """)
            count = cursor.fetchone()[0]
            print(f"  {field}: {count:,} records with timezone")
        
        # Get total record count
        cursor.execute("SELECT COUNT(*) FROM health_records")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal records: {total_count:,}")
        
        # Ask for confirmation
        response = input("\nDo you want to fix these dates? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Begin transaction
        print("\nFixing dates...")
        conn.execute('BEGIN TRANSACTION')
        
        # Process each date field
        for field in date_fields:
            print(f"\nProcessing {field}...")
            
            # Get all unique date values with timezone
            cursor.execute(f"""
                SELECT DISTINCT {field} FROM health_records 
                WHERE {field} LIKE '% -%' OR {field} LIKE '% +%'
            """)
            
            dates_to_fix = cursor.fetchall()
            print(f"  Found {len(dates_to_fix)} unique date values to fix")
            
            # Update each unique date value
            fixed_count = 0
            for (date_value,) in dates_to_fix:
                if date_value:
                    fixed_date = strip_timezone(date_value)
                    cursor.execute(f"""
                        UPDATE health_records 
                        SET {field} = ? 
                        WHERE {field} = ?
                    """, (fixed_date, date_value))
                    
                    fixed_count += cursor.rowcount
                    
                    if fixed_count % 1000 == 0:
                        print(f"    Fixed {fixed_count:,} records...")
            
            print(f"  Fixed {fixed_count:,} records in {field}")
        
        # Commit the transaction
        conn.commit()
        print("\nDatabase update completed successfully!")
        
        # Verify the fix
        print("\nVerifying fix...")
        for field in date_fields:
            cursor.execute(f"""
                SELECT COUNT(*) FROM health_records 
                WHERE {field} LIKE '% -%' OR {field} LIKE '% +%'
            """)
            count = cursor.fetchone()[0]
            print(f"  {field}: {count} records with timezone (should be 0)")
        
        # Test DATE() function
        print("\nTesting DATE() function...")
        cursor.execute("""
            SELECT COUNT(*) FROM health_records 
            WHERE DATE(startDate) IS NOT NULL
        """)
        valid_dates = cursor.fetchone()[0]
        print(f"  Records with valid DATE(startDate): {valid_dates:,} out of {total_count:,}")
        
        conn.close()
        
        print("\nDates fixed! The Daily tab should now work properly.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_database_dates()