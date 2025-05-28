"""
Unit tests for MonthlyMetricsCalculator class.
Tests monthly statistics, dual mode support, year-over-year comparisons,
growth rates, and distribution analysis.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
import calendar

from src.analytics.monthly_metrics_calculator import (
    MonthlyMetricsCalculator,
    MonthMode,
    DistributionStats,
    MonthlyComparison,
    GrowthRateInfo,
    MonthlyMetrics
)
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics


class TestMonthlyMetricsCalculator:
    """Test suite for MonthlyMetricsCalculator."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data for testing."""
        # Create 3 months of data with trend
        dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
        n_days = len(dates)
        
        # Create trending data with seasonal pattern
        trend = np.linspace(70, 85, n_days)  # Upward trend
        seasonal = 3 * np.sin(2 * np.pi * np.arange(n_days) / 30)  # Monthly cycle
        noise = np.random.normal(0, 2, n_days)
        values = trend + seasonal + noise
        
        data = {
            'creationDate': dates,
            'type': ['HeartRate'] * n_days,
            'value': values,
            'sourceName': ['Apple Watch'] * n_days
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def leap_year_data(self):
        """Create sample data including leap year February."""
        dates = pd.date_range(start='2024-02-01', end='2024-02-29', freq='D')  # 2024 is leap year
        data = {
            'creationDate': dates,
            'type': ['HeartRate'] * 29,
            'value': np.random.normal(75, 5, 29),
            'sourceName': ['Apple Watch'] * 29
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def multi_year_data(self):
        """Create multi-year data for growth rate testing."""
        dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        n_days = len(dates)
        
        # Create data with compound growth
        base_value = 70
        daily_growth = 0.0003  # Small daily growth
        values = [base_value * (1 + daily_growth) ** i for i in range(n_days)]
        values = np.array(values) + np.random.normal(0, 2, n_days)
        
        data = {
            'creationDate': dates,
            'type': ['Steps'] * n_days,
            'value': values,
            'sourceName': ['iPhone'] * n_days
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def mock_daily_calculator(self, sample_data):
        """Create mock daily calculator for testing."""
        return DailyMetricsCalculator(sample_data)
    
    @pytest.fixture
    def monthly_calculator_calendar(self, mock_daily_calculator):
        """Create monthly calculator in calendar mode."""
        return MonthlyMetricsCalculator(mock_daily_calculator, mode=MonthMode.CALENDAR)
    
    @pytest.fixture
    def monthly_calculator_rolling(self, mock_daily_calculator):
        """Create monthly calculator in rolling mode."""
        return MonthlyMetricsCalculator(mock_daily_calculator, mode=MonthMode.ROLLING)
    
    def test_initialization_calendar_mode(self, mock_daily_calculator):
        """Test calculator initialization in calendar mode."""
        calc = MonthlyMetricsCalculator(mock_daily_calculator, mode=MonthMode.CALENDAR)
        assert calc.mode == MonthMode.CALENDAR
        assert calc.daily_calculator == mock_daily_calculator
        assert calc.use_parallel is True
        assert calc._cache_size == 100
    
    def test_initialization_rolling_mode(self, mock_daily_calculator):
        """Test calculator initialization in rolling mode."""
        calc = MonthlyMetricsCalculator(mock_daily_calculator, mode=MonthMode.ROLLING)
        assert calc.mode == MonthMode.ROLLING
        assert calc.daily_calculator == mock_daily_calculator
    
    def test_calculate_monthly_stats_calendar_mode(self, monthly_calculator_calendar):
        """Test monthly statistics calculation in calendar mode."""
        # Test January 2024
        stats = monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 1)
        
        assert isinstance(stats, MonthlyMetrics)
        assert stats.mode == MonthMode.CALENDAR
        assert stats.count > 0
        assert stats.avg > 0
        assert stats.median > 0
        assert stats.min <= stats.avg <= stats.max
        assert stats.month_start.year == 2024
        assert stats.month_start.month == 1
    
    def test_calculate_monthly_stats_rolling_mode(self, monthly_calculator_rolling):
        """Test monthly statistics calculation in rolling mode."""
        # Test January 2024 (rolling 30-day window)
        stats = monthly_calculator_rolling.calculate_monthly_stats('HeartRate', 2024, 1)
        
        assert isinstance(stats, MonthlyMetrics)
        assert stats.mode == MonthMode.ROLLING
        assert stats.count > 0
        assert stats.avg > 0
    
    def test_month_boundaries_calendar_mode(self, monthly_calculator_calendar):
        """Test month boundary calculation for calendar mode."""
        # Test regular month
        start, end = monthly_calculator_calendar._get_month_boundaries(2024, 1)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)
        
        # Test February in leap year
        start, end = monthly_calculator_calendar._get_month_boundaries(2024, 2)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # Leap year
        
        # Test February in non-leap year
        start, end = monthly_calculator_calendar._get_month_boundaries(2023, 2)
        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)  # Non-leap year
    
    def test_month_boundaries_rolling_mode(self, monthly_calculator_rolling):
        """Test month boundary calculation for rolling mode."""
        start, end = monthly_calculator_rolling._get_month_boundaries(2024, 1)
        # Rolling mode: 30 days ending on 15th
        expected_end = date(2024, 1, 15)
        expected_start = expected_end - timedelta(days=29)
        
        assert start == expected_start
        assert end == expected_end
        assert (end - start).days == 29  # 30 days total
    
    def test_leap_year_handling(self):
        """Test proper handling of leap year February."""
        leap_data = pd.DataFrame({
            'creationDate': pd.date_range('2024-02-01', '2024-02-29', freq='D'),
            'type': ['HeartRate'] * 29,
            'value': np.random.normal(75, 5, 29),
            'sourceName': ['Apple Watch'] * 29
        })
        
        daily_calc = DailyMetricsCalculator(leap_data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc, mode=MonthMode.CALENDAR)
        
        stats = monthly_calc.calculate_monthly_stats('HeartRate', 2024, 2)
        assert stats.count == 29  # All days in leap year February
    
    def test_compare_year_over_year(self):
        """Test year-over-year comparison functionality."""
        # Create multi-year data
        dates = pd.date_range('2022-01-01', '2024-03-31', freq='D')
        n_days = len(dates)
        
        # Create data with clear year-over-year improvement
        years = [d.year for d in dates]
        base_values = [70 if y == 2022 else 75 if y == 2023 else 80 for y in years]
        values = np.array(base_values) + np.random.normal(0, 2, n_days)
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * n_days,
            'value': values,
            'sourceName': ['Apple Watch'] * n_days
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Compare January 2024 vs January 2023
        comparison = monthly_calc.compare_year_over_year('HeartRate', 1, 2024, 1)
        
        assert isinstance(comparison, MonthlyComparison)
        assert comparison.years_compared == 1
        assert comparison.percent_change > 0  # Should show improvement
        assert comparison.current_month_avg > comparison.previous_year_avg
    
    def test_calculate_growth_rate(self):
        """Test compound growth rate calculation."""
        # Create data with steady growth
        dates = pd.date_range('2024-01-01', '2024-06-30', freq='D')
        n_days = len(dates)
        
        # Monthly compound growth of ~2%
        monthly_growth = 0.02
        daily_growth = (1 + monthly_growth) ** (1/30) - 1
        
        values = []
        for i, d in enumerate(dates):
            month_factor = (d.year - 2024) * 12 + (d.month - 1)
            value = 70 * ((1 + monthly_growth) ** month_factor)
            values.append(value + np.random.normal(0, 1))
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['Steps'] * n_days,
            'value': values,
            'sourceName': ['iPhone'] * n_days
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Calculate 6-month growth rate
        growth_info = monthly_calc.calculate_growth_rate('Steps', 6, 2024, 6)
        
        assert isinstance(growth_info, GrowthRateInfo)
        assert growth_info.periods_analyzed >= 2
        assert growth_info.monthly_growth_rate > 0  # Positive growth
        assert 0 < growth_info.annualized_growth_rate < 1  # Reasonable annual rate
    
    def test_distribution_analysis(self, monthly_calculator_calendar):
        """Test distribution statistics calculation."""
        # Create data with known distribution characteristics
        np.random.seed(42)  # For reproducible results
        dates = pd.date_range('2024-01-01', '2024-01-31', freq='D')
        
        # Create right-skewed data
        values = np.random.gamma(2, 2, 31) + 70  # Gamma distribution (right-skewed)
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['TestMetric'] * 31,
            'value': values,
            'sourceName': ['Test'] * 31
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        dist_stats = monthly_calc.analyze_distribution('TestMetric', 2024, 1)
        
        assert isinstance(dist_stats, DistributionStats)
        assert dist_stats.skewness > 0  # Right-skewed
        assert isinstance(dist_stats.kurtosis, float)
        assert isinstance(dist_stats.normality_p_value, float)
        assert isinstance(dist_stats.is_normal, bool)
    
    def test_distribution_analysis_insufficient_data(self, monthly_calculator_calendar):
        """Test distribution analysis with insufficient data."""
        # Create minimal data (less than 8 days)
        dates = pd.date_range('2024-01-01', '2024-01-05', freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['TestMetric'] * 5,
            'value': [70, 71, 72, 73, 74],
            'sourceName': ['Test'] * 5
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        with pytest.raises(ValueError, match="Insufficient data"):
            monthly_calc.analyze_distribution('TestMetric', 2024, 1)
    
    def test_empty_data_handling(self, monthly_calculator_calendar):
        """Test handling of empty data."""
        # Create empty data
        empty_data = pd.DataFrame({
            'creationDate': [],
            'type': [],
            'value': [],
            'sourceName': []
        })
        
        daily_calc = DailyMetricsCalculator(empty_data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        stats = monthly_calc.calculate_monthly_stats('NonExistentMetric', 2024, 1)
        
        assert stats.count == 0
        assert stats.avg == 0.0
        assert stats.median == 0.0
        assert stats.std == 0.0
    
    def test_parallel_processing(self, multi_year_data):
        """Test parallel processing for multiple months."""
        daily_calc = DailyMetricsCalculator(multi_year_data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc, use_parallel=True)
        
        # Test multiple metrics and months
        metrics = ['Steps']
        year_month_pairs = [(2024, 1), (2024, 2), (2024, 3), (2024, 4)]
        
        results = monthly_calc.calculate_multiple_months_parallel(metrics, year_month_pairs)
        
        assert 'Steps' in results
        assert len(results['Steps']) == 4
        
        for year, month in year_month_pairs:
            assert (year, month) in results['Steps']
            assert isinstance(results['Steps'][(year, month)], MonthlyMetrics)
    
    def test_monthly_summary(self, monthly_calculator_calendar):
        """Test comprehensive monthly summary."""
        summary = monthly_calculator_calendar.get_monthly_summary(['HeartRate'], 2024, 1)
        
        assert 'HeartRate' in summary
        metric_summary = summary['HeartRate']
        
        # Check required fields
        required_fields = ['avg', 'median', 'std', 'min', 'max', 'count', 
                          'yoy_percent_change', 'monthly_growth_rate', 'mode']
        for field in required_fields:
            assert field in metric_summary
    
    def test_caching_functionality(self, monthly_calculator_calendar):
        """Test that caching is working correctly."""
        # First call
        stats1 = monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 1)
        
        # Second call should use cache
        stats2 = monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 1)
        
        # Results should be identical
        assert stats1.avg == stats2.avg
        assert stats1.count == stats2.count
        assert stats1.mode == stats2.mode
    
    def test_edge_case_month_transitions(self, monthly_calculator_calendar):
        """Test month boundary edge cases."""
        # Test December to January transition
        stats_dec = monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2023, 12)
        stats_jan = monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 1)
        
        # Both should be valid (even if empty)
        assert isinstance(stats_dec, MonthlyMetrics)
        assert isinstance(stats_jan, MonthlyMetrics)
    
    def test_invalid_month_handling(self, monthly_calculator_calendar):
        """Test handling of invalid month values."""
        with pytest.raises((ValueError, calendar.IllegalMonthError)):
            monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 13)
        
        with pytest.raises((ValueError, calendar.IllegalMonthError)):
            monthly_calculator_calendar.calculate_monthly_stats('HeartRate', 2024, 0)
    
    def test_growth_rate_insufficient_data(self, monthly_calculator_calendar):
        """Test growth rate calculation with insufficient data."""
        # This should handle the case gracefully
        growth_info = monthly_calculator_calendar.calculate_growth_rate('NonExistentMetric', 6, 2024, 6)
        
        assert growth_info.monthly_growth_rate == 0.0
        assert growth_info.periods_analyzed == 0
        assert not growth_info.is_significant
    
    def test_yoy_comparison_no_previous_data(self, monthly_calculator_calendar):
        """Test year-over-year comparison when no previous year data exists."""
        # Use a metric that doesn't exist in the data
        comparison = monthly_calculator_calendar.compare_year_over_year('NonExistentMetric', 1, 2024, 1)
        
        assert comparison.years_compared == 0
        assert comparison.previous_year_avg == 0.0
        assert not comparison.is_significant
        
    @pytest.mark.parametrize("mode", [MonthMode.CALENDAR, MonthMode.ROLLING])
    def test_mode_consistency(self, mock_daily_calculator, mode):
        """Test that mode is consistently applied across calculations."""
        calc = MonthlyMetricsCalculator(mock_daily_calculator, mode=mode)
        stats = calc.calculate_monthly_stats('HeartRate', 2024, 1)
        
        assert stats.mode == mode
        
    def test_performance_requirements_simulation(self):
        """Test performance with simulated large dataset."""
        # Simulate 5 years of daily data
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        n_days = len(dates)
        
        # Create realistic health data
        values = 70 + 10 * np.sin(2 * np.pi * np.arange(n_days) / 365.25) + np.random.normal(0, 5, n_days)
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * n_days,
            'value': values,
            'sourceName': ['Apple Watch'] * n_days
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        # Time the calculation (should be < 5 seconds for 5 years)
        import time
        start_time = time.time()
        
        # Calculate multiple months
        for year in [2022, 2023, 2024]:
            for month in range(1, 13):
                stats = monthly_calc.calculate_monthly_stats('HeartRate', year, month)
                assert isinstance(stats, MonthlyMetrics)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (relaxed for CI)
        assert execution_time < 30  # 30 seconds for CI environments

# Distributed from comprehensive tests

"""
Tests for Monthly Metrics Calculator

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest


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


class TestMonthlyMetricsCalculatorDistributed(BaseCalculatorTest):
    """Additional tests distributed from comprehensive test suite."""
    
    def test_monthly_aggregation_all_methods(self, calculator, sample_data):
        """Test all monthly aggregation methods."""
        methods = ['mean', 'sum', 'max', 'min', 'median']
        
        for method in methods:
            result = calculator.aggregate_by_month(sample_data, 'steps', method)
            assert result is not None
        

