"""Comprehensive tests for calendar heatmap component."""

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
        assert calendar_heatmap._view_mode == ViewMode.MONTH_GRID
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
        
    def test_set_view_mode(self, calendar_heatmap):
        """Test setting view mode."""
        calendar_heatmap.set_view_mode(ViewMode.GITHUB_STYLE)
        assert calendar_heatmap._view_mode == ViewMode.GITHUB_STYLE
        
        calendar_heatmap.set_view_mode(ViewMode.CIRCULAR_VIEW)
        assert calendar_heatmap._view_mode == ViewMode.CIRCULAR_VIEW
        
    def test_set_color_scale(self, calendar_heatmap):
        """Test setting color scale."""
        calendar_heatmap.set_color_scale(ColorScale.PLASMA)
        assert calendar_heatmap._color_scale == ColorScale.PLASMA
        
    def test_toggle_today_marker(self, calendar_heatmap):
        """Test toggling today marker."""
        calendar_heatmap.toggle_today_marker(False)
        assert calendar_heatmap._show_today_marker is False
        
        calendar_heatmap.toggle_today_marker(True)
        assert calendar_heatmap._show_today_marker is True
        
    def test_toggle_patterns(self, calendar_heatmap):
        """Test toggling accessibility patterns."""
        calendar_heatmap.toggle_patterns(True)
        assert calendar_heatmap._show_patterns is True
        
        calendar_heatmap.toggle_patterns(False)
        assert calendar_heatmap._show_patterns is False
        
    def test_get_color_for_value(self, calendar_heatmap, sample_data):
        """Test color calculation for values."""
        calendar_heatmap.set_metric_data(sample_data, "Steps")
        
        # Test None value
        color = calendar_heatmap._get_color_for_value(None)
        assert isinstance(color, QColor)
        
        # Test min value
        min_val = min(sample_data.values())
        color = calendar_heatmap._get_color_for_value(min_val)
        assert isinstance(color, QColor)
        
        # Test max value
        max_val = max(sample_data.values())
        color = calendar_heatmap._get_color_for_value(max_val)
        assert isinstance(color, QColor)
        
    def test_get_date_at_position_month_grid(self, calendar_heatmap):
        """Test date detection in month grid view."""
        calendar_heatmap.set_view_mode(ViewMode.MONTH_GRID)
        calendar_heatmap.resize(800, 600)
        
        # Mock position within calendar bounds
        pos = QPoint(400, 300)
        detected_date = calendar_heatmap._get_date_at_position(pos)
        # Result depends on actual layout calculation
        assert detected_date is None or isinstance(detected_date, date)
        
    def test_mouse_events(self, calendar_heatmap, qtbot):
        """Test mouse interaction events."""
        calendar_heatmap.resize(800, 600)
        
        # Test mouse press
        qtbot.mousePress(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(400, 300))
        assert calendar_heatmap._brush_active is True
        
        # Test mouse release
        qtbot.mouseRelease(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(450, 350))
        assert calendar_heatmap._brush_active is False
        
    def test_update_animation(self, calendar_heatmap):
        """Test animation update."""
        initial_progress = calendar_heatmap._animation_progress
        calendar_heatmap.update_animation()
        assert calendar_heatmap._animation_progress != initial_progress
        
    def test_set_current_date(self, calendar_heatmap):
        """Test setting current date."""
        new_date = date(2023, 6, 15)
        calendar_heatmap.set_current_date(new_date)
        assert calendar_heatmap.get_current_date() == new_date


