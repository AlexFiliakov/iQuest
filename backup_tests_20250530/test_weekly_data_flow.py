#!/usr/bin/env python3
"""
Test data flow for weekly dashboard without GUI.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from datetime import date, datetime, timedelta
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Create test data
def create_test_data():
    data = []
    for i in range(30):
        d = date.today() - timedelta(days=i)
        timestamp = pd.Timestamp(d)
        data.append({
            'type': 'HKQuantityTypeIdentifierStepCount',
            'value': 5000 + i * 100,
            'unit': 'count',
            'creationDate': timestamp,
            'startDate': timestamp,
            'endDate': timestamp + pd.Timedelta(hours=1)
        })
    return pd.DataFrame(data)

# Test the data flow
print("Creating test data...")
data = create_test_data()
print(f"Data shape: {data.shape}")
print(f"Data columns: {data.columns.tolist()}")

print("\nCreating calculators...")
daily_calc = DailyMetricsCalculator(data)
print("Daily calculator created")

weekly_calc = WeeklyMetricsCalculator(daily_calc)
print("Weekly calculator created")

# Test getting weekly metrics
week_start = date.today() - timedelta(days=date.today().weekday())
week_start_dt = datetime.combine(week_start, datetime.min.time())
print(f"\nGetting metrics for week starting: {week_start}")

try:
    # Need to prepare the data
    calc_data = data.copy()
    if 'startDate' in calc_data.columns and 'creationDate' not in calc_data.columns:
        calc_data['creationDate'] = calc_data['startDate']
    
    metrics = weekly_calc.calculate_weekly_metrics(
        data=calc_data,
        metric_type='HKQuantityTypeIdentifierStepCount',
        week_start=week_start_dt
    )
    
    print(f"Success! Got metrics:")
    print(f"  Average: {metrics.avg}")
    print(f"  Min: {metrics.min}")
    print(f"  Max: {metrics.max}")
    print(f"  Trend: {metrics.trend_direction}")
    print(f"  Daily values: {len(metrics.daily_values)} days")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()