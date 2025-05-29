"""
Smooth zoom controller with momentum for health charts.

Provides fluid zooming with momentum scrolling and proper bounds checking.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QPointF, QTimer, QEasingCurve, QPropertyAnimation
from typing import Optional, Tuple
import math


class SmoothZoomController(QObject):
    """Smooth zoom control with momentum"""
    
    # Signals
    zoom_changed = pyqtSignal(float, QPointF)  # zoom_level, center
    redraw_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Zoom parameters
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.zoom_step = 0.1
        
        # Momentum parameters
        self.momentum = 0.0
        self.momentum_decay = 0.85
        self.min_momentum = 0.001
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_momentum)
        self.animation_timer.setInterval(16)  # 60fps
        
        # Zoom center tracking
        self.zoom_center = QPointF()
        self.viewport_size: Optional[Tuple[float, float]] = None
        
    def set_viewport_size(self, width: float, height: float):
        """Set the viewport size for zoom calculations"""
        self.viewport_size = (width, height)
        
    def zoom(self, delta: float, center: QPointF):
        """Apply zoom with smooth animation"""
        # Calculate zoom factor
        factor = 1.0 + (delta * self.zoom_step)
        self.target_zoom = self.zoom_level * factor
        
        # Clamp to limits
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom))
        
        # Store zoom center
        self.zoom_center = center
        
        # Add momentum for smooth feel
        self.momentum = (self.target_zoom - self.zoom_level) * 0.5
        
        # Start animation if not running
        if not self.animation_timer.isActive():
            self.animation_timer.start()
            
    def zoom_to_level(self, level: float, center: Optional[QPointF] = None):
        """Zoom directly to a specific level"""
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, level))
        
        if center:
            self.zoom_center = center
        elif self.viewport_size:
            # Default to viewport center
            self.zoom_center = QPointF(
                self.viewport_size[0] / 2,
                self.viewport_size[1] / 2
            )
            
        # Animate to target
        self.momentum = (self.target_zoom - self.zoom_level) * 0.3
        
        if not self.animation_timer.isActive():
            self.animation_timer.start()
            
    def zoom_to_fit(self, data_bounds: Tuple[float, float, float, float]):
        """Zoom to fit data bounds in viewport"""
        if not self.viewport_size:
            return
            
        x_min, y_min, x_max, y_max = data_bounds
        data_width = x_max - x_min
        data_height = y_max - y_min
        
        if data_width <= 0 or data_height <= 0:
            return
            
        # Calculate zoom to fit
        viewport_width, viewport_height = self.viewport_size
        zoom_x = viewport_width / data_width
        zoom_y = viewport_height / data_height
        
        # Use smaller zoom to fit both dimensions
        target_zoom = min(zoom_x, zoom_y) * 0.9  # 90% to add padding
        
        # Center on data
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        center = QPointF(center_x, center_y)
        
        self.zoom_to_level(target_zoom, center)
        
    def update_momentum(self):
        """Update zoom momentum for smooth animation"""
        if abs(self.momentum) < self.min_momentum and abs(self.zoom_level - self.target_zoom) < 0.001:
            # Stop animation when close enough
            self.animation_timer.stop()
            self.momentum = 0.0
            self.zoom_level = self.target_zoom
            return
            
        # Apply momentum with easing
        if abs(self.target_zoom - self.zoom_level) > 0.01:
            # Move towards target with easing
            diff = self.target_zoom - self.zoom_level
            self.zoom_level += diff * 0.15  # Easing factor
        else:
            # Apply momentum when close to target
            self.zoom_level += self.momentum
            self.momentum *= self.momentum_decay
            
        # Ensure within bounds
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, self.zoom_level))
        
        # Emit signals
        self.zoom_changed.emit(self.zoom_level, self.zoom_center)
        self.redraw_requested.emit()
        
    def apply_zoom_transform(self, new_zoom: float, center: QPointF):
        """Apply zoom transformation around a center point"""
        old_zoom = self.zoom_level
        self.zoom_level = new_zoom
        
        # Calculate offset to maintain center point
        if self.viewport_size and old_zoom != new_zoom:
            # This calculation maintains the data point under the cursor
            # at the same screen position after zoom
            scale_factor = new_zoom / old_zoom
            
            # The offset calculation would be done by the chart widget
            # as it knows the current view transformation
            pass
            
        self.zoom_changed.emit(self.zoom_level, center)
        
    def reset_zoom(self):
        """Reset zoom to default level"""
        self.target_zoom = 1.0
        self.momentum = (self.target_zoom - self.zoom_level) * 0.5
        
        if self.viewport_size:
            self.zoom_center = QPointF(
                self.viewport_size[0] / 2,
                self.viewport_size[1] / 2
            )
            
        if not self.animation_timer.isActive():
            self.animation_timer.start()
            
    def is_zoomed(self) -> bool:
        """Check if currently zoomed"""
        return abs(self.zoom_level - 1.0) > 0.001
        
    def can_zoom_in(self) -> bool:
        """Check if can zoom in further"""
        return self.zoom_level < self.max_zoom - 0.001
        
    def can_zoom_out(self) -> bool:
        """Check if can zoom out further"""
        return self.zoom_level > self.min_zoom + 0.001
        
    def get_zoom_percentage(self) -> int:
        """Get current zoom as percentage"""
        return int(self.zoom_level * 100)
        
    def set_zoom_limits(self, min_zoom: float, max_zoom: float):
        """Set custom zoom limits"""
        self.min_zoom = max(0.01, min_zoom)
        self.max_zoom = min(100.0, max_zoom)
        
        # Ensure current zoom is within limits
        if self.zoom_level < self.min_zoom:
            self.zoom_to_level(self.min_zoom)
        elif self.zoom_level > self.max_zoom:
            self.zoom_to_level(self.max_zoom)
            
    def cleanup(self):
        """Clean up resources"""
        self.animation_timer.stop()