"""
Unit tests for CorrelationAnalyzer class.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.analytics.correlation_analyzer import CorrelationAnalyzer


class TestCorrelationAnalyzer:
    """Test suite for CorrelationAnalyzer class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data for testing."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        
        # Create correlated data
        base_trend = np.linspace(0, 10, 100)
        noise = np.random.normal(0, 1, 100)
        
        data = {
            'steps': 8000 + base_trend * 500 + noise * 1000,
            'heart_rate': 70 + base_trend * 2 + noise * 5,
            'sleep_hours': 7.5 - base_trend * 0.1 + noise * 0.5,
            'calories': 2000 + base_trend * 100 + noise * 200
        }
        
        return pd.DataFrame(data, index=dates)
    
    @pytest.fixture
    def analyzer(self, sample_data):
        """Create CorrelationAnalyzer instance."""
        return CorrelationAnalyzer(sample_data)
    
    def test_initialization(self, sample_data):
        """Test analyzer initialization."""
        analyzer = CorrelationAnalyzer(sample_data)
        
        assert len(analyzer.numeric_columns) == 4
        assert 'steps' in analyzer.numeric_columns
        assert analyzer.significance_threshold == 0.05
        assert isinstance(analyzer.data.index, pd.DatetimeIndex)
    
    def test_initialization_with_date_column(self):
        """Test initialization when date is a column instead of index."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=50),
            'metric1': np.random.normal(0, 1, 50),
            'metric2': np.random.normal(0, 1, 50)
        })
        
        analyzer = CorrelationAnalyzer(data)
        assert isinstance(analyzer.data.index, pd.DatetimeIndex)
        assert len(analyzer.numeric_columns) == 2
    
    def test_insufficient_columns_error(self):
        """Test error when insufficient numeric columns."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'metric1': np.random.normal(0, 1, 10)
        })
        
        with pytest.raises(ValueError, match="Need at least 2 numeric columns"):
            CorrelationAnalyzer(data)
    
    def test_pearson_correlations(self, analyzer):
        """Test Pearson correlation calculation."""
        corr_matrix = analyzer.calculate_correlations('pearson')
        
        assert isinstance(corr_matrix, pd.DataFrame)
        assert corr_matrix.shape == (4, 4)
        assert np.allclose(np.diag(corr_matrix.values.astype(float)), 1.0, atol=0.001)
        
        # Check that cache is populated
        assert 'pearson_30' in analyzer.correlation_cache
        assert 'pearson_30' in analyzer.p_value_cache
    
    def test_spearman_correlations(self, analyzer):
        """Test Spearman correlation calculation."""
        corr_matrix = analyzer.calculate_correlations('spearman')
        
        assert isinstance(corr_matrix, pd.DataFrame)
        assert corr_matrix.shape == (4, 4)
        
        # Check that cache is populated
        assert 'spearman_30' in analyzer.correlation_cache
        assert 'spearman_30' in analyzer.p_value_cache
    
    def test_invalid_correlation_method(self, analyzer):
        """Test error with invalid correlation method."""
        with pytest.raises(ValueError, match="Unknown correlation method"):
            analyzer.calculate_correlations('invalid_method')
    
    def test_lag_correlation_analysis(self, analyzer):
        """Test lag correlation analysis."""
        lag_results = analyzer.calculate_lag_correlation('steps', 'calories', max_lag=5)
        
        assert 'lags' in lag_results
        assert 'correlations' in lag_results
        assert 'p_values' in lag_results
        assert 'confidence_intervals' in lag_results
        assert 'optimal_lag' in lag_results
        
        assert len(lag_results['lags']) == len(lag_results['correlations'])
        assert all(isinstance(ci, tuple) for ci in lag_results['confidence_intervals'])
    
    def test_lag_correlation_invalid_metrics(self, analyzer):
        """Test lag correlation with invalid metric names."""
        with pytest.raises(ValueError, match="Metrics must be numeric columns"):
            analyzer.calculate_lag_correlation('steps', 'invalid_metric')
    
    def test_partial_correlation(self, analyzer):
        """Test partial correlation calculation."""
        partial_corr, p_value = analyzer.calculate_partial_correlation(
            'steps', 'calories', ['heart_rate']
        )
        
        assert isinstance(partial_corr, float)
        assert isinstance(p_value, float)
        assert -1 <= partial_corr <= 1
        assert 0 <= p_value <= 1
    
    def test_partial_correlation_invalid_metrics(self, analyzer):
        """Test partial correlation with invalid metrics."""
        with pytest.raises(ValueError, match="Metrics not found"):
            analyzer.calculate_partial_correlation(
                'steps', 'invalid_metric', ['heart_rate']
            )
    
    def test_partial_correlation_insufficient_data(self, analyzer):
        """Test partial correlation with insufficient data."""
        # Create analyzer with minimal data
        small_data = analyzer.data.head(10)
        small_analyzer = CorrelationAnalyzer(small_data)
        
        partial_corr, p_value = small_analyzer.calculate_partial_correlation(
            'steps', 'calories', ['heart_rate'], min_periods=50
        )
        
        assert np.isnan(partial_corr)
        assert p_value == 1.0
    
    def test_correlation_strength_categories(self, analyzer):
        """Test correlation strength categorization."""
        assert analyzer.get_correlation_strength_category(0.9) == "Very Strong"
        assert analyzer.get_correlation_strength_category(0.7) == "Strong"
        assert analyzer.get_correlation_strength_category(0.5) == "Moderate"
        assert analyzer.get_correlation_strength_category(0.3) == "Weak"
        assert analyzer.get_correlation_strength_category(0.1) == "Very Weak"
        assert analyzer.get_correlation_strength_category(-0.8) == "Very Strong"
    
    def test_significant_correlations(self, analyzer):
        """Test significant correlations extraction."""
        significant_corrs = analyzer.get_significant_correlations(
            method='pearson', 
            min_strength=0.1
        )
        
        assert isinstance(significant_corrs, list)
        
        for corr in significant_corrs:
            assert 'metric1' in corr
            assert 'metric2' in corr
            assert 'correlation' in corr
            assert 'p_value' in corr
            assert 'strength_category' in corr
            assert 'direction' in corr
            
            assert abs(corr['correlation']) >= 0.1
            assert corr['p_value'] < analyzer.significance_threshold
            assert corr['direction'] in ['positive', 'negative']
    
    def test_correlation_summary(self, analyzer):
        """Test correlation summary generation."""
        summary = analyzer.get_correlation_summary()
        
        assert 'total_metric_pairs' in summary
        assert 'pearson_summary' in summary
        assert 'spearman_summary' in summary
        assert 'data_quality' in summary
        
        # Check Pearson summary structure
        pearson = summary['pearson_summary']
        assert 'mean_correlation' in pearson
        assert 'max_correlation' in pearson
        assert 'significant_correlations' in pearson
        assert 'strong_correlations' in pearson
        
        # Check data quality info
        data_quality = summary['data_quality']
        assert data_quality['metrics_count'] == 4
        assert data_quality['total_observations'] == 100
        assert 'date_range' in data_quality
    
    def test_confidence_interval_calculation(self, analyzer):
        """Test confidence interval calculation."""
        ci_low, ci_high = analyzer._calculate_confidence_interval(0.5, 50)
        
        assert ci_low < ci_high
        assert -1 <= ci_low <= 1
        assert -1 <= ci_high <= 1
        
        # Test with small sample size
        ci_low_small, ci_high_small = analyzer._calculate_confidence_interval(0.5, 3)
        assert ci_low_small == -1.0
        assert ci_high_small == 1.0
    
    def test_optimal_lag_finding(self, analyzer):
        """Test optimal lag identification."""
        # Create test lag results
        lag_results = {
            'correlations': [0.2, 0.5, 0.3, 0.6, 0.1],
            'p_values': [0.1, 0.01, 0.08, 0.001, 0.2],
            'lags': [-2, -1, 0, 1, 2]
        }
        
        optimal_lag = analyzer._find_optimal_lag(lag_results)
        
        # Should find lag 1 (highest significant correlation)
        assert optimal_lag == 1
    
    def test_missing_data_handling(self):
        """Test handling of missing data."""
        # Create data with missing values
        dates = pd.date_range('2023-01-01', periods=50)
        data = pd.DataFrame({
            'metric1': np.random.normal(0, 1, 50),
            'metric2': np.random.normal(0, 1, 50)
        }, index=dates)
        
        # Introduce missing values
        data.loc[data.index[:10], 'metric1'] = np.nan
        data.loc[data.index[40:], 'metric2'] = np.nan
        
        analyzer = CorrelationAnalyzer(data)
        corr_matrix = analyzer.calculate_correlations('pearson', min_periods=20)
        
        assert not np.isnan(corr_matrix.loc['metric1', 'metric2'])
    
    def test_cache_functionality(self, analyzer):
        """Test correlation caching."""
        # First calculation
        corr1 = analyzer.calculate_correlations('pearson')
        
        # Second calculation should use cache
        corr2 = analyzer.calculate_correlations('pearson')
        
        pd.testing.assert_frame_equal(
            analyzer._extract_numeric_correlations(corr1),
            analyzer._extract_numeric_correlations(corr2)
        )
        
        # Check cache keys exist
        assert 'pearson_30' in analyzer.correlation_cache
        assert 'pearson_30' in analyzer.p_value_cache
    
    def test_extract_numeric_correlations(self, analyzer):
        """Test extraction of numeric values from marked correlations."""
        # Create test data with significance markers
        test_data = pd.DataFrame({
            'A': [1.0, '0.500*', '-0.300**'],
            'B': ['0.500*', 1.0, '0.200'],
            'C': ['-0.300**', '0.200', 1.0]
        }, index=['A', 'B', 'C'])
        
        numeric_data = analyzer._extract_numeric_correlations(test_data)
        
        assert numeric_data.loc['A', 'B'] == 0.5
        assert numeric_data.loc['A', 'C'] == -0.3
        assert numeric_data.loc['B', 'C'] == 0.2
        assert all(numeric_data.dtypes == float)


class TestCorrelationAnalyzerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_single_metric_data(self):
        """Test with single metric (should fail)."""
        data = pd.DataFrame({
            'metric1': np.random.normal(0, 1, 100)
        }, index=pd.date_range('2023-01-01', periods=100))
        
        with pytest.raises(ValueError):
            CorrelationAnalyzer(data)
    
    def test_empty_data(self):
        """Test with empty DataFrame."""
        data = pd.DataFrame()
        
        with pytest.raises(ValueError):
            CorrelationAnalyzer(data)
    
    def test_all_nan_data(self):
        """Test with all NaN data."""
        data = pd.DataFrame({
            'metric1': [np.nan] * 100,
            'metric2': [np.nan] * 100
        }, index=pd.date_range('2023-01-01', periods=100))
        
        analyzer = CorrelationAnalyzer(data)
        corr_matrix = analyzer.calculate_correlations('pearson')
        
        # Should handle NaN gracefully
        assert corr_matrix.shape == (2, 2)
    
    def test_constant_values(self):
        """Test with constant metric values."""
        data = pd.DataFrame({
            'constant': [5.0] * 100,
            'variable': np.random.normal(0, 1, 100)
        }, index=pd.date_range('2023-01-01', periods=100))
        
        analyzer = CorrelationAnalyzer(data)
        corr_matrix = analyzer.calculate_correlations('pearson')
        
        # Correlation with constant should be NaN
        assert pd.isna(analyzer._extract_numeric_correlations(corr_matrix).loc['constant', 'variable'])


if __name__ == "__main__":
    pytest.main([__file__])