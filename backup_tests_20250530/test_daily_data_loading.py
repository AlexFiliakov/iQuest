#!/usr/bin/env python3
"""Test script to verify Daily tab data loading fixes."""

import sys
import os
from datetime import date, timedelta
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer
from src.ui.main_window import MainWindow
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.utils.logging_config import get_logger

# Set up logging to see debug messages
import logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)

class TestResultsWindow(QWidget):
    """Window to display test results."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily Tab Data Loading Test")
        self.resize(600, 800)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Daily Tab Data Loading Test Results")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Test button
        self.test_btn = QPushButton("Run Tests")
        self.test_btn.clicked.connect(self.run_tests)
        layout.addWidget(self.test_btn)
        
        # Main window reference
        self.main_window = None
        
    def log(self, message):
        """Add message to results."""
        self.results_text.append(message)
        QApplication.processEvents()
        
    def run_tests(self):
        """Run all tests."""
        self.results_text.clear()
        self.log("Starting Daily Tab Data Loading Tests...")
        self.log("=" * 50)
        
        # Create main window
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Run tests in sequence
        QTimer.singleShot(500, self.test_data_loading)
        QTimer.singleShot(1500, self.test_calculator_creation)
        QTimer.singleShot(2500, self.test_date_filtering)
        QTimer.singleShot(3500, self.test_daily_tab_display)
        QTimer.singleShot(4500, self.test_date_navigation)
        QTimer.singleShot(5500, self.complete_tests)
        
    def test_data_loading(self):
        """Test if data is loaded properly."""
        self.log("\n1. Testing Data Loading...")
        
        if hasattr(self.main_window, 'config_tab'):
            data = None
            if hasattr(self.main_window.config_tab, 'get_filtered_data'):
                data = self.main_window.config_tab.get_filtered_data()
            elif hasattr(self.main_window.config_tab, 'filtered_data'):
                data = self.main_window.config_tab.filtered_data
            
            if data is not None and not data.empty:
                self.log(f"✓ Data loaded: {len(data)} records")
                
                # Check columns
                self.log(f"✓ Columns: {', '.join(data.columns)}")
                
                # Check date range
                if 'creationDate' in data.columns:
                    dates = pd.to_datetime(data['creationDate'])
                    self.log(f"✓ Date range: {dates.min()} to {dates.max()}")
                
                # Check unique types
                if 'type' in data.columns:
                    unique_types = data['type'].unique()
                    self.log(f"✓ Unique metric types: {len(unique_types)}")
                    # Show first 5 types
                    for i, metric_type in enumerate(unique_types[:5]):
                        self.log(f"    - {metric_type}")
            else:
                self.log("✗ No data loaded - please import data in Configuration tab")
        else:
            self.log("✗ Configuration tab not found")
    
    def test_calculator_creation(self):
        """Test DailyMetricsCalculator creation."""
        self.log("\n2. Testing Calculator Creation...")
        
        if hasattr(self.main_window, 'config_tab'):
            data = None
            if hasattr(self.main_window.config_tab, 'get_filtered_data'):
                data = self.main_window.config_tab.get_filtered_data()
            
            if data is not None and not data.empty:
                try:
                    import time
                    local_tz = time.tzname[0]
                    calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    self.log(f"✓ Calculator created successfully with timezone: {local_tz}")
                    
                    # Check prepared data
                    if hasattr(calculator, 'data'):
                        self.log(f"✓ Calculator data shape: {calculator.data.shape}")
                        
                        # Check date column
                        if 'date' in calculator.data.columns:
                            self.log("✓ Date column exists in calculator")
                            unique_dates = calculator.data['date'].unique()
                            self.log(f"✓ Unique dates in calculator: {len(unique_dates)}")
                        else:
                            self.log("✗ Date column NOT found in calculator")
                except Exception as e:
                    self.log(f"✗ Error creating calculator: {e}")
                    import traceback
                    self.log(traceback.format_exc())
    
    def test_date_filtering(self):
        """Test date filtering in calculator."""
        self.log("\n3. Testing Date Filtering...")
        
        if hasattr(self.main_window, 'config_tab'):
            data = None
            if hasattr(self.main_window.config_tab, 'get_filtered_data'):
                data = self.main_window.config_tab.get_filtered_data()
            
            if data is not None and not data.empty:
                try:
                    import time
                    local_tz = time.tzname[0]
                    calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    
                    # Test filtering for today
                    today = date.today()
                    if 'type' in data.columns:
                        unique_types = data['type'].unique()
                        if len(unique_types) > 0:
                            test_metric = unique_types[0]
                            
                            # Test calculate_daily_statistics
                            stats = calculator.calculate_daily_statistics(test_metric, today)
                            if stats:
                                self.log(f"✓ Stats for {test_metric} on {today}: count={stats.count}, mean={stats.mean}")
                            else:
                                self.log(f"✗ No stats returned for {test_metric} on {today}")
                                
                            # Test yesterday
                            yesterday = today - timedelta(days=1)
                            stats_yesterday = calculator.calculate_daily_statistics(test_metric, yesterday)
                            if stats_yesterday:
                                self.log(f"✓ Stats for {test_metric} on {yesterday}: count={stats_yesterday.count}")
                            else:
                                self.log(f"✗ No stats for {test_metric} on {yesterday}")
                except Exception as e:
                    self.log(f"✗ Error testing date filtering: {e}")
    
    def test_daily_tab_display(self):
        """Test Daily tab display."""
        self.log("\n4. Testing Daily Tab Display...")
        
        # Switch to Daily tab
        self.main_window.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        if hasattr(self.main_window, 'daily_dashboard'):
            dashboard = self.main_window.daily_dashboard
            self.log("✓ Daily dashboard exists")
            
            # Check calculator
            if dashboard.daily_calculator:
                self.log("✓ Daily calculator is set")
            else:
                self.log("✗ Daily calculator is NOT set")
            
            # Check metric cards
            if hasattr(dashboard, '_metric_cards') and dashboard._metric_cards:
                self.log(f"✓ Metric cards created: {len(dashboard._metric_cards)}")
                
                # Check data in cards
                cards_with_data = 0
                for metric_name, card in dashboard._metric_cards.items():
                    if card.value_label.text() != "--":
                        cards_with_data += 1
                        self.log(f"  - {metric_name}: {card.value_label.text()}")
                
                self.log(f"✓ Cards with data: {cards_with_data}/{len(dashboard._metric_cards)}")
            else:
                self.log("✗ No metric cards found")
            
            # Check current date
            self.log(f"✓ Current date: {dashboard._current_date}")
            
            # Check cache
            if hasattr(dashboard, '_cache_date'):
                self.log(f"✓ Cache date: {dashboard._cache_date}")
        else:
            self.log("✗ Daily dashboard not found")
    
    def test_date_navigation(self):
        """Test date navigation."""
        self.log("\n5. Testing Date Navigation...")
        
        if hasattr(self.main_window, 'daily_dashboard'):
            dashboard = self.main_window.daily_dashboard
            
            # Navigate to previous day
            original_date = dashboard._current_date
            dashboard._go_to_previous_day()
            QApplication.processEvents()
            
            if dashboard._current_date == original_date - timedelta(days=1):
                self.log("✓ Previous day navigation works")
                
                # Check if data is displayed
                cards_with_data = 0
                for metric_name, card in dashboard._metric_cards.items():
                    if card.value_label.text() != "--":
                        cards_with_data += 1
                self.log(f"  - Cards with data after navigation: {cards_with_data}")
            else:
                self.log("✗ Previous day navigation failed")
            
            # Navigate back to today
            dashboard._go_to_today()
            QApplication.processEvents()
            
            if dashboard._current_date == date.today():
                self.log("✓ Today navigation works")
            else:
                self.log("✗ Today navigation failed")
    
    def complete_tests(self):
        """Complete tests and show summary."""
        self.log("\n" + "=" * 50)
        self.log("Test Summary:")
        self.log("=" * 50)
        
        # Count successes and failures
        text = self.results_text.toPlainText()
        successes = text.count("✓")
        failures = text.count("✗")
        
        self.log(f"\nTotal tests passed: {successes}")
        self.log(f"Total tests failed: {failures}")
        
        if failures == 0:
            self.log("\n✅ All tests passed! Daily tab should be working properly.")
        else:
            self.log("\n⚠️ Some tests failed. Please check the results above.")
            self.log("\nCommon issues:")
            self.log("1. No data loaded - import data in Configuration tab first")
            self.log("2. Date mismatch - check timezone settings")
            self.log("3. Empty data - ensure imported file has valid health data")

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    test_window = TestResultsWindow()
    test_window.show()
    
    print("\n" + "="*60)
    print("Daily Tab Data Loading Test")
    print("="*60)
    print("\nThis test will verify:")
    print("1. Data is loaded properly from Configuration tab")
    print("2. DailyMetricsCalculator is created correctly")
    print("3. Date filtering works properly")
    print("4. Daily tab displays data correctly")
    print("5. Date navigation updates data")
    print("\nClick 'Run Tests' to begin")
    print("="*60 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())