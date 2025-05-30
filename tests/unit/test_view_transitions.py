"""Unit tests for view transition framework."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QTimer, QPoint
from PyQt6.QtTest import QTest

from src.ui.view_transitions import (
    ViewTransitionManager, ViewType, TransitionType, ViewState,
    PerformanceMonitor, AnimationController, TransitionStateManager
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def transition_manager(app):
    """Create ViewTransitionManager for testing."""
    return ViewTransitionManager(accessibility_mode=False)


@pytest.fixture
def test_widgets(qtbot):
    """Create test widgets."""
    widget1 = QWidget()
    widget1.resize(200, 100)
    widget2 = QWidget()
    widget2.resize(200, 100)
    
    # Register with qtbot for proper cleanup
    qtbot.addWidget(widget1)
    qtbot.addWidget(widget2)
    
    return widget1, widget2


class TestViewState:
    """Test ViewState dataclass."""
    
    def test_view_state_creation(self):
        """Test ViewState creation with defaults."""
        state = ViewState(ViewType.DAILY)
        
        assert state.view_type == ViewType.DAILY
        assert state.data_range is None
        assert state.selected_metrics == []
        assert state.zoom_level == 1.0
        assert state.scroll_position == QPoint(0, 0)
        assert state.filters == {}
        assert state.user_selections == {}
        assert state.timestamp is not None
        
    def test_view_state_with_values(self):
        """Test ViewState creation with custom values."""
        state = ViewState(
            view_type=ViewType.WEEKLY,
            data_range=("2024-01-01", "2024-01-07"),
            selected_metrics=["heart_rate", "steps"],
            zoom_level=1.5,
            scroll_position=QPoint(10, 20),
            filters={"source": "iPhone"},
            user_selections={"period": "week"}
        )
        
        assert state.view_type == ViewType.WEEKLY
        assert state.data_range == ("2024-01-01", "2024-01-07")
        assert state.selected_metrics == ["heart_rate", "steps"]
        assert state.zoom_level == 1.5
        assert state.scroll_position == QPoint(10, 20)
        assert state.filters == {"source": "iPhone"}
        assert state.user_selections == {"period": "week"}


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        
        assert monitor.target_fps == 60
        assert monitor.frame_times == []
        assert monitor.max_frames_tracked == 60
        assert monitor.start_time is None
        assert monitor.frame_count == 0
        
    def test_start_tracking(self):
        """Test starting performance tracking."""
        monitor = PerformanceMonitor()
        monitor.start_tracking()
        
        assert monitor.start_time is not None
        assert monitor.frame_count == 0
        assert monitor.frame_times == []
        
    def test_record_frame(self):
        """Test frame recording."""
        monitor = PerformanceMonitor()
        monitor.start_tracking()
        
        # Simulate some time passing
        time.sleep(0.01)
        monitor.record_frame()
        
        assert len(monitor.frame_times) == 1
        assert monitor.frame_count == 1
        assert monitor.frame_times[0] > 0
        
    def test_get_current_fps(self):
        """Test FPS calculation."""
        monitor = PerformanceMonitor()
        monitor.start_tracking()
        
        # Record a few frames
        for _ in range(3):
            time.sleep(0.01)
            monitor.record_frame()
            
        fps = monitor.get_current_fps()
        assert fps > 0
        assert fps < 1000  # Should be reasonable


class TestAnimationController:
    """Test AnimationController class."""
    
    def test_animation_controller_initialization(self, app):
        """Test AnimationController initialization."""
        controller = AnimationController()
        
        assert controller.current_animation is None
        assert controller.quality_settings['disable_shadows'] is False
        assert controller.quality_settings['reduce_animation_steps'] is False
        
    def test_create_fade_animation(self, app, test_widgets):
        """Test fade animation creation."""
        controller = AnimationController()
        widget, _ = test_widgets
        
        animation = controller.create_fade_animation(widget, 0.0, 1.0, 300)
        
        assert animation is not None
        assert animation.duration() == 300
        assert animation.startValue() == 0.0
        assert animation.endValue() == 1.0
        
    def test_create_slide_animation(self, app, test_widgets):
        """Test slide animation creation."""
        controller = AnimationController()
        widget, _ = test_widgets
        
        from_pos = QPoint(0, 0)
        to_pos = QPoint(100, 0)
        
        animation = controller.create_slide_animation(widget, from_pos, to_pos, 300)
        
        assert animation is not None
        assert animation.duration() == 300
        assert animation.startValue() == from_pos
        assert animation.endValue() == to_pos
        
    def test_apply_quality_settings(self, app):
        """Test quality settings application."""
        controller = AnimationController()
        
        settings = {
            'disable_shadows': True,
            'reduce_animation_steps': True
        }
        
        controller.apply_quality_settings(settings)
        
        assert controller.quality_settings['disable_shadows'] is True
        assert controller.quality_settings['reduce_animation_steps'] is True


class TestTransitionStateManager:
    """Test TransitionStateManager class."""
    
    def test_state_manager_initialization(self):
        """Test TransitionStateManager initialization."""
        manager = TransitionStateManager()
        
        assert manager.state_stack == []
        assert manager.transition_cache == {}
        assert manager.max_stack_size == 10
        
    def test_capture_state(self, app, test_widgets):
        """Test state capture."""
        manager = TransitionStateManager()
        widget, _ = test_widgets
        
        # Mock widget properties
        widget.data_range = ("2024-01-01", "2024-01-07")
        widget.selected_metrics = ["heart_rate"]
        widget.zoom_level = 1.2
        
        state = manager.capture_state(ViewType.DAILY, widget)
        
        assert state.view_type == ViewType.DAILY
        assert state.data_range == ("2024-01-01", "2024-01-07")
        assert state.selected_metrics == ["heart_rate"]
        assert state.zoom_level == 1.2
        assert len(manager.state_stack) == 1
        
    def test_create_intermediate_states(self):
        """Test intermediate state creation."""
        manager = TransitionStateManager()
        
        start = ViewState(
            view_type=ViewType.DAILY,
            zoom_level=1.0,
            scroll_position=QPoint(0, 0)
        )
        
        end = ViewState(
            view_type=ViewType.WEEKLY,
            zoom_level=2.0,
            scroll_position=QPoint(100, 50)
        )
        
        states = manager.create_intermediate_states(start, end, steps=4)
        
        assert len(states) == 5  # Including start and end
        assert states[0].zoom_level == 1.0
        assert states[2].zoom_level == 1.5  # Middle state
        assert states[4].zoom_level == 2.0
        
    def test_stack_size_limit(self, app, test_widgets):
        """Test state stack size limiting."""
        manager = TransitionStateManager()
        manager.max_stack_size = 3
        widget, _ = test_widgets
        
        # Add more states than max size
        for i in range(5):
            manager.capture_state(ViewType.DAILY, widget)
            
        assert len(manager.state_stack) == 3  # Should be limited


class TestViewTransitionManager:
    """Test ViewTransitionManager class."""
    
    def test_transition_manager_initialization(self, app):
        """Test ViewTransitionManager initialization."""
        manager = ViewTransitionManager(accessibility_mode=False)
        
        assert manager.current_view is None
        assert manager.accessibility_mode is False
        assert manager.enable_animations is True
        assert manager.default_duration == 300
        
    def test_accessibility_mode(self, app):
        """Test accessibility mode functionality."""
        manager = ViewTransitionManager(accessibility_mode=True)
        
        assert manager.accessibility_mode is True
        assert manager.enable_animations is False
        
        # Test toggling
        manager.set_accessibility_mode(False)
        assert manager.accessibility_mode is False
        assert manager.enable_animations is True
        
    def test_determine_transition_type(self, app):
        """Test transition type determination."""
        manager = ViewTransitionManager()
        
        # Test zoom transition (hierarchical)
        transition_type = manager._determine_transition_type(ViewType.DAILY, ViewType.WEEKLY)
        assert transition_type == TransitionType.ZOOM
        
        # Test fade transition (fallback)
        transition_type = manager._determine_transition_type(ViewType.CONFIG, ViewType.JOURNAL)
        assert transition_type == TransitionType.FADE
        
    def test_immediate_transition_accessibility(self, app, test_widgets):
        """Test immediate transition in accessibility mode."""
        manager = ViewTransitionManager(accessibility_mode=True)
        widget1, widget2 = test_widgets
        
        # Mock signal emission
        manager.transition_completed = Mock()
        
        result = manager.transition_to(
            widget1, widget2, ViewType.DAILY, ViewType.WEEKLY
        )
        
        assert result is True
        assert manager.current_view == ViewType.WEEKLY
        manager.transition_completed.emit.assert_called_once_with(ViewType.WEEKLY)
        
    def test_get_current_view(self, app):
        """Test getting current view."""
        manager = ViewTransitionManager()
        
        assert manager.get_current_view() is None
        
        manager.current_view = ViewType.DAILY
        assert manager.get_current_view() == ViewType.DAILY
        
    def test_is_transitioning(self, app):
        """Test transition state checking."""
        manager = ViewTransitionManager()
        
        assert manager.is_transitioning() is False
        
        # Mock running animation
        mock_animation = Mock()
        mock_animation.state.return_value = mock_animation.State.Running
        manager.current_animation_group = mock_animation
        
        assert manager.is_transitioning() is True


class TestIntegration:
    """Integration tests for the transition system."""
    
    def test_full_transition_cycle(self, app, test_widgets):
        """Test a complete transition cycle."""
        manager = ViewTransitionManager(accessibility_mode=True)  # Use accessibility for speed
        widget1, widget2 = test_widgets
        
        # Set up signal tracking
        transition_started_calls = []
        transition_completed_calls = []
        
        manager.transition_started.connect(
            lambda f, t: transition_started_calls.append((f, t))
        )
        manager.transition_completed.connect(
            lambda t: transition_completed_calls.append(t)
        )
        
        # Perform transition
        result = manager.transition_to(
            widget1, widget2, ViewType.DAILY, ViewType.WEEKLY
        )
        
        assert result is True
        assert len(transition_started_calls) == 1
        assert len(transition_completed_calls) == 1
        assert transition_started_calls[0] == (ViewType.DAILY, ViewType.WEEKLY)
        assert transition_completed_calls[0] == ViewType.WEEKLY
        assert manager.get_current_view() == ViewType.WEEKLY
        
    def test_state_preservation_during_transition(self, app, test_widgets):
        """Test that state is preserved during transitions."""
        manager = ViewTransitionManager(accessibility_mode=True)
        widget1, widget2 = test_widgets
        
        # Mock widget with state
        widget1.data_range = ("2024-01-01", "2024-01-07")
        widget1.selected_metrics = ["heart_rate", "steps"]
        widget1.zoom_level = 1.5
        
        # Perform transition
        manager.transition_to(widget1, widget2, ViewType.DAILY, ViewType.WEEKLY)
        
        # Check that state was captured
        states = manager.state_manager.state_stack
        assert len(states) == 1
        assert states[0].view_type == ViewType.DAILY
        assert states[0].data_range == ("2024-01-01", "2024-01-07")
        assert states[0].selected_metrics == ["heart_rate", "steps"]
        assert states[0].zoom_level == 1.5
        
    def test_performance_monitoring_integration(self, app):
        """Test performance monitoring integration."""
        manager = ViewTransitionManager(accessibility_mode=False)
        
        # Mock quality adjustment signal
        adjustment_calls = []
        manager.performance_monitor.quality_adjustment_needed.connect(
            lambda adj: adjustment_calls.append(adj)
        )
        
        # Start tracking and simulate poor performance
        manager.performance_monitor.start_tracking()
        
        # Record frames with long frame times to trigger adjustment
        for _ in range(15):  # Enough to trigger check
            manager.performance_monitor.frame_times.append(50)  # 50ms = 20fps
            manager.performance_monitor._check_performance()
            
        # Should have triggered quality adjustment
        assert len(adjustment_calls) > 0
        assert 'disable_shadows' in adjustment_calls[0]