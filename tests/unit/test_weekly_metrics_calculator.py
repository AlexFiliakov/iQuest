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

# Distributed from comprehensive tests

"""
Tests for Weekly Metrics Calculator

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest


class TestWeeklyMetricsCalculatorComplete(BaseCalculatorTest):
    """Complete test coverage for WeeklyMetricsCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return WeeklyMetricsCalculator()
    
    def test_week_aggregation_methods(self, calculator, sample_data):
        """Test different week aggregation methods."""
        methods = ['mean', 'sum', 'max', 'min']
        
        for method in methods:
            result = calculator.aggregate_by_week(sample_data, 'steps', method)
            assert result is not None
            assert len(result) > 0
    
    def test_week_aggregation_invalid_method(self, calculator, sample_data):
        """Test week aggregation with invalid method."""
        with pytest.raises(ValueError):
            calculator.aggregate_by_week(sample_data, 'steps', 'invalid_method')
    
    def test_week_over_week_comparison(self, calculator, sample_data):
        """Test week-over-week comparison calculations."""
        result = calculator.calculate_week_over_week_change(sample_data, 'steps')
        
        assert result is not None
        assert 'current_week' in result
        assert 'previous_week' in result
        assert 'change_percent' in result
    
    def test_insufficient_data_for_comparison(self, calculator):
        """Test handling of insufficient data for week comparison."""
        insufficient_data = pd.DataFrame({
            'date': [datetime.now()],
            'steps': [5000]
        })
        
        result = calculator.calculate_week_over_week_change(insufficient_data, 'steps')
        
        assert result is None or 'insufficient_data' in result


# Monthly Metrics Calculator - Complete Coverage  
class TestMonthlyMetricsCalculatorComplete(BaseCalculatorTest):
    """Complete test coverage for MonthlyMetricsCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return MonthlyMetricsCalculator()
    
    def test_monthly_aggregation_all_methods(self, calculator, sample_data):
        """Test all monthly aggregation methods."""
        methods = ['mean', 'sum', 'max', 'min', 'median']
        
        for method in methods:
            result = calculator.aggregate_by_month(sample_data, 'steps', method)
            assert result is not None
    
    def test_seasonal_pattern_detection(self, calculator, data_generator):
        """Test seasonal pattern detection."""
        # Generate full year of data
        yearly_data = data_generator.generate(365)
        
        patterns = calculator.detect_seasonal_patterns(yearly_data, 'steps')
        
        assert patterns is not None
        assert 'seasonal_strength' in patterns
    
    def test_month_over_month_trends(self, calculator, data_generator):
        """Test month-over-month trend calculations."""
        multi_month_data = data_generator.generate(90)  # 3 months
        
        trends = calculator.calculate_monthly_trends(multi_month_data, 'steps')
        
        assert trends is not None
        assert len(trends) >= 2  # At least 2 months for comparison


# Statistics Calculator - Complete Coverage
class TestStatisticsCalculatorComplete(BaseCalculatorTest):
    """Complete test coverage for StatisticsCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return StatisticsCalculator()
    
    def test_descriptive_statistics_complete(self, calculator):
        """Test all descriptive statistics."""
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        stats = calculator.calculate_descriptive_stats(data)
        
        expected_keys = ['mean', 'median', 'mode', 'std', 'var', 'skewness', 'kurtosis',
                       'min', 'max', 'range', 'q1', 'q3', 'iqr']
        
        for key in expected_keys:
            assert key in stats
    
    def test_correlation_analysis_complete(self, calculator, sample_data):
        """Test complete correlation analysis."""
        numeric_cols = sample_data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) >= 2:
            correlations = calculator.calculate_correlation_matrix(
                sample_data[numeric_cols.tolist()]
            )
            
            assert correlations is not None
            assert correlations.shape[0] == correlations.shape[1]
    
    def test_distribution_analysis(self, calculator):
        """Test distribution analysis methods."""
        normal_data = pd.Series(np.random.normal(0, 1, 1000))
        
        distribution_stats = calculator.analyze_distribution(normal_data)
        
        assert 'normality_test' in distribution_stats
        assert 'distribution_type' in distribution_stats
    
    def test_time_series_analysis(self, calculator, sample_data):
        """Test time series analysis methods."""
        if 'date' in sample_data.columns:
            ts_analysis = calculator.analyze_time_series(
                sample_data['date'], 
                sample_data['steps']
            )
            
            assert ts_analysis is not None
            assert 'trend' in ts_analysis
            assert 'seasonality' in ts_analysis
    
    def test_statistical_tests(self, calculator):
        """Test various statistical tests."""
        group1 = pd.Series(np.random.normal(10, 2, 100))
        group2 = pd.Series(np.random.normal(12, 2, 100))
        
        test_results = calculator.perform_statistical_tests(group1, group2)
        
        assert 't_test' in test_results
        assert 'mann_whitney' in test_results
    
    def test_confidence_intervals(self, calculator):
        """Test confidence interval calculations."""
        data = pd.Series(np.random.normal(100, 15, 50))
        
        ci_95 = calculator.calculate_confidence_interval(data, confidence=0.95)
        ci_99 = calculator.calculate_confidence_interval(data, confidence=0.99)
        
        assert ci_95['lower'] < ci_95['upper']
        assert ci_99['lower'] < ci_99['upper']
        # 99% CI should be wider than 95% CI
        assert (ci_99['upper'] - ci_99['lower']) > (ci_95['upper'] - ci_95['lower'])
    
    def test_bootstrap_statistics(self, calculator):
        """Test bootstrap statistical methods."""
        data = pd.Series(np.random.normal(50, 10, 100))
        
        bootstrap_stats = calculator.bootstrap_statistics(
            data, 
            statistic=np.mean, 
            n_bootstrap=1000
        )
        
        assert 'estimate' in bootstrap_stats
        assert 'confidence_interval' in bootstrap_stats
        assert 'standard_error' in bootstrap_stats


