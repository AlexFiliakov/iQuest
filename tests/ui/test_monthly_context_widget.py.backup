"""
UI tests for MonthlyContextWidget and related components.
Tests widget creation, interaction, and visual updates.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QMouseEvent

from src.ui.monthly_context_widget import (
    MonthlyContextWidget, PercentileGaugeWidget, GoalProgressWidget,
    FloatingLabel, MonthlyContextVisualization
)
from src.analytics.monthly_context_provider import MonthlyContextProvider, WeekContext


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def mock_context_provider():
    """Create mock context provider."""
    provider = Mock(spec=MonthlyContextProvider)
    
    # Mock context data
    mock_context = WeekContext(
        week_number=1, month=1, year=2025, metric_name="steps",
        percentile_rank=75.0, is_best_week=False, is_worst_week=False,
        goal_progress=80.0, seasonal_factor=1.1, monthly_average=50000,
        current_week_value=55000, rank_within_month=2, total_weeks_in_month=4,
        confidence_level=0.8, exceptional_reason="Above average performance"
    )
    
    provider.get_week_context.return_value = mock_context
    return provider


class TestPercentileGaugeWidget:
    """Test PercentileGaugeWidget functionality."""
    
    def test_widget_creation(self, qapp):
        """Test gauge widget creation."""
        widget = PercentileGaugeWidget()
        assert widget.percentile == 50.0
        assert widget.category == "average"
        assert widget.size().width() == 80
        assert widget.size().height() == 80
        
    def test_set_percentile(self, qapp):
        """Test setting percentile values."""
        widget = PercentileGaugeWidget()
        
        widget.set_percentile(85.0, "above_average")
        assert widget.percentile == 85.0
        assert widget.category == "above_average"
        
        widget.set_percentile(95.0, "exceptional")
        assert widget.percentile == 95.0
        assert widget.category == "exceptional"
        
    def test_paint_event_no_crash(self, qapp):
        """Test that paint event doesn't crash."""
        widget = PercentileGaugeWidget()
        widget.set_percentile(75.0, "above_average")
        
        # Trigger paint event - should not crash
        widget.show()
        widget.repaint()
        widget.hide()


class TestGoalProgressWidget:
    """Test GoalProgressWidget functionality."""
    
    def test_widget_creation(self, qapp):
        """Test progress widget creation."""
        widget = GoalProgressWidget()
        assert widget.progress == 0.0
        assert widget.on_track is True
        assert widget.projected_end == 0.0
        assert widget.height() == 60
        
    def test_set_progress(self, qapp):
        """Test setting progress values."""
        widget = GoalProgressWidget()
        
        widget.set_progress(75.5, True, 85.0)
        assert widget.progress == 75.5
        assert widget.on_track is True
        assert widget.projected_end == 85.0
        
        widget.set_progress(45.0, False, 60.0)
        assert widget.progress == 45.0
        assert widget.on_track is False
        assert widget.projected_end == 60.0
        
    def test_paint_event_no_crash(self, qapp):
        """Test that paint event doesn't crash."""
        widget = GoalProgressWidget()
        widget.set_progress(60.0, True, 75.0)
        
        # Trigger paint event - should not crash
        widget.show()
        widget.repaint()
        widget.hide()


class TestFloatingLabel:
    """Test FloatingLabel functionality."""
    
    def test_label_creation(self, qapp):
        """Test floating label creation."""
        label = FloatingLabel("Test Label")
        assert label.text() == "Test Label"
        assert not label.isVisible()  # Should start hidden
        
    def test_show_at_position(self, qapp):
        """Test showing label at specific position."""
        label = FloatingLabel("Test Label")
        position = QPoint(100, 50)
        
        label.show_at(position)
        assert label.isVisible()
        assert label.pos() == position
        
    def test_hide_with_fade(self, qapp):
        """Test hiding label with fade effect."""
        label = FloatingLabel("Test Label")
        label.show()
        
        label.hide_with_fade()
        # Animation should be started (we can't easily test completion)
        assert label.fade_animation.state() != label.fade_animation.State.Stopped


