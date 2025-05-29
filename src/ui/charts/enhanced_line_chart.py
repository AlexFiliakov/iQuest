"""
Enhanced line chart component with advanced features.

This module provides a feature-rich line chart widget with:
- Multiple data series support
- Interactive zoom and pan
- Wall Street Journal-inspired styling
- Export functionality
- Advanced animations
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, 
    QFileDialog, QRubberBand
)
from PyQt6.QtCore import (
    Qt, QPointF, QRectF, pyqtSignal as Signal, QPropertyAnimation, 
    QEasingCurve, QPoint, QRect, QSize, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPainterPath, 
    QFontMetrics, QMouseEvent, QWheelEvent, QKeyEvent,
    QPixmap, QImage, QPdfWriter, QIcon, QAction
)

from .chart_config import LineChartConfig


class DataSeries:
    """Represents a single data series in the chart."""
    
    def __init__(self, name: str, data: List[Dict[str, Any]], 
                 color: Optional[str] = None, style: str = 'solid'):
        self.name = name
        self.data = data
        self.color = color
        self.style = style
        self.visible = True
        self.highlighted = False


class EnhancedLineChart(QWidget):
    """
    Advanced line chart with multiple series, interactivity, and WSJ styling.
    
    Features:
    - Multiple data series with legend
    - Zoom and pan capabilities  
    - Export to PNG/SVG/PDF
    - Smooth animations
    - Wall Street Journal-inspired design
    - Tooltips and crosshairs
    - Keyboard navigation
    """
    
    # Signals
    dataPointHovered = Signal(str, dict)  # series_name, point_data
    dataPointClicked = Signal(str, dict)
    rangeChanged = Signal(float, float, float, float)  # x_min, x_max, y_min, y_max
    
    def __init__(self, config: Optional[LineChartConfig] = None, parent=None):
        """Initialize the enhanced line chart."""
        super().__init__(parent)
        
        # Configuration
        self.config = config or LineChartConfig()
        
        # Data
        self.series: Dict[str, DataSeries] = {}
        self.x_range = (0, 100)
        self.y_range = (0, 100)
        self.view_x_range = None  # Current zoomed range
        self.view_y_range = None
        
        # Labels
        self.title = ""
        self.subtitle = ""
        self.x_label = ""
        self.y_label = ""
        
        # Interaction state
        self.hover_series = None
        self.hover_index = -1
        self.is_panning = False
        self.pan_start = QPoint()
        self.pan_start_ranges = None
        self.selection_rect = None
        self.rubber_band = None
        
        # Animation
        self.animation_progress = 1.0
        self._animation = None
        
        # Setup
        self._setup_ui()
        self._setup_toolbar()
        self._setup_animations()
        
    def _setup_ui(self):
        """Set up the widget UI."""
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Apply background
        if self.config.wsj_mode:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.config.background_color};
                    border: 1px solid #DDDDDD;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.config.background_color};
                    border-radius: 12px;
                    border: 1px solid rgba(139, 115, 85, 0.1);
                }}
            """)
            
    def _setup_toolbar(self):
        """Set up interactive toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        
        # Style toolbar
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }
            QToolButton:hover {
                background: rgba(0, 0, 0, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Actions
        self.action_reset = QAction("Reset View", self)
        self.action_reset.triggered.connect(self.reset_view)
        
        self.action_zoom_in = QAction("Zoom In", self)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        
        self.action_zoom_out = QAction("Zoom Out", self)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        
        self.action_export = QAction("Export", self)
        self.action_export.triggered.connect(self.export_chart)
        
        # Add to toolbar
        self.toolbar.addAction(self.action_reset)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_zoom_in)
        self.toolbar.addAction(self.action_zoom_out)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_export)
        
        # Add to layout
        self.layout().addWidget(self.toolbar)
        
    def _setup_animations(self):
        """Set up animation system."""
        self._animation = QPropertyAnimation(self, b"animation_progress")
        self._animation.setDuration(self.config.animation_duration)
        
        # Set easing curve
        easing_map = {
            'Linear': QEasingCurve.Type.Linear,
            'InOutQuad': QEasingCurve.Type.InOutQuad,
            'OutCubic': QEasingCurve.Type.OutCubic,
            'OutElastic': QEasingCurve.Type.OutElastic,
        }
        curve = easing_map.get(self.config.animation_easing, QEasingCurve.Type.OutCubic)
        self._animation.setEasingCurve(curve)
        
        self._animation.valueChanged.connect(self.update)
        
    @pyqtProperty(float)
    def animation_progress(self):
        return self._animation_progress
        
    @animation_progress.setter
    def animation_progress(self, value):
        self._animation_progress = value
        self.update()
        
    def add_series(self, name: str, data: Union[List[Dict], pd.DataFrame],
                   x_column: str = 'x', y_column: str = 'y',
                   color: Optional[str] = None):
        """
        Add a data series to the chart.
        
        Args:
            name: Series name for legend
            data: List of dicts or pandas DataFrame
            x_column: Column name for x values
            y_column: Column name for y values  
            color: Optional color override
        """
        # Convert DataFrame to list of dicts
        if isinstance(data, pd.DataFrame):
            data_points = []
            for _, row in data.iterrows():
                point = {
                    'x': row[x_column],
                    'y': row[y_column],
                    'label': str(row[x_column])
                }
                # Add extra columns as metadata
                for col in data.columns:
                    if col not in [x_column, y_column]:
                        point[col] = row[col]
                data_points.append(point)
        else:
            data_points = data
            
        # Assign color
        if not color:
            series_index = len(self.series)
            color = self.config.series_colors[series_index % len(self.config.series_colors)]
            
        # Create series
        series = DataSeries(name, data_points, color)
        self.series[name] = series
        
        # Update ranges
        self._update_ranges()
        
        # Animate if enabled
        if self.config.animate:
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0) 
            self._animation.start()
        else:
            self.update()
            
    def remove_series(self, name: str):
        """Remove a data series."""
        if name in self.series:
            del self.series[name]
            self._update_ranges()
            self.update()
            
    def clear_series(self):
        """Remove all data series."""
        self.series.clear()
        self.update()
        
    def set_labels(self, title: str = "", subtitle: str = "", 
                   x_label: str = "", y_label: str = ""):
        """Set chart labels."""
        self.title = title
        self.subtitle = subtitle
        self.x_label = x_label
        self.y_label = y_label
        self.update()
        
    def _update_ranges(self):
        """Update data ranges based on all series."""
        if not self.series:
            return
            
        x_min = float('inf')
        x_max = float('-inf')
        y_min = float('inf')
        y_max = float('-inf')
        
        for series in self.series.values():
            if not series.visible or not series.data:
                continue
                
            for point in series.data:
                x_val = point.get('x', 0)
                y_val = point.get('y', 0)
                
                # Handle datetime
                if isinstance(x_val, datetime):
                    x_val = x_val.timestamp()
                    
                x_min = min(x_min, x_val)
                x_max = max(x_max, x_val)
                y_min = min(y_min, y_val)
                y_max = max(y_max, y_val)
                
        # Add padding
        x_padding = (x_max - x_min) * 0.05
        y_padding = (y_max - y_min) * 0.05
        
        self.x_range = (x_min - x_padding, x_max + x_padding)
        self.y_range = (y_min - y_padding, y_max + y_padding)
        
        # Reset view if needed
        if self.view_x_range is None:
            self.view_x_range = self.x_range
        if self.view_y_range is None:
            self.view_y_range = self.y_range
            
    def paintEvent(self, event):
        """Paint the chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Get drawing area
        chart_rect = self._get_chart_rect()
        
        # Draw components in order
        self._draw_background(painter)
        self._draw_chart_background(painter, chart_rect)
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_data(painter, chart_rect)
        self._draw_legend(painter)
        self._draw_labels(painter, chart_rect)
        self._draw_hover_elements(painter, chart_rect)
        
        # Draw selection rectangle
        if self.rubber_band and self.rubber_band.isVisible():
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(100, 100, 100, 50)))
            painter.drawRect(self.rubber_band.geometry())
            
    def _get_chart_rect(self) -> QRectF:
        """Calculate the actual chart drawing area."""
        # Account for toolbar
        toolbar_height = self.toolbar.height() if self.toolbar.isVisible() else 0
        
        return QRectF(
            self.config.margins['left'],
            self.config.margins['top'] + toolbar_height,
            self.width() - self.config.margins['left'] - self.config.margins['right'],
            self.height() - self.config.margins['top'] - self.config.margins['bottom'] - toolbar_height
        )
        
    def _draw_background(self, painter: QPainter):
        """Draw widget background."""
        painter.fillRect(self.rect(), QColor(self.config.background_color))
        
    def _draw_chart_background(self, painter: QPainter, chart_rect: QRectF):
        """Draw chart plot area background."""
        if self.config.plot_background != self.config.background_color:
            painter.fillRect(chart_rect, QColor(self.config.plot_background))
            
        # WSJ style: subtle border
        if self.config.wsj_mode:
            painter.setPen(QPen(QColor('#DDDDDD'), 1))
            painter.drawRect(chart_rect)
            
    def _draw_grid(self, painter: QPainter, chart_rect: QRectF):
        """Draw grid lines."""
        if not self.config.show_grid:
            return
            
        # Set grid style
        pen = QPen(QColor(self.config.grid_color), 1)
        if self.config.grid_style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        elif self.config.grid_style == 'dotted':
            pen.setStyle(Qt.PenStyle.DotLine)
            
        painter.setPen(pen)
        painter.setOpacity(self.config.grid_alpha)
        
        # Get view ranges
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # Horizontal grid lines
        y_steps = 5
        for i in range(y_steps + 1):
            y = chart_rect.top() + (i * chart_rect.height() / y_steps)
            painter.drawLine(
                QPointF(chart_rect.left(), y),
                QPointF(chart_rect.right(), y)
            )
            
        # Vertical grid lines
        x_steps = 8
        for i in range(x_steps + 1):
            x = chart_rect.left() + (i * chart_rect.width() / x_steps)
            painter.drawLine(
                QPointF(x, chart_rect.top()),
                QPointF(x, chart_rect.bottom())
            )
            
        painter.setOpacity(1.0)
        
    def _draw_axes(self, painter: QPainter, chart_rect: QRectF):
        """Draw X and Y axes."""
        painter.setPen(QPen(QColor(self.config.axis_color), self.config.axis_width))
        
        if self.config.show_x_axis:
            painter.drawLine(
                QPointF(chart_rect.left(), chart_rect.bottom()),
                QPointF(chart_rect.right(), chart_rect.bottom())
            )
            
        if self.config.show_y_axis:
            painter.drawLine(
                QPointF(chart_rect.left(), chart_rect.top()),
                QPointF(chart_rect.left(), chart_rect.bottom())
            )
            
    def _draw_labels(self, painter: QPainter, chart_rect: QRectF):
        """Draw title, axis labels, and tick labels."""
        # Title
        if self.title:
            font = QFont(self.config.title_font_family, self.config.title_font_size, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(self.config.text_color))
            
            title_rect = QRectF(0, 10, self.width(), 30)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
            
        # Subtitle
        if self.subtitle:
            font = QFont(self.config.font_family, self.config.subtitle_font_size)
            painter.setFont(font)
            painter.setPen(QColor(self.config.text_muted))
            
            subtitle_rect = QRectF(0, 35, self.width(), 20)
            painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, self.subtitle)
            
        # Axis tick labels
        self._draw_axis_labels(painter, chart_rect)
        
    def _draw_axis_labels(self, painter: QPainter, chart_rect: QRectF):
        """Draw axis tick labels."""
        font = QFont(self.config.font_family, self.config.tick_font_size)
        painter.setFont(font)
        painter.setPen(QColor(self.config.text_muted))
        
        # Get view ranges
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # Y-axis labels
        y_steps = 5
        for i in range(y_steps + 1):
            value = y_min + (y_max - y_min) * (1 - i / y_steps)
            y = chart_rect.top() + (i * chart_rect.height() / y_steps)
            
            label = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            label_rect = QRectF(0, y - 10, self.config.margins['left'] - 10, 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
            
        # X-axis labels
        x_steps = min(8, len(self.series) * 10) if self.series else 8
        for i in range(x_steps + 1):
            x = chart_rect.left() + (i * chart_rect.width() / x_steps)
            value = x_min + (x_max - x_min) * (i / x_steps)
            
            label = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            label_rect = QRectF(x - 50, chart_rect.bottom() + 5, 100, 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
            
        # Axis labels
        if self.x_label:
            painter.drawText(
                QRectF(0, self.height() - 25, self.width(), 20),
                Qt.AlignmentFlag.AlignCenter,
                self.x_label
            )
            
        if self.y_label:
            painter.save()
            painter.translate(15, self.height() / 2)
            painter.rotate(-90)
            painter.drawText(
                QRectF(-50, -10, 100, 20),
                Qt.AlignmentFlag.AlignCenter,
                self.y_label
            )
            painter.restore()
            
    def _draw_data(self, painter: QPainter, chart_rect: QRectF):
        """Draw all data series."""
        for series_name, series in self.series.items():
            if not series.visible or not series.data:
                continue
                
            self._draw_series(painter, chart_rect, series)
            
    def _draw_series(self, painter: QPainter, chart_rect: QRectF, series: DataSeries):
        """Draw a single data series."""
        # Set pen for line
        pen = QPen(QColor(series.color), self.config.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        if series.style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        elif series.style == 'dotted':
            pen.setStyle(Qt.PenStyle.DotLine)
            
        painter.setPen(pen)
        
        # Create path
        path = QPainterPath()
        points = []
        
        # Get view ranges
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # Draw line
        for i, point in enumerate(series.data):
            x = self._map_x(point['x'], chart_rect, x_min, x_max)
            y = self._map_y(point['y'], chart_rect, y_min, y_max)
            
            # Skip points outside view
            if x < chart_rect.left() or x > chart_rect.right():
                continue
                
            # Apply animation
            if self.config.animate:
                y = chart_rect.bottom() - (chart_rect.bottom() - y) * self.animation_progress
                
            points.append((x, y, i))
            
            if len(points) == 1:
                path.moveTo(x, y)
            else:
                if self.config.smooth_lines and len(points) > 2:
                    # Smooth curve using quadratic Bezier
                    prev_x, prev_y, _ = points[-2]
                    ctrl_x = (prev_x + x) / 2
                    ctrl_y = (prev_y + y) / 2
                    path.quadTo(prev_x, prev_y, ctrl_x, ctrl_y)
                else:
                    path.lineTo(x, y)
                    
        painter.drawPath(path)
        
        # Draw area fill
        if self.config.area_fill and len(points) > 1:
            area_path = QPainterPath(path)
            area_path.lineTo(points[-1][0], chart_rect.bottom())
            area_path.lineTo(points[0][0], chart_rect.bottom())
            area_path.closeSubpath()
            
            painter.setOpacity(self.config.area_opacity)
            painter.fillPath(area_path, QBrush(QColor(series.color)))
            painter.setOpacity(1.0)
            
        # Draw data points
        if self.config.show_data_points:
            for x, y, idx in points:
                if series.name == self.hover_series and idx == self.hover_index:
                    painter.setBrush(QBrush(QColor(series.color)))
                    painter.setPen(QPen(QColor(series.color).darker(120), 2))
                    painter.drawEllipse(QPointF(x, y), 
                                      self.config.hover_point_size, 
                                      self.config.hover_point_size)
                else:
                    painter.setBrush(QBrush(QColor(series.color)))
                    painter.setPen(QPen(self.config.background_color, 2))
                    painter.drawEllipse(QPointF(x, y), 
                                      self.config.point_size, 
                                      self.config.point_size)
                    
    def _draw_legend(self, painter: QPainter):
        """Draw series legend."""
        if not self.config.show_legend or not self.series:
            return
            
        font = QFont(self.config.font_family, self.config.label_font_size)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        
        # Calculate legend dimensions
        legend_items = []
        max_width = 0
        
        for series_name, series in self.series.items():
            if series.visible:
                text_width = metrics.horizontalAdvance(series_name)
                max_width = max(max_width, text_width)
                legend_items.append((series_name, series))
                
        if not legend_items:
            return
            
        # Legend positioning
        item_height = 20
        legend_padding = 10
        color_box_size = 12
        spacing = 8
        
        # Calculate total legend size
        legend_width = color_box_size + spacing + max_width + legend_padding * 2
        legend_height = len(legend_items) * item_height + legend_padding * 2
        
        # Position based on config
        if self.config.legend_position == 'top':
            legend_x = (self.width() - legend_width) / 2
            legend_y = self.config.margins['top'] + 40
        elif self.config.legend_position == 'right':
            legend_x = self.width() - self.config.margins['right'] - legend_width - 20
            legend_y = self.config.margins['top'] + 100
        else:
            legend_x = self.config.margins['left'] + 20
            legend_y = self.config.margins['top'] + 100
            
        # Draw legend background
        legend_rect = QRectF(legend_x, legend_y, legend_width, legend_height)
        painter.fillRect(legend_rect, QColor(255, 255, 255, 230))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(legend_rect)
        
        # Draw legend items
        y = legend_y + legend_padding
        
        for series_name, series in legend_items:
            # Color box
            color_rect = QRectF(
                legend_x + legend_padding,
                y + (item_height - color_box_size) / 2,
                color_box_size,
                color_box_size
            )
            painter.fillRect(color_rect, QColor(series.color))
            painter.setPen(QPen(QColor(series.color).darker(120), 1))
            painter.drawRect(color_rect)
            
            # Series name
            painter.setPen(QColor(self.config.text_color))
            text_rect = QRectF(
                legend_x + legend_padding + color_box_size + spacing,
                y,
                max_width,
                item_height
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, series_name)
            
            y += item_height
            
    def _draw_hover_elements(self, painter: QPainter, chart_rect: QRectF):
        """Draw hover tooltips and crosshairs."""
        if self.hover_series is None or self.hover_index < 0:
            return
            
        series = self.series.get(self.hover_series)
        if not series or self.hover_index >= len(series.data):
            return
            
        point = series.data[self.hover_index]
        
        # Get view ranges
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        x = self._map_x(point['x'], chart_rect, x_min, x_max)
        y = self._map_y(point['y'], chart_rect, y_min, y_max)
        
        # Draw crosshairs if enabled
        if self.config.enable_crosshair:
            painter.setPen(QPen(QColor(100, 100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))
            painter.drawLine(QPointF(chart_rect.left(), y), QPointF(chart_rect.right(), y))
            
        # Draw tooltip
        if self.config.enable_tooltips:
            # Format tooltip text
            tooltip_lines = [
                f"{self.hover_series}",
                f"X: {point['x']:.2f}" if isinstance(point['x'], (int, float)) else f"X: {point['x']}",
                f"Y: {point['y']:.2f}" if isinstance(point['y'], (int, float)) else f"Y: {point['y']}"
            ]
            
            # Add any extra metadata
            for key, value in point.items():
                if key not in ['x', 'y', 'label']:
                    tooltip_lines.append(f"{key}: {value}")
                    
            # Calculate tooltip dimensions
            font = QFont(self.config.font_family, 11)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            
            max_width = max(metrics.horizontalAdvance(line) for line in tooltip_lines)
            line_height = metrics.height()
            tooltip_height = len(tooltip_lines) * line_height + 16
            tooltip_width = max_width + 20
            
            # Position tooltip
            tooltip_x = x + 10
            tooltip_y = y - tooltip_height - 10
            
            # Keep tooltip within bounds
            if tooltip_x + tooltip_width > self.width():
                tooltip_x = x - tooltip_width - 10
            if tooltip_y < 0:
                tooltip_y = y + 10
                
            # Draw tooltip background
            tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
            
            if self.config.wsj_mode:
                painter.fillRect(tooltip_rect, QColor(40, 40, 40, 240))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.drawRect(tooltip_rect)
            else:
                painter.setBrush(QBrush(QColor(50, 50, 50, 220)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(tooltip_rect, 6, 6)
                
            # Draw tooltip text
            painter.setPen(QColor(255, 255, 255))
            y_offset = 8
            for line in tooltip_lines:
                painter.drawText(
                    QRectF(tooltip_x + 10, tooltip_y + y_offset, 
                          tooltip_width - 20, line_height),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    line
                )
                y_offset += line_height
                
    def _map_x(self, value: float, chart_rect: QRectF, x_min: float, x_max: float) -> float:
        """Map data X value to pixel coordinate."""
        if isinstance(value, datetime):
            value = value.timestamp()
            
        if x_max == x_min:
            return chart_rect.center().x()
            
        normalized = (value - x_min) / (x_max - x_min)
        return chart_rect.left() + normalized * chart_rect.width()
        
    def _map_y(self, value: float, chart_rect: QRectF, y_min: float, y_max: float) -> float:
        """Map data Y value to pixel coordinate."""
        if y_max == y_min:
            return chart_rect.center().y()
            
        normalized = (value - y_min) / (y_max - y_min)
        return chart_rect.bottom() - normalized * chart_rect.height()
        
    def _map_from_pixel(self, pixel_x: float, pixel_y: float, 
                       chart_rect: QRectF) -> Tuple[float, float]:
        """Map pixel coordinates back to data values."""
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # X value
        if chart_rect.width() > 0:
            x_normalized = (pixel_x - chart_rect.left()) / chart_rect.width()
            x_value = x_min + x_normalized * (x_max - x_min)
        else:
            x_value = (x_min + x_max) / 2
            
        # Y value
        if chart_rect.height() > 0:
            y_normalized = 1 - (pixel_y - chart_rect.top()) / chart_rect.height()
            y_value = y_min + y_normalized * (y_max - y_min)
        else:
            y_value = (y_min + y_max) / 2
            
        return x_value, y_value
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement."""
        chart_rect = self._get_chart_rect()
        pos = event.position().toPoint()
        
        # Handle panning
        if self.is_panning and event.buttons() & Qt.MouseButton.MiddleButton:
            delta = pos - self.pan_start
            self._pan_view(delta.x(), delta.y())
            self.pan_start = pos
            return
            
        # Handle selection
        if self.rubber_band and event.buttons() & Qt.MouseButton.LeftButton:
            self.rubber_band.setGeometry(QRect(self.selection_rect.topLeft(), pos).normalized())
            return
            
        # Handle hover
        if not chart_rect.contains(pos):
            if self.hover_series is not None:
                self.hover_series = None
                self.hover_index = -1
                self.update()
            return
            
        # Find closest point
        min_distance = float('inf')
        closest_series = None
        closest_index = -1
        
        for series_name, series in self.series.items():
            if not series.visible or not series.data:
                continue
                
            x_min, x_max = self.view_x_range or self.x_range
            y_min, y_max = self.view_y_range or self.y_range
            
            for i, point in enumerate(series.data):
                x = self._map_x(point['x'], chart_rect, x_min, x_max)
                y = self._map_y(point['y'], chart_rect, y_min, y_max)
                
                # Skip points outside view
                if x < chart_rect.left() or x > chart_rect.right():
                    continue
                    
                distance = ((x - pos.x()) ** 2 + (y - pos.y()) ** 2) ** 0.5
                
                if distance < min_distance and distance < 20:
                    min_distance = distance
                    closest_series = series_name
                    closest_index = i
                    
        # Update hover state
        if closest_series != self.hover_series or closest_index != self.hover_index:
            self.hover_series = closest_series
            self.hover_index = closest_index
            
            if self.hover_series is not None:
                series = self.series[self.hover_series]
                point = series.data[self.hover_index]
                self.dataPointHovered.emit(self.hover_series, point)
                
            self.update()
            
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        chart_rect = self._get_chart_rect()
        pos = event.position().toPoint()
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self.hover_series is not None and self.hover_index >= 0:
                # Click on data point
                series = self.series[self.hover_series]
                point = series.data[self.hover_index]
                self.dataPointClicked.emit(self.hover_series, point)
            elif chart_rect.contains(pos) and self.config.enable_selection:
                # Start selection
                self.selection_rect = QRect(pos, pos)
                self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
                self.rubber_band.setGeometry(self.selection_rect)
                self.rubber_band.show()
                
        elif event.button() == Qt.MouseButton.MiddleButton and self.config.enable_pan:
            # Start panning
            self.is_panning = True
            self.pan_start = pos
            self.pan_start_ranges = (
                self.view_x_range or self.x_range,
                self.view_y_range or self.y_range
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton and self.rubber_band:
            # Complete selection
            self.rubber_band.hide()
            selection = self.rubber_band.geometry()
            self.rubber_band = None
            
            if selection.width() > 10 and selection.height() > 10:
                self._zoom_to_rect(selection)
                
        elif event.button() == Qt.MouseButton.MiddleButton:
            # Stop panning
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        if not self.config.enable_zoom:
            return
            
        chart_rect = self._get_chart_rect()
        if not chart_rect.contains(event.position()):
            return
            
        # Zoom factor
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        
        # Get current ranges
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # Get mouse position in data coordinates
        mouse_x, mouse_y = self._map_from_pixel(
            event.position().x(), event.position().y(), chart_rect
        )
        
        # Calculate new ranges
        new_x_min = mouse_x - (mouse_x - x_min) * factor
        new_x_max = mouse_x + (x_max - mouse_x) * factor
        new_y_min = mouse_y - (mouse_y - y_min) * factor
        new_y_max = mouse_y + (y_max - mouse_y) * factor
        
        # Apply zoom
        self.view_x_range = (new_x_min, new_x_max)
        self.view_y_range = (new_y_min, new_y_max)
        
        self.rangeChanged.emit(new_x_min, new_x_max, new_y_min, new_y_max)
        self.update()
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_R:
            self.reset_view()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.export_chart()
            
    def _pan_view(self, dx: float, dy: float):
        """Pan the view by pixel amounts."""
        if not self.pan_start_ranges:
            return
            
        chart_rect = self._get_chart_rect()
        
        # Calculate data units per pixel
        (x_min, x_max), (y_min, y_max) = self.pan_start_ranges
        x_scale = (x_max - x_min) / chart_rect.width()
        y_scale = (y_max - y_min) / chart_rect.height()
        
        # Apply pan
        self.view_x_range = (x_min - dx * x_scale, x_max - dx * x_scale)
        self.view_y_range = (y_min + dy * y_scale, y_max + dy * y_scale)
        
        self.update()
        
    def _zoom_to_rect(self, rect: QRect):
        """Zoom to selected rectangle."""
        chart_rect = self._get_chart_rect()
        
        # Map rectangle corners to data coordinates
        x1, y1 = self._map_from_pixel(rect.left(), rect.top(), chart_rect)
        x2, y2 = self._map_from_pixel(rect.right(), rect.bottom(), chart_rect)
        
        # Set new view range
        self.view_x_range = (min(x1, x2), max(x1, x2))
        self.view_y_range = (min(y1, y2), max(y1, y2))
        
        self.rangeChanged.emit(*self.view_x_range, *self.view_y_range)
        self.update()
        
    def reset_view(self):
        """Reset zoom to show all data."""
        self.view_x_range = None
        self.view_y_range = None
        self._update_ranges()
        
        self.rangeChanged.emit(*self.x_range, *self.y_range)
        self.update()
        
    def zoom_in(self):
        """Zoom in by 20%."""
        self._zoom_by_factor(0.8)
        
    def zoom_out(self):
        """Zoom out by 20%.""" 
        self._zoom_by_factor(1.2)
        
    def _zoom_by_factor(self, factor: float):
        """Zoom by a given factor."""
        x_min, x_max = self.view_x_range or self.x_range
        y_min, y_max = self.view_y_range or self.y_range
        
        # Calculate centers
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        # Calculate new ranges
        x_half = (x_max - x_min) / 2 * factor
        y_half = (y_max - y_min) / 2 * factor
        
        self.view_x_range = (x_center - x_half, x_center + x_half)
        self.view_y_range = (y_center - y_half, y_center + y_half)
        
        self.rangeChanged.emit(*self.view_x_range, *self.view_y_range)
        self.update()
        
    def export_chart(self):
        """Export chart to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            "chart.png",
            "PNG Files (*.png);;SVG Files (*.svg);;PDF Files (*.pdf)"
        )
        
        if file_path:
            self.save_to_file(file_path)
            
    def save_to_file(self, file_path: str, width: Optional[int] = None, 
                     height: Optional[int] = None):
        """
        Save chart to file.
        
        Args:
            file_path: Output file path
            width: Optional width override
            height: Optional height override
        """
        path = Path(file_path)
        format = path.suffix.lower()[1:]  # Remove the dot
        
        # Hide toolbar for export
        toolbar_visible = self.toolbar.isVisible()
        self.toolbar.setVisible(False)
        
        try:
            if format == 'png':
                # Render to pixmap
                pixmap = QPixmap(width or self.width(), height or self.height())
                pixmap.fill(Qt.GlobalColor.transparent if self.config.export_transparent else QColor(self.config.background_color))
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.render(painter)
                painter.end()
                
                pixmap.save(file_path, 'PNG', quality=100)
                
            elif format == 'svg':
                from PyQt6.QtSvg import QSvgGenerator
                
                generator = QSvgGenerator()
                generator.setFileName(file_path)
                generator.setSize(QSize(width or self.width(), height or self.height()))
                generator.setViewBox(self.rect())
                
                painter = QPainter(generator)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.render(painter)
                painter.end()
                
            elif format == 'pdf':
                pdf = QPdfWriter(file_path)
                pdf.setPageSize(QPdfWriter.PageSize.A4)
                pdf.setResolution(self.config.export_dpi)
                
                painter = QPainter(pdf)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # Scale to fit page
                page_rect = painter.viewport()
                scale = min(page_rect.width() / self.width(), 
                           page_rect.height() / self.height())
                painter.scale(scale, scale)
                
                self.render(painter)
                painter.end()
                
        finally:
            # Restore toolbar
            self.toolbar.setVisible(toolbar_visible)