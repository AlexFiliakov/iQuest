#!/usr/bin/env python3
"""Verify portable mode fix and check database files."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Check portable mode configuration and database files."""
    
    print("=== Portable Mode Verification ===\n")
    
    # Import config after adding src to path
    import config
    
    print(f"1. Configuration:")
    print(f"   - Portable mode: {config.is_portable_mode()}")
    print(f"   - Data directory: {config.DATA_DIR}")
    print(f"   - DB filename constant: {config.DB_FILE_NAME}")
    
    # Check what database files exist
    print(f"\n2. Database Files in Data Directory:")
    data_dir = Path(config.DATA_DIR)
    if data_dir.exists():
        db_files = list(data_dir.glob("*.db"))
        if db_files:
            for db_file in db_files:
                size = db_file.stat().st_size
                print(f"   - {db_file.name}: {size:,} bytes")
        else:
            print("   - No .db files found")
    else:
        print(f"   - Data directory does not exist: {data_dir}")
    
    # Check portable marker
    print(f"\n3. Portable Marker:")
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    marker_path = Path(app_dir) / "portable.marker"
    print(f"   - Marker path: {marker_path}")
    print(f"   - Marker exists: {marker_path.exists()}")
    
    # Check database module
    print(f"\n4. Database Manager:")
    from database import DatabaseManager, DB_FILE_NAME as db_module_filename
    db = DatabaseManager()
    print(f"   - Module DB_FILE_NAME: {db_module_filename}")
    print(f"   - Database path: {db.db_path}")
    print(f"   - Database exists: {db.db_path.exists()}")
    
    # Try to get some stats
    if db.db_path.exists():
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM health_records")
                count = cursor.fetchone()[0]
                print(f"   - Health records count: {count}")
        except Exception as e:
            print(f"   - Error querying database: {e}")
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()