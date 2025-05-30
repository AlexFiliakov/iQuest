#!/usr/bin/env python3
"""Test script to verify Daily tab navigation fixes."""

import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from src.ui.daily_dashboard_widget import DailyDashboardWidget
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_navigation():
    """Test the daily dashboard navigation functionality."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    window.setWindowTitle("Daily Tab Navigation Test")
    layout = QVBoxLayout(window)
    
    # Create daily dashboard
    dashboard = DailyDashboardWidget()
    layout.addWidget(dashboard)
    
    # Add test buttons
    test_buttons = QWidget()
    test_layout = QVBoxLayout(test_buttons)
    
    def test_previous_day():
        logger.info("Testing previous day navigation...")
        dashboard._go_to_previous_day()
        
    def test_next_day():
        logger.info("Testing next day navigation...")
        dashboard._go_to_next_day()
        
    def test_today():
        logger.info("Testing today navigation...")
        dashboard._go_to_today()
        
    def test_specific_date():
        logger.info("Testing specific date navigation...")
        # Set a date from last week
        dashboard._current_date = date.today() - timedelta(days=7)
        dashboard._update_date_display()
        dashboard._refresh_data()
    
    # Create test buttons
    prev_btn = QPushButton("Test Previous Day")
    prev_btn.clicked.connect(test_previous_day)
    test_layout.addWidget(prev_btn)
    
    next_btn = QPushButton("Test Next Day")
    next_btn.clicked.connect(test_next_day)
    test_layout.addWidget(next_btn)
    
    today_btn = QPushButton("Test Today")
    today_btn.clicked.connect(test_today)
    test_layout.addWidget(today_btn)
    
    specific_btn = QPushButton("Test Specific Date (7 days ago)")
    specific_btn.clicked.connect(test_specific_date)
    test_layout.addWidget(specific_btn)
    
    layout.addWidget(test_buttons)
    
    # Show window
    window.resize(900, 700)
    window.show()
    
    print("\n" + "="*50)
    print("Daily Tab Navigation Test")
    print("="*50)
    print("\nInstructions:")
    print("1. Click the test buttons to test different navigation scenarios")
    print("2. Use the navigation controls in the Daily dashboard")
    print("3. Check that the UI doesn't crash")
    print("4. Verify error messages are shown properly for any issues")
    print("\nExpected behavior:")
    print("- Navigation should work without crashes")
    print("- Error messages should appear for any issues")
    print("- The display should update properly for each date")
    print("="*50 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_navigation())