"""
Unit tests for WeeklyMetricsCalculator class.
Tests rolling statistics, trend detection, volatility analysis, and week comparisons.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

from src.analytics.weekly_metrics_calculator import (
    WeeklyMetricsCalculator,
    WeekStandard,
    TrendInfo,
    WeekComparison,
    WeeklyMetrics
)
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics


class TestWeeklyMetricsCalculator:
    """Test suite for WeeklyMetricsCalculator."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data for testing."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        data = {
            'creationDate': dates,
            'type': ['HeartRate'] * 31,
            'value': 70 + 5 * np.sin(np.arange(31) * 2 * np.pi / 7) + np.random.normal(0, 2, 31),
            'sourceName': ['Apple Watch'] * 31
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def mock_daily_calculator(self, sample_data):
        """Create mock daily calculator for testing."""
        daily_calc = DailyMetricsCalculator(sample_data)
        return daily_calc
    
    @pytest.fixture
    def weekly_calculator(self, mock_daily_calculator):
        """Create weekly calculator instance."""
        return WeeklyMetricsCalculator(mock_daily_calculator)
    
    def test_initialization(self, mock_daily_calculator):
        """Test calculator initialization."""
        calc = WeeklyMetricsCalculator(mock_daily_calculator)
        assert calc.daily_calculator is mock_daily_calculator
        assert calc.week_standard == WeekStandard.ISO
        assert calc.use_parallel is True
        assert calc.window_cache == {}
    
    def test_initialization_with_us_standard(self, mock_daily_calculator):
        """Test initialization with US week standard."""
        calc = WeeklyMetricsCalculator(mock_daily_calculator, week_standard=WeekStandard.US)
        assert calc.week_standard == WeekStandard.US
    
    def test_calculate_rolling_stats(self, weekly_calculator):
        """Test rolling statistics calculation."""
        stats = weekly_calculator.calculate_rolling_stats('HeartRate', window=7)
        
        assert isinstance(stats, pd.DataFrame)
        assert 'rolling_mean' in stats.columns
        assert 'rolling_std' in stats.columns
        assert 'rolling_min' in stats.columns
        assert 'rolling_max' in stats.columns
        assert 'rolling_median' in stats.columns
        assert 'rolling_cv' in stats.columns
        assert len(stats) == 31  # January has 31 days
    
    def test_calculate_rolling_stats_empty_data(self, mock_daily_calculator):
        """Test rolling stats with no data."""
        # Mock empty daily aggregates
        mock_daily_calculator.calculate_daily_aggregates = Mock(return_value=pd.Series(dtype=float))
        calc = WeeklyMetricsCalculator(mock_daily_calculator)
        
        stats = calc.calculate_rolling_stats('NonexistentMetric')
        assert stats.empty
    
    def test_compare_week_to_date(self, weekly_calculator):
        """Test week-to-date comparison."""
        comparison = weekly_calculator.compare_week_to_date('HeartRate', current_week=2, year=2024)
        
        assert isinstance(comparison, WeekComparison)
        assert comparison.current_week_days > 0
        assert comparison.previous_week_days > 0
        assert hasattr(comparison, 'percent_change')
        assert hasattr(comparison, 'absolute_change')
    
    def test_compare_week_to_date_year_boundary(self, weekly_calculator):
        """Test week comparison across year boundary."""
        # Week 1 of 2024 compared to last week of 2023
        comparison = weekly_calculator.compare_week_to_date('HeartRate', current_week=1, year=2024)
        
        assert isinstance(comparison, WeekComparison)
        # Should handle year boundary correctly
    
    def test_calculate_moving_averages(self, weekly_calculator):
        """Test moving averages calculation."""
        ma_df = weekly_calculator.calculate_moving_averages('HeartRate', windows=[7, 14])
        
        assert isinstance(ma_df, pd.DataFrame)
        assert 'ma_7' in ma_df.columns
        assert 'ma_14' in ma_df.columns
        assert 'ema_7' in ma_df.columns
        assert 'ema_14' in ma_df.columns
        assert len(ma_df) == 31
    
    def test_detect_trend_significant(self, weekly_calculator):
        """Test trend detection with significant trend."""
        # Create data with clear upward trend
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        trend_data = {
            'creationDate': dates,
            'type': ['HeartRate'] * 31,
            'value': 70 + np.arange(31) * 0.5,  # Clear upward trend
            'sourceName': ['Apple Watch'] * 31
        }
        trend_df = pd.DataFrame(trend_data)
        
        daily_calc = DailyMetricsCalculator(trend_df)
        calc = WeeklyMetricsCalculator(daily_calc)
        
        trend = calc.detect_trend('HeartRate', window=7)
        
        assert isinstance(trend, TrendInfo)
        assert trend.slope > 0
        assert trend.trend_direction == "up"
        assert trend.is_significant(alpha=0.05)
    
    def test_detect_trend_insufficient_data(self, mock_daily_calculator):
        """Test trend detection with insufficient data."""
        # Mock insufficient data
        short_data = pd.Series([70, 71], index=pd.date_range('2024-01-01', '2024-01-02'))
        mock_daily_calculator.calculate_daily_aggregates = Mock(return_value=short_data)
        calc = WeeklyMetricsCalculator(mock_daily_calculator)
        
        with pytest.raises(ValueError, match="Insufficient data"):
            calc.detect_trend('HeartRate', window=7)
    
    def test_calculate_volatility(self, weekly_calculator):
        """Test volatility calculation."""
        volatility = weekly_calculator.calculate_volatility('HeartRate', window=7)
        
        assert isinstance(volatility, dict)
        assert 'volatility_score' in volatility
        assert 'consistency_score' in volatility
        assert 0 <= volatility['consistency_score'] <= 1
        assert 'coefficient_of_variation' in volatility
        assert 'range_ratio' in volatility
        assert 'rolling_volatility' in volatility
    
    def test_calculate_volatility_empty_data(self, mock_daily_calculator):
        """Test volatility with no data."""
        mock_daily_calculator.calculate_daily_aggregates = Mock(return_value=pd.Series(dtype=float))
        calc = WeeklyMetricsCalculator(mock_daily_calculator)
        
        volatility = calc.calculate_volatility('NonexistentMetric')
        assert volatility['volatility_score'] is None
        assert volatility['consistency_score'] is None
    
    def test_calculate_multiple_metrics_parallel(self, weekly_calculator):
        """Test parallel processing of multiple metrics."""
        # Add more metric types to the data
        data = weekly_calculator.daily_calculator.data.copy()
        steps_data = data.copy()
        steps_data['type'] = 'StepCount'
        steps_data['value'] = 8000 + np.random.normal(0, 500, len(data))
        
        combined_data = pd.concat([data, steps_data])
        daily_calc = DailyMetricsCalculator(combined_data)
        calc = WeeklyMetricsCalculator(daily_calc, use_parallel=True)
        
        results = calc.calculate_multiple_metrics_parallel(['HeartRate', 'StepCount'], window=7)
        
        assert 'HeartRate' in results
        assert 'StepCount' in results
        assert isinstance(results['HeartRate'], pd.DataFrame)
        assert isinstance(results['StepCount'], pd.DataFrame)
    
    def test_get_week_dates_iso(self, weekly_calculator):
        """Test ISO week date calculation."""
        # ISO week 1 of 2024 starts on Monday, January 1, 2024
        start, end = weekly_calculator._get_week_dates(2024, 1)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 7)
        assert start.weekday() == 0  # Monday
    
    def test_get_week_dates_us(self, mock_daily_calculator):
        """Test US week date calculation."""
        calc = WeeklyMetricsCalculator(mock_daily_calculator, week_standard=WeekStandard.US)
        # US week 1 of 2024 contains January 1
        start, end = calc._get_week_dates(2024, 1)
        assert start.weekday() == 6  # Sunday
        assert start <= date(2024, 1, 1) <= end
    
    def test_get_weeks_in_year(self, weekly_calculator):
        """Test week count for different years."""
        # 2024 has 52 ISO weeks
        assert weekly_calculator._get_weeks_in_year(2024) == 52
        
        # 2020 had 53 ISO weeks
        assert weekly_calculator._get_weeks_in_year(2020) == 53
    
    def test_get_weekly_summary(self, weekly_calculator):
        """Test comprehensive weekly summary."""
        summary = weekly_calculator.get_weekly_summary(['HeartRate'], week=1, year=2024)
        
        assert 'HeartRate' in summary
        heart_rate_summary = summary['HeartRate']
        assert 'mean' in heart_rate_summary
        assert 'median' in heart_rate_summary
        assert 'consistency_score' in heart_rate_summary
        assert 'coefficient_of_variation' in heart_rate_summary
    
    def test_caching_behavior(self, weekly_calculator):
        """Test that results are cached properly."""
        # First call
        stats1 = weekly_calculator.calculate_rolling_stats('HeartRate', window=7)
        
        # Check cache
        cache_key = 'HeartRate_7_None_None'
        assert cache_key in weekly_calculator.window_cache
        
        # Second call should use cache
        with patch.object(weekly_calculator.daily_calculator, 'calculate_daily_aggregates') as mock:
            stats2 = weekly_calculator.calculate_rolling_stats('HeartRate', window=7)
            # Should not call daily calculator again
            mock.assert_not_called()
        
        # Results should be the same
        pd.testing.assert_frame_equal(stats1, stats2)
    
    def test_edge_cases_date_ranges(self, weekly_calculator):
        """Test edge cases with date ranges."""
        # Test with very specific date range
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)
        
        stats = weekly_calculator.calculate_rolling_stats(
            'HeartRate', window=3, start_date=start, end_date=end
        )
        
        assert not stats.empty
        assert stats['date'].min().date() >= start
        assert stats['date'].max().date() <= end
    
    def test_partial_week_handling(self, mock_daily_calculator):
        """Test handling of partial weeks."""
        # Mock today as Wednesday (partial week)
        with patch('src.analytics.weekly_metrics_calculator.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 3)  # Wednesday
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            calc = WeeklyMetricsCalculator(mock_daily_calculator)
            comparison = calc.compare_week_to_date('HeartRate', current_week=1, year=2024)
            
            assert comparison.is_partial_week
            assert comparison.current_week_days <= 3  # Mon, Tue, Wed
    
    def test_parallel_processing_toggle(self, mock_daily_calculator):
        """Test that parallel processing can be disabled."""
        calc = WeeklyMetricsCalculator(mock_daily_calculator, use_parallel=False)
        
        # Should work without parallel processing
        with patch('src.analytics.weekly_metrics_calculator.ProcessPoolExecutor') as mock_executor:
            results = calc.calculate_multiple_metrics_parallel(['HeartRate'], window=7)
            # Should not use ProcessPoolExecutor when disabled
            mock_executor.assert_not_called()
            assert 'HeartRate' in results
    
    def test_performance_requirement(self, weekly_calculator):
        """Test that calculations complete within 500ms as per requirements."""
        import time
        
        # Test rolling stats calculation
        start_time = time.time()
        stats = weekly_calculator.calculate_rolling_stats('HeartRate', window=7)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        assert elapsed_time < 500, f"Rolling stats took {elapsed_time:.2f}ms, exceeding 500ms requirement"
        assert not stats.empty
        
        # Test trend detection
        start_time = time.time()
        trend = weekly_calculator.detect_trend('HeartRate', window=7)
        elapsed_time = (time.time() - start_time) * 1000
        
        assert elapsed_time < 500, f"Trend detection took {elapsed_time:.2f}ms, exceeding 500ms requirement"
        assert isinstance(trend, TrendInfo)
        
        # Test volatility calculation
        start_time = time.time()
        volatility = weekly_calculator.calculate_volatility('HeartRate', window=7)
        elapsed_time = (time.time() - start_time) * 1000
        
        assert elapsed_time < 500, f"Volatility calculation took {elapsed_time:.2f}ms, exceeding 500ms requirement"
        assert isinstance(volatility, dict)
    
    def test_api_compatibility_weekly_metrics(self, sample_data):
        """Test the calculate_weekly_metrics method matches API specification."""
        daily_calc = DailyMetricsCalculator(sample_data)
        calc = WeeklyMetricsCalculator(daily_calc)
        
        week_start = datetime(2024, 1, 1)
        result = calc.calculate_weekly_metrics(sample_data, 'HeartRate', week_start)
        
        # Verify it returns WeeklyMetrics dataclass
        assert isinstance(result, WeeklyMetrics)
        assert result.week_start == week_start
        assert isinstance(result.daily_values, dict)
        assert len(result.daily_values) == 7  # One week of data
        assert result.trend_direction in ['up', 'down', 'stable']
        assert hasattr(result, 'avg')
        assert hasattr(result, 'min')
        assert hasattr(result, 'max')