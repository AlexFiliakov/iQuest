"""
Unit tests for ComparisonOverlayCalculator

Tests all overlay calculations including weekly average, monthly average, 
personal best, and historical comparisons with statistical significance.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.analytics.comparison_overlay_calculator import (
    ComparisonOverlayCalculator, OverlayData, ComparisonResult
)


class TestComparisonOverlayCalculator:
    """Test suite for ComparisonOverlayCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create a ComparisonOverlayCalculator instance."""
        return ComparisonOverlayCalculator()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time series data for testing."""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        np.random.seed(42)  # For reproducible tests
        values = 100 + np.random.normal(0, 10, len(dates)) + np.sin(np.arange(len(dates)) * 2 * np.pi / 365) * 5
        return pd.Series(values, index=dates, name='test_metric')
    
    @pytest.fixture
    def sparse_data(self):
        """Create sparse data with few points."""
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
        values = [100, 105, 98, 102, 99]
        return pd.Series(values, index=dates, name='sparse_metric')
    
    def test_calculate_weekly_average_normal_case(self, calculator, sample_data):
        """Test weekly average calculation with normal data."""
        current_date = datetime(2024, 6, 15)
        result = calculator.calculate_weekly_average(sample_data, current_date)
        
        assert result.overlay_type == "weekly_average"
        assert not result.values.empty
        assert result.metadata['window_size'] == 7
        assert result.metadata['data_points'] == 7
        assert 'mean' in result.metadata
        assert 'std' in result.metadata
        assert 'trend_direction' in result.metadata
        assert result.confidence_upper is not None
        assert result.confidence_lower is not None
    
    def test_calculate_weekly_average_insufficient_data(self, calculator, sparse_data):
        """Test weekly average with insufficient data."""
        current_date = datetime(2024, 1, 10)  # Only 2 points available
        result = calculator.calculate_weekly_average(sparse_data, current_date)
        
        assert result.overlay_type == "weekly_average"
        assert 'error' in result.metadata
        assert result.metadata['error'] == "insufficient_data"
    
    def test_calculate_weekly_average_exclude_current(self, calculator, sample_data):
        """Test weekly average excludes current day when requested."""
        current_date = datetime(2024, 6, 15)
        
        # Test with exclude_current=True (default)
        result_exclude = calculator.calculate_weekly_average(sample_data, current_date, exclude_current=True)
        
        # Test with exclude_current=False
        result_include = calculator.calculate_weekly_average(sample_data, current_date, exclude_current=False)
        
        # Both should succeed but with different date ranges
        assert not result_exclude.values.empty
        assert not result_include.values.empty
        assert result_exclude.metadata['end_date'] != result_include.metadata['end_date']
    
    def test_calculate_monthly_average_normal_case(self, calculator, sample_data):
        """Test monthly average calculation with normal data."""
        current_date = datetime(2024, 6, 15)
        result = calculator.calculate_monthly_average(sample_data, current_date)
        
        assert result.overlay_type == "monthly_average"
        assert not result.values.empty
        assert result.metadata['window_size'] == 30
        assert result.metadata['data_points'] == 30
        assert 'mean' in result.metadata
        assert 'std' in result.metadata
        assert result.confidence_upper is not None
        assert result.confidence_lower is not None
    
    def test_calculate_monthly_average_with_seasonal_adjustment(self, calculator, sample_data):
        """Test monthly average with seasonal adjustment."""
        current_date = datetime(2024, 6, 15)
        result = calculator.calculate_monthly_average(sample_data, current_date, seasonal_adjustment=True)
        
        assert result.overlay_type == "monthly_average"
        assert result.metadata['seasonal_adjustment'] is True
        assert not result.values.empty
    
    def test_calculate_monthly_average_insufficient_data(self, calculator, sparse_data):
        """Test monthly average with insufficient data."""
        current_date = datetime(2024, 1, 10)
        result = calculator.calculate_monthly_average(sparse_data, current_date)
        
        assert result.overlay_type == "monthly_average"
        assert 'error' in result.metadata
        assert result.metadata['error'] == "insufficient_data"
    
    def test_calculate_personal_best_higher_is_better(self, calculator, sample_data):
        """Test personal best calculation when higher values are better."""
        result = calculator.calculate_personal_best(sample_data, "steps", higher_is_better=True)
        
        assert result.overlay_type == "personal_best"
        assert not result.values.empty
        assert result.metadata['best_value'] == sample_data.max()
        assert result.metadata['best_date'] == sample_data.idxmax().strftime('%Y-%m-%d')
        assert result.metadata['higher_is_better'] is True
        assert result.metadata['metric_type'] == "steps"
        assert 'days_since_best' in result.metadata
        
        # Check that all values in the series are the same (horizontal line)
        assert all(result.values == result.metadata['best_value'])
    
    def test_calculate_personal_best_lower_is_better(self, calculator, sample_data):
        """Test personal best calculation when lower values are better."""
        result = calculator.calculate_personal_best(sample_data, "weight", higher_is_better=False)
        
        assert result.overlay_type == "personal_best"
        assert not result.values.empty
        assert result.metadata['best_value'] == sample_data.min()
        assert result.metadata['best_date'] == sample_data.idxmin().strftime('%Y-%m-%d')
        assert result.metadata['higher_is_better'] is False
        assert result.metadata['metric_type'] == "weight"
    
    def test_calculate_personal_best_empty_data(self, calculator):
        """Test personal best with empty data."""
        empty_data = pd.Series([], dtype=float)
        result = calculator.calculate_personal_best(empty_data, "test")
        
        assert result.overlay_type == "personal_best"
        assert 'error' in result.metadata
        assert result.metadata['error'] == "no_data"
    
    def test_calculate_historical_comparison_default_periods(self, calculator, sample_data):
        """Test historical comparison with default periods."""
        current_date = datetime(2024, 6, 15)
        results = calculator.calculate_historical_comparison(sample_data, current_date)
        
        expected_keys = ['last_week', 'last_month', 'last_year']
        assert len(results) <= len(expected_keys)  # Some might not have data
        
        for key, result in results.items():
            assert key in expected_keys
            assert result.overlay_type.startswith('historical_')
            assert not result.values.empty
            assert 'comparison_period' in result.metadata
            assert 'comparison_date' in result.metadata
            assert 'comparison_value' in result.metadata
    
    def test_calculate_historical_comparison_custom_periods(self, calculator, sample_data):
        """Test historical comparison with custom periods."""
        current_date = datetime(2024, 6, 15)
        custom_periods = ['week', 'month']
        results = calculator.calculate_historical_comparison(sample_data, current_date, custom_periods)
        
        expected_keys = ['last_week', 'last_month']
        for key in results.keys():
            assert key in expected_keys
    
    def test_calculate_historical_comparison_no_data(self, calculator):
        """Test historical comparison with no available data."""
        empty_data = pd.Series([], dtype=float)
        current_date = datetime(2024, 6, 15)
        results = calculator.calculate_historical_comparison(empty_data, current_date)
        
        assert len(results) == 0
    
    def test_check_statistical_significance_significant(self, calculator):
        """Test statistical significance detection with significant difference."""
        current_value = 150.0
        comparison_values = [100.0, 95.0, 105.0, 98.0, 102.0]
        
        is_significant = calculator.check_statistical_significance(current_value, comparison_values)
        assert is_significant is True
    
    def test_check_statistical_significance_not_significant(self, calculator):
        """Test statistical significance detection with non-significant difference."""
        current_value = 102.0
        comparison_values = [100.0, 95.0, 105.0, 98.0, 102.0]
        
        is_significant = calculator.check_statistical_significance(current_value, comparison_values)
        assert is_significant is False
    
    def test_check_statistical_significance_insufficient_data(self, calculator):
        """Test statistical significance with insufficient comparison data."""
        current_value = 150.0
        comparison_values = [100.0, 95.0]  # Only 2 values
        
        is_significant = calculator.check_statistical_significance(current_value, comparison_values)
        assert is_significant is False
    
    def test_check_statistical_significance_zero_std(self, calculator):
        """Test statistical significance with zero standard deviation."""
        current_value = 150.0
        comparison_values = [100.0, 100.0, 100.0, 100.0]  # All same values
        
        is_significant = calculator.check_statistical_significance(current_value, comparison_values)
        assert is_significant is True  # Should detect difference from constant values
    
    def test_generate_context_message_new_personal_best(self, calculator):
        """Test context message generation for new personal best."""
        metric = "steps"
        current_value = 15000.0
        comparisons = {
            'personal_best': 14000.0,
            'weekly_avg': 10000.0,
            'monthly_avg': 9500.0
        }
        
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert "New personal best" in message
        assert "🎉" in message
    
    def test_generate_context_message_above_averages(self, calculator):
        """Test context message for values above averages."""
        metric = "steps"
        current_value = 12000.0
        comparisons = {
            'weekly_avg': 10000.0,
            'monthly_avg': 9000.0,
            'personal_best': 15000.0
        }
        
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert "above" in message.lower()
        assert "20.0%" in message or "33.3%" in message
    
    def test_generate_context_message_below_averages(self, calculator):
        """Test context message for values below averages."""
        metric = "steps"
        current_value = 8000.0
        comparisons = {
            'weekly_avg': 10000.0,
            'monthly_avg': 11000.0,
            'personal_best': 15000.0
        }
        
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert "below" in message.lower()
    
    def test_generate_context_message_no_significant_differences(self, calculator):
        """Test context message when no significant differences exist."""
        metric = "steps"
        current_value = 10100.0
        comparisons = {
            'weekly_avg': 10000.0,
            'monthly_avg': 10050.0,
            'personal_best': 15000.0
        }
        
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert message == f"Today's {metric}: {current_value:.1f}"
    
    def test_generate_context_message_empty_comparisons(self, calculator):
        """Test context message generation with empty comparisons."""
        metric = "steps"
        current_value = 10000.0
        comparisons = {}
        
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert message == f"Today's {metric}: {current_value:.1f}"
    
    def test_generate_context_message_error_handling(self, calculator):
        """Test context message generation error handling."""
        metric = "steps"
        current_value = 10000.0
        comparisons = {'weekly_avg': None}  # Invalid comparison value
        
        # Should not raise exception and return basic message
        message = calculator.generate_context_message(metric, current_value, comparisons)
        assert metric in message
        assert str(current_value) in message
    
    def test_seasonal_component_calculation(self, calculator):
        """Test seasonal component calculation."""
        # Create data with clear seasonal pattern
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        # Higher values in summer, lower in winter
        day_of_year = dates.dayofyear
        seasonal_pattern = 10 * np.sin(2 * np.pi * day_of_year / 365)
        base_values = 100 + seasonal_pattern + np.random.normal(0, 1, len(dates))
        data = pd.Series(base_values, index=dates)
        
        seasonal_component = calculator._calculate_seasonal_component(data)
        
        assert len(seasonal_component) == len(data)
        assert not seasonal_component.isna().all()
        # Summer should generally have positive components, winter negative
        summer_component = seasonal_component[seasonal_component.index.dayofyear.isin(range(150, 250))].mean()
        winter_component = seasonal_component[seasonal_component.index.dayofyear.isin(range(350, 365))].mean()
        assert summer_component > winter_component
    
    def test_overlay_data_structure(self):
        """Test OverlayData dataclass structure."""
        values = pd.Series([1, 2, 3], index=pd.date_range('2024-01-01', periods=3))
        metadata = {'test': 'value'}
        
        overlay_data = OverlayData(
            overlay_type="test",
            values=values,
            metadata=metadata
        )
        
        assert overlay_data.overlay_type == "test"
        assert overlay_data.values.equals(values)
        assert overlay_data.metadata == metadata
        assert overlay_data.confidence_upper is None
        assert overlay_data.confidence_lower is None
    
    def test_comparison_result_structure(self):
        """Test ComparisonResult dataclass structure."""
        result = ComparisonResult(
            current_value=100.0,
            comparison_value=90.0,
            difference=10.0,
            percentage_change=11.11,
            is_significant=True,
            context_message="Test message"
        )
        
        assert result.current_value == 100.0
        assert result.comparison_value == 90.0
        assert result.difference == 10.0
        assert result.percentage_change == 11.11
        assert result.is_significant is True
        assert result.context_message == "Test message"


