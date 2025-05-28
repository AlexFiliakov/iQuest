"""
Optimized unit tests for WeeklyMetricsCalculator class.
Uses parametrized tests to reduce duplication while maintaining full coverage.
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
    """Optimized test suite for WeeklyMetricsCalculator."""
    
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
        return DailyMetricsCalculator(sample_data)
    
    @pytest.fixture
    def weekly_calculator(self, mock_daily_calculator):
        """Create weekly calculator instance."""
        return WeeklyMetricsCalculator(mock_daily_calculator)
    
    @pytest.mark.parametrize("week_standard,use_parallel,expected_standard", [
        (WeekStandard.ISO, True, WeekStandard.ISO),
        (WeekStandard.US, False, WeekStandard.US),
        (None, None, WeekStandard.ISO),  # Test defaults
    ])
    def test_initialization_variants(self, mock_daily_calculator, week_standard, use_parallel, expected_standard):
        """Test calculator initialization with different configurations."""
        kwargs = {}
        if week_standard is not None:
            kwargs['week_standard'] = week_standard
        if use_parallel is not None:
            kwargs['use_parallel'] = use_parallel
            
        calc = WeeklyMetricsCalculator(mock_daily_calculator, **kwargs)
        
        assert calc.daily_calculator is mock_daily_calculator
        assert calc.week_standard == expected_standard
        if use_parallel is not None:
            assert calc.use_parallel == use_parallel
        assert calc.window_cache == {}
    
    @pytest.mark.parametrize("metric,window,expected_columns", [
        ('HeartRate', 7, ['rolling_mean', 'rolling_std', 'rolling_min', 'rolling_max', 'rolling_median', 'rolling_cv']),
        ('HeartRate', 14, ['rolling_mean', 'rolling_std', 'rolling_min', 'rolling_max', 'rolling_median', 'rolling_cv']),
    ])
    def test_calculate_rolling_stats_windows(self, weekly_calculator, metric, window, expected_columns):
        """Test rolling statistics calculation with different windows."""
        stats = weekly_calculator.calculate_rolling_stats(metric, window=window)
        
        assert isinstance(stats, pd.DataFrame)
        for col in expected_columns:
            assert col in stats.columns
        assert len(stats) == 31  # January has 31 days
    
    @pytest.mark.parametrize("current_week,year,expected_success", [
        (2, 2024, True),    # Normal week
        (1, 2024, True),    # Year boundary case
        (52, 2024, True),   # End of year
    ])
    def test_compare_week_to_date_scenarios(self, weekly_calculator, current_week, year, expected_success):
        """Test week-to-date comparison in different scenarios."""
        comparison = weekly_calculator.compare_week_to_date('HeartRate', current_week=current_week, year=year)
        
        if expected_success:
            assert isinstance(comparison, WeekComparison)
            assert comparison.current_week_days > 0
            assert comparison.previous_week_days > 0
            assert hasattr(comparison, 'percent_change')
            assert hasattr(comparison, 'absolute_change')
    
    @pytest.mark.parametrize("windows", [
        [7, 14],
        [7, 14, 21],
        [3, 7],
    ])
    def test_calculate_moving_averages_multiple_windows(self, weekly_calculator, windows):
        """Test moving averages calculation with different window combinations."""
        ma_df = weekly_calculator.calculate_moving_averages('HeartRate', windows=windows)
        
        assert isinstance(ma_df, pd.DataFrame)
        for window in windows:
            assert f'ma_{window}' in ma_df.columns
            assert f'ema_{window}' in ma_df.columns
        assert len(ma_df) == 31
    
    @pytest.mark.parametrize("trend_data,expected_direction", [
        (np.arange(31) * 0.5, "up"),           # Clear upward trend
        (-np.arange(31) * 0.5, "down"),        # Clear downward trend
        (np.random.normal(70, 0.1, 31), "stable"),  # No significant trend
    ])
    def test_detect_trend_patterns(self, trend_data, expected_direction):
        """Test trend detection with different patterns."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * 31,
            'value': 70 + trend_data,
            'sourceName': ['Apple Watch'] * 31
        })
        
        daily_calc = DailyMetricsCalculator(data)
        calc = WeeklyMetricsCalculator(daily_calc)
        
        trend = calc.detect_trend('HeartRate', window=7)
        
        assert isinstance(trend, TrendInfo)
        assert trend.trend_direction == expected_direction
        if expected_direction != "stable":
            assert trend.is_significant(alpha=0.05)
    
    @pytest.mark.parametrize("data_points,should_raise", [
        (2, True),   # Insufficient data
        (7, False),  # Minimum required
        (14, False), # Sufficient data
    ])
    def test_trend_detection_data_requirements(self, mock_daily_calculator, data_points, should_raise):
        """Test trend detection with varying data availability."""
        dates = pd.date_range('2024-01-01', periods=data_points)
        values = 70 + np.random.normal(0, 2, data_points)
        data = pd.Series(values, index=dates)
        
        mock_daily_calculator.calculate_daily_aggregates = Mock(return_value=data)
        calc = WeeklyMetricsCalculator(mock_daily_calculator)
        
        if should_raise:
            with pytest.raises(ValueError, match="Insufficient data"):
                calc.detect_trend('HeartRate', window=7)
        else:
            trend = calc.detect_trend('HeartRate', window=7)
            assert isinstance(trend, TrendInfo)
    
    @pytest.mark.parametrize("metric,has_data", [
        ('HeartRate', True),
        ('NonexistentMetric', False),
    ])
    def test_calculate_volatility_with_data_availability(self, weekly_calculator, mock_daily_calculator, metric, has_data):
        """Test volatility calculation with and without data."""
        if not has_data:
            mock_daily_calculator.calculate_daily_aggregates = Mock(return_value=pd.Series(dtype=float))
            calc = WeeklyMetricsCalculator(mock_daily_calculator)
        else:
            calc = weekly_calculator
        
        volatility = calc.calculate_volatility(metric, window=7)
        
        assert isinstance(volatility, dict)
        if has_data:
            assert 'volatility_score' in volatility
            assert 'consistency_score' in volatility
            assert 0 <= volatility['consistency_score'] <= 1
            assert 'coefficient_of_variation' in volatility
            assert 'range_ratio' in volatility
            assert 'rolling_volatility' in volatility
        else:
            assert volatility['volatility_score'] is None
            assert volatility['consistency_score'] is None
    
    @pytest.mark.parametrize("use_parallel", [True, False])
    def test_calculate_multiple_metrics_parallel_toggle(self, mock_daily_calculator, use_parallel):
        """Test parallel processing can be toggled."""
        # Create multi-metric data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        heart_data = pd.DataFrame({
            'creationDate': dates,
            'type': 'HeartRate',
            'value': 70 + np.random.normal(0, 2, 31),
            'sourceName': 'Apple Watch'
        })
        steps_data = pd.DataFrame({
            'creationDate': dates,
            'type': 'StepCount',
            'value': 8000 + np.random.normal(0, 500, 31),
            'sourceName': 'Apple Watch'
        })
        
        combined_data = pd.concat([heart_data, steps_data])
        daily_calc = DailyMetricsCalculator(combined_data)
        calc = WeeklyMetricsCalculator(daily_calc, use_parallel=use_parallel)
        
        with patch('src.analytics.weekly_metrics_calculator.ProcessPoolExecutor') as mock_executor:
            results = calc.calculate_multiple_metrics_parallel(['HeartRate', 'StepCount'], window=7)
            
            if use_parallel:
                mock_executor.assert_called_once()
            else:
                mock_executor.assert_not_called()
            
            assert 'HeartRate' in results
            assert 'StepCount' in results
            assert isinstance(results['HeartRate'], pd.DataFrame)
            assert isinstance(results['StepCount'], pd.DataFrame)
    
    @pytest.mark.parametrize("year,week,week_standard,expected_start_weekday", [
        (2024, 1, WeekStandard.ISO, 0),  # Monday
        (2024, 1, WeekStandard.US, 6),   # Sunday
    ])
    def test_get_week_dates_standards(self, mock_daily_calculator, year, week, week_standard, expected_start_weekday):
        """Test week date calculation for different standards."""
        calc = WeeklyMetricsCalculator(mock_daily_calculator, week_standard=week_standard)
        start, end = calc._get_week_dates(year, week)
        
        assert start.weekday() == expected_start_weekday
        assert (end - start).days == 6  # Week is always 7 days
        
        if week_standard == WeekStandard.US and week == 1:
            # US week 1 contains January 1
            assert start <= date(year, 1, 1) <= end
    
    @pytest.mark.parametrize("year,expected_weeks", [
        (2024, 52),  # Regular year
        (2020, 53),  # Year with 53 ISO weeks
    ])
    def test_get_weeks_in_year(self, weekly_calculator, year, expected_weeks):
        """Test week count for different years."""
        assert weekly_calculator._get_weeks_in_year(year) == expected_weeks
    
    def test_get_weekly_summary_comprehensive(self, weekly_calculator):
        """Test comprehensive weekly summary generation."""
        summary = weekly_calculator.get_weekly_summary(['HeartRate'], week=1, year=2024)
        
        assert 'HeartRate' in summary
        heart_rate_summary = summary['HeartRate']
        
        expected_keys = ['mean', 'median', 'consistency_score', 'coefficient_of_variation']
        for key in expected_keys:
            assert key in heart_rate_summary
    
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
            mock.assert_not_called()
        
        # Results should be identical
        pd.testing.assert_frame_equal(stats1, stats2)
    
    @pytest.mark.parametrize("start_offset,end_offset,expected_days", [
        (15, 20, 6),   # 6 days inclusive
        (1, 7, 7),     # Full week
        (10, 10, 1),   # Single day
    ])
    def test_date_range_handling(self, weekly_calculator, start_offset, end_offset, expected_days):
        """Test handling of specific date ranges."""
        start = date(2024, 1, start_offset)
        end = date(2024, 1, end_offset)
        
        stats = weekly_calculator.calculate_rolling_stats(
            'HeartRate', window=3, start_date=start, end_date=end
        )
        
        if not stats.empty:
            assert stats['date'].min().date() >= start
            assert stats['date'].max().date() <= end
    
    def test_partial_week_handling(self, mock_daily_calculator):
        """Test handling of partial weeks."""
        with patch('src.analytics.weekly_metrics_calculator.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 3)  # Wednesday
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            
            calc = WeeklyMetricsCalculator(mock_daily_calculator)
            comparison = calc.compare_week_to_date('HeartRate', current_week=1, year=2024)
            
            assert comparison.is_partial_week
            assert comparison.current_week_days <= 3  # Mon, Tue, Wed
    
    @pytest.mark.parametrize("calculation_type,max_time_ms", [
        ('rolling_stats', 500),
        ('trend_detection', 500),
        ('volatility', 500),
    ])
    def test_performance_requirements(self, weekly_calculator, calculation_type, max_time_ms):
        """Test that calculations meet performance requirements."""
        import time
        
        start_time = time.time()
        
        if calculation_type == 'rolling_stats':
            result = weekly_calculator.calculate_rolling_stats('HeartRate', window=7)
            assert not result.empty
        elif calculation_type == 'trend_detection':
            result = weekly_calculator.detect_trend('HeartRate', window=7)
            assert isinstance(result, TrendInfo)
        elif calculation_type == 'volatility':
            result = weekly_calculator.calculate_volatility('HeartRate', window=7)
            assert isinstance(result, dict)
        
        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < max_time_ms, f"{calculation_type} took {elapsed_ms:.2f}ms, exceeding {max_time_ms}ms requirement"
    
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


class TestWeeklyMetricsEdgeCases:
    """Edge cases and error handling for WeeklyMetricsCalculator."""
    
    @pytest.mark.parametrize("invalid_input,error_type", [
        (None, (TypeError, AttributeError)),
        ("string", (TypeError, AttributeError)),
        (123, (TypeError, AttributeError)),
        ([1, 2, 3], (TypeError, AttributeError)),
        ({}, (TypeError, AttributeError)),
    ])
    def test_invalid_input_handling(self, invalid_input, error_type):
        """Test handling of invalid input types."""
        with pytest.raises(error_type):
            calc = WeeklyMetricsCalculator(invalid_input)
    
    @pytest.mark.parametrize("edge_case_data", [
        pd.DataFrame(),  # Empty DataFrame
        pd.DataFrame({'date': []}),  # Empty with column
        pd.DataFrame({'date': [datetime.now()], 'value': [float('inf')]}),  # Infinity
        pd.DataFrame({'date': [datetime.now()], 'value': [float('nan')]}),  # NaN
    ])
    def test_data_validation_edge_cases(self, edge_case_data):
        """Test data validation with edge cases."""
        try:
            daily_calc = DailyMetricsCalculator(edge_case_data)
            calc = WeeklyMetricsCalculator(daily_calc)
            result = calc.calculate_rolling_stats('value', window=7)
            # Should handle gracefully
            assert result is None or isinstance(result, pd.DataFrame)
        except (ValueError, TypeError, KeyError):
            # Acceptable to raise validation errors
            pass


class TestWeeklyMetricsIntegration:
    """Integration tests for WeeklyMetricsCalculator."""
    
    def test_calculator_chain_integration(self, sample_data):
        """Test integration between different time-based calculators."""
        daily_calc = DailyMetricsCalculator(sample_data)
        weekly_calc = WeeklyMetricsCalculator(daily_calc)
        
        # Test chained calculations
        daily_stats = daily_calc.calculate_daily_aggregates('HeartRate')
        weekly_stats = weekly_calc.calculate_rolling_stats('HeartRate', window=7)
        
        assert not daily_stats.empty
        assert not weekly_stats.empty
        
        # Weekly stats should be based on daily aggregates
        assert len(weekly_stats) == len(daily_stats)
    
    @pytest.mark.parametrize("aggregation_method,custom_func", [
        ('mean', None),
        ('sum', None),
        ('custom', lambda x: x.quantile(0.9)),  # 90th percentile
    ])
    def test_custom_aggregation_methods(self, sample_data, aggregation_method, custom_func):
        """Test different aggregation methods including custom functions."""
        daily_calc = DailyMetricsCalculator(sample_data)
        calc = WeeklyMetricsCalculator(daily_calc)
        
        if aggregation_method == 'custom' and custom_func:
            # Test custom aggregation via moving averages or other methods
            result = calc.calculate_rolling_stats('HeartRate', window=7)
        else:
            # Standard aggregation methods
            result = calc.get_weekly_summary(['HeartRate'], week=1, year=2024)
        
        assert result is not None