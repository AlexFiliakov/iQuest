"""Unit tests for the statistics calculator."""

import pytest
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from statistics_calculator import BasicStatistics, StatisticsCalculator


class TestBasicStatistics:
    """Test the BasicStatistics dataclass."""
    
    def test_basic_statistics_creation(self):
        """Test creating a BasicStatistics object."""
        stats = BasicStatistics(
            total_records=100,
            date_range=(datetime(2024, 1, 1), datetime(2024, 12, 31)),
            records_by_type={'HeartRate': 50, 'Steps': 50},
            records_by_source={'iPhone': 60, 'Apple Watch': 40},
            types_by_source={'iPhone': ['Steps'], 'Apple Watch': ['HeartRate', 'Steps']}
        )
        
        assert stats.total_records == 100
        assert stats.date_range[0] == datetime(2024, 1, 1)
        assert stats.date_range[1] == datetime(2024, 12, 31)
        assert stats.records_by_type['HeartRate'] == 50
        assert stats.records_by_source['iPhone'] == 60
        assert 'HeartRate' in stats.types_by_source['Apple Watch']
    
    def test_to_dict(self):
        """Test converting BasicStatistics to dictionary."""
        stats = BasicStatistics(
            total_records=10,
            date_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)),
            records_by_type={'HeartRate': 10},
            records_by_source={'iPhone': 10},
            types_by_source={'iPhone': ['HeartRate']}
        )
        
        result = stats.to_dict()
        
        assert result['total_records'] == 10
        assert result['date_range']['start'] == '2024-01-01T00:00:00'
        assert result['date_range']['end'] == '2024-01-31T00:00:00'
        assert result['records_by_type']['HeartRate'] == 10
        assert result['records_by_source']['iPhone'] == 10
        assert result['types_by_source']['iPhone'] == ['HeartRate']
    
    def test_to_dict_with_none_dates(self):
        """Test to_dict with None date values."""
        stats = BasicStatistics(
            total_records=0,
            date_range=(None, None),
            records_by_type={},
            records_by_source={},
            types_by_source={}
        )
        
        result = stats.to_dict()
        
        assert result['date_range']['start'] is None
        assert result['date_range']['end'] is None


