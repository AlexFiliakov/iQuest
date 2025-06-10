"""Test data access in portable mode."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_access import DataAccess
from src.utils.logging_config import setup_logging
from datetime import date

def test_data_access():
    """Test DataAccess functionality."""
    setup_logging()
    
    print("Testing DataAccess...")
    
    # Create data access instance
    data_access = DataAccess()
    
    print(f"DataAccess created: {data_access}")
    print(f"Database path: {data_access.db_path if hasattr(data_access, 'db_path') else 'Not set'}")
    
    # Test getting available metrics
    try:
        metrics = data_access.get_available_metrics()
        print(f"\nAvailable metrics: {len(metrics)}")
        for i, metric in enumerate(metrics[:5]):  # Show first 5
            print(f"  - {metric}")
        if len(metrics) > 5:
            print(f"  ... and {len(metrics) - 5} more")
    except Exception as e:
        print(f"Error getting metrics: {e}")
    
    # Test getting data for today
    try:
        today = date.today()
        # Try to get step count for today
        data = data_access.get_health_records_by_date_range(
            start_date=today,
            end_date=today,
            metric_type='StepCount'
        )
        if data:
            print(f"\nStep data for today: {len(data)} records")
        else:
            print("\nNo step data for today")
    except Exception as e:
        print(f"Error getting step data: {e}")

if __name__ == "__main__":
    test_data_access()