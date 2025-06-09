#!/usr/bin/env python3
"""Test script to verify portable mode database path."""

import os
import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import is_portable_mode, get_data_directory, DATA_DIR, DB_FILE_NAME
from database import DatabaseManager

def test_portable_mode():
    """Test portable mode detection and database path configuration."""
    print("=== Portable Mode Test ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    
    if getattr(sys, 'frozen', False):
        print(f"Running as executable from: {sys.executable}")
        app_dir = os.path.dirname(sys.executable)
    else:
        print("Running from source")
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Application directory: {app_dir}")
    
    # Check for portable marker
    portable_marker = os.path.join(app_dir, 'portable.marker')
    print(f"\nChecking for portable marker at: {portable_marker}")
    print(f"Portable marker exists: {os.path.exists(portable_marker)}")
    
    # Test portable mode detection
    print(f"\nis_portable_mode(): {is_portable_mode()}")
    print(f"get_data_directory(): {get_data_directory()}")
    print(f"DATA_DIR: {DATA_DIR}")
    
    # Test database path
    db_manager = DatabaseManager()
    print(f"\nDatabaseManager db_path: {db_manager.db_path}")
    print(f"Database file exists: {db_manager.db_path.exists()}")
    
    # Expected paths
    if is_portable_mode():
        expected_data_dir = os.path.join(app_dir, 'data')
        expected_db_path = os.path.join(expected_data_dir, DB_FILE_NAME)
        print(f"\nExpected data directory: {expected_data_dir}")
        print(f"Expected database path: {expected_db_path}")
        print(f"Paths match: {str(db_manager.db_path) == expected_db_path}")
    
    # Test database access
    print("\n=== Testing Database Access ===")
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables in database: {[t[0] for t in tables]}")
            
            # Try to query health_records
            cursor.execute("SELECT COUNT(*) FROM health_records")
            count = cursor.fetchone()[0]
            print(f"Health records count: {count}")
            
        print("Database access successful!")
        
    except Exception as e:
        print(f"Database access failed: {e}")
    
    # Test creating portable marker if not exists
    if not os.path.exists(portable_marker) and input("\nCreate portable.marker for testing? (y/n): ").lower() == 'y':
        Path(portable_marker).touch()
        print(f"Created portable marker at: {portable_marker}")
        print("Please restart the script to test portable mode.")

if __name__ == "__main__":
    test_portable_mode()