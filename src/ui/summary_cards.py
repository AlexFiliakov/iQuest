"""
Summary card components for displaying key health metrics.
Provides reusable card widgets with trend indicators, animations, and responsive layouts.
"""

from typing import Dict, Optional, Union

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.utils.logging_config import get_logger

from .style_manager import StyleManager

logger = get_logger(__name__)


class SummaryCard(QWidget):
    """Base class for summary cards displaying health metrics."""
    
    # Signal emitted when card is clicked
    clicked = pyqtSignal(str)  # card_id
    
    SIZE_CONFIGS = {
        'small': {
            'min_width': 150,
            'min_height': 100,
            'title_font': 12,
            'value_font': 24,
            'padding': 10
        },
        'medium': {
            'min_width': 200,
            'min_height': 150,
            'title_font': 14,
            'value_font': 32,
            'padding': 15
        },
        'large': {
            'min_width': 300,
            'min_height': 200,
            'title_font': 16,
            'value_font': 48,
            'padding': 20
        }
    }
    
    def __init__(self, card_type: str = 'simple', size: str = 'medium', card_id: str = ""):
        super().__init__()
        self.card_type = card_type
        self.size = size
        self.card_id = card_id
        self.style_manager = StyleManager()
        
        # Animation properties
        self._animated_value = 0.0
        self.value_animator = QPropertyAnimation(self, b"animated_value")
        self.value_animator.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.setup_ui()
        self.apply_size_config()
        self.apply_card_style()
        
        logger.debug(f"Created {card_type} summary card with size {size}")
    
    @pyqtProperty(float)
    def animated_value(self):
        """Property for animating numeric values."""
        return self._animated_value
    
    @animated_value.setter
    def animated_value(self, value):
        """Setter for animated value property."""
        self._animated_value = value
        self.update_value_display(value)
    
    def setup_ui(self):
        """Setup card UI based on type. Override in subclasses."""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        # Card container with styling
        self.card_frame = QFrame(self)
        self.card_frame.setObjectName("summaryCard")
        
        # Default content
        self.content_layout = QVBoxLayout(self.card_frame)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.layout.addWidget(self.card_frame)
    
    def apply_size_config(self):
        """Apply size-specific configuration."""
        config = self.SIZE_CONFIGS[self.size]
        
        self.setMinimumSize(config['min_width'], config['min_height'])
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def apply_card_style(self):
        """Apply card styling using StyleManager."""
        shadow = self.style_manager.get_shadow_style('md')
        padding = self.SIZE_CONFIGS[self.size]['padding']
        
        style = f"""
            QFrame#summaryCard {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
                border: none;
                padding: {padding}px;
            }}
            
            QFrame#summaryCard:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
            }}
        """
        self.setStyleSheet(style)
        
        # Add modern shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(15)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(2)
        shadow_effect.setColor(QColor(0, 0, 0, 40))
        self.card_frame.setGraphicsEffect(shadow_effect)
    
    def update_content(self, data: Dict, animate: bool = True):
        """Update card content with optional animation. Override in subclasses."""
        logger.debug(f"Updating card content: {data}")
    
    def update_value_display(self, value: float):
        """Update value display during animation. Override in subclasses."""
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press events for card clicks."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.card_id)
        super().mousePressEvent(event)


