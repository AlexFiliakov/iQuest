#!/usr/bin/env python3
"""Check what sources are available in the database."""

import sys
sys.path.insert(0, 'src')

from src.health_database import HealthDatabase
from src.database import DatabaseManager

# Create database connections
health_db = HealthDatabase()
db_manager = DatabaseManager()

print("Checking database for sources...\n")

# Check if health_records table exists
check_table = "SELECT name FROM sqlite_master WHERE type='table' AND name='health_records'"
tables = db_manager.execute_query(check_table)
print(f"health_records table exists: {bool(tables)}")

if tables:
    # Count total records
    count_query = "SELECT COUNT(*) FROM health_records"
    count_result = db_manager.execute_query(count_query)
    print(f"Total records: {count_result[0][0] if count_result else 0}")
    
    # Get unique sources
    sources_query = "SELECT DISTINCT sourceName FROM health_records WHERE sourceName IS NOT NULL ORDER BY sourceName"
    sources = db_manager.execute_query(sources_query)
    print(f"\nUnique sources found: {len(sources)}")
    for source in sources[:10]:  # Show first 10
        print(f"  - {source[0]}")
    if len(sources) > 10:
        print(f"  ... and {len(sources) - 10} more")
    
    # Get sample of records with sources
    sample_query = """
        SELECT type, sourceName, COUNT(*) as count 
        FROM health_records 
        WHERE sourceName IS NOT NULL 
        GROUP BY type, sourceName 
        ORDER BY count DESC 
        LIMIT 10
    """
    samples = db_manager.execute_query(sample_query)
    print(f"\nTop metric-source combinations:")
    for type_name, source, count in samples:
        clean_type = type_name.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
        print(f"  - {clean_type} from {source}: {count} records")
    
    # Check if get_available_sources() is working
    print(f"\nTesting HealthDatabase.get_available_sources():")
    db_sources = health_db.get_available_sources()
    print(f"Returned {len(db_sources)} sources")
    for source in db_sources[:5]:
        print(f"  - {source}")