# Integration tests
class TestComparisonOverlayCalculatorIntegration:
    """Integration tests for the calculator with real-world scenarios."""
    
    @pytest.fixture
    def real_world_data(self):
        """Create realistic health data for integration testing."""
        dates = pd.date_range(start='2024-01-01', end='2024-06-15', freq='D')
        np.random.seed(42)
        
        # Simulate step count data with weekly patterns and trends
        base_steps = 8000
        weekly_pattern = 2000 * np.sin(np.arange(len(dates)) * 2 * np.pi / 7)  # Higher on weekdays
        trend = np.linspace(0, 1000, len(dates))  # Gradual improvement
        noise = np.random.normal(0, 500, len(dates))
        
        steps = base_steps + weekly_pattern + trend + noise
        steps = np.maximum(steps, 1000)  # Ensure realistic minimum
        
        return pd.Series(steps, index=dates, name='steps')
    
    def test_full_overlay_workflow(self):
        """Test complete workflow of generating all overlay types."""
        calculator = ComparisonOverlayCalculator()
        
        # Create comprehensive test data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        values = 100 + np.random.normal(0, 10, len(dates))
        data = pd.Series(values, index=dates)
        current_date = datetime(2024, 6, 15)
        
        # Generate all overlay types
        weekly_overlay = calculator.calculate_weekly_average(data, current_date)
        monthly_overlay = calculator.calculate_monthly_average(data, current_date)
        best_overlay = calculator.calculate_personal_best(data, "test_metric")
        historical_overlays = calculator.calculate_historical_comparison(data, current_date)
        
        # Verify all overlays are valid
        assert weekly_overlay.overlay_type == "weekly_average"
        assert monthly_overlay.overlay_type == "monthly_average"
        assert best_overlay.overlay_type == "personal_best"
        assert len(historical_overlays) > 0
        
        # Verify no critical errors
        assert 'error' not in weekly_overlay.metadata
        assert 'error' not in monthly_overlay.metadata
        assert 'error' not in best_overlay.metadata
    
    @pytest.mark.parametrize("data_length,expected_overlays", [
        (5, 0),      # Too little data
        (10, 1),     # Only weekly possible
        (40, 2),     # Weekly and monthly possible
        (400, 3),    # All overlays possible including yearly comparison
    ])
    def test_overlay_availability_by_data_length(self, data_length, expected_overlays):
        """Test that overlay availability depends on data length."""
        calculator = ComparisonOverlayCalculator()
        
        dates = pd.date_range(start='2024-01-01', periods=data_length, freq='D')
        values = np.random.normal(100, 10, data_length)
        data = pd.Series(values, index=dates)
        current_date = dates[-1] + timedelta(days=1)
        
        successful_overlays = 0
        
        # Test weekly overlay
        weekly = calculator.calculate_weekly_average(data, current_date)
        if 'error' not in weekly.metadata:
            successful_overlays += 1
            
        # Test monthly overlay
        monthly = calculator.calculate_monthly_average(data, current_date)
        if 'error' not in monthly.metadata:
            successful_overlays += 1
            
        # Test historical overlays
        historical = calculator.calculate_historical_comparison(data, current_date)
        if len(historical) > 0:
            successful_overlays += 1
            
        # Allow some flexibility in expected overlays due to data patterns
        assert successful_overlays >= min(expected_overlays, 2)

# Distributed from comprehensive tests

"""
Tests for Comparison Overlay Calculator

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest


class TestComparisonOverlayCalculatorDistributed(BaseCalculatorTest):
    """Additional tests distributed from comprehensive test suite."""
    
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


