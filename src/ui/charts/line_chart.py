"""
Line chart component for visualizing time-series health data.

This module provides a customizable line chart widget that follows
the Apple Health Monitor design specifications.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPainterPath, 
    QFontMetrics, QMouseEvent, QResizeEvent
)


class LineChart(QWidget):
    """
    A custom line chart widget for displaying time-series health data.
    
    Features:
    - Smooth line rendering with anti-aliasing
    - Interactive hover tooltips
    - Animated transitions
    - Responsive design
    - Customizable colors following design system
    """
    
    # Signals
    dataPointHovered = Signal(dict)  # Emits data point info on hover
    dataPointClicked = Signal(dict)  # Emits data point info on click
    
    def __init__(self, parent=None):
        """Initialize the line chart widget."""
        super().__init__(parent)
        
        # Chart data
        self.data_points: List[Dict[str, Any]] = []
        self.x_labels: List[str] = []
        self.y_range: Tuple[float, float] = (0, 100)
        
        # Chart configuration
        self.title = ""
        self.x_axis_label = ""
        self.y_axis_label = ""
        self.show_grid = True
        self.show_dots = True
        self.animate = True
        
        # Colors from design system
        self.colors = {
            'background': QColor('#FFFFFF'),
            'grid': QColor('#E8DCC8'),
            'axis': QColor('#8B7355'),
            'line': QColor('#FF8C42'),  # Primary orange
            'dot': QColor('#FF8C42'),
            'hover': QColor('#E67A35'),
            'text': QColor('#5D4E37'),
            'text_muted': QColor('#A69583')
        }
        
        # Layout configuration
        self.margins = {
            'top': 40,
            'right': 20,
            'bottom': 60,
            'left': 80
        }
        
        # Interaction state
        self.hover_index = -1
        self.animation_progress = 0.0
        
        # Setup
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
        # Set background
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['background'].name()};
                border-radius: 12px;
                border: 1px solid rgba(139, 115, 85, 0.1);
            }}
        """)
        
    def _setup_animations(self):
        """Set up animation properties."""
        self.animation = QPropertyAnimation(self, b"animation_progress")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.update)
        
    @property
    def animation_progress(self):
        """Get animation progress value."""
        return self._animation_progress
        
    @animation_progress.setter
    def animation_progress(self, value):
        """Set animation progress value."""
        self._animation_progress = value
        self.update()
        
    def set_data(self, data_points: List[Dict[str, Any]], animate: bool = True):
        """
        Set chart data.
        
        Args:
            data_points: List of dictionaries with 'x', 'y', and optional 'label' keys
            animate: Whether to animate the data change
        """
        self.data_points = data_points
        
        if animate and self.animate:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
        else:
            self.animation_progress = 1.0
            self.update()
            
    def set_labels(self, title: str = "", x_label: str = "", y_label: str = ""):
        """Set chart labels."""
        self.title = title
        self.x_axis_label = x_label
        self.y_axis_label = y_label
        self.update()
        
    def set_y_range(self, min_val: float, max_val: float):
        """Set Y-axis range."""
        self.y_range = (min_val, max_val)
        self.update()
        
    def paintEvent(self, event):
        """Paint the chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get drawing area
        chart_rect = self._get_chart_rect()
        
        # Draw components
        self._draw_background(painter)
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_labels(painter, chart_rect)
        self._draw_data(painter, chart_rect)
        self._draw_hover_tooltip(painter, chart_rect)
        
    def _get_chart_rect(self) -> QRectF:
        """Calculate the actual chart drawing area."""
        return QRectF(
            self.margins['left'],
            self.margins['top'],
            self.width() - self.margins['left'] - self.margins['right'],
            self.height() - self.margins['top'] - self.margins['bottom']
        )
        
    def _draw_background(self, painter: QPainter):
        """Draw chart background."""
        painter.fillRect(self.rect(), self.colors['background'])
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        if not self.show_grid:
            return
            
        painter.setPen(QPen(self.colors['grid'], 1, Qt.DashLine))
        
        # Horizontal grid lines
        y_steps = 5
        for i in range(y_steps + 1):
            y = chart_rect.top() + (i * chart_rect.height() / y_steps)
            painter.drawLine(
                QPointF(chart_rect.left(), y),
                QPointF(chart_rect.right(), y)
            )
            
        # Vertical grid lines
        if self.data_points:
            x_steps = min(len(self.data_points) - 1, 10)
            for i in range(x_steps + 1):
                x = chart_rect.left() + (i * chart_rect.width() / x_steps)
                painter.drawLine(
                    QPointF(x, chart_rect.top()),
                    QPointF(x, chart_rect.bottom())
                )
                
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw X and Y axes."""
        painter.setPen(QPen(self.colors['axis'], 2))
        
        # X-axis
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.bottom()),
            QPointF(chart_rect.right(), chart_rect.bottom())
        )
        
        # Y-axis
        painter.drawLine(
            QPointF(chart_rect.left(), chart_rect.top()),
            QPointF(chart_rect.left(), chart_rect.bottom())
        )
        
    def _draw_labels(self, painter: QPainter, chart_rect: QRectF):
        """Draw axis labels and title."""
        # Title
        if self.title:
            title_font = QFont("Inter", 18, QFont.Bold)
            painter.setFont(title_font)
            painter.setPen(self.colors['text'])
            
            title_rect = QRectF(0, 0, self.width(), self.margins['top'])
            painter.drawText(title_rect, Qt.AlignCenter, self.title)
            
        # Y-axis labels
        label_font = QFont("Inter", 10)
        painter.setFont(label_font)
        painter.setPen(self.colors['text_muted'])
        
        y_steps = 5
        y_min, y_max = self.y_range
        for i in range(y_steps + 1):
            value = y_min + (y_max - y_min) * (1 - i / y_steps)
            y = chart_rect.top() + (i * chart_rect.height() / y_steps)
            
            label = f"{value:.0f}"
            label_rect = QRectF(0, y - 10, self.margins['left'] - 10, 20)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
            
        # X-axis labels
        if self.data_points:
            x_steps = min(len(self.data_points) - 1, 10)
            for i in range(0, len(self.data_points), max(1, len(self.data_points) // x_steps)):
                x = self._map_x(i, chart_rect)
                
                if 'label' in self.data_points[i]:
                    label = self.data_points[i]['label']
                else:
                    label = str(self.data_points[i]['x'])
                    
                label_rect = QRectF(x - 50, chart_rect.bottom() + 5, 100, 20)
                painter.drawText(label_rect, Qt.AlignCenter, label)
                
        # Axis labels
        if self.x_axis_label:
            painter.drawText(
                QRectF(0, self.height() - 30, self.width(), 20),
                Qt.AlignCenter,
                self.x_axis_label
            )
            
        if self.y_axis_label:
            painter.save()
            painter.translate(15, self.height() / 2)
            painter.rotate(-90)
            painter.drawText(
                QRectF(-50, -10, 100, 20),
                Qt.AlignCenter,
                self.y_axis_label
            )
            painter.restore()
            
    def _draw_data(self, painter: QPainter, chart_rect: QRectF):
        """Draw the data line and points."""
        if not self.data_points:
            return
            
        # Create path for line
        path = QPainterPath()
        
        # Draw line
        painter.setPen(QPen(self.colors['line'], 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        for i, point in enumerate(self.data_points):
            x = self._map_x(i, chart_rect)
            y = self._map_y(point['y'], chart_rect)
            
            # Apply animation
            if self.animate:
                y = chart_rect.bottom() - (chart_rect.bottom() - y) * self.animation_progress
                
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
                
        painter.drawPath(path)
        
        # Draw dots
        if self.show_dots:
            for i, point in enumerate(self.data_points):
                x = self._map_x(i, chart_rect)
                y = self._map_y(point['y'], chart_rect)
                
                # Apply animation
                if self.animate:
                    y = chart_rect.bottom() - (chart_rect.bottom() - y) * self.animation_progress
                    
                # Highlight on hover
                if i == self.hover_index:
                    painter.setBrush(QBrush(self.colors['hover']))
                    painter.setPen(QPen(self.colors['hover'], 2))
                    painter.drawEllipse(QPointF(x, y), 6, 6)
                else:
                    painter.setBrush(QBrush(self.colors['dot']))
                    painter.setPen(QPen(self.colors['background'], 2))
                    painter.drawEllipse(QPointF(x, y), 4, 4)
                    
    def _draw_hover_tooltip(self, painter: QPainter, chart_rect: QRectF):
        """Draw tooltip for hovered data point."""
        if self.hover_index < 0 or self.hover_index >= len(self.data_points):
            return
            
        point = self.data_points[self.hover_index]
        x = self._map_x(self.hover_index, chart_rect)
        y = self._map_y(point['y'], chart_rect)
        
        # Tooltip text
        tooltip_text = f"{point['y']:.1f}"
        if 'label' in point:
            tooltip_text = f"{point['label']}: {tooltip_text}"
            
        # Calculate tooltip dimensions
        font = QFont("Inter", 11)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(tooltip_text)
        
        # Tooltip box
        padding = 8
        tooltip_rect = QRectF(
            x - text_rect.width() / 2 - padding,
            y - text_rect.height() - padding * 2 - 10,
            text_rect.width() + padding * 2,
            text_rect.height() + padding * 2
        )
        
        # Ensure tooltip stays within widget
        if tooltip_rect.left() < 0:
            tooltip_rect.moveLeft(0)
        if tooltip_rect.right() > self.width():
            tooltip_rect.moveRight(self.width())
            
        # Draw tooltip
        painter.setBrush(QBrush(QColor(93, 78, 55, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(tooltip_rect, 6, 6)
        
        # Draw text
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(tooltip_rect, Qt.AlignCenter, tooltip_text)
        
    def _map_x(self, index: int, chart_rect: QRectF) -> float:
        """Map data index to X coordinate."""
        if len(self.data_points) <= 1:
            return chart_rect.center().x()
        return chart_rect.left() + (index / (len(self.data_points) - 1)) * chart_rect.width()
        
    def _map_y(self, value: float, chart_rect: QRectF) -> float:
        """Map data value to Y coordinate."""
        y_min, y_max = self.y_range
        if y_max == y_min:
            return chart_rect.center().y()
        normalized = (value - y_min) / (y_max - y_min)
        return chart_rect.bottom() - normalized * chart_rect.height()
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for hover effects."""
        chart_rect = self._get_chart_rect()
        mouse_x = event.pos().x()
        
        # Find closest data point
        old_hover = self.hover_index
        self.hover_index = -1
        
        if chart_rect.contains(event.pos()) and self.data_points:
            min_distance = float('inf')
            
            for i in range(len(self.data_points)):
                x = self._map_x(i, chart_rect)
                distance = abs(x - mouse_x)
                
                if distance < min_distance and distance < 20:  # 20px threshold
                    min_distance = distance
                    self.hover_index = i
                    
            if self.hover_index >= 0 and self.hover_index != old_hover:
                self.dataPointHovered.emit(self.data_points[self.hover_index])
                
        if self.hover_index != old_hover:
            self.update()
            
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click on data points."""
        if event.button() == Qt.LeftButton and self.hover_index >= 0:
            self.dataPointClicked.emit(self.data_points[self.hover_index])
            
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.hover_index = -1
        self.update()
        
    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize."""
        super().resizeEvent(event)
        self.update()