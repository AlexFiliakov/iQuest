#!/usr/bin/env python3
"""Test script to verify the no_data_message attribute error fix."""

import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import QApplication
from src.ui.daily_dashboard_widget import DailyDashboardWidget
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_no_data_scenarios():
    """Test various scenarios that trigger no data messages."""
    app = QApplication(sys.argv)
    
    # Create daily dashboard widget
    widget = DailyDashboardWidget()
    widget.resize(800, 600)
    widget.show()
    
    print("\n" + "="*50)
    print("No Data Message Test")
    print("="*50)
    print("\nTesting various no data scenarios...")
    
    # Test 1: No calculator set (should show "No Data Loaded")
    print("\n1. Testing with no calculator...")
    widget._load_daily_data()
    
    # Test 2: Show no data for specific date
    print("\n2. Testing no data for specific date...")
    widget._show_no_data_for_date()
    
    # Test 3: Hide no data message
    print("\n3. Testing hide no data message...")
    widget._hide_no_data_message()
    
    # Test 4: Show error message
    print("\n4. Testing error message...")
    widget._show_error_message("Test error message")
    
    print("\n✓ All tests completed without AttributeError")
    print("="*50 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_no_data_scenarios())