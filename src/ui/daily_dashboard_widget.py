"""
Daily dashboard widget for viewing today's health metrics.

This widget provides a comprehensive view of daily health data including:
- Real-time metric updates
- Daily summaries and statistics
- Comparison with weekly/monthly averages
- Activity timeline
- Personal records tracking
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QGroupBox, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from .summary_cards import SummaryCard
from .daily_trend_indicator import DailyTrendIndicator
from .activity_timeline_component import ActivityTimelineComponent
from .charts.line_chart import LineChart
from ..analytics.daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics
from ..analytics.personal_records_tracker import PersonalRecordsTracker
from ..analytics.day_of_week_analyzer import DayOfWeekAnalyzer
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MetricCard(QFrame):
    """Individual metric display card with trend indicator."""
    
    clicked = pyqtSignal(str)  # Emits metric name when clicked
    
    def __init__(self, metric_name: str, display_name: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.metric_name = metric_name
        self.display_name = display_name
        self.unit = unit
        
        self._setup_ui()
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def _setup_ui(self):
        """Set up the card UI."""
        self.setFixedHeight(120)
        from .style_manager import StyleManager
        style_manager = StyleManager()
        shadow = style_manager.get_shadow_style('md')
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style_manager.PRIMARY_BG};
                border: none;
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                background-color: {style_manager.TERTIARY_BG};
            }}
        """)
        
        # Add shadow effect
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(15)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(2)
        shadow_effect.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow_effect)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Metric name
        self.name_label = QLabel(self.display_name)
        self.name_label.setFont(QFont('Inter', 11))
        self.name_label.setStyleSheet(f"color: {style_manager.TEXT_SECONDARY};")
        layout.addWidget(self.name_label)
        
        # Value and unit
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont('Inter', 24, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {style_manager.ACCENT_PRIMARY};")
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            self.unit_label = QLabel(self.unit)
            self.unit_label.setFont(QFont('Inter', 12))
            self.unit_label.setStyleSheet(f"color: {style_manager.TEXT_MUTED};")
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            value_layout.addWidget(self.unit_label)
            
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Trend indicator
        self.trend_indicator = DailyTrendIndicator()
        layout.addWidget(self.trend_indicator)
        
    def update_value(self, value: float, trend_data: Optional[Dict] = None):
        """Update the displayed value and trend."""
        if value is not None:
            self.value_label.setText(f"{value:,.0f}" if value >= 100 else f"{value:.1f}")
        else:
            self.value_label.setText("--")
            
        if trend_data:
            self.trend_indicator.update_trend(
                trend_data.get('direction', 'stable'),
                trend_data.get('percentage', 0),
                trend_data.get('label', '')
            )
            
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.metric_name)
        super().mousePressEvent(event)


