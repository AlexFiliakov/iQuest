#!/usr/bin/env python3
"""Test database access in portable mode."""

import sqlite3
from datetime import date

# Test with the portable database directly
portable_db_path = "build/dist/HealthMonitor-0.0.1-portable/HealthMonitor/data/health_monitor.db"

# Test database access
try:
    print(f"Testing database access to: {portable_db_path}")
    
    # Use a copy to avoid OneDrive issues
    import shutil
    temp_db = "/tmp/test_portable.db"
    shutil.copy2(portable_db_path, temp_db)
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Test query
    query = """
        SELECT type, COUNT(*) as count, SUM(value) as total
        FROM health_records 
        WHERE type = 'StepCount' 
        AND DATE(startDate) = ?
        GROUP BY type
    """
    
    test_date = date(2025, 4, 30)
    cursor.execute(query, (test_date.isoformat(),))
    result = cursor.fetchall()
    
    if result:
        print(f"\nStepCount data for {test_date}:")
        for row in result:
            print(f"  Type: {row[0]}, Count: {row[1]}, Total: {row[2]}")
    else:
        print(f"\nNo data found for {test_date}")
        
    # Check what dates have data
    query2 = """
        SELECT DISTINCT DATE(startDate) as date
        FROM health_records 
        WHERE type = 'StepCount'
        ORDER BY date DESC
        LIMIT 10
    """
    
    cursor.execute(query2)
    result2 = cursor.fetchall()
    print("\nLatest dates with StepCount data:")
    for row in result2:
        print(f"  {row[0]}")
        
    conn.close()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()