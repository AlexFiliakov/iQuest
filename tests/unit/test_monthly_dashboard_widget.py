"""Unit tests for the MonthlyDashboardWidget."""

import unittest
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator


class TestMonthlyDashboardWidget(unittest.TestCase):
    """Test suite for MonthlyDashboardWidget functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for widget tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the health database
        self.mock_health_db = MagicMock()
        self.mock_health_db.get_available_sources.return_value = ['iPhone', 'Apple Watch']
        self.mock_health_db.get_types_for_source.return_value = [
            'HKQuantityTypeIdentifierStepCount',
            'HKQuantityTypeIdentifierHeartRate'
        ]
        self.mock_health_db.get_available_types.return_value = [
            'HKQuantityTypeIdentifierStepCount',
            'HKQuantityTypeIdentifierHeartRate',
            'HKQuantityTypeIdentifierDistanceWalkingRunning'
        ]
        
        # Create test data
        self.test_data = self._create_test_data()
        
    def _create_test_data(self):
        """Create test health data."""
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        records = []
        
        for date in dates:
            records.append({
                'type': 'HKQuantityTypeIdentifierStepCount',
                'sourceName': 'iPhone',
                'unit': 'count',
                'creationDate': date,
                'startDate': date,
                'endDate': date + timedelta(hours=23, minutes=59),
                'value': str(np.random.randint(5000, 15000)),
                'date': date.date()
            })
            
            records.append({
                'type': 'HKQuantityTypeIdentifierHeartRate',
                'sourceName': 'Apple Watch',
                'unit': 'count/min',
                'creationDate': date,
                'startDate': date,
                'endDate': date + timedelta(minutes=1),
                'value': str(np.random.randint(60, 80)),
                'date': date.date()
            })
        
        df = pd.DataFrame(records)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        return df
    
    def test_widget_initialization(self):
        """Test that widget initializes correctly."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Check initialization
            self.assertIsNotNone(widget)
            self.assertEqual(widget._current_month, datetime.now().month)
            self.assertEqual(widget._current_year, datetime.now().year)
            
            # Check that metrics were loaded
            self.assertGreater(len(widget._available_metrics), 0)
            
            # Check UI components
            self.assertTrue(hasattr(widget, 'metric_combo'))
            self.assertTrue(hasattr(widget, 'calendar_heatmap'))
            self.assertTrue(hasattr(widget, 'stats_cards'))
    
    def test_metric_loading(self):
        """Test that metrics are loaded correctly from the database."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Check available metrics
            metrics = widget._available_metrics
            self.assertIsInstance(metrics, list)
            self.assertGreater(len(metrics), 0)
            
            # Check metric structure (should be tuples of (metric, source))
            for metric in metrics:
                self.assertIsInstance(metric, tuple)
                self.assertEqual(len(metric), 2)
    
    def test_data_loading_with_calculator(self):
        """Test data loading when monthly calculator is available."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            # Create calculators
            daily_calc = DailyMetricsCalculator(self.test_data)
            monthly_calc = MonthlyMetricsCalculator(daily_calc)
            
            # Create widget with calculator
            widget = MonthlyDashboardWidget(monthly_calculator=monthly_calc)
            
            # Force data loading
            widget._load_month_data()
            
            # Check that data was loaded
            self.assertIsNotNone(widget.calendar_heatmap._metric_data)
    
    def test_data_loading_without_calculator(self):
        """Test data loading when no calculator is available (sample data generation)."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Force data loading (should generate sample data)
            widget._load_month_data()
            
            # Check that sample data was generated
            self.assertIsNotNone(widget.calendar_heatmap._metric_data)
            self.assertGreater(len(widget.calendar_heatmap._metric_data), 0)
    
    def test_month_navigation(self):
        """Test month navigation functionality."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Test previous month
            current_month = widget._current_month
            current_year = widget._current_year
            
            widget._go_to_previous_month()
            
            if current_month == 1:
                self.assertEqual(widget._current_month, 12)
                self.assertEqual(widget._current_year, current_year - 1)
            else:
                self.assertEqual(widget._current_month, current_month - 1)
                self.assertEqual(widget._current_year, current_year)
            
            # Test next month (should not go to future)
            widget.reset_to_current_month()
            widget._go_to_next_month()
            
            # Should stay at current month (can't go to future)
            self.assertLessEqual(widget._current_year, datetime.now().year)
            if widget._current_year == datetime.now().year:
                self.assertLessEqual(widget._current_month, datetime.now().month)
    
    def test_metric_conversion(self):
        """Test metric value conversion for display."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Test distance conversion (meters to km)
            self.assertEqual(widget._convert_value_for_display(5000, "DistanceWalkingRunning"), 5.0)
            
            # Test sleep conversion (seconds to hours)
            self.assertEqual(widget._convert_value_for_display(28800, "SleepAnalysis"), 8.0)
            
            # Test exercise time conversion (seconds to minutes)
            self.assertEqual(widget._convert_value_for_display(1800, "AppleExerciseTime"), 30.0)
            
            # Test no conversion (steps)
            self.assertEqual(widget._convert_value_for_display(10000, "StepCount"), 10000)
    
    def test_summary_statistics_update(self):
        """Test that summary statistics are calculated correctly."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Test with sample data
            test_data = {
                date(2024, 1, 1): 5000,
                date(2024, 1, 2): 6000,
                date(2024, 1, 3): 7000,
                date(2024, 1, 4): 8000,
                date(2024, 1, 5): 9000,
            }
            
            widget._update_summary_stats(test_data)
            
            # Check that stats were updated
            avg_text = widget.stats_cards["average"].value_label.text()
            self.assertIn("7,000", avg_text)  # Average should be 7000
            
            total_text = widget.stats_cards["total"].value_label.text()
            self.assertIn("35,000", total_text)  # Total should be 35000
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Update with empty data
            widget._update_summary_stats({})
            
            # Check that stats show empty state
            for card in widget.stats_cards.values():
                self.assertEqual(card.value_label.text(), "--")
    
    def test_metric_selection_change(self):
        """Test changing selected metric."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Change metric
            if widget.metric_combo.count() > 1:
                widget.metric_combo.setCurrentIndex(1)
                
                # Check that metric changed
                new_metric = widget.metric_combo.itemData(1)
                self.assertEqual(widget._current_metric, new_metric)
    
    def test_sample_data_generation(self):
        """Test that sample data generation produces reasonable values."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Set different metrics and test sample data
            test_metrics = [
                ("StepCount", 3000, 15000),
                ("HeartRate", 60, 80),
                ("SleepAnalysis", 6, 9),
            ]
            
            for metric, min_expected, max_expected in test_metrics:
                widget._current_metric = (metric, None)
                sample_data = widget._generate_sample_data()
                
                self.assertGreater(len(sample_data), 0)
                
                # Check values are in expected range
                for value in sample_data.values():
                    self.assertGreaterEqual(value, min_expected * 0.7)  # Allow for weekend factor
                    self.assertLessEqual(value, max_expected * 1.1)  # Allow for noise
    
    def test_calendar_style_switching(self):
        """Test switching between calendar styles."""
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase', return_value=self.mock_health_db):
            widget = MonthlyDashboardWidget()
            
            # Test classic style
            widget._set_calendar_style("classic")
            self.assertEqual(widget.calendar_heatmap._view_mode, "month_grid")
            self.assertTrue(widget.classic_btn.isChecked())
            self.assertFalse(widget.github_btn.isChecked())
            
            # Test github style
            widget._set_calendar_style("github")
            self.assertEqual(widget.calendar_heatmap._view_mode, "github_style")
            self.assertFalse(widget.classic_btn.isChecked())
            self.assertTrue(widget.github_btn.isChecked())


