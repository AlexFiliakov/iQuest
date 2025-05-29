"""
Modern weekly dashboard widget with updated UI design.

Features the modern Wall Street Journal-inspired aesthetic with:
- Borderless cards with shadow effects
- Vibrant color palette
- Improved spacing and typography
- Modern navigation controls
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QGroupBox, QButtonGroup, QRadioButton,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from .summary_cards import SummaryCard
from .week_over_week_widget import WeekOverWeekWidget
from .charts.line_chart import LineChart
from .bar_chart_component import BarChart as BarChartComponent
from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator, WeeklyMetrics, TrendInfo
from ..analytics.day_of_week_analyzer import DayOfWeekAnalyzer
from ..analytics.week_over_week_trends import WeekOverWeekTrends
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ModernWeeklyStatCard(QFrame):
    """Modern statistical card for weekly metrics."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the modern card UI."""
        self.setFixedHeight(120)
        from .style_manager import StyleManager
        style_manager = StyleManager()
        
        # Modern card style without borders
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style_manager.PRIMARY_BG};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(QFont('Segoe UI Emoji', 16))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont('Inter', 12, QFont.Weight.Medium))
        title_label.setStyleSheet(f"color: {style_manager.TEXT_SECONDARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Main value with larger font
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont('Inter', 24, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {style_manager.ACCENT_PRIMARY};")
        layout.addWidget(self.value_label)
        
        # Sub-label
        self.sub_label = QLabel("")
        self.sub_label.setFont(QFont('Inter', 11))
        self.sub_label.setStyleSheet(f"color: {style_manager.TEXT_MUTED};")
        layout.addWidget(self.sub_label)
        
    def update_value(self, value: str, sub_label: str = "", trend_color: str = None):
        """Update the displayed values with optional trend coloring."""
        self.value_label.setText(value)
        self.sub_label.setText(sub_label)
        
        if trend_color:
            self.value_label.setStyleSheet(f"color: {trend_color};")


class ModernWeeklyDashboardWidget(QWidget):
    """
    Modern weekly dashboard widget with updated UI design.
    
    Features:
    - Week-at-a-glance summary with modern cards
    - Smooth navigation between weeks
    - Interactive charts with modern styling
    - Week-over-week comparisons
    - Day-of-week patterns
    """
    
    # Signals
    week_changed = pyqtSignal(date, date)  # start_date, end_date
    metric_selected = pyqtSignal(str)
    
    def __init__(self, weekly_calculator=None, daily_calculator=None, parent=None):
        """Initialize the modern weekly dashboard widget."""
        super().__init__(parent)
        
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(
            daily_calculator.data if hasattr(daily_calculator, 'data') else daily_calculator
        ) if daily_calculator else None
        
        # Calculate current week boundaries
        today = date.today()
        self._current_week_start = today - timedelta(days=today.weekday())  # Monday
        self._current_week_end = self._current_week_start + timedelta(days=6)  # Sunday
        
        self._available_metrics = []
        self._selected_metric = "steps"
        
        # Get style manager
        from .style_manager import StyleManager
        self.style_manager = StyleManager()
        
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        if self.weekly_calculator:
            self._detect_available_metrics()
            self._load_weekly_data()
    
    def _setup_ui(self):
        """Set up the modern user interface."""
        # Main layout with modern spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(16)
        
        # Set background color
        self.setStyleSheet(f"background-color: {self.style_manager.SECONDARY_BG};")
        
        # Header section
        header = self._create_modern_header()
        main_layout.addWidget(header)
        
        # Content area with scroll
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {self.style_manager.TERTIARY_BG};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #1D4ED8;
            }}
        """)
        
        # Content widget
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Weekly summary section
        summary_section = self._create_modern_summary_section()
        content_layout.addWidget(summary_section)
        
        # Week-over-week comparison
        wow_section = self._create_modern_wow_section()
        content_layout.addWidget(wow_section)
        
        # Day patterns section
        patterns_section = self._create_modern_patterns_section()
        content_layout.addWidget(patterns_section)
        
        # Detailed charts section
        charts_section = self._create_modern_charts_section()
        content_layout.addWidget(charts_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_modern_header(self) -> QWidget:
        """Create the modern dashboard header with week navigation."""
        header = QFrame(self)
        header.setStyleSheet(self.style_manager.get_modern_card_style(padding=16))
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        header.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(20)
        
        # Week navigation
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        # Previous week button
        self.prev_week_btn = QPushButton("◀")
        self.prev_week_btn.setFixedSize(40, 40)
        self.prev_week_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: none;
                border-radius: 20px;
                color: {self.style_manager.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        self.prev_week_btn.setToolTip("Previous week")
        self.prev_week_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(self.prev_week_btn)
        
        # Week label
        week_layout = QVBoxLayout()
        week_layout.setSpacing(4)
        
        self.week_label = QLabel()
        self.week_label.setFont(QFont('Inter', 20, QFont.Weight.Bold))
        self.week_label.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.week_label)
        
        self.date_range_label = QLabel()
        self.date_range_label.setFont(QFont('Inter', 13))
        self.date_range_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        self.date_range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.date_range_label)
        
        nav_layout.addLayout(week_layout)
        
        # Next week button
        self.next_week_btn = QPushButton("▶")
        self.next_week_btn.setFixedSize(40, 40)
        self.next_week_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: none;
                border-radius: 20px;
                color: {self.style_manager.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        self.next_week_btn.setToolTip("Next week")
        self.next_week_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_layout.addWidget(self.next_week_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # This week button
        self.this_week_btn = QPushButton("This Week")
        self.this_week_btn.setFixedSize(100, 40)
        self.this_week_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                color: white;
                border: none;
                border-radius: 20px;
                font-family: Inter;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
            QPushButton:pressed {{
                background-color: #1E40AF;
            }}
            QPushButton:disabled {{
                background-color: {self.style_manager.TEXT_MUTED};
            }}
        """)
        self.this_week_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.this_week_btn)
        
        self._update_week_labels()
        
        return header
    
    def _create_modern_summary_section(self) -> QWidget:
        """Create the modern weekly summary section."""
        section = QFrame()
        section.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Week at a Glance")
        title.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Metric selector card
        selector_card = QFrame()
        selector_card.setStyleSheet(self.style_manager.get_modern_card_style(padding=16))
        selector_card.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        selector_layout = QHBoxLayout(selector_card)
        
        metric_label = QLabel("Metric:")
        metric_label.setFont(QFont('Inter', 13, QFont.Weight.Medium))
        metric_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        selector_layout.addWidget(metric_label)
        
        self.metric_selector = QComboBox()
        self.metric_selector.setMinimumWidth(200)
        self.metric_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Inter;
                font-size: 13px;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.style_manager.TEXT_SECONDARY};
                margin-right: 8px;
            }}
        """)
        selector_layout.addWidget(self.metric_selector)
        
        selector_layout.addStretch()
        layout.addWidget(selector_card)
        
        # Statistics cards grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        
        # Create modern stat cards
        self.stat_cards = {
            'average': ModernWeeklyStatCard("Weekly Average", "📊"),
            'total': ModernWeeklyStatCard("Weekly Total", "Σ"),
            'best': ModernWeeklyStatCard("Best Day", "🏆"),
            'worst': ModernWeeklyStatCard("Worst Day", "📉"),
            'trend': ModernWeeklyStatCard("Trend", "📈"),
            'volatility': ModernWeeklyStatCard("Volatility", "📊")
        }
        
        # Arrange cards in grid (2x3)
        positions = [
            ('average', 0, 0), ('total', 0, 1), ('best', 0, 2),
            ('worst', 1, 0), ('trend', 1, 1), ('volatility', 1, 2)
        ]
        
        for key, row, col in positions:
            stats_grid.addWidget(self.stat_cards[key], row, col)
        
        layout.addLayout(stats_grid)
        
        return section
    
    def _create_modern_wow_section(self) -> QWidget:
        """Create the modern week-over-week comparison section."""
        section = QFrame()
        section.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Week-over-Week Comparison")
        title.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # WoW card
        wow_card = QFrame()
        wow_card.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        wow_card.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        wow_layout = QVBoxLayout(wow_card)
        
        # WoW widget
        self.wow_widget = WeekOverWeekWidget()
        self.wow_widget.setMinimumHeight(300)
        wow_layout.addWidget(self.wow_widget)
        
        layout.addWidget(wow_card)
        
        return section
    
    def _create_modern_patterns_section(self) -> QWidget:
        """Create the modern day-of-week patterns section."""
        section = QFrame()
        section.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Weekly Patterns")
        title.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Patterns card
        patterns_card = QFrame()
        patterns_card.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        patterns_card.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        patterns_layout = QVBoxLayout(patterns_card)
        patterns_layout.setSpacing(16)
        
        # Day-of-week chart
        self.dow_chart = BarChartComponent()
        self.dow_chart.setMinimumHeight(250)
        patterns_layout.addWidget(self.dow_chart)
        
        # Pattern insights
        self.pattern_label = QLabel("Loading patterns...")
        self.pattern_label.setFont(QFont('Inter', 12))
        self.pattern_label.setStyleSheet(f"""
            color: {self.style_manager.TEXT_SECONDARY};
            padding: 12px;
            background-color: {self.style_manager.TERTIARY_BG};
            border-radius: 8px;
        """)
        self.pattern_label.setWordWrap(True)
        patterns_layout.addWidget(self.pattern_label)
        
        layout.addWidget(patterns_card)
        
        return section
    
    def _create_modern_charts_section(self) -> QWidget:
        """Create the modern detailed charts section."""
        section = QFrame()
        section.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Weekly Trend")
        title.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Chart card
        chart_card = QFrame()
        chart_card.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        chart_card.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setSpacing(16)
        
        # View options
        view_layout = QHBoxLayout()
        view_layout.setSpacing(16)
        
        view_label = QLabel("View:")
        view_label.setFont(QFont('Inter', 13, QFont.Weight.Medium))
        view_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        view_layout.addWidget(view_label)
        
        # Radio buttons for view selection
        self.view_group = QButtonGroup(self)
        
        radio_style = f"""
            QRadioButton {{
                color: {self.style_manager.TEXT_PRIMARY};
                font-family: Inter;
                font-size: 13px;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {self.style_manager.ACCENT_LIGHT};
                background-color: {self.style_manager.PRIMARY_BG};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QRadioButton::indicator:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
        """
        
        self.daily_view_rb = QRadioButton("Daily Values")
        self.daily_view_rb.setChecked(True)
        self.daily_view_rb.setStyleSheet(radio_style)
        self.view_group.addButton(self.daily_view_rb, 0)
        view_layout.addWidget(self.daily_view_rb)
        
        self.cumulative_view_rb = QRadioButton("Cumulative")
        self.cumulative_view_rb.setStyleSheet(radio_style)
        self.view_group.addButton(self.cumulative_view_rb, 1)
        view_layout.addWidget(self.cumulative_view_rb)
        
        self.rolling_view_rb = QRadioButton("7-Day Average")
        self.rolling_view_rb.setStyleSheet(radio_style)
        self.view_group.addButton(self.rolling_view_rb, 2)
        view_layout.addWidget(self.rolling_view_rb)
        
        view_layout.addStretch()
        chart_layout.addLayout(view_layout)
        
        # Trend chart
        self.trend_chart = LineChart()
        self.trend_chart.setMinimumHeight(300)
        
        # Configure chart with modern styling
        self.trend_chart.set_labels(title="", x_label="Date", y_label="Value")
        self.trend_chart.show_grid = True
        
        chart_layout.addWidget(self.trend_chart)
        
        layout.addWidget(chart_card)
        
        return section
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.prev_week_btn.clicked.connect(self._go_to_previous_week)
        self.next_week_btn.clicked.connect(self._go_to_next_week)
        self.this_week_btn.clicked.connect(self._go_to_current_week)
        
        self.metric_selector.currentTextChanged.connect(self._on_metric_changed)
        self.view_group.buttonClicked.connect(self._update_trend_chart)
    
    def _detect_available_metrics(self):
        """Detect available metrics from the data."""
        if not self.weekly_calculator or not self.weekly_calculator.daily_calculator:
            return
            
        try:
            # Get unique metric types
            data = self.weekly_calculator.daily_calculator.data
            available_types = data['type'].unique()
            
            # Map to display names
            metric_mapping = {
                'HKQuantityTypeIdentifierStepCount': ('Steps', 'steps'),
                'HKQuantityTypeIdentifierDistanceWalkingRunning': ('Distance (km)', 'distance'),
                'HKQuantityTypeIdentifierFlightsClimbed': ('Floors Climbed', 'flights'),
                'HKQuantityTypeIdentifierActiveEnergyBurned': ('Active Calories', 'calories'),
                'HKQuantityTypeIdentifierHeartRate': ('Heart Rate', 'heart_rate'),
                'HKQuantityTypeIdentifierRestingHeartRate': ('Resting HR', 'resting_hr'),
                'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': ('HRV', 'hrv'),
                'HKQuantityTypeIdentifierBodyMass': ('Weight', 'weight')
            }
            
            self._available_metrics = []
            self.metric_selector.clear()
            
            for hk_type, (display_name, metric_key) in metric_mapping.items():
                if hk_type in available_types:
                    self._available_metrics.append((hk_type, metric_key))
                    self.metric_selector.addItem(display_name, hk_type)
            
            if self._available_metrics:
                self._selected_metric = self._available_metrics[0][0]
                
        except Exception as e:
            logger.error(f"Error detecting available metrics: {e}")
    
    def _update_week_labels(self):
        """Update the week display labels."""
        # Calculate week number
        week_num = self._current_week_start.isocalendar()[1]
        year = self._current_week_start.year
        
        # Check if this is the current week
        today = date.today()
        is_current_week = (self._current_week_start <= today <= self._current_week_end)
        
        # Update labels
        if is_current_week:
            self.week_label.setText("This Week")
        else:
            self.week_label.setText(f"Week {week_num}, {year}")
        
        # Format date range
        if self._current_week_start.month == self._current_week_end.month:
            date_range = f"{self._current_week_start.strftime('%b %d')} - {self._current_week_end.strftime('%d, %Y')}"
        else:
            date_range = f"{self._current_week_start.strftime('%b %d')} - {self._current_week_end.strftime('%b %d, %Y')}"
        
        self.date_range_label.setText(date_range)
        
        # Update button states
        self.this_week_btn.setEnabled(not is_current_week)
    
    def _load_weekly_data(self):
        """Load data for the current week."""
        if not self.weekly_calculator:
            self._show_no_data_message()
            return
            
        try:
            # Get selected metric
            metric_type = self.metric_selector.currentData()
            if not metric_type:
                return
            
            # Calculate weekly statistics
            self._update_summary_stats(metric_type)
            
            # Update week-over-week comparison
            self._update_wow_comparison(metric_type)
            
            # Update day-of-week patterns
            self._update_dow_patterns(metric_type)
            
            # Update trend chart
            self._update_trend_chart()
            
        except Exception as e:
            logger.error(f"Error loading weekly data: {e}")
    
    def _update_summary_stats(self, metric_type: str):
        """Update the summary statistics cards."""
        try:
            # Get weekly data
            weekly_data = self.weekly_calculator.get_weekly_metrics(
                metric=metric_type,
                week_start=self._current_week_start
            )
            
            if not weekly_data:
                return
            
            # Hide no data message if showing
            self._hide_no_data_message()
            
            # Update average
            avg_value = weekly_data.avg
            self.stat_cards['average'].update_value(
                f"{avg_value:,.0f}" if avg_value >= 100 else f"{avg_value:.1f}",
                "daily average"
            )
            
            # Update total
            total = sum(weekly_data.daily_values.values())
            self.stat_cards['total'].update_value(
                f"{total:,.0f}" if total >= 100 else f"{total:.1f}",
                "weekly total"
            )
            
            # Update best/worst days
            if weekly_data.daily_values:
                best_date = max(weekly_data.daily_values, key=weekly_data.daily_values.get)
                worst_date = min(weekly_data.daily_values, key=weekly_data.daily_values.get)
                
                self.stat_cards['best'].update_value(
                    f"{weekly_data.daily_values[best_date]:,.0f}",
                    best_date.strftime("%A"),
                    self.style_manager.ACCENT_SUCCESS
                )
                
                self.stat_cards['worst'].update_value(
                    f"{weekly_data.daily_values[worst_date]:,.0f}",
                    worst_date.strftime("%A"),
                    self.style_manager.ACCENT_WARNING
                )
            
            # Update trend with color coding
            trend_symbol = "↑" if weekly_data.trend_direction == "up" else "↓" if weekly_data.trend_direction == "down" else "→"
            trend_color = (
                self.style_manager.ACCENT_SUCCESS if weekly_data.trend_direction == "up" 
                else self.style_manager.ACCENT_ERROR if weekly_data.trend_direction == "down"
                else self.style_manager.TEXT_SECONDARY
            )
            self.stat_cards['trend'].update_value(
                trend_symbol,
                weekly_data.trend_direction,
                trend_color
            )
            
            # Calculate volatility
            if weekly_data.daily_values:
                values = list(weekly_data.daily_values.values())
                if len(values) > 1:
                    volatility = np.std(values) / np.mean(values) * 100 if np.mean(values) > 0 else 0
                    volatility_color = (
                        self.style_manager.ACCENT_SUCCESS if volatility < 20
                        else self.style_manager.ACCENT_WARNING if volatility < 40
                        else self.style_manager.ACCENT_ERROR
                    )
                    self.stat_cards['volatility'].update_value(
                        f"{volatility:.1f}%",
                        "coefficient of variation",
                        volatility_color
                    )
                    
        except Exception as e:
            logger.error(f"Error updating summary stats: {e}")
    
    def _update_wow_comparison(self, metric_type: str):
        """Update week-over-week comparison."""
        if not self.wow_analyzer:
            return
            
        try:
            # Get WoW data
            # TODO: Fix when get_week_over_week_comparison is available
            comparison = None  # self.wow_analyzer.get_week_over_week_comparison(...)
            
            if False:  # Disabled until WoW analysis is fixed
                # Update WoW widget
                self.wow_widget.set_comparison_data(comparison)
                
        except Exception as e:
            logger.error(f"Error updating WoW comparison: {e}")
    
    def _update_dow_patterns(self, metric_type: str):
        """Update day-of-week patterns."""
        if not self.dow_analyzer:
            return
            
        try:
            # Get day-of-week pattern
            # TODO: Fix when analyze_day_patterns is available
            pattern = None  # self.dow_analyzer.analyze_day_patterns(...)
            
            if False:  # Disabled until pattern analysis is fixed
                # Update bar chart
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                values = [pattern.average_by_day.get(i, 0) for i in range(7)]
                
                # Prepare data for bar chart
                import pandas as pd
                df = pd.DataFrame({
                    'Day': days,
                    'Value': values
                })
                # Use modern colors - weekdays vs weekends
                df['Color'] = [
                    self.style_manager.ACCENT_SECONDARY if i < 5 
                    else self.style_manager.ACCENT_WARNING 
                    for i in range(7)
                ]
                
                self.dow_chart.plot(df, chart_type='simple', x='Day', y='Value', color_column='Color')
                
                # Update pattern insights
                insights = self._generate_pattern_insights(pattern)
                self.pattern_label.setText(insights)
                
        except Exception as e:
            logger.error(f"Error updating DoW patterns: {e}")
    
    def _generate_pattern_insights(self, pattern: Any) -> str:
        """Generate insights from day-of-week patterns."""
        insights = []
        
        # Best/worst days
        if pattern.best_day is not None and pattern.worst_day is not None:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            insights.append(f"Best day: {days[pattern.best_day]} | Worst day: {days[pattern.worst_day]}")
        
        # Weekend vs weekday
        if pattern.weekend_avg is not None and pattern.weekday_avg is not None:
            diff = ((pattern.weekend_avg - pattern.weekday_avg) / pattern.weekday_avg * 100) if pattern.weekday_avg > 0 else 0
            if abs(diff) > 10:
                comparison = "higher" if diff > 0 else "lower"
                insights.append(f"Weekend average is {abs(diff):.0f}% {comparison} than weekdays")
        
        # Consistency
        if pattern.consistency_score is not None:
            if pattern.consistency_score > 0.8:
                insights.append("Very consistent throughout the week")
            elif pattern.consistency_score < 0.5:
                insights.append("High variability between days")
        
        return " • ".join(insights) if insights else "Analyzing patterns..."
    
    def _update_trend_chart(self):
        """Update the trend chart based on selected view."""
        if not self.weekly_calculator:
            return
            
        try:
            metric_type = self.metric_selector.currentData()
            if not metric_type:
                return
            
            # Get daily data for the week
            start_date = self._current_week_start
            end_date = self._current_week_end
            
            # Get data based on view selection
            view_id = self.view_group.checkedId()
            
            if view_id == 0:  # Daily values
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    x_data = [d.strftime("%a") for d in data.index]
                    y_data = data.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = min(y_data) * 0.9
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
            elif view_id == 1:  # Cumulative
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not data.empty:
                    cumulative = data.cumsum()
                    x_data = [d.strftime("%a") for d in cumulative.index]
                    y_data = cumulative.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = 0  # Cumulative starts at 0
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
            elif view_id == 2:  # 7-day rolling average
                # Get extended data for rolling average
                extended_start = start_date - timedelta(days=6)
                data = self.weekly_calculator.daily_calculator.calculate_daily_aggregates(
                    metric=metric_type,
                    start_date=extended_start,
                    end_date=end_date
                )
                
                if not data.empty:
                    rolling = data.rolling(window=7, min_periods=1).mean()
                    # Filter to current week
                    rolling = rolling[rolling.index >= pd.to_datetime(start_date)]
                    
                    x_data = [d.strftime("%a") for d in rolling.index]
                    y_data = rolling.values.tolist()
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data:
                        y_min = min(y_data) * 0.9
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                    
        except Exception as e:
            logger.error(f"Error updating trend chart: {e}")
    
    def _show_no_data_message(self):
        """Show message when no data is loaded."""
        # Create or update no data overlay
        if not hasattr(self, 'no_data_overlay'):
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PyQt6.QtCore import Qt
            
            self.no_data_overlay = QWidget(self)
            self.no_data_overlay.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba(255, 255, 255, 0.98);
                    border-radius: 16px;
                    margin: 20px;
                }}
            """)
            
            overlay_layout = QVBoxLayout(self.no_data_overlay)
            overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📅")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 72px;")
            overlay_layout.addWidget(icon_label)
            
            # Message
            message_label = QLabel("No Data Loaded")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet(f"""
                font-family: Inter;
                font-size: 28px;
                font-weight: 700;
                color: {self.style_manager.TEXT_PRIMARY};
                margin: 20px 0;
            """)
            overlay_layout.addWidget(message_label)
            
            # Instructions
            instructions = QLabel("Please go to the Configuration tab and import your Apple Health data.")
            instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
            instructions.setWordWrap(True)
            instructions.setStyleSheet(f"""
                font-family: Inter;
                font-size: 16px;
                color: {self.style_manager.TEXT_SECONDARY};
                max-width: 400px;
            """)
            overlay_layout.addWidget(instructions)
        
        # Position and show overlay
        self._position_overlay()
        self.no_data_overlay.show()
        self.no_data_overlay.raise_()
    
    def _hide_no_data_message(self):
        """Hide the no data message overlay."""
        if hasattr(self, 'no_data_overlay'):
            self.no_data_overlay.hide()
    
    def _position_overlay(self):
        """Position the overlay to cover the content area."""
        if hasattr(self, 'no_data_overlay'):
            # Cover the entire widget
            self.no_data_overlay.setGeometry(
                0, 0,
                self.width(),
                self.height()
            )
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        # Reposition overlay if visible
        if hasattr(self, 'no_data_overlay') and self.no_data_overlay.isVisible():
            self._position_overlay()
    
    def _go_to_previous_week(self):
        """Navigate to the previous week."""
        self._current_week_start -= timedelta(weeks=1)
        self._current_week_end -= timedelta(weeks=1)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _go_to_next_week(self):
        """Navigate to the next week."""
        self._current_week_start += timedelta(weeks=1)
        self._current_week_end += timedelta(weeks=1)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _go_to_current_week(self):
        """Navigate to the current week."""
        today = date.today()
        self._current_week_start = today - timedelta(days=today.weekday())
        self._current_week_end = self._current_week_start + timedelta(days=6)
        self._update_week_labels()
        self._load_weekly_data()
        self.week_changed.emit(self._current_week_start, self._current_week_end)
    
    def _on_metric_changed(self):
        """Handle metric selection change."""
        self._load_weekly_data()
        metric_key = self.metric_selector.currentData()
        if metric_key:
            self.metric_selected.emit(metric_key)
    
    def set_calculators(self, weekly_calculator: WeeklyMetricsCalculator, 
                       daily_calculator=None):
        """Set the calculator instances."""
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator or (
            weekly_calculator.daily_calculator if weekly_calculator else None
        )
        
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(
            self.daily_calculator.data if hasattr(self.daily_calculator, 'data') else self.daily_calculator
        ) if self.daily_calculator else None
        
        self._detect_available_metrics()
        self._load_weekly_data()
    
    def get_current_week(self) -> Tuple[date, date]:
        """Get the current week's start and end dates."""
        return self._current_week_start, self._current_week_end
    
    def set_weekly_calculator(self, weekly_calculator: WeeklyMetricsCalculator):
        """Set the weekly metrics calculator."""
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = weekly_calculator.daily_calculator if weekly_calculator else None
        
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(
            self.daily_calculator.data if hasattr(self.daily_calculator, 'data') else self.daily_calculator
        ) if self.daily_calculator else None
        
        self._detect_available_metrics()
        self._hide_no_data_message()  # Hide no data message when calculator is set
        self._load_weekly_data()
        
        # Force UI refresh
        self.update()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def showEvent(self, event):
        """Handle widget show event to ensure UI is refreshed."""
        super().showEvent(event)
        # Force a refresh when the widget is shown
        if self.weekly_calculator:
            self._load_weekly_data()
            self.update()
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()