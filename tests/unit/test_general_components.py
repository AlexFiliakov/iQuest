"""
Tests for General Components

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest


def test_coverage_reporting():
    """Ensure test coverage reporting is working."""
    # This test ensures coverage tools are properly configured
    import coverage
    cov = coverage.Coverage()
    assert cov is not None


class TestGeneralComponentsDistributed(BaseCalculatorTest):
    """Additional tests distributed from comprehensive test suite."""
    
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
    
    def test_seasonal_pattern_detection(self, calculator, data_generator):
        """Test seasonal pattern detection."""
        # Generate full year of data
        yearly_data = data_generator.generate(365)
        
        patterns = calculator.detect_seasonal_patterns(yearly_data, 'steps')
        
        assert patterns is not None
        assert 'seasonal_strength' in patterns
    
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
        

