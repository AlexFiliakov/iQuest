#!/usr/bin/env python3
"""
Minimal fix for weekly tab display.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
import pandas as pd
from datetime import date, timedelta

from src.ui.weekly_dashboard_widget import WeeklyDashboardWidget
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Create simple test data
def create_simple_data():
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

# Test the weekly dashboard directly
app = QApplication(sys.argv)

# Create window
window = QMainWindow()
window.setWindowTitle("Weekly Tab Fix Test")
window.setGeometry(100, 100, 1200, 800)

# Create weekly dashboard
weekly = WeeklyDashboardWidget()

# Create and set data
data = create_simple_data()
daily_calc = DailyMetricsCalculator(data)
weekly_calc = WeeklyMetricsCalculator(daily_calc)
weekly.set_weekly_calculator(weekly_calc)

# Set as central widget
window.setCentralWidget(weekly)
window.show()

sys.exit(app.exec())