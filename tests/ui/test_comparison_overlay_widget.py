"""
UI tests for ComparisonOverlayWidget

Tests the interactive overlay visualization widget including legend functionality,
overlay toggling, and chart integration.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.comparison_overlay_widget import (
    ComparisonOverlayWidget, InteractiveLegend
)
from src.analytics.comparison_overlay_calculator import OverlayData


class TestInteractiveLegend:
    """Test suite for InteractiveLegend widget."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication instance."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        
    @pytest.fixture
    def legend(self, app):
        """Create InteractiveLegend instance."""
        return InteractiveLegend()
    
    @pytest.fixture
    def sample_overlay_data(self):
        """Create sample overlay data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        values = pd.Series(np.random.normal(100, 10, 10), index=dates)
        metadata = {
            'mean': 100.0,
            'std': 10.0,
            'data_points': 10
        }
        return OverlayData(
            overlay_type="weekly_average",
            values=values,
            metadata=metadata
        )
    
    def test_legend_initialization(self, legend):
        """Test legend widget initialization."""
        assert legend.overlay_items == {}
        assert legend.width() == 250
        assert legend.show_all_btn is not None
        assert legend.hide_all_btn is not None
    
    def test_add_overlay_item(self, legend, sample_overlay_data):
        """Test adding overlay item to legend."""
        overlay_type = "weekly_average"
        color = "#4A90E2"
        
        legend.add_overlay_item(overlay_type, sample_overlay_data, color)
        
        assert overlay_type in legend.overlay_items
        item = legend.overlay_items[overlay_type]
        assert item['color'] == color
        assert item['data'] == sample_overlay_data
        assert item['checkbox'].isChecked()
    
    def test_add_duplicate_overlay_item(self, legend, sample_overlay_data):
        """Test adding duplicate overlay item does nothing."""
        overlay_type = "weekly_average"
        color = "#4A90E2"
        
        # Add first time
        legend.add_overlay_item(overlay_type, sample_overlay_data, color)
        original_count = len(legend.overlay_items)
        
        # Try to add again
        legend.add_overlay_item(overlay_type, sample_overlay_data, color)
        
        assert len(legend.overlay_items) == original_count
    
    def test_remove_overlay_item(self, legend, sample_overlay_data):
        """Test removing overlay item from legend."""
        overlay_type = "weekly_average"
        color = "#4A90E2"
        
        # Add item first
        legend.add_overlay_item(overlay_type, sample_overlay_data, color)
        assert overlay_type in legend.overlay_items
        
        # Remove item
        legend.remove_overlay_item(overlay_type)
        assert overlay_type not in legend.overlay_items
    
    def test_remove_nonexistent_overlay_item(self, legend):
        """Test removing non-existent overlay item does nothing."""
        # Should not raise exception
        legend.remove_overlay_item("nonexistent")
        assert len(legend.overlay_items) == 0
    
    def test_show_all_overlays(self, legend, sample_overlay_data):
        """Test show all overlays functionality."""
        # Add multiple overlay items
        overlay_types = ["weekly_average", "monthly_average", "personal_best"]
        for overlay_type in overlay_types:
            legend.add_overlay_item(overlay_type, sample_overlay_data, "#FF0000")
            # Uncheck some items
            legend.overlay_items[overlay_type]['checkbox'].setChecked(False)
        
        # Show all
        legend.show_all_overlays()
        
        # Verify all are checked
        for overlay_type in overlay_types:
            assert legend.overlay_items[overlay_type]['checkbox'].isChecked()
    
    def test_hide_all_overlays(self, legend, sample_overlay_data):
        """Test hide all overlays functionality."""
        # Add multiple overlay items
        overlay_types = ["weekly_average", "monthly_average", "personal_best"]
        for overlay_type in overlay_types:
            legend.add_overlay_item(overlay_type, sample_overlay_data, "#FF0000")
            # Ensure all are checked initially
            legend.overlay_items[overlay_type]['checkbox'].setChecked(True)
        
        # Hide all
        legend.hide_all_overlays()
        
        # Verify all are unchecked
        for overlay_type in overlay_types:
            assert not legend.overlay_items[overlay_type]['checkbox'].isChecked()
    
    def test_overlay_label_formatting(self, legend):
        """Test overlay label formatting for different types."""
        # Test weekly average
        weekly_data = OverlayData(
            overlay_type="weekly_average",
            values=pd.Series(),
            metadata={'mean': 150.5, 'data_points': 7}
        )
        label = legend._format_overlay_label("weekly_average", weekly_data)
        assert "7-Day Average" in label
        assert "150.5" in label
        
        # Test monthly average
        monthly_data = OverlayData(
            overlay_type="monthly_average",
            values=pd.Series(),
            metadata={'mean': 200.0, 'data_points': 30}
        )
        label = legend._format_overlay_label("monthly_average", monthly_data)
        assert "30-Day Average" in label
        assert "200.0" in label
        
        # Test personal best
        best_data = OverlayData(
            overlay_type="personal_best",
            values=pd.Series(),
            metadata={'best_value': 300.0, 'days_since_best': 5}
        )
        label = legend._format_overlay_label("personal_best", best_data)
        assert "Personal Best" in label
        assert "300.0" in label
        assert "5d ago" in label
        
        # Test historical comparison
        historical_data = OverlayData(
            overlay_type="historical_week",
            values=pd.Series(),
            metadata={'comparison_value': 180.0}
        )
        label = legend._format_overlay_label("historical_week", historical_data)
        assert "Last Week" in label
        assert "180.0" in label


class TestComparisonOverlayWidget:
    """Test suite for ComparisonOverlayWidget."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication instance."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def mock_figure_and_axes(self):
        """Create mock matplotlib figure and axes."""
        figure = Mock(spec=Figure)
        axes = Mock(spec=Axes)
        
        # Mock canvas
        canvas = Mock()
        figure.canvas = canvas
        
        # Mock basic plotting methods
        axes.plot = Mock(return_value=[Mock()])
        axes.fill_between = Mock(return_value=Mock())
        axes.lines = []
        axes.collections = []
        
        return figure, axes
    
    @pytest.fixture
    def overlay_widget(self, app, mock_figure_and_axes):
        """Create ComparisonOverlayWidget instance."""
        figure, axes = mock_figure_and_axes
        return ComparisonOverlayWidget(figure, axes)
    
    @pytest.fixture
    def sample_overlay_data(self):
        """Create sample overlay data."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        values = pd.Series(np.random.normal(100, 10, 30), index=dates)
        metadata = {
            'mean': 100.0,
            'std': 10.0,
            'data_points': 30
        }
        return OverlayData(
            overlay_type="weekly_average",
            values=values,
            metadata=metadata
        )
    
    def test_widget_initialization(self, overlay_widget):
        """Test widget initialization."""
        assert overlay_widget.overlays == {}
        assert overlay_widget.overlay_lines == {}
        assert overlay_widget.confidence_bands == {}
        assert overlay_widget.legend is not None
        assert len(overlay_widget.overlay_colors) > 0
    
    def test_add_overlay_success(self, overlay_widget, sample_overlay_data):
        """Test successfully adding an overlay."""
        overlay_type = "weekly_average"
        
        overlay_widget.add_overlay(overlay_type, sample_overlay_data)
        
        assert overlay_type in overlay_widget.overlays
        assert overlay_widget.overlays[overlay_type] == sample_overlay_data
    
    def test_add_overlay_with_error(self, overlay_widget):
        """Test adding overlay with error metadata."""
        error_data = OverlayData(
            overlay_type="weekly_average",
            values=pd.Series(),
            metadata={'error': 'insufficient_data'}
        )
        
        overlay_widget.add_overlay("weekly_average", error_data)
        
        # Should not be added to overlays
        assert "weekly_average" not in overlay_widget.overlays
    
    def test_add_overlay_empty_values(self, overlay_widget):
        """Test adding overlay with empty values."""
        empty_data = OverlayData(
            overlay_type="weekly_average",
            values=pd.Series(),
            metadata={}
        )
        
        overlay_widget.add_overlay("weekly_average", empty_data)
        
        # Should not be added to overlays
        assert "weekly_average" not in overlay_widget.overlays
    
    def test_remove_overlay(self, overlay_widget, sample_overlay_data):
        """Test removing an overlay."""
        overlay_type = "weekly_average"
        
        # Add overlay first
        overlay_widget.add_overlay(overlay_type, sample_overlay_data)
        assert overlay_type in overlay_widget.overlays
        
        # Remove overlay
        overlay_widget.remove_overlay(overlay_type)
        assert overlay_type not in overlay_widget.overlays
    
    def test_remove_nonexistent_overlay(self, overlay_widget):
        """Test removing non-existent overlay."""
        # Should not raise exception
        overlay_widget.remove_overlay("nonexistent")
        assert len(overlay_widget.overlays) == 0
    
    def test_toggle_overlay_visibility(self, overlay_widget, sample_overlay_data):
        """Test toggling overlay visibility."""
        overlay_type = "weekly_average"
        
        # Add overlay and mock line
        overlay_widget.add_overlay(overlay_type, sample_overlay_data)
        mock_line = Mock()
        overlay_widget.overlay_lines[overlay_type] = mock_line
        
        # Test hiding
        overlay_widget.toggle_overlay(overlay_type, False)
        mock_line.set_visible.assert_called_with(False)
        
        # Test showing
        overlay_widget.toggle_overlay(overlay_type, True)
        mock_line.set_visible.assert_called_with(True)
    
    def test_clear_all_overlays(self, overlay_widget, sample_overlay_data):
        """Test clearing all overlays."""
        # Add multiple overlays
        overlay_types = ["weekly_average", "monthly_average", "personal_best"]
        for overlay_type in overlay_types:
            overlay_widget.add_overlay(overlay_type, sample_overlay_data)
        
        assert len(overlay_widget.overlays) == len(overlay_types)
        
        # Clear all
        overlay_widget.clear_all_overlays()
        assert len(overlay_widget.overlays) == 0
    
    def test_color_assignment(self, overlay_widget):
        """Test that overlays get assigned appropriate colors."""
        assert "weekly_average" in overlay_widget.overlay_colors
        assert "monthly_average" in overlay_widget.overlay_colors
        assert "personal_best" in overlay_widget.overlay_colors
        
        # Colors should be valid hex colors
        for color in overlay_widget.overlay_colors.values():
            assert color.startswith('#')
            assert len(color) == 7
    
    @patch('src.ui.comparison_overlay_widget.ComparisonOverlayCalculator')
    def test_convenience_methods(self, mock_calculator, overlay_widget):
        """Test convenience methods for adding specific overlay types."""
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        data = pd.Series(np.random.normal(100, 10, 30), index=dates)
        current_date = datetime(2024, 6, 15)
        
        # Mock calculator methods
        mock_calc_instance = mock_calculator.return_value
        mock_calc_instance.calculate_weekly_average.return_value = OverlayData(
            overlay_type="weekly_average",
            values=data,
            metadata={}
        )
        mock_calc_instance.calculate_monthly_average.return_value = OverlayData(
            overlay_type="monthly_average",
            values=data,
            metadata={}
        )
        mock_calc_instance.calculate_personal_best.return_value = OverlayData(
            overlay_type="personal_best",
            values=data,
            metadata={}
        )
        mock_calc_instance.calculate_historical_comparison.return_value = {
            'last_week': OverlayData(overlay_type="historical_week", values=data, metadata={}),
            'last_month': OverlayData(overlay_type="historical_month", values=data, metadata={})
        }
        
        # Test convenience methods
        overlay_widget.add_weekly_average_overlay(data, current_date)
        overlay_widget.add_monthly_average_overlay(data, current_date)
        overlay_widget.add_personal_best_overlay(data, "steps", True)
        overlay_widget.add_historical_comparison_overlays(data, current_date, ['week', 'month'])
        
        # Verify calculator methods were called
        mock_calc_instance.calculate_weekly_average.assert_called_once()
        mock_calc_instance.calculate_monthly_average.assert_called_once()
        mock_calc_instance.calculate_personal_best.assert_called_once()
        mock_calc_instance.calculate_historical_comparison.assert_called_once()
    
    def test_generate_context_message(self, overlay_widget, sample_overlay_data):
        """Test context message generation."""
        # Add some overlays
        overlay_widget.overlays["weekly_average"] = sample_overlay_data
        overlay_widget.overlays["personal_best"] = sample_overlay_data
        
        # Test message generation
        data = pd.Series([100, 110, 105], index=pd.date_range('2024-01-01', periods=3))
        message = overlay_widget.generate_context_message("steps", 120.0, data)
        
        assert isinstance(message, str)
        assert "steps" in message
        assert "120.0" in message
    
    def test_chart_style_update(self, overlay_widget, mock_figure_and_axes):
        """Test WSJ chart style application."""
        figure, axes = mock_figure_and_axes
        
        # Mock figure and axes properties
        figure.patch = Mock()
        axes.set_facecolor = Mock()
        axes.spines = {
            'top': Mock(),
            'right': Mock(),
            'left': Mock(),
            'bottom': Mock()
        }
        axes.grid = Mock()
        axes.tick_params = Mock()
        axes.get_xticklabels = Mock(return_value=[])
        axes.get_yticklabels = Mock(return_value=[])
        
        # Test style update
        overlay_widget.update_chart_style()
        
        # Verify style methods were called
        figure.patch.set_facecolor.assert_called_once()
        axes.set_facecolor.assert_called_once()
        axes.grid.assert_called_once()
        axes.tick_params.assert_called_once()
    
    def test_draw_overlay_personal_best_style(self, overlay_widget, mock_figure_and_axes):
        """Test that personal best overlay uses different line style."""
        figure, axes = mock_figure_and_axes
        
        # Create personal best overlay data
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        values = pd.Series([150] * 10, index=dates)  # Horizontal line
        overlay_data = OverlayData(
            overlay_type="personal_best",
            values=values,
            metadata={'best_value': 150}
        )
        
        # Test drawing
        overlay_widget._draw_overlay("personal_best", overlay_data, "#FF0000")
        
        # Verify plot was called
        axes.plot.assert_called_once()
        
        # Check that the call used solid line style for personal best
        call_args = axes.plot.call_args
        assert call_args[1]['linestyle'] == '-'  # Solid line for personal best
    
    def test_draw_overlay_with_confidence_bands(self, overlay_widget, mock_figure_and_axes):
        """Test drawing overlay with confidence bands."""
        figure, axes = mock_figure_and_axes
        
        # Create overlay data with confidence bands
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        values = pd.Series(np.random.normal(100, 10, 10), index=dates)
        upper = pd.Series(np.random.normal(110, 10, 10), index=dates)
        lower = pd.Series(np.random.normal(90, 10, 10), index=dates)
        
        overlay_data = OverlayData(
            overlay_type="weekly_average",
            values=values,
            metadata={},
            confidence_upper=upper,
            confidence_lower=lower
        )
        
        # Test drawing
        overlay_widget._draw_overlay("weekly_average", overlay_data, "#0000FF")
        
        # Verify both plot and fill_between were called
        axes.plot.assert_called_once()
        axes.fill_between.assert_called_once()


# Integration tests
class TestComparisonOverlayWidgetIntegration:
    """Integration tests for the comparison overlay widget."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication instance."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    def test_full_widget_workflow(self, app):
        """Test complete workflow with real matplotlib components."""
        # Create real matplotlib figure and axes
        figure = Figure(figsize=(10, 6))
        axes = figure.add_subplot(111)
        
        # Create widget
        widget = ComparisonOverlayWidget(figure, axes)
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        np.random.seed(42)
        data = pd.Series(np.random.normal(100, 15, 50), index=dates)
        current_date = datetime(2024, 2, 20)
        
        # Add various overlays
        widget.add_weekly_average_overlay(data, current_date)
        widget.add_monthly_average_overlay(data, current_date)
        widget.add_personal_best_overlay(data, "test_metric", True)
        widget.add_historical_comparison_overlays(data, current_date, ['week'])
        
        # Verify overlays were added
        assert len(widget.overlays) > 0
        
        # Test context message generation
        message = widget.generate_context_message("test_metric", 120.0, data)
        assert isinstance(message, str)
        assert "test_metric" in message
        
        # Test clearing overlays
        widget.clear_all_overlays()
        assert len(widget.overlays) == 0
    
    def test_legend_integration(self, app):
        """Test integration between widget and legend."""
        # Create real components
        figure = Figure(figsize=(10, 6))
        axes = figure.add_subplot(111)
        widget = ComparisonOverlayWidget(figure, axes)
        
        # Create sample overlay
        dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
        values = pd.Series(np.random.normal(100, 10, 20), index=dates)
        overlay_data = OverlayData(
            overlay_type="weekly_average",
            values=values,
            metadata={'mean': 100.0, 'std': 10.0}
        )
        
        # Add overlay
        widget.add_overlay("weekly_average", overlay_data)
        
        # Verify legend was updated
        assert "weekly_average" in widget.legend.overlay_items
        
        # Test legend toggle functionality
        legend_item = widget.legend.overlay_items["weekly_average"]
        checkbox = legend_item['checkbox']
        
        # Simulate checkbox toggle
        checkbox.setChecked(False)
        
        # The signal should be connected and widget should respond
        # (In a real app, this would trigger the toggle_overlay method)