#!/usr/bin/env python3
"""Fix script to ensure portable mode uses consistent database paths."""

import os
import sys
import shutil
from pathlib import Path

def fix_portable_db_path():
    """Ensure portable mode database is in the correct location."""
    
    print("=== Fixing Portable Mode Database Path ===")
    
    # Determine application directory
    if getattr(sys, 'frozen', False):
        # Running as executable
        app_dir = os.path.dirname(sys.executable)
        print(f"Frozen executable directory: {app_dir}")
    else:
        # Running from source
        app_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Source directory: {app_dir}")
    
    # Check for portable marker
    portable_marker = os.path.join(app_dir, 'portable.marker')
    if not os.path.exists(portable_marker):
        print("Not in portable mode (no portable.marker found)")
        return
    
    print("Portable mode detected!")
    
    # Expected database location in portable mode
    data_dir = os.path.join(app_dir, 'data')
    expected_db = os.path.join(data_dir, 'health_monitor.db')
    
    print(f"\nExpected database location: {expected_db}")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    print(f"Data directory exists: {os.path.exists(data_dir)}")
    
    # Check various possible database locations
    possible_locations = [
        os.path.join(app_dir, 'health_monitor.db'),  # Root directory
        os.path.join(os.getcwd(), 'health_monitor.db'),  # Current directory
        os.path.join(os.getcwd(), 'data', 'health_monitor.db'),  # Current/data
    ]
    
    # Look for existing database files
    found_db = None
    for location in possible_locations:
        if os.path.exists(location) and location != expected_db:
            size = os.path.getsize(location)
            print(f"\nFound database at: {location}")
            print(f"Size: {size:,} bytes")
            
            if size > 0 and (found_db is None or size > os.path.getsize(found_db)):
                found_db = location
    
    # If we found a database in the wrong location, move it
    if found_db and found_db != expected_db:
        print(f"\nMoving database from {found_db} to {expected_db}")
        
        # If target exists, back it up first
        if os.path.exists(expected_db):
            backup_path = expected_db + '.backup'
            print(f"Backing up existing database to {backup_path}")
            shutil.copy2(expected_db, backup_path)
        
        # Move the database
        shutil.move(found_db, expected_db)
        print("Database moved successfully!")
    
    # Verify final state
    if os.path.exists(expected_db):
        size = os.path.getsize(expected_db)
        print(f"\nDatabase is now at: {expected_db}")
        print(f"Size: {size:,} bytes")
        
        # Try to check record count
        try:
            import sqlite3
            conn = sqlite3.connect(expected_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM health_records")
            count = cursor.fetchone()[0]
            print(f"Health records: {count:,}")
            conn.close()
        except Exception as e:
            print(f"Error checking records: {e}")
    else:
        print("\nNo database found to move")

if __name__ == "__main__":
    fix_portable_db_path()