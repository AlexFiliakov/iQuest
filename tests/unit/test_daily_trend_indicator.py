"""Unit tests for daily trend indicator components."""

import pytest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.daily_trend_indicator import DailyTrendIndicator, TrendData, ArrowIndicator
from src.ui.trend_calculator import TrendCalculator


@pytest.fixture(scope="module")
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestTrendCalculator:
    """Test the TrendCalculator utility class."""
    
    def test_calculate_daily_change_normal(self):
        """Test normal daily change calculation."""
        abs_change, pct_change = TrendCalculator.calculate_daily_change(110, 100)
        assert abs_change == 10
        assert pct_change == 10.0
        
        abs_change, pct_change = TrendCalculator.calculate_daily_change(90, 100)
        assert abs_change == -10
        assert pct_change == -10.0
        
    def test_calculate_daily_change_zero_previous(self):
        """Test change calculation when previous value is zero."""
        abs_change, pct_change = TrendCalculator.calculate_daily_change(50, 0, handle_zero=True)
        assert abs_change == 50
        assert pct_change is None  # Should return None for percentage
        
        abs_change, pct_change = TrendCalculator.calculate_daily_change(50, 0, handle_zero=False)
        assert abs_change == 50
        assert pct_change == 100.0
        
    def test_calculate_daily_change_none_previous(self):
        """Test change calculation when previous value is None."""
        abs_change, pct_change = TrendCalculator.calculate_daily_change(100, None)
        assert abs_change is None
        assert pct_change is None
        
    def test_get_previous_day_value(self):
        """Test getting previous day value with lookback."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'value': range(10)
        }, index=dates)
        
        # Remove some dates to simulate gaps
        data = data.drop(dates[5])  # Remove 2023-01-06
        
        # Test immediate previous day
        prev = TrendCalculator.get_previous_day_value(
            data, datetime(2023, 1, 5), 'value'
        )
        assert prev == 3  # 2023-01-04's value
        
        # Test with gap - should skip missing day
        prev = TrendCalculator.get_previous_day_value(
            data, datetime(2023, 1, 7), 'value'
        )
        assert prev == 4  # 2023-01-05's value (skips missing 01-06)
        
        # Test beyond lookback
        prev = TrendCalculator.get_previous_day_value(
            data, datetime(2023, 1, 20), 'value', max_lookback_days=7
        )
        assert prev is None
        
    def test_get_trend_history(self):
        """Test getting historical trend data."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'value': range(10)
        }, index=dates)
        
        # Get 7-day history
        history = TrendCalculator.get_trend_history(
            data, datetime(2023, 1, 7), 'value', days=7
        )
        assert len(history) == 7
        assert history == [0, 1, 2, 3, 4, 5, 6]
        
        # Test with missing data
        data_with_gaps = data.drop([dates[3], dates[5]])
        history = TrendCalculator.get_trend_history(
            data_with_gaps, datetime(2023, 1, 7), 'value', days=7, fill_missing=True
        )
        assert len(history) == 7
        # Should interpolate missing values
        
    def test_classify_change_magnitude(self):
        """Test change magnitude classification."""
        assert TrendCalculator.classify_change_magnitude(None) == 'neutral'
        assert TrendCalculator.classify_change_magnitude(0.05) == 'minimal'
        assert TrendCalculator.classify_change_magnitude(5) == 'minor_increase'
        assert TrendCalculator.classify_change_magnitude(15) == 'moderate_increase'
        assert TrendCalculator.classify_change_magnitude(25) == 'significant_increase'
        assert TrendCalculator.classify_change_magnitude(-5) == 'minor_decrease'
        assert TrendCalculator.classify_change_magnitude(-15) == 'moderate_decrease'
        assert TrendCalculator.classify_change_magnitude(-25) == 'significant_decrease'
        
    def test_calculate_trend_statistics(self):
        """Test trend statistics calculation."""
        values = [10, 12, 11, 13, 15, 14, 16]
        stats = TrendCalculator.calculate_trend_statistics(values)
        
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'trend_slope' in stats
        assert 'trend_direction' in stats
        assert 'volatility' in stats
        
        assert stats['mean'] == np.mean(values)
        assert stats['trend_direction'] == 'increasing'  # Values trend upward
        
        # Test with empty values
        empty_stats = TrendCalculator.calculate_trend_statistics([])
        assert empty_stats == {}


class TestArrowIndicator:
    """Test the ArrowIndicator widget."""
    
    def test_arrow_rotation(self, app):
        """Test arrow rotation based on trend."""
        arrow = ArrowIndicator()
        
        # Test upward trend
        arrow.set_trend(15)
        # Wait for animation to complete
        arrow.rotation_anim.finished.connect(lambda: None)
        QTest.qWait(600)
        assert arrow.rotation == 90
        
        # Test downward trend
        arrow.set_trend(-15)
        QTest.qWait(600)
        assert arrow.rotation == -90
        
        # Test neutral trend
        arrow.set_trend(0.05)
        QTest.qWait(600)
        assert arrow.rotation == 0
        
    def test_arrow_colors(self, app):
        """Test arrow color changes based on magnitude."""
        arrow = ArrowIndicator()
        
        # Test color for different magnitudes
        arrow.set_trend(15)  # Moderate increase
        assert arrow._color.name() == "#95c17b"
        
        arrow.set_trend(-15)  # Moderate decrease
        assert arrow._color.name() == "#e76f51"
        
        arrow.set_trend(5)  # Minor increase
        assert arrow._color.name() == "#ffd166"
        
        arrow.set_trend(None)  # Neutral
        assert arrow._color.name() == "#8b7355"
        
    def test_pulse_animation(self, app):
        """Test pulse animation for significant changes."""
        arrow = ArrowIndicator()
        
        # Test pulse starts for >20% change
        arrow.set_trend(25)
        QTest.qWait(100)
        assert arrow.pulse_anim.state() == arrow.pulse_anim.State.Running
        
        # Test pulse stops for <20% change
        arrow.set_trend(10)
        QTest.qWait(100)
        assert arrow.pulse_anim.state() == arrow.pulse_anim.State.Stopped


