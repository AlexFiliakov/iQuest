#!/usr/bin/env python3
"""Test script to verify data access in portable mode."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_portable_data_access():
    """Test that data can be accessed in portable mode."""
    
    print("=== Testing Portable Mode Data Access ===\n")
    
    # Import necessary modules
    import config
    import data_access
    from database import DatabaseManager
    
    print(f"1. Configuration:")
    print(f"   - Portable mode: {config.is_portable_mode()}")
    print(f"   - Data directory: {config.DATA_DIR}")
    print(f"   - DB file: {config.DB_FILE_NAME}")
    
    # Test database connection
    print(f"\n2. Database Connection:")
    db = DatabaseManager()
    print(f"   - Database path: {db.db_path}")
    print(f"   - Database exists: {db.db_path.exists()}")
    
    # Test data access
    print(f"\n3. Data Access:")
    da = data_access.DataAccess()
    
    # Get database stats
    stats = da.get_database_stats()
    print(f"   - Health records count: {stats.get('health_records_count', 0)}")
    print(f"   - Date range: {stats.get('date_range', 'N/A')}")
    print(f"   - Total data sources: {stats.get('total_sources', 0)}")
    
    # Get available metrics
    print(f"\n4. Available Metrics:")
    from health_database import HealthDatabase
    try:
        health_db = HealthDatabase()
        types = health_db.get_available_types()
        print(f"   - Total metric types: {len(types)}")
        if types:
            print(f"   - First 5 types: {types[:5]}")
    except Exception as e:
        print(f"   - Error accessing health database: {e}")
    
    # Test getting some actual data
    print(f"\n5. Sample Data Query:")
    try:
        # Query for recent records
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT type, COUNT(*) as count, 
                       MIN(creationDate) as min_date, 
                       MAX(creationDate) as max_date
                FROM health_records
                GROUP BY type
                LIMIT 5
            """)
            results = cursor.fetchall()
            
            if results:
                print("   - Sample metrics:")
                for row in results:
                    print(f"     * {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
            else:
                print("   - No data found in database")
                
    except Exception as e:
        print(f"   - Error querying database: {e}")
    
    # Check if database has any data
    print(f"\n6. Database Content Check:")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   - Tables in database: {[t[0] for t in tables]}")
            
            # Check row counts for main tables
            for table_name in ['health_records', 'journal_entries', 'user_preferences']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table_name}: {count} rows")
                except:
                    print(f"   - {table_name}: table not found or error")
                    
    except Exception as e:
        print(f"   - Error checking database content: {e}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_portable_data_access()