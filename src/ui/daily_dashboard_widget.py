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
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QGroupBox, QApplication, QGraphicsDropShadowEffect,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDateTime, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from .summary_cards import SummaryCard
from .daily_trend_indicator import DailyTrendIndicator, TrendData
from .activity_timeline_component import ActivityTimelineComponent
from .charts.line_chart import LineChart
from ..analytics.daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics
from ..analytics.personal_records_tracker import PersonalRecordsTracker
from ..analytics.day_of_week_analyzer import DayOfWeekAnalyzer
from ..utils.logging_config import get_logger
from ..health_database import HealthDatabase

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
        self.setFixedHeight(180)  # Increased from 120 to 180 for better visibility
        from .style_manager import StyleManager
        style_manager = StyleManager()
        shadow = style_manager.get_shadow_style('md')
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {style_manager.PRIMARY_BG};
                border: none;
                border-radius: 12px;
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
        layout.setSpacing(12)  # Increased spacing for better distribution
        layout.setContentsMargins(16, 16, 16, 16)  # Add margins inside the card
        
        # Metric name
        self.name_label = QLabel(self.display_name)
        self.name_label.setFont(QFont('Inter', 12))  # Increased from 11
        self.name_label.setStyleSheet(f"color: {style_manager.TEXT_SECONDARY};")
        layout.addWidget(self.name_label)
        
        # Value and unit
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont('Inter', 32, QFont.Weight.Bold))  # Increased from 24
        self.value_label.setStyleSheet(f"color: {style_manager.ACCENT_PRIMARY};")
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            self.unit_label = QLabel(self.unit)
            self.unit_label.setFont(QFont('Inter', 14))  # Increased from 12
            self.unit_label.setStyleSheet(f"color: {style_manager.TEXT_MUTED};")
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            value_layout.addWidget(self.unit_label)
            
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Add stretch to center content vertically
        layout.addStretch(1)
        
        # Trend indicator
        self.trend_indicator = DailyTrendIndicator(self.metric_name)
        self.trend_indicator.setMinimumHeight(30)  # Ensure trend indicator has space
        layout.addWidget(self.trend_indicator)
        
    def update_value(self, value: float, trend_data: Optional[Dict] = None):
        """Update the displayed value and trend."""
        if value is not None:
            self.value_label.setText(f"{value:,.0f}" if value >= 100 else f"{value:.1f}")
        else:
            self.value_label.setText("--")
            
        if trend_data and value is not None:
            # Create a TrendData object from the trend_data dictionary
            # Calculate previous value from percentage change if available
            percentage = trend_data.get('percentage', 0)
            direction = trend_data.get('direction', 'stable')
            
            # Calculate previous value and absolute change
            if percentage != 0 and direction != 'stable':
                # If direction is 'down', percentage should be negative
                actual_percentage = -percentage if direction == 'down' else percentage
                previous_value = value / (1 + actual_percentage / 100)
                change_absolute = value - previous_value
            else:
                previous_value = value
                change_absolute = 0
                actual_percentage = 0
            
            # Create TrendData object
            trend_obj = TrendData(
                current_value=value,
                previous_value=previous_value,
                change_absolute=change_absolute,
                change_percent=actual_percentage,
                history=[],  # Empty for now, could be populated if we have historical data
                dates=[],    # Empty for now
                unit=self.unit,
                metric_name=self.metric_name
            )
            
            self.trend_indicator.update_trend(trend_obj)
            
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
        
        # Support both old calculator and new cached access
        self.daily_calculator = daily_calculator
        self.cached_data_access = None
        self.personal_records = personal_records
        self.day_analyzer = DayOfWeekAnalyzer(daily_calculator) if daily_calculator else None
        
        # Try to initialize HealthDatabase
        try:
            self.health_db = HealthDatabase()
        except Exception as e:
            logger.error(f"Failed to initialize HealthDatabase: {e}")
            self.health_db = None
        
        self._current_date = date.today()
        self._metric_cards = {}
        self._available_metrics = []  # List of (metric_type, source) tuples
        self._current_metric = ("StepCount", None)  # Default to aggregated steps
        self._selected_metric = None
        
        # Initialize metric mappings
        self._init_metric_mappings()
        
        
        # Debounce timer for updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._perform_delayed_update)
        self._pending_update = False
        
        # Cache for metric stats
        self._stats_cache = {}
        self._cache_date = None
        
        self._setup_ui()
        self._setup_connections()
        
        # Load initial data
        if self.daily_calculator:
            self._detect_available_metrics()
            self._refresh_metric_combo()
            self._load_daily_data()
    
    def set_cached_data_access(self, cached_access):
        """Set the cached data access for performance optimization.
        
        Args:
            cached_access: CachedDataAccess instance for reading pre-computed summaries
        """
        self.cached_data_access = cached_access
        # Reload data with new access method
        if cached_access:
            self._detect_available_metrics()
            self._refresh_metric_combo()
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
        scroll_area = QScrollArea()
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
        content_widget = QWidget()
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
    
    def _init_metric_mappings(self):
        """Initialize comprehensive metric name mappings."""
        # Map database metric types (without HK prefix) to display names
        self._metric_display_names = {
            # Activity & Fitness
            "StepCount": "Steps",
            "DistanceWalkingRunning": "Walking + Running Distance",
            "FlightsClimbed": "Flights Climbed",
            "ActiveEnergyBurned": "Active Calories",
            "BasalEnergyBurned": "Resting Calories",
            "AppleExerciseTime": "Exercise Minutes",
            "AppleStandHour": "Stand Hours",
            
            # Cardiovascular
            "HeartRate": "Heart Rate",
            "RestingHeartRate": "Resting Heart Rate",
            "WalkingHeartRateAverage": "Walking Heart Rate",
            "HeartRateVariabilitySDNN": "Heart Rate Variability",
            "BloodPressureSystolic": "Blood Pressure (Systolic)",
            "BloodPressureDiastolic": "Blood Pressure (Diastolic)",
            
            # Body Measurements
            "BodyMass": "Body Weight",
            "LeanBodyMass": "Lean Body Mass",
            "BodyMassIndex": "BMI",
            "BodyFatPercentage": "Body Fat %",
            "Height": "Height",
            
            # Mobility & Balance
            "WalkingSpeed": "Walking Speed",
            "WalkingStepLength": "Step Length",
            "WalkingAsymmetryPercentage": "Walking Asymmetry",
            "WalkingDoubleSupportPercentage": "Double Support %",
            "AppleWalkingSteadiness": "Walking Steadiness",
            
            # Respiratory
            "RespiratoryRate": "Respiratory Rate",
            "VO2Max": "VO2 Max",
            
            # Sleep
            "SleepAnalysis": "Sleep Analysis",
            
            # Nutrition
            "DietaryEnergyConsumed": "Calories Consumed",
            "DietaryProtein": "Protein",
            "DietaryCarbohydrates": "Carbohydrates",
            "DietaryFatTotal": "Total Fat",
            "DietaryWater": "Water",
            
            # Environmental
            "HeadphoneAudioExposure": "Headphone Audio Exposure",
            
            # Mindfulness
            "MindfulSession": "Mindful Minutes",
        }
        
        # Map database metric types to units for display
        self._metric_units = {
            "StepCount": "steps",
            "DistanceWalkingRunning": "km",
            "FlightsClimbed": "flights",
            "ActiveEnergyBurned": "kcal",
            "BasalEnergyBurned": "kcal",
            "AppleExerciseTime": "min",
            "AppleStandHour": "hours",
            "HeartRate": "bpm",
            "RestingHeartRate": "bpm",
            "WalkingHeartRateAverage": "bpm",
            "HeartRateVariabilitySDNN": "ms",
            "BodyMass": "kg",
            "RespiratoryRate": "bpm",
            "MindfulSession": "min",
            "HeadphoneAudioExposure": "dB",
            "DietaryWater": "mL",
        }
        
        # Create reverse mapping from shorthand names to database names
        self._shorthand_to_db = {
            'steps': 'StepCount',
            'distance': 'DistanceWalkingRunning',
            'flights_climbed': 'FlightsClimbed',
            'active_calories': 'ActiveEnergyBurned',
            'heart_rate': 'HeartRate',
            'resting_heart_rate': 'RestingHeartRate',
            'hrv': 'HeartRateVariabilitySDNN',
            'sleep_hours': 'SleepAnalysis',
            'weight': 'BodyMass',
            'body_fat': 'BodyFatPercentage'
        }
    
    def _create_header(self) -> QWidget:
        """Create the dashboard header with date selector and refresh."""
        header = QFrame()
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
        
        self.date_picker = QDateEdit()
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
        from .summary_cards import SimpleMetricCard
        
        self.activity_score = SimpleMetricCard(size='small', card_id='activity_score')
        self.activity_score.setToolTip("Overall activity level for today")
        layout.addWidget(self.activity_score)
        
        self.goals_progress = SimpleMetricCard(size='small', card_id='goals_progress')
        self.goals_progress.setToolTip("Progress towards daily goals")
        layout.addWidget(self.goals_progress)
        
        self.personal_best = SimpleMetricCard(size='small', card_id='personal_best')
        self.personal_best.setToolTip("New personal records today")
        layout.addWidget(self.personal_best)
        
        self.health_status = SimpleMetricCard(size='small', card_id='health_status')
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
        section = QWidget()
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
        self.timeline.setMinimumHeight(400)  # Increased from fixed 200 to minimum 400
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
        try:
            if hasattr(self, 'today_btn'):
                self.today_btn.clicked.connect(self._go_to_today)
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.clicked.connect(self._refresh_data)
            if hasattr(self, 'prev_day_btn'):
                self.prev_day_btn.clicked.connect(self._go_to_previous_day)
            if hasattr(self, 'next_day_btn'):
                self.next_day_btn.clicked.connect(self._go_to_next_day)
            if hasattr(self, 'view_selector'):
                self.view_selector.currentTextChanged.connect(self._filter_metric_cards)
            if hasattr(self, 'detail_metric_selector'):
                self.detail_metric_selector.currentIndexChanged.connect(self._on_detail_metric_changed)
        except Exception as e:
            logger.error(f"Error setting up connections: {e}", exc_info=True)
    
    def _detect_available_metrics(self):
        """Load available metrics from the database with source information."""
        logger.info("Loading available metrics with source information...")
        
        # Initialize metric mappings if not already done
        if not hasattr(self, '_metric_display_names'):
            self._init_metric_mappings()
        
        # Try cached data access first
        if self.cached_data_access:
            logger.info("Loading metrics from cache")
            available_types = self.cached_data_access.get_available_metrics()
            
            self._available_metrics = []
            for db_type in available_types:
                # Check if it already exists in our display names
                if db_type in self._metric_display_names:
                    clean_type = db_type
                else:
                    # If not, try stripping HK prefixes
                    clean_type = db_type.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
                
                # Only include metrics we have display names for
                if clean_type in self._metric_display_names:
                    self._available_metrics.append((clean_type, None))
                    logger.debug(f"Added metric from cache: {clean_type}")
            
            if self._available_metrics:
                self._available_metrics.sort(key=lambda x: self._metric_display_names.get(x[0], x[0]))
                logger.info(f"Loaded {len(self._available_metrics)} metrics from cache")
                return
        
        # Fall back to database if no cached access
        if not self.health_db:
            logger.warning("No data access available - cannot load metrics")
            self._available_metrics = []
            return
        
        try:
            # Get all available types from database
            db_types = self.health_db.get_available_types()
            logger.info(f"Found {len(db_types)} types in database")
            
            # Get all available sources
            sources = self.health_db.get_available_sources()
            logger.info(f"Found {len(sources)} data sources in database")
            
            # Build list of (metric, source) tuples
            self._available_metrics = []
            seen_metrics = set()
            
            # First, add aggregated metrics (no source specified) for all available types
            for db_type in db_types:
                # Check if it already exists in our display names
                if db_type in self._metric_display_names:
                    clean_type = db_type
                else:
                    # If not, try stripping HK prefixes
                    clean_type = db_type.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
                
                # Only include metrics we have display names for
                if clean_type in self._metric_display_names:
                    self._available_metrics.append((clean_type, None))
                    seen_metrics.add(clean_type)
                    logger.debug(f"Added aggregated metric: {clean_type}")
            
            # Then, add source-specific metrics
            for source in sources:
                types_for_source = self.health_db.get_types_for_source(source)
                
                for db_type in types_for_source:
                    # Check if it already exists in our display names
                    if db_type in self._metric_display_names:
                        clean_type = db_type
                    else:
                        # If not, try stripping HK prefixes
                        clean_type = db_type.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
                    
                    # Only include metrics we have display names for
                    if clean_type in self._metric_display_names:
                        self._available_metrics.append((clean_type, source))
                        logger.debug(f"Added metric: {clean_type} from {source}")
            
            # Sort by display name and source for better UX
            self._available_metrics.sort(key=lambda x: (
                self._metric_display_names.get(x[0], x[0]), 
                x[1] if x[1] else ""  # Put "All Sources" first
            ))
            
            logger.info(f"Loaded {len(self._available_metrics)} metric-source combinations")
            
        except Exception as e:
            logger.error(f"Error loading available metrics: {e}", exc_info=True)
            self._available_metrics = []
    
    def _refresh_metric_combo(self):
        """Refresh the detail metric combo box with current available metrics."""
        if not hasattr(self, 'detail_metric_selector'):
            return
            
        # Save current selection
        current_index = self.detail_metric_selector.currentIndex()
        current_data = self.detail_metric_selector.itemData(current_index) if current_index >= 0 else None
        
        # Clear and repopulate
        self.detail_metric_selector.clear()
        logger.info(f"Refreshing combo box with {len(self._available_metrics)} metrics")
        
        if not self._available_metrics:
            # No metrics available - add placeholder
            self.detail_metric_selector.addItem("No metrics available", None)
            self.detail_metric_selector.setEnabled(False)
            logger.warning("No metrics available to display")
            return
        
        # Enable combo box if it was disabled
        self.detail_metric_selector.setEnabled(True)
        
        for metric_tuple in self._available_metrics:
            metric, source = metric_tuple
            display_name = self._metric_display_names.get(metric, metric)
            
            # Format display text based on source
            if source:
                display_text = f"{display_name} - {source}"
            else:
                display_text = f"{display_name} (All Sources)"
                
            self.detail_metric_selector.addItem(display_text, metric_tuple)
            logger.debug(f"Added to combo: {display_text}")
        
        # Try to restore saved preference first
        from ..data_access import PreferenceDAO
        saved_metric = PreferenceDAO.get_preference('daily_selected_metric')
        
        restored = False
        if saved_metric:
            try:
                saved_tuple = tuple(saved_metric)  # JSON already decoded by PreferenceDAO
                if saved_tuple in self._available_metrics:
                    index = self._available_metrics.index(saved_tuple)
                    self.detail_metric_selector.setCurrentIndex(index)
                    self._selected_metric = saved_tuple
                    restored = True
                    logger.info(f"Restored saved metric preference: {saved_tuple}")
            except Exception as e:
                logger.error(f"Failed to restore metric preference: {e}")
        
        # If preference wasn't restored, fall back to existing logic
        if not restored:
            # Restore selection if possible
            if current_data and current_data in self._available_metrics:
                index = self._available_metrics.index(current_data)
                self.detail_metric_selector.setCurrentIndex(index)
            elif self._current_metric in self._available_metrics:
                index = self._available_metrics.index(self._current_metric)
                self.detail_metric_selector.setCurrentIndex(index)
    
    def _create_metric_cards(self):
        """Create metric cards for available metrics."""
        # Get unique metric types (ignore sources for cards)
        unique_metrics = []
        seen = set()
        for metric_tuple in self._available_metrics:
            metric_type = metric_tuple[0]
            if metric_type not in seen:
                unique_metrics.append(metric_type)
                seen.add(metric_type)
        
        # Only recreate if metrics have changed
        current_metrics = set(self._metric_cards.keys())
        new_metrics = set(unique_metrics[:8])
        
        if current_metrics == new_metrics:
            return  # No need to recreate
            
        # Clear existing cards
        for i in reversed(range(self.cards_grid.count())):
            widget = self.cards_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self._metric_cards.clear()
        
        # Create cards for up to 8 metrics
        cols = 4
        for i, metric_name in enumerate(unique_metrics[:8]):
            display_name = self._metric_display_names.get(metric_name, metric_name)
            unit = self._metric_units.get(metric_name, '')
            
            card = MetricCard(
                metric_name,
                display_name,
                unit
            )
            card.clicked.connect(self._on_metric_card_clicked)
            
            row = i // cols
            col = i % cols
            self.cards_grid.addWidget(card, row, col)
            self._metric_cards[metric_name] = card
    
    def _load_daily_data(self):
        """Load data for the current date."""
        logger.info(f"Loading daily data for {self._current_date}")
        
        if not self.daily_calculator and not self.cached_data_access:
            logger.debug("No data access available - data not loaded yet")
            self._show_no_data_message()
            return
            
        try:
            # Clear cache if date changed
            if self._cache_date != self._current_date:
                logger.info(f"Date changed from {self._cache_date} to {self._current_date}, clearing cache")
                self._stats_cache.clear()
                self._cache_date = self._current_date
                if hasattr(self, '_hourly_cache'):
                    self._hourly_cache.clear()
            
            # Create metric cards if needed
            logger.info("Checking metric cards")
            self._create_metric_cards()
            self._populate_detail_selector()
            
            # Check if we have any data for this date
            has_any_data = False
            metrics_with_data = []
            
            # Process metrics immediately without batching
            for metric_name, card in self._metric_cards.items():
                try:
                    # For metric cards, we show aggregated data (all sources)
                    stats = self._get_metric_stats((metric_name, None))
                    if stats and stats['value'] is not None:
                        card.update_value(stats['value'], stats.get('trend'))
                        has_any_data = True
                        metrics_with_data.append(metric_name)
                        logger.info(f"Updated {metric_name} card with value {stats['value']}")
                    else:
                        card.update_value(None, None)
                        logger.warning(f"No data for {metric_name} on {self._current_date}")
                except Exception as e:
                    logger.error(f"Error getting stats for {metric_name}: {e}", exc_info=True)
                    card.update_value(None, None)
            
            logger.info(f"Found data for {len(metrics_with_data)} metrics on {self._current_date}")
            
            if not has_any_data:
                logger.warning(f"No data found for date {self._current_date}")
                self._show_no_data_for_date()
            else:
                # Hide no data message if it exists
                self._hide_no_data_message()
                
                # Update other components immediately
                self._update_summary_cards()
                self._update_timeline()
                
                # Update detail chart if metric selected
                if hasattr(self, 'detail_metric_selector') and self.detail_metric_selector.currentText():
                    self._update_detail_chart()
                
        except Exception as e:
            logger.error(f"Error loading daily data: {e}", exc_info=True)
            self._show_error_message(str(e))
    
    def _get_metric_stats(self, metric_tuple) -> Optional[Dict]:
        """Get statistics for a specific metric with caching."""
        # Handle both old format (string) and new format (tuple)
        if isinstance(metric_tuple, str):
            metric_name = metric_tuple
            source = None
        else:
            metric_name, source = metric_tuple
            
        # Check cache first
        cache_key = f"{metric_name}_{source}_{self._current_date}"
        if self._cache_date == self._current_date and cache_key in self._stats_cache:
            return self._stats_cache[cache_key]
            
        # Get the database format for this metric
        hk_type = self._get_database_metric_type(metric_name)
        if not hk_type:
            return None
            
        try:
            # Get daily value based on source
            if source:
                # Get source-specific data
                daily_value = self._get_source_specific_daily_value(hk_type, self._current_date, source)
            else:
                # Get aggregated data from all sources
                if self.cached_data_access:
                    logger.debug(f"Getting cached stats for {metric_name} on {self._current_date}")
                    summary = self.cached_data_access.get_daily_summary(hk_type, self._current_date)
                    
                    if summary:
                        # Convert cached summary to expected format
                        today_stats = self.cached_data_access.convert_to_metric_statistics(summary)
                        daily_value = today_stats.mean if today_stats and today_stats.count > 0 else None
                    else:
                        daily_value = None
                elif self.daily_calculator:
                    # Fallback to calculator if no cached access
                    logger.debug(f"Calculating stats for {metric_name} on {self._current_date}")
                    today_stats = self.daily_calculator.calculate_daily_statistics(
                        hk_type,
                        self._current_date
                    )
                    daily_value = today_stats.mean if today_stats and today_stats.count > 0 else None
                else:
                    daily_value = None
            
            logger.debug(f"Stats for {metric_name} (source: {source}): {daily_value}")
            
            if daily_value is not None:
                # Calculate trend only for visible metrics and aggregated data
                trend_data = None
                if not source and metric_name in ['StepCount', 'ActiveEnergyBurned']:  # Only for key aggregated metrics
                    yesterday = self._current_date - timedelta(days=1)
                    
                    # Get yesterday's stats
                    yesterday_value = None
                    if self.cached_data_access:
                        yesterday_summary = self.cached_data_access.get_daily_summary(hk_type, yesterday)
                        if yesterday_summary:
                            yesterday_stats = self.cached_data_access.convert_to_metric_statistics(yesterday_summary)
                            yesterday_value = yesterday_stats.mean if yesterday_stats and yesterday_stats.count > 0 else None
                    elif self.daily_calculator:
                        yesterday_stats = self.daily_calculator.calculate_daily_statistics(
                            hk_type,
                            yesterday
                        )
                        yesterday_value = yesterday_stats.mean if yesterday_stats and yesterday_stats.count > 0 else None
                    
                    if yesterday_value is not None and yesterday_value > 0:
                        change = daily_value - yesterday_value
                        pct_change = (change / yesterday_value * 100)
                        
                        trend_data = {
                            'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                            'percentage': abs(pct_change),
                            'label': f"{pct_change:+.1f}% vs yesterday"
                        }
                
                # Convert value for display
                display_value = self._convert_value_for_display(daily_value, metric_name)
                
                result = {
                    'value': display_value,
                    'count': 1,  # We have data
                    'trend': trend_data
                }
                
                # Cache the result
                if self._cache_date != self._current_date:
                    self._stats_cache.clear()
                    self._cache_date = self._current_date
                self._stats_cache[cache_key] = result
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting stats for {metric_name}: {e}")
            
        return None
    
    def _update_summary_cards(self):
        """Update the summary cards with calculated scores."""
        logger.info("Updating summary cards")
        
        # Check if summary cards exist before updating
        if not hasattr(self, 'activity_score') or not hasattr(self, 'goals_progress'):
            logger.warning("Summary cards not initialized yet")
            return
            
        try:
            # Activity Score (based on steps and active calories)
            activity_score = self._calculate_activity_score()
            logger.info(f"Calculated activity score: {activity_score}%")
            
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
                        'value': str(len(records_today)),
                        'subtitle': 'New records today!',
                        'status': "good"
                    })
                else:
                    self.personal_best.update_content({
                        'title': 'Personal Bests',
                        'value': '0',
                        'subtitle': 'No records yet',
                        'status': "neutral"
                    })
            else:
                self.personal_best.update_content({
                    'title': 'Personal Bests',
                    'value': '0',
                    'subtitle': 'Tracker not loaded',
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
        # Use database metric name instead of shorthand
        steps_stats = self._get_metric_stats(('StepCount', None))
        if steps_stats and steps_stats['value']:
            steps_score = min(100, (steps_stats['value'] / 10000) * 100)
            score += steps_score * 0.5
        
        # Active calories contribution (50%)
        calories_stats = self._get_metric_stats(('ActiveEnergyBurned', None))
        if calories_stats and calories_stats['value']:
            calories_score = min(100, (calories_stats['value'] / 500) * 100)
            score += calories_score * 0.5
            
        return int(score)
    
    def _calculate_goals_progress(self) -> int:
        """Calculate progress towards daily goals."""
        # Simplified goal calculation - use database metric names
        goals = {
            'StepCount': 10000,
            'ActiveEnergyBurned': 500,
            'FlightsClimbed': 10
        }
        
        progress_values = []
        for metric, goal in goals.items():
            stats = self._get_metric_stats((metric, None))
            if stats and stats['value']:
                progress = min(100, (stats['value'] / goal) * 100)
                progress_values.append(progress)
        
        return int(sum(progress_values) / len(progress_values)) if progress_values else 0
    
    def _calculate_health_status(self) -> int:
        """Calculate overall health status score."""
        # Simplified health score based on available vitals
        score = 70  # Base score
        
        # Heart rate contribution
        hr_stats = self._get_metric_stats(('RestingHeartRate', None))
        if hr_stats and hr_stats['value']:
            # Lower resting heart rate is better
            if hr_stats['value'] < 60:
                score += 10
            elif hr_stats['value'] > 80:
                score -= 10
        
        # HRV contribution
        hrv_stats = self._get_metric_stats(('HeartRateVariabilitySDNN', None))
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
            
        # Check each unique metric type for records (ignore sources)
        seen_metrics = set()
        for metric_tuple in self._available_metrics:
            metric_name = metric_tuple[0]
            if metric_name not in seen_metrics:
                seen_metrics.add(metric_name)
                # Check aggregated data for records
                stats = self._get_metric_stats((metric_name, None))
                if stats and stats['value']:
                    # Get database metric type
                    hk_type = self._get_database_metric_type(metric_name)
                    if hk_type:
                        # Convert display value back to raw value for record checking
                        raw_value = stats['value']
                        if metric_name == "DistanceWalkingRunning":
                            raw_value = raw_value * 1000  # Convert km back to meters
                        elif metric_name in ["AppleExerciseTime", "MindfulSession"]:
                            raw_value = raw_value * 60  # Convert minutes back to seconds
                            
                        records_found = self.personal_records.check_for_records(
                            hk_type,
                            raw_value,
                            self._current_date
                        )
                        is_record = len(records_found) > 0
                        if is_record:
                            records.append(metric_name)
        
        return records
    
    def _update_timeline(self):
        """Update the activity timeline."""
        if not self.daily_calculator and not self.health_db and not self.cached_data_access:
            logger.debug("No data access available for timeline update")
            return
            
        # Check if timeline widget exists and is visible
        if not hasattr(self, 'timeline'):
            logger.warning("Timeline widget not initialized yet")
            return
            
        if not self.timeline.isVisible():
            return  # Skip update if not visible
            
        try:
            # Map display names to database metric types
            metric_mapping = {
                'StepCount': 'steps',
                'HeartRate': 'heart_rate', 
                'ActiveEnergyBurned': 'active_calories'
            }
            
            timeline_data = {}
            available_metrics = []
            
            # Collect data for each metric
            for db_metric, display_name in metric_mapping.items():
                # Use the database metric type to get hourly data
                hourly_data = self._get_hourly_data(db_metric)
                if hourly_data is not None and not hourly_data.empty:
                    # Create datetime index for the current date
                    hourly_data['datetime'] = pd.to_datetime(
                        self._current_date.strftime('%Y-%m-%d') + ' ' + 
                        hourly_data['hour'].astype(str).str.zfill(2) + ':00:00'
                    )
                    hourly_data = hourly_data.set_index('datetime')
                    # Use display name for the timeline
                    timeline_data[display_name] = hourly_data['value']
                    available_metrics.append(display_name)
                    logger.debug(f"Added {display_name} to timeline with {len(hourly_data)} hours of data")
            
            # Create combined DataFrame if we have any data
            if timeline_data:
                combined_df = pd.DataFrame(timeline_data)
                # Fill missing hours with 0 for better visualization
                # Create full 24-hour index
                full_index = pd.date_range(
                    start=f"{self._current_date} 00:00:00",
                    end=f"{self._current_date} 23:00:00",
                    freq='h'
                )
                combined_df = combined_df.reindex(full_index, fill_value=0)
                
                logger.info(f"Timeline DataFrame shape: {combined_df.shape}")
                logger.info(f"Timeline columns: {combined_df.columns.tolist()}")
                logger.info(f"Timeline index range: {combined_df.index.min()} to {combined_df.index.max()}")
                logger.info(f"Updating timeline with {len(available_metrics)} metrics and {len(combined_df)} time points")
                
                # Update timeline with proper method and data format
                self.timeline.update_data(combined_df, available_metrics)
            else:
                logger.warning("No timeline data available for current date")
                # Clear timeline if no data
                self.timeline.update_data(pd.DataFrame(), [])
                
        except Exception as e:
            logger.error(f"Error updating timeline: {e}", exc_info=True)
    
    def _get_hourly_data(self, metric_tuple) -> Optional[pd.DataFrame]:
        """Get hourly data for a metric with caching."""
        if not self.daily_calculator and not self.health_db:
            return None
            
        # Handle both old format (string) and new format (tuple)
        if isinstance(metric_tuple, str):
            metric_name = metric_tuple
            source = None
        else:
            metric_name, source = metric_tuple
            
        # Check cache
        cache_key = f"hourly_{metric_name}_{source}_{self._current_date}"
        if hasattr(self, '_hourly_cache') and cache_key in self._hourly_cache:
            return self._hourly_cache[cache_key]
            
        try:
            # Get database metric type
            hk_type = self._get_database_metric_type(metric_name)
            if not hk_type:
                return None
            
            hourly = None
            
            if source and self.health_db:
                # Get source-specific hourly data from database
                db = self.health_db.db_manager
                query = """
                    SELECT 
                        CAST(strftime('%H', startDate) AS INTEGER) as hour,
                        SUM(CAST(value AS FLOAT)) as hourly_total
                    FROM health_records
                    WHERE type = ?
                    AND DATE(startDate) = ?
                    AND sourceName = ?
                    AND value IS NOT NULL
                    GROUP BY hour
                    ORDER BY hour
                """
                
                result = db.execute_query(query, (hk_type, self._current_date.isoformat(), source))
                
                if result:
                    hourly = pd.DataFrame(result, columns=['hour', 'value'])
                    # Convert values for display
                    hourly['value'] = hourly['value'].apply(lambda x: self._convert_value_for_display(x, metric_name))
                else:
                    return None
                    
            elif self.daily_calculator and hasattr(self.daily_calculator, 'data'):
                # Use calculator data for aggregated metrics
                # Filter data for current date and metric
                mask = (self.daily_calculator.data['type'] == hk_type) & \
                       (pd.to_datetime(self.daily_calculator.data['creationDate']).dt.date == self._current_date)
                data = self.daily_calculator.data.loc[mask].copy()
                
                if data.empty:
                    return None
                
                # Group by hour
                data['hour'] = pd.to_datetime(data['creationDate']).dt.hour
                hourly = data.groupby('hour')['value'].sum().reset_index()
                
                # Convert values for display
                hourly['value'] = hourly['value'].apply(lambda x: self._convert_value_for_display(x, metric_name))
            
            if hourly is not None and not hourly.empty:
                # Only fill hours with actual data range
                min_hour = hourly['hour'].min()
                max_hour = hourly['hour'].max()
                hour_range = pd.DataFrame({'hour': range(min_hour, max_hour + 1)})
                hourly = hour_range.merge(hourly, on='hour', how='left').fillna(0)
                
                # Cache result
                if not hasattr(self, '_hourly_cache'):
                    self._hourly_cache = {}
                self._hourly_cache[cache_key] = hourly
                
                return hourly
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting hourly data: {e}")
            return None
    
    def _populate_detail_selector(self):
        """Populate the detail metric selector."""
        # This is now handled by _refresh_metric_combo
        self._refresh_metric_combo()
    
    def _get_database_metric_type(self, clean_metric: str) -> str:
        """Convert a clean metric name to the format stored in the database.
        
        Args:
            clean_metric: Metric name without HK prefix (e.g., 'StepCount')
            
        Returns:
            The metric type as stored in the database
        """
        # First check if the metric exists as-is in the database
        if self.health_db:
            available_types = self.health_db.get_available_types()
            
            # Check if clean name exists directly
            if clean_metric in available_types:
                return clean_metric
                
            # Check with HK prefix for quantities
            hk_quantity = f"HKQuantityTypeIdentifier{clean_metric}"
            if hk_quantity in available_types:
                return hk_quantity
                
            # Check with HK prefix for categories
            hk_category = f"HKCategoryTypeIdentifier{clean_metric}"
            if hk_category in available_types:
                return hk_category
        
        # Default: assume it needs HK prefix based on known category types
        if clean_metric in ["SleepAnalysis", "MindfulSession", "HKDataTypeSleepDurationGoal"]:
            return f"HKCategoryTypeIdentifier{clean_metric}"
        else:
            return f"HKQuantityTypeIdentifier{clean_metric}"
    
    def _get_source_specific_daily_value(self, metric_type: str, date: date, source: str) -> Optional[float]:
        """Get daily aggregate value for a specific metric, date, and source."""
        try:
            # Query the database directly for source-specific data
            if not self.health_db:
                logger.warning("No health database connection available")
                return None
                
            # Use the existing database manager from health_db
            db = self.health_db.db_manager
            
            # Query for sum of values for this metric, date, and source
            query = """
                SELECT SUM(CAST(value AS FLOAT)) as daily_total
                FROM health_records
                WHERE type = ?
                AND DATE(startDate) = ?
                AND sourceName = ?
                AND value IS NOT NULL
            """
            
            result = db.execute_query(query, (metric_type, date.isoformat(), source))
            
            if result and result[0][0] is not None:
                value = float(result[0][0])
                logger.debug(f"Got value {value} for {metric_type} on {date} from {source}")
                return value
            else:
                logger.debug(f"No data found for {metric_type} on {date} from {source}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting source-specific daily value: {e}", exc_info=True)
            return None
    
    def _convert_value_for_display(self, value: float, metric: str) -> float:
        """Convert raw value to display units based on metric type."""
        if metric == "DistanceWalkingRunning":
            return value / 1000  # Convert meters to km
        elif metric == "SleepAnalysis":
            return value / 3600  # Convert seconds to hours
        elif metric == "BodyMass" or metric == "LeanBodyMass":
            return value  # Already in kg
        elif metric == "Height":
            return value * 100  # Convert meters to cm
        elif metric == "WalkingSpeed":
            return value * 3.6  # Convert m/s to km/h
        elif metric == "WalkingStepLength":
            return value * 100  # Convert meters to cm
        elif metric in ["AppleExerciseTime", "MindfulSession"]:
            return value / 60  # Convert seconds to minutes
        elif metric == "DietaryWater":
            return value  # Already in mL
        else:
            return value  # Return as-is for other metrics
    
    def _on_detail_metric_changed(self, index: int):
        """Handle detail metric selection change."""
        if index >= 0:
            metric_tuple = self.detail_metric_selector.itemData(index)
            if metric_tuple:
                self._selected_metric = metric_tuple
                self._update_detail_chart()
                
                # Save preference
                from ..data_access import PreferenceDAO
                try:
                    # Save the metric selection preference
                    PreferenceDAO.set_preference('daily_selected_metric', 
                                              json.dumps(metric_tuple))
                except Exception as e:
                    logger.error(f"Failed to save metric preference: {e}")
    
    def _update_detail_chart(self):
        """Update the detailed metric chart."""
        # Check if required widgets exist
        if not hasattr(self, 'detail_metric_selector') or not hasattr(self, 'detail_chart'):
            logger.warning("Detail chart widgets not initialized yet")
            return
            
        if not self.daily_calculator or not self.detail_metric_selector.count():
            return
            
        try:
            # Get selected metric tuple
            current_index = self.detail_metric_selector.currentIndex()
            if current_index < 0:
                return
                
            metric_tuple = self.detail_metric_selector.itemData(current_index)
            if not metric_tuple:
                return
                
            metric_name, source = metric_tuple
            
            # Defer heavy chart update
            def update_chart():
                hourly_data = self._get_hourly_data(metric_tuple)
                if hourly_data is None or hourly_data.empty:
                    return
                
                # Simplify data - only show hours with data
                hourly_data = hourly_data[hourly_data['value'] > 0]
                
                if hourly_data.empty:
                    return
                
                x_data = hourly_data['hour'].tolist()
                y_data = hourly_data['value'].tolist()
                
                # Update chart
                display_name = self._metric_display_names.get(metric_name, metric_name)
                unit = self._metric_units.get(metric_name, '')
                
                # Add source to title if specific source selected
                if source:
                    title = f"{display_name} ({source}) - Today"
                else:
                    title = f"{display_name} - Today"
                    
                self.detail_chart.set_labels(
                    title=title,
                    x_label="Hour",
                    y_label=unit if unit else 'Value'
                )
                
                # Prepare data points for LineChart
                data_points = [
                    {'x': i, 'y': y, 'label': f"{x}:00"}
                    for i, (x, y) in enumerate(zip(x_data, y_data))
                ]
                
                # Set y-range based on data
                if y_data:
                    y_min = min(y_data) * 0.9
                    y_max = max(y_data) * 1.1
                    self.detail_chart.set_y_range(y_min, y_max)
                
                self.detail_chart.set_data(data_points)
            
            # Run update in next event loop iteration
            QTimer.singleShot(0, update_chart)
            
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
        try:
            self._current_date = date.today()
            self.today_btn.setEnabled(False)
            self._update_date_display()
            self._refresh_data()
            self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error navigating to today: {e}", exc_info=True)
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate to today: {e}")
    
    def _go_to_previous_day(self):
        """Navigate to the previous day."""
        try:
            self._current_date = self._current_date - timedelta(days=1)
            self._update_date_display()
            self._refresh_data()
            self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error navigating to previous day: {e}", exc_info=True)
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate to previous day: {e}")
    
    def _go_to_next_day(self):
        """Navigate to the next day."""
        try:
            if self._current_date < date.today():
                self._current_date = self._current_date + timedelta(days=1)
                self._update_date_display()
                self._refresh_data()
                self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error navigating to next day: {e}", exc_info=True)
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate to next day: {e}")
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        from PyQt6.QtCore import Qt
        
        if event.key() == Qt.Key.Key_Left:
            self._go_to_previous_day()
        elif event.key() == Qt.Key.Key_Right:
            self._go_to_next_day()
        elif event.key() == Qt.Key.Key_Home:
            self._go_to_today()
        else:
            super().keyPressEvent(event)
    
    def _update_date_display(self):
        """Update the date display labels."""
        # Update title
        if self._current_date == date.today():
            title_text = "Today's Summary"
        else:
            title_text = self._current_date.strftime("%A")
        
        if hasattr(self, 'date_label'):
            self.date_label.setText(title_text)
        
        # Update relative date
        relative_text = self._get_relative_date_text()
        if hasattr(self, 'relative_date_label'):
            self.relative_date_label.setText(relative_text)
        
        # Update date picker without triggering signal
        if hasattr(self, 'date_picker'):
            from PyQt6.QtCore import QDate
            self.date_picker.blockSignals(True)
            self.date_picker.setDate(QDate(self._current_date))
            self.date_picker.blockSignals(False)
        
        # Update navigation buttons
        if hasattr(self, 'today_btn'):
            self.today_btn.setEnabled(self._current_date != date.today())
        if hasattr(self, 'next_day_btn'):
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
        try:
            self._current_date = self._current_date - timedelta(days=1)
            self._update_date_display()
            self._refresh_data()
            self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error navigating to previous day: {e}", exc_info=True)
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate to previous day: {e}")
    
    def _go_to_next_day(self):
        """Navigate to the next day."""
        try:
            if self._current_date < date.today():
                self._current_date = self._current_date + timedelta(days=1)
                self._update_date_display()
                self._refresh_data()
                self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error navigating to next day: {e}", exc_info=True)
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate to next day: {e}")
    
    def _on_date_picked(self, qdate):
        """Handle date selection from the date picker."""
        try:
            new_date = qdate.toPyDate()
            if new_date != self._current_date and new_date <= date.today():
                self._current_date = new_date
                self._update_date_display()
                self._refresh_data()
                self.date_changed.emit(self._current_date)
        except Exception as e:
            logger.error(f"Error handling date selection: {e}", exc_info=True)
            QMessageBox.warning(self, "Date Selection Error", f"Failed to change date: {e}")
    
    def _refresh_data(self):
        """Refresh all data displays."""
        logger.info(f"Refreshing daily dashboard data for {self._current_date}")
        
        # Check if calculator is available
        if not self.daily_calculator:
            logger.debug("No daily calculator available, skipping refresh")
            self._show_no_data_message()
            return
            
        # For immediate response, update directly if no pending update
        if not self._pending_update:
            # Clear cache if date changed
            if self._cache_date != self._current_date:
                self._stats_cache.clear()
                self._cache_date = self._current_date
                if hasattr(self, '_hourly_cache'):
                    self._hourly_cache.clear()
            # Load data immediately
            self._load_daily_data()
        else:
            # Use debounced update if already pending
            self._pending_update = True
            self._update_timer.stop()
            self._update_timer.start(50)  # Reduced to 50ms for better responsiveness
    
    def _perform_delayed_update(self):
        """Perform the actual update after debounce delay."""
        if self._pending_update:
            self._pending_update = False
            logger.info(f"Performing delayed update for {self._current_date}")
            
            # Check if data access is available
            if not self.daily_calculator and not self.cached_data_access and not self.health_db:
                logger.debug("No data access available for delayed update")
                self._show_no_data_message()
                return
                
            # Clear cache when date changes
            if self._cache_date != self._current_date:
                self._stats_cache.clear()
                self._cache_date = self._current_date
                if hasattr(self, '_hourly_cache'):
                    self._hourly_cache.clear()
            # Then reload data
            self._load_daily_data()
    
    def _on_metric_card_clicked(self, metric_name: str):
        """Handle metric card click."""
        # Find the first matching metric tuple with this metric type
        selected_tuple = None
        for metric_tuple in self._available_metrics:
            if metric_tuple[0] == metric_name:
                selected_tuple = metric_tuple
                break
                
        if selected_tuple:
            self._selected_metric = selected_tuple
            
            # Update detail selector
            for i in range(self.detail_metric_selector.count()):
                if self.detail_metric_selector.itemData(i) == selected_tuple:
                    self.detail_metric_selector.setCurrentIndex(i)
                    break
        
        self.metric_selected.emit(metric_name)
    
    def set_daily_calculator(self, calculator: DailyMetricsCalculator):
        """Set the daily metrics calculator."""
        logger.info("Setting daily calculator")
        self.daily_calculator = calculator
        
        # Clear caches when calculator changes
        self._stats_cache.clear()
        self._cache_date = None
        if hasattr(self, '_hourly_cache'):
            self._hourly_cache.clear()
        
        # Clear any existing metric cards before creating new ones
        self._metric_cards.clear()
        self._available_metrics = []
        
        # Prepare data for DayOfWeekAnalyzer
        if calculator and hasattr(calculator, 'data'):
            logger.info(f"Calculator has data with {len(calculator.data)} records")
            # Skip DayOfWeekAnalyzer for now to improve performance
            self.day_analyzer = None
        else:
            logger.warning("Calculator has no data attribute")
            self.day_analyzer = None
            
        # Hide any existing no data message
        self._hide_no_data_message()
        
        # Detect metrics and load data immediately
        self._detect_available_metrics()
        self._refresh_metric_combo()
        self._load_daily_data()
    
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
        # Create overlay if it doesn't exist
        if not hasattr(self, 'no_data_overlay') or not hasattr(self, 'no_data_message'):
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
        # For now, just log the error and show a simple message box
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error Loading Data", f"Failed to load daily data:\n{error}")
    
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
        # Clear any leftover content from other tabs
        self._hide_no_data_message()
        # Force immediate refresh when widget is shown
        if self.daily_calculator or self.cached_data_access or self.health_db:
            # Clear cache to ensure fresh data
            self._stats_cache.clear()
            if hasattr(self, '_hourly_cache'):
                self._hourly_cache.clear()
            # Detect available metrics
            self._detect_available_metrics()
            self._refresh_metric_combo()
            # Load data immediately
            self._load_daily_data()
        else:
            self._show_no_data_message()
    
    def _delayed_refresh(self):
        """Delayed refresh to ensure complete rendering."""
        # Force full refresh of all visible widgets
        if hasattr(self, 'timeline') and self.timeline.isVisible():
            self.timeline.update()
        if hasattr(self, 'detail_chart') and self.detail_chart.isVisible():
            self.detail_chart.update()
        # Update all metric cards
        for card in self._metric_cards.values():
            if card.isVisible():
                card.update()