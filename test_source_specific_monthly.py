#!/usr/bin/env python3
"""Test source-specific metric selection in the Monthly tab."""

import sys
from PyQt6.QtWidgets import QApplication
from datetime import date, datetime
import random

# Add src to path
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator


def create_test_data():
    """Create test data with multiple sources."""
    test_data = {}
    
    # Create data for current month with different sources
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # iPhone data (higher values)
    for day in range(1, 20):
        d = date(current_year, current_month, day)
        test_data[d] = {
            'iPhone': random.randint(8000, 15000),
            'Apple Watch': random.randint(2000, 5000)
        }
    
    return test_data


class MockHealthDatabase:
    """Mock health database for testing."""
    
    def get_available_sources(self):
        """Return test sources."""
        return ["iPhone", "Apple Watch Series 7", "Health App"]
    
    def get_types_for_source(self, source):
        """Return test types for a source."""
        if source == "iPhone":
            return ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierDistanceWalkingRunning"]
        elif source == "Apple Watch Series 7":
            return ["HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierHeartRate", 
                    "HKQuantityTypeIdentifierActiveEnergyBurned"]
        else:
            return ["HKQuantityTypeIdentifierBodyMass"]


class MockMonthlyCalculator:
    """Mock monthly calculator for testing."""
    
    def __init__(self, test_data):
        self.test_data = test_data
    
    def get_daily_aggregate(self, metric, date):
        """Return test data for a date (aggregated)."""
        if date in self.test_data:
            # Return sum of all sources
            return sum(self.test_data[date].values())
        return None


def main():
    app = QApplication(sys.argv)
    
    # Create test data
    test_data = create_test_data()
    
    # Create mock calculator
    mock_calculator = MockMonthlyCalculator(test_data)
    
    # Create monthly dashboard widget
    widget = MonthlyDashboardWidget(monthly_calculator=mock_calculator)
    
    # Replace health_db with mock
    widget.health_db = MockHealthDatabase()
    
    # Reload available metrics to get mock data
    widget._load_available_metrics()
    
    # Update combo box
    widget.metric_combo.clear()
    for metric_tuple in widget._available_metrics:
        metric, source = metric_tuple
        display_name = widget._metric_display_names.get(metric, metric)
        
        if source:
            display_text = f"{display_name} - {source}"
        else:
            display_text = f"{display_name} (All Sources)"
            
        widget.metric_combo.addItem(display_text, metric_tuple)
    
    # Override _get_source_specific_daily_value for testing
    def mock_get_source_specific_daily_value(metric_type, date, source):
        if date in test_data and source in test_data[date]:
            return float(test_data[date][source])
        return None
    
    widget._get_source_specific_daily_value = mock_get_source_specific_daily_value
    
    # Show widget
    widget.resize(1200, 800)
    widget.show()
    
    print("Source-specific Monthly tab test:")
    print("- Check the dropdown shows sources like 'Steps - iPhone'")
    print("- Select different sources and verify the calendar shows different data")
    print("- Hover over dates to see source in tooltip")
    print("- Check that the title shows the selected source")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()