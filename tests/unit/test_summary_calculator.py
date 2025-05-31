"""Unit tests for the centralized summary calculator.

Tests the SummaryCalculator class that pre-computes metric summaries
during the import process.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime, timedelta
import json

from src.analytics.summary_calculator import SummaryCalculator
from src.data_access import DataAccess


class TestSummaryCalculator(unittest.TestCase):
    """Test cases for SummaryCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock data access
        self.mock_data_access = Mock(spec=DataAccess)
        self.mock_db_manager = Mock()
        self.mock_data_access.db_manager = self.mock_db_manager
        self.mock_db_manager.db_path = ":memory:"
        
        # Create calculator instance
        self.calculator = SummaryCalculator(self.mock_data_access)
        
    def test_calculate_all_summaries_empty_database(self):
        """Test calculation with no data in database."""
        # Mock empty metric discovery
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Calculate summaries
        result = self.calculator.calculate_all_summaries(months_back=1)
        
        # Verify structure
        self.assertIn('daily', result)
        self.assertIn('weekly', result)
        self.assertIn('monthly', result)
        self.assertIn('metadata', result)
        
        # Verify empty results
        self.assertEqual(len(result['daily']), 0)
        self.assertEqual(result['metadata']['metrics_processed'], 0)
        
    def test_calculate_all_summaries_with_metrics(self):
        """Test calculation with multiple metrics."""
        # Mock metric discovery
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Configure different return values for different queries
        def execute_side_effect(query, params=None):
            cursor = MagicMock()
            
            if "SELECT DISTINCT type" in query:
                # Metric discovery query
                cursor.fetchall.return_value = [
                    ('StepCount',),
                    ('HeartRate',)
                ]
            elif "WITH source_aggregates" in query:
                # Daily summary query
                cursor.fetchall.return_value = [
                    ('2024-01-15', 8542.0, 8542.0, 8542.0, 8542.0, 1, 1),
                    ('2024-01-16', 10234.0, 10234.0, 10234.0, 10234.0, 1, 1)
                ]
            elif "strftime('%Y-W%W'" in query:
                # Weekly summary query
                cursor.fetchall.return_value = [
                    ('2024-W03', 59794.0, 8542.0, 10234.0, 7123.0, 7)
                ]
            elif "strftime('%Y-%m'" in query:
                # Monthly summary query
                cursor.fetchall.return_value = [
                    ('2024-01', 264802.0, 8542.0, 15234.0, 3421.0, 31, 1234.5)
                ]
            
            return cursor
            
        mock_conn.execute.side_effect = execute_side_effect
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Track progress updates
        progress_updates = []
        def progress_callback(percentage, message):
            progress_updates.append((percentage, message))
            
        # Calculate summaries
        result = self.calculator.calculate_all_summaries(
            progress_callback=progress_callback,
            months_back=1
        )
        
        # Verify metrics were processed
        self.assertEqual(result['metadata']['metrics_processed'], 2)
        
        # Verify daily summaries
        self.assertIn('StepCount', result['daily'])
        self.assertIn('2024-01-15', result['daily']['StepCount'])
        self.assertEqual(result['daily']['StepCount']['2024-01-15']['sum'], 8542.0)
        
        # Verify weekly summaries
        self.assertIn('StepCount', result['weekly'])
        self.assertIn('2024-W03', result['weekly']['StepCount'])
        self.assertEqual(result['weekly']['StepCount']['2024-W03']['sum'], 59794.0)
        
        # Verify monthly summaries
        self.assertIn('StepCount', result['monthly'])
        self.assertIn('2024-01', result['monthly']['StepCount'])
        self.assertEqual(result['monthly']['StepCount']['2024-01']['sum'], 264802.0)
        
        # Verify progress was reported
        self.assertTrue(len(progress_updates) > 0)
        self.assertEqual(progress_updates[0], (0, "Discovering available metrics..."))
        self.assertEqual(progress_updates[-1], (100, "Summary calculation complete!"))
        
    def test_calculate_with_missing_data(self):
        """Test calculation handles sparse data correctly."""
        # Mock metric discovery
        mock_conn = MagicMock()
        
        def execute_side_effect(query, params=None):
            cursor = MagicMock()
            
            if "SELECT DISTINCT type" in query:
                cursor.fetchall.return_value = [('StepCount',)]
            else:
                # Return empty results for summaries
                cursor.fetchall.return_value = []
            
            return cursor
            
        mock_conn.execute.side_effect = execute_side_effect
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Calculate summaries
        result = self.calculator.calculate_all_summaries(months_back=1)
        
        # Verify metric was attempted but no data found
        self.assertEqual(result['metadata']['metrics_processed'], 1)
        self.assertNotIn('StepCount', result['daily'])  # No data, so not included
        
    def test_progress_callback_updates(self):
        """Test that progress callbacks are called correctly."""
        # Mock single metric
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        def execute_side_effect(query, params=None):
            cursor = MagicMock()
            if "SELECT DISTINCT type" in query:
                cursor.fetchall.return_value = [('StepCount',)]
            else:
                cursor.fetchall.return_value = []
            return cursor
            
        mock_conn.execute.side_effect = execute_side_effect
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Track progress
        progress_updates = []
        def progress_callback(percentage, message):
            progress_updates.append(percentage)
            
        # Calculate
        self.calculator.calculate_all_summaries(progress_callback=progress_callback)
        
        # Verify progress went from 0 to 100
        self.assertEqual(progress_updates[0], 0)
        self.assertEqual(progress_updates[-1], 100)
        
        # Verify intermediate progress
        self.assertTrue(any(0 < p < 100 for p in progress_updates))
        
    def test_handles_database_errors_gracefully(self):
        """Test that database errors are handled properly."""
        # Mock database error
        self.mock_db_manager.get_connection.side_effect = Exception("Database error")
        
        # Should raise the exception
        with self.assertRaises(Exception) as context:
            self.calculator.calculate_all_summaries()
            
        self.assertIn("Database error", str(context.exception))
        
    def test_date_range_calculation(self):
        """Test that date range is calculated correctly."""
        # Mock metric discovery
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Calculate with specific months_back
        result = self.calculator.calculate_all_summaries(months_back=6)
        
        # Verify date range in metadata
        self.assertIn('date_range', result['metadata'])
        end_date = date.fromisoformat(result['metadata']['date_range']['end'])
        start_date = date.fromisoformat(result['metadata']['date_range']['start'])
        
        # Should be approximately 6 months
        self.assertEqual(end_date, date.today())
        self.assertAlmostEqual((end_date - start_date).days, 180, delta=5)


if __name__ == '__main__':
    unittest.main()