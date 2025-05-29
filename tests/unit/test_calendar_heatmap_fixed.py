"""Fixed tests for calendar heatmap component."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QWidget

from src.ui.charts.calendar_heatmap import (
    CalendarHeatmapComponent, CalendarHeatmap, ViewMode, ColorScale
)


@pytest.fixture
def app(qtbot):
    """Create QApplication for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def calendar_heatmap(qtbot):
    """Create calendar heatmap instance."""
    widget = CalendarHeatmapComponent()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def sample_data():
    """Generate sample metric data."""
    data = {}
    today = date.today()
    for i in range(365):
        day = today - timedelta(days=i)
        value = 5000 + np.random.randint(-2000, 3000)
        data[day] = value
    return data


class TestCalendarHeatmapComponent:
    """Test CalendarHeatmapComponent class."""
    
    def test_initialization(self, calendar_heatmap):
        """Test component initialization."""
        assert calendar_heatmap._view_mode == ViewMode.GITHUB_STYLE  # Default is GitHub style
        assert calendar_heatmap._metric_type == ""
        assert calendar_heatmap._metric_data == {}
        assert calendar_heatmap._current_date == date.today()
        assert calendar_heatmap._show_today_marker is True
        assert calendar_heatmap._show_patterns is False
        
    def test_set_metric_data(self, calendar_heatmap, sample_data):
        """Test setting metric data."""
        calendar_heatmap.set_metric_data("Steps", sample_data)
        
        assert calendar_heatmap._metric_data == sample_data
        assert calendar_heatmap._metric_type == "Steps"
        assert calendar_heatmap._data_bounds[0] == min(sample_data.values())
        assert calendar_heatmap._data_bounds[1] == max(sample_data.values())
        
    def test_change_view_mode(self, calendar_heatmap):
        """Test changing view mode internally."""
        calendar_heatmap._change_view_mode(ViewMode.MONTH_GRID)
        assert calendar_heatmap._view_mode == ViewMode.MONTH_GRID
        
        calendar_heatmap._change_view_mode(ViewMode.CIRCULAR)
        assert calendar_heatmap._view_mode == ViewMode.CIRCULAR
        
    def test_change_color_scale(self, calendar_heatmap):
        """Test changing color scale internally."""
        calendar_heatmap._change_color_scale("Viridis")
        assert calendar_heatmap._color_scale == ColorScale.VIRIDIS
        
        calendar_heatmap._change_color_scale("Warm Orange")
        assert calendar_heatmap._color_scale == ColorScale.WARM_ORANGE
        
    def test_toggle_patterns(self, calendar_heatmap):
        """Test toggling accessibility patterns."""
        calendar_heatmap._toggle_patterns(True)
        assert calendar_heatmap._show_patterns is True
        
        calendar_heatmap._toggle_patterns(False)
        assert calendar_heatmap._show_patterns is False
        
    def test_get_color_for_value(self, calendar_heatmap, sample_data):
        """Test color calculation for values."""
        calendar_heatmap.set_metric_data("Steps", sample_data)
        
        # Test None value
        color = calendar_heatmap._get_color_for_value(None)
        assert isinstance(color, QColor)
        assert color.name() == "#F0F0F0"  # Light gray for missing data
        
        # Test min value
        min_val = min(sample_data.values())
        color = calendar_heatmap._get_color_for_value(min_val)
        assert isinstance(color, QColor)
        
        # Test max value
        max_val = max(sample_data.values())
        color = calendar_heatmap._get_color_for_value(max_val)
        assert isinstance(color, QColor)
        
    def test_animation_progress_property(self, calendar_heatmap):
        """Test animation progress property."""
        initial_progress = calendar_heatmap.animationProgress
        assert 0 <= initial_progress <= 1
        
        calendar_heatmap.animationProgress = 0.5
        assert calendar_heatmap.animationProgress == 0.5
        assert calendar_heatmap._animation_progress == 0.5
        
    def test_set_current_date(self, calendar_heatmap):
        """Test setting current date."""
        new_date = date(2023, 6, 15)
        calendar_heatmap.set_current_date(new_date)
        assert calendar_heatmap.get_current_date() == new_date
        
    def test_color_scale_initialization(self, calendar_heatmap):
        """Test color scales are properly initialized."""
        assert ColorScale.WARM_ORANGE in calendar_heatmap._color_scales
        assert ColorScale.VIRIDIS in calendar_heatmap._color_scales
        assert ColorScale.CIVIDIS in calendar_heatmap._color_scales
        
        # Check each scale has colors
        for scale_name, colors in calendar_heatmap._color_scales.items():
            assert len(colors) > 0
            assert all(isinstance(c, QColor) for c in colors)