class SimpleMetricCard(SummaryCard):
    """Card displaying a single metric with trend indicator."""
    
    def __init__(self, size: str = 'medium', card_id: str = ""):
        super().__init__('simple', size, card_id)
        
    def setup_ui(self):
        """Setup simple metric card layout."""
        super().setup_ui()
        
        config = self.SIZE_CONFIGS[self.size]
        
        # Metric name (top)
        self.title_label = QLabel("Metric")
        self.title_label.setObjectName("cardTitle")
        title_font = QFont()
        title_font.setPointSize(config['title_font'])
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Main value (center, large)
        self.value_label = QLabel("0")
        self.value_label.setObjectName("cardValue")
        value_font = QFont()
        value_font.setPointSize(config['value_font'])
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Trend indicator (bottom)
        self.trend_widget = TrendIndicatorWidget()
        
        # Subtitle (optional)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("cardSubtitle")
        subtitle_font = QFont()
        subtitle_font.setPointSize(max(10, config['title_font'] - 2))
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Layout
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.value_label, 1, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.trend_widget)
        self.content_layout.addWidget(self.subtitle_label)
        
        # Apply text colors
        self._apply_text_styles()
    
    def _apply_text_styles(self):
        """Apply text styling to labels."""
        self.title_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        self.value_label.setStyleSheet(f"color: {self.style_manager.ACCENT_PRIMARY};")
        self.subtitle_label.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
    
    def update_content(self, data: Dict, animate: bool = True):
        """Update card content with optional animation."""
        super().update_content(data, animate)
        
        # Update text content immediately
        if 'title' in data:
            self.title_label.setText(str(data['title']))
        if 'subtitle' in data:
            self.subtitle_label.setText(str(data['subtitle']))
        
        # Update trend
        if 'current_value' in data and 'previous_value' in data:
            self.trend_widget.set_trend(data['current_value'], data['previous_value'])
        
        # Animate main value
        if 'value' in data and animate:
            # parse current value
            try:
                current_value = float(self.value_label.text().replace(',', ''))
            except ValueError:
                current_value = 0.0

            # parse target value
            value_str = data['value']
            try:
                target_value = float(value_str)
            except (ValueError, TypeError):
                # non‐numeric: just display and skip animation
                self.value_label.setText(value_str)
                return
            
            self.value_animator.setStartValue(current_value)
            self.value_animator.setEndValue(target_value)
            self.value_animator.setDuration(500)
            self.value_animator.start()
        elif 'value' in data:
            try:
                current_value = float(data['value'])
                self.update_value_display(current_value)
            except (ValueError, TypeError):
                self.value_label.setText(f"{data['value']}")
    
    def update_value_display(self, value: float):
        """Update value display during animation."""
        if 'unit' in self.__dict__:
            self.value_label.setText(f"{value:,.1f} {self.unit}")
        else:
            self.value_label.setText(f"{value:,.1f}")


class ComparisonCard(SummaryCard):
    """Card displaying current vs previous value comparison."""
    
    def __init__(self, size: str = 'medium', card_id: str = ""):
        super().__init__('comparison', size, card_id)
    
    def setup_ui(self):
        """Setup comparison card with current vs previous."""
        super().setup_ui()
        
        config = self.SIZE_CONFIGS[self.size]
        grid = QGridLayout(self.card_frame)
        self.content_layout = grid
        
        # Title
        self.title_label = QLabel("Comparison")
        title_font = QFont()
        title_font.setPointSize(config['title_font'])
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.title_label, 0, 0, 1, 2)
        
        # Current value
        self.current_label = QLabel("Current")
        self.current_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        self.current_value = QLabel("0")
        current_font = QFont()
        current_font.setPointSize(config['value_font'] - 8)
        current_font.setBold(True)
        self.current_value.setFont(current_font)
        self.current_value.setStyleSheet(f"color: {self.style_manager.ACCENT_PRIMARY};")
        
        # Previous value
        self.previous_label = QLabel("Previous")
        self.previous_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        self.previous_value = QLabel("0")
        previous_font = QFont()
        previous_font.setPointSize(config['value_font'] - 8)
        self.previous_value.setFont(previous_font)
        self.previous_value.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
        
        # Change indicator
        self.change_widget = ChangeIndicatorWidget()
        
        # Layout in grid
        grid.addWidget(self.current_label, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.current_value, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.previous_label, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.previous_value, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.change_widget, 3, 0, 1, 2)
    
    def update_content(self, data: Dict, animate: bool = True):
        """Update comparison card content."""
        super().update_content(data, animate)
        
        if 'title' in data:
            self.title_label.setText(str(data['title']))
        if 'current_value' in data:
            self.current_value.setText(f"{data['current_value']:,.1f}")
        if 'previous_value' in data:
            self.previous_value.setText(f"{data['previous_value']:,.1f}")
        if 'current_value' in data and 'previous_value' in data:
            self.change_widget.set_change(data['current_value'], data['previous_value'])