class TestMonthlyContextVisualization:
    """Test MonthlyContextVisualization functionality."""
    
    def test_widget_creation(self, qapp):
        """Test visualization widget creation."""
        widget = MonthlyContextVisualization()
        assert widget.week_context is None
        assert widget.background_gradient is None
        assert len(widget.floating_labels) == 4  # Four labels expected
        assert widget.hasMouseTracking()
        
    def test_set_week_context(self, qapp):
        """Test setting week context."""
        widget = MonthlyContextVisualization()
        
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=85.0, is_best_week=True, is_worst_week=False,
            goal_progress=90.0, seasonal_factor=1.2, monthly_average=50000,
            current_week_value=60000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.9, exceptional_reason="Best week of month"
        )
        
        widget.set_week_context(context)
        assert widget.week_context == context
        assert widget.background_gradient is not None
        
    def test_mouse_move_event(self, qapp):
        """Test mouse movement for floating labels."""
        widget = MonthlyContextVisualization()
        widget.resize(400, 200)
        
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=75.0, is_best_week=False, is_worst_week=False,
            goal_progress=80.0, seasonal_factor=1.1, monthly_average=50000,
            current_week_value=55000, rank_within_month=2, total_weeks_in_month=4,
            confidence_level=0.8
        )
        widget.set_week_context(context)
        
        # Simulate mouse move in widget area
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPoint(100, 100),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        widget.mouseMoveEvent(event)
        
        # Should not crash and should handle event gracefully
        
    def test_mouse_press_event_drill_down(self, qapp):
        """Test mouse press event for drill-down."""
        widget = MonthlyContextVisualization()
        
        context = WeekContext(
            week_number=15, month=4, year=2025, metric_name="steps",
            percentile_rank=60.0, is_best_week=False, is_worst_week=False,
            goal_progress=70.0, seasonal_factor=1.0, monthly_average=45000,
            current_week_value=48000, rank_within_month=3, total_weeks_in_month=5,
            confidence_level=0.7
        )
        widget.set_week_context(context)
        
        # Connect signal to test
        signal_received = []
        widget.drill_down_requested.connect(
            lambda week, year: signal_received.append((week, year))
        )
        
        # Simulate left click
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        widget.mousePressEvent(event)
        
        # Should emit drill-down signal
        assert len(signal_received) == 1
        assert signal_received[0] == (15, 2025)
        
    def test_paint_event_no_crash(self, qapp):
        """Test that paint event doesn't crash with and without context."""
        widget = MonthlyContextVisualization()
        widget.resize(400, 200)
        
        # Test paint without context
        widget.show()
        widget.repaint()
        
        # Test paint with context
        context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=80.0, is_best_week=False, is_worst_week=False,
            goal_progress=85.0, seasonal_factor=1.1, monthly_average=50000,
            current_week_value=55000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.8
        )
        widget.set_week_context(context)
        widget.repaint()
        
        widget.hide()


