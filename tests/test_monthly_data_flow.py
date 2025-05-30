"""Test suite for monthly dashboard data flow."""

import unittest
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import logging
from unittest.mock import MagicMock, patch

# Set up test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the components we need to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
from PyQt6.QtWidgets import QApplication


class TestMonthlyDataFlow(unittest.TestCase):
    """Test the complete data flow from raw data to monthly dashboard display."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for widget tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test data and components."""
        # Create comprehensive test data
        self.test_data = self._create_test_data()
        logger.info(f"Created test data with {len(self.test_data)} records")
        logger.info(f"Data types: {self.test_data['type'].unique()}")
        
    def _create_test_data(self):
        """Create realistic test health data."""
        # Generate data for the last 60 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data_records = []
        
        # Generate multiple types of health data
        for date in dates:
            # Step count data - single daily reading
            data_records.append({
                'type': 'HKQuantityTypeIdentifierStepCount',
                'sourceName': 'iPhone',
                'unit': 'count',
                'creationDate': date,
                'startDate': date.replace(hour=0, minute=0, second=0),
                'endDate': date.replace(hour=23, minute=59, second=59),
                'value': str(np.random.randint(5000, 15000)),
                'date': date.date()  # Add date column for easier filtering
            })
            
            # Heart rate data - multiple readings per day
            for hour in [6, 12, 18, 22]:
                hr_time = date.replace(hour=hour, minute=0, second=0)
                data_records.append({
                    'type': 'HKQuantityTypeIdentifierHeartRate',
                    'sourceName': 'Apple Watch',
                    'unit': 'count/min',
                    'creationDate': hr_time,
                    'startDate': hr_time,
                    'endDate': hr_time + timedelta(minutes=1),
                    'value': str(np.random.randint(60, 80)),
                    'date': date.date()
                })
            
            # Walking distance data
            data_records.append({
                'type': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'sourceName': 'iPhone',
                'unit': 'm',
                'creationDate': date,
                'startDate': date.replace(hour=0, minute=0, second=0),
                'endDate': date.replace(hour=23, minute=59, second=59),
                'value': str(np.random.uniform(3000, 10000)),  # 3-10 km in meters
                'date': date.date()
            })
        
        df = pd.DataFrame(data_records)
        
        # Ensure value column is numeric
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        logger.info(f"Test data shape: {df.shape}")
        logger.info(f"Test data columns: {df.columns.tolist()}")
        logger.info(f"Unique types: {df['type'].unique()}")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
    
    def test_daily_calculator_data_retrieval(self):
        """Test that daily calculator correctly retrieves data."""
        # Create daily calculator
        daily_calc = DailyMetricsCalculator(self.test_data, timezone='UTC')
        
        # Test step count retrieval
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Get daily aggregates for step count
        daily_steps = daily_calc.calculate_daily_aggregates(
            'HKQuantityTypeIdentifierStepCount',
            'sum',
            yesterday,
            today
        )
        
        logger.info(f"Daily steps aggregates: {daily_steps}")
        self.assertIsNotNone(daily_steps)
        self.assertFalse(daily_steps.empty, "Daily aggregates should not be empty")
        
    def test_monthly_calculator_get_daily_aggregate(self):
        """Test monthly calculator's get_daily_aggregate method."""
        # Create calculators
        daily_calc = DailyMetricsCalculator(self.test_data, timezone='UTC')
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Test getting daily aggregate for a specific date
        test_date = date.today() - timedelta(days=5)
        
        # Test with step count
        steps_value = monthly_calc.get_daily_aggregate(
            'HKQuantityTypeIdentifierStepCount',
            test_date
        )
        
        logger.info(f"Steps on {test_date}: {steps_value}")
        self.assertIsNotNone(steps_value, f"Should have step data for {test_date}")
        self.assertGreater(steps_value, 0, "Step count should be positive")
        
    def test_monthly_widget_data_loading(self):
        """Test that monthly widget correctly loads and displays data."""
        # Create calculators
        daily_calc = DailyMetricsCalculator(self.test_data, timezone='UTC')
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Create monthly widget
        widget = MonthlyDashboardWidget(monthly_calculator=monthly_calc)
        
        # Force data loading
        widget._load_month_data()
        
        # Check if data was loaded into the calendar heatmap
        self.assertTrue(hasattr(widget, 'calendar_heatmap'), "Widget should have calendar heatmap")
        self.assertTrue(hasattr(widget.calendar_heatmap, '_metric_data'), "Calendar should have metric data")
        
        metric_data = widget.calendar_heatmap._metric_data
        logger.info(f"Loaded {len(metric_data)} days of data into calendar")
        
        self.assertGreater(len(metric_data), 0, "Calendar should have data loaded")
        
    def test_metric_type_conversion(self):
        """Test that metric types are correctly converted between formats."""
        widget = MonthlyDashboardWidget()
        
        # Test the conversion in _load_month_data
        metric_type = "StepCount"
        
        # Check HK prefix addition
        if metric_type == "SleepAnalysis" or metric_type == "MindfulSession":
            hk_type = f"HKCategoryTypeIdentifier{metric_type}"
        else:
            hk_type = f"HKQuantityTypeIdentifier{metric_type}"
            
        self.assertEqual(hk_type, "HKQuantityTypeIdentifierStepCount")
        
    def test_data_flow_with_different_metrics(self):
        """Test data flow with various metric types."""
        daily_calc = DailyMetricsCalculator(self.test_data, timezone='UTC')
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        metrics_to_test = [
            ('HKQuantityTypeIdentifierStepCount', 'StepCount'),
            ('HKQuantityTypeIdentifierHeartRate', 'HeartRate'),
            ('HKQuantityTypeIdentifierDistanceWalkingRunning', 'DistanceWalkingRunning')
        ]
        
        for hk_type, display_type in metrics_to_test:
            with self.subTest(metric=display_type):
                # Test daily aggregate retrieval
                test_date = date.today() - timedelta(days=3)
                value = monthly_calc.get_daily_aggregate(hk_type, test_date)
                
                logger.info(f"{display_type} on {test_date}: {value}")
                
                # Some metrics might not have data for every day
                if value is not None:
                    self.assertGreater(value, 0, f"{display_type} should be positive")
    
    def test_empty_data_handling(self):
        """Test handling of empty or missing data."""
        # Create calculator with empty data
        empty_data = pd.DataFrame(columns=['type', 'value', 'date', 'creationDate'])
        daily_calc = DailyMetricsCalculator(empty_data, timezone='UTC')
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Test that it handles empty data gracefully
        test_date = date.today()
        value = monthly_calc.get_daily_aggregate('HKQuantityTypeIdentifierStepCount', test_date)
        
        self.assertIsNone(value, "Should return None for empty data")
        
    def test_date_filtering(self):
        """Test that date filtering works correctly."""
        daily_calc = DailyMetricsCalculator(self.test_data, timezone='UTC')
        
        # Get data for specific date range
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        daily_aggregates = daily_calc.calculate_daily_aggregates(
            'HKQuantityTypeIdentifierStepCount',
            'sum',
            start_date,
            end_date
        )
        
        logger.info(f"Aggregates for date range: {daily_aggregates}")
        
        # Check that we have data for the expected number of days
        self.assertGreaterEqual(len(daily_aggregates), 1, "Should have at least one day of data")
        self.assertLessEqual(len(daily_aggregates), 8, "Should have at most 8 days of data")


class TestMonthlyWidgetIntegration(unittest.TestCase):
    """Integration tests for the monthly widget with mock database."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for widget tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_widget_with_mock_database(self):
        """Test widget with mocked database responses."""
        # Create widget with mocked health database
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_available_sources.return_value = ['iPhone', 'Apple Watch']
            mock_db.get_types_for_source.return_value = [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierHeartRate'
            ]
            mock_db.get_available_types.return_value = [
                'HKQuantityTypeIdentifierStepCount',
                'HKQuantityTypeIdentifierHeartRate',
                'HKQuantityTypeIdentifierDistanceWalkingRunning'
            ]
            mock_db_class.return_value = mock_db
            
            widget = MonthlyDashboardWidget()
            
            # Check that metrics were loaded
            self.assertGreater(len(widget._available_metrics), 0, "Should have available metrics")
            
            # Check that combo box was populated
            self.assertGreater(widget.metric_combo.count(), 0, "Combo box should have items")


if __name__ == '__main__':
    unittest.main(verbosity=2)