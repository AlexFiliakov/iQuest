"""
Monthly dashboard widget containing the calendar heatmap and related components.

This widget provides the monthly view of health metrics with calendar heatmap visualization,
summary statistics, and month navigation controls.
"""

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from ..health_database import HealthDatabase
from ..utils.logging_config import get_logger
from .charts.calendar_heatmap import CalendarHeatmapComponent
from .statistics_widget import StatisticsWidget

logger = get_logger(__name__)


class MonthlyDashboardWidget(QWidget):
    """
    Monthly dashboard widget with calendar heatmap and analytics.
    
    Features:
    - Calendar heatmap visualization
    - Monthly summary statistics
    - Month navigation controls
    - Metric selection dropdown
    - Journal entry integration
    """
    
    # Signals
    month_changed = pyqtSignal(int, int)  # year, month
    metric_changed = pyqtSignal(str)
    
    def __init__(self, monthly_calculator=None, parent=None):
        """Initialize the monthly dashboard widget."""
        print("[MONTHLY_DEBUG] MonthlyDashboardWidget.__init__ starting")
        logger.info("[MONTHLY_DEBUG] Initializing MonthlyDashboardWidget")
        
        try:
            super().__init__(parent)
            print("[MONTHLY_DEBUG] Parent class initialized successfully")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to initialize parent: {e}")
            logger.error(f"Failed to initialize parent: {e}", exc_info=True)
            raise
        
        # Support both old calculator and new cached access
        self.monthly_calculator = monthly_calculator
        self.cached_data_access = None
        
        # Try to initialize HealthDatabase
        print("[MONTHLY_DEBUG] Attempting to initialize HealthDatabase")
        try:
            self.health_db = HealthDatabase()
            print("[MONTHLY_DEBUG] HealthDatabase initialized successfully")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to initialize HealthDatabase: {e}")
            logger.error(f"Failed to initialize HealthDatabase: {e}")
            self.health_db = None
        
        # Always initialize to current date
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Initializing MonthlyDashboardWidget with date: {self._current_month}/{self._current_year}")
        
        # Initialize metric mappings
        self._init_metric_mappings()
        
        # Initialize with empty metrics list
        self._available_metrics = []
        
        # Load available metrics from database
        self._load_available_metrics()
        
        # Don't add default metrics if none are found
        if not self._available_metrics:
            logger.warning("No metrics available in database")
        
        # Set default metric (now a tuple of (metric, source))
        # Try to find StepCount with no source (aggregated)
        default_found = False
        for metric_tuple in self._available_metrics:
            if metric_tuple[0] == "StepCount" and metric_tuple[1] is None:
                self._current_metric = metric_tuple
                default_found = True
                break
        
        if not default_found:
            # Use first available metric
            self._current_metric = self._available_metrics[0] if self._available_metrics else ("StepCount", None)
        
        # Data storage
        self._metric_data = {}
        self._summary_stats = {}
        
        # Try to set up UI with error handling
        try:
            print("[MONTHLY_DEBUG] Setting up UI...")
            self._setup_ui()
            print("[MONTHLY_DEBUG] UI setup complete")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to setup UI: {e}")
            logger.error(f"Failed to setup UI: {e}", exc_info=True)
            self._create_error_ui(f"UI Setup Failed: {str(e)}")
            return
            
        try:
            print("[MONTHLY_DEBUG] Setting up connections...")
            self._setup_connections()
            print("[MONTHLY_DEBUG] Connections setup complete")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to setup connections: {e}")
            logger.error(f"Failed to setup connections: {e}", exc_info=True)
        
        # Refresh combo box to ensure it has latest metrics
        try:
            print("[MONTHLY_DEBUG] Refreshing metric combo...")
            self._refresh_metric_combo()
            print("[MONTHLY_DEBUG] Metric combo refreshed")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to refresh metric combo: {e}")
            logger.error(f"Failed to refresh metric combo: {e}", exc_info=True)
        
        # Load initial data
        try:
            print("[MONTHLY_DEBUG] Loading initial data...")
            self._load_month_data()
            print("[MONTHLY_DEBUG] Initial data loaded")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to load initial data: {e}")
            logger.error(f"Failed to load initial data: {e}", exc_info=True)
            
        print("[MONTHLY_DEBUG] MonthlyDashboardWidget initialization complete")
    
    def set_cached_data_access(self, cached_access):
        """Set the cached data access for performance optimization.
        
        Args:
            cached_access: CachedDataAccess instance for reading pre-computed summaries
        """
        self.cached_data_access = cached_access
        # Reload metrics and data with new access method
        if cached_access:
            self._load_available_metrics()
            self._refresh_metric_combo()
            self._load_month_data()
        
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
            "DietaryFatSaturated": "Saturated Fat",
            "DietaryFatMonounsaturated": "Monounsaturated Fat",
            "DietaryFatPolyunsaturated": "Polyunsaturated Fat",
            "DietaryCholesterol": "Cholesterol",
            "DietaryFiber": "Fiber",
            "DietarySugar": "Sugar",
            "DietarySodium": "Sodium",
            "DietaryPotassium": "Potassium",
            "DietaryCalcium": "Calcium",
            "DietaryIron": "Iron",
            "DietaryVitaminC": "Vitamin C",
            "DietaryWater": "Water",
            
            # Environmental
            "HeadphoneAudioExposure": "Headphone Audio Exposure",
            
            # Mindfulness
            "MindfulSession": "Mindful Minutes",
            
            # Additional metrics from logs
            "HKDataTypeSleepDurationGoal": "Sleep Duration Goal"
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
            "BloodPressureSystolic": "mmHg",
            "BloodPressureDiastolic": "mmHg",
            "BodyMass": "kg",
            "LeanBodyMass": "kg",
            "BodyMassIndex": "",
            "BodyFatPercentage": "%",
            "Height": "cm",
            "WalkingSpeed": "km/h",
            "WalkingStepLength": "cm",
            "WalkingAsymmetryPercentage": "%",
            "WalkingDoubleSupportPercentage": "%",
            "AppleWalkingSteadiness": "%",
            "RespiratoryRate": "breaths/min",
            "VO2Max": "mL/kg/min",
            "SleepAnalysis": "hours",
            "DietaryEnergyConsumed": "kcal",
            "DietaryProtein": "g",
            "DietaryCarbohydrates": "g",
            "DietaryFatTotal": "g",
            "DietaryFatSaturated": "g",
            "DietaryFatMonounsaturated": "g",
            "DietaryFatPolyunsaturated": "g",
            "DietaryCholesterol": "mg",
            "DietaryFiber": "g",
            "DietarySugar": "g",
            "DietarySodium": "mg",
            "DietaryPotassium": "mg",
            "DietaryCalcium": "mg",
            "DietaryIron": "mg",
            "DietaryVitaminC": "mg",
            "DietaryWater": "mL",
            "HeadphoneAudioExposure": "dB",
            "MindfulSession": "min",
            "HKDataTypeSleepDurationGoal": "hours"
        }
        
    def _load_available_metrics(self):
        """Load available metrics from the database with source information."""
        # Try cached data access first
        if self.cached_data_access:
            logger.info("Loading metrics from cache")
            available_types = self.cached_data_access.get_available_metrics()
            available_sources = self.cached_data_access.get_available_sources()
            
            self._available_metrics = []
            
            # Add aggregated and source-specific metrics
            for db_type in available_types:
                # Check if it already exists in our display names
                if db_type in self._metric_display_names:
                    clean_type = db_type
                else:
                    # If not, try stripping HK prefixes
                    clean_type = db_type.replace("HKQuantityTypeIdentifier", "").replace("HKCategoryTypeIdentifier", "")
                
                # Only include metrics we have display names for
                if clean_type in self._metric_display_names:
                    # Add aggregated metric
                    self._available_metrics.append((clean_type, None))
                    logger.debug(f"Added aggregated metric from cache: {clean_type}")
                    
                    # Add source-specific metrics
                    for source in available_sources:
                        self._available_metrics.append((clean_type, source))
                        logger.debug(f"Added metric from cache: {clean_type} - {source}")
            
            if self._available_metrics:
                # Sort by display name, then by source (aggregated first)
                self._available_metrics.sort(key=lambda x: (self._metric_display_names.get(x[0], x[0]), x[1] is not None, x[1] or ''))
                logger.info(f"Loaded {len(self._available_metrics)} metric-source combinations from cache")
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
                # Types in the database might already have HK prefix stripped (based on weekly tab log)
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
            
            # If no metrics found, log warning but don't use defaults
            if not self._available_metrics:
                logger.warning("No metrics found in database - data may not be loaded or filtered out")
            
            # Sort by display name and source for better UX
            self._available_metrics.sort(key=lambda x: (
                self._metric_display_names.get(x[0], x[0]), 
                x[1] if x[1] else ""  # Put "All Sources" first
            ))
            
            logger.info(f"Loaded {len(self._available_metrics)} metric-source combinations")
            
        except Exception as e:
            logger.error(f"Error loading available metrics: {e}", exc_info=True)
            # Don't fall back to defaults - let the UI show "no data" state
            self._available_metrics = []
    
    def _refresh_metric_combo(self):
        """Refresh the metric combo box with current available metrics."""
        if not hasattr(self, 'metric_combo'):
            return
            
        # Save current selection
        current_index = self.metric_combo.currentIndex()
        current_data = self.metric_combo.itemData(current_index) if current_index >= 0 else None
        
        # Clear and repopulate
        self.metric_combo.clear()
        logger.info(f"Refreshing combo box with {len(self._available_metrics)} metrics")
        
        if not self._available_metrics:
            # No metrics available - add placeholder
            self.metric_combo.addItem("No metrics available", None)
            self.metric_combo.setEnabled(False)
            logger.warning("No metrics available to display")
            # Clear the calendar display
            self.calendar_heatmap.set_metric_data("", {})
            self._update_summary_stats({})
            return
        
        # Enable combo box if it was disabled
        self.metric_combo.setEnabled(True)
        
        for metric_tuple in self._available_metrics:
            metric, source = metric_tuple
            display_name = self._metric_display_names.get(metric, metric)
            
            # Format display text based on source
            if source:
                display_text = f"{display_name} - {source}"
            else:
                display_text = f"{display_name} (All Sources)"
                
            self.metric_combo.addItem(display_text, metric_tuple)
            logger.debug(f"Added to combo: {display_text}")
        
        # Try to restore saved preference first
        from ..data_access import PreferenceDAO
        saved_metric = PreferenceDAO.get_preference('monthly_selected_metric')
        
        restored = False
        if saved_metric:
            try:
                saved_tuple = tuple(saved_metric)  # JSON already decoded by PreferenceDAO
                if saved_tuple in self._available_metrics:
                    index = self._available_metrics.index(saved_tuple)
                    self.metric_combo.setCurrentIndex(index)
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
                self.metric_combo.setCurrentIndex(index)
            elif self._current_metric in self._available_metrics:
                index = self._available_metrics.index(self._current_metric)
                self.metric_combo.setCurrentIndex(index)
            
    def _create_error_ui(self, error_message: str):
        """Create an error UI when initialization fails."""
        print(f"[MONTHLY_DEBUG] Creating error UI: {error_message}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Error header
        error_header = QLabel("Monthly Dashboard Error")
        error_header.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #DC3545;
                padding: 20px;
            }
        """)
        error_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_header)
        
        # Error details
        error_frame = QFrame()
        error_frame.setStyleSheet("""
            QFrame {
                background-color: #F8D7DA;
                border: 2px solid #F5C6CB;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        error_layout = QVBoxLayout(error_frame)
        
        error_label = QLabel("Failed to initialize Monthly Dashboard:")
        error_label.setStyleSheet("font-weight: bold; color: #721C24;")
        error_layout.addWidget(error_label)
        
        error_text = QLabel(error_message)
        error_text.setWordWrap(True)
        error_text.setStyleSheet("color: #721C24; padding: 10px;")
        error_layout.addWidget(error_text)
        
        # Suggestions
        suggestions = QLabel(
            "Suggestions:\n"
            "• Check if health data has been imported\n"
            "• Try switching to another tab and back\n"
            "• Check the console for detailed error messages"
        )
        suggestions.setStyleSheet("color: #721C24; padding: 10px;")
        error_layout.addWidget(suggestions)
        
        layout.addWidget(error_frame)
        layout.addStretch()
    
    def _setup_ui(self):
        """Set up the user interface."""
        print("[MONTHLY_DEBUG] _setup_ui called")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        try:
            print("[MONTHLY_DEBUG] Creating header...")
            header = self._create_header()
            main_layout.addWidget(header)
            print("[MONTHLY_DEBUG] Header created and added")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to create header: {e}")
            logger.error(f"Failed to create header: {e}", exc_info=True)
            error_label = QLabel(f"Header Error: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            main_layout.addWidget(error_label)
        
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
                background-color: #F8F9FA;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ADB5BD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6C757D;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Calendar heatmap section
        try:
            print("[MONTHLY_DEBUG] Creating heatmap section...")
            heatmap_section = self._create_heatmap_section()
            content_layout.addWidget(heatmap_section)
            print("[MONTHLY_DEBUG] Heatmap section created")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to create heatmap section: {e}")
            logger.error(f"Failed to create heatmap section: {e}", exc_info=True)
            error_label = QLabel(f"Heatmap Error: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            content_layout.addWidget(error_label)
        
        # Summary statistics section
        stats_section = self._create_statistics_section()
        content_layout.addWidget(stats_section)
        
        # Journal section placeholder
        journal_section = self._create_journal_section()
        content_layout.addWidget(journal_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_header(self) -> QWidget:
        """Create the dashboard header with navigation and controls."""
        print("[MONTHLY_DEBUG] _create_header called")
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
        
        # Month navigation
        nav_layout = QHBoxLayout()
        
        # Previous month button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setStyleSheet(self._get_nav_button_style())
        self.prev_btn.setToolTip("Previous month")
        nav_layout.addWidget(self.prev_btn)
        
        # Current month/year label
        self.month_label = QLabel()
        self.month_label.setFont(QFont('Poppins', 18, QFont.Weight.Bold))
        self.month_label.setStyleSheet("color: #5D4E37; padding: 0 20px;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set fixed width to accommodate longest month name (September) plus year
        # Typical width: "September 2023" with padding
        self.month_label.setFixedWidth(250)
        nav_layout.addWidget(self.month_label)
        
        # Next month button
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet(self._get_nav_button_style())
        self.next_btn.setToolTip("Next month")
        nav_layout.addWidget(self.next_btn)
        
        # Today button
        self.today_btn = QPushButton("Today")
        self.today_btn.setFixedSize(70, 40)
        self.today_btn.setStyleSheet(self._get_nav_button_style())
        self.today_btn.setToolTip("Go to current month")
        nav_layout.addWidget(self.today_btn)
        
        layout.addLayout(nav_layout)
        layout.addStretch()
        
        # Metric selector
        metric_layout = QHBoxLayout()
        
        metric_label = QLabel("Metric:")
        metric_label.setFont(QFont('Inter', 12, QFont.Weight.Medium))
        metric_label.setStyleSheet("color: #5D4E37;")
        metric_layout.addWidget(metric_label)
        
        self.metric_combo = QComboBox()
        # Populate with available metrics from database
        logger.info(f"Populating combo box with {len(self._available_metrics)} metrics")
        for metric_tuple in self._available_metrics:
            metric, source = metric_tuple
            display_name = self._metric_display_names.get(metric, metric)
            
            # Format display text based on source
            if source:
                display_text = f"{display_name} - {source}"
            else:
                display_text = f"{display_name} (All Sources)"
                
            self.metric_combo.addItem(display_text, metric_tuple)  # Display text with source, tuple as data
            logger.debug(f"Added to combo: {display_text}")
        
        # Set current metric
        if self._current_metric in self._available_metrics:
            index = self._available_metrics.index(self._current_metric)
            self.metric_combo.setCurrentIndex(index)
            logger.info(f"Set current metric to: {self._current_metric} at index {index}")
        
        # Ensure combo box is visible
        self.metric_combo.setVisible(True)
        self.metric_combo.setMinimumHeight(40)
            
        self.metric_combo.setStyleSheet(self._get_combo_style())
        metric_layout.addWidget(self.metric_combo)
        
        layout.addLayout(metric_layout)
        
        # Update month label
        self._update_month_label()
        
        return header
        
    def _create_heatmap_section(self) -> QWidget:
        """Create the calendar heatmap section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Header with title and style toggle
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Activity Calendar")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Style toggle buttons
        self.style_button_group = QButtonGroup()
        
        self.classic_btn = QPushButton("Classic")
        self.classic_btn.setCheckable(True)
        self.classic_btn.setChecked(True)
        self.classic_btn.setFixedSize(80, 32)
        self.classic_btn.clicked.connect(lambda: self._set_calendar_style("classic"))
        self.style_button_group.addButton(self.classic_btn)
        
        self.github_btn = QPushButton("GitHub")
        self.github_btn.setCheckable(True)
        self.github_btn.setChecked(False)
        self.github_btn.setFixedSize(80, 32)
        self.github_btn.clicked.connect(lambda: self._set_calendar_style("github"))
        self.style_button_group.addButton(self.github_btn)
        
        # Style the toggle buttons
        toggle_style = """
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 16px;
                color: #5D4E37;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                border-color: #FF8C42;
                background-color: #FFF8F0;
            }
            QPushButton:checked {
                background-color: #FF8C42;
                border-color: #FF8C42;
                color: #FFFFFF;
            }
        """
        
        self.classic_btn.setStyleSheet(toggle_style)
        self.github_btn.setStyleSheet(toggle_style)
        
        header_layout.addWidget(self.classic_btn)
        header_layout.addWidget(self.github_btn)
        
        layout.addLayout(header_layout)
        
        # Calendar heatmap
        try:
            print("[MONTHLY_DEBUG] Creating CalendarHeatmapComponent...")
            self.calendar_heatmap = CalendarHeatmapComponent()
            self.calendar_heatmap.setMinimumHeight(350)  # Reduced minimum height
            print("[MONTHLY_DEBUG] CalendarHeatmapComponent created successfully")
        except Exception as e:
            print(f"[MONTHLY_ERROR] Failed to create CalendarHeatmapComponent: {e}")
            logger.error(f"Failed to create CalendarHeatmapComponent: {e}", exc_info=True)
            # Create placeholder
            self.calendar_heatmap = QLabel("Calendar Heatmap Error")
            self.calendar_heatmap.setStyleSheet("color: red; padding: 20px; background-color: #FFF0F0;")
            self.calendar_heatmap.setMinimumHeight(350)
        # Set to Month Grid view by default for monthly dashboard
        self.calendar_heatmap._view_mode = "month_grid"
        # Hide view mode controls since we want our own toggle
        self.calendar_heatmap.set_show_controls(False)
        layout.addWidget(self.calendar_heatmap)
        
        return section
        
    def _create_statistics_section(self) -> QWidget:
        """Create the summary statistics section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Summary")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Statistics grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Create statistics cards
        self.stats_cards = {}
        stats_info = [
            ("average", "Average", "#FF8C42"),
            ("total", "Total", "#FFD166"),
            ("best_day", "Best Day", "#95C17B"),
            ("trend", "Trend", "#6C9BD1")
        ]
        
        for i, (key, label, color) in enumerate(stats_info):
            card = self._create_stat_card(label, "0", color)
            self.stats_cards[key] = card
            row, col = divmod(i, 2)
            stats_grid.addWidget(card, row, col)
            
        layout.addLayout(stats_grid)
        
        return section
        
    def _create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a summary statistic card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFF8F0;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont('Inter', 12, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #8B7355;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont('Poppins', 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
        
    def _create_journal_section(self) -> QWidget:
        """Create the journal section placeholder."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Monthly Reflection")
        title.setFont(QFont('Poppins', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #5D4E37; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Placeholder content
        placeholder = QLabel("Journal feature coming soon...")
        placeholder.setStyleSheet("color: #A69583; font-style: italic;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)
        
        return section
        
    def _get_nav_button_style(self) -> str:
        """Get navigation button stylesheet."""
        return """
            QPushButton {
                background-color: #FFFFFF;
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
            QPushButton:pressed {
                background-color: #FFE8D1;
            }
        """
        
    def _get_combo_style(self) -> str:
        """Get combobox stylesheet."""
        return """
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 6px;
                padding: 8px 32px 8px 12px;
                color: #5D4E37;
                font-size: 12px;
                min-width: 200px;
                font-family: 'Inter', sans-serif;
            }
            QComboBox:hover {
                border-color: #FF8C42;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #E8DCC8;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #5D4E37;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                selection-background-color: #FFF8F0;
                selection-color: #FF8C42;
                padding: 4px;
            }
        """
        
    def _setup_connections(self):
        """Set up signal connections."""
        # Navigation buttons
        self.prev_btn.clicked.connect(self._go_to_previous_month)
        self.next_btn.clicked.connect(self._go_to_next_month)
        self.today_btn.clicked.connect(self.reset_to_current_month)
        
        # Metric selection
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        
        # Calendar heatmap signals
        if hasattr(self.calendar_heatmap, 'date_clicked'):
            self.calendar_heatmap.date_clicked.connect(self._on_date_clicked)
        if hasattr(self.calendar_heatmap, 'date_range_selected'):
            self.calendar_heatmap.date_range_selected.connect(self._on_date_range_selected)
            
    def _update_month_label(self):
        """Update the month/year label."""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        month_name = month_names[self._current_month - 1]
        self.month_label.setText(f"{month_name} {self._current_year}")
        
    def _go_to_previous_month(self):
        """Navigate to the previous month."""
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
            
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _go_to_next_month(self):
        """Navigate to the next month."""
        # Get current date to prevent navigating to future
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # Calculate next month
        next_year = self._current_year
        next_month = self._current_month + 1
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        # Check if next month is in the future
        if next_year > current_year or (next_year == current_year and next_month > current_month):
            logger.warning(f"Cannot navigate to future month: {next_month}/{next_year}")
            return
            
        self._current_month = next_month
        self._current_year = next_year
            
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _on_metric_changed(self, text: str):
        """Handle metric selection change."""
        # Get the metric tuple from the combo box data
        current_index = self.metric_combo.currentIndex()
        if current_index >= 0:
            metric_tuple = self.metric_combo.itemData(current_index)
            if metric_tuple:
                self._current_metric = metric_tuple
                self._load_month_data()
                
                # Save preference
                from ..data_access import PreferenceDAO
                try:
                    # Save the metric selection preference
                    PreferenceDAO.set_preference('monthly_selected_metric', 
                                              json.dumps(self._current_metric))
                except Exception as e:
                    logger.error(f"Failed to save metric preference: {e}")
                
                # Emit just the metric type for compatibility
                self.metric_changed.emit(self._current_metric[0])
            else:
                # No valid metric selected (e.g., "No metrics available")
                logger.warning("No valid metric selected")
                self.calendar_heatmap.set_metric_data("", {})
                self._update_summary_stats({})
            
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
    
    def _load_month_data(self):
        """Load data for the current month and metric."""
        data = {}
        
        if self.monthly_calculator:
            # Use real data from the calculator
            try:
                # Extract metric and source from tuple
                metric_type, source = self._current_metric
                
                # Get the correct database format for this metric
                hk_type = self._get_database_metric_type(metric_type)
                
                # Get data for the entire month
                days_in_month = monthrange(self._current_year, self._current_month)[1]
                today = date.today()
                
                logger.info(f"Loading data for {hk_type} in {self._current_month}/{self._current_year}")
                
                for day in range(1, days_in_month + 1):
                    current_date = date(self._current_year, self._current_month, day)
                    
                    # Skip future dates
                    if current_date > today:
                        continue
                    
                    # Get daily aggregate value
                    if source:
                        # Get source-specific data
                        daily_value = self._get_source_specific_daily_value(hk_type, current_date, source)
                    else:
                        # Get aggregated data from all sources
                        daily_value = self.monthly_calculator.get_daily_aggregate(
                            metric=hk_type,
                            date=current_date
                        )
                    
                    if daily_value is not None and daily_value > 0:
                        # Convert values for display based on metric type
                        data[current_date] = self._convert_value_for_display(daily_value, metric_type)
                        logger.debug(f"Loaded {metric_type} for {current_date}: {daily_value}")
                
                logger.info(f"Loaded {len(data)} days of data for {metric_type}")
                            
            except Exception as e:
                logger.error(f"Error loading month data: {e}", exc_info=True)
                # Return empty data
                data = {}
        else:
            # No calculator available - try to use database directly
            logger.warning("No monthly calculator available, attempting direct database access")
            data = self._load_data_from_database()
        
        # Update calendar heatmap with metric type and source
        if isinstance(self._current_metric, tuple):
            metric_type, source = self._current_metric
        else:
            metric_type = self._current_metric
            source = None
        
        self.calendar_heatmap.set_metric_data(metric_type, data, source)
        self.calendar_heatmap.set_current_date(date(self._current_year, self._current_month, 1))
        
        # Update summary statistics
        self._update_summary_stats(data)
        
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
        
    def _load_data_from_database(self) -> Dict[date, float]:
        """Load data directly from the database when no calculator is available."""
        data = {}
        
        if not self.health_db:
            logger.warning("No health database connection available")
            return data
            
        try:
            # Get metric and source from current metric tuple
            if isinstance(self._current_metric, tuple):
                metric_type, source = self._current_metric
            else:
                metric_type = self._current_metric
                source = None
                
            # Get the correct database format for this metric
            hk_type = self._get_database_metric_type(metric_type)
                
            # Get data for the entire month
            first_day = date(self._current_year, self._current_month, 1)
            last_day = date(self._current_year, self._current_month, 
                           monthrange(self._current_year, self._current_month)[1])
            today = date.today()
            
            logger.info(f"Loading data directly from database for {hk_type} in {self._current_month}/{self._current_year}")
            
            current_date = first_day
            while current_date <= last_day and current_date <= today:
                if source:
                    # Get source-specific data
                    daily_value = self._get_source_specific_daily_value(hk_type, current_date, source)
                else:
                    # Get aggregated data from database
                    daily_value = self._get_daily_aggregate_from_db(hk_type, current_date)
                
                if daily_value is not None and daily_value > 0:
                    # Convert values for display based on metric type
                    data[current_date] = self._convert_value_for_display(daily_value, metric_type)
                    logger.debug(f"Loaded {metric_type} for {current_date}: {daily_value}")
                
                current_date += timedelta(days=1)
            
            logger.info(f"Loaded {len(data)} days of data for {metric_type} from database")
            
        except Exception as e:
            logger.error(f"Error loading data from database: {e}", exc_info=True)
            
        return data
    
    def _get_daily_aggregate_from_db(self, metric_type: str, target_date: date) -> Optional[float]:
        """Get daily aggregate value directly from database."""
        try:
            from ..database import db_manager

            # Query database for the specific date
            query = """
                SELECT SUM(value) as total_value
                FROM health_records
                WHERE type = ? 
                AND DATE(startDate) = ?
            """
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (metric_type, target_date.isoformat()))
                result = cursor.fetchone()
                
                if result and result[0] is not None:
                    return float(result[0])
                
        except Exception as e:
            logger.error(f"Error getting daily aggregate from database: {e}")
            
        return None
    
        
    def _update_summary_stats(self, data: Dict[date, float]):
        """Update the summary statistics cards."""
        if not data:
            # Set empty state for stats cards
            for card in self.stats_cards.values():
                card.value_label.setText("--")
            return
            
        values = list(data.values())
        
        # Calculate statistics
        average = sum(values) / len(values)
        total = sum(values)
        best_day = max(data, key=data.get)
        best_value = data[best_day]
        
        # Determine trend (simplified)
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point) if len(values) > mid_point else 0
        trend = "↑" if second_half_avg > first_half_avg else "↓"
        
        # Extract metric type from tuple if needed
        metric_type = self._current_metric[0] if isinstance(self._current_metric, tuple) else self._current_metric
        
        # Format values based on metric type
        unit = self._metric_units.get(metric_type, "")
        
        # Special formatting for certain metrics
        if metric_type in ["StepCount", "FlightsClimbed", "AppleStandHour"]:
            # Integer values with thousands separator
            avg_text = f"{int(average):,}"
            total_text = f"{int(total):,}"
            best_text = f"{int(best_value):,}"
            if unit:
                avg_text = f"{avg_text} {unit}"
                total_text = f"{total_text} {unit}"
                best_text = f"{best_text} {unit}"
        elif metric_type in ["HeartRate", "RestingHeartRate", "WalkingHeartRateAverage", 
                                      "BloodPressureSystolic", "BloodPressureDiastolic"]:
            # Integer values for heart rate and blood pressure
            avg_text = f"{int(average)} {unit}"
            total_text = f"{int(average)} avg"  # Average makes more sense than total
            best_text = f"{int(best_value)} {unit}"
        elif metric_type in ["BodyMass", "LeanBodyMass", "Height"]:
            # One decimal place for body measurements
            avg_text = f"{average:.1f} {unit}"
            total_text = f"{average:.1f} avg"  # Average makes more sense
            best_text = f"{best_value:.1f} {unit}"
        elif metric_type in ["BodyFatPercentage", "WalkingAsymmetryPercentage", 
                                      "WalkingDoubleSupportPercentage", "AppleWalkingSteadiness"]:
            # Percentages with one decimal
            avg_text = f"{average:.1f}{unit}"
            total_text = f"{average:.1f} avg"
            best_text = f"{best_value:.1f}{unit}"
        elif metric_type == "BodyMassIndex":
            # BMI with one decimal, no unit
            avg_text = f"{average:.1f}"
            total_text = f"{average:.1f} avg"
            best_text = f"{best_value:.1f}"
        else:
            # Default: one decimal place with unit
            avg_text = f"{average:.1f}"
            total_text = f"{total:.1f}"
            best_text = f"{best_value:.1f}"
            if unit:
                avg_text = f"{avg_text} {unit}"
                total_text = f"{total_text} {unit}"
                best_text = f"{best_text} {unit}"
            
        # Update cards
        self.stats_cards["average"].value_label.setText(avg_text)
        self.stats_cards["total"].value_label.setText(total_text)
        self.stats_cards["best_day"].value_label.setText(f"{best_text}")
        self.stats_cards["trend"].value_label.setText(f"{trend} Trending")
        
    def _on_date_clicked(self, clicked_date: date):
        """Handle date click in calendar heatmap."""
        # TODO: Show detailed daily view
        print(f"Date clicked: {clicked_date}")
        
    def _on_date_range_selected(self, start_date: date, end_date: date):
        """Handle date range selection in calendar heatmap."""
        # TODO: Show range statistics
        print(f"Date range selected: {start_date} to {end_date}")
        
    def set_data_source(self, monthly_calculator):
        """Set the monthly metrics calculator data source."""
        self.monthly_calculator = monthly_calculator
        
        # Reload available metrics when data source changes
        self._load_available_metrics()
        self._refresh_metric_combo()
        
        # Update month label
        self._update_month_label()
        
        # Load data for current month
        self._load_month_data()
        
        # Force UI update
        self.update()
        QApplication.processEvents()
        
    def set_cached_data_access(self, cached_data_access):
        """Set the cached data access for metric queries.
        
        Args:
            cached_data_access: The cached data access instance
        """
        self.cached_data_access = cached_data_access
        logger.info("Set cached data access for monthly dashboard")
        
        # Reload available metrics when data source changes
        self._load_available_metrics()
        self._refresh_metric_combo()
        
        # Load data for current month
        self._load_month_data()
        
    def get_current_month(self) -> tuple[int, int]:
        """Get the current year and month being displayed."""
        return self._current_year, self._current_month
    
    def reset_to_current_month(self):
        """Reset the view to the current month."""
        now = datetime.now()
        self._current_year = now.year
        self._current_month = now.month
        logger.info(f"Resetting to current month: {self._current_month}/{self._current_year}")
        self._update_month_label()
        self._load_month_data()
        self.month_changed.emit(self._current_year, self._current_month)
        
    def _set_calendar_style(self, style: str):
        """Set the calendar heatmap style."""
        if style == "classic":
            self.calendar_heatmap._view_mode = "month_grid"
            self.classic_btn.setChecked(True)
            self.github_btn.setChecked(False)
        elif style == "github":
            self.calendar_heatmap._view_mode = "github_style"
            self.classic_btn.setChecked(False)
            self.github_btn.setChecked(True)
        
        # Force redraw
        self.calendar_heatmap.update()
        
    def showEvent(self, event):
        """Handle widget show event to ensure UI is refreshed."""
        super().showEvent(event)
        
        # Reload available metrics when widget is shown
        self._load_available_metrics()
        self._refresh_metric_combo()
        
        # Check if we're showing a future month and reset if needed
        now = datetime.now()
        if self._current_year > now.year or (self._current_year == now.year and self._current_month > now.month):
            logger.warning(f"Widget showing future month {self._current_month}/{self._current_year}, resetting to current")
            self.reset_to_current_month()
        else:
            # Force a refresh when the widget is shown
            self._load_month_data()
            self._update_month_label()