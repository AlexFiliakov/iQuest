"""View transition framework for smooth animations between time periods."""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import time

from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsView
from PyQt6.QtCore import (
    QObject, pyqtSignal, QPropertyAnimation, QParallelAnimationGroup,
    QSequentialAnimationGroup, QEasingCurve, QTimer, QRect, QPoint, QSize
)
from PyQt6.QtGui import QTransform, QPainter

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ViewType(Enum):
    """Types of dashboard views."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    JOURNAL = "journal"
    CONFIG = "config"


class TransitionType(Enum):
    """Types of view transitions."""
    ZOOM = "zoom"
    SLIDE = "slide"
    MORPH = "morph"
    FADE = "fade"


@dataclass
class ViewState:
    """Represents the state of a view during transition."""
    view_type: ViewType
    data_range: tuple = None
    selected_metrics: List[str] = None
    zoom_level: float = 1.0
    scroll_position: QPoint = None
    filters: Dict[str, Any] = None
    user_selections: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.scroll_position is None:
            self.scroll_position = QPoint(0, 0)
        if self.filters is None:
            self.filters = {}
        if self.user_selections is None:
            self.user_selections = {}
        if self.selected_metrics is None:
            self.selected_metrics = []


class PerformanceMonitor(QObject):
    """Monitors animation performance and suggests quality adjustments."""
    
    quality_adjustment_needed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.target_fps = 60
        self.frame_times = []
        self.max_frames_tracked = 60
        self.start_time = None
        self.frame_count = 0
        
    def start_tracking(self):
        """Start performance tracking."""
        self.start_time = time.time()
        self.frame_count = 0
        self.frame_times.clear()
        
    def record_frame(self):
        """Record a frame for performance monitoring."""
        if self.start_time is None:
            return
            
        current_time = time.time()
        frame_time = (current_time - self.start_time) * 1000  # Convert to ms
        
        self.frame_times.append(frame_time)
        self.frame_count += 1
        
        # Keep only recent frame times
        if len(self.frame_times) > self.max_frames_tracked:
            self.frame_times.pop(0)
            
        # Check if adjustment needed
        if self.frame_count % 10 == 0:  # Check every 10 frames
            self._check_performance()
            
        self.start_time = current_time
        
    def _check_performance(self):
        """Check if performance adjustments are needed."""
        if not self.frame_times:
            return
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        target_frame_time = 1000 / self.target_fps  # ms per frame
        
        if avg_frame_time > target_frame_time * 1.2:  # 20% tolerance
            adjustments = self._get_quality_adjustments()
            self.quality_adjustment_needed.emit(adjustments)
            
    def _get_quality_adjustments(self) -> Dict[str, bool]:
        """Get recommended quality adjustments."""
        return {
            'disable_shadows': True,
            'reduce_animation_steps': True,
            'use_lower_resolution': True,
            'disable_antialiasing': True,
            'skip_intermediate_frames': True
        }
        
    def get_current_fps(self) -> float:
        """Get current estimated FPS."""
        if len(self.frame_times) < 2:
            return 0.0
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1000 / avg_frame_time if avg_frame_time > 0 else 0.0


class AnimationController(QObject):
    """Controls individual animations with easing and performance optimization."""
    
    animation_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_animation = None
        self.quality_settings = {
            'disable_shadows': False,
            'reduce_animation_steps': False,
            'use_lower_resolution': False,
            'disable_antialiasing': False,
            'skip_intermediate_frames': False
        }
        
    def create_fade_animation(self, widget: QWidget, from_opacity: float, 
                            to_opacity: float, duration: int = 300) -> QPropertyAnimation:
        """Create a fade in/out animation."""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(from_opacity)
        animation.setEndValue(to_opacity)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        return animation
        
    def create_zoom_animation(self, widget: QWidget, from_scale: float, 
                            to_scale: float, duration: int = 300) -> QPropertyAnimation:
        """Create a zoom in/out animation."""
        # Store original transform
        original_transform = widget.transform() if hasattr(widget, 'transform') else QTransform()
        
        animation = QPropertyAnimation(widget, b"scale")
        animation.setDuration(duration)
        animation.setStartValue(from_scale)
        animation.setEndValue(to_scale)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        return animation
        
    def create_slide_animation(self, widget: QWidget, from_pos: QPoint, 
                             to_pos: QPoint, duration: int = 300) -> QPropertyAnimation:
        """Create a slide animation."""
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(from_pos)
        animation.setEndValue(to_pos)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        return animation
        
    def create_spring_animation(self, widget: QWidget, property_name: bytes,
                              from_value: Any, to_value: Any, duration: int = 400) -> QPropertyAnimation:
        """Create a spring physics animation."""
        animation = QPropertyAnimation(widget, property_name)
        animation.setDuration(duration)
        animation.setStartValue(from_value)
        animation.setEndValue(to_value)
        
        # Custom spring easing
        curve = QEasingCurve()
        curve.setType(QEasingCurve.Type.OutElastic)
        curve.setAmplitude(1.0)
        curve.setPeriod(0.3)
        animation.setEasingCurve(curve)
        
        return animation
        
    def apply_quality_settings(self, settings: Dict[str, bool]):
        """Apply quality settings to reduce performance load."""
        self.quality_settings.update(settings)
        logger.debug(f"Applied quality settings: {settings}")


class TransitionStateManager(QObject):
    """Manages state during view transitions."""
    
    def __init__(self):
        super().__init__()
        self.state_stack = []
        self.transition_cache = {}
        self.max_stack_size = 10
        
    def capture_state(self, view_type: ViewType, widget: QWidget) -> ViewState:
        """Capture current view state."""
        state = ViewState(
            view_type=view_type,
            data_range=getattr(widget, 'data_range', None),
            selected_metrics=getattr(widget, 'selected_metrics', []),
            zoom_level=getattr(widget, 'zoom_level', 1.0),
            scroll_position=getattr(widget, 'scroll_position', QPoint(0, 0)),
            filters=getattr(widget, 'filters', {}),
            user_selections=getattr(widget, 'user_selections', {})
        )
        
        # Add to stack
        self.state_stack.append(state)
        
        # Limit stack size
        if len(self.state_stack) > self.max_stack_size:
            self.state_stack.pop(0)
            
        logger.debug(f"Captured state for {view_type.value}")
        return state
        
    def restore_state(self, widget: QWidget, state: ViewState):
        """Restore view to previous state."""
        if hasattr(widget, 'set_data_range') and state.data_range:
            widget.set_data_range(state.data_range)
            
        if hasattr(widget, 'set_selected_metrics'):
            widget.set_selected_metrics(state.selected_metrics)
            
        if hasattr(widget, 'set_zoom_level'):
            widget.set_zoom_level(state.zoom_level)
            
        if hasattr(widget, 'set_scroll_position'):
            widget.set_scroll_position(state.scroll_position)
            
        if hasattr(widget, 'set_filters'):
            widget.set_filters(state.filters)
            
        if hasattr(widget, 'set_user_selections'):
            widget.set_user_selections(state.user_selections)
            
        logger.debug(f"Restored state for {state.view_type.value}")
        
    def create_intermediate_states(self, start: ViewState, end: ViewState, 
                                 steps: int = 10) -> List[ViewState]:
        """Generate intermediate states for smooth transition."""
        states = []
        
        for i in range(steps + 1):
            t = i / steps  # Normalized time 0-1
            
            # Interpolate zoom level
            zoom = start.zoom_level + (end.zoom_level - start.zoom_level) * t
            
            # Interpolate scroll position
            scroll_x = int(start.scroll_position.x() + 
                          (end.scroll_position.x() - start.scroll_position.x()) * t)
            scroll_y = int(start.scroll_position.y() + 
                          (end.scroll_position.y() - start.scroll_position.y()) * t)
            
            intermediate = ViewState(
                view_type=end.view_type if t > 0.5 else start.view_type,
                zoom_level=zoom,
                scroll_position=QPoint(scroll_x, scroll_y),
                selected_metrics=end.selected_metrics if t > 0.5 else start.selected_metrics,
                filters=end.filters if t > 0.5 else start.filters,
                user_selections=end.user_selections if t > 0.5 else start.user_selections
            )
            
            states.append(intermediate)
            
        return states
        
    def get_previous_state(self) -> Optional[ViewState]:
        """Get the previous state from stack."""
        if len(self.state_stack) < 2:
            return None
        return self.state_stack[-2]
        
    def clear_cache(self):
        """Clear transition cache to free memory."""
        self.transition_cache.clear()
        logger.debug("Transition cache cleared")


class ViewTransitionManager(QObject):
    """Main manager for view transitions with animation framework."""
    
    transition_started = pyqtSignal(ViewType, ViewType)
    transition_completed = pyqtSignal(ViewType)
    transition_interrupted = pyqtSignal()
    
    def __init__(self, accessibility_mode: bool = False):
        super().__init__()
        self.current_view = None
        self.animation_controller = AnimationController()
        self.state_manager = TransitionStateManager()
        self.performance_monitor = PerformanceMonitor()
        self.accessibility_mode = accessibility_mode
        
        # Animation settings
        self.default_duration = 300
        self.enable_animations = not accessibility_mode
        self.current_animation_group = None
        
        # Connect performance monitor
        self.performance_monitor.quality_adjustment_needed.connect(
            self.animation_controller.apply_quality_settings
        )
        
        logger.info(f"ViewTransitionManager initialized (accessibility_mode={accessibility_mode})")
        
    def set_accessibility_mode(self, enabled: bool):
        """Enable or disable accessibility mode."""
        self.accessibility_mode = enabled
        self.enable_animations = not enabled
        logger.info(f"Accessibility mode {'enabled' if enabled else 'disabled'}")
        
    def transition_to(self, from_widget: QWidget, to_widget: QWidget, 
                     from_view: ViewType, to_view: ViewType, 
                     duration: int = None) -> bool:
        """Orchestrate transition to target view."""
        if duration is None:
            duration = 0 if self.accessibility_mode else self.default_duration
            
        logger.info(f"Starting transition: {from_view.value} → {to_view.value}")
        
        # Interrupt any current animation
        self._interrupt_current_animation()
        
        # Capture current state
        current_state = self.state_manager.capture_state(from_view, from_widget)
        
        # Determine transition type
        transition_type = self._determine_transition_type(from_view, to_view)
        
        # Emit transition started signal
        self.transition_started.emit(from_view, to_view)
        
        # Start performance monitoring
        self.performance_monitor.start_tracking()
        
        if not self.enable_animations or duration == 0:
            # Immediate transition for accessibility mode
            self._complete_immediate_transition(to_view)
            return True
            
        # Create and execute animation
        try:
            animation = self._create_transition_animation(
                from_widget, to_widget, transition_type, duration
            )
            
            if animation:
                self.current_animation_group = animation
                animation.finished.connect(lambda: self._on_transition_complete(to_view))
                animation.start()
                
                self.current_view = to_view
                return True
            else:
                # Fallback to immediate transition
                self._complete_immediate_transition(to_view)
                return True
                
        except Exception as e:
            logger.error(f"Animation creation failed: {e}")
            self._complete_immediate_transition(to_view)
            return False
            
    def _determine_transition_type(self, from_view: ViewType, to_view: ViewType) -> TransitionType:
        """Determine the appropriate transition type based on view types."""
        # Define view hierarchy levels
        view_levels = {
            ViewType.DAILY: 1,
            ViewType.WEEKLY: 2,
            ViewType.MONTHLY: 3,
            ViewType.JOURNAL: 0,
            ViewType.CONFIG: 0
        }
        
        from_level = view_levels.get(from_view, 0)
        to_level = view_levels.get(to_view, 0)
        
        # Zoom for hierarchical transitions
        if from_level != to_level and from_level > 0 and to_level > 0:
            return TransitionType.ZOOM
            
        # Slide for same-level transitions
        if from_level == to_level and from_level > 0:
            return TransitionType.SLIDE
            
        # Morph for special cases (future use)
        # return TransitionType.MORPH
        
        # Fade as fallback
        return TransitionType.FADE
        
    def _create_transition_animation(self, from_widget: QWidget, to_widget: QWidget,
                                   transition_type: TransitionType, duration: int) -> QParallelAnimationGroup:
        """Create the appropriate transition animation."""
        animation_group = QParallelAnimationGroup()
        
        if transition_type == TransitionType.ZOOM:
            zoom_animations = self._create_zoom_transition(from_widget, to_widget, duration)
            for anim in zoom_animations:
                animation_group.addAnimation(anim)
                
        elif transition_type == TransitionType.SLIDE:
            slide_animations = self._create_slide_transition(from_widget, to_widget, duration)
            for anim in slide_animations:
                animation_group.addAnimation(anim)
                
        elif transition_type == TransitionType.MORPH:
            morph_animations = self._create_morph_transition(from_widget, to_widget, duration)
            for anim in morph_animations:
                animation_group.addAnimation(anim)
                
        else:  # FADE
            fade_animations = self._create_fade_transition(from_widget, to_widget, duration)
            for anim in fade_animations:
                animation_group.addAnimation(anim)
                
        return animation_group
        
    def _create_zoom_transition(self, from_widget: QWidget, to_widget: QWidget, 
                              duration: int) -> List[QPropertyAnimation]:
        """Create zoom in/out transition animations."""
        animations = []
        
        # Fade out the from widget
        fade_out = self.animation_controller.create_fade_animation(
            from_widget, 1.0, 0.0, duration // 2
        )
        animations.append(fade_out)
        
        # Scale animation for zoom effect
        if hasattr(from_widget, 'setTransform'):
            zoom_out = self.animation_controller.create_zoom_animation(
                from_widget, 1.0, 0.8, duration // 2
            )
            animations.append(zoom_out)
            
        # Delayed fade in for to widget
        fade_in = self.animation_controller.create_fade_animation(
            to_widget, 0.0, 1.0, duration // 2
        )
        
        # Start fade in after half duration
        fade_in_timer = QTimer()
        fade_in_timer.setSingleShot(True)
        fade_in_timer.timeout.connect(fade_in.start)
        fade_in_timer.start(duration // 2)
        
        animations.append(fade_in)
        
        return animations
        
    def _create_slide_transition(self, from_widget: QWidget, to_widget: QWidget, 
                               duration: int) -> List[QPropertyAnimation]:
        """Create slide transition animations."""
        animations = []
        
        # Get widget positions
        from_pos = from_widget.pos()
        widget_width = from_widget.width()
        
        # Slide from widget out to the left
        slide_out = self.animation_controller.create_slide_animation(
            from_widget, from_pos, QPoint(from_pos.x() - widget_width, from_pos.y()), duration
        )
        animations.append(slide_out)
        
        # Slide to widget in from the right
        to_start_pos = QPoint(from_pos.x() + widget_width, from_pos.y())
        slide_in = self.animation_controller.create_slide_animation(
            to_widget, to_start_pos, from_pos, duration
        )
        animations.append(slide_in)
        
        return animations
        
    def _create_morph_transition(self, from_widget: QWidget, to_widget: QWidget, 
                               duration: int) -> List[QPropertyAnimation]:
        """Create morph transition animations (for future chart type changes)."""
        animations = []
        
        # For now, use a combination of fade and scale
        fade_out = self.animation_controller.create_fade_animation(
            from_widget, 1.0, 0.0, duration // 2
        )
        animations.append(fade_out)
        
        fade_in = self.animation_controller.create_fade_animation(
            to_widget, 0.0, 1.0, duration // 2
        )
        
        # Start fade in after half duration
        fade_in_timer = QTimer()
        fade_in_timer.setSingleShot(True)
        fade_in_timer.timeout.connect(fade_in.start)
        fade_in_timer.start(duration // 2)
        
        animations.append(fade_in)
        
        return animations
        
    def _create_fade_transition(self, from_widget: QWidget, to_widget: QWidget, 
                              duration: int) -> List[QPropertyAnimation]:
        """Create simple fade transition animations."""
        animations = []
        
        # Fade out current widget
        fade_out = self.animation_controller.create_fade_animation(
            from_widget, 1.0, 0.0, duration // 2
        )
        animations.append(fade_out)
        
        # Fade in new widget
        fade_in = self.animation_controller.create_fade_animation(
            to_widget, 0.0, 1.0, duration // 2
        )
        
        # Start fade in after fade out completes
        fade_in_timer = QTimer()
        fade_in_timer.setSingleShot(True)
        fade_in_timer.timeout.connect(fade_in.start)
        fade_in_timer.start(duration // 2)
        
        animations.append(fade_in)
        
        return animations
        
    def _interrupt_current_animation(self):
        """Interrupt any currently running animation."""
        if self.current_animation_group and self.current_animation_group.state() == self.current_animation_group.State.Running:
            self.current_animation_group.stop()
            self.transition_interrupted.emit()
            logger.debug("Current animation interrupted")
            
    def _on_transition_complete(self, target_view: ViewType):
        """Handle transition completion."""
        self.current_view = target_view
        self.current_animation_group = None
        
        # Log performance metrics
        fps = self.performance_monitor.get_current_fps()
        logger.info(f"Transition to {target_view.value} completed (FPS: {fps:.1f})")
        
        self.transition_completed.emit(target_view)
        
    def _complete_immediate_transition(self, target_view: ViewType):
        """Complete transition immediately (accessibility mode)."""
        self.current_view = target_view
        self.transition_completed.emit(target_view)
        logger.debug(f"Immediate transition to {target_view.value}")
        
    def get_current_view(self) -> Optional[ViewType]:
        """Get the current view type."""
        return self.current_view
        
    def is_transitioning(self) -> bool:
        """Check if a transition is currently in progress."""
        return (self.current_animation_group is not None and 
                self.current_animation_group.state() == self.current_animation_group.State.Running)