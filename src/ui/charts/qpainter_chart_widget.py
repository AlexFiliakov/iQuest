"""QPainter-based chart widget for high-performance rendering."""

from typing import Optional, List, Tuple
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

from .base_chart import ChartConfig, ChartTheme
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class QPainterChartWidget(QWidget):
    """Custom widget for QPainter-based chart rendering."""
    
    # Signals
    dataPointHovered = pyqtSignal(int, float, float)  # index, x, y
    dataPointClicked = pyqtSignal(int, float, float)
    
    def __init__(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme, 
                 parent: Optional[QWidget] = None):
        """Initialize QPainter chart widget."""
        super().__init__(parent)
        
        self.data = data
        self.config = config
        self.theme = theme
        
        # Animation
        self._animation_progress = 0.0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_duration = config.animation_duration
        
        # Interaction
        self._hover_point: Optional[int] = None
        self._selected_points: List[int] = []
        
        # Cache
        self._data_bounds: Optional[Tuple[float, float, float, float]] = None
        self._transform_cache: Optional[dict] = None
        
        # Setup
        self.setMouseTracking(True)
        self.setMinimumSize(config.min_width, config.min_height)
        
        if config.max_width and config.max_height:
            self.setMaximumSize(config.max_width, config.max_height)
        
        # Calculate data bounds
        self._calculate_bounds()
    
    def _calculate_bounds(self):
        """Calculate data boundaries for scaling."""
        if self.data.empty:
            self._data_bounds = (0, 0, 1, 1)
            return
        
        # Assuming first column is X, second is Y for simplicity
        # Real implementation would be more sophisticated
        if len(self.data.columns) >= 2:
            x_col = self.data.columns[0]
            y_col = self.data.columns[1]
            
            x_min = self.data[x_col].min()
            x_max = self.data[x_col].max()
            y_min = self.data[y_col].min()
            y_max = self.data[y_col].max()
            
            # Add padding
            x_padding = (x_max - x_min) * 0.1
            y_padding = (y_max - y_min) * 0.1
            
            self._data_bounds = (
                x_min - x_padding,
                y_min - y_padding,
                x_max + x_padding,
                y_max + y_padding
            )
        else:
            self._data_bounds = (0, 0, 1, 1)
    
    def start_animation(self):
        """Start chart animation."""
        if self.config.animation_duration > 0:
            self._animation_progress = 0.0
            self._animation_timer.start(16)  # ~60 FPS
    
    def _update_animation(self):
        """Update animation progress."""
        self._animation_progress += 16 / self.config.animation_duration
        
        if self._animation_progress >= 1.0:
            self._animation_progress = 1.0
            self._animation_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(self.theme.background_color))
        
        # Calculate chart area
        chart_rect = self._get_chart_rect()
        
        # Draw components
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_data(painter, chart_rect)
        self._draw_title(painter)
        self._draw_labels(painter, chart_rect)
        
        if self.config.show_legend:
            self._draw_legend(painter)
    
    def _get_chart_rect(self) -> QRectF:
        """Get the drawable chart area."""
        margins = {
            'left': 80,
            'right': 40,
            'top': 60,
            'bottom': 60
        }
        
        return QRectF(
            margins['left'],
            margins['top'],
            self.width() - margins['left'] - margins['right'],
            self.height() - margins['top'] - margins['bottom']
        )
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        if not self.config.show_grid:
            return
        
        pen = QPen(QColor(self.theme.grid_color))
        pen.setWidth(1)
        
        if self.config.grid_style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        elif self.config.grid_style == 'dotted':
            pen.setStyle(Qt.PenStyle.DotLine)
        
        painter.setPen(pen)
        painter.setOpacity(0.3)
        
        # Vertical grid lines
        num_v_lines = 5
        for i in range(num_v_lines + 1):
            x = chart_rect.left() + (i / num_v_lines) * chart_rect.width()
            painter.drawLine(QPointF(x, chart_rect.top()), 
                           QPointF(x, chart_rect.bottom()))
        
        # Horizontal grid lines
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = chart_rect.top() + (i / num_h_lines) * chart_rect.height()
            painter.drawLine(QPointF(chart_rect.left(), y), 
                           QPointF(chart_rect.right(), y))
        
        painter.setOpacity(1.0)
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw axes."""
        pen = QPen(QColor(self.theme.border_color))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # X-axis
        if self.config.show_x_axis:
            painter.drawLine(QPointF(chart_rect.left(), chart_rect.bottom()),
                           QPointF(chart_rect.right(), chart_rect.bottom()))
        
        # Y-axis
        if self.config.show_y_axis:
            painter.drawLine(QPointF(chart_rect.left(), chart_rect.top()),
                           QPointF(chart_rect.left(), chart_rect.bottom()))
    
    def _draw_data(self, painter: QPainter, chart_rect: QRectF):
        """Draw the actual data."""
        if self.data.empty or len(self.data.columns) < 2:
            return
        
        # Get data columns
        x_col = self.data.columns[0]
        y_col = self.data.columns[1]
        
        # Create path for line
        path = QPainterPath()
        
        # Convert data points to screen coordinates
        points = []
        for i, (x, y) in enumerate(zip(self.data[x_col], self.data[y_col])):
            screen_x, screen_y = self._data_to_screen(x, y, chart_rect)
            points.append((screen_x, screen_y, i))
            
            if i == 0:
                path.moveTo(screen_x, screen_y)
            else:
                path.lineTo(screen_x, screen_y)
        
        # Apply animation
        if self._animation_progress < 1.0:
            # Clip path based on animation progress
            visible_points = int(len(points) * self._animation_progress)
            if visible_points > 0:
                new_path = QPainterPath()
                new_path.moveTo(points[0][0], points[0][1])
                for i in range(1, visible_points):
                    new_path.lineTo(points[i][0], points[i][1])
                path = new_path
        
        # Draw line
        pen = QPen(QColor(self.theme.primary_color))
        pen.setWidth(int(self.config.line_width))
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw data points
        if self.config.show_data_points and self._animation_progress >= 1.0:
            brush = QBrush(QColor(self.theme.primary_color))
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)
            
            for x, y, idx in points:
                radius = self.config.point_size
                
                # Highlight hover point
                if idx == self._hover_point:
                    radius = self.config.hover_point_size
                    painter.setBrush(QBrush(QColor(self.theme.secondary_color)))
                
                painter.drawEllipse(QPointF(x, y), radius, radius)
                
                # Reset brush for next point
                if idx == self._hover_point:
                    painter.setBrush(brush)
    
    def _draw_title(self, painter: QPainter):
        """Draw chart title and subtitle."""
        if not self.config.title:
            return
        
        # Title
        font = QFont(self.theme.font_family, self.theme.title_font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(self.theme.text_color))
        
        title_rect = QRectF(0, 10, self.width(), 30)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.config.title)
        
        # Subtitle
        if self.config.subtitle:
            font.setPointSize(self.theme.subtitle_font_size)
            font.setBold(False)
            painter.setFont(font)
            
            subtitle_rect = QRectF(0, 35, self.width(), 20)
            painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, self.config.subtitle)
    
    def _draw_labels(self, painter: QPainter, chart_rect: QRectF):
        """Draw axis labels."""
        font = QFont(self.theme.font_family, self.theme.label_font_size)
        painter.setFont(font)
        painter.setPen(QColor(self.theme.text_color))
        
        # X-axis label
        if self.config.x_label:
            label_rect = QRectF(chart_rect.left(), chart_rect.bottom() + 30,
                              chart_rect.width(), 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.config.x_label)
        
        # Y-axis label
        if self.config.y_label:
            painter.save()
            painter.translate(chart_rect.left() - 60, chart_rect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-50, -10, 100, 20), 
                           Qt.AlignmentFlag.AlignCenter, self.config.y_label)
            painter.restore()
    
    def _draw_legend(self, painter: QPainter):
        """Draw chart legend."""
        # Simple legend implementation
        font = QFont(self.theme.font_family, self.theme.label_font_size)
        painter.setFont(font)
        
        legend_x = self.width() - 150
        legend_y = 80
        
        # Draw legend box
        legend_rect = QRectF(legend_x, legend_y, 130, 50)
        painter.fillRect(legend_rect, QColor(255, 255, 255, 200))
        painter.setPen(QColor(self.theme.border_color))
        painter.drawRect(legend_rect)
        
        # Draw legend items
        painter.setPen(QColor(self.theme.text_color))
        if len(self.data.columns) >= 2:
            # Color indicator
            painter.fillRect(QRectF(legend_x + 10, legend_y + 15, 15, 3),
                           QColor(self.theme.primary_color))
            
            # Label
            painter.drawText(QRectF(legend_x + 30, legend_y + 10, 90, 20),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                           self.data.columns[1])
    
    def _data_to_screen(self, x: float, y: float, chart_rect: QRectF) -> Tuple[float, float]:
        """Convert data coordinates to screen coordinates."""
        if not self._data_bounds:
            return chart_rect.center().x(), chart_rect.center().y()
        
        x_min, y_min, x_max, y_max = self._data_bounds
        
        # Normalize to 0-1
        if x_max != x_min:
            x_norm = (x - x_min) / (x_max - x_min)
        else:
            x_norm = 0.5
        
        if y_max != y_min:
            y_norm = (y - y_min) / (y_max - y_min)
        else:
            y_norm = 0.5
        
        # Convert to screen coordinates
        screen_x = chart_rect.left() + x_norm * chart_rect.width()
        screen_y = chart_rect.bottom() - y_norm * chart_rect.height()  # Flip Y
        
        return screen_x, screen_y
    
    def _screen_to_data(self, screen_x: float, screen_y: float, 
                       chart_rect: QRectF) -> Tuple[float, float]:
        """Convert screen coordinates to data coordinates."""
        if not self._data_bounds:
            return 0, 0
        
        x_min, y_min, x_max, y_max = self._data_bounds
        
        # Normalize screen coordinates
        x_norm = (screen_x - chart_rect.left()) / chart_rect.width()
        y_norm = 1.0 - (screen_y - chart_rect.top()) / chart_rect.height()
        
        # Convert to data coordinates
        data_x = x_min + x_norm * (x_max - x_min)
        data_y = y_min + y_norm * (y_max - y_min)
        
        return data_x, data_y
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover effects."""
        chart_rect = self._get_chart_rect()
        
        if chart_rect.contains(event.position().toPoint()):
            # Find nearest data point
            min_dist = float('inf')
            hover_idx = None
            
            if not self.data.empty and len(self.data.columns) >= 2:
                x_col = self.data.columns[0]
                y_col = self.data.columns[1]
                
                for i, (x, y) in enumerate(zip(self.data[x_col], self.data[y_col])):
                    screen_x, screen_y = self._data_to_screen(x, y, chart_rect)
                    dist = ((event.position().x() - screen_x) ** 2 + 
                           (event.position().y() - screen_y) ** 2) ** 0.5
                    
                    if dist < min_dist and dist < 20:  # 20 pixel threshold
                        min_dist = dist
                        hover_idx = i
            
            if hover_idx != self._hover_point:
                self._hover_point = hover_idx
                self.update()
                
                if hover_idx is not None:
                    self.dataPointHovered.emit(hover_idx, 
                                             self.data.iloc[hover_idx, 0],
                                             self.data.iloc[hover_idx, 1])
        else:
            if self._hover_point is not None:
                self._hover_point = None
                self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse click for selection."""
        if event.button() == Qt.MouseButton.LeftButton and self._hover_point is not None:
            if self._hover_point in self._selected_points:
                self._selected_points.remove(self._hover_point)
            else:
                self._selected_points.append(self._hover_point)
            
            self.dataPointClicked.emit(self._hover_point,
                                     self.data.iloc[self._hover_point, 0],
                                     self.data.iloc[self._hover_point, 1])
            self.update()