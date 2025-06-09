#!/usr/bin/env python3
"""Diagnostic script to check database path in portable mode."""

import os
import sys
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import is_portable_mode, get_data_directory, DATA_DIR, DB_FILE_NAME
from database import DatabaseManager

def test_portable_db_path():
    """Test database path configuration in portable mode."""
    print("=== Portable Mode Database Path Test ===")
    print(f"Script location: {os.path.abspath(__file__)}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if running as frozen executable
    if getattr(sys, 'frozen', False):
        print(f"Running as FROZEN EXECUTABLE")
        print(f"sys.executable: {sys.executable}")
        print(f"Executable directory: {os.path.dirname(sys.executable)}")
    else:
        print("Running from SOURCE")
    
    # Check portable mode detection
    print(f"\nis_portable_mode(): {is_portable_mode()}")
    
    # Check for portable marker
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    portable_marker = os.path.join(app_dir, 'portable.marker')
    print(f"Portable marker path: {portable_marker}")
    print(f"Portable marker exists: {os.path.exists(portable_marker)}")
    
    # Check data directory
    print(f"\nget_data_directory(): {get_data_directory()}")
    print(f"DATA_DIR from config: {DATA_DIR}")
    
    # Check database manager path
    db = DatabaseManager()
    print(f"\nDatabaseManager db_path: {db.db_path}")
    print(f"Database file exists: {db.db_path.exists()}")
    
    if db.db_path.exists():
        print(f"Database size: {db.db_path.stat().st_size:,} bytes")
        
        # Check record count
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_records")
                count = cursor.fetchone()[0]
                print(f"Health records count: {count:,}")
        except Exception as e:
            print(f"Error querying database: {e}")
    
    # List files in data directory
    data_dir = get_data_directory()
    print(f"\nFiles in data directory ({data_dir}):")
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  - {file} ({size:,} bytes)")
    else:
        print("  Data directory does not exist!")
    
    # Check all possible database locations
    print("\n=== Checking possible database locations ===")
    locations = [
        ("App dir", os.path.join(app_dir, DB_FILE_NAME)),
        ("App dir/data", os.path.join(app_dir, 'data', DB_FILE_NAME)),
        ("DATA_DIR", os.path.join(DATA_DIR, DB_FILE_NAME)),
        ("Current dir", os.path.join(os.getcwd(), DB_FILE_NAME)),
        ("Current dir/data", os.path.join(os.getcwd(), 'data', DB_FILE_NAME)),
    ]
    
    for name, path in locations:
        exists = os.path.exists(path)
        print(f"{name}: {path}")
        print(f"  Exists: {exists}")
        if exists:
            size = os.path.getsize(path)
            print(f"  Size: {size:,} bytes")
            # Try to count records
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_records")
                count = cursor.fetchone()[0]
                print(f"  Health records: {count:,}")
                conn.close()
            except Exception as e:
                print(f"  Error reading: {e}")

if __name__ == "__main__":
    test_portable_db_path()