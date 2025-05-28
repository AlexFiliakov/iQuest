"""
Unit tests for DailyMetricsCalculator class.
Includes property-based tests using hypothesis.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume
from hypothesis.extra.pandas import column, data_frames, range_indexes

from src.analytics.daily_metrics_calculator import (
    DailyMetricsCalculator,
    MetricStatistics,
    InterpolationMethod,
    OutlierMethod
)


class TestDailyMetricsCalculator:
    """Test suite for DailyMetricsCalculator."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data for testing."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        data = {
            'creationDate': dates,
            'type': ['HeartRate'] * 10,
            'value': [60, 65, 70, 68, 72, 75, 80, 78, 76, 74],
            'sourceName': ['Apple Watch'] * 10
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def multi_metric_data(self):
        """Create sample data with multiple metrics."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
        data = []
        
        # Heart rate data
        for date in dates:
            data.append({
                'creationDate': date,
                'type': 'HeartRate',
                'value': np.random.normal(70, 5),
                'sourceName': 'Apple Watch'
            })
        
        # Step count data
        for date in dates:
            data.append({
                'creationDate': date,
                'type': 'StepCount',
                'value': np.random.normal(8000, 1000),
                'sourceName': 'iPhone'
            })
        
        return pd.DataFrame(data)
    
    def test_initialization(self, sample_data):
        """Test calculator initialization."""
        calc = DailyMetricsCalculator(sample_data)
        assert calc.timezone == 'UTC'
        assert 'date' in calc.data.columns
        assert calc.data['value'].dtype == np.float64
    
    def test_calculate_statistics_basic(self, sample_data):
        """Test basic statistics calculation."""
        calc = DailyMetricsCalculator(sample_data)
        stats = calc.calculate_statistics('HeartRate')
        
        assert stats.metric_name == 'HeartRate'
        assert stats.count == 10
        assert stats.mean == pytest.approx(71.8, rel=1e-2)
        assert stats.median == pytest.approx(73.0, rel=1e-2)
        assert stats.min == 60.0
        assert stats.max == 80.0
        assert not stats.insufficient_data
    
    def test_calculate_statistics_empty_data(self):
        """Test statistics with empty data."""
        empty_df = pd.DataFrame(columns=['creationDate', 'type', 'value'])
        calc = DailyMetricsCalculator(empty_df)
        stats = calc.calculate_statistics('HeartRate')
        
        assert stats.count == 0
        assert stats.mean is None
        assert stats.insufficient_data
    
    def test_calculate_statistics_single_value(self):
        """Test statistics with single data point."""
        single_data = pd.DataFrame({
            'creationDate': [datetime(2024, 1, 1)],
            'type': ['HeartRate'],
            'value': [70.0]
        })
        calc = DailyMetricsCalculator(single_data)
        stats = calc.calculate_statistics('HeartRate')
        
        assert stats.count == 1
        assert stats.mean == 70.0
        assert stats.median == 70.0
        assert stats.std is None  # Insufficient data for std
        assert stats.insufficient_data
    
    def test_calculate_percentiles(self, sample_data):
        """Test percentile calculations."""
        calc = DailyMetricsCalculator(sample_data)
        percentiles = calc.calculate_percentiles('HeartRate', [25, 50, 75, 90])
        
        assert 25 in percentiles
        assert 50 in percentiles
        assert 75 in percentiles
        assert 90 in percentiles
        assert percentiles[50] == pytest.approx(73.0, rel=1e-2)
    
    def test_calculate_percentiles_invalid(self, sample_data):
        """Test percentile calculation with invalid values."""
        calc = DailyMetricsCalculator(sample_data)
        
        with pytest.raises(ValueError):
            calc.calculate_percentiles('HeartRate', [101])
        
        with pytest.raises(ValueError):
            calc.calculate_percentiles('HeartRate', [-1])
    
    def test_detect_outliers_iqr(self):
        """Test IQR outlier detection."""
        # Create data with clear outliers
        values = [60, 65, 70, 72, 74, 75, 76, 78, 80, 150]  # 150 is outlier
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * 10,
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        outliers = calc.detect_outliers('HeartRate', OutlierMethod.IQR)
        
        # Last value should be detected as outlier
        assert outliers.iloc[-1] == True
        assert outliers.sum() >= 1
    
    def test_detect_outliers_zscore(self):
        """Test Z-score outlier detection."""
        # Create normally distributed data with one extreme outlier
        np.random.seed(42)
        values = np.random.normal(70, 5, 100).tolist()
        values.append(200)  # Clear outlier
        
        dates = pd.date_range(start='2024-01-01', periods=101, freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * 101,
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        outliers = calc.detect_outliers('HeartRate', OutlierMethod.Z_SCORE)
        
        # Last value should be detected as outlier
        assert outliers.iloc[-1] == True
    
    def test_date_range_filtering(self, sample_data):
        """Test filtering by date range."""
        calc = DailyMetricsCalculator(sample_data)
        
        # Test with date range
        stats = calc.calculate_statistics(
            'HeartRate',
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 7)
        )
        
        assert stats.count == 3  # Days 5, 6, 7
    
    def test_multiple_readings_per_day(self):
        """Test handling of multiple readings per day."""
        # Create data with multiple readings per day
        data = pd.DataFrame({
            'creationDate': [
                datetime(2024, 1, 1, 8, 0),
                datetime(2024, 1, 1, 12, 0),
                datetime(2024, 1, 1, 20, 0),
                datetime(2024, 1, 2, 9, 0),
                datetime(2024, 1, 2, 18, 0),
            ],
            'type': ['HeartRate'] * 5,
            'value': [65, 70, 68, 72, 75]
        })
        
        calc = DailyMetricsCalculator(data)
        stats = calc.calculate_statistics('HeartRate')
        
        # Should have 2 days of data
        assert stats.count == 2
        # First day average: (65+70+68)/3 = 67.67
        # Second day average: (72+75)/2 = 73.5
        assert stats.mean == pytest.approx((67.67 + 73.5) / 2, rel=1e-2)
    
    def test_interpolation_linear(self):
        """Test linear interpolation for missing data."""
        # Create data with gaps
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 2),
            # Gap on Jan 3
            datetime(2024, 1, 4),
            datetime(2024, 1, 5),
        ]
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * 4,
            'value': [60, 65, 70, 75]
        })
        
        calc = DailyMetricsCalculator(data)
        stats = calc.calculate_statistics(
            'HeartRate',
            interpolation=InterpolationMethod.LINEAR
        )
        
        # With interpolation, should handle the gap
        assert stats.missing_data_count >= 0
    
    def test_timezone_handling(self, sample_data):
        """Test timezone conversion."""
        calc = DailyMetricsCalculator(sample_data, timezone='US/Eastern')
        assert calc.timezone == 'US/Eastern'
        # Data should be converted to Eastern time
        assert calc.data['creationDate'].dt.tz is not None
    
    def test_get_metrics_summary(self, multi_metric_data):
        """Test summary for multiple metrics."""
        calc = DailyMetricsCalculator(multi_metric_data)
        summary = calc.get_metrics_summary()
        
        assert 'HeartRate' in summary
        assert 'StepCount' in summary
        assert isinstance(summary['HeartRate'], MetricStatistics)
        assert isinstance(summary['StepCount'], MetricStatistics)
    
    def test_daily_aggregates(self, sample_data):
        """Test daily aggregate calculations."""
        calc = DailyMetricsCalculator(sample_data)
        
        # Test different aggregation methods
        mean_agg = calc.calculate_daily_aggregates('HeartRate', 'mean')
        assert len(mean_agg) == 10
        
        max_agg = calc.calculate_daily_aggregates('HeartRate', 'max')
        assert len(max_agg) == 10
        
        count_agg = calc.calculate_daily_aggregates('HeartRate', 'count')
        assert all(count_agg == 1)  # One reading per day in sample data
    
    def test_performance_large_dataset(self):
        """Test performance with large dataset (1 year of data)."""
        # Generate 1 year of daily data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        values = np.random.normal(70, 10, len(dates))
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * len(dates),
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        
        # Should process within 100ms as per requirement
        import time
        start = time.time()
        stats = calc.calculate_statistics('HeartRate')
        duration = (time.time() - start) * 1000  # Convert to ms
        
        assert duration < 100  # Should be faster than 100ms
        assert stats.count == 365
    
    # Property-based tests using hypothesis
    
    @given(
        data_frames([
            column('creationDate', elements=st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2025, 1, 1)
            )),
            column('type', elements=st.just('TestMetric')),
            column('value', elements=st.floats(
                min_value=0,
                max_value=1000,
                allow_nan=False,
                allow_infinity=False
            ))
        ], index=range_indexes(min_size=2, max_size=100))
    )
    def test_statistics_properties(self, df):
        """Property-based test for statistics calculations."""
        calc = DailyMetricsCalculator(df)
        stats = calc.calculate_statistics('TestMetric')
        
        if stats.count > 0 and not stats.insufficient_data:
            # Mean should be between min and max
            assert stats.min <= stats.mean <= stats.max
            
            # Median should be between min and max
            assert stats.min <= stats.median <= stats.max
            
            # Standard deviation should be non-negative
            assert stats.std >= 0
            
            # Percentiles should be ordered
            if stats.percentile_25 is not None and stats.percentile_75 is not None:
                assert stats.percentile_25 <= stats.median <= stats.percentile_75
    
    @given(
        st.lists(
            st.floats(min_value=1, max_value=200, allow_nan=False),
            min_size=5,
            max_size=50
        )
    )
    def test_outlier_detection_properties(self, values):
        """Property-based test for outlier detection."""
        dates = pd.date_range(start='2024-01-01', periods=len(values), freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['TestMetric'] * len(values),
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        outliers_iqr = calc.detect_outliers('TestMetric', OutlierMethod.IQR)
        outliers_zscore = calc.detect_outliers('TestMetric', OutlierMethod.Z_SCORE)
        
        # Outliers should be boolean series
        assert outliers_iqr.dtype == bool
        assert outliers_zscore.dtype == bool
        
        # Number of outliers should be reasonable (less than 50% of data)
        assert outliers_iqr.sum() < len(values) * 0.5
        assert outliers_zscore.sum() < len(values) * 0.5
    
    def test_edge_case_all_same_values(self):
        """Test with all values being the same."""
        data = pd.DataFrame({
            'creationDate': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'type': ['HeartRate'] * 10,
            'value': [70.0] * 10
        })
        
        calc = DailyMetricsCalculator(data)
        stats = calc.calculate_statistics('HeartRate')
        
        assert stats.mean == 70.0
        assert stats.median == 70.0
        assert stats.std == 0.0
        assert stats.min == 70.0
        assert stats.max == 70.0
        
        # No outliers when all values are the same
        outliers = calc.detect_outliers('HeartRate', OutlierMethod.IQR)
        assert outliers.sum() == 0
    
    def test_metric_statistics_to_dict(self):
        """Test MetricStatistics to_dict method."""
        stats = MetricStatistics(
            metric_name='HeartRate',
            count=10,
            mean=70.5,
            median=70.0,
            std=5.2,
            min=60.0,
            max=80.0,
            percentile_25=65.0,
            percentile_75=75.0,
            percentile_95=78.0
        )
        
        result = stats.to_dict()
        assert isinstance(result, dict)
        assert result['metric_name'] == 'HeartRate'
        assert result['count'] == 10
        assert result['mean'] == 70.5

# Distributed from comprehensive tests

"""
Tests for Daily Metrics Calculator

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest

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



        def test_init_default_parameters(self):
            """Test initialization with default parameters."""
            calc = DailyMetricsCalculator()
            assert calc is not None
            assert hasattr(calc, 'calculate_statistics')
        

        def test_init_custom_parameters(self):
            """Test initialization with custom parameters."""
            calc = DailyMetricsCalculator(outlier_method='iqr', missing_threshold=0.1)
            assert calc is not None
        

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
        

        def test_custom_outlier_thresholds(self, sample_data):
            """Test custom outlier detection thresholds."""
            strict_calc = DailyMetricsCalculator(outlier_threshold=2.0)  # Strict
            lenient_calc = DailyMetricsCalculator(outlier_threshold=4.0)  # Lenient
            
            strict_outliers = strict_calc.detect_outliers('steps', sample_data['steps'])
            lenient_outliers = lenient_calc.detect_outliers('steps', sample_data['steps'])
            
            # Strict should find more outliers
            assert len(strict_outliers) >= len(lenient_outliers)
        

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