# Error Handling and Edge Cases
class TestErrorHandlingComplete:
    """Test comprehensive error handling."""
    
    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        calc = DailyMetricsCalculator()
        
        invalid_inputs = [None, "string", 123, [1, 2, 3], {}]
        
        for invalid_input in invalid_inputs:
            with pytest.raises((TypeError, AttributeError, ValueError)):
                calc.calculate_all_metrics(invalid_input)
    
    def test_memory_efficient_processing(self, data_generator):
        """Test memory-efficient processing of large datasets."""
        calc = DailyMetricsCalculator()
        
        # Process in chunks to test memory efficiency
        large_data = data_generator.generate_performance_data('large')
        
        # Should complete without memory errors
        result = calc.calculate_all_metrics(large_data)
        assert result is not None
    
    def test_thread_safety(self, data_generator):
        """Test thread safety of calculators."""
        calc = DailyMetricsCalculator()
        data = data_generator.generate(100)
        
        import threading
        results = []
        
        def calculate():
            result = calc.calculate_all_metrics(data.copy())
            results.append(result)
        
        threads = [threading.Thread(target=calculate) for _ in range(3)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 3
        assert all(r is not None for r in results)
    
    def test_data_validation_edge_cases(self):
        """Test data validation with edge cases."""
        calc = DailyMetricsCalculator()
        
        edge_cases = [
            pd.DataFrame(),  # Empty DataFrame
            pd.DataFrame({'date': []}),  # Empty with column
            pd.DataFrame({'date': [datetime.now()], 'steps': [float('inf')]}),  # Infinity
            pd.DataFrame({'date': [datetime.now()], 'steps': [float('nan')]}),  # NaN
        ]
        
        for edge_case in edge_cases:
            try:
                result = calc.calculate_all_metrics(edge_case)
                # Should handle gracefully
                assert result is None or isinstance(result, dict)
            except (ValueError, TypeError):
                # Acceptable to raise validation errors
                pass


# Integration with Other Components
class TestComponentIntegration:
    """Test integration between analytics components."""
    
    def test_calculator_chain_integration(self, sample_data):
        """Test integration between different calculators."""
        daily_calc = DailyMetricsCalculator()
        weekly_calc = WeeklyMetricsCalculator()
        monthly_calc = MonthlyMetricsCalculator()
        
        # Chain calculations
        daily_results = daily_calc.calculate_all_metrics(sample_data)
        weekly_results = weekly_calc.calculate_weekly_trends(sample_data)
        monthly_results = monthly_calc.calculate_monthly_summary(sample_data)
        
        # All should produce compatible results
        assert daily_results is not None
        assert weekly_results is not None
        assert monthly_results is not None
    
    def test_statistics_calculator_integration(self, sample_data):
        """Test integration with statistics calculator."""
        daily_calc = DailyMetricsCalculator()
        stats_calc = StatisticsCalculator()
        
        daily_results = daily_calc.calculate_all_metrics(sample_data)
        
        if daily_results and 'steps_mean' in daily_results:
            # Use daily results for further statistical analysis
            detailed_stats = stats_calc.calculate_descriptive_stats(sample_data['steps'])
            
            assert detailed_stats is not None
            # Results should be consistent
            assert abs(detailed_stats['mean'] - daily_results['steps_mean']) < 0.01


# Configuration and Customization Tests
class TestConfigurationComplete:
    """Test configuration and customization options."""
    
    def test_custom_outlier_thresholds(self, sample_data):
        """Test custom outlier detection thresholds."""
        strict_calc = DailyMetricsCalculator(outlier_threshold=2.0)  # Strict
        lenient_calc = DailyMetricsCalculator(outlier_threshold=4.0)  # Lenient
        
        strict_outliers = strict_calc.detect_outliers('steps', sample_data['steps'])
        lenient_outliers = lenient_calc.detect_outliers('steps', sample_data['steps'])
        
        # Strict should find more outliers
        assert len(strict_outliers) >= len(lenient_outliers)
    
    def test_custom_aggregation_methods(self, sample_data):
        """Test custom aggregation methods."""
        calc = WeeklyMetricsCalculator()
        
        # Test with custom aggregation function
        def custom_agg(x):
            return x.quantile(0.9)  # 90th percentile
        
        result = calc.aggregate_by_week(sample_data, 'steps', custom_agg)
        assert result is not None
    
    def test_configuration_persistence(self):
        """Test that configuration persists across calculations."""
        calc = DailyMetricsCalculator(
            outlier_method='zscore',
            outlier_threshold=2.5,
            missing_threshold=0.2
        )
        
        # Configuration should persist
        assert calc.outlier_method == 'zscore'
        assert calc.outlier_threshold == 2.5
        assert calc.missing_threshold == 0.2


class TestWeeklyMetricsCalculatorDistributed(BaseCalculatorTest):
    """Additional tests distributed from comprehensive test suite."""
    
    def test_custom_aggregation_methods(self, sample_data):
        """Test custom aggregation methods."""
        calc = WeeklyMetricsCalculator()
        
        # Test with custom aggregation function
        def custom_agg(x):
            return x.quantile(0.9)  # 90th percentile
        
        result = calc.aggregate_by_week(sample_data, 'steps', custom_agg)
        assert result is not None
        