class TestMouseInteraction:
    """Test mouse interaction with proper setup."""
    
    def test_mouse_press_release(self, calendar_heatmap, qtbot):
        """Test mouse press and release events."""
        calendar_heatmap.resize(800, 600)
        
        # Mock the date detection method
        test_date = date.today()
        calendar_heatmap._get_date_at_position = Mock(return_value=test_date)
        
        # Test mouse press
        pos = QPoint(400, 300)
        qtbot.mousePress(calendar_heatmap, Qt.MouseButton.LeftButton, pos=pos)
        
        # Verify selection started
        assert calendar_heatmap._selection_start == test_date
        assert calendar_heatmap._brush_active is True
        
        # Test mouse release
        qtbot.mouseRelease(calendar_heatmap, Qt.MouseButton.LeftButton, pos=pos)
        
        # Verify selection ended
        assert calendar_heatmap._brush_active is False
        
    def test_hover_interaction(self, calendar_heatmap, qtbot):
        """Test hover functionality."""
        calendar_heatmap.resize(800, 600)
        
        # Mock date detection
        test_date = date.today()
        calendar_heatmap._get_date_at_position = Mock(return_value=test_date)
        
        # Add data for the hover date
        calendar_heatmap.set_metric_data("Steps", {test_date: 5000})
        
        # Simulate mouse move
        pos = QPoint(400, 300)
        calendar_heatmap.mouseMoveEvent(Mock(position=Mock(return_value=pos)))
        
        # Verify hover state updated
        assert calendar_heatmap._hover_date == test_date


class TestDataHandling:
    """Test data handling edge cases."""
    
    def test_empty_data(self, calendar_heatmap):
        """Test handling of empty data."""
        calendar_heatmap.set_metric_data("Empty", {})
        
        assert calendar_heatmap._metric_data == {}
        assert calendar_heatmap._data_bounds == (0, 1)  # Default bounds
        
    def test_single_data_point(self, calendar_heatmap):
        """Test handling of single data point."""
        data = {date.today(): 100}
        calendar_heatmap.set_metric_data("Single", data)
        
        assert calendar_heatmap._data_bounds == (100, 100)
        
    def test_large_dataset(self, calendar_heatmap):
        """Test performance with large dataset."""
        # Generate 5 years of data
        data = {}
        today = date.today()
        for i in range(365 * 5):
            day = today - timedelta(days=i)
            data[day] = np.random.randint(0, 10000)
            
        calendar_heatmap.set_metric_data("Large Dataset", data)
        assert len(calendar_heatmap._metric_data) == 365 * 5
        
    def test_data_bounds_calculation(self, calendar_heatmap):
        """Test data bounds are correctly calculated."""
        data = {
            date(2023, 1, 1): 100,
            date(2023, 1, 2): 500,
            date(2023, 1, 3): 300
        }
        calendar_heatmap.set_metric_data("Test", data)
        
        assert calendar_heatmap._data_bounds == (100, 500)


class TestGitHubStyleSpecifics:
    """Test GitHub style specific functionality."""
    
    def test_github_style_is_default(self, calendar_heatmap):
        """Test that GitHub style is the default view."""
        assert calendar_heatmap._view_mode == ViewMode.GITHUB_STYLE
        
    def test_github_style_rendering(self, calendar_heatmap, sample_data):
        """Test GitHub style rendering setup."""
        calendar_heatmap.set_metric_data("Steps", sample_data)
        calendar_heatmap._change_view_mode(ViewMode.GITHUB_STYLE)
        
        # The actual rendering happens in paintEvent
        # We can at least verify the mode is set correctly
        assert calendar_heatmap._view_mode == ViewMode.GITHUB_STYLE
        
        # Verify widget is set up for painting
        assert calendar_heatmap.width() > 0
        assert calendar_heatmap.height() > 0


class TestColorInterpolation:
    """Test color interpolation functionality."""
    
    def test_color_interpolation_extremes(self, calendar_heatmap):
        """Test color interpolation at extreme values."""
        data = {date.today(): 100, date.today() - timedelta(days=1): 1000}
        calendar_heatmap.set_metric_data("Test", data)
        
        # Test minimum value
        color_min = calendar_heatmap._get_color_for_value(100)
        assert isinstance(color_min, QColor)
        
        # Test maximum value
        color_max = calendar_heatmap._get_color_for_value(1000)
        assert isinstance(color_max, QColor)
        
        # Test middle value
        color_mid = calendar_heatmap._get_color_for_value(550)
        assert isinstance(color_mid, QColor)
        
    def test_color_interpolation_edge_cases(self, calendar_heatmap):
        """Test color interpolation edge cases."""
        # Single value dataset
        data = {date.today(): 500}
        calendar_heatmap.set_metric_data("Test", data)
        
        # When min == max, normalized should be 0.5
        color = calendar_heatmap._get_color_for_value(500)
        assert isinstance(color, QColor)


class TestSignals:
    """Test signal emissions."""
    
    def test_view_mode_changed_signal(self, calendar_heatmap, qtbot):
        """Test view mode changed signal."""
        with qtbot.waitSignal(calendar_heatmap.view_mode_changed, timeout=1000) as blocker:
            calendar_heatmap._change_view_mode(ViewMode.MONTH_GRID)
            
        assert blocker.args[0] == ViewMode.MONTH_GRID
        
    def test_date_clicked_signal(self, calendar_heatmap, qtbot):
        """Test date clicked signal."""
        test_date = date.today()
        calendar_heatmap._get_date_at_position = Mock(return_value=test_date)
        
        with qtbot.waitSignal(calendar_heatmap.date_clicked, timeout=1000) as blocker:
            # Simulate single click
            pos = QPoint(100, 100)
            qtbot.mousePress(calendar_heatmap, Qt.MouseButton.LeftButton, pos=pos)
            qtbot.mouseRelease(calendar_heatmap, Qt.MouseButton.LeftButton, pos=pos)
            
        assert blocker.args[0] == test_date


# Test the alias
def test_calendar_heatmap_alias():
    """Test that CalendarHeatmap alias works."""
    assert CalendarHeatmap == CalendarHeatmapComponent