class TestMonthlyDashboardIntegration(unittest.TestCase):
    """Integration tests for monthly dashboard with real data flow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for widget tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def test_full_data_flow_integration(self):
        """Test complete data flow from database to display."""
        # Create test data
        test_data = pd.DataFrame({
            'type': ['HKQuantityTypeIdentifierStepCount'] * 30,
            'sourceName': ['iPhone'] * 30,
            'unit': ['count'] * 30,
            'creationDate': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'startDate': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'endDate': pd.date_range(end=datetime.now(), periods=30, freq='D'),
            'value': [str(x) for x in np.random.randint(5000, 15000, 30)],
            'date': pd.date_range(end=datetime.now(), periods=30, freq='D').date
        })
        test_data['value'] = pd.to_numeric(test_data['value'])
        
        # Create calculators
        daily_calc = DailyMetricsCalculator(test_data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Mock health database
        with patch('src.ui.monthly_dashboard_widget.HealthDatabase') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_available_sources.return_value = ['iPhone']
            mock_db.get_types_for_source.return_value = ['HKQuantityTypeIdentifierStepCount']
            mock_db.get_available_types.return_value = ['HKQuantityTypeIdentifierStepCount']
            mock_db_class.return_value = mock_db
            
            # Create widget
            widget = MonthlyDashboardWidget(monthly_calculator=monthly_calc)
            
            # Force data loading
            widget._load_month_data()
            
            # Verify data was loaded
            self.assertIsNotNone(widget.calendar_heatmap._metric_data)
            self.assertGreater(len(widget.calendar_heatmap._metric_data), 0)
            
            # Verify statistics were calculated
            avg_label = widget.stats_cards["average"].value_label.text()
            self.assertNotEqual(avg_label, "--")
            self.assertNotEqual(avg_label, "0")


if __name__ == '__main__':
    unittest.main(verbosity=2)