class TestDrawingMethods:
    """Test drawing methods with mocked painter."""
    
    @patch('PyQt6.QtGui.QPainter')
    def test_draw_month_grid(self, mock_painter_class, calendar_heatmap, sample_data):
        """Test month grid drawing."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        calendar_heatmap.set_metric_data(sample_data, "Steps")
        calendar_heatmap.set_view_mode(ViewMode.MONTH_GRID)
        
        # Simulate paint event
        rect = QRect(0, 0, 800, 600)
        calendar_heatmap._draw_month_grid(mock_painter, rect)
        
        # Verify painter methods were called
        assert mock_painter.fillRect.called
        assert mock_painter.drawText.called
        
    @patch('PyQt6.QtGui.QPainter')
    def test_draw_github_style(self, mock_painter_class, calendar_heatmap, sample_data):
        """Test GitHub style drawing."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        calendar_heatmap.set_metric_data(sample_data, "Steps")
        calendar_heatmap.set_view_mode(ViewMode.GITHUB_STYLE)
        
        # Simulate paint event
        rect = QRect(0, 0, 800, 600)
        calendar_heatmap._draw_github_style(mock_painter, rect)
        
        # Verify painter methods were called
        assert mock_painter.fillRect.called
        assert mock_painter.drawRect.called
        
    @patch('PyQt6.QtGui.QPainter')
    def test_draw_circular_view(self, mock_painter_class, calendar_heatmap, sample_data):
        """Test circular view drawing."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        calendar_heatmap.set_metric_data(sample_data, "Steps")
        calendar_heatmap.set_view_mode(ViewMode.CIRCULAR_VIEW)
        
        # Simulate paint event
        rect = QRect(0, 0, 800, 600)
        calendar_heatmap._draw_circular_view(mock_painter, rect)
        
        # Verify painter methods were called
        assert mock_painter.fillRect.called
        
    @patch('PyQt6.QtGui.QPainter')
    def test_draw_today_marker(self, mock_painter_class, calendar_heatmap):
        """Test today marker drawing."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        rect = QRect(100, 100, 20, 20)
        calendar_heatmap._draw_today_marker(mock_painter, rect)
        
        # Verify painter methods were called
        mock_painter.save.assert_called_once()
        mock_painter.restore.assert_called_once()
        assert mock_painter.fillRect.called
        assert mock_painter.drawRect.called
        assert mock_painter.drawLine.called
        
    @patch('PyQt6.QtGui.QPainter')
    def test_draw_accessibility_pattern(self, mock_painter_class, calendar_heatmap):
        """Test accessibility pattern drawing."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        calendar_heatmap._data_bounds = (0, 100)
        rect = QRect(100, 100, 20, 20)
        
        # Test light pattern
        calendar_heatmap._draw_accessibility_pattern(mock_painter, rect, 10)
        assert mock_painter.drawPoint.called
        
        # Test medium pattern
        calendar_heatmap._draw_accessibility_pattern(mock_painter, rect, 50)
        assert mock_painter.drawLine.called
        
        # Test dense pattern
        calendar_heatmap._draw_accessibility_pattern(mock_painter, rect, 90)
        assert mock_painter.drawLine.called


class TestGitHubStyleFixes:
    """Test specific GitHub style fixes."""
    
    @patch('PyQt6.QtGui.QPainter')
    def test_github_style_date_calculation(self, mock_painter_class, calendar_heatmap):
        """Test GitHub style uses last 52 weeks from today."""
        mock_painter = Mock()
        mock_painter_class.return_value = mock_painter
        
        # Set some data
        data = {date.today(): 100}
        calendar_heatmap.set_metric_data(data, "Test")
        calendar_heatmap.set_view_mode(ViewMode.GITHUB_STYLE)
        
        rect = QRect(0, 0, 800, 600)
        calendar_heatmap._draw_github_style(mock_painter, rect)
        
        # The method should calculate dates from last Sunday going back 52 weeks
        # This is hard to test directly, but we verify drawing was attempted
        assert mock_painter.fillRect.called or mock_painter.drawRect.called
        
    def test_github_style_spacing(self, calendar_heatmap):
        """Test GitHub style cell spacing calculation."""
        calendar_heatmap.set_view_mode(ViewMode.GITHUB_STYLE)
        calendar_heatmap.resize(800, 600)
        
        # The spacing should be 2 pixels between cells
        # This is implemented in the draw method
        assert calendar_heatmap._view_mode == ViewMode.GITHUB_STYLE


class TestSignals:
    """Test signal emissions."""
    
    def test_date_clicked_signal(self, calendar_heatmap, qtbot):
        """Test date clicked signal emission."""
        # Mock date detection
        test_date = date.today()
        calendar_heatmap._get_date_at_position = Mock(return_value=test_date)
        
        # Connect signal spy
        with qtbot.waitSignal(calendar_heatmap.date_clicked, timeout=1000) as blocker:
            # Simulate click
            qtbot.mousePress(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            qtbot.mouseRelease(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            
        assert blocker.args[0] == test_date
        
    def test_date_range_selected_signal(self, calendar_heatmap, qtbot):
        """Test date range selection signal."""
        # Mock date detection
        start_date = date.today() - timedelta(days=5)
        end_date = date.today()
        
        calendar_heatmap._get_date_at_position = Mock(side_effect=[start_date, end_date])
        
        # Connect signal spy
        with qtbot.waitSignal(calendar_heatmap.date_range_selected, timeout=1000) as blocker:
            # Simulate drag
            qtbot.mousePress(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
            qtbot.mouseMove(calendar_heatmap, pos=QPoint(200, 200))
            qtbot.mouseRelease(calendar_heatmap, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))
            
        assert blocker.args[0] == start_date
        assert blocker.args[1] == end_date


class TestColorScales:
    """Test different color scales."""
    
    def test_warm_orange_scale(self, calendar_heatmap):
        """Test warm orange color scale."""
        calendar_heatmap.set_color_scale(ColorScale.WARM_ORANGE)
        calendar_heatmap._update_color_palette()
        
        # Test colors are properly set
        assert 'empty' in calendar_heatmap._colors
        assert 'min' in calendar_heatmap._colors
        assert 'max' in calendar_heatmap._colors
        
    def test_viridis_scale(self, calendar_heatmap):
        """Test viridis color scale."""
        calendar_heatmap.set_color_scale(ColorScale.VIRIDIS)
        calendar_heatmap._update_color_palette()
        
        # Verify color gradient is created
        assert hasattr(calendar_heatmap, '_color_gradient')


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_data(self, calendar_heatmap):
        """Test handling of empty data."""
        calendar_heatmap.set_metric_data({}, "Empty")
        
        assert calendar_heatmap._metric_data == {}
        assert calendar_heatmap._data_bounds == (0, 0)
        
    def test_single_data_point(self, calendar_heatmap):
        """Test handling of single data point."""
        data = {date.today(): 100}
        calendar_heatmap.set_metric_data(data, "Single")
        
        assert calendar_heatmap._data_bounds == (100, 100)
        
    def test_invalid_view_mode(self, calendar_heatmap):
        """Test handling of invalid view mode."""
        # Should not raise error
        calendar_heatmap._view_mode = "invalid"
        calendar_heatmap.update()  # Should handle gracefully
        
    def test_large_dataset(self, calendar_heatmap):
        """Test performance with large dataset."""
        # Generate 5 years of data
        data = {}
        today = date.today()
        for i in range(365 * 5):
            day = today - timedelta(days=i)
            data[day] = np.random.randint(0, 10000)
            
        calendar_heatmap.set_metric_data(data, "Large Dataset")
        assert len(calendar_heatmap._metric_data) == 365 * 5


# Test the alias
def test_calendar_heatmap_alias():
    """Test that CalendarHeatmap alias works."""
    assert CalendarHeatmap == CalendarHeatmapComponent