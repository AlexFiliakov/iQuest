"""
Test mock objects compliance with interfaces.
Ensures mocks properly implement required protocols.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from tests.mocks.data_sources import MockDataSource, EmptyDataSource, LargeDataSource, CorruptDataSource
from tests.fixtures.factories import FixtureFactory
from src.analytics.data_source_protocol import DataSourceProtocol


class TestMockCompliance:
    """Verify mocks implement required interfaces correctly."""
    
    def test_mock_implements_protocol(self):
        """Verify MockDataSource implements DataSourceProtocol."""
        data = FixtureFactory.create_health_data(days=7)
        mock = MockDataSource(data)
        
        # Check all protocol methods exist
        assert hasattr(mock, 'get_dataframe')
        assert hasattr(mock, 'get_data_for_period')
        assert hasattr(mock, 'get_available_metrics')
        assert hasattr(mock, 'get_date_range')
        
        # Verify return types
        df = mock.get_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert 'creationDate' in df.columns
        assert 'type' in df.columns
        assert 'value' in df.columns
        
        # Test get_available_metrics
        metrics = mock.get_available_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert all(isinstance(m, str) for m in metrics)
        
        # Test get_date_range
        date_range = mock.get_date_range()
        assert date_range is not None
        assert isinstance(date_range, tuple)
        assert len(date_range) == 2
        assert isinstance(date_range[0], (datetime, pd.Timestamp))
        assert isinstance(date_range[1], (datetime, pd.Timestamp))
    
    def test_empty_data_source_compliance(self):
        """Verify EmptyDataSource handles empty data correctly."""
        mock = EmptyDataSource()
        
        # Should return empty DataFrame
        df = mock.get_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        # Should have at least the required columns
        required_cols = {'creationDate', 'type', 'value'}
        assert required_cols.issubset(set(df.columns))
        
        # Should return empty list
        metrics = mock.get_available_metrics()
        assert metrics == []
        
        # Should return None for date range
        date_range = mock.get_date_range()
        assert date_range is None
    
    def test_large_data_source_performance(self):
        """Verify LargeDataSource generates data efficiently."""
        mock = LargeDataSource(days=365)
        
        # Should have substantial data
        df = mock.get_dataframe()
        assert len(df) > 365  # At least one entry per day
        
        # Should have multiple metrics
        metrics = mock.get_available_metrics()
        assert len(metrics) >= 4
        
        # Date range should span full year
        date_range = mock.get_date_range()
        assert date_range is not None
        delta = date_range[1] - date_range[0]
        assert delta.days >= 364  # Allow for edge cases
    
    def test_mock_data_consistency(self):
        """Verify mock data maintains consistency."""
        data = FixtureFactory.create_health_data(days=30)
        mock = MockDataSource(data)
        
        # Multiple calls should return copies, not references
        df1 = mock.get_dataframe()
        df2 = mock.get_dataframe()
        
        # Modify df1
        df1.loc[0, 'value'] = -999
        
        # df2 should be unaffected
        assert df2.loc[0, 'value'] != -999
    
    def test_get_data_for_period(self):
        """Test period-based data retrieval."""
        mock = LargeDataSource(days=30)
        
        # Get available metrics
        metrics = mock.get_available_metrics()
        metric = metrics[0]
        
        # Get data for specific period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        period_data = mock.get_data_for_period(metric, start_date, end_date)
        
        assert isinstance(period_data, pd.Series)
        assert len(period_data) > 0
        assert period_data.index.name == 'creationDate'
        
        # All dates should be within range
        for date in period_data.index:
            assert start_date <= date <= end_date
    
    def test_mock_with_calculator_integration(self):
        """Test mock works with DailyMetricsCalculator."""
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        
        # Create mock with known data
        mock = LargeDataSource(days=30)
        
        # Should work with calculator
        calculator = DailyMetricsCalculator(mock)
        
        # Get metrics summary
        metrics = mock.get_available_metrics()
        summary = calculator.get_metrics_summary(metrics[:1])
        
        assert len(summary) == 1
        stats = summary[metrics[0]]
        assert stats.count > 0
        assert stats.mean is not None
        assert stats.median is not None
    
    def test_fixture_factory_integration(self):
        """Test FixtureFactory creates compatible data."""
        # Test various factory methods
        data_source = FixtureFactory.create_data_source(days=7)
        assert isinstance(data_source, MockDataSource)
        
        # Weekly data
        weekly_df = FixtureFactory.create_weekly_data()
        weekly_source = MockDataSource(weekly_df)
        assert len(weekly_source.get_available_metrics()) > 0
        
        # Monthly data
        monthly_df = FixtureFactory.create_monthly_data()
        monthly_source = MockDataSource(monthly_df)
        date_range = monthly_source.get_date_range()
        assert date_range is not None
        delta = date_range[1] - date_range[0]
        assert 28 <= delta.days <= 31  # Month range
    
    def test_corrupt_data_handling(self):
        """Test CorruptDataSource for error testing."""
        mock = CorruptDataSource()
        
        # Should still return a DataFrame
        df = mock.get_dataframe()
        assert isinstance(df, pd.DataFrame)
        
        # Should have corrupt data
        assert df['creationDate'].isna().any() or df['creationDate'].astype(str).str.contains('invalid').any()
        assert df['value'].isna().any() or not pd.api.types.is_numeric_dtype(df['value'])
    
    def test_mock_immutability(self):
        """Test that mock data is immutable from external changes."""
        original_data = FixtureFactory.create_health_data(days=7)
        mock = MockDataSource(original_data)
        
        # Modify original data
        original_data.loc[0, 'value'] = -999
        
        # Mock should have original values
        mock_df = mock.get_dataframe()
        assert mock_df.loc[0, 'value'] != -999


class TestCalculatorIntegration:
    """Test calculators work correctly with mock data sources."""
    
    def test_daily_calculator_with_mock(self):
        """Test DailyMetricsCalculator with MockDataSource."""
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        
        # Create realistic data
        data = FixtureFactory.create_health_data(
            days=30,
            metrics=['HKQuantityTypeIdentifierStepCount']
        )
        mock = MockDataSource(data)
        
        # Create calculator
        calculator = DailyMetricsCalculator(mock)
        
        # Calculate statistics
        stats = calculator.calculate_statistics('HKQuantityTypeIdentifierStepCount')
        
        assert stats.count > 0
        assert stats.mean > 0
        assert stats.std >= 0
        assert stats.min <= stats.mean <= stats.max
    
    def test_weekly_calculator_with_mock(self):
        """Test WeeklyMetricsCalculator with mock chain."""
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
        
        # Create data source
        mock = LargeDataSource(days=60)
        
        # Create calculator chain
        daily = DailyMetricsCalculator(mock)
        weekly = WeeklyMetricsCalculator(daily)
        
        # Should be able to calculate rolling stats
        metric = mock.get_available_metrics()[0]
        result = weekly.calculate_rolling_stats(metric, window=7)
        
        assert result is not None
        assert len(result) > 0
    
    def test_monthly_calculator_with_mock(self):
        """Test MonthlyMetricsCalculator with mock chain."""
        from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
        from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
        
        # Create data source
        mock = LargeDataSource(days=90)
        
        # Create calculator chain
        daily = DailyMetricsCalculator(mock)
        monthly = MonthlyMetricsCalculator(daily)
        
        # Should be able to calculate monthly stats
        metric = mock.get_available_metrics()[0]
        result = monthly.calculate_monthly_stats(metric, 2024, 3)
        
        assert result is not None