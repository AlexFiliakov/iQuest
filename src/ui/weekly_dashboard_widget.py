"""
Weekly dashboard widget for viewing weekly health metrics and trends.

This widget provides comprehensive weekly health data analysis including:
- 7-day rolling statistics
- Week-over-week comparisons
- Weekly patterns and trends
- Day-of-week analysis
- Volatility scoring
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QGroupBox, QButtonGroup, QRadioButton
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
from ..health_database import HealthDatabase

logger = get_logger(__name__)


class WeeklyStatCard(QFrame):
    """Statistical card for weekly metrics."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the card UI."""
        self.setFixedHeight(100)
        from .style_manager import StyleManager
        style_manager = StyleManager()
        shadow = style_manager.get_shadow_style('md')
        
        self.setStyleSheet(f"""
            WeeklyStatCard {{
                background-color: {style_manager.PRIMARY_BG};
                border: {shadow['border']};
                border-radius: 8px;
                padding: 16px;
            }}
            WeeklyStatCard:hover {{
                background-color: {style_manager.PRIMARY_BG};
                border: 1px solid {style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFont(QFont('Segoe UI Emoji', 14))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont('Inter', 11))
        title_label.setStyleSheet(f"color: {style_manager.TEXT_SECONDARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Main value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont('Inter', 20, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {style_manager.ACCENT_PRIMARY};")
        layout.addWidget(self.value_label)
        
        # Sub-label
        self.sub_label = QLabel("")
        self.sub_label.setFont(QFont('Inter', 10))
        self.sub_label.setStyleSheet(f"color: {style_manager.TEXT_MUTED};")
        layout.addWidget(self.sub_label)
        
    def update_value(self, value: str, sub_label: str = ""):
        """Update the displayed values."""
        self.value_label.setText(value)
        self.sub_label.setText(sub_label)
        self.update()  # Force repaint


class WeeklyDashboardWidget(QWidget):
    """
    Weekly dashboard widget showing 7-day rolling statistics and trends.
    
    Features:
    - Week-at-a-glance summary
    - Week-over-week comparisons
    - Day-of-week patterns
    - Trend analysis
    - Best/worst day tracking
    - Volatility scoring
    """
    
    # Signals
    week_changed = pyqtSignal(date, date)  # start_date, end_date
    metric_selected = pyqtSignal(str)  # Emits just the metric type for compatibility
    metric_changed = pyqtSignal(str)  # Alias for compatibility
    
    def __init__(self, weekly_calculator=None, daily_calculator=None, parent=None):
        """Initialize the weekly dashboard widget."""
        super().__init__(parent)
        
        # Support both old calculators and new cached access
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator
        self.cached_data_access = None
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(daily_calculator.data if hasattr(daily_calculator, 'data') else daily_calculator) if daily_calculator else None
        
        # Try to initialize HealthDatabase
        try:
            self.health_db = HealthDatabase()
        except Exception as e:
            logger.error(f"Failed to initialize HealthDatabase: {e}")
            self.health_db = None
        
        # Calculate current week boundaries
        today = date.today()
        self._current_week_start = today - timedelta(days=today.weekday())  # Monday
        self._current_week_end = self._current_week_start + timedelta(days=6)  # Sunday
        
        self._available_metrics = []  # List of (metric_type, source) tuples
        self._current_metric = ("StepCount", None)  # Default to aggregated steps
        
        self._setup_ui()
        self._setup_connections()
        
        # Update week labels
        self._update_week_labels()
        
        # Load initial data
        if self.weekly_calculator:
            self._detect_available_metrics()
            if self._available_metrics:
                self._load_weekly_data()
        else:
            # Show no data message if no calculator
            self._show_no_data_message()
    
    def set_cached_data_access(self, cached_access):
        """Set the cached data access for performance optimization.
        
        Args:
            cached_access: CachedDataAccess instance for reading pre-computed summaries
        """
        self.cached_data_access = cached_access
        # Reload data with new access method
        if cached_access:
            self._detect_available_metrics()
            if self._available_metrics:
                self._load_weekly_data()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollArea > QWidget > QWidget {
                background-color: white;
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
        content_widget.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Weekly summary section
        summary_section = self._create_summary_section()
        content_layout.addWidget(summary_section)
        
        # Week-over-week comparison
        wow_section = self._create_wow_section()
        content_layout.addWidget(wow_section)
        
        # Day patterns section
        patterns_section = self._create_patterns_section()
        content_layout.addWidget(patterns_section)
        
        # Detailed charts section
        charts_section = self._create_charts_section()
        content_layout.addWidget(charts_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_header(self) -> QWidget:
        """Create the dashboard header with week navigation."""
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
        
        # Week navigation
        nav_layout = QHBoxLayout()
        
        # Previous week button
        self.prev_week_btn = QPushButton("◀")
        self.prev_week_btn.setFixedSize(40, 40)
        self.prev_week_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #E8DCC8;
                border-radius: 20px;
                color: #5D4E37;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border-color: #FF8C42;
                color: #FF8C42;
            }
        """)
        self.prev_week_btn.setToolTip("Previous week")
        nav_layout.addWidget(self.prev_week_btn)
        
        # Week label
        week_layout = QVBoxLayout()
        
        self.week_label = QLabel()
        self.week_label.setFont(QFont('Poppins', 18, QFont.Weight.Bold))
        self.week_label.setStyleSheet("color: #5D4E37;")
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.week_label)
        
        self.date_range_label = QLabel()
        self.date_range_label.setFont(QFont('Inter', 12))
        self.date_range_label.setStyleSheet("color: #8B7355;")
        self.date_range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self.date_range_label)
        
        nav_layout.addLayout(week_layout)
        
        # Next week button
        self.next_week_btn = QPushButton("▶")
        self.next_week_btn.setFixedSize(40, 40)
        self.next_week_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #E8DCC8;
                border-radius: 20px;
                color: #5D4E37;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
                border-color: #FF8C42;
                color: #FF8C42;
            }
        """)
        self.next_week_btn.setToolTip("Next week")
        nav_layout.addWidget(self.next_week_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # This week button
        self.this_week_btn = QPushButton("This Week")
        self.this_week_btn.setFixedSize(100, 40)
        self.this_week_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: rgba(255, 140, 66, 0.5);
            }
        """)
        layout.addWidget(self.this_week_btn)
        
        self._update_week_labels()
        
        return header
    
    def _create_summary_section(self) -> QWidget:
        """Create the weekly summary section."""
        section = QGroupBox("Week at a Glance")
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
        layout.setSpacing(16)
        
        # Metric selector
        selector_layout = QHBoxLayout()
        
        metric_label = QLabel("Metric:")
        metric_label.setFont(QFont('Inter', 12))
        metric_label.setStyleSheet("color: #5D4E37;")
        selector_layout.addWidget(metric_label)
        
        self.metric_selector = QComboBox()
        self.metric_selector.setMinimumWidth(200)
        self.metric_selector.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid rgba(139, 115, 85, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: Poppins;
                color: #5D4E37;
            }
        """)
        selector_layout.addWidget(self.metric_selector)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Statistics cards grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Create stat cards
        self.stat_cards = {
            'average': WeeklyStatCard("Weekly Average", "📊"),
            'total': WeeklyStatCard("Weekly Total", "Σ"),
            'best': WeeklyStatCard("Best Day", "🏆"),
            'worst': WeeklyStatCard("Worst Day", "📉"),
            'trend': WeeklyStatCard("Trend", "📈"),
            'volatility': WeeklyStatCard("Volatility", "📊")
        }
        
        # Arrange cards in grid
        positions = [
            ('average', 0, 0), ('total', 0, 1), ('best', 0, 2),
            ('worst', 1, 0), ('trend', 1, 1), ('volatility', 1, 2)
        ]
        
        for key, row, col in positions:
            stats_grid.addWidget(self.stat_cards[key], row, col)
        
        layout.addLayout(stats_grid)
        
        return section
    
    def _create_wow_section(self) -> QWidget:
        """Create the week-over-week comparison section."""
        section = QGroupBox("Week-over-Week Comparison")
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
        
        # WoW widget
        self.wow_widget = WeekOverWeekWidget()
        self.wow_widget.setMinimumHeight(300)
        layout.addWidget(self.wow_widget)
        
        return section
    
    def _create_patterns_section(self) -> QWidget:
        """Create the day-of-week patterns section."""
        section = QGroupBox("Weekly Patterns")
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
        layout.setSpacing(16)
        
        # Day-of-week chart
        self.dow_chart = BarChartComponent()
        self.dow_chart.setMinimumHeight(250)
        
        # Configure chart styling will be done when plotting
        
        layout.addWidget(self.dow_chart)
        
        # Pattern insights
        self.pattern_label = QLabel("Loading patterns...")
        self.pattern_label.setFont(QFont('Inter', 12))
        self.pattern_label.setStyleSheet("color: #8B7355; padding: 10px;")
        self.pattern_label.setWordWrap(True)
        layout.addWidget(self.pattern_label)
        
        return section
    
    def _create_charts_section(self) -> QWidget:
        """Create the detailed charts section."""
        section = QGroupBox("Weekly Trend")
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
        layout.setSpacing(16)
        
        # View options
        view_layout = QHBoxLayout()
        
        view_label = QLabel("View:")
        view_label.setFont(QFont('Inter', 12))
        view_label.setStyleSheet("color: #5D4E37;")
        view_layout.addWidget(view_label)
        
        # Radio buttons for view selection
        self.view_group = QButtonGroup()
        
        self.daily_view_rb = QRadioButton("Daily Values")
        self.daily_view_rb.setChecked(True)
        self.view_group.addButton(self.daily_view_rb, 0)
        view_layout.addWidget(self.daily_view_rb)
        
        self.cumulative_view_rb = QRadioButton("Cumulative")
        self.view_group.addButton(self.cumulative_view_rb, 1)
        view_layout.addWidget(self.cumulative_view_rb)
        
        self.rolling_view_rb = QRadioButton("7-Day Average")
        self.view_group.addButton(self.rolling_view_rb, 2)
        view_layout.addWidget(self.rolling_view_rb)
        
        view_layout.addStretch()
        layout.addLayout(view_layout)
        
        # Trend chart
        self.trend_chart = LineChart()
        self.trend_chart.setMinimumHeight(300)
        
        # Configure chart
        self.trend_chart.set_labels(title="", x_label="Date", y_label="Value")
        self.trend_chart.show_grid = True
        
        layout.addWidget(self.trend_chart)
        
        return section
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.prev_week_btn.clicked.connect(self._go_to_previous_week)
        self.next_week_btn.clicked.connect(self._go_to_next_week)
        self.this_week_btn.clicked.connect(self._go_to_current_week)
        
        self.metric_selector.currentTextChanged.connect(self._on_metric_changed)
        self.view_group.buttonClicked.connect(self._update_trend_chart)
    
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
                self._refresh_metric_combo()
                return
        
        # Fall back to database if no cached access
        if not self.health_db:
            logger.warning("No data access available - cannot load metrics")
            self._available_metrics = []
            self._refresh_metric_combo()
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
                # Types in the database might already have HK prefix stripped
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
            
            # If no metrics found, log warning but don't use defaults
            if not self._available_metrics:
                logger.warning("No metrics found in database - data may not be loaded or filtered out")
            
            # Sort by display name and source for better UX
            self._available_metrics.sort(key=lambda x: (
                self._metric_display_names.get(x[0], x[0]), 
                x[1] if x[1] else ""  # Put "All Sources" first
            ))
            
            logger.info(f"Loaded {len(self._available_metrics)} metric-source combinations")
            
            # Refresh the metric combo box
            self._refresh_metric_combo()
            
        except Exception as e:
            logger.error(f"Error loading available metrics: {e}", exc_info=True)
            # Don't fall back to defaults - let the UI show "no data" state
            self._available_metrics = []
            self._refresh_metric_combo()
    
    def _refresh_metric_combo(self):
        """Refresh the metric combo box with current available metrics."""
        if not hasattr(self, 'metric_selector'):
            return
            
        # Save current selection
        current_index = self.metric_selector.currentIndex()
        current_data = self.metric_selector.itemData(current_index) if current_index >= 0 else None
        
        # Clear and repopulate
        self.metric_selector.clear()
        logger.info(f"Refreshing combo box with {len(self._available_metrics)} metrics")
        
        if not self._available_metrics:
            # No metrics available - add placeholder
            self.metric_selector.addItem("No metrics available", None)
            self.metric_selector.setEnabled(False)
            logger.warning("No metrics available to display")
            # Clear displays
            self._show_no_data_message()
            return
        
        # Enable combo box if it was disabled
        self.metric_selector.setEnabled(True)
        
        for metric_tuple in self._available_metrics:
            metric, source = metric_tuple
            display_name = self._metric_display_names.get(metric, metric)
            
            # Format display text based on source
            if source:
                display_text = f"{display_name} - {source}"
            else:
                display_text = f"{display_name} (All Sources)"
                
            self.metric_selector.addItem(display_text, metric_tuple)
            logger.debug(f"Added to combo: {display_text}")
        
        # Try to restore saved preference first
        from ..data_access import PreferenceDAO
        saved_metric = PreferenceDAO.get_preference('weekly_selected_metric')
        
        restored = False
        if saved_metric:
            try:
                saved_tuple = tuple(saved_metric)  # JSON already decoded by PreferenceDAO
                if saved_tuple in self._available_metrics:
                    index = self._available_metrics.index(saved_tuple)
                    self.metric_selector.setCurrentIndex(index)
                    self._current_metric = saved_tuple
                    restored = True
                    logger.info(f"Restored saved metric preference: {saved_tuple}")
            except Exception as e:
                logger.error(f"Failed to restore metric preference: {e}")
        
        # If preference wasn't restored, fall back to existing logic
        if not restored:
            # Restore selection if possible
            if current_data and current_data in self._available_metrics:
                index = self._available_metrics.index(current_data)
                self.metric_selector.setCurrentIndex(index)
            elif self._current_metric in self._available_metrics:
                index = self._available_metrics.index(self._current_metric)
                self.metric_selector.setCurrentIndex(index)
            else:
                # Default to first metric
                self.metric_selector.setCurrentIndex(0)
                if self._available_metrics:
                    self._current_metric = self._available_metrics[0]
    
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
        logger.info("Loading weekly data...")
        
        if not self.weekly_calculator and not self.cached_data_access:
            logger.warning("No data access available - showing no data message")
            self._show_no_data_message()
            return
            
        try:
            # Hide no data message first
            self._hide_no_data_message()
            
            # Get selected metric
            if not hasattr(self, '_current_metric') or not self._current_metric:
                logger.warning("No metric selected")
                return
            
            # Extract metric type and source from tuple
            metric_type, source = self._current_metric
            logger.info(f"Loading data for metric: {metric_type}, source: {source}")
            
            # Calculate weekly statistics
            self._update_summary_stats(metric_type, source)
            
            # Update week-over-week comparison
            self._update_wow_comparison(metric_type, source)
            
            # Update day-of-week patterns
            self._update_dow_patterns(metric_type, source)
            
            # Update trend chart
            self._update_trend_chart()
            
            # Force UI update
            self.update()
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
        except Exception as e:
            logger.error(f"Error loading weekly data: {e}", exc_info=True)
            # Show error to user
            self._show_no_data_message()
    
    def _get_source_specific_daily_value(self, metric_type: str, target_date: date, source: Optional[str] = None) -> Optional[float]:
        """Get daily value for a specific metric and source.
        
        Args:
            metric_type: The metric type (e.g., 'StepCount')
            target_date: The date to get value for
            source: The specific source name (e.g., 'iPhone') or None for all sources
            
        Returns:
            Daily value or None if not found
        """
        try:
            # Import DatabaseManager to execute queries
            from ..database import DatabaseManager
            db = DatabaseManager()
            
            # Query the database directly for source-specific data
            query = """
                SELECT SUM(value) as total_value
                FROM health_records
                WHERE type = ? 
                AND DATE(creationDate) = ?
            """
            params = [metric_type, target_date.isoformat()]
            
            if source:
                query += " AND sourceName = ?"
                params.append(source)
                
            result = db.execute_query(query, params)
            if result and result[0]['total_value'] is not None:
                return float(result[0]['total_value'])
        except Exception as e:
            logger.error(f"Error getting source-specific daily value: {e}")
            
        return None

    def _get_weekly_data_from_cache(self, metric_type: str, week_start: date, source: Optional[str] = None):
        """Get weekly data from cache or calculator.
        
        Args:
            metric_type: The metric type
            week_start: Start date of the week
            source: Optional source name for filtering
        
        Returns a dict with daily_values and summary stats.
        """
        # Create ISO week string for cache lookup
        iso_week = week_start.strftime('%Y-W%U')
        
        if self.cached_data_access and not source:
            # Try to get from cache only for aggregated data (no source specified)
            logger.info(f"Getting cached weekly data for {metric_type} week {iso_week}")
            summary = self.cached_data_access.get_weekly_summary(metric_type, iso_week)
            
            if summary:
                # Also get daily values for the week
                daily_values = {}
                for i in range(7):
                    day = week_start + timedelta(days=i)
                    daily_summary = self.cached_data_access.get_daily_summary(metric_type, day)
                    if daily_summary:
                        daily_values[day] = daily_summary.get('sum', 0)
                
                # Convert to expected format
                from types import SimpleNamespace
                return SimpleNamespace(
                    avg=summary.get('daily_avg', 0),
                    total=summary.get('sum', 0),
                    daily_values=daily_values,
                    days_with_data=summary.get('days_with_data', len(daily_values)),
                    trend_direction=summary.get('trend_direction', 'stable')
                )
        
        # For source-specific data or when cache misses, calculate directly
        if source and self.health_db:
            # Get daily values for source-specific data
            daily_values = {}
            for i in range(7):
                day = week_start + timedelta(days=i)
                value = self._get_source_specific_daily_value(metric_type, day, source)
                if value is not None:
                    daily_values[day] = value
                    
            if daily_values:
                values = list(daily_values.values())
                total = sum(values)
                avg = total / 7  # Weekly average (7 days)
                
                # Determine trend
                if len(values) >= 3:
                    first_half = sum(values[:len(values)//2])
                    second_half = sum(values[len(values)//2:])
                    trend_direction = "up" if second_half > first_half else "down" if second_half < first_half else "stable"
                else:
                    trend_direction = "stable"
                
                from types import SimpleNamespace
                return SimpleNamespace(
                    avg=avg,
                    total=total,
                    daily_values=daily_values,
                    days_with_data=len(daily_values),
                    trend_direction=trend_direction
                )
        
        # Fallback to calculator
        if self.weekly_calculator and not source:
            data = self.weekly_calculator.daily_calculator.data.copy()
            if 'startDate' in data.columns and 'creationDate' not in data.columns:
                data['creationDate'] = data['startDate']
            
            week_start_datetime = datetime.combine(week_start, datetime.min.time())
            return self.weekly_calculator.calculate_weekly_metrics(
                data=data,
                metric_type=metric_type,
                week_start=week_start_datetime
            )
        
        return None
    
    def _update_summary_stats(self, metric_type: str, source: Optional[str] = None):
        """Update the summary statistics cards."""
        logger.info(f"Updating summary stats for metric: {metric_type}, source: {source}")
        try:
            # Get weekly data
            logger.info(f"Getting weekly metrics for week starting: {self._current_week_start}")
            
            weekly_data = self._get_weekly_data_from_cache(metric_type, self._current_week_start, source)
            
            if not weekly_data:
                logger.warning(f"No weekly data found for metric: {metric_type}, source: {source}")
                return
            
            logger.info(f"Got weekly data: avg={weekly_data.avg}, days={len(weekly_data.daily_values)}")
            
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
                    best_date.strftime("%a")
                )
                
                self.stat_cards['worst'].update_value(
                    f"{weekly_data.daily_values[worst_date]:,.0f}",
                    worst_date.strftime("%a")
                )
            
            # Update trend
            trend_symbol = "↑" if weekly_data.trend_direction == "up" else "↓" if weekly_data.trend_direction == "down" else "→"
            self.stat_cards['trend'].update_value(
                trend_symbol,
                weekly_data.trend_direction
            )
            
            # Calculate volatility
            if weekly_data.daily_values:
                values = list(weekly_data.daily_values.values())
                if len(values) > 1:
                    volatility = np.std(values) / np.mean(values) * 100 if np.mean(values) > 0 else 0
                    self.stat_cards['volatility'].update_value(
                        f"{volatility:.1f}%",
                        "coefficient of variation"
                    )
            
            # Force UI update
            self.update()
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            logger.info("Summary stats updated successfully")
                    
        except Exception as e:
            logger.error(f"Error updating summary stats: {e}", exc_info=True)
    
    def _update_wow_comparison(self, metric_type: str, source: Optional[str] = None):
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
    
    def _update_dow_patterns(self, metric_type: str, source: Optional[str] = None):
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
                df['Color'] = ['#FF8C42' if i < 5 else '#FFD166' for i in range(7)]  # Weekday vs weekend colors
                
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
        try:
            # Get the current metric tuple from the selector
            current_index = self.metric_selector.currentIndex()
            if current_index < 0:
                return
                
            metric_tuple = self.metric_selector.itemData(current_index)
            if not metric_tuple:
                return
                
            metric_type, source = metric_tuple
            logger.info(f"Updating trend chart for metric: {metric_type}, source: {source}")
            
            # Get daily data for the week
            start_date = self._current_week_start
            end_date = self._current_week_end
            
            # Get data based on view selection
            view_id = self.view_group.checkedId()
            
            if view_id == 0:  # Daily values
                if source and self.health_db:
                    # Get source-specific daily values
                    daily_values = []
                    dates = []
                    for i in range(7):
                        day = start_date + timedelta(days=i)
                        value = self._get_source_specific_daily_value(metric_type, day, source)
                        if value is not None:
                            daily_values.append(value)
                            dates.append(day)
                        else:
                            daily_values.append(0)  # Use 0 for missing days
                            dates.append(day)
                    
                    if any(v > 0 for v in daily_values):
                        x_data = [d.strftime("%a") for d in dates]
                        y_data = daily_values
                        # Prepare data points for LineChart
                        data_points = [
                            {'x': i, 'y': y, 'label': x}
                            for i, (x, y) in enumerate(zip(x_data, y_data))
                        ]
                        
                        # Set y-range
                        non_zero_values = [v for v in y_data if v > 0]
                        if non_zero_values:
                            y_min = min(non_zero_values) * 0.9
                            y_max = max(non_zero_values) * 1.1
                            self.trend_chart.set_y_range(y_min, y_max)
                        
                        self.trend_chart.set_data(data_points)
                elif self.weekly_calculator:
                    # Use calculator for aggregated data
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
                if source and self.health_db:
                    # Get source-specific cumulative values
                    daily_values = []
                    dates = []
                    cumulative_sum = 0
                    for i in range(7):
                        day = start_date + timedelta(days=i)
                        value = self._get_source_specific_daily_value(metric_type, day, source)
                        if value is not None:
                            cumulative_sum += value
                        daily_values.append(cumulative_sum)
                        dates.append(day)
                    
                    x_data = [d.strftime("%a") for d in dates]
                    y_data = daily_values
                    # Prepare data points for LineChart
                    data_points = [
                        {'x': i, 'y': y, 'label': x}
                        for i, (x, y) in enumerate(zip(x_data, y_data))
                    ]
                    
                    # Set y-range
                    if y_data and max(y_data) > 0:
                        y_min = 0  # Cumulative starts at 0
                        y_max = max(y_data) * 1.1
                        self.trend_chart.set_y_range(y_min, y_max)
                    
                    self.trend_chart.set_data(data_points)
                elif self.weekly_calculator:
                    # Use calculator for aggregated data
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
                if source and self.health_db:
                    # Get extended data for rolling average
                    extended_start = start_date - timedelta(days=6)
                    all_values = []
                    all_dates = []
                    
                    # Get 13 days of data (6 before + 7 week days)
                    for i in range(13):
                        day = extended_start + timedelta(days=i)
                        value = self._get_source_specific_daily_value(metric_type, day, source)
                        all_values.append(value if value is not None else 0)
                        all_dates.append(day)
                    
                    # Calculate rolling average for the week
                    rolling_values = []
                    dates = []
                    for i in range(6, 13):  # Week days only
                        window_values = [v for v in all_values[i-6:i+1] if v > 0]
                        if window_values:
                            rolling_values.append(sum(window_values) / len(window_values))
                        else:
                            rolling_values.append(0)
                        dates.append(all_dates[i])
                    
                    if any(v > 0 for v in rolling_values):
                        x_data = [d.strftime("%a") for d in dates]
                        y_data = rolling_values
                        # Prepare data points for LineChart
                        data_points = [
                            {'x': i, 'y': y, 'label': x}
                            for i, (x, y) in enumerate(zip(x_data, y_data))
                        ]
                        
                        # Set y-range
                        non_zero_values = [v for v in y_data if v > 0]
                        if non_zero_values:
                            y_min = min(non_zero_values) * 0.9
                            y_max = max(non_zero_values) * 1.1
                            self.trend_chart.set_y_range(y_min, y_max)
                        
                        self.trend_chart.set_data(data_points)
                elif self.weekly_calculator:
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
        from PyQt6.QtCore import Qt
        
        # Create or update no data overlay
        if not hasattr(self, 'no_data_overlay'):
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
            
            self.no_data_overlay = QWidget()
            self.no_data_overlay.setParent(self)
            self.no_data_overlay.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 255, 255, 1.0);
                    border-radius: 12px;
                    border: 1px solid rgba(139, 115, 85, 0.1);
                    margin: 10px;
                }
            """)
            
            overlay_layout = QVBoxLayout(self.no_data_overlay)
            overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Icon
            icon_label = QLabel("📅")
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
        
        # Ensure widgets remain interactive
        self.no_data_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    
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
        # Get the metric tuple from the combo box data
        current_index = self.metric_selector.currentIndex()
        if current_index >= 0:
            metric_tuple = self.metric_selector.itemData(current_index)
            if metric_tuple:
                self._current_metric = metric_tuple
                self._load_weekly_data()
                
                # Save preference
                from ..data_access import PreferenceDAO
                try:
                    # Save the metric selection preference
                    PreferenceDAO.set_preference('weekly_selected_metric', 
                                              json.dumps(self._current_metric))
                except Exception as e:
                    logger.error(f"Failed to save metric preference: {e}")
                
                # Emit just the metric type for compatibility
                self.metric_selected.emit(self._current_metric[0])
                self.metric_changed.emit(self._current_metric[0])
            else:
                # No valid metric selected (e.g., "No metrics available")
                logger.warning("No valid metric selected")
                self._show_no_data_message()
    
    def set_calculators(self, weekly_calculator: WeeklyMetricsCalculator, 
                       daily_calculator=None):
        """Set the calculator instances."""
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = daily_calculator or (
            weekly_calculator.daily_calculator if weekly_calculator else None
        )
        
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(self.daily_calculator.data if hasattr(self.daily_calculator, 'data') else self.daily_calculator) if self.daily_calculator else None
        
        self._detect_available_metrics()
        self._load_weekly_data()
    
    def get_current_week(self) -> Tuple[date, date]:
        """Get the current week's start and end dates."""
        return self._current_week_start, self._current_week_end
    
    def set_weekly_calculator(self, weekly_calculator: WeeklyMetricsCalculator):
        """Set the weekly metrics calculator."""
        logger.info("Setting weekly calculator")
        self.weekly_calculator = weekly_calculator
        self.daily_calculator = weekly_calculator.daily_calculator if weekly_calculator else None
        
        self.wow_analyzer = WeekOverWeekTrends(weekly_calculator) if weekly_calculator else None
        self.dow_analyzer = DayOfWeekAnalyzer(self.daily_calculator.data if hasattr(self.daily_calculator, 'data') else self.daily_calculator) if self.daily_calculator else None
        
        # Detect metrics first
        self._detect_available_metrics()
        
        # Hide no data message
        self._hide_no_data_message()
        
        # Update week labels
        self._update_week_labels()
        
        # Load data after everything is set up
        if self._available_metrics:
            self._load_weekly_data()
        
        # Force UI refresh
        self.update()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def showEvent(self, event):
        """Handle widget show event to ensure UI is refreshed."""
        super().showEvent(event)
        logger.info("Weekly dashboard shown")
        
        # Ensure all widgets are visible
        self._ensure_widgets_visible()
        
        # Force a refresh when the widget is shown
        if self.weekly_calculator:
            logger.info("Weekly calculator available - loading data")
            self._hide_no_data_message()  # Hide overlay if calculator is available
            self._load_weekly_data()
            self.update()
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        else:
            logger.warning("No weekly calculator available on show event")
            self._show_no_data_message()
            
    def _ensure_widgets_visible(self):
        """Ensure all main widgets are visible."""
        # Make sure the main widget is visible
        self.show()
        
        # Make sure stat cards are visible
        if hasattr(self, 'stat_cards'):
            for card in self.stat_cards.values():
                card.show()
        
        # Make sure sections are visible
        if hasattr(self, 'metric_selector'):
            self.metric_selector.show()
            
        # Update geometry
        self.updateGeometry()