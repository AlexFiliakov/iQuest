"""
Calendar heatmap component for visualizing health metrics over time.

Provides multiple view modes:
- Traditional month grid calendar
- GitHub-style contribution graph
- Circular/spiral year view

Inspired by Wall Street Journal chart styling with warm, accessible design.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, date, timedelta
import calendar
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QPushButton, 
    QLabel, QToolTip, QComboBox, QSlider, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, 
    QLinearGradient, QRadialGradient, QPainterPath, QPolygonF
)
import numpy as np

class ViewMode:
    """Calendar heatmap view modes."""
    MONTH_GRID = "month_grid"
    GITHUB_STYLE = "github_style"
    CIRCULAR = "circular"


class ColorScale:
    """Available color scales for the heatmap."""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    CIVIDIS = "cividis"
    WARM_ORANGE = "warm_orange"  # Custom WSJ-inspired scale


class CalendarHeatmapComponent(QWidget):
    """
    Advanced calendar heatmap component with multiple view modes.
    
    Features:
    - Three view modes: month grid, GitHub-style, circular
    - Interactive hover details and drill-down
    - Brush selection for date ranges
    - Touch gesture support
    - Perceptually uniform color scales
    - Colorblind accessibility patterns
    - Wall Street Journal styling inspiration
    """
    
    # Signals
    date_clicked = pyqtSignal(date)
    date_range_selected = pyqtSignal(date, date)
    view_mode_changed = pyqtSignal(str)
    
    def __init__(self, monthly_calculator=None, parent=None):
        """Initialize the calendar heatmap component."""
        super().__init__(parent)
        
        self.monthly_calculator = monthly_calculator
        
        # View configuration
        self._view_mode = ViewMode.MONTH_GRID
        self._color_scale = ColorScale.WARM_ORANGE
        self._metric_type = "steps"
        self._current_date = datetime.now().date()
        self._data_range = None
        
        # Interactive state
        self._hover_date = None
        self._selection_start = None
        self._selection_end = None
        self._brush_active = False
        
        # Visual configuration
        self._cell_size = 20
        self._cell_spacing = 2
        self._show_patterns = False  # For colorblind accessibility
        self._show_today_marker = True
        
        # Animation
        self._pulse_animation = QPropertyAnimation(self, b"animationProgress")
        self._pulse_animation.setDuration(2000)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Color system
        self._colors = self._get_default_colors()
        self._fonts = self._get_default_fonts()
        
        # Color scales
        self._color_scales = self._initialize_color_scales()
        
        # Data cache
        self._metric_data = {}
        self._data_bounds = (0, 1)
        
        # Setup
        self._setup_ui()
        self._setup_interactions()
        
    def _get_default_colors(self) -> Dict[str, QColor]:
        """Get default color scheme from design system."""
        return {
            # Background colors
            'background': QColor('#FFFFFF'),
            'background_alt': QColor('#FFF8F0'),
            'tertiary_bg': QColor('#FFF8F0'),
            
            # Grid and axes
            'grid': QColor('#E8DCC8'),
            'axis': QColor('#8B7355'),
            
            # Data colors
            'primary': QColor('#FF8C42'),
            'secondary': QColor('#FFD166'),
            'success': QColor('#95C17B'),
            'warning': QColor('#F4A261'),
            'error': QColor('#E76F51'),
            
            # Text colors
            'text': QColor('#5D4E37'),
            'text_secondary': QColor('#8B7355'),
            'text_muted': QColor('#A69583'),
            'text_inverse': QColor('#FFFFFF'),
            
            # Interactive states
            'hover': QColor('#E67A35'),
            'active': QColor('#D56F2B'),
            'disabled': QColor('#E8DCC8')
        }
        
    def _get_default_fonts(self) -> Dict[str, QFont]:
        """Get default fonts from design system."""
        return {
            'title': QFont('Poppins', 18, QFont.Weight.Bold),
            'subtitle': QFont('Inter', 14, QFont.Weight.Normal),
            'label': QFont('Inter', 11, QFont.Weight.Normal),
            'label_small': QFont('Inter', 10, QFont.Weight.Normal),
            'value': QFont('Inter', 13, QFont.Weight.Medium),
            'value_large': QFont('Poppins', 16, QFont.Weight.Bold)
        }
        
    def _initialize_color_scales(self) -> Dict[str, List[QColor]]:
        """Initialize perceptually uniform color scales."""
        return {
            ColorScale.WARM_ORANGE: [
                QColor("#FFF8F0"),  # Very light cream
                QColor("#FFE8D1"),  # Light cream
                QColor("#FFD4B3"),  # Light peach
                QColor("#FFB584"),  # Medium peach
                QColor("#FF8C42"),  # Main orange
                QColor("#E67A35"),  # Dark orange
                QColor("#CC6B2E"),  # Darker orange
                QColor("#B85C27")   # Darkest orange
            ],
            ColorScale.VIRIDIS: [
                QColor("#440154"),
                QColor("#482777"),
                QColor("#3F4A8A"),
                QColor("#31678E"),
                QColor("#26838F"),
                QColor("#1F9D8A"),
                QColor("#6CCE5A"),
                QColor("#B6DE2B")
            ],
            ColorScale.CIVIDIS: [
                QColor("#00204C"),
                QColor("#31446B"),
                QColor("#666870"),
                QColor("#958F78"),
                QColor("#C7B884"),
                QColor("#F0E795"),
                QColor("#FFEA46")
            ]
        }
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Control panel
        controls = self._create_control_panel()
        layout.addWidget(controls)
        
        # Chart area (will be drawn in paintEvent)
        layout.addStretch()
        
        # Set minimum size
        self.setMinimumSize(600, 400)
        
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with view mode buttons and options."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['background_alt'].name()};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        
        layout = QHBoxLayout(panel)
        layout.setSpacing(16)
        
        # View mode buttons
        view_group = QButtonGroup(self)
        
        # Month grid button
        month_btn = QPushButton("Month Grid")
        month_btn.setCheckable(True)
        month_btn.setChecked(True)
        month_btn.clicked.connect(lambda: self._change_view_mode(ViewMode.MONTH_GRID))
        view_group.addButton(month_btn)
        layout.addWidget(month_btn)
        
        # GitHub style button
        github_btn = QPushButton("GitHub Style")
        github_btn.setCheckable(True)
        github_btn.clicked.connect(lambda: self._change_view_mode(ViewMode.GITHUB_STYLE))
        view_group.addButton(github_btn)
        layout.addWidget(github_btn)
        
        # Circular view button
        circular_btn = QPushButton("Circular View")
        circular_btn.setCheckable(True)
        circular_btn.clicked.connect(lambda: self._change_view_mode(ViewMode.CIRCULAR))
        view_group.addButton(circular_btn)
        layout.addWidget(circular_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.VLine)
        separator.setStyleSheet("color: rgba(139, 115, 85, 0.3);")
        layout.addWidget(separator)
        
        # Color scale selector
        scale_label = QLabel("Color Scale:")
        layout.addWidget(scale_label)
        
        scale_combo = QComboBox()
        scale_combo.addItems(["Warm Orange", "Viridis", "Cividis"])
        scale_combo.currentTextChanged.connect(self._change_color_scale)
        layout.addWidget(scale_combo)
        
        # Accessibility options
        patterns_cb = QCheckBox("Colorblind Patterns")
        patterns_cb.toggled.connect(self._toggle_patterns)
        layout.addWidget(patterns_cb)
        
        layout.addStretch()
        
        # Apply button styling
        button_style = f"""
            QPushButton {{
                background-color: {self._colors['background'].name()};
                border: 2px solid {self._colors['grid'].name()};
                border-radius: 6px;
                padding: 8px 16px;
                color: {self._colors['text'].name()};
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {self._colors['primary'].name()};
                background-color: {self._colors['background_alt'].name()};
            }}
            QPushButton:checked {{
                background-color: {self._colors['primary'].name()};
                border-color: {self._colors['primary'].name()};
                color: {self._colors['text_inverse'].name()};
            }}
        """
        
        for btn in view_group.buttons():
            btn.setStyleSheet(button_style)
            
        return panel
        
    def _setup_interactions(self):
        """Set up mouse and keyboard interactions."""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Start pulse animation for today marker
        if self._show_today_marker:
            self._pulse_animation.setStartValue(0.3)
            self._pulse_animation.setEndValue(1.0)
            self._pulse_animation.start()
            
    def _change_view_mode(self, mode: str):
        """Change the calendar view mode."""
        if mode != self._view_mode:
            self._view_mode = mode
            self.view_mode_changed.emit(mode)
            self.animate_update()
            
    def _change_color_scale(self, scale_name: str):
        """Change the color scale."""
        scale_map = {
            "Warm Orange": ColorScale.WARM_ORANGE,
            "Viridis": ColorScale.VIRIDIS,
            "Cividis": ColorScale.CIVIDIS
        }
        
        if scale_name in scale_map:
            self._color_scale = scale_map[scale_name]
            self.update()
            
    def _toggle_patterns(self, enabled: bool):
        """Toggle colorblind accessibility patterns."""
        self._show_patterns = enabled
        self.update()
        
    def set_metric_data(self, metric_type: str, data: Dict[date, float]):
        """Set the metric data for the heatmap."""
        self._metric_type = metric_type
        self._metric_data = data
        
        # Calculate data bounds for color scaling
        if data:
            values = list(data.values())
            self._data_bounds = (min(values), max(values))
        else:
            self._data_bounds = (0, 1)
            
        self._on_data_changed()
        
    def _on_data_changed(self):
        """Handle data changes."""
        self.update()
        
    def _get_color_for_value(self, value: Optional[float]) -> QColor:
        """Get color for a metric value using the selected scale."""
        if value is None:
            return QColor("#F0F0F0")  # Light gray for missing data
            
        # Normalize value to 0-1 range
        min_val, max_val = self._data_bounds
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)
            
        # Clamp to valid range
        normalized = max(0, min(1, normalized))
        
        # Get color from scale
        colors = self._color_scales[self._color_scale]
        if normalized == 0:
            return colors[0]
        elif normalized == 1:
            return colors[-1]
        else:
            # Interpolate between colors
            index = normalized * (len(colors) - 1)
            lower_idx = int(index)
            upper_idx = min(lower_idx + 1, len(colors) - 1)
            
            if lower_idx == upper_idx:
                return colors[lower_idx]
                
            # Linear interpolation
            t = index - lower_idx
            lower_color = colors[lower_idx]
            upper_color = colors[upper_idx]
            
            r = int(lower_color.red() + t * (upper_color.red() - lower_color.red()))
            g = int(lower_color.green() + t * (upper_color.green() - lower_color.green()))
            b = int(lower_color.blue() + t * (upper_color.blue() - lower_color.blue()))
            
            return QColor(r, g, b)
            
    def paintEvent(self, event):
        """Paint the calendar heatmap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), self._colors['background'])
        
        # Get chart area (excluding margins)
        margins = {'top': 80, 'right': 20, 'bottom': 60, 'left': 20}
        chart_rect = self.rect().adjusted(
            margins['left'], margins['top'],
            -margins['right'], -margins['bottom']
        )
        
        # Draw based on view mode
        if self._view_mode == ViewMode.MONTH_GRID:
            self._draw_month_grid(painter, chart_rect)
        elif self._view_mode == ViewMode.GITHUB_STYLE:
            self._draw_github_style(painter, chart_rect)
        elif self._view_mode == ViewMode.CIRCULAR:
            self._draw_circular_view(painter, chart_rect)
            
        # Draw title if set
        title = f"{self._metric_type.title()} Calendar Heatmap"
        self._draw_title(painter, title)
        
    def _draw_month_grid(self, painter: QPainter, rect: QRect):
        """Draw traditional month grid calendar view."""
        if not self._metric_data:
            self._draw_no_data_message(painter, rect)
            return
            
        # Calculate grid dimensions
        year = self._current_date.year
        month = self._current_date.month
        
        # Get month info
        first_day = date(year, month, 1)
        days_in_month = calendar.monthrange(year, month)[1]
        first_weekday = first_day.weekday()  # 0 = Monday
        
        # Calculate cell size
        grid_width = rect.width() - 100  # Leave space for labels
        grid_height = rect.height() - 80
        
        cell_width = min(grid_width // 7, grid_height // 6)
        cell_height = cell_width
        
        # Starting position
        start_x = rect.x() + (rect.width() - 7 * cell_width) // 2
        start_y = rect.y() + 60
        
        # Draw day labels
        painter.setFont(self._fonts['label'])
        painter.setPen(self._colors['text_secondary'])
        
        day_labels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        for i, label in enumerate(day_labels):
            x = start_x + i * cell_width + cell_width // 2
            y = start_y - 10
            painter.drawText(QPoint(x, y), label)
            
        # Draw calendar cells
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            week = (day + first_weekday - 1) // 7
            weekday = (day + first_weekday - 1) % 7
            
            x = start_x + weekday * cell_width
            y = start_y + week * cell_height
            
            cell_rect = QRect(x + 1, y + 1, cell_width - 2, cell_height - 2)
            
            # Get value and color
            value = self._metric_data.get(current_date)
            color = self._get_color_for_value(value)
            
            # Draw cell
            painter.fillRect(cell_rect, color)
            
            # Draw border
            painter.setPen(QPen(self._colors['grid'], 1))
            painter.drawRect(cell_rect)
            
            # Draw pattern if enabled
            if self._show_patterns and value is not None:
                self._draw_accessibility_pattern(painter, cell_rect, value)
                
            # Draw today marker
            if current_date == date.today() and self._show_today_marker:
                self._draw_today_marker(painter, cell_rect)
                
            # Draw day number
            painter.setPen(self._colors['text'])
            painter.setFont(self._fonts['label_small'])
            painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, str(day))
            
    def _draw_github_style(self, painter: QPainter, rect: QRect):
        """Draw GitHub-style contribution graph."""
        if not self._metric_data:
            self._draw_no_data_message(painter, rect)
            return
            
        # Calculate 52 weeks x 7 days grid
        cell_size = min((rect.width() - 100) // 53, (rect.height() - 80) // 8)
        
        start_x = rect.x() + 50
        start_y = rect.y() + 60
        
        # Draw month labels
        painter.setFont(self._fonts['label'])
        painter.setPen(self._colors['text_secondary'])
        
        current_year = self._current_date.year
        start_date = date(current_year, 1, 1)
        
        # Draw each week
        for week in range(52):
            for day in range(7):
                target_date = start_date + timedelta(weeks=week, days=day)
                
                if target_date.year != current_year:
                    continue
                    
                x = start_x + week * (cell_size + 1)
                y = start_y + day * (cell_size + 1)
                
                cell_rect = QRect(x, y, cell_size, cell_size)
                
                # Get value and color
                value = self._metric_data.get(target_date)
                color = self._get_color_for_value(value)
                
                # Draw cell
                painter.fillRect(cell_rect, color)
                painter.setPen(QPen(self._colors['grid'], 1))
                painter.drawRect(cell_rect)
                
                # Draw pattern if enabled
                if self._show_patterns and value is not None:
                    self._draw_accessibility_pattern(painter, cell_rect, value)
                    
                # Draw today marker
                if target_date == date.today() and self._show_today_marker:
                    self._draw_today_marker(painter, cell_rect)
                    
    def _draw_circular_view(self, painter: QPainter, rect: QRect):
        """Draw circular/spiral year view."""
        if not self._metric_data:
            self._draw_no_data_message(painter, rect)
            return
            
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 50
        
        # Draw 365 days in a circle
        current_year = self._current_date.year
        start_date = date(current_year, 1, 1)
        days_in_year = 366 if calendar.isleap(current_year) else 365
        
        for day_of_year in range(days_in_year):
            target_date = start_date + timedelta(days=day_of_year)
            
            # Calculate angle (start from top, go clockwise)
            angle = -90 + (day_of_year / days_in_year) * 360
            angle_rad = math.radians(angle)
            
            # Calculate position on circle
            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)
            
            # Cell size varies by radius for spiral effect
            cell_size = 4
            cell_rect = QRect(int(x - cell_size//2), int(y - cell_size//2), cell_size, cell_size)
            
            # Get value and color
            value = self._metric_data.get(target_date)
            color = self._get_color_for_value(value)
            
            # Draw cell
            painter.fillRect(cell_rect, color)
            
            # Draw today marker
            if target_date == date.today() and self._show_today_marker:
                painter.setPen(QPen(self._colors['primary'], 2))
                painter.drawEllipse(cell_rect.adjusted(-2, -2, 2, 2))
                
        # Draw season labels
        painter.setFont(self._fonts['label'])
        painter.setPen(self._colors['text'])
        
        season_labels = ['Winter', 'Spring', 'Summer', 'Fall']
        season_angles = [0, 90, 180, 270]
        
        for i, (label, angle) in enumerate(zip(season_labels, season_angles)):
            angle_rad = math.radians(angle - 90)
            label_radius = radius + 30
            x = center.x() + label_radius * math.cos(angle_rad)
            y = center.y() + label_radius * math.sin(angle_rad)
            
            painter.drawText(QPoint(int(x), int(y)), label)
            
    def _draw_accessibility_pattern(self, painter: QPainter, rect: QRect, value: float):
        """Draw accessibility patterns for colorblind users."""
        min_val, max_val = self._data_bounds
        normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
        
        painter.setPen(QPen(self._colors['text'], 1))
        
        if normalized < 0.3:
            # Light dots
            painter.drawPoint(rect.center())
        elif normalized < 0.6:
            # Diagonal lines
            painter.drawLine(rect.topLeft(), rect.bottomRight())
        else:
            # Dense pattern
            for i in range(0, rect.width(), 3):
                painter.drawLine(rect.x() + i, rect.y(), rect.x() + i, rect.bottom())
                
    def _draw_today_marker(self, painter: QPainter, rect: QRect):
        """Draw the today marker with pulse animation."""
        opacity = 0.5 + 0.5 * self._animation_progress  # Pulse between 0.5 and 1.0
        
        # Draw pulsing border
        pen = QPen(self._colors['primary'], 3)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setOpacity(opacity)
        painter.drawRect(rect.adjusted(-2, -2, 2, 2))
        painter.setOpacity(1.0)
        
    def _draw_title(self, painter: QPainter, title: str):
        """Draw chart title."""
        if not title:
            return
            
        painter.setFont(self._fonts['title'])
        painter.setPen(self._colors['text'])
        
        # Title area
        title_rect = QRect(20, 10, self.width() - 40, 30)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        
    def _draw_no_data_message(self, painter: QPainter, rect: QRect):
        """Draw a message when no data is available."""
        painter.setFont(self._fonts['subtitle'])
        painter.setPen(self._colors['text_muted'])
        
        message = "No metric data available for the selected period"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, message)
        
    def mousePressEvent(self, event):
        """Handle mouse press for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            date_clicked = self._get_date_at_position(event.position().toPoint())
            if date_clicked:
                self._selection_start = date_clicked
                self._brush_active = True
                
    def mouseMoveEvent(self, event):
        """Handle mouse move for hover and selection."""
        pos = event.position().toPoint()
        hover_date = self._get_date_at_position(pos)
        
        if hover_date != self._hover_date:
            self._hover_date = hover_date
            
            # Show tooltip
            if hover_date and hover_date in self._metric_data:
                value = self._metric_data[hover_date]
                tooltip_text = f"{hover_date.strftime('%B %d, %Y')}\n{self._metric_type}: {value:,.1f}"
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text)
            else:
                QToolTip.hideText()
                
            self.update()
            
        # Handle brush selection
        if self._brush_active and hover_date:
            self._selection_end = hover_date
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release for selection completion."""
        if event.button() == Qt.MouseButton.LeftButton and self._brush_active:
            self._brush_active = False
            
            if self._selection_start and self._selection_end:
                start = min(self._selection_start, self._selection_end)
                end = max(self._selection_start, self._selection_end)
                self.date_range_selected.emit(start, end)
            elif self._selection_start:
                self.date_clicked.emit(self._selection_start)
                
            self._selection_start = None
            self._selection_end = None
            self.update()
            
    def _get_date_at_position(self, pos: QPoint) -> Optional[date]:
        """Get the date at the given position based on current view mode."""
        # This would be implemented based on the current view mode
        # For now, return None as placeholder
        return None
        
    def set_current_date(self, target_date: date):
        """Set the current date for month grid view."""
        self._current_date = target_date
        self.update()
        
    def get_current_date(self) -> date:
        """Get the current date."""
        return self._current_date