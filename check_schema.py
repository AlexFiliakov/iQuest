#!/usr/bin/env python3
"""Check the actual schema of health_records table."""

import sys
sys.path.insert(0, 'src')

from src.database import DatabaseManager

db = DatabaseManager()

# Get table info
schema_query = "PRAGMA table_info(health_records)"
columns = db.execute_query(schema_query)

print("health_records table schema:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")  # name (type)