class TestMonthlyContextWidget:
    """Test complete MonthlyContextWidget functionality."""
    
    def test_widget_creation(self, qapp, mock_context_provider):
        """Test main widget creation."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Check components exist
        assert widget.context_provider == mock_context_provider
        assert widget.percentile_gauge is not None
        assert widget.goal_progress is not None
        assert widget.context_viz is not None
        assert widget.best_worst_label is not None
        assert widget.seasonal_label is not None
        assert widget.toggle_btn is not None
        
    def test_widget_creation_without_provider(self, qapp):
        """Test widget creation without context provider."""
        widget = MonthlyContextWidget()
        assert widget.context_provider is None
        assert widget.current_context is None
        
    def test_set_context_provider(self, qapp, mock_context_provider):
        """Test setting context provider."""
        widget = MonthlyContextWidget()
        widget.set_context_provider(mock_context_provider)
        assert widget.context_provider == mock_context_provider
        
    def test_update_context(self, qapp, mock_context_provider):
        """Test updating widget context."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        widget.update_context(1, 2025, "steps")
        
        # Should call context provider
        mock_context_provider.get_week_context.assert_called_once_with(1, 2025, "steps")
        assert widget.current_context is not None
        
    def test_update_context_no_provider(self, qapp):
        """Test updating context without provider."""
        widget = MonthlyContextWidget()
        
        # Should not crash
        widget.update_context(1, 2025, "steps")
        assert widget.current_context is None
        
    def test_update_displays_best_week(self, qapp, mock_context_provider):
        """Test display updates for best week."""
        # Modify mock to return best week context
        best_week_context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=95.0, is_best_week=True, is_worst_week=False,
            goal_progress=90.0, seasonal_factor=1.2, monthly_average=50000,
            current_week_value=65000, rank_within_month=1, total_weeks_in_month=4,
            confidence_level=0.9, exceptional_reason="Top performance"
        )
        mock_context_provider.get_week_context.return_value = best_week_context
        
        widget = MonthlyContextWidget(mock_context_provider)
        widget.update_context(1, 2025, "steps")
        
        # Check display updates
        assert "Best Week" in widget.best_worst_label.text()
        assert widget.percentile_gauge.percentile == 95.0
        assert widget.percentile_gauge.category == "exceptional"
        
    def test_update_displays_worst_week(self, qapp, mock_context_provider):
        """Test display updates for worst week."""
        # Modify mock to return worst week context
        worst_week_context = WeekContext(
            week_number=3, month=1, year=2025, metric_name="steps",
            percentile_rank=5.0, is_best_week=False, is_worst_week=True,
            goal_progress=30.0, seasonal_factor=0.9, monthly_average=50000,
            current_week_value=25000, rank_within_month=4, total_weeks_in_month=4,
            confidence_level=0.6, exceptional_reason="Unusual low performance"
        )
        mock_context_provider.get_week_context.return_value = worst_week_context
        
        widget = MonthlyContextWidget(mock_context_provider)
        widget.update_context(3, 2025, "steps")
        
        # Check display updates
        assert "Worst Week" in widget.best_worst_label.text()
        assert widget.percentile_gauge.percentile == 5.0
        assert widget.percentile_gauge.category == "below_average"
        
    def test_seasonal_adjustment_display(self, qapp, mock_context_provider):
        """Test seasonal adjustment display."""
        # Peak season context
        peak_context = WeekContext(
            week_number=27, month=7, year=2025, metric_name="steps",
            percentile_rank=70.0, is_best_week=False, is_worst_week=False,
            goal_progress=75.0, seasonal_factor=1.15, monthly_average=55000,
            current_week_value=58000, rank_within_month=2, total_weeks_in_month=4,
            confidence_level=0.8
        )
        mock_context_provider.get_week_context.return_value = peak_context
        
        widget = MonthlyContextWidget(mock_context_provider)
        widget.update_context(27, 2025, "steps")
        
        # Check seasonal display
        assert "Peak Season" in widget.seasonal_label.text()
        
        # Off season context
        off_context = WeekContext(
            week_number=1, month=1, year=2025, metric_name="steps",
            percentile_rank=60.0, is_best_week=False, is_worst_week=False,
            goal_progress=65.0, seasonal_factor=0.85, monthly_average=45000,
            current_week_value=47000, rank_within_month=2, total_weeks_in_month=4,
            confidence_level=0.7
        )
        mock_context_provider.get_week_context.return_value = off_context
        
        widget.update_context(1, 2025, "steps")
        assert "Off Season" in widget.seasonal_label.text()
        
    def test_drill_down_signal_propagation(self, qapp, mock_context_provider):
        """Test drill-down signal propagation."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Connect signal to test
        signal_received = []
        widget.drill_down_requested.connect(
            lambda week, year: signal_received.append((week, year))
        )
        
        # Trigger drill-down from visualization widget
        widget.context_viz.drill_down_requested.emit(15, 2025)
        
        # Should propagate signal
        assert len(signal_received) == 1
        assert signal_received[0] == (15, 2025)
        
    def test_widget_styling(self, qapp, mock_context_provider):
        """Test widget styling and appearance."""
        widget = MonthlyContextWidget(mock_context_provider)
        widget.show()
        
        # Check that styling is applied (basic test)
        style_sheet = widget.styleSheet()
        assert "QGroupBox" in style_sheet
        assert "#5D4E37" in style_sheet  # Primary text color
        assert "#FF8C42" in style_sheet  # Button color
        
        widget.hide()
        
    @patch('src.ui.monthly_context_widget.logger')
    def test_update_context_error_handling(self, mock_logger, qapp, mock_context_provider):
        """Test error handling in context updates."""
        # Make context provider raise exception
        mock_context_provider.get_week_context.side_effect = Exception("Test error")
        
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Should not crash and should log error
        widget.update_context(1, 2025, "steps")
        mock_logger.error.assert_called_once()
        
    def test_widget_components_integration(self, qapp, mock_context_provider):
        """Test integration between widget components."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Update context and verify all components are updated
        widget.update_context(1, 2025, "steps")
        
        # All components should have received updates
        assert widget.current_context is not None
        assert widget.percentile_gauge.percentile > 0
        assert widget.context_viz.week_context is not None
        
        # Labels should have content
        assert widget.best_worst_label.text() != "—"
        assert "Season" in widget.seasonal_label.text()


class TestWidgetInteractions:
    """Test widget interactions and user experience."""
    
    def test_mouse_interaction_flow(self, qapp, mock_context_provider):
        """Test complete mouse interaction flow."""
        widget = MonthlyContextWidget(mock_context_provider)
        widget.resize(600, 400)
        widget.show()
        
        # Update with context
        widget.update_context(1, 2025, "steps")
        
        # Test mouse movement on visualization (should show floating labels)
        viz_widget = widget.context_viz
        
        # Simulate mouse enter
        QTest.mouseMove(viz_widget, QPoint(100, 100))
        
        # Simulate mouse click (should emit drill-down)
        signal_received = []
        widget.drill_down_requested.connect(
            lambda week, year: signal_received.append((week, year))
        )
        
        QTest.mouseClick(viz_widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(100, 100))
        
        # Should receive drill-down signal
        assert len(signal_received) == 1
        
        widget.hide()
        
    def test_accessibility_features(self, qapp, mock_context_provider):
        """Test accessibility features."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Check that widgets have tooltips or accessible names
        assert widget.percentile_gauge.toolTip() != ""
        
        # Check that focus can be set on interactive elements
        widget.toggle_btn.setFocus()
        assert widget.toggle_btn.hasFocus()
        
    def test_responsive_layout(self, qapp, mock_context_provider):
        """Test widget layout responsiveness."""
        widget = MonthlyContextWidget(mock_context_provider)
        
        # Test different sizes
        sizes = [(400, 300), (800, 600), (1200, 800)]
        
        for width, height in sizes:
            widget.resize(width, height)
            widget.show()
            widget.repaint()
            # Should not crash and should layout properly
            
        widget.hide()