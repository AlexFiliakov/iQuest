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