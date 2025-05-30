"""
Unit tests for DailyMetricsCalculator class.
Optimized using BaseCalculatorTest patterns and parametrized tests.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume

from tests.base_test_classes import ParametrizedCalculatorTests
from src.analytics.daily_metrics_calculator import (
    DailyMetricsCalculator,
    MetricStatistics,
    InterpolationMethod,
    OutlierMethod
)


class TestDailyMetricsCalculator:
    """Test suite for DailyMetricsCalculator using optimized patterns."""
    
    @pytest.fixture
    def health_data(self):
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
    
    @pytest.fixture
    def calculator(self, health_data):
        """Create calculator instance with health data."""
        return DailyMetricsCalculator(health_data)

    # Consolidated Statistics Tests
    @pytest.mark.parametrize("metric_type,expected_count", [
        ('HeartRate', 10),
        ('StepCount', 0),  # Not in basic data
    ])
    def test_calculate_statistics_basic(self, calculator, metric_type, expected_count):
        """Test basic statistics calculation with parametrized metrics."""
        stats = calculator.calculate_statistics(metric_type)
        assert stats.metric_name == metric_type
        assert stats.count == expected_count
        if expected_count > 0:
            assert stats.mean is not None
            assert not stats.insufficient_data
        else:
            assert stats.insufficient_data

    @pytest.mark.parametrize("data_fixture,metric", [
        ('health_data', 'HeartRate'),
        ('multi_metric_data', 'HeartRate'),
        ('multi_metric_data', 'StepCount'),
    ])
    def test_statistics_with_different_data(self, request, data_fixture, metric):
        """Parametrized test for statistics with different data sets."""
        data = request.getfixturevalue(data_fixture)
        calc = DailyMetricsCalculator(data)
        stats = calc.calculate_statistics(metric)
        assert isinstance(stats, MetricStatistics)
        assert stats.metric_name == metric

    # Consolidated Outlier Detection Tests
    @pytest.mark.parametrize("method,outlier_value", [
        (OutlierMethod.IQR, 150),
        (OutlierMethod.Z_SCORE, 500),  # Very extreme outlier for Z-score detection (threshold=3.0)
    ])
    def test_outlier_detection_methods(self, method, outlier_value):
        """Test different outlier detection methods."""
        values = [60, 65, 70, 72, 74, 75, 76, 78, 80, outlier_value]
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * 10,
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        outliers = calc.detect_outliers('HeartRate', method)
        assert outliers.iloc[-1] == True  # Last value should be outlier
        assert outliers.sum() >= 1

    # Consolidated Percentile Tests
    @pytest.mark.parametrize("percentiles", [
        [25, 50, 75],
        [10, 25, 50, 75, 90],
        [5, 95],
    ])
    def test_percentile_calculations(self, calculator, percentiles):
        """Test percentile calculations with different percentile sets."""
        result = calculator.calculate_percentiles('HeartRate', percentiles)
        for p in percentiles:
            assert p in result
            assert isinstance(result[p], (int, float))

    @pytest.mark.parametrize("invalid_percentile", [-1, 101, 0, 100.1])
    def test_invalid_percentiles(self, calculator, invalid_percentile):
        """Test error handling for invalid percentiles."""
        with pytest.raises(ValueError):
            calculator.calculate_percentiles('HeartRate', [invalid_percentile])

    # Specialized Tests (kept from original but consolidated)
    def test_initialization(self, health_data):
        """Test calculator initialization."""
        calc = DailyMetricsCalculator(health_data)
        assert calc.timezone == 'UTC'
        assert 'date' in calc.data.columns
        assert calc.data['value'].dtype == np.float64

    def test_timezone_handling(self, health_data):
        """Test timezone conversion."""
        calc = DailyMetricsCalculator(health_data, timezone='US/Eastern')
        assert calc.timezone == 'US/Eastern'
        assert calc.data['creationDate'].dt.tz is not None

    def test_date_range_filtering(self, calculator):
        """Test filtering by date range."""
        stats = calculator.calculate_statistics(
            'HeartRate',
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 7)
        )
        assert stats.count == 3  # Days 5, 6, 7

    def test_multiple_readings_per_day(self):
        """Test handling of multiple readings per day."""
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
        assert stats.count == 2  # Should have 2 days of data

    def test_interpolation_linear(self):
        """Test linear interpolation for missing data."""
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
        assert stats.missing_data_count >= 0

    def test_get_metrics_summary(self, multi_metric_data):
        """Test summary for multiple metrics."""
        calc = DailyMetricsCalculator(multi_metric_data)
        summary = calc.get_metrics_summary()
        
        assert 'HeartRate' in summary
        assert 'StepCount' in summary
        assert isinstance(summary['HeartRate'], MetricStatistics)
        assert isinstance(summary['StepCount'], MetricStatistics)

    # Property-based tests (simplified)
    @given(st.integers(min_value=1, max_value=100))
    def test_statistics_calculation_property(self, data_size):
        """Property-based test for statistics calculation."""
        assume(data_size >= 1)
        
        dates = pd.date_range(start='2024-01-01', periods=data_size, freq='D')
        values = np.random.uniform(50, 100, data_size)
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * data_size,
            'value': values
        })
        
        calc = DailyMetricsCalculator(data)
        stats = calc.calculate_statistics('HeartRate')
        
        assert stats.count == data_size
        assert stats.min <= stats.max
        if data_size > 1:
            assert stats.std is not None