class DailyDashboardWidget(QWidget):
    """
    Daily dashboard widget showing current day's health metrics.
    
    Features:
    - Real-time metric cards with trends
    - Activity timeline visualization
    - Comparison with weekly/monthly averages
    - Personal records tracking
    - Smart metric prioritization
    """
    
    # Signals
    metric_selected = pyqtSignal(str)
    date_changed = pyqtSignal(date)
    refresh_requested = pyqtSignal()
    
    # Common health metrics configuration
    METRIC_CONFIG = {
        'steps': {'display': 'Steps', 'unit': '', 'icon': '🚶', 'priority': 1},
        'distance': {'display': 'Distance', 'unit': 'km', 'icon': '📏', 'priority': 2},
        'flights_climbed': {'display': 'Floors', 'unit': '', 'icon': '🏢', 'priority': 3},
        'active_calories': {'display': 'Active Calories', 'unit': 'kcal', 'icon': '🔥', 'priority': 4},
        'heart_rate': {'display': 'Heart Rate', 'unit': 'bpm', 'icon': '❤️', 'priority': 5},
        'resting_heart_rate': {'display': 'Resting HR', 'unit': 'bpm', 'icon': '💤', 'priority': 6},
        'hrv': {'display': 'HRV', 'unit': 'ms', 'icon': '📊', 'priority': 7},
        'sleep_hours': {'display': 'Sleep', 'unit': 'hrs', 'icon': '😴', 'priority': 8},
        'weight': {'display': 'Weight', 'unit': 'kg', 'icon': '⚖️', 'priority': 9},
        'body_fat': {'display': 'Body Fat', 'unit': '%', 'icon': '📊', 'priority': 10}
    }
    
    def __init__(self, daily_calculator=None, personal_records=None, parent=None):
        """Initialize the daily dashboard widget."""
        super().__init__(parent)
        
        self.daily_calculator = daily_calculator
        self.personal_records = personal_records
        self.day_analyzer = DayOfWeekAnalyzer(daily_calculator) if daily_calculator else None
        
        self._current_date = date.today()
        self._metric_cards = {}
        self._available_metrics = []
        self._selected_metric = None
        
        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.refresh_timer.start(60000)  # Refresh every minute
        
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        if self.daily_calculator:
            self._detect_available_metrics()
            self._load_daily_data()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        self.header_widget = self._create_header()
        main_layout.addWidget(self.header_widget)
        
        # Content area with scroll
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F5E6D3;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #FF8C42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #E67A35;
            }
        """)
        
        # Content widget
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Today's summary section
        summary_section = self._create_summary_section()
        content_layout.addWidget(summary_section)
        
        # Metric cards grid
        cards_section = self._create_metric_cards_section()
        content_layout.addWidget(cards_section)
        
        # Activity timeline
        timeline_section = self._create_timeline_section()
        content_layout.addWidget(timeline_section)
        
        # Detailed view section
        detail_section = self._create_detail_section()
        content_layout.addWidget(detail_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_header(self) -> QWidget:
        """Create the dashboard header with date selector and refresh."""
        header = QFrame(self)
        header.setStyleSheet("""
            QFrame {
                background-color: #FFF8F0;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(20)
        
        # Date navigation
        date_nav_layout = QHBoxLayout()
        date_nav_layout.setSpacing(10)
        
        # Previous day button
        self.prev_day_btn = QPushButton("◀")
        self.prev_day_btn.setFixedSize(36, 36)
        self.prev_day_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 18px;
                font-size: 14px;
                color: #5D4E37;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border: 2px solid #FF8C42;
            }
            QPushButton:pressed {
                background-color: #F5E6D3;
            }
        """)
        self.prev_day_btn.setToolTip("Previous day")
        date_nav_layout.addWidget(self.prev_day_btn)
        
        # Date picker button
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate
        
        self.date_picker = QDateEdit(self)
        self.date_picker.setDate(QDate(self._current_date))
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("MMMM d, yyyy")
        self.date_picker.setStyleSheet("""
            QDateEdit {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Poppins;
                font-size: 14px;
                color: #5D4E37;
                min-width: 180px;
            }
            QDateEdit:hover {
                border: 2px solid #FF8C42;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid rgba(139, 115, 85, 0.2);
            }
            QDateEdit::down-arrow {
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #5D4E37;
            }
        """)
        self.date_picker.dateChanged.connect(self._on_date_picked)
        date_nav_layout.addWidget(self.date_picker)
        
        # Next day button
        self.next_day_btn = QPushButton("▶")
        self.next_day_btn.setFixedSize(36, 36)
        self.next_day_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 18px;
                font-size: 14px;
                color: #5D4E37;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border: 2px solid #FF8C42;
            }
            QPushButton:pressed {
                background-color: #F5E6D3;
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.5);
                color: rgba(93, 78, 55, 0.3);
            }
        """)
        self.next_day_btn.setToolTip("Next day")
        # Disable if current date is today
        self.next_day_btn.setEnabled(self._current_date < date.today())
        date_nav_layout.addWidget(self.next_day_btn)
        
        layout.addLayout(date_nav_layout)
        
        # Date display
        date_display_layout = QVBoxLayout()
        
        # Dynamic title based on whether it's today
        if self._current_date == date.today():
            title_text = "Today's Summary"
        else:
            title_text = self._current_date.strftime("%A")
        
        self.date_label = QLabel(title_text)
        self.date_label.setFont(QFont('Poppins', 24, QFont.Weight.Bold))
        self.date_label.setStyleSheet("color: #5D4E37;")
        date_display_layout.addWidget(self.date_label)
        
        # Subtitle showing relative date
        relative_text = self._get_relative_date_text()
        self.relative_date_label = QLabel(relative_text)
        self.relative_date_label.setFont(QFont('Poppins', 12))
        self.relative_date_label.setStyleSheet("color: #8B7355;")
        date_display_layout.addWidget(self.relative_date_label)
        
        layout.addLayout(date_display_layout)
        layout.addStretch()
        
        # Today button
        self.today_btn = QPushButton("Today")
        self.today_btn.setFixedSize(100, 40)
        self.today_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C42;
                color: white;
                border-radius: 20px;
                font-family: Poppins;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E67A35;
            }
            QPushButton:pressed {
                background-color: #CC6F2F;
            }
            QPushButton:disabled {
                background-color: rgba(255, 140, 66, 0.5);
            }
        """)
        self.today_btn.setEnabled(self._current_date != date.today())
        layout.addWidget(self.today_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border: 2px solid #FF8C42;
            }
        """)
        self.refresh_btn.setToolTip("Refresh data")
        layout.addWidget(self.refresh_btn)
        
        return header
    
    def _create_summary_section(self) -> QWidget:
        """Create summary section."""
        title = "Today's Summary" if self._current_date == date.today() else f"{self._current_date.strftime('%A')}'s Summary"
        section = QGroupBox(title)
        self.summary_section = section
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QHBoxLayout(section)
        layout.setSpacing(20)
        
        # Key metrics summary cards
        self.activity_score = SummaryCard(card_type='simple', size='small', card_id='activity_score')
        self.activity_score.setToolTip("Overall activity level for today")
        layout.addWidget(self.activity_score)
        
        self.goals_progress = SummaryCard(card_type='simple', size='small', card_id='goals_progress')
        self.goals_progress.setToolTip("Progress towards daily goals")
        layout.addWidget(self.goals_progress)
        
        self.personal_best = SummaryCard(card_type='simple', size='small', card_id='personal_best')
        self.personal_best.setToolTip("New personal records today")
        layout.addWidget(self.personal_best)
        
        self.health_status = SummaryCard(card_type='simple', size='small', card_id='health_status')
        self.health_status.setToolTip("Overall health indicators")
        layout.addWidget(self.health_status)
        
        return section
    
    def _create_simple_card(self, title: str, icon: str) -> QWidget:
        """Create a simple card widget with title and icon."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Icon label
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-family: Poppins;
            font-size: 12px;
            font-weight: 600;
            color: #5D4E37;
        """)
        layout.addWidget(title_label)
        
        # Value label (placeholder)
        value_label = QLabel("--")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("""
            font-family: Poppins;
            font-size: 18px;
            font-weight: 700;
            color: #FF8C42;
        """)
        layout.addWidget(value_label)
        
        return card
    
    def _create_metric_cards_section(self) -> QWidget:
        """Create the metric cards grid section."""
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section header
        header_layout = QHBoxLayout()
        
        title = QLabel("Health Metrics")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # View selector
        self.view_selector = QComboBox()
        self.view_selector.addItems(["All Metrics", "Activity", "Vitals", "Body"])
        self.view_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Poppins;
                color: #5D4E37;
                min-width: 120px;
            }
        """)
        header_layout.addWidget(self.view_selector)
        
        layout.addLayout(header_layout)
        
        # Metric cards grid
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(16)
        layout.addLayout(self.cards_grid)
        
        return section
    
    def _create_timeline_section(self) -> QWidget:
        """Create the activity timeline section."""
        section = QGroupBox("Activity Timeline")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # Timeline component
        self.timeline = ActivityTimelineComponent()
        self.timeline.setFixedHeight(200)
        layout.addWidget(self.timeline)
        
        return section
    
    def _create_detail_section(self) -> QWidget:
        """Create the detailed metric view section."""
        section = QGroupBox("Detailed View")
        section.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-family: Poppins;
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # Metric selector
        selector_layout = QHBoxLayout()
        
        metric_label = QLabel("Select Metric:")
        metric_label.setFont(QFont('Poppins', 12))
        metric_label.setStyleSheet("color: #8B7355;")
        selector_layout.addWidget(metric_label)
        
        self.detail_metric_selector = QComboBox()
        self.detail_metric_selector.setMinimumWidth(200)
        self.detail_metric_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Poppins;
                color: #5D4E37;
            }
        """)
        selector_layout.addWidget(self.detail_metric_selector)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Chart area
        self.detail_chart = LineChart()
        self.detail_chart.setMinimumHeight(300)
        
        # Configure chart
        self.detail_chart.set_labels(title="", x_label="Time", y_label="Value")
        self.detail_chart.show_grid = True
        
        layout.addWidget(self.detail_chart)
        
        return section
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.today_btn.clicked.connect(self._go_to_today)
        self.refresh_btn.clicked.connect(self._refresh_data)
        self.prev_day_btn.clicked.connect(self._go_to_previous_day)
        self.next_day_btn.clicked.connect(self._go_to_next_day)
        self.view_selector.currentTextChanged.connect(self._filter_metric_cards)
        self.detail_metric_selector.currentTextChanged.connect(self._update_detail_chart)
    
    def _detect_available_metrics(self):
        """Detect which metrics are available in the data."""
        if not self.daily_calculator:
            return
            
        try:
            # Get unique metric types from the data
            available_types = self.daily_calculator.data['type'].unique()
            
            # Map to our metric names
            metric_mapping = {
                'HKQuantityTypeIdentifierStepCount': 'steps',
                'HKQuantityTypeIdentifierDistanceWalkingRunning': 'distance',
                'HKQuantityTypeIdentifierFlightsClimbed': 'flights_climbed',
                'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_calories',
                'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
                'HKQuantityTypeIdentifierRestingHeartRate': 'resting_heart_rate',
                'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv',
                'HKQuantityTypeIdentifierBodyMass': 'weight',
                'HKQuantityTypeIdentifierBodyFatPercentage': 'body_fat'
            }
            
            self._available_metrics = []
            for hk_type, metric_name in metric_mapping.items():
                if hk_type in available_types:
                    self._available_metrics.append(metric_name)
                    
            # Sort by priority
            self._available_metrics.sort(
                key=lambda x: self.METRIC_CONFIG.get(x, {}).get('priority', 999)
            )
            
            logger.info(f"Detected {len(self._available_metrics)} available metrics")
            
        except Exception as e:
            logger.error(f"Error detecting available metrics: {e}")
            self._available_metrics = []
    
    def _create_metric_cards(self):
        """Create metric cards for available metrics."""
        # Clear existing cards
        for i in reversed(range(self.cards_grid.count())):
            self.cards_grid.itemAt(i).widget().deleteLater()
        self._metric_cards.clear()
        
        # Create cards for up to 8 metrics
        cols = 4
        for i, metric_name in enumerate(self._available_metrics[:8]):
            config = self.METRIC_CONFIG.get(metric_name, {})
            
            card = MetricCard(
                metric_name,
                config.get('display', metric_name),
                config.get('unit', '')
            )
            card.clicked.connect(self._on_metric_card_clicked)
            
            row = i // cols
            col = i % cols
            self.cards_grid.addWidget(card, row, col)
            self._metric_cards[metric_name] = card
    
    def _load_daily_data(self):
        """Load data for the current date."""
        if not self.daily_calculator:
            self._show_no_data_message()
            return
            
        try:
            # Create metric cards if not already done
            if not self._metric_cards:
                self._create_metric_cards()
                self._populate_detail_selector()
            
            # Check if we have any data for this date
            has_any_data = False
            metrics_with_data = []
            
            # Get today's data for each metric
            for metric_name, card in self._metric_cards.items():
                stats = self._get_metric_stats(metric_name)
                if stats and stats['value'] is not None:
                    card.update_value(stats['value'], stats.get('trend'))
                    has_any_data = True
                    metrics_with_data.append(metric_name)
                else:
                    card.update_value(None, None)
            
            if not has_any_data:
                self._show_no_data_for_date()
            else:
                # Hide no data message if it exists
                self._hide_no_data_message()
                
                # Update summary cards
                self._update_summary_cards()
                
                # Update timeline
                self._update_timeline()
                
                # Update detail chart if metric selected
                if self.detail_metric_selector.currentText():
                    self._update_detail_chart()
                
        except Exception as e:
            logger.error(f"Error loading daily data: {e}")
            self._show_error_message(str(e))
    
    def _get_metric_stats(self, metric_name: str) -> Optional[Dict]:
        """Get statistics for a specific metric."""
        if not self.daily_calculator:
            return None
            
        try:
            # Map metric name to HK type
            type_mapping = {
                'steps': 'HKQuantityTypeIdentifierStepCount',
                'distance': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                'flights_climbed': 'HKQuantityTypeIdentifierFlightsClimbed',
                'active_calories': 'HKQuantityTypeIdentifierActiveEnergyBurned',
                'heart_rate': 'HKQuantityTypeIdentifierHeartRate',
                'resting_heart_rate': 'HKQuantityTypeIdentifierRestingHeartRate',
                'hrv': 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN',
                'weight': 'HKQuantityTypeIdentifierBodyMass',
                'body_fat': 'HKQuantityTypeIdentifierBodyFatPercentage'
            }
            
            hk_type = type_mapping.get(metric_name)
            if not hk_type:
                return None
            
            # Get today's value
            today_stats = self.daily_calculator.calculate_daily_statistics(
                metric=hk_type,
                date=self._current_date
            )
            
            if today_stats and today_stats.count > 0:
                # Get yesterday's value for trend
                yesterday = self._current_date - timedelta(days=1)
                yesterday_stats = self.daily_calculator.calculate_daily_statistics(
                    metric=hk_type,
                    date=yesterday
                )
                
                # Calculate trend
                trend_data = None
                if yesterday_stats and yesterday_stats.count > 0:
                    change = today_stats.mean - yesterday_stats.mean
                    pct_change = (change / yesterday_stats.mean * 100) if yesterday_stats.mean else 0
                    
                    trend_data = {
                        'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                        'percentage': abs(pct_change),
                        'label': f"{pct_change:+.1f}% vs yesterday"
                    }
                
                # Convert distance to km
                value = today_stats.mean
                if metric_name == 'distance' and value:
                    value = value / 1000  # Convert meters to km
                
                return {
                    'value': value,
                    'count': today_stats.count,
                    'trend': trend_data
                }
                
        except Exception as e:
            logger.error(f"Error getting stats for {metric_name}: {e}")
            
        return None
    
    def _update_summary_cards(self):
        """Update the summary cards with calculated scores."""
        try:
            # Activity Score (based on steps and active calories)
            activity_score = self._calculate_activity_score()
            self.activity_score.update_content({
                'title': 'Activity Score',
                'value': f"{activity_score}%",
                'subtitle': 'Steps & Calories',
                'status': "good" if activity_score >= 70 else "warning" if activity_score >= 40 else "critical"
            })
            
            # Goals Progress
            goals_progress = self._calculate_goals_progress()
            self.goals_progress.update_content({
                'title': 'Goals Progress',
                'value': f"{goals_progress}%",
                'subtitle': 'Daily targets',
                'status': "good" if goals_progress >= 80 else "warning" if goals_progress >= 50 else "critical"
            })
            
            # Personal Best check
            if self.personal_records:
                records_today = self._check_personal_records()
                if records_today:
                    self.personal_best.update_content({
                        'title': 'Personal Bests',
                        'value': f"{len(records_today)} New!",
                        'subtitle': 'Records today',
                        'status': "good"
                    })
                else:
                    self.personal_best.update_content({
                        'title': 'Personal Bests',
                        'value': "None",
                        'subtitle': 'No records yet',
                        'status': "neutral"
                    })
            else:
                self.personal_best.update_content({
                    'title': 'Personal Bests',
                    'value': "--",
                    'subtitle': 'Loading...',
                    'status': "neutral"
                })
            
            # Health Status (simplified)
            health_score = self._calculate_health_status()
            status_text = "Excellent" if health_score >= 80 else "Good" if health_score >= 60 else "Fair"
            self.health_status.update_content({
                'title': 'Health Status',
                'value': status_text,
                'subtitle': f"Score: {health_score}",
                'status': "good" if health_score >= 80 else "warning" if health_score >= 60 else "critical"
            })
            
        except Exception as e:
            logger.error(f"Error updating summary cards: {e}")
    
    def _calculate_activity_score(self) -> int:
        """Calculate activity score based on steps and calories."""
        score = 0
        
        # Steps contribution (50%)
        steps_stats = self._get_metric_stats('steps')
        if steps_stats and steps_stats['value']:
            steps_score = min(100, (steps_stats['value'] / 10000) * 100)
            score += steps_score * 0.5
        
        # Active calories contribution (50%)
        calories_stats = self._get_metric_stats('active_calories')
        if calories_stats and calories_stats['value']:
            calories_score = min(100, (calories_stats['value'] / 500) * 100)
            score += calories_score * 0.5
            
        return int(score)
    
    def _calculate_goals_progress(self) -> int:
        """Calculate progress towards daily goals."""
        # Simplified goal calculation
        goals = {
            'steps': 10000,
            'active_calories': 500,
            'flights_climbed': 10
        }
        
        progress_values = []
        for metric, goal in goals.items():
            stats = self._get_metric_stats(metric)
            if stats and stats['value']:
                progress = min(100, (stats['value'] / goal) * 100)
                progress_values.append(progress)
        
        return int(sum(progress_values) / len(progress_values)) if progress_values else 0
    
    def _calculate_health_status(self) -> int:
        """Calculate overall health status score."""
        # Simplified health score based on available vitals
        score = 70  # Base score
        
        # Heart rate contribution
        hr_stats = self._get_metric_stats('resting_heart_rate')
        if hr_stats and hr_stats['value']:
            # Lower resting heart rate is better
            if hr_stats['value'] < 60:
                score += 10
            elif hr_stats['value'] > 80:
                score -= 10
        
        # HRV contribution
        hrv_stats = self._get_metric_stats('hrv')
        if hrv_stats and hrv_stats['value']:
            # Higher HRV is better
            if hrv_stats['value'] > 50:
                score += 10
            elif hrv_stats['value'] < 30:
                score -= 10
        
        # Activity bonus
        activity_score = self._calculate_activity_score()
        if activity_score > 70:
            score += 10
            
        return max(0, min(100, score))
    
    def _check_personal_records(self) -> List[str]:
        """Check for new personal records today."""
        records = []
        
        if not self.personal_records:
            return records
            
        # Check each metric for records
        for metric_name in self._available_metrics:
            stats = self._get_metric_stats(metric_name)
            if stats and stats['value']:
                # Map to HK type for personal records
                type_mapping = {
                    'steps': 'HKQuantityTypeIdentifierStepCount',
                    'distance': 'HKQuantityTypeIdentifierDistanceWalkingRunning',
                    'flights_climbed': 'HKQuantityTypeIdentifierFlightsClimbed',
                    'active_calories': 'HKQuantityTypeIdentifierActiveEnergyBurned'
                }
                
                hk_type = type_mapping.get(metric_name)
                if hk_type:
                    is_record = self.personal_records.check_record(
                        hk_type,
                        stats['value'],
                        self._current_date
                    )
                    if is_record:
                        records.append(metric_name)
        
        return records
    
    def _update_timeline(self):
        """Update the activity timeline."""
        if not self.daily_calculator:
            return
            
        try:
            # Get hourly data for steps
            hourly_data = self._get_hourly_data('steps')
            if hourly_data:
                self.timeline.set_activity_data(hourly_data)
                
        except Exception as e:
            logger.error(f"Error updating timeline: {e}")
    
    def _get_hourly_data(self, metric_name: str) -> Optional[pd.DataFrame]:
        """Get hourly data for a metric."""
        if not self.daily_calculator:
            return None
            
        try:
            type_mapping = {
                'steps': 'HKQuantityTypeIdentifierStepCount',
                'active_calories': 'HKQuantityTypeIdentifierActiveEnergyBurned'
            }
            
            hk_type = type_mapping.get(metric_name)
            if not hk_type:
                return None
            
            # Filter data for current date and metric
            data = self.daily_calculator.data[
                (self.daily_calculator.data['type'] == hk_type) &
                (pd.to_datetime(self.daily_calculator.data['creationDate']).dt.date == self._current_date)
            ].copy()
            
            if data.empty:
                return None
            
            # Group by hour
            data['hour'] = pd.to_datetime(data['creationDate']).dt.hour
            hourly = data.groupby('hour')['value'].sum().reset_index()
            
            # Fill missing hours with 0
            all_hours = pd.DataFrame({'hour': range(24)})
            hourly = all_hours.merge(hourly, on='hour', how='left').fillna(0)
            
            return hourly
            
        except Exception as e:
            logger.error(f"Error getting hourly data: {e}")
            return None
    
    def _populate_detail_selector(self):
        """Populate the detail metric selector."""
        self.detail_metric_selector.clear()
        
        for metric_name in self._available_metrics:
            config = self.METRIC_CONFIG.get(metric_name, {})
            display_name = f"{config.get('icon', '')} {config.get('display', metric_name)}"
            self.detail_metric_selector.addItem(display_name, metric_name)
    
    def _update_detail_chart(self):
        """Update the detailed metric chart."""
        if not self.daily_calculator or not self.detail_metric_selector.count():
            return
            
        try:
            # Get selected metric
            metric_name = self.detail_metric_selector.currentData()
            if not metric_name:
                return
            
            # Get hourly data
            hourly_data = self._get_hourly_data(metric_name)
            if hourly_data is None or hourly_data.empty:
                return
            
            # Prepare data for chart
            x_data = hourly_data['hour'].tolist()
            y_data = hourly_data['value'].tolist()
            
            # Update chart
            config = self.METRIC_CONFIG.get(metric_name, {})
            self.detail_chart.set_labels(
                title=f"{config.get('display', metric_name)} - Today",
                x_label="Hour",
                y_label=config.get('unit', 'Value')
            )
            
            # Prepare data points for LineChart
            data_points = [
                {'x': i, 'y': y, 'label': str(x)}
                for i, (x, y) in enumerate(zip(x_data, y_data))
            ]
            
            # Set y-range based on data
            if y_data:
                y_min = min(y_data) * 0.9
                y_max = max(y_data) * 1.1
                self.detail_chart.set_y_range(y_min, y_max)
            
            self.detail_chart.set_data(data_points)
            
        except Exception as e:
            logger.error(f"Error updating detail chart: {e}")
    
    def _filter_metric_cards(self, filter_text: str):
        """Filter metric cards based on category."""
        category_mapping = {
            'Activity': ['steps', 'distance', 'flights_climbed', 'active_calories'],
            'Vitals': ['heart_rate', 'resting_heart_rate', 'hrv'],
            'Body': ['weight', 'body_fat'],
            'All Metrics': self._available_metrics
        }
        
        visible_metrics = category_mapping.get(filter_text, self._available_metrics)
        
        for metric_name, card in self._metric_cards.items():
            card.setVisible(metric_name in visible_metrics)
    
    def _go_to_today(self):
        """Navigate to today's date."""
        self._current_date = date.today()
        self.today_btn.setEnabled(False)
        self._update_date_display()
        self._refresh_data()
        self.date_changed.emit(self._current_date)
    
    def _update_date_display(self):
        """Update the date display labels."""
        # Update title
        if self._current_date == date.today():
            title_text = "Today's Summary"
        else:
            title_text = self._current_date.strftime("%A")
        self.date_label.setText(title_text)
        
        # Update relative date
        relative_text = self._get_relative_date_text()
        self.relative_date_label.setText(relative_text)
        
        # Update date picker
        from PyQt6.QtCore import QDate
        self.date_picker.setDate(QDate(self._current_date))
        
        # Update navigation buttons
        self.today_btn.setEnabled(self._current_date != date.today())
        self.next_day_btn.setEnabled(self._current_date < date.today())
        
        # Update summary section title
        if hasattr(self, 'summary_section'):
            summary_title = "Today's Summary" if self._current_date == date.today() else f"{self._current_date.strftime('%A')}'s Summary"
            self.summary_section.setTitle(summary_title)
    
    def _get_relative_date_text(self) -> str:
        """Get relative date text for display."""
        today = date.today()
        delta = (self._current_date - today).days
        
        if delta == 0:
            return self._current_date.strftime("%B %d, %Y")
        elif delta == -1:
            return "Yesterday"
        elif delta == 1:
            return "Tomorrow"
        elif -7 <= delta < -1:
            return f"{-delta} days ago"
        elif 1 < delta <= 7:
            return f"In {delta} days"
        else:
            return self._current_date.strftime("%B %d, %Y")
    
    def _go_to_previous_day(self):
        """Navigate to the previous day."""
        self._current_date = self._current_date - timedelta(days=1)
        self._update_date_display()
        self._refresh_data()
        self.date_changed.emit(self._current_date)
    
    def _go_to_next_day(self):
        """Navigate to the next day."""
        if self._current_date < date.today():
            self._current_date = self._current_date + timedelta(days=1)
            self._update_date_display()
            self._refresh_data()
            self.date_changed.emit(self._current_date)
    
    def _on_date_picked(self, qdate):
        """Handle date selection from the date picker."""
        new_date = qdate.toPyDate()
        if new_date != self._current_date and new_date <= date.today():
            self._current_date = new_date
            self._update_date_display()
            self._refresh_data()
            self.date_changed.emit(self._current_date)
    
    def _refresh_data(self):
        """Refresh all data displays."""
        self._load_daily_data()
        self.refresh_requested.emit()
    
    def _auto_refresh(self):
        """Auto-refresh data if viewing today."""
        if self._current_date == date.today():
            self._refresh_data()
    
    def _on_metric_card_clicked(self, metric_name: str):
        """Handle metric card click."""
        self._selected_metric = metric_name
        
        # Update detail selector
        for i in range(self.detail_metric_selector.count()):
            if self.detail_metric_selector.itemData(i) == metric_name:
                self.detail_metric_selector.setCurrentIndex(i)
                break
        
        self.metric_selected.emit(metric_name)
    
    def set_daily_calculator(self, calculator: DailyMetricsCalculator):
        """Set the daily metrics calculator."""
        self.daily_calculator = calculator
        self.day_analyzer = DayOfWeekAnalyzer(calculator) if calculator else None
        self._detect_available_metrics()
        self._load_daily_data()
        
        # Force UI refresh
        self.update()
        QApplication.processEvents()
    
    def set_personal_records(self, tracker: PersonalRecordsTracker):
        """Set the personal records tracker."""
        self.personal_records = tracker
        self._update_summary_cards()
    
    def _show_no_data_message(self):
        """Show message when no data is loaded."""
        # Create or update no data overlay
        if not hasattr(self, 'no_data_overlay'):
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PyQt6.QtCore import Qt
            
            self.no_data_overlay = QWidget(self)
            self.no_data_overlay.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    border: 1px solid rgba(139, 115, 85, 0.1);
                    margin: 10px;
                }
            """)
            
            overlay_layout = QVBoxLayout(self.no_data_overlay)
            overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📊")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 64px;")
            overlay_layout.addWidget(icon_label)
            
            # Message
            message_label = QLabel("No Data Loaded")
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setStyleSheet("""
                font-family: Poppins;
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                margin: 20px 0;
            """)
            overlay_layout.addWidget(message_label)
            
            # Instructions
            instructions = QLabel("Please go to the Configuration tab and import your Apple Health data.")
            instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
            instructions.setWordWrap(True)
            instructions.setStyleSheet("""
                font-family: Poppins;
                font-size: 14px;
                color: #8B7355;
                max-width: 400px;
            """)
            overlay_layout.addWidget(instructions)
        
        # Position and show overlay
        self._position_overlay()
        self.no_data_overlay.show()
        self.no_data_overlay.raise_()
    
    def _show_no_data_for_date(self):
        """Show message when no data exists for selected date."""
        if not hasattr(self, 'no_data_overlay'):
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
            from PyQt6.QtCore import Qt
            
            self.no_data_overlay = QWidget(self)
            self.no_data_overlay.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    border: 1px solid rgba(139, 115, 85, 0.1);
                    margin: 10px;
                }
            """)
            
            overlay_layout = QVBoxLayout(self.no_data_overlay)
            overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            self.no_data_icon = QLabel("📅")
            self.no_data_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_data_icon.setStyleSheet("font-size: 64px;")
            overlay_layout.addWidget(self.no_data_icon)
            
            # Message
            self.no_data_message = QLabel("No Data for This Day")
            self.no_data_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_data_message.setStyleSheet("""
                font-family: Poppins;
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                margin: 20px 0;
            """)
            overlay_layout.addWidget(self.no_data_message)
            
            # Date info
            self.no_data_date = QLabel()
            self.no_data_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_data_date.setWordWrap(True)
            self.no_data_date.setStyleSheet("""
                font-family: Poppins;
                font-size: 14px;
                color: #8B7355;
                max-width: 400px;
            """)
            overlay_layout.addWidget(self.no_data_date)
        
        # Update message for specific date
        date_str = self._current_date.strftime("%B %d, %Y")
        if self._current_date == date.today():
            self.no_data_message.setText("No Data for Today")
            self.no_data_date.setText("Start recording activities and they'll appear here automatically.\n\nUse the navigation controls above to view other days.")
        else:
            self.no_data_message.setText("No Data Available")
            self.no_data_date.setText(f"No health data was recorded on {date_str}.\n\nUse the navigation controls above to view other days.")
        
        # Position and show overlay
        self._position_overlay()
        self.no_data_overlay.show()
        self.no_data_overlay.raise_()
    
    def _hide_no_data_message(self):
        """Hide the no data message overlay."""
        if hasattr(self, 'no_data_overlay'):
            self.no_data_overlay.hide()
    
    def _show_error_message(self, error: str):
        """Show error message overlay."""
        logger.error(f"Showing error: {error}")
        # For now, just log the error
        # Could implement a proper error overlay if needed
    
    def _position_overlay(self):
        """Position the overlay to cover the content area."""
        if hasattr(self, 'no_data_overlay'):
            # Only cover the content area below the header
            # Calculate actual header height including margins
            header_height = 20  # top margin
            if hasattr(self, 'header_widget'):
                header_height += self.header_widget.height() + 20  # header + spacing
            else:
                header_height = 100  # fallback
            
            self.no_data_overlay.setGeometry(
                20,  # left margin
                header_height, 
                self.width() - 40,  # account for left/right margins
                self.height() - header_height - 20  # account for bottom margin
            )
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        # Reposition overlay if visible
        if hasattr(self, 'no_data_overlay') and self.no_data_overlay.isVisible():
            self._position_overlay()
    
    def showEvent(self, event):
        """Handle widget show event to ensure UI is refreshed."""
        super().showEvent(event)
        # Force a refresh when the widget is shown
        if self.daily_calculator:
            self._load_daily_data()
            self.update()
            QApplication.processEvents()
            # Schedule another update after a short delay to ensure complete rendering
            QTimer.singleShot(100, self._delayed_refresh)
        else:
            self._show_no_data_message()
    
    def _delayed_refresh(self):
        """Delayed refresh to ensure complete rendering."""
        if hasattr(self, 'timeline'):
            self.timeline.update()
        if hasattr(self, 'detail_chart'):
            self.detail_chart.update()
        for card in self._metric_cards.values():
            card.update()
        self.update()