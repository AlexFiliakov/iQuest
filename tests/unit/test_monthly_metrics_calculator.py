"""
Optimized unit tests for MonthlyMetricsCalculator class.
Uses parametrized tests and base class patterns to reduce test count while maintaining coverage.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock
import calendar

from tests.base_test_classes import BaseCalculatorTest
from src.analytics.monthly_metrics_calculator import (
    MonthlyMetricsCalculator,
    MonthMode,
    DistributionStats,
    MonthlyComparison,
    GrowthRateInfo,
    MonthlyMetrics
)
from src.analytics.daily_metrics_calculator import DailyMetricsCalculator


class TestMonthlyMetricsCalculatorOptimized(BaseCalculatorTest):
    """Optimized test suite for MonthlyMetricsCalculator."""
    
    def get_calculator_class(self):
        """Return the calculator class to test."""
        return MonthlyMetricsCalculator
    
    @pytest.fixture
    def health_data_fixtures(self):
        """Consolidated fixture for different data scenarios."""
        fixtures = {}
        
        # Standard 3-month data with trend
        dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
        n_days = len(dates)
        trend = np.linspace(70, 85, n_days)
        seasonal = 3 * np.sin(2 * np.pi * np.arange(n_days) / 30)
        noise = np.random.normal(0, 2, n_days)
        fixtures['standard'] = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * n_days,
            'value': trend + seasonal + noise,
            'sourceName': ['Apple Watch'] * n_days
        })
        
        # Leap year data
        leap_dates = pd.date_range(start='2024-02-01', end='2024-02-29', freq='D')
        fixtures['leap_year'] = pd.DataFrame({
            'creationDate': leap_dates,
            'type': ['HeartRate'] * 29,
            'value': np.random.normal(75, 5, 29),
            'sourceName': ['Apple Watch'] * 29
        })
        
        # Multi-year data for growth
        multi_dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        base_value = 70
        daily_growth = 0.0003
        multi_values = [base_value * (1 + daily_growth) ** i for i in range(len(multi_dates))]
        fixtures['multi_year'] = pd.DataFrame({
            'creationDate': multi_dates,
            'type': ['Steps'] * len(multi_dates),
            'value': np.array(multi_values) + np.random.normal(0, 2, len(multi_dates)),
            'sourceName': ['iPhone'] * len(multi_dates)
        })
        
        # Minimal data
        fixtures['minimal'] = pd.DataFrame({
            'creationDate': pd.date_range('2024-01-01', '2024-01-05', freq='D'),
            'type': ['TestMetric'] * 5,
            'value': [70, 71, 72, 73, 74],
            'sourceName': ['Test'] * 5
        })
        
        # Empty data
        fixtures['empty'] = pd.DataFrame({
            'creationDate': [],
            'type': [],
            'value': [],
            'sourceName': []
        })
        
        return fixtures
    
    @pytest.fixture
    def calculators(self, health_data_fixtures):
        """Create calculators for different modes and data sets."""
        daily_calc = DailyMetricsCalculator(health_data_fixtures['standard'])
        return {
            'calendar': MonthlyMetricsCalculator(daily_calc, mode=MonthMode.CALENDAR),
            'rolling': MonthlyMetricsCalculator(daily_calc, mode=MonthMode.ROLLING),
            'multi_year': MonthlyMetricsCalculator(
                DailyMetricsCalculator(health_data_fixtures['multi_year'])
            )
        }
    
    # Parametrized initialization tests
    @pytest.mark.parametrize("mode,use_parallel,cache_size", [
        (MonthMode.CALENDAR, True, 100),
        (MonthMode.ROLLING, False, 50),
        (MonthMode.CALENDAR, False, 200),
    ])
    def test_initialization_modes(self, health_data_fixtures, mode, use_parallel, cache_size):
        """Test calculator initialization with different configurations."""
        daily_calc = DailyMetricsCalculator(health_data_fixtures['standard'])
        calc = MonthlyMetricsCalculator(
            daily_calc, 
            mode=mode, 
            use_parallel=use_parallel,
            cache_size=cache_size
        )
        assert calc.mode == mode
        assert calc.use_parallel == use_parallel
        assert calc._cache_size == cache_size
    
    # Parametrized monthly statistics tests
    @pytest.mark.parametrize("mode,metric,year,month,expected_fields", [
        (MonthMode.CALENDAR, 'HeartRate', 2024, 1, ['avg', 'median', 'std', 'min', 'max']),
        (MonthMode.ROLLING, 'HeartRate', 2024, 1, ['avg', 'median', 'std', 'min', 'max']),
        (MonthMode.CALENDAR, 'HeartRate', 2024, 2, ['avg', 'median', 'std', 'min', 'max']),
    ])
    def test_calculate_monthly_stats(self, calculators, mode, metric, year, month, expected_fields):
        """Test monthly statistics calculation for different modes."""
        calc = calculators['calendar'] if mode == MonthMode.CALENDAR else calculators['rolling']
        stats = calc.calculate_monthly_stats(metric, year, month)
        
        assert isinstance(stats, MonthlyMetrics)
        assert stats.mode == mode
        for field in expected_fields:
            assert hasattr(stats, field)
        if stats.count > 0:
            assert stats.min <= stats.avg <= stats.max
    
    # Parametrized boundary tests
    @pytest.mark.parametrize("year,month,expected_days", [
        (2024, 1, 31),  # January
        (2024, 2, 29),  # Leap year February
        (2023, 2, 28),  # Non-leap year February
        (2024, 4, 30),  # April
        (2024, 12, 31), # December
    ])
    def test_month_boundaries_calendar(self, calculators, year, month, expected_days):
        """Test month boundary calculations for calendar mode."""
        calc = calculators['calendar']
        start, end = calc._get_month_boundaries(year, month)
        assert start.year == year
        assert start.month == month
        assert start.day == 1
        assert (end - start).days + 1 == expected_days
    
    # Consolidated comparison tests
    @pytest.mark.parametrize("comparison_type,method_name,params", [
        ('yoy', 'compare_year_over_year', {'metric': 'Steps', 'month': 1, 'year': 2024, 'years_back': 1}),
        ('growth', 'calculate_growth_rate', {'metric': 'Steps', 'periods': 6, 'year': 2024, 'month': 6}),
    ])
    def test_comparisons(self, calculators, comparison_type, method_name, params):
        """Test various comparison methods."""
        calc = calculators['multi_year']
        method = getattr(calc, method_name)
        result = method(**params)
        
        if comparison_type == 'yoy':
            assert isinstance(result, MonthlyComparison)
            assert hasattr(result, 'percent_change')
            assert hasattr(result, 'is_significant')
        elif comparison_type == 'growth':
            assert isinstance(result, GrowthRateInfo)
            assert hasattr(result, 'monthly_growth_rate')
            assert hasattr(result, 'annualized_growth_rate')
    
    # Distribution analysis tests
    def test_distribution_analysis(self, health_data_fixtures):
        """Test distribution statistics calculation."""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', '2024-01-31', freq='D')
        values = np.random.gamma(2, 2, 31) + 70  # Right-skewed distribution
        
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
        assert isinstance(dist_stats.normality_p_value, float)
        assert isinstance(dist_stats.is_normal, bool)
    
    # Edge case tests
    @pytest.mark.parametrize("data_key,metric,year,month,error_type", [
        ('minimal', 'TestMetric', 2024, 1, ValueError),  # Insufficient data for distribution
        ('empty', 'NonExistent', 2024, 1, None),  # Empty data handling
    ])
    def test_edge_cases(self, health_data_fixtures, data_key, metric, year, month, error_type):
        """Test edge cases and error handling."""
        data = health_data_fixtures[data_key]
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        if error_type and metric == 'TestMetric':
            with pytest.raises(error_type):
                monthly_calc.analyze_distribution(metric, year, month)
        else:
            stats = monthly_calc.calculate_monthly_stats(metric, year, month)
            assert stats.count == 0 if data_key == 'empty' else stats.count > 0
    
    # Invalid input tests
    @pytest.mark.parametrize("year,month", [
        (2024, 13),  # Invalid month > 12
        (2024, 0),   # Invalid month < 1
        (2024, -1),  # Negative month
    ])
    def test_invalid_month_handling(self, calculators, year, month):
        """Test handling of invalid month values."""
        calc = calculators['calendar']
        with pytest.raises((ValueError, calendar.IllegalMonthError)):
            calc.calculate_monthly_stats('HeartRate', year, month)
    
    # Parallel processing test
    def test_parallel_processing(self, calculators):
        """Test parallel processing for multiple months."""
        calc = calculators['multi_year']
        metrics = ['Steps']
        year_month_pairs = [(2024, m) for m in range(1, 5)]
        
        results = calc.calculate_multiple_months_parallel(metrics, year_month_pairs)
        
        assert 'Steps' in results
        assert len(results['Steps']) == 4
        for year, month in year_month_pairs:
            assert (year, month) in results['Steps']
            assert isinstance(results['Steps'][(year, month)], MonthlyMetrics)
    
    # Summary and caching tests
    def test_monthly_summary_and_caching(self, calculators):
        """Test monthly summary generation and caching behavior."""
        calc = calculators['calendar']
        
        # Get summary (first call)
        summary1 = calc.get_monthly_summary(['HeartRate'], 2024, 1)
        assert 'HeartRate' in summary1
        
        required_fields = ['avg', 'median', 'std', 'min', 'max', 'count', 
                          'yoy_percent_change', 'monthly_growth_rate', 'mode']
        for field in required_fields:
            assert field in summary1['HeartRate']
        
        # Second call should use cache
        summary2 = calc.get_monthly_summary(['HeartRate'], 2024, 1)
        assert summary1['HeartRate']['avg'] == summary2['HeartRate']['avg']
    
    # Performance test
    def test_performance_with_large_dataset(self):
        """Test performance with large dataset."""
        # Create 2 years of data
        dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
        values = 70 + 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25) + \
                 np.random.normal(0, 5, len(dates))
        
        data = pd.DataFrame({
            'creationDate': dates,
            'type': ['HeartRate'] * len(dates),
            'value': values,
            'sourceName': ['Apple Watch'] * len(dates)
        })
        
        daily_calc = DailyMetricsCalculator(data)
        monthly_calc = MonthlyMetricsCalculator(daily_calc)
        
        import time
        start_time = time.time()
        
        # Calculate 12 months
        for month in range(1, 13):
            stats = monthly_calc.calculate_monthly_stats('HeartRate', 2024, month)
            assert isinstance(stats, MonthlyMetrics)
        
        execution_time = time.time() - start_time
        assert execution_time < 10  # Should complete quickly


class TestMonthlyMetricsIntegration:
    """Integration tests for monthly metrics calculator."""
    
    def test_mode_consistency_across_operations(self):
        """Test that mode is preserved across all operations."""
        data = pd.DataFrame({
            'creationDate': pd.date_range('2024-01-01', '2024-03-31', freq='D'),
            'type': ['HeartRate'] * 90,
            'value': np.random.normal(75, 5, 90),
            'sourceName': ['Apple Watch'] * 90
        })
        
        daily_calc = DailyMetricsCalculator(data)
        
        for mode in [MonthMode.CALENDAR, MonthMode.ROLLING]:
            calc = MonthlyMetricsCalculator(daily_calc, mode=mode)
            
            # Test various operations preserve mode
            stats = calc.calculate_monthly_stats('HeartRate', 2024, 2)
            assert stats.mode == mode
            
            summary = calc.get_monthly_summary(['HeartRate'], 2024, 2)
            assert summary['HeartRate']['mode'] == mode.value
    
    def test_leap_year_handling_comprehensive(self):
        """Comprehensive test for leap year handling."""
        # Test multiple leap year scenarios
        leap_years = [2020, 2024]
        non_leap_years = [2021, 2023]
        
        for year in leap_years + non_leap_years:
            dates = pd.date_range(f'{year}-02-01', f'{year}-03-01', freq='D')[:-1]
            expected_days = 29 if year in leap_years else 28
            
            data = pd.DataFrame({
                'creationDate': dates,
                'type': ['HeartRate'] * len(dates),
                'value': np.random.normal(75, 5, len(dates)),
                'sourceName': ['Apple Watch'] * len(dates)
            })
            
            daily_calc = DailyMetricsCalculator(data)
            monthly_calc = MonthlyMetricsCalculator(daily_calc)
            
            stats = monthly_calc.calculate_monthly_stats('HeartRate', year, 2)
            assert stats.count == expected_days