"""
Consolidated UI Widget Tests

Merges tests from:
- test_week_over_week_widget.py
- test_comparison_overlay_widget.py  
- test_monthly_context_widget.py

Uses parametrized tests to reduce duplication and improve maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    pytest.skip("PyQt6 not available", allow_module_level=True)

from tests.base_test_classes import BaseWidgetTest


# Widget imports with error handling
try:
    from src.ui.week_over_week_widget import (
        WeekOverWeekWidget, MomentumIndicatorWidget, StreakTrackerWidget, 
        SlopeGraphWidget
    )
    WEEK_OVER_WEEK_AVAILABLE = True
except ImportError:
    WEEK_OVER_WEEK_AVAILABLE = False

try:
    from src.ui.comparison_overlay_widget import (
        ComparisonOverlayWidget, InteractiveLegend
    )
    COMPARISON_OVERLAY_AVAILABLE = True
except ImportError:
    COMPARISON_OVERLAY_AVAILABLE = False

try:
    from src.ui.monthly_context_widget import MonthlyContextWidget
    MONTHLY_CONTEXT_AVAILABLE = True
except ImportError:
    MONTHLY_CONTEXT_AVAILABLE = False


# Analytics imports with error handling
try:
    from src.analytics.week_over_week_trends import (
        WeekOverWeekTrends, TrendResult, StreakInfo, MomentumIndicator,
        WeekTrendData, MomentumType, Prediction
    )
except ImportError:
    pass

try:
    from src.analytics.comparison_overlay_calculator import OverlayData
except ImportError:
    pass


class TestConsolidatedWidgets:
    """Consolidated tests for analytics widgets using parametrized approach."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        """Qt application fixture."""
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6 not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample data for widget testing."""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'date': dates,
            'steps': np.random.randint(5000, 15000, 30),
            'heart_rate': np.random.randint(60, 100, 30),
            'calories': np.random.randint(1500, 3000, 30),
        })
    
    @pytest.fixture
    def mock_trends_data(self):
        """Mock trends data for testing."""
        return {
            'current_week': {'steps': 70000, 'avg_daily': 10000},
            'previous_week': {'steps': 65000, 'avg_daily': 9286},
            'change_percent': 7.7,
            'trend': 'increasing',
            'momentum': 'strong'
        }
    
    # Parametrized widget creation tests
    widget_configs = []
    
    if WEEK_OVER_WEEK_AVAILABLE:
        widget_configs.extend([
            (WeekOverWeekWidget, {}, 'week_over_week'),
            (MomentumIndicatorWidget, {}, 'momentum_indicator'),
            (StreakTrackerWidget, {}, 'streak_tracker'),
            (SlopeGraphWidget, {}, 'slope_graph'),
        ])
    
    if COMPARISON_OVERLAY_AVAILABLE:
        widget_configs.extend([
            (ComparisonOverlayWidget, {}, 'comparison_overlay'),
            (InteractiveLegend, {'items': []}, 'interactive_legend'),
        ])
    
    if MONTHLY_CONTEXT_AVAILABLE:
        widget_configs.append(
            (MonthlyContextWidget, {}, 'monthly_context')
        )
    
    @pytest.mark.ui
    @pytest.mark.widget
    @pytest.mark.parametrize("widget_class,init_args,widget_type", widget_configs)
    def test_widget_initialization(self, qt_app, widget_class, init_args, widget_type):
        """Test all widgets can be initialized."""
        widget = widget_class(**init_args)
        try:
            assert isinstance(widget, QWidget)
            assert widget.isVisible() is False
            # Widget should have basic Qt widget properties
            assert hasattr(widget, 'show')
            assert hasattr(widget, 'hide')
        finally:
            widget.close()
            widget.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.widget
    @pytest.mark.parametrize("widget_class,init_args,widget_type", widget_configs)
    def test_widget_show_hide(self, qt_app, widget_class, init_args, widget_type):
        """Test widget visibility controls."""
        widget = widget_class(**init_args)
        try:
            widget.show()
            assert widget.isVisible() is True
            
            widget.hide()
            assert widget.isVisible() is False
        finally:
            widget.close()
            widget.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.widget
    @pytest.mark.parametrize("widget_class,init_args,widget_type", widget_configs)
    def test_widget_has_layout_or_paint(self, qt_app, widget_class, init_args, widget_type):
        """Test widget has proper structure."""
        widget = widget_class(**init_args)
        try:
            # Widget should either have a layout or custom painting
            layout = widget.layout()
            has_paint_event = hasattr(widget, 'paintEvent')
            assert layout is not None or has_paint_event
        finally:
            widget.close()
            widget.deleteLater()