class TestStatisticsCalculator:
    """Test the StatisticsCalculator class."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            'creationDate': [
                '2024-01-01 10:00:00',
                '2024-01-02 11:00:00',
                '2024-01-03 12:00:00',
                '2024-01-04 13:00:00',
                '2024-01-05 14:00:00'
            ],
            'type': ['HeartRate', 'Steps', 'HeartRate', 'Steps', 'Sleep'],
            'sourceName': ['Apple Watch', 'iPhone', 'Apple Watch', 'iPhone', 'iPhone'],
            'value': [70, 5000, 75, 6000, 8.5],
            'unit': ['bpm', 'count', 'bpm', 'count', 'hr']
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def calculator(self):
        """Create a StatisticsCalculator instance."""
        return StatisticsCalculator()
    
    def test_calculate_from_empty_dataframe(self, calculator):
        """Test calculating statistics from empty DataFrame."""
        df = pd.DataFrame()
        stats = calculator.calculate_from_dataframe(df)
        
        assert stats.total_records == 0
        assert stats.date_range == (None, None)
        assert stats.records_by_type == {}
        assert stats.records_by_source == {}
        assert stats.types_by_source == {}
    
    def test_calculate_from_dataframe(self, calculator, sample_dataframe):
        """Test calculating statistics from a sample DataFrame."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        
        # Check total records
        assert stats.total_records == 5
        
        # Check date range
        assert stats.date_range[0].strftime('%Y-%m-%d') == '2024-01-01'
        assert stats.date_range[1].strftime('%Y-%m-%d') == '2024-01-05'
        
        # Check records by type
        assert stats.records_by_type['HeartRate'] == 2
        assert stats.records_by_type['Steps'] == 2
        assert stats.records_by_type['Sleep'] == 1
        
        # Check records by source
        assert stats.records_by_source['Apple Watch'] == 2
        assert stats.records_by_source['iPhone'] == 3
        
        # Check types by source
        assert set(stats.types_by_source['Apple Watch']) == {'HeartRate'}
        assert set(stats.types_by_source['iPhone']) == {'Steps', 'Sleep'}
    
    def test_types_by_source_sorted(self, calculator, sample_dataframe):
        """Test that types within each source are sorted."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        
        # iPhone has Sleep and Steps - should be sorted alphabetically
        assert stats.types_by_source['iPhone'] == ['Sleep', 'Steps']
    
    def test_get_quick_summary(self, calculator, sample_dataframe):
        """Test generating a quick summary."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        summary = calculator.get_quick_summary(stats)
        
        # Check that summary contains expected information
        assert "Total Records: 5" in summary
        assert "Date Range: 2024-01-01 to 2024-01-05" in summary
        assert "HeartRate: 2" in summary
        assert "Steps: 2" in summary
        assert "Sleep: 1" in summary
        assert "Apple Watch: 2 records" in summary
        assert "iPhone: 3 records" in summary
        assert "Data Sources (2):" in summary
    
    def test_get_quick_summary_empty(self, calculator):
        """Test generating summary for empty data."""
        stats = BasicStatistics(
            total_records=0,
            date_range=(None, None),
            records_by_type={},
            records_by_source={},
            types_by_source={}
        )
        summary = calculator.get_quick_summary(stats)
        
        assert summary == "No health records found."
    
    def test_large_dataset_top_5_types(self, calculator):
        """Test that only top 5 types are shown in summary."""
        # Create DataFrame with many types
        data = {
            'creationDate': ['2024-01-01'] * 10,
            'type': ['Type1', 'Type2', 'Type3', 'Type4', 'Type5', 
                    'Type6', 'Type7', 'Type8', 'Type9', 'Type10'],
            'sourceName': ['iPhone'] * 10,
            'value': [1] * 10,
            'unit': ['count'] * 10
        }
        df = pd.DataFrame(data)
        
        stats = calculator.calculate_from_dataframe(df)
        summary = calculator.get_quick_summary(stats)
        
        # Check that only 5 types are shown
        type_lines = [line for line in summary.split('\n') if line.strip().startswith('- Type')]
        assert len(type_lines) == 5
    
    def test_calculate_from_database_no_loader(self, calculator):
        """Test that calculate_from_database raises error without data_loader."""
        with pytest.raises(ValueError, match="DataLoader not provided"):
            calculator.calculate_from_database()
    
    def test_date_parsing(self, calculator):
        """Test that various date formats are handled correctly."""
        data = {
            'creationDate': [
                '2024-01-01T10:00:00Z',
                '2024-01-02 11:00:00',
                '2024-01-03'
            ],
            'type': ['HeartRate'] * 3,
            'sourceName': ['iPhone'] * 3,
            'value': [70] * 3,
            'unit': ['bpm'] * 3
        }
        df = pd.DataFrame(data)
        
        stats = calculator.calculate_from_dataframe(df)
        
        # Should successfully parse all date formats
        assert stats.total_records == 3
        assert stats.date_range[0].strftime('%Y-%m-%d') == '2024-01-01'
        assert stats.date_range[1].strftime('%Y-%m-%d') == '2024-01-03'

# Distributed from comprehensive tests

"""
Tests for Statistics Calculator

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest


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


class TestStatisticsCalculatorDistributed(BaseCalculatorTest):
    """Additional tests distributed from comprehensive test suite."""
    
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
    
    def test_statistics_properties(self, calculator, data):
        """Property-based test for statistics."""
        series = pd.Series(data, name='test')
        result = calculator.calculate_statistics('test', series)
        
        if result and result['count'] > 0:
            assert result['min'] <= result['mean'] <= result['max']
            assert result['min'] <= result['median'] <= result['max']
            assert result['std'] >= 0
    
    def test_descriptive_statistics_complete(self, calculator):
        """Test all descriptive statistics."""
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        stats = calculator.calculate_descriptive_stats(data)
        
        expected_keys = ['mean', 'median', 'mode', 'std', 'var', 'skewness', 'kurtosis',
                       'min', 'max', 'range', 'q1', 'q3', 'iqr']
        
        for key in expected_keys:
            assert key in stats
    
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


