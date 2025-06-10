#!/usr/bin/env python3
"""Test script to verify daily dashboard works in portable mode."""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test portable mode detection
from config import is_portable_mode, get_data_directory, DATA_DIR
print(f"Portable mode: {is_portable_mode()}")
print(f"Data directory: {DATA_DIR}")

# Test database initialization
from database import DatabaseManager
from health_database import HealthDatabase

print("\n=== Testing DatabaseManager ===")
try:
    db = DatabaseManager()
    print(f"DatabaseManager initialized successfully")
    print(f"Database path: {db.db_path}")
    print(f"Database exists: {db.db_path.exists()}")
    
    # Try a simple query
    result = db.execute_query("SELECT COUNT(*) FROM health_records")
    if result:
        print(f"Health records count: {result[0][0]}")
except Exception as e:
    print(f"DatabaseManager error: {e}")

print("\n=== Testing HealthDatabase ===")
try:
    health_db = HealthDatabase()
    print("HealthDatabase initialized successfully")
    
    # Try getting available types
    types = health_db.get_available_types()
    print(f"Available types: {len(types)}")
    if types:
        print(f"First few types: {types[:5]}")
except Exception as e:
    print(f"HealthDatabase error: {e}")

print("\n=== Testing DailyDashboardWidget ===")
try:
    from PyQt6.QtWidgets import QApplication
    from ui.daily_dashboard_widget import DailyDashboardWidget
    from data_access import DataAccess
    
    # Create minimal Qt app
    app = QApplication(sys.argv)
    
    # Create data access
    data_access = DataAccess()
    
    # Create daily dashboard
    daily_widget = DailyDashboardWidget(data_access=data_access)
    print("DailyDashboardWidget created successfully")
    
    # Check initialization
    print(f"Daily calculator available: {daily_widget.daily_calculator is not None}")
    print(f"Health DB available: {daily_widget.health_db is not None}")
    print(f"Data access available: {daily_widget.data_access is not None}")
    
    # Try detecting metrics
    daily_widget._detect_available_metrics()
    print(f"Available metrics: {len(daily_widget._available_metrics)}")
    if daily_widget._available_metrics:
        print(f"First few metrics: {daily_widget._available_metrics[:5]}")
    
    # Try loading data
    print("\n=== Testing data loading ===")
    daily_widget._load_daily_data()
    print("Data loading completed without errors")
    
except Exception as e:
    print(f"DailyDashboardWidget error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test complete ===")