class TestDailyTrendIndicator:
    """Test the complete DailyTrendIndicator widget."""
    
    def test_indicator_creation(self, app):
        """Test basic indicator creation."""
        indicator = DailyTrendIndicator("Steps")
        assert indicator.metric_name == "Steps"
        assert indicator.name_label.text() == "Steps"
        assert indicator.value_label.text() == "--"
        
    def test_update_with_increase(self, app):
        """Test updating indicator with increasing trend."""
        indicator = DailyTrendIndicator("Steps")
        
        trend_data = TrendData(
            current_value=10000,
            previous_value=8000,
            change_absolute=2000,
            change_percent=25.0,
            history=[7000, 7500, 8000, 8500, 9000, 9500, 10000],
            dates=[datetime.now() - timedelta(days=i) for i in range(6, -1, -1)],
            unit="steps",
            metric_name="Steps"
        )
        
        indicator.update_trend(trend_data)
        
        assert indicator.value_label.text() == "10000.0 steps"
        assert "+2000.0 (+25.0%)" in indicator.change_label.text()
        
    def test_update_with_decrease(self, app):
        """Test updating indicator with decreasing trend."""
        indicator = DailyTrendIndicator("Heart Rate")
        
        trend_data = TrendData(
            current_value=65,
            previous_value=70,
            change_absolute=-5,
            change_percent=-7.14,
            history=[72, 71, 70, 69, 68, 67, 65],
            dates=[datetime.now() - timedelta(days=i) for i in range(6, -1, -1)],
            unit="bpm",
            metric_name="Heart Rate"
        )
        
        indicator.update_trend(trend_data)
        
        assert indicator.value_label.text() == "65.0 bpm"
        assert "-5.0 (-7.1%)" in indicator.change_label.text()
        
    def test_baseline_indicator(self, app):
        """Test indicator when no previous data exists."""
        indicator = DailyTrendIndicator("New Metric")
        
        trend_data = TrendData(
            current_value=100,
            previous_value=None,
            change_absolute=None,
            change_percent=None,
            history=[100],
            dates=[datetime.now()],
            unit="units",
            metric_name="New Metric"
        )
        
        indicator.update_trend(trend_data)
        
        assert indicator.value_label.text() == "100.0 units"
        assert indicator.change_label.text() == "Setting baseline"
        
    def test_zero_previous_value(self, app):
        """Test handling of zero previous value."""
        indicator = DailyTrendIndicator("Activity")
        
        trend_data = TrendData(
            current_value=50,
            previous_value=0,
            change_absolute=50,
            change_percent=None,  # Should be None when previous is 0
            history=[0, 0, 0, 10, 20, 30, 50],
            dates=[datetime.now() - timedelta(days=i) for i in range(6, -1, -1)],
            unit="min",
            metric_name="Activity"
        )
        
        indicator.update_trend(trend_data)
        
        assert indicator.value_label.text() == "50.0 min"
        assert "+50.0 min" in indicator.change_label.text()
        assert "%" not in indicator.change_label.text()  # No percentage shown
        
    def test_tooltip_generation(self, app):
        """Test tooltip content generation."""
        indicator = DailyTrendIndicator("Sleep")
        
        trend_data = TrendData(
            current_value=8.5,
            previous_value=7.0,
            change_absolute=1.5,
            change_percent=21.4,
            history=[6.5, 7.0, 7.5, 7.0, 7.5, 7.0, 8.5],
            dates=[datetime.now() - timedelta(days=i) for i in range(6, -1, -1)],
            unit="hours",
            metric_name="Sleep"
        )
        
        indicator.update_trend(trend_data)
        
        # Simulate hover event
        indicator.enterEvent(None)
        # Tooltip should be shown, but we can't easily test QToolTip
        # Just verify the method doesn't crash
        
    def test_sparkline_update(self, app):
        """Test sparkline chart updates."""
        indicator = DailyTrendIndicator("Weight")
        
        trend_data = TrendData(
            current_value=150,
            previous_value=151,
            change_absolute=-1,
            change_percent=-0.66,
            history=[152, 151.5, 151, 150.5, 150.2, 150.1, 150],
            dates=[datetime.now() - timedelta(days=i) for i in range(6, -1, -1)],
            unit="lbs",
            metric_name="Weight"
        )
        
        indicator.update_trend(trend_data)
        
        # Sparkline should have data
        # Can't easily test matplotlib rendering, but verify no crashes
        assert indicator.sparkline is not None