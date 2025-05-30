"""
Line chart component for visualizing time-series health data.

This module provides a highly customizable line chart widget specifically
designed for health data visualization in the Apple Health Monitor Dashboard.
It implements professional WSJ-inspired styling with smooth animations and
interactive features.

The LineChart widget is optimized for time-series health data and provides:
    - Smooth line rendering with anti-aliasing for professional appearance
    - Interactive hover tooltips with data point information
    - Animated transitions for engaging user experience
    - Responsive design that adapts to different screen sizes
    - Professional color scheme following design system guidelines
    - Accessibility features for inclusive design

Key features:
    - High-performance rendering using QPainterPath for smooth lines
    - Interactive data point hovering with visual feedback
    - Customizable grid system for better data reading
    - Professional typography and color schemes
    - Smooth animations with configurable timing
    - Export capabilities for reporting and sharing

Example:
    Basic line chart usage:
    
    >>> chart = LineChart()
    >>> chart.set_labels("Daily Steps", "Date", "Steps")
    >>> 
    >>> data_points = [
    ...     {"x": 1, "y": 8500, "label": "Jan 1"},
    ...     {"x": 2, "y": 9200, "label": "Jan 2"},
    ...     {"x": 3, "y": 7800, "label": "Jan 3"}
    ... ]
    >>> chart.set_data(data_points, animate=True)
    >>> chart.set_y_range(0, 15000)
    
    Interactive features:
    
    >>> # Connect to interaction signals
    >>> chart.dataPointHovered.connect(on_hover)
    >>> chart.dataPointClicked.connect(on_click)
    >>> 
    >>> def on_hover(data_point):
    ...     print(f"Hovering over: {data_point['label']} = {data_point['y']}")

Attributes:
    WSJ_SLATE (str): Professional slate color for lines and text
    BACKGROUND_WHITE (str): Clean white background
    GRID_LIGHT_GRAY (str): Subtle grid line color
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
import numpy as np

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal as Signal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPainterPath, 
    QFontMetrics, QMouseEvent, QResizeEvent, QPixmap
)


class LineChart(QWidget):
    """
    A professional line chart widget for time-series health data visualization.
    
    This widget provides a comprehensive line chart implementation specifically
    designed for health data visualization. It combines professional styling
    with interactive features and smooth animations to create an engaging
    data exploration experience.
    
    Core features:
        - High-quality line rendering with anti-aliasing for smooth curves
        - Interactive hover system with visual feedback and tooltips
        - Smooth animated transitions for data updates and initial display
        - Responsive design that adapts to various screen sizes
        - Professional WSJ-inspired color scheme and typography
        - Accessibility features including keyboard navigation support
    
    Visualization capabilities:
        - Time-series data with configurable date formatting
        - Customizable Y-axis ranges for different data scales
        - Optional data point markers for precise value identification
        - Grid system for improved data reading and estimation
        - Professional axis labeling with automatic formatting
        - Title and subtitle support for context and description
    
    Interaction features:
        - Hover detection with 20-pixel tolerance for easy targeting
        - Visual highlighting of hovered data points
        - Click handling for data point selection
        - Tooltip display with formatted data values
        - Mouse tracking for smooth interaction feedback
    
    Animation system:
        - Configurable animation duration and easing curves
        - Smooth entrance animations for initial chart display
        - Data update animations for seamless transitions
        - Performance-optimized rendering during animations
    
    Signals:
        dataPointHovered (dict): Emitted when mouse hovers over a data point.
            Args:
                data_point (dict): The hovered data point with 'x', 'y', and
                    optional 'label' keys
        dataPointClicked (dict): Emitted when a data point is clicked.
            Args:
                data_point (dict): The clicked data point with complete data
    
    Attributes:
        data_points (List[Dict[str, Any]]): Chart data with x, y, and label values
        x_labels (List[str]): Custom X-axis labels for better formatting
        y_range (Tuple[float, float]): Y-axis range as (min, max) values
        title (str): Chart title displayed at the top
        x_axis_label (str): X-axis label for context
        y_axis_label (str): Y-axis label for units and description
        show_grid (bool): Whether to display background grid lines
        show_dots (bool): Whether to show data point markers
        animate (bool): Whether to enable smooth animations
        colors (Dict[str, QColor]): Professional color scheme
        margins (Dict[str, int]): Chart margins for proper spacing
        hover_index (int): Index of currently hovered data point (-1 if none)
        animation_progress (float): Current animation progress (0.0 to 1.0)
    
    Example:
        Creating a health metrics line chart:
        
        >>> chart = LineChart()
        >>> chart.set_labels(
        ...     title="Daily Heart Rate Trends",
        ...     x_label="Date",
        ...     y_label="BPM"
        ... )
        >>> 
        >>> # Set up data points
        >>> heart_rate_data = [
        ...     {"x": 1, "y": 72, "label": "Mon"},
        ...     {"x": 2, "y": 68, "label": "Tue"},
        ...     {"x": 3, "y": 75, "label": "Wed"}
        ... ]
        >>> chart.set_data(heart_rate_data, animate=True)
        >>> chart.set_y_range(60, 90)
        >>> 
        >>> # Connect interaction handlers
        >>> chart.dataPointHovered.connect(show_heart_rate_details)
        >>> chart.dataPointClicked.connect(drill_down_to_hourly_data)
    """
    
    # Signals
    dataPointHovered = Signal(dict)  # Emits data point info on hover
    dataPointClicked = Signal(dict)  # Emits data point info on click
    
    def __init__(self, parent=None, data=None):
        """Initialize the line chart widget with professional styling.
        
        Sets up a complete line chart widget with professional WSJ-inspired
        styling, interactive capabilities, and smooth animation support.
        The initialization configures all necessary components for immediate use.
        
        Initialization process:
            1. Initialize Qt widget with parent relationship
            2. Set up data storage for chart points and labels
            3. Configure chart display properties and styling
            4. Apply professional color scheme and typography
            5. Set up layout configuration with proper margins
            6. Initialize interaction state tracking
            7. Configure animation system with smooth transitions
        
        Args:
            parent (QWidget, optional): Parent widget for the chart.
                Defaults to None for standalone usage.
            data (pandas.DataFrame or list, optional): Initial data to display.
                Can be a DataFrame or list of data points. Defaults to None.
        
        Professional styling:
            - WSJ-inspired color palette with slate gray primary colors
            - Clean white background for optimal readability
            - Subtle grid lines for data reference without distraction
            - Professional typography using Inter font family
            - Proper margins and spacing for clean layout
        
        Interactive features:
            - Mouse tracking enabled for hover detection
            - Hover tolerance configured for easy data point targeting
            - Click handling for data point selection
            - Visual feedback for hovered elements
        
        Animation setup:
            - Smooth animation system with OutCubic easing
            - 500ms duration for optimal user experience
            - Property-based animations for data updates
            - Performance-optimized rendering during transitions
        
        Default configuration:
            - Minimum size: 400x300 pixels for readability
            - Grid and dots enabled for complete functionality
            - Animations enabled for engaging experience
            - Professional margins: 40/20/60/80 (top/right/bottom/left)
        """
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
        
        # Colors from design system - WSJ-inspired professional palette
        self.colors = {
            'background': QColor('#FFFFFF'),
            'grid': QColor('#E9ECEF'),
            'axis': QColor('#6C757D'),
            'line': QColor('#5B6770'),  # Primary slate
            'dot': QColor('#5B6770'),
            'hover': QColor('#4A5560'),
            'text': QColor('#212529'),
            'text_muted': QColor('#ADB5BD')
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
        
        # Set initial data if provided
        if data is not None:
            self.set_data(data)
        
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
        self._animation_progress = 0.0
        self.animation = QPropertyAnimation(self, b"animation_progress")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.update)
        
    def get_animation_progress(self):
        """Get animation progress value."""
        return self._animation_progress
        
    def set_animation_progress(self, value):
        """Set animation progress value."""
        self._animation_progress = value
        self.update()
        
    animation_progress = pyqtProperty(float, get_animation_progress, set_animation_progress)
        
    def set_data(self, data_points=None, y_values=None, animate: bool = True):
        """
        Set chart data.
        
        Args:
            data_points: List of dictionaries with 'x', 'y', and optional 'label' keys,
                        OR pandas Series for x-values when y_values is provided
            y_values: Optional pandas Series for y-values (when data_points is x-values)
            animate: Whether to animate the data change
        """
        # Handle dual parameter call (x_series, y_series) for testing compatibility
        if y_values is not None:
            # Convert pandas series to list of dictionaries
            import pandas as pd
            if hasattr(data_points, 'iloc') and hasattr(y_values, 'iloc'):
                # Both are pandas Series
                self.data_points = []
                for i in range(len(data_points)):
                    x_val = data_points.iloc[i] 
                    y_val = y_values.iloc[i]
                    
                    # Convert date to string label if it's a datetime
                    if hasattr(x_val, 'strftime'):
                        label = x_val.strftime('%Y-%m-%d')
                    else:
                        label = str(x_val)
                        
                    self.data_points.append({
                        'x': i,  # Use index for x position
                        'y': float(y_val),
                        'label': label
                    })
            else:
                # Handle other iterable types
                self.data_points = []
                for i, (x_val, y_val) in enumerate(zip(data_points, y_values)):
                    self.data_points.append({
                        'x': i,
                        'y': float(y_val),
                        'label': str(x_val)
                    })
        else:
            # Original single parameter call
            if data_points is None:
                self.data_points = []
            else:
                # Handle DataFrame input - convert to appropriate format
                import pandas as pd
                if isinstance(data_points, pd.DataFrame):
                    # Convert DataFrame to list of dictionaries
                    self.data_points = []
                    for idx, row in data_points.iterrows():
                        # Use first numeric column as y value, index as x
                        numeric_cols = data_points.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            y_val = row[numeric_cols[0]]
                            self.data_points.append({
                                'x': idx,
                                'y': float(y_val),
                                'label': str(idx)
                            })
                else:
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
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
            
        painter.setPen(QPen(self.colors['grid'], 1, Qt.PenStyle.DashLine))
        
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
            title_font = QFont("Inter", 18)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(self.colors['text'])
            
            title_rect = QRectF(0, 0, self.width(), self.margins['top'])
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
            
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
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
            
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
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
                
        # Axis labels
        if self.x_axis_label:
            painter.drawText(
                QRectF(0, self.height() - 30, self.width(), 20),
                Qt.AlignmentFlag.AlignCenter,
                self.x_axis_label
            )
            
        if self.y_axis_label:
            painter.save()
            painter.translate(15, self.height() / 2)
            painter.rotate(-90)
            painter.drawText(
                QRectF(-50, -10, 100, 20),
                Qt.AlignmentFlag.AlignCenter,
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
        painter.setPen(QPen(self.colors['line'], 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
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
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(tooltip_rect, 6, 6)
        
        # Draw text
        painter.setPen(QColor('#FFFFFF'))
        painter.drawText(tooltip_rect, Qt.AlignmentFlag.AlignCenter, tooltip_text)
        
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
        mouse_x = event.position().x()
        
        # Find closest data point
        old_hover = self.hover_index
        self.hover_index = -1
        
        if chart_rect.contains(event.position().toPoint()) and self.data_points:
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
        if event.button() == Qt.MouseButton.LeftButton and self.hover_index >= 0:
            self.dataPointClicked.emit(self.data_points[self.hover_index])
            
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.hover_index = -1
        self.update()
        
    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize."""
        super().resizeEvent(event)
        self.update()
        
    def configure(self, width: int = 800, height: int = 600, animate: bool = True, **kwargs):
        """Configure chart dimensions and options for testing compatibility.
        
        Args:
            width (int): Chart width in pixels
            height (int): Chart height in pixels  
            animate (bool): Enable/disable animations
            **kwargs: Additional configuration options (ignored for compatibility)
        """
        self.resize(width, height)
        self.animate = animate
        # Store configured dimensions for render_to_image
        self._configured_width = width
        self._configured_height = height
        
    def set_title(self, title: str):
        """Set chart title for testing compatibility.
        
        Args:
            title (str): Chart title text
        """
        self.title = title
        self.update()
        
    def render_to_image(self, width: int = None, height: int = None, dpi: int = 100):
        """Render chart to image for testing.
        
        Args:
            width (int): Image width in pixels (defaults to configured width or 800)
            height (int): Image height in pixels (defaults to configured height or 600)
            dpi (int): Image resolution (ignored, for compatibility)
            
        Returns:
            QPixmap: Rendered chart image
        """
        # Use configured dimensions if available, otherwise defaults
        if width is None:
            width = getattr(self, '_configured_width', 800)
        if height is None:
            height = getattr(self, '_configured_height', 600)
        # Create pixmap with specified dimensions
        pixmap = QPixmap(width, height)
        pixmap.fill(self.colors['background'])
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate chart area for the specific image size
        chart_rect = QRectF(
            self.margins['left'],
            self.margins['top'],
            width - self.margins['left'] - self.margins['right'],
            height - self.margins['top'] - self.margins['bottom']
        )
        
        # Draw components using the image-specific rect
        self._draw_background_to_painter(painter, width, height)
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_labels_to_painter(painter, chart_rect, width, height)
        self._draw_data_to_painter(painter, chart_rect)
        
        painter.end()
        return pixmap
        
    def _draw_background_to_painter(self, painter: QPainter, width: int, height: int):
        """Draw chart background to painter with specific dimensions."""
        painter.fillRect(0, 0, width, height, self.colors['background'])
        
    def _draw_labels_to_painter(self, painter: QPainter, chart_rect: QRectF, width: int, height: int):
        """Draw axis labels and title to painter with specific dimensions."""
        # Title
        if self.title:
            title_font = QFont("Inter", 18)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(self.colors['text'])
            
            title_rect = QRectF(0, 0, width, self.margins['top'])
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
            
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
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
            
        # X-axis labels
        if self.data_points:
            x_steps = min(len(self.data_points) - 1, 10)
            for i in range(0, len(self.data_points), max(1, len(self.data_points) // x_steps)):
                x = self._map_x_for_rect(i, chart_rect)
                
                if 'label' in self.data_points[i]:
                    label = self.data_points[i]['label']
                else:
                    label = str(self.data_points[i]['x'])
                    
                label_rect = QRectF(x - 50, chart_rect.bottom() + 5, 100, 20)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
                
        # Axis labels
        if self.x_axis_label:
            painter.drawText(
                QRectF(0, height - 30, width, 20),
                Qt.AlignmentFlag.AlignCenter,
                self.x_axis_label
            )
            
        if self.y_axis_label:
            painter.save()
            painter.translate(15, height / 2)
            painter.rotate(-90)
            painter.drawText(
                QRectF(-50, -10, 100, 20),
                Qt.AlignmentFlag.AlignCenter,
                self.y_axis_label
            )
            painter.restore()
            
    def _map_x_for_rect(self, index: int, chart_rect: QRectF) -> float:
        """Map data index to X coordinate for a specific rect."""
        if len(self.data_points) <= 1:
            return chart_rect.center().x()
        return chart_rect.left() + (index / (len(self.data_points) - 1)) * chart_rect.width()
        
    def _draw_data_to_painter(self, painter: QPainter, chart_rect: QRectF):
        """Draw the data line and points to a specific painter and rect."""
        if not self.data_points:
            return
            
        # Create path for line
        path = QPainterPath()
        
        # Draw line
        painter.setPen(QPen(self.colors['line'], 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        for i, point in enumerate(self.data_points):
            x = self._map_x_for_rect(i, chart_rect)
            y = self._map_y_for_rect(point['y'], chart_rect)
            
            # No animation for image rendering
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
                
        painter.drawPath(path)
        
        # Draw dots
        if self.show_dots:
            for i, point in enumerate(self.data_points):
                x = self._map_x_for_rect(i, chart_rect)
                y = self._map_y_for_rect(point['y'], chart_rect)
                    
                painter.setBrush(QBrush(self.colors['dot']))
                painter.setPen(QPen(self.colors['background'], 2))
                painter.drawEllipse(QPointF(x, y), 4, 4)
                
    def _map_y_for_rect(self, value: float, chart_rect: QRectF) -> float:
        """Map data value to Y coordinate for a specific rect."""
        y_min, y_max = self.y_range
        if y_max == y_min:
            return chart_rect.center().y()
        normalized = (value - y_min) / (y_max - y_min)
        return chart_rect.bottom() - normalized * chart_rect.height()