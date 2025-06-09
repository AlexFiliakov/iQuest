#!/usr/bin/env python3
"""Debug script to trace database operations in portable mode."""

import os
import sys
import sqlite3
from pathlib import Path

# Monkey patch to trace database connections
original_connect = sqlite3.connect

def traced_connect(database, **kwargs):
    """Traced version of sqlite3.connect to log all database connections."""
    print(f"\n=== SQLITE3.CONNECT CALLED ===")
    print(f"Database path: {database}")
    print(f"Absolute path: {os.path.abspath(database)}")
    print(f"Path exists: {os.path.exists(database)}")
    
    if os.path.exists(database):
        size = os.path.getsize(database)
        print(f"File size: {size:,} bytes")
        
        # Try to get record count
        try:
            conn = original_connect(database, **kwargs)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM health_records")
            count = cursor.fetchone()[0]
            print(f"Health records in this DB: {count:,}")
            conn.close()
        except Exception as e:
            print(f"Error checking record count: {e}")
    
    print("==============================\n")
    
    return original_connect(database, **kwargs)

sqlite3.connect = traced_connect

# Now import the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from config import is_portable_mode, get_data_directory, DATA_DIR
from database import DatabaseManager
from ui.main_window import MainWindow

def main():
    print("=== PORTABLE MODE DATABASE DEBUG ===")
    print(f"Running from: {os.path.abspath(__file__)}")
    print(f"Current directory: {os.getcwd()}")
    
    if getattr(sys, 'frozen', False):
        print(f"FROZEN executable: {sys.executable}")
        app_dir = os.path.dirname(sys.executable)
    else:
        print("Running from SOURCE")
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"App directory: {app_dir}")
    print(f"Portable mode: {is_portable_mode()}")
    print(f"Data directory: {get_data_directory()}")
    print(f"DATA_DIR: {DATA_DIR}")
    
    # Check for databases in various locations
    print("\n=== Checking for existing databases ===")
    locations = [
        ("App dir", app_dir),
        ("Data dir", DATA_DIR),
        ("App/data", os.path.join(app_dir, 'data')),
    ]
    
    for name, directory in locations:
        db_path = os.path.join(directory, 'health_monitor.db')
        print(f"\n{name}: {db_path}")
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"  EXISTS - Size: {size:,} bytes")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_records")
                count = cursor.fetchone()[0]
                print(f"  Health records: {count:,}")
                conn.close()
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("  NOT FOUND")
    
    print("\n=== Starting application (this will trace all DB connections) ===")
    
    app = QApplication(sys.argv)
    
    # Create the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()