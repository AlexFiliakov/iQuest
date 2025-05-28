"""
Tests for seasonal pattern analysis functionality.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch

# Adjust imports based on actual project structure
try:
    from src.analytics.seasonal_pattern_analyzer import (
        SeasonalPatternAnalyzer, FourierAnalyzer, ProphetForecaster, 
        WeatherCorrelator, SeasonalStrength
    )
except ImportError:
    # Handle case where package structure might be different
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from analytics.seasonal_pattern_analyzer import (
        SeasonalPatternAnalyzer, FourierAnalyzer, ProphetForecaster,
        WeatherCorrelator, SeasonalStrength
    )


class TestSeasonalPatternAnalyzer:
    """Test suite for SeasonalPatternAnalyzer."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample health data with artificial seasonal patterns."""
        # Create 2 years of daily data
        date_range = pd.date_range(
            start='2022-01-01', 
            end='2023-12-31', 
            freq='D'
        )
        
        # Create artificial seasonal pattern (higher in summer, lower in winter)
        day_of_year = date_range.dayofyear
        seasonal_pattern = 5000 + 2000 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
        
        # Add noise and trend
        noise = np.random.normal(0, 500, len(date_range))
        trend = np.linspace(0, 1000, len(date_range))  # Gradual increase over time
        
        step_count = seasonal_pattern + noise + trend
        
        # Create DataFrame
        data = pd.DataFrame({
            'StepCount': step_count,
            'ActiveEnergyBurned': step_count * 0.04 + np.random.normal(0, 20, len(date_range)),
        }, index=date_range)
        
        return data
    
    @pytest.fixture
    def analyzer(self, sample_data):
        """Create analyzer instance with sample data."""
        return SeasonalPatternAnalyzer(sample_data)
    
    def test_fourier_analyzer_detects_annual_cycle(self, sample_data):
        """Test that Fourier analysis correctly identifies annual cycles."""
        fourier_analyzer = FourierAnalyzer()
        metric_data = sample_data['StepCount']
        
        result = fourier_analyzer.analyze(metric_data)
        
        # Should detect annual cycle
        assert result.annual_cycle_detected, "Annual cycle should be detected"
        assert result.seasonal_strength > 0.1, "Seasonal strength should be significant"
        assert len(result.dominant_frequencies) > 0, "Should find dominant frequencies"
        
        # Check for annual frequency component (around 1 cycle per year)
        annual_components = [
            comp for comp in result.dominant_frequencies
            if 0.8 <= comp.frequency <= 1.2
        ]
        assert len(annual_components) > 0, "Should detect annual frequency component"
    
    def test_comprehensive_seasonal_analysis(self, analyzer):
        """Test the main comprehensive analysis method."""
        result = analyzer.analyze_seasonality('StepCount')
        
        # Verify basic structure
        assert result.metric_name == 'StepCount'
        assert result.fourier_results is not None
        assert result.stl_decomposition is not None
        
        # Verify seasonality detection
        assert result.seasonality_strength > 0
        assert result.seasonality_category != SeasonalStrength.NONE
        
        # Verify visualization data
        assert result.polar_plot_data is not None
        assert result.phase_plot_data is not None
        assert len(result.polar_plot_data.angles) == 12  # 12 months
        
        # Verify forecast data
        assert result.forecast_data is not None
        assert 'dates' in result.forecast_data
        assert 'forecast' in result.forecast_data
        
    def test_polar_plot_data_generation(self, analyzer):
        """Test polar plot data generation for annual cycles."""
        polar_data = analyzer.create_polar_visualization('StepCount')
        
        assert len(polar_data.angles) == 12, "Should have 12 angles for months"
        assert len(polar_data.radii) == 12, "Should have 12 radii for months"
        assert len(polar_data.labels) == 12, "Should have 12 month labels"
        assert len(polar_data.colors) == 12, "Should have 12 colors"
        
        # Verify angles are correct (0 to 2π)
        expected_angles = [2 * np.pi * i / 12 for i in range(12)]
        np.testing.assert_allclose(polar_data.angles, expected_angles, rtol=1e-10)
    
    def test_pattern_break_detection(self, analyzer):
        """Test pattern break detection functionality."""
        # This will depend on the specific data and decomposition
        alerts = analyzer.detect_pattern_breaks('StepCount')
        
        # Should return a list (may be empty for clean synthetic data)
        assert isinstance(alerts, list)
        
        # If alerts exist, verify structure
        for alert in alerts:
            assert hasattr(alert, 'date')
            assert hasattr(alert, 'deviation_score')
            assert hasattr(alert, 'significance')
            assert alert.severity in ['low', 'medium', 'high']
    
    def test_goal_timing_recommendations(self, analyzer):
        """Test goal timing recommendation generation."""
        recommendations = analyzer.identify_optimal_goal_timing('fitness')
        
        # Should return a list
        assert isinstance(recommendations, list)
        
        # If recommendations exist, verify structure
        for rec in recommendations:
            assert hasattr(rec, 'goal_type')
            assert hasattr(rec, 'optimal_start_date')
            assert hasattr(rec, 'success_probability')
            assert 0 <= rec.success_probability <= 1
    
    def test_weather_correlation(self):
        """Test weather correlation analysis."""
        # Create simple test data
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
        metric_data = pd.Series(
            np.random.normal(5000, 1000, len(dates)), 
            index=dates, 
            name='StepCount'
        )
        
        correlator = WeatherCorrelator()
        result = correlator.correlate(metric_data)
        
        assert result is not None
        assert hasattr(result, 'temperature_correlation')
        assert hasattr(result, 'precipitation_correlation')
        assert hasattr(result, 'weather_significance')
        assert -1 <= result.temperature_correlation <= 1
    
    def test_prophet_forecaster_fallback(self):
        """Test Prophet forecaster with fallback when Prophet not available."""
        # Create simple test data
        dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
        metric_data = pd.Series(
            np.random.normal(5000, 1000, len(dates)), 
            index=dates
        )
        
        forecaster = ProphetForecaster()
        
        # Test fallback method directly (in case Prophet is not installed)
        result = forecaster._fallback_forecast(metric_data, periods=30)
        
        assert 'dates' in result
        assert 'forecast' in result
        assert 'lower_bound' in result
        assert 'upper_bound' in result
        assert len(result['forecast']) == 30
        assert len(result['dates']) == 30
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data scenarios."""
        # Create very short dataset
        short_data = pd.DataFrame({
            'StepCount': [1000, 1100, 1200]
        }, index=pd.date_range('2022-01-01', periods=3, freq='D'))
        
        analyzer = SeasonalPatternAnalyzer(short_data)
        
        # Should raise error for insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            analyzer.analyze_seasonality('StepCount')
    
    def test_missing_metric_handling(self, analyzer):
        """Test handling of missing metrics."""
        with pytest.raises(ValueError, match="not found in data"):
            analyzer.analyze_seasonality('NonExistentMetric')
    
    @pytest.mark.parametrize("strength,expected_category", [
        (0.05, SeasonalStrength.NONE),
        (0.2, SeasonalStrength.WEAK),
        (0.4, SeasonalStrength.MODERATE),
        (0.7, SeasonalStrength.STRONG),
        (0.9, SeasonalStrength.VERY_STRONG),
    ])
    def test_seasonality_categorization(self, analyzer, strength, expected_category):
        """Test seasonality strength categorization."""
        result = analyzer._categorize_seasonality(strength)
        assert result == expected_category


class TestFourierAnalyzer:
    """Focused tests for Fourier analysis components."""
    
    def test_empty_analysis_for_short_series(self):
        """Test that short time series return empty analysis."""
        # Create very short series (less than 1 year)
        short_data = pd.Series(
            np.random.normal(100, 10, 100),
            index=pd.date_range('2022-01-01', periods=100, freq='D')
        )
        
        analyzer = FourierAnalyzer()
        result = analyzer.analyze(short_data)
        
        assert not result.annual_cycle_detected
        assert result.seasonal_strength == 0.0
        assert len(result.dominant_frequencies) == 0
    
    def test_frequency_significance_calculation(self):
        """Test statistical significance calculation for frequencies."""
        analyzer = FourierAnalyzer()
        
        # Test significance calculation
        power_spectrum = np.array([1, 2, 10, 3, 1, 2, 1])  # Peak at index 2
        peak_power = 10
        n_samples = 365
        
        significance = analyzer._calculate_frequency_significance(
            peak_power, power_spectrum, n_samples
        )
        
        assert 0 <= significance <= 1, "P-value should be between 0 and 1"
        assert significance < 0.05, "High peak should be significant"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])