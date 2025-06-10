#\!/usr/bin/env python3
"""Debug script to understand why Daily tab is not showing data."""

import sqlite3
import sys
import os
from datetime import date, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_data_directory, DB_FILE_NAME

def debug_daily_data():
    """Debug why daily data is not showing."""
    # Get database path
    data_dir = get_data_directory()
    db_path = Path(data_dir) / DB_FILE_NAME
    
    if not db_path.exists():
        print(f"ERROR: Database does not exist at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("Debugging Daily Data Issue")
    print("=" * 80)
    
    # Check date formats in database
    print("\n1. Checking date formats in database:")
    cursor.execute("""
        SELECT startDate, DATE(startDate) as date_func_result
        FROM health_records
        WHERE type LIKE '%StepCount%'
        ORDER BY startDate DESC
        LIMIT 10
    """)
    
    print("Recent StepCount records:")
    for row in cursor.fetchall():
        print(f"  startDate: {row[0]!r}, DATE(startDate): {row[1]!r}")
    
    # Check what dates we have data for
    print("\n2. Checking available dates for StepCount:")
    cursor.execute("""
        SELECT DATE(startDate) as record_date, COUNT(*) as count
        FROM health_records
        WHERE type LIKE '%StepCount%'
        AND DATE(startDate) IS NOT NULL
        GROUP BY DATE(startDate)
        ORDER BY record_date DESC
        LIMIT 10
    """)
    
    print("Available dates:")
    for row in cursor.fetchall():
        print(f"  Date: {row[0]}, Count: {row[1]}")
    
    # Test the exact query used by Daily tab
    test_date = date.today()
    print(f"\n3. Testing Daily tab query for today ({test_date.isoformat()}):")
    
    # First check if we have any data for today
    cursor.execute("""
        SELECT COUNT(*) 
        FROM health_records
        WHERE type LIKE '%StepCount%'
        AND DATE(startDate) = ?
    """, (test_date.isoformat(),))
    
    count = cursor.fetchone()[0]
    print(f"  Records found for {test_date.isoformat()}: {count}")
    
    # Try yesterday
    from datetime import timedelta
    yesterday = test_date - timedelta(days=1)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM health_records
        WHERE type LIKE '%StepCount%'
        AND DATE(startDate) = ?
    """, (yesterday.isoformat(),))
    
    count = cursor.fetchone()[0]
    print(f"  Records found for {yesterday.isoformat()}: {count}")
    
    # Check the most recent date with data
    print("\n4. Most recent date with StepCount data:")
    cursor.execute("""
        SELECT DATE(startDate) as most_recent
        FROM health_records
        WHERE type LIKE '%StepCount%'
        AND DATE(startDate) IS NOT NULL
        ORDER BY startDate DESC
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if result:
        print(f"  Most recent date: {result[0]}")
        
        # Now test the full query as used in daily dashboard
        print(f"\n5. Testing full query for most recent date:")
        cursor.execute("""
            SELECT SUM(CAST(value AS FLOAT)) as daily_total
            FROM health_records
            WHERE type LIKE '%StepCount%'
            AND DATE(startDate) = ?
            AND value IS NOT NULL
        """, (result[0],))
        
        total = cursor.fetchone()
        if total and total[0]:
            print(f"  Total steps: {total[0]}")
        else:
            print("  No data returned!")
    
    # Check if there's a timezone issue
    print("\n6. Checking for potential timezone issues:")
    cursor.execute("""
        SELECT startDate, 
               datetime(startDate) as datetime_func,
               date(startDate) as date_func,
               strftime('%Y-%m-%d', startDate) as strftime_date
        FROM health_records
        WHERE type LIKE '%StepCount%'
        LIMIT 5
    """)
    
    print("Date function results:")
    for row in cursor.fetchall():
        print(f"  Original: {row[0]}")
        print(f"    datetime(): {row[1]}")
        print(f"    date(): {row[2]}")
        print(f"    strftime(): {row[3]}")
        print()
    
    conn.close()

if __name__ == "__main__":
    debug_daily_data()
