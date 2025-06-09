#\!/usr/bin/env python3
"""Create portable.marker file to enable portable mode."""

import os
from pathlib import Path

def main():
    """Create portable marker file."""
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Create portable.marker file
    marker_path = script_dir / "portable.marker"
    
    print(f"Creating portable marker at: {marker_path}")
    
    # Create the file
    marker_path.touch()
    
    print("✅ Portable marker created\!")
    print("\nNow when you run the app, it will use portable mode:")
    print("- Data will be stored in ./data/")
    print("- Database will be ./data/health_monitor.db")
    
    # Check if data directory exists
    data_dir = script_dir / "data"
    if data_dir.exists():
        print(f"\n📁 Data directory already exists: {data_dir}")
        
        # Check for database file
        db_file = data_dir / "health_monitor.db"
        if db_file.exists():
            print(f"✅ Database file found: {db_file} ({db_file.stat().st_size:,} bytes)")
        else:
            print("❌ No database file found yet")
    else:
        print(f"\n📁 Data directory will be created at: {data_dir}")

if __name__ == "__main__":
    main()
EOF < /dev/null