class GoalProgressCard(SummaryCard):
    """Card displaying progress toward a goal."""
    
    def __init__(self, size: str = 'medium', card_id: str = ""):
        super().__init__('goal_progress', size, card_id)
    
    def setup_ui(self):
        """Setup goal progress card with progress bar."""
        super().setup_ui()
        
        config = self.SIZE_CONFIGS[self.size]
        
        # Title
        self.title_label = QLabel("Goal Progress")
        title_font = QFont('Roboto Condensed')
        title_font.setPointSize(config['title_font'])
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        
        # Current vs target
        self.progress_label = QLabel("0 / 0")
        progress_font = QFont('Roboto')
        progress_font.setPointSize(config['value_font'] - 6)
        progress_font.setBold(True)
        self.progress_label.setFont(progress_font)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_PRIMARY};")
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                background-color: {self.style_manager.TERTIARY_BG};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {self.style_manager.ACCENT_SUCCESS};
                border-radius: 7px;
            }}
        """)
        
        # Completion percentage
        self.percentage_label = QLabel("0%")
        percentage_font = QFont('Roboto')
        percentage_font.setPointSize(config['title_font'])
        percentage_font.setBold(True)
        self.percentage_label.setFont(percentage_font)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
        
        # Layout
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.progress_label)
        self.content_layout.addWidget(self.progress_bar)
        self.content_layout.addWidget(self.percentage_label)
    
    def update_content(self, data: Dict, animate: bool = True):
        """Update goal progress card content."""
        super().update_content(data, animate)
        
        if 'title' in data:
            self.title_label.setText(str(data['title']))
        
        current = data.get('current_value', 0)
        target = data.get('target_value', 1)
        
        self.progress_label.setText(f"{current:,.1f} / {target:,.1f}")
        
        # Calculate percentage
        percentage = min(100, (current / target * 100) if target > 0 else 0)
        
        if animate:
            # Animate progress bar
            self.value_animator.setStartValue(self.progress_bar.value())
            self.value_animator.setEndValue(percentage)
            self.value_animator.setDuration(800)
            self.value_animator.valueChanged.connect(self._update_progress)
            self.value_animator.start()
        else:
            self._update_progress(percentage)
    
    def _update_progress(self, value):
        """Update progress bar and percentage during animation."""
        self.progress_bar.setValue(int(value))
        self.percentage_label.setText(f"{value:.1f}%")


class TrendIndicatorWidget(QWidget):
    """Widget displaying trend indicators with arrows and percentages."""
    
    def __init__(self):
        super().__init__()
        self.trend_value = 0
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup trend indicator UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("→ 0.0%")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont('Roboto')
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setMaximumHeight(30)
    
    def set_trend(self, current: float, previous: float):
        """Set trend based on values."""
        if previous == 0:
            self.trend_value = 0
        else:
            self.trend_value = ((current - previous) / previous) * 100
            
        self.update_display()
        
    def update_display(self):
        """Update visual display of trend."""
        # Arrow direction and color
        if self.trend_value > 5:  # Significant increase
            arrow = "↗"
            color = self.style_manager.ACCENT_SUCCESS
        elif self.trend_value > 0:  # Small increase
            arrow = "↑"
            color = self.style_manager.ACCENT_SUCCESS
        elif self.trend_value < -5:  # Significant decrease
            arrow = "↘"
            color = self.style_manager.ACCENT_ERROR
        elif self.trend_value < 0:  # Small decrease
            arrow = "↓"
            color = self.style_manager.ACCENT_ERROR
        else:  # No change
            arrow = "→"
            color = self.style_manager.TEXT_MUTED
            
        # Update label
        self.label.setText(f"{arrow} {abs(self.trend_value):.1f}%")
        self.label.setStyleSheet(f"color: {color};")


class ChangeIndicatorWidget(QWidget):
    """Widget displaying change between two values."""
    
    def __init__(self):
        super().__init__()
        self.style_manager = StyleManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup change indicator UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.change_label = QLabel("No change")
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont('Roboto Condensed')
        font.setPointSize(14)
        font.setBold(True)
        self.change_label.setFont(font)
        
        self.percentage_label = QLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        percentage_font = QFont('Roboto')
        percentage_font.setPointSize(12)
        self.percentage_label.setFont(percentage_font)
        
        layout.addWidget(self.change_label)
        layout.addWidget(self.percentage_label)
        self.setLayout(layout)
    
    def set_change(self, current: float, previous: float):
        """Set change values and update display."""
        change = current - previous
        
        if previous == 0:
            percentage = 0
        else:
            percentage = (change / previous) * 100
        
        # Update change label
        if change > 0:
            self.change_label.setText(f"+{change:.1f}")
            color = self.style_manager.ACCENT_SUCCESS
        elif change < 0:
            self.change_label.setText(f"{change:.1f}")
            color = self.style_manager.ACCENT_ERROR
        else:
            self.change_label.setText("No change")
            color = self.style_manager.TEXT_MUTED
        
        # Update percentage
        self.percentage_label.setText(f"({percentage:+.1f}%)")
        
        # Apply colors
        self.change_label.setStyleSheet(f"color: {color};")
        self.percentage_label.setStyleSheet(f"color: {color};")


class MiniChartCard(SummaryCard):
    """Card with a small chart and current value."""
    
    def __init__(self, size: str = 'medium', card_id: str = ""):
        super().__init__('mini_chart', size, card_id)
    
    def setup_ui(self):
        """Setup mini chart card layout."""
        super().setup_ui()
        
        config = self.SIZE_CONFIGS[self.size]
        
        # Title
        self.title_label = QLabel("Mini Chart")
        title_font = QFont()
        title_font.setPointSize(config['title_font'])
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        
        # Current value
        self.value_label = QLabel("0")
        value_font = QFont()
        value_font.setPointSize(config['value_font'] - 6)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"color: {self.style_manager.ACCENT_PRIMARY};")
        
        # Placeholder for chart (would integrate with actual chart components)
        self.chart_placeholder = QLabel("📊 Chart Area")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_placeholder.setStyleSheet(f"""
            background-color: {self.style_manager.TERTIARY_BG};
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 4px;
            padding: 20px;
            color: {self.style_manager.TEXT_MUTED};
        """)
        
        # Subtitle
        self.subtitle_label = QLabel("")
        subtitle_font = QFont()
        subtitle_font.setPointSize(max(10, config['title_font'] - 2))
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
        
        # Mini chart (will be replaced with actual chart widget)
        self.mini_chart = QWidget(self)
        self.mini_chart.setFixedHeight(50)
        # Add stub set_data method
        self.mini_chart.set_data = lambda data: None
        
        # Min/max indicators
        indicator_layout = QHBoxLayout()
        self.min_label = QLabel("Min: 0")
        self.max_label = QLabel("Max: 0")
        self.min_label.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
        self.max_label.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
        
        indicator_layout.addWidget(self.min_label)
        indicator_layout.addStretch()
        indicator_layout.addWidget(self.max_label)
        
        # Layout
        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.value_label)
        self.content_layout.addWidget(self.subtitle_label)
        self.content_layout.addWidget(self.chart_placeholder, 1)
        self.content_layout.addLayout(indicator_layout)
    
    def update_content(self, data: Dict, animate: bool = True):
        """Update mini chart card content."""
        super().update_content(data, animate)
        
        if 'title' in data:
            self.title_label.setText(str(data['title']))
        if 'value' in data:
            self.value_label.setText(f"{data['value']:,.1f}")
        if 'min_value' in data:
            self.min_label.setText(f"Min: {data['min_value']:,.1f}")
        if 'max_value' in data:
            self.max_label.setText(f"Max: {data['max_value']:,.1f}")