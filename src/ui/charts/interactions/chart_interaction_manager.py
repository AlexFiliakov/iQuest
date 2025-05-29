"""
Main interaction manager for health charts.

Coordinates all interactive behaviors including zoom, pan, selection,
tooltips, and keyboard navigation.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QPointF, Qt, QTimer, QRectF
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QWheelEvent, QTouchEvent
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from .zoom_controller import SmoothZoomController
from .brush_selector import BrushRangeSelector
from .wsj_tooltip import WSJTooltip
from .keyboard_navigation import KeyboardNavigationHandler
from .crossfilter_manager import CrossfilterManager
from .drill_down_navigator import DrillDownNavigator
from .performance_monitor import InteractionPerformanceMonitor

import logging
logger = logging.getLogger(__name__)


class ChartInteractionManager(QObject):
    """Manages all interactions for health charts"""
    
    # Signals
    point_hovered = pyqtSignal(int, dict)  # index, data
    point_clicked = pyqtSignal(int, dict)
    range_selected = pyqtSignal(float, float)  # start, end
    zoom_changed = pyqtSignal(float, QPointF)  # level, center
    drill_down_requested = pyqtSignal(str, dict)  # target_view, context
    crossfilter_updated = pyqtSignal(str, object)  # filter_id, filter_value
    
    def __init__(self, chart_widget: QWidget):
        super().__init__()
        self.chart_widget = chart_widget
        self.chart_data: Optional[Dict[str, Any]] = None
        self.visible_range: Optional[Tuple[float, float]] = None
        
        # Initialize sub-controllers
        self.zoom_controller = SmoothZoomController()
        self.brush_selector = BrushRangeSelector(chart_widget)
        self.tooltip = WSJTooltip(chart_widget)
        self.keyboard_handler = KeyboardNavigationHandler()
        self.crossfilter_manager = CrossfilterManager()
        self.drill_down_navigator = DrillDownNavigator()
        self.performance_monitor = InteractionPerformanceMonitor(target_frame_time=16.0)
        
        # Connect sub-controller signals
        self._connect_signals()
        
        # Interaction state
        self.is_panning = False
        self.pan_start_pos = QPointF()
        self.hover_index = -1
        self.last_hover_pos = QPointF()
        
        # Performance optimization
        self.hover_threshold = 10  # pixels
        self.hover_timer = QTimer()
        self.hover_timer.timeout.connect(self._process_hover)
        self.hover_timer.setSingleShot(True)
        
        # Touch gesture state
        self.touch_points: Dict[int, QPointF] = {}
        self.initial_touch_distance = 0.0
        self.touch_zoom_active = False
        
        # Install event filters
        self.install_event_filters()
        
    def _connect_signals(self):
        """Connect signals from sub-controllers"""
        self.zoom_controller.zoom_changed.connect(self.zoom_changed)
        self.zoom_controller.redraw_requested.connect(self._request_redraw)
        
        self.brush_selector.range_selected.connect(self.range_selected)
        self.brush_selector.selection_changed.connect(self._update_crossfilter)
        
        self.keyboard_handler.action_triggered.connect(self._handle_keyboard_action)
        
        self.drill_down_navigator.navigation_requested.connect(self.drill_down_requested)
        
        self.performance_monitor.performance_warning.connect(
            lambda t: logger.warning(f"Interaction frame time exceeded target: {t:.1f}ms")
        )
        
    def install_event_filters(self):
        """Install event filters for interaction handling"""
        self.chart_widget.setMouseTracking(True)
        self.chart_widget.installEventFilter(self)
        self.chart_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.chart_widget.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
    def set_chart_data(self, data: Dict[str, Any]):
        """Set the chart data for interaction calculations"""
        self.chart_data = data
        self.visible_range = None
        self._update_visible_range()
        
    def eventFilter(self, obj: QObject, event) -> bool:
        """Handle mouse and keyboard events"""
        if obj != self.chart_widget:
            return False
            
        event_type = event.type()
        
        if event_type == QMouseEvent.Type.MouseMove:
            self.handle_mouse_move(event)
        elif event_type == QMouseEvent.Type.MouseButtonPress:
            self.handle_mouse_press(event)
        elif event_type == QMouseEvent.Type.MouseButtonRelease:
            self.handle_mouse_release(event)
        elif event_type == QMouseEvent.Type.Wheel:
            self.handle_wheel(event)
        elif event_type == QKeyEvent.Type.KeyPress:
            self.handle_key_press(event)
        elif event_type == QMouseEvent.Type.MouseButtonDblClick:
            self.handle_double_click(event)
        elif event_type == QTouchEvent.Type.TouchBegin:
            self.handle_touch_begin(event)
        elif event_type == QTouchEvent.Type.TouchUpdate:
            self.handle_touch_update(event)
        elif event_type == QTouchEvent.Type.TouchEnd:
            self.handle_touch_end(event)
            
        return False
        
    def handle_mouse_move(self, event: QMouseEvent):
        """Handle mouse movement for hover effects and panning"""
        # Start performance tracking
        self.performance_monitor.start_frame()
        
        pos = event.position()
        
        if self.is_panning:
            # Handle pan
            delta = pos - self.pan_start_pos
            self._apply_pan(delta)
            self.pan_start_pos = pos
            return
            
        if self.brush_selector.is_selecting:
            # Handle brush selection
            self.brush_selector.update_selection(pos)
            return
        
        # Optimize: only process hover if moved significantly
        if (pos - self.last_hover_pos).manhattanLength() < self.hover_threshold:
            return
            
        self.last_hover_pos = pos
        
        # Debounce hover processing
        self.hover_timer.stop()
        self.hover_timer.start(50)  # 50ms debounce
        
        # End performance tracking
        self.performance_monitor.end_frame()
        
    def _process_hover(self):
        """Process hover after debounce"""
        # Find nearest data point
        data_index = self.find_nearest_data_point(self.last_hover_pos)
        
        if data_index != self.hover_index:
            self.hover_index = data_index
            if data_index >= 0:
                data = self.get_data_at_index(data_index)
                self.point_hovered.emit(data_index, data)
                self._show_tooltip(data)
            else:
                self.tooltip.hide()
                
    def handle_mouse_press(self, event: QMouseEvent):
        """Handle mouse button press"""
        pos = event.position()
        button = event.button()
        modifiers = event.modifiers()
        
        if button == Qt.MouseButton.LeftButton:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                # Start brush selection
                self.brush_selector.start_selection(pos)
            else:
                # Start pan or click
                self.is_panning = True
                self.pan_start_pos = pos
                self.chart_widget.setCursor(Qt.CursorShape.ClosedHandCursor)
                
        elif button == Qt.MouseButton.RightButton:
            # Context menu or reset zoom
            if self.zoom_controller.zoom_level != 1.0:
                self.zoom_controller.reset_zoom()
                
    def handle_mouse_release(self, event: QMouseEvent):
        """Handle mouse button release"""
        button = event.button()
        
        if button == Qt.MouseButton.LeftButton:
            if self.brush_selector.is_selecting:
                self.brush_selector.finish_selection()
            elif self.is_panning:
                self.is_panning = False
                self.chart_widget.setCursor(Qt.CursorShape.ArrowCursor)
                
                # Check if it was a click (minimal movement)
                if (event.position() - self.pan_start_pos).manhattanLength() < 5:
                    self._handle_click(event.position())
                    
    def handle_wheel(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        with self.performance_monitor.measure_operation("zoom"):
            delta = event.angleDelta().y() / 120.0  # Standard wheel step
            center = event.position()
            
            # Apply zoom with Ctrl modifier for fine control
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                delta *= 0.5
                
            self.zoom_controller.zoom(delta, center)
        
    def handle_key_press(self, event: QKeyEvent):
        """Handle keyboard navigation"""
        self.keyboard_handler.handle_key_event(event)
        
    def handle_double_click(self, event: QMouseEvent):
        """Handle double click for drill-down"""
        pos = event.position()
        data_index = self.find_nearest_data_point(pos)
        
        if data_index >= 0:
            data = self.get_data_at_index(data_index)
            self.drill_down_navigator.request_drill_down(data)
            
    def find_nearest_data_point(self, pos: QPointF) -> int:
        """Find nearest data point to mouse position"""
        if not self.chart_data or 'points' not in self.chart_data:
            return -1
            
        # Convert screen coordinates to data coordinates
        data_pos = self.screen_to_data_coords(pos)
        
        # Get visible data points
        visible_points = self.get_visible_data_points()
        
        if not visible_points:
            return -1
            
        # Calculate distances efficiently using numpy
        points_array = np.array([(p['x'], p['y']) for p in visible_points])
        distances = np.sqrt(
            (points_array[:, 0] - data_pos.x())**2 + 
            (points_array[:, 1] - data_pos.y())**2
        )
        
        # Find minimum distance
        min_idx = np.argmin(distances)
        min_distance = distances[min_idx]
        
        # Return index if within threshold
        if min_distance < self._data_to_screen_distance(self.hover_threshold):
            return visible_points[min_idx].get('index', min_idx)
            
        return -1
        
    def get_visible_data_points(self) -> List[Dict[str, Any]]:
        """Get data points visible in current view"""
        if not self.chart_data or 'points' not in self.chart_data:
            return []
            
        if not self.visible_range:
            return self.chart_data['points']
            
        # Filter points within visible range
        min_x, max_x = self.visible_range
        return [
            p for p in self.chart_data['points']
            if min_x <= p['x'] <= max_x
        ]
        
    def get_data_at_index(self, index: int) -> Dict[str, Any]:
        """Get data for a specific index"""
        if not self.chart_data or 'points' not in self.chart_data:
            return {}
            
        points = self.chart_data['points']
        if 0 <= index < len(points):
            return points[index]
            
        return {}
        
    def screen_to_data_coords(self, screen_pos: QPointF) -> QPointF:
        """Convert screen coordinates to data coordinates"""
        if not hasattr(self.chart_widget, 'screen_to_data'):
            # Fallback implementation
            rect = self.chart_widget.rect()
            x_ratio = screen_pos.x() / rect.width()
            y_ratio = 1.0 - (screen_pos.y() / rect.height())
            
            if self.visible_range:
                x_min, x_max = self.visible_range
                x_data = x_min + (x_max - x_min) * x_ratio
            else:
                x_data = x_ratio
                
            return QPointF(x_data, y_ratio)
            
        return self.chart_widget.screen_to_data(screen_pos)
        
    def data_to_screen_coords(self, data_pos: QPointF) -> QPointF:
        """Convert data coordinates to screen coordinates"""
        if not hasattr(self.chart_widget, 'data_to_screen'):
            # Fallback implementation
            rect = self.chart_widget.rect()
            
            if self.visible_range:
                x_min, x_max = self.visible_range
                x_ratio = (data_pos.x() - x_min) / (x_max - x_min)
            else:
                x_ratio = data_pos.x()
                
            x_screen = x_ratio * rect.width()
            y_screen = (1.0 - data_pos.y()) * rect.height()
            
            return QPointF(x_screen, y_screen)
            
        return self.chart_widget.data_to_screen(data_pos)
        
    def _data_to_screen_distance(self, pixels: float) -> float:
        """Convert pixel distance to data distance"""
        # Approximate conversion based on current zoom
        if self.visible_range and self.chart_widget.rect().width() > 0:
            x_min, x_max = self.visible_range
            data_per_pixel = (x_max - x_min) / self.chart_widget.rect().width()
            return pixels * data_per_pixel
        return pixels
        
    def _apply_pan(self, delta: QPointF):
        """Apply pan transformation"""
        if not self.visible_range:
            return
            
        # Convert pixel delta to data delta
        x_min, x_max = self.visible_range
        rect = self.chart_widget.rect()
        
        if rect.width() > 0:
            data_delta = -(delta.x() / rect.width()) * (x_max - x_min)
            
            # Update visible range
            new_min = x_min + data_delta
            new_max = x_max + data_delta
            
            # Constrain to data bounds
            if self.chart_data and 'bounds' in self.chart_data:
                bounds = self.chart_data['bounds']
                if new_min < bounds['x_min']:
                    new_max += bounds['x_min'] - new_min
                    new_min = bounds['x_min']
                elif new_max > bounds['x_max']:
                    new_min -= new_max - bounds['x_max']
                    new_max = bounds['x_max']
                    
            self.visible_range = (new_min, new_max)
            self._request_redraw()
            
    def _handle_click(self, pos: QPointF):
        """Handle click event"""
        data_index = self.find_nearest_data_point(pos)
        
        if data_index >= 0:
            data = self.get_data_at_index(data_index)
            self.point_clicked.emit(data_index, data)
            
    def _show_tooltip(self, data: Dict[str, Any]):
        """Show tooltip with health data"""
        if not data:
            self.tooltip.hide()
            return
            
        # Position tooltip near cursor
        cursor_pos = self.chart_widget.mapFromGlobal(self.chart_widget.cursor().pos())
        tooltip_pos = cursor_pos + QPointF(15, 15)
        
        # Keep tooltip within widget bounds
        tooltip_rect = self.tooltip.rect()
        widget_rect = self.chart_widget.rect()
        
        if tooltip_pos.x() + tooltip_rect.width() > widget_rect.right():
            tooltip_pos.setX(cursor_pos.x() - tooltip_rect.width() - 15)
            
        if tooltip_pos.y() + tooltip_rect.height() > widget_rect.bottom():
            tooltip_pos.setY(cursor_pos.y() - tooltip_rect.height() - 15)
            
        self.tooltip.move(tooltip_pos.toPoint())
        self.tooltip.show_health_data(data)
        
    def _update_visible_range(self):
        """Update visible range based on zoom and pan"""
        if not self.chart_data or 'bounds' not in self.chart_data:
            return
            
        bounds = self.chart_data['bounds']
        zoom_level = self.zoom_controller.zoom_level
        
        if zoom_level == 1.0:
            self.visible_range = (bounds['x_min'], bounds['x_max'])
        else:
            # Calculate zoomed range
            center = (bounds['x_min'] + bounds['x_max']) / 2
            width = (bounds['x_max'] - bounds['x_min']) / zoom_level
            self.visible_range = (center - width/2, center + width/2)
            
    def _request_redraw(self):
        """Request chart redraw"""
        if hasattr(self.chart_widget, 'update_chart'):
            self.chart_widget.update_chart()
        else:
            self.chart_widget.update()
            
    def _update_crossfilter(self, start: float, end: float):
        """Update crossfilter with selection"""
        filter_value = {'start': start, 'end': end}
        self.crossfilter_manager.apply_filter('time_range', filter_value)
        self.crossfilter_updated.emit('time_range', filter_value)
        
    def _handle_keyboard_action(self, action: str, data: Any):
        """Handle keyboard navigation action"""
        if action == 'zoom_in':
            self.zoom_controller.zoom(1.0, self.chart_widget.rect().center())
        elif action == 'zoom_out':
            self.zoom_controller.zoom(-1.0, self.chart_widget.rect().center())
        elif action == 'pan_left':
            self._apply_pan(QPointF(50, 0))
        elif action == 'pan_right':
            self._apply_pan(QPointF(-50, 0))
        elif action == 'reset_view':
            self.zoom_controller.reset_zoom()
            self._update_visible_range()
            self._request_redraw()
            
    def enable_interactions(self):
        """Enable all chart interactions"""
        self.setEnabled(True)
        
    def disable_interactions(self):
        """Disable all chart interactions"""
        self.setEnabled(False)
        self.tooltip.hide()
        
    def handle_touch_begin(self, event: QTouchEvent):
        """Handle touch begin event"""
        points = event.points()
        
        # Store touch points
        for point in points:
            self.touch_points[point.id()] = point.position()
            
        # Check for multi-touch gestures
        if len(self.touch_points) == 2:
            # Start pinch zoom
            self.touch_zoom_active = True
            points_list = list(self.touch_points.values())
            self.initial_touch_distance = self._calculate_touch_distance(
                points_list[0], points_list[1]
            )
        elif len(self.touch_points) == 1:
            # Single touch - start pan
            self.is_panning = True
            self.pan_start_pos = list(self.touch_points.values())[0]
            
        event.accept()
        
    def handle_touch_update(self, event: QTouchEvent):
        """Handle touch update event"""
        points = event.points()
        
        # Update touch points
        for point in points:
            self.touch_points[point.id()] = point.position()
            
        if self.touch_zoom_active and len(self.touch_points) >= 2:
            # Handle pinch zoom
            points_list = list(self.touch_points.values())
            current_distance = self._calculate_touch_distance(
                points_list[0], points_list[1]
            )
            
            if self.initial_touch_distance > 0:
                zoom_factor = current_distance / self.initial_touch_distance
                center = QPointF(
                    (points_list[0].x() + points_list[1].x()) / 2,
                    (points_list[0].y() + points_list[1].y()) / 2
                )
                
                # Apply zoom
                self.zoom_controller.zoom_to_level(zoom_factor, center)
                
        elif self.is_panning and len(self.touch_points) == 1:
            # Handle pan
            current_pos = list(self.touch_points.values())[0]
            delta = current_pos - self.pan_start_pos
            self._apply_pan(delta)
            self.pan_start_pos = current_pos
            
        event.accept()
        
    def handle_touch_end(self, event: QTouchEvent):
        """Handle touch end event"""
        points = event.points()
        
        # Remove ended touch points
        for point in points:
            if point.id() in self.touch_points:
                del self.touch_points[point.id()]
                
        # Check if gestures should end
        if len(self.touch_points) < 2:
            self.touch_zoom_active = False
            
        if len(self.touch_points) == 0:
            self.is_panning = False
            
            # Check for tap
            if len(points) == 1 and hasattr(event, 'timestamp'):
                # Quick tap - treat as click
                tap_pos = points[0].position()
                self._handle_click(tap_pos)
                
        event.accept()
        
    def _calculate_touch_distance(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two touch points"""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return np.sqrt(dx * dx + dy * dy)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'average_frame_time': self.performance_monitor.get_average_frame_time(),
            'max_frame_time': self.performance_monitor.get_max_frame_time(),
            'fps': self.performance_monitor.get_fps(),
            'meeting_target': self.performance_monitor.is_meeting_target(),
            'performance_score': self.performance_monitor.get_performance_score()
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.hover_timer.stop()
        self.tooltip.hide()
        self.zoom_controller.cleanup()
        self.brush_selector.cleanup()
        self.performance_monitor.cleanup()