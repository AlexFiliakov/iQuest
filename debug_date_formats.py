#!/usr/bin/env python3
"""Debug script to investigate date format issues in Apple Health Monitor database.

This script checks:
1. What date formats are stored after XML import
2. How DATE() SQL function behaves with different formats
3. Timezone and format inconsistencies
"""

import sqlite3
import os
from datetime import datetime, date
from pathlib import Path
import sys

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_data_directory, DB_FILE_NAME


def get_db_connection():
    """Get a connection to the health database."""
    # Get the data directory and construct database path
    data_dir = get_data_directory()
    db_path = Path(data_dir) / DB_FILE_NAME
    
    print(f"Connecting to database at: {db_path}")
    
    if not db_path.exists():
        print(f"ERROR: Database does not exist at {db_path}")
        return None
    
    return sqlite3.connect(str(db_path))


def analyze_date_formats():
    """Analyze date formats stored in the database."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATE FORMAT ANALYSIS")
    print("="*80)
    
    # Check if health_records table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='health_records'
    """)
    if not cursor.fetchone():
        print("ERROR: health_records table does not exist!")
        conn.close()
        return
    
    # Get sample of dates from database
    print("\n1. Sample of raw startDate values from database:")
    print("-" * 50)
    cursor.execute("""
        SELECT DISTINCT startDate, type, sourceName
        FROM health_records 
        ORDER BY startDate DESC 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  startDate: {row[0]!r}")
        print(f"  type: {row[1]}, source: {row[2]}")
        print()
    
    # Check unique date formats
    print("\n2. Unique date format patterns:")
    print("-" * 50)
    cursor.execute("""
        SELECT 
            startDate,
            LENGTH(startDate) as len,
            COUNT(*) as count
        FROM health_records
        WHERE startDate IS NOT NULL
        GROUP BY LENGTH(startDate)
        ORDER BY count DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  Example: {row[0]!r}")
        print(f"  Length: {row[1]}, Count: {row[2]}")
        print()
    
    # Test DATE() function with different formats
    print("\n3. Testing DATE() SQL function with stored dates:")
    print("-" * 50)
    
    # Get a few distinct dates
    cursor.execute("""
        SELECT DISTINCT startDate 
        FROM health_records 
        WHERE startDate IS NOT NULL
        ORDER BY startDate DESC
        LIMIT 5
    """)
    
    sample_dates = cursor.fetchall()
    
    for (date_value,) in sample_dates:
        # Test DATE() function
        cursor.execute("SELECT DATE(?), DATE(?) = DATE(?)", 
                      (date_value, date_value, date_value))
        result = cursor.fetchone()
        print(f"  Original: {date_value!r}")
        print(f"  DATE():   {result[0]!r}")
        print(f"  Self-compare: {result[1]}")
        
        # Test with Python date comparison
        today = date.today()
        test_date = today.isoformat()
        cursor.execute("SELECT DATE(?) = ?", (date_value, test_date))
        result = cursor.fetchone()
        print(f"  Compares with '{test_date}': {result[0]}")
        print()
    
    # Check for timezone information
    print("\n4. Checking for timezone information:")
    print("-" * 50)
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN startDate LIKE '%+%' OR startDate LIKE '%-%' THEN 1 ELSE 0 END) as with_tz,
               SUM(CASE WHEN startDate LIKE '%T%' THEN 1 ELSE 0 END) as with_time
        FROM health_records
        WHERE startDate IS NOT NULL
    """)
    
    result = cursor.fetchone()
    print(f"  Total records: {result[0]}")
    print(f"  With timezone: {result[1]}")
    print(f"  With time component: {result[2]}")
    
    # Test specific date query patterns
    print("\n5. Testing query patterns used in Daily tab:")
    print("-" * 50)
    
    # Test with today's date
    test_date = date.today()
    test_date_str = test_date.isoformat()
    
    print(f"\nTesting with date: {test_date_str}")
    
    # Pattern 1: DATE(startDate) = ?
    cursor.execute("""
        SELECT COUNT(*) 
        FROM health_records 
        WHERE DATE(startDate) = ?
    """, (test_date_str,))
    count1 = cursor.fetchone()[0]
    print(f"  DATE(startDate) = '{test_date_str}': {count1} records")
    
    # Pattern 2: Direct string comparison
    cursor.execute("""
        SELECT COUNT(*) 
        FROM health_records 
        WHERE startDate = ?
    """, (test_date_str,))
    count2 = cursor.fetchone()[0]
    print(f"  startDate = '{test_date_str}': {count2} records")
    
    # Pattern 3: LIKE pattern
    cursor.execute("""
        SELECT COUNT(*) 
        FROM health_records 
        WHERE startDate LIKE ?
    """, (f"{test_date_str}%",))
    count3 = cursor.fetchone()[0]
    print(f"  startDate LIKE '{test_date_str}%': {count3} records")
    
    # Find dates that match today
    print(f"\n  Records for {test_date_str}:")
    cursor.execute("""
        SELECT type, startDate, value
        FROM health_records 
        WHERE DATE(startDate) = ?
        LIMIT 5
    """, (test_date_str,))
    
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]!r} = {row[2]}")
    
    conn.close()


def check_import_methods():
    """Check how different import methods store dates."""
    print("\n" + "="*80)
    print("IMPORT METHOD COMPARISON")
    print("="*80)
    
    # Check XML import code
    print("\n1. Checking XML import date handling...")
    print("-" * 50)
    
    # Read the XML streaming processor
    xml_processor_path = os.path.join(os.path.dirname(__file__), 'src', 'xml_streaming_processor.py')
    if os.path.exists(xml_processor_path):
        with open(xml_processor_path, 'r') as f:
            content = f.read()
            
        # Look for date parsing
        if 'startDate' in content:
            print("  Found startDate handling in XML processor")
            # Extract relevant lines
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'startDate' in line and ('=' in line or 'get(' in line):
                    print(f"  Line {i+1}: {line.strip()}")
    
    # Check data loader
    print("\n2. Checking data_loader.py date handling...")
    print("-" * 50)
    
    data_loader_path = os.path.join(os.path.dirname(__file__), 'src', 'data_loader.py')
    if os.path.exists(data_loader_path):
        with open(data_loader_path, 'r') as f:
            content = f.read()
            
        # Look for date processing
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'startDate' in line and any(keyword in line for keyword in ['parse', 'format', 'convert']):
                print(f"  Line {i+1}: {line.strip()}")


def suggest_fixes():
    """Suggest potential fixes based on findings."""
    print("\n" + "="*80)
    print("POTENTIAL FIXES")
    print("="*80)
    
    print("""
Based on common XML date format issues, here are potential fixes:

1. If XML stores dates with timezone (e.g., '2024-01-15T10:30:00-05:00'):
   - Modify XML import to strip timezone and convert to local date
   - Use: DATE(datetime(startDate, 'localtime')) in SQL queries

2. If XML stores full datetime strings (e.g., '2024-01-15 10:30:00'):
   - Ensure DATE() function is used consistently in queries
   - Or store only date portion during import

3. For consistent behavior:
   - Standardize all date storage to YYYY-MM-DD format
   - Update import code to convert dates during import
   - Ensure all queries use the same date comparison method
""")


if __name__ == "__main__":
    print("Apple Health Monitor - Date Format Debug Tool")
    print("=" * 80)
    
    analyze_date_formats()
    check_import_methods()
    suggest_fixes()