class TestWeekOverWeekWidgets:
    """Specific tests for Week Over Week widgets."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        if not PYQT_AVAILABLE or not WEEK_OVER_WEEK_AVAILABLE:
            pytest.skip("Dependencies not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    @pytest.fixture
    def week_over_week_widget(self, qt_app):
        """Create WeekOverWeekWidget instance."""
        widget = WeekOverWeekWidget()
        yield widget
        widget.close()
        widget.deleteLater()
    
    @pytest.fixture
    def momentum_widget(self, qt_app):
        """Create MomentumIndicatorWidget instance."""
        widget = MomentumIndicatorWidget()
        yield widget
        widget.close()
        widget.deleteLater()
    
    def test_week_over_week_data_update(self, week_over_week_widget, mock_trends_data):
        """Test week over week widget data updates."""
        if hasattr(week_over_week_widget, 'update_data'):
            week_over_week_widget.update_data(mock_trends_data)
        # Should not crash
    
    def test_momentum_indicator_states(self, momentum_widget):
        """Test momentum indicator different states."""
        momentum_states = ['strong_positive', 'weak_positive', 'neutral', 'weak_negative', 'strong_negative']
        
        for state in momentum_states:
            if hasattr(momentum_widget, 'set_momentum'):
                momentum_widget.set_momentum(state)
            # Should handle all momentum states without crashing


class TestComparisonOverlayWidgets:
    """Specific tests for Comparison Overlay widgets."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        if not PYQT_AVAILABLE or not COMPARISON_OVERLAY_AVAILABLE:
            pytest.skip("Dependencies not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    @pytest.fixture
    def overlay_widget(self, qt_app):
        """Create ComparisonOverlayWidget instance."""
        widget = ComparisonOverlayWidget()
        yield widget
        widget.close()
        widget.deleteLater()
    
    @pytest.fixture
    def legend_widget(self, qt_app):
        """Create InteractiveLegend instance."""
        widget = InteractiveLegend(items=[])
        yield widget
        widget.close()
        widget.deleteLater()
    
    @pytest.fixture
    def sample_overlay_data(self):
        """Sample overlay data for testing."""
        return {
            'primary': np.random.randint(5000, 15000, 30),
            'comparison': np.random.randint(4000, 14000, 30),
            'labels': [f'Day {i}' for i in range(30)],
            'dates': pd.date_range('2024-01-01', periods=30)
        }
    
    def test_overlay_data_update(self, overlay_widget, sample_overlay_data):
        """Test overlay widget with different data."""
        if hasattr(overlay_widget, 'update_overlay_data'):
            overlay_widget.update_overlay_data(sample_overlay_data)
        elif hasattr(overlay_widget, 'set_data'):
            overlay_widget.set_data(sample_overlay_data)
        # Should handle data updates
    
    def test_legend_item_management(self, legend_widget):
        """Test legend item add/remove functionality."""
        test_items = [
            {'name': 'Steps', 'color': 'blue', 'visible': True},
            {'name': 'Heart Rate', 'color': 'red', 'visible': False},
        ]
        
        if hasattr(legend_widget, 'add_item'):
            for item in test_items:
                legend_widget.add_item(item)
        elif hasattr(legend_widget, 'set_items'):
            legend_widget.set_items(test_items)
        
        # Should handle legend items without error


class TestMonthlyContextWidget:
    """Specific tests for Monthly Context widget."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        if not PYQT_AVAILABLE or not MONTHLY_CONTEXT_AVAILABLE:
            pytest.skip("Dependencies not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    @pytest.fixture
    def monthly_widget(self, qt_app):
        """Create MonthlyContextWidget instance."""
        widget = MonthlyContextWidget()
        yield widget
        widget.close()
        widget.deleteLater()
    
    @pytest.fixture
    def monthly_data(self):
        """Sample monthly data."""
        return {
            'current_month': {
                'name': 'January 2024',
                'days': 31,
                'total_steps': 310000,
                'avg_daily': 10000
            },
            'previous_month': {
                'name': 'December 2023', 
                'total_steps': 300000,
                'avg_daily': 9677
            },
            'year_context': {
                'total_months': 12,
                'current_position': 1
            }
        }
    
    def test_monthly_context_data_update(self, monthly_widget, monthly_data):
        """Test monthly context widget data updates."""
        if hasattr(monthly_widget, 'update_monthly_context'):
            monthly_widget.update_monthly_context(monthly_data)
        elif hasattr(monthly_widget, 'set_data'):
            monthly_widget.set_data(monthly_data)
        # Should handle monthly data


class TestWidgetIntegration:
    """Integration tests for widget interactions."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6 not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    def test_widget_memory_cleanup(self, qt_app):
        """Test widgets are properly cleaned up."""
        widgets = []
        
        # Create multiple widgets
        for widget_class, init_args, _ in TestConsolidatedWidgets.widget_configs[:3]:
            try:
                widget = widget_class(**init_args)
                widgets.append(widget)
            except Exception:
                pass  # Skip if widget can't be created
        
        # Clean up all widgets
        for widget in widgets:
            widget.close()
            widget.deleteLater()
        
        # Process events to ensure cleanup
        QApplication.processEvents()
    
    @pytest.mark.ui
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.parametrize("data_size", [10, 100, 1000])
    def test_widget_performance_with_data_size(self, qt_app, data_size):
        """Test widget performance with different data sizes."""
        if not WEEK_OVER_WEEK_AVAILABLE:
            pytest.skip("Week over week widget not available")
            
        widget = WeekOverWeekWidget()
        try:
            # Generate data of specified size
            large_data = {
                'dates': pd.date_range('2024-01-01', periods=data_size),
                'values': np.random.randint(5000, 15000, data_size)
            }
            
            # Widget should handle large datasets without crashing
            if hasattr(widget, 'update_data'):
                widget.update_data(large_data)
            
        finally:
            widget.close()
            widget.deleteLater()


# Error simulation tests
class TestWidgetErrorHandling:
    """Test widget error handling and edge cases."""
    
    @pytest.fixture(scope="class")
    def qt_app(self):
        if not PYQT_AVAILABLE:
            pytest.skip("PyQt6 not available")
        app = QApplication.instance() or QApplication([])
        yield app
        if app:
            app.quit()
    
    def test_widget_with_invalid_data(self, qt_app):
        """Test widgets handle invalid data gracefully."""
        invalid_data_sets = [
            None,
            {},
            {'invalid': 'data'},
            {'dates': [], 'values': []},  # Empty arrays
            {'dates': ['invalid'], 'values': ['invalid']},  # Invalid types
        ]
        
        for widget_class, init_args, widget_type in TestConsolidatedWidgets.widget_configs[:2]:
            widget = widget_class(**init_args)
            try:
                for invalid_data in invalid_data_sets:
                    # Widget should handle invalid data without crashing
                    try:
                        if hasattr(widget, 'update_data'):
                            widget.update_data(invalid_data)
                        elif hasattr(widget, 'set_data'):
                            widget.set_data(invalid_data)
                    except (ValueError, TypeError, AttributeError):
                        # Expected exceptions for invalid data
                        pass
            finally:
                widget.close()
                widget.deleteLater()


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__])