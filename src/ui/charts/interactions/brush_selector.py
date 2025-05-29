"""
Brush range selector for date filtering in health charts.

Provides visual range selection with overlay and real-time updates.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QPointF, QRectF, Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from typing import Optional, Tuple


class SelectionOverlay(QWidget):
    """Visual overlay for brush selection"""
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # WSJ-style colors
        self.fill_color = QColor('#FF8C42')  # Orange
        self.fill_color.setAlpha(51)  # 20% opacity
        self.border_color = QColor('#6B4226')  # Dark brown
        
        # Selection bounds
        self.selection_rect = QRectF()
        
        # Initially hidden
        self.hide()
        
    def update_selection(self, start: QPointF, end: QPointF):
        """Update selection rectangle"""
        # Create normalized rectangle
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()
        
        self.selection_rect = QRectF(
            min(x1, x2), min(y1, y2),
            abs(x2 - x1), abs(y2 - y1)
        )
        
        # Update widget geometry to match parent
        self.setGeometry(self.parent().rect())
        self.update()
        
    def paintEvent(self, event):
        """Paint selection overlay"""
        if self.selection_rect.isEmpty():
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(self.selection_rect, 2, 2)
        
        # Fill
        painter.fillPath(path, QBrush(self.fill_color))
        
        # Border
        pen = QPen(self.border_color, 1)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw resize handles at edges
        self._draw_resize_handles(painter)
        
    def _draw_resize_handles(self, painter: QPainter):
        """Draw small handles at selection edges"""
        if self.selection_rect.width() < 20:
            return
            
        handle_size = 4
        handle_color = QColor(self.border_color)
        handle_color.setAlpha(180)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(handle_color))
        
        # Left edge
        left_handle = QRectF(
            self.selection_rect.left() - handle_size/2,
            self.selection_rect.center().y() - handle_size/2,
            handle_size, handle_size
        )
        painter.drawEllipse(left_handle)
        
        # Right edge
        right_handle = QRectF(
            self.selection_rect.right() - handle_size/2,
            self.selection_rect.center().y() - handle_size/2,
            handle_size, handle_size
        )
        painter.drawEllipse(right_handle)


class BrushRangeSelector(QObject):
    """Range selection with brush interaction"""
    
    # Signals
    range_selected = pyqtSignal(float, float)  # start, end values
    selection_changed = pyqtSignal(float, float)  # real-time updates
    selection_cleared = pyqtSignal()
    
    def __init__(self, chart_widget: QWidget):
        super().__init__()
        self.chart_widget = chart_widget
        
        # Selection overlay
        self.selection_overlay = SelectionOverlay(chart_widget)
        
        # Selection state
        self.is_selecting = False
        self.selection_start: Optional[QPointF] = None
        self.selection_end: Optional[QPointF] = None
        self.selection_start_data: Optional[float] = None
        self.selection_end_data: Optional[float] = None
        
        # Minimum selection size (pixels)
        self.min_selection_width = 10
        
    def start_selection(self, pos: QPointF):
        """Start brush selection"""
        self.is_selecting = True
        self.selection_start = pos
        self.selection_end = pos
        
        # Convert to data coordinates
        self.selection_start_data = self.screen_to_data_x(pos)
        self.selection_end_data = self.selection_start_data
        
        # Show overlay
        self.selection_overlay.show()
        self.selection_overlay.raise_()
        
        # Set cursor
        self.chart_widget.setCursor(Qt.CursorShape.CrossCursor)
        
    def update_selection(self, pos: QPointF):
        """Update brush selection"""
        if not self.is_selecting or not self.selection_start:
            return
            
        self.selection_end = pos
        self.selection_end_data = self.screen_to_data_x(pos)
        
        # Update overlay visualization
        self.selection_overlay.update_selection(
            self.selection_start,
            self.selection_end
        )
        
        # Emit real-time update if selection is large enough
        if abs(self.selection_end.x() - self.selection_start.x()) >= self.min_selection_width:
            start_data = min(self.selection_start_data, self.selection_end_data)
            end_data = max(self.selection_start_data, self.selection_end_data)
            self.selection_changed.emit(start_data, end_data)
            
    def finish_selection(self):
        """Complete brush selection"""
        if not self.is_selecting:
            return
            
        self.is_selecting = False
        self.selection_overlay.hide()
        
        # Reset cursor
        self.chart_widget.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Check if selection is valid
        if (self.selection_start and self.selection_end and 
            abs(self.selection_end.x() - self.selection_start.x()) >= self.min_selection_width):
            
            # Emit selected range
            start_data = min(self.selection_start_data, self.selection_end_data)
            end_data = max(self.selection_start_data, self.selection_end_data)
            self.range_selected.emit(start_data, end_data)
        else:
            # Selection too small, clear it
            self.clear_selection()
            
    def clear_selection(self):
        """Clear current selection"""
        self.selection_start = None
        self.selection_end = None
        self.selection_start_data = None
        self.selection_end_data = None
        self.selection_overlay.hide()
        self.selection_cleared.emit()
        
    def set_selection(self, start: float, end: float):
        """Programmatically set selection range"""
        # Convert data coordinates to screen
        start_screen = self.data_to_screen_x(start)
        end_screen = self.data_to_screen_x(end)
        
        self.selection_start = QPointF(start_screen, 0)
        self.selection_end = QPointF(end_screen, self.chart_widget.height())
        self.selection_start_data = start
        self.selection_end_data = end
        
        # Update overlay
        self.selection_overlay.update_selection(
            self.selection_start,
            self.selection_end
        )
        self.selection_overlay.show()
        
    def get_selection(self) -> Optional[Tuple[float, float]]:
        """Get current selection range in data coordinates"""
        if self.selection_start_data is not None and self.selection_end_data is not None:
            return (
                min(self.selection_start_data, self.selection_end_data),
                max(self.selection_start_data, self.selection_end_data)
            )
        return None
        
    def screen_to_data_x(self, pos: QPointF) -> float:
        """Convert screen X coordinate to data value"""
        # This should be implemented by the chart widget
        if hasattr(self.chart_widget, 'screen_to_data_x'):
            return self.chart_widget.screen_to_data_x(pos.x())
        else:
            # Fallback: assume linear mapping
            width = self.chart_widget.width()
            if width > 0:
                return pos.x() / width
            return 0.0
            
    def data_to_screen_x(self, value: float) -> float:
        """Convert data value to screen X coordinate"""
        # This should be implemented by the chart widget
        if hasattr(self.chart_widget, 'data_to_screen_x'):
            return self.chart_widget.data_to_screen_x(value)
        else:
            # Fallback: assume linear mapping
            return value * self.chart_widget.width()
            
    def cleanup(self):
        """Clean up resources"""
        self.clear_selection()
        if self.selection_overlay:
            self.selection_overlay.deleteLater()