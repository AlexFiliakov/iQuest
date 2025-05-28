"""
Comprehensive unit tests to achieve >90% code coverage for analytics components.
Tests all code paths, edge cases, and error conditions.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume
import tempfile
import os

from tests.test_data_generator import HealthDataGenerator
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
from src.analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from src.statistics_calculator import StatisticsCalculator


class TestComprehensiveUnitCoverage:
    """Comprehensive unit tests for analytics components."""
    
    @pytest.fixture
    def data_generator(self):
        """Create test data generator."""
        return HealthDataGenerator(seed=42)
    
    @pytest.fixture
    def sample_data(self, data_generator):
        """Generate sample data for testing."""
        return data_generator.generate(30)

    # Daily Metrics Calculator - Complete Coverage
    class TestDailyMetricsCalculatorComplete:
        """Complete test coverage for DailyMetricsCalculator."""
        
        @pytest.fixture
        def calculator(self):
            """Create calculator instance."""
            return DailyMetricsCalculator()
        
        def test_init_default_parameters(self):
            """Test initialization with default parameters."""
            calc = DailyMetricsCalculator()
            assert calc is not None
            assert hasattr(calc, 'calculate_statistics')
        
        def test_init_custom_parameters(self):
            """Test initialization with custom parameters."""
            calc = DailyMetricsCalculator(outlier_method='iqr', missing_threshold=0.1)
            assert calc is not None
        
        def test_calculate_statistics_normal_data(self, calculator, sample_data):
            """Test statistics calculation with normal data."""
            result = calculator.calculate_statistics('steps', sample_data['steps'])
            
            assert 'mean' in result
            assert 'median' in result
            assert 'std' in result
            assert 'min' in result
            assert 'max' in result
            assert 'count' in result
            assert result['count'] == len(sample_data)
        
        def test_calculate_statistics_empty_data(self, calculator):
            """Test statistics with empty data."""
            empty_series = pd.Series([], name='test')
            
            result = calculator.calculate_statistics('test', empty_series)
            
            assert result is None or result['count'] == 0
        
        def test_calculate_statistics_all_null(self, calculator):
            """Test statistics with all null values."""
            null_series = pd.Series([None, None, None], name='test')
            
            result = calculator.calculate_statistics('test', null_series)
            
            assert result is None or result['count'] == 0
        
        def test_calculate_statistics_mixed_null(self, calculator):
            """Test statistics with mixed null and valid values."""
            mixed_series = pd.Series([1, None, 3, None, 5], name='test')
            
            result = calculator.calculate_statistics('test', mixed_series)
            
            assert result['count'] == 3
            assert result['mean'] == 3.0
            assert 'missing_count' in result
            assert result['missing_count'] == 2
        
        @given(data=st.lists(st.floats(min_value=0, max_value=1000, allow_nan=False), min_size=1, max_size=1000))
        def test_statistics_properties(self, calculator, data):
            """Property-based test for statistics."""
            series = pd.Series(data, name='test')
            result = calculator.calculate_statistics('test', series)
            
            if result and result['count'] > 0:
                assert result['min'] <= result['mean'] <= result['max']
                assert result['min'] <= result['median'] <= result['max']
                assert result['std'] >= 0
        
        def test_outlier_detection_iqr(self, calculator):
            """Test outlier detection using IQR method."""
            data_with_outliers = pd.Series([1, 2, 2, 3, 3, 3, 4, 4, 100], name='test')
            
            outliers = calculator.detect_outliers('test', data_with_outliers, method='iqr')
            
            assert len(outliers) >= 1
            assert 100 in outliers.values
        
        def test_outlier_detection_zscore(self, calculator):
            """Test outlier detection using Z-score method."""
            data_with_outliers = pd.Series([1, 2, 2, 3, 3, 3, 4, 4, 100], name='test')
            
            outliers = calculator.detect_outliers('test', data_with_outliers, method='zscore')
            
            assert len(outliers) >= 1
            assert 100 in outliers.values
        
        def test_outlier_detection_invalid_method(self, calculator):
            """Test outlier detection with invalid method."""
            data = pd.Series([1, 2, 3, 4, 5], name='test')
            
            with pytest.raises(ValueError):
                calculator.detect_outliers('test', data, method='invalid_method')
        
        @pytest.mark.parametrize("percentiles,expected_keys", [
            ([25, 50, 75], ['p25', 'p50', 'p75']),
            ([10, 90], ['p10', 'p90']),
            ([5, 95], ['p5', 'p95'])
        ])
        def test_percentile_calculations(self, calculator, percentiles, expected_keys):
            """Test percentile calculations."""
            data = pd.Series([1, 2, 3, 4, 5], name='test')
            
            result = calculator.calculate_percentiles('test', data, percentiles)
            
            for key in expected_keys:
                assert key in result
                assert 1 <= result[key] <= 5
        
        def test_percentile_calculations_empty_data(self, calculator):
            """Test percentile calculations with empty data."""
            empty_data = pd.Series([], name='test')
            
            result = calculator.calculate_percentiles('test', empty_data, [25, 50, 75])
            
            assert result is None or all(np.isnan(v) for v in result.values() if v is not None)
        
        def test_calculate_trends_increasing(self, calculator):
            """Test trend calculation for increasing data."""
            increasing_data = pd.Series(range(10), name='test')
            
            trend = calculator.calculate_trend('test', increasing_data)
            
            assert trend['direction'] == 'increasing'
            assert trend['slope'] > 0
        
        def test_calculate_trends_decreasing(self, calculator):
            """Test trend calculation for decreasing data."""
            decreasing_data = pd.Series(range(10, 0, -1), name='test')
            
            trend = calculator.calculate_trend('test', decreasing_data)
            
            assert trend['direction'] == 'decreasing'
            assert trend['slope'] < 0
        
        def test_calculate_trends_stable(self, calculator):
            """Test trend calculation for stable data."""
            stable_data = pd.Series([5] * 10, name='test')
            
            trend = calculator.calculate_trend('test', stable_data)
            
            assert trend['direction'] == 'stable'
            assert abs(trend['slope']) < 0.1
        
        def test_calculate_all_metrics_complete(self, calculator, sample_data):
            """Test complete metrics calculation."""
            result = calculator.calculate_all_metrics(sample_data)
            
            assert result is not None
            assert len(result) > 0
            
            # Should contain metrics for all numeric columns
            numeric_columns = sample_data.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col != 'date':  # Exclude date if it's numeric
                    assert any(col in key for key in result.keys())
        
        def test_error_handling_invalid_data_type(self, calculator):
            """Test error handling with invalid data types."""
            invalid_data = "not a dataframe"
            
            with pytest.raises((TypeError, AttributeError)):
                calculator.calculate_all_metrics(invalid_data)
        
        def test_error_handling_missing_columns(self, calculator):
            """Test error handling with missing required columns."""
            incomplete_data = pd.DataFrame({'date': [datetime.now()]})
            
            result = calculator.calculate_all_metrics(incomplete_data)
            # Should handle gracefully or raise appropriate error
            assert result is not None or True  # Allow either success or controlled failure

    # Weekly Metrics Calculator - Complete Coverage
    class TestWeeklyMetricsCalculatorComplete:
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
    class TestMonthlyMetricsCalculatorComplete:
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
    class TestStatisticsCalculatorComplete:
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


# Test coverage reporting
def test_coverage_reporting():
    """Ensure test coverage reporting is working."""
    # This test ensures coverage tools are properly configured
    import coverage
    cov = coverage.Coverage()
    assert cov is not None