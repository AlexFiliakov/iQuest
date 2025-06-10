"""Main window implementation with tab navigation for Apple Health Monitor Dashboard.

This module provides the primary application window that serves as the main
interface for the Apple Health Monitor Dashboard. It implements a modern,
accessible tab-based navigation system with comprehensive functionality.

The main window manages:
    - Multi-tab interface for different dashboard views
    - Menu system with keyboard shortcuts
    - Window state persistence
    - View transitions with smooth animations
    - Personal records tracking integration
    - Export and backup functionality

Example:
    Basic usage:
        
        >>> app = QApplication(sys.argv)
        >>> window = MainWindow()
        >>> window.show()
        >>> app.exec()
        
    Custom initialization:
        
        >>> window = MainWindow()
        >>> window.toggle_accessibility_mode(True)  # Disable animations
        >>> window.show()

Attributes:
    WINDOW_TITLE (str): Application window title from config
    WINDOW_MIN_WIDTH (int): Minimum window width from config
    WINDOW_MIN_HEIGHT (int): Minimum window height from config
"""

import os
import shutil
import time
from datetime import date
from typing import List

import pandas as pd
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QIcon, QKeyEvent, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..analytics.personal_records_tracker import PersonalRecordsTracker
from ..config import (
    DATA_DIR,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)

# from ..analytics.background_trend_processor import BackgroundTrendProcessor
from ..database import db_manager
from ..utils.logging_config import get_logger
from .configuration_tab import ConfigurationTab
from .settings_manager import SettingsManager
from .style_manager import StyleManager
from .trophy_case_widget import TrophyCaseWidget
from .view_transitions import ViewTransitionManager, ViewType

logger = get_logger(__name__)

# Windows to pytz timezone mapping
WINDOWS_TIMEZONE_MAP = {
    'Eastern Standard Time': 'US/Eastern',
    'Eastern Daylight Time': 'US/Eastern',
    'Central Standard Time': 'US/Central',
    'Central Daylight Time': 'US/Central',
    'Mountain Standard Time': 'US/Mountain',
    'Mountain Daylight Time': 'US/Mountain',
    'Pacific Standard Time': 'US/Pacific',
    'Pacific Daylight Time': 'US/Pacific',
    'GMT Standard Time': 'Europe/London',
    'Central European Standard Time': 'Europe/Berlin',
    'W. Europe Standard Time': 'Europe/Amsterdam',
    'Romance Standard Time': 'Europe/Paris',
    'Tokyo Standard Time': 'Asia/Tokyo',
    'China Standard Time': 'Asia/Shanghai',
    'India Standard Time': 'Asia/Kolkata',
    'AUS Eastern Standard Time': 'Australia/Sydney',
}

def get_local_timezone():
    """Get the local timezone in pytz-compatible format.
    
    Returns:
        str: pytz-compatible timezone name
    """
    import time
    local_tz = time.tzname[0]
    return WINDOWS_TIMEZONE_MAP.get(local_tz, 'UTC')


class MainWindow(QMainWindow):
    """Main application window with tab-based navigation.
    
    This is the primary window of the Apple Health Monitor Dashboard application.
    It provides a comprehensive tab-based interface for different views and
    functionalities including data configuration, visualization dashboards,
    analytics, and user records.
    
    The window implements modern UI patterns with:
        - Accessible keyboard navigation with shortcuts
        - Smooth view transitions and animations
        - Persistent window state management
        - Professional theming and styling
        - Personal health records tracking
        - Export and backup capabilities
        - Comprehensive help system
    
    Available tabs:
        - Configuration: Data import and filtering settings
        - Daily Dashboard: Daily health metrics visualization
        - Weekly Dashboard: Weekly aggregated health data
        - Monthly Dashboard: Monthly health trends and patterns
        - Comparative Analytics: Cross-metric analysis and comparisons
        - Health Insights: AI-powered health recommendations
        - Trophy Case: Personal records and achievements
        - Journal: Daily, weekly, and monthly reflection entries
        - Help: Application documentation and keyboard shortcuts
    
    Attributes:
        style_manager (StyleManager): Manages application styling and themes.
        settings_manager (SettingsManager): Handles window state persistence.
        transition_manager (ViewTransitionManager): Manages smooth view transitions.
        personal_records_tracker (PersonalRecordsTracker): Tracks health achievements.
        background_trend_processor (BackgroundTrendProcessor): Processes trend data.
        tab_widget (QTabWidget): The main tab container widget.
        config_tab (ConfigurationTab): The configuration tab instance.
        tab_to_view_map (dict): Maps tab indices to ViewType enums.
        previous_tab_index (int): Index of the previously active tab.
        status_update_timer (QTimer): Timer for updating status bar information.
        
    Example:
        Creating and displaying the main window:
        
        >>> app = QApplication(sys.argv)
        >>> window = MainWindow()
        >>> window.show()
        >>> app.exec()
    """
    
    def __init__(self, initialization_callback=None):
        """Initialize the main window.
        
        Sets up the complete window structure including theming, tab navigation,
        keyboard shortcuts, and restores the previous session state. The
        initialization process is carefully ordered to ensure proper dependency
        resolution and optimal startup performance.
        
        The initialization sequence:
            1. Initialize core managers (style, settings, transitions)
            2. Initialize data tracking components (records, trends)
            3. Set window properties and default dimensions
            4. Apply professional theming and color palette
            5. Create UI components (menu bar, tabs, status bar)
            6. Configure keyboard navigation and shortcuts
            7. Restore previous window state and active tab
            8. Start background status monitoring
        
        Args:
            initialization_callback: Optional callback function that receives
                initialization messages as strings.
        
        Raises:
            ImportError: If required background trend processor cannot be imported.
            
        Note:
            The window is created but not shown. Call show() to display it.
        """
        super().__init__()
        logger.info("Initializing main window with tab navigation")
        self._init_callback = initialization_callback
        
        self._report_init("Initializing core managers...")
        
        # Initialize managers
        self.style_manager = StyleManager()
        self.settings_manager = SettingsManager()
        
        # Initialize transition manager (check accessibility settings)
        accessibility_mode = self.settings_manager.get_setting("accessibility/disable_animations", False)
        self.transition_manager = ViewTransitionManager(accessibility_mode=accessibility_mode)
        
        self._report_init("Setting up personal records tracker...")
        
        # Initialize personal records tracker
        self.personal_records_tracker = PersonalRecordsTracker(db_manager)
        
        # Cache calculator instances to avoid recreation
        self._calculator_cache = {
            'daily': None,
            'weekly': None,
            'monthly': None,
            'daily_base': None  # Base calculator used by weekly/monthly
        }
        self._last_data_hash = None
        
        # Initialize background trend processor
        self.background_trend_processor = None
        try:
            self._report_init("Initializing background analytics...")
            from ..analytics.background_trend_processor import BackgroundTrendProcessor
            self.background_trend_processor = BackgroundTrendProcessor(db_manager)
            logger.info("Background trend processor initialized")
        except ImportError as e:
            logger.warning(f"Could not initialize background trend processor: {e}")
        
        self._report_init("Performing database health check...")
        
        # Perform database health check (G084 infrastructure validation)
        self._perform_database_health_check()
        
        self._report_init("Configuring window properties...")
        
        # Set up the window
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        # Set default size appropriate for 1920x1080 at 150% scale
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # Ensure window stays open
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # Apply warm color theme
        self._apply_theme()
        
        self._report_init("Creating menu system...")
        
        # Create UI components
        self._create_menu_bar()
        
        self._report_init("Creating dashboard tabs...")
        
        try:
            self._create_central_widget()
        except Exception as e:
            logger.error(f"Failed to create central widget: {e}", exc_info=True)
            self._report_init(f"ERROR: Failed to create tabs - {str(e)}")
            raise
        
        self._report_init("Setting up status bar...")
        
        try:
            self._create_status_bar()
        except Exception as e:
            logger.error(f"Failed to create status bar: {e}", exc_info=True)
            self._report_init(f"ERROR: Failed to create status bar - {str(e)}")
            raise
        
        self._report_init("Restoring window state...")
        
        # Restore window state after UI is created
        self.settings_manager.restore_window_state(self)
        
        # Always open to Configuration tab
        self.tab_widget.setCurrentIndex(0)
        
        # Ensure only the current tab is visible
        self._ensure_only_current_tab_visible()
        
        self._report_init("Starting background services...")
        
        # Set up status update timer
        self.status_update_timer = QTimer(self)
        self.status_update_timer.timeout.connect(self._update_trend_status)
        self.status_update_timer.start(2000)  # Update every 2 seconds
        
        logger.info("Main window initialization complete")
        logger.info(f"Window visible at end of init: {self.isVisible()}")
        logger.info(f"Window attributes - WA_QuitOnClose: {self.testAttribute(Qt.WidgetAttribute.WA_QuitOnClose)}")
        self._report_init("Main window initialization complete!")
    
    def _report_init(self, message: str):
        """Report initialization progress.
        
        Args:
            message: Progress message to report.
        """
        if self._init_callback:
            try:
                self._init_callback(message)
            except Exception as e:
                logger.warning(f"Failed to report init progress: {e}")
    
    def _apply_theme(self):
        """Apply the professional color theme to the window.
        
        Sets up the application's visual styling with a modern, professional
        color palette that follows WSJ-inspired design principles. The theme
        provides excellent readability and accessibility.
        
        Theme features:
            - Clean background colors (light beige/cream tones)
            - Professional text colors (earth tones)
            - Orange accent colors for highlights and CTAs
            - Consistent styling across all UI components
            - High contrast ratios for accessibility
            - Warm, inviting appearance that reduces eye strain
        
        The theme is applied through both stylesheets and QPalette settings
        to ensure consistency across all Qt widgets and custom components.
        """
        logger.debug("Applying warm color theme")
        
        # Apply stylesheet
        self.setStyleSheet(self.style_manager.get_main_window_style())
        
        # Set application palette for consistent colors
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F5E6D3"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#5D4E37"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#FFF8F0"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#5D4E37"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#5D4E37"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#FF8C42"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(palette)
    
    def _create_menu_bar(self):
        """Create the application menu bar with comprehensive functionality.
        
        Sets up a complete menu system with keyboard shortcuts, tooltips,
        and status tips for enhanced accessibility and user experience.
        
        Menu structure:
            File menu:
                - Import: Data import with Ctrl+O shortcut
                - Save Configuration: Save current settings with Ctrl+S
                - Export submenu: Generate reports, quick exports (PDF/Excel/CSV)
                - Create Backup: Complete data backup functionality
                - Erase All Data: Secure data removal with confirmation
                - Exit: Close application with Ctrl+Q
                
            Help menu:
                - Keyboard Shortcuts: Reference dialog with Ctrl+?
                - About: Application information dialog
        
        All menu items include:
            - Keyboard shortcuts for power users
            - Descriptive tooltips with shortcut information
            - Status bar tips explaining functionality
            - Proper mnemonics for keyboard navigation
        """
        logger.debug("Creating menu bar")
        
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(self.style_manager.get_menu_bar_style())
        menu_bar.setNativeMenuBar(False)  # Ensure menu bar is displayed within the window
        menu_bar.setFixedHeight(30)  # Set a fixed height to prevent overlap
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Import action
        import_action = QAction("&Import...", self)
        import_action.setShortcut("Ctrl+O")
        import_action.setStatusTip("Import Apple Health data")
        import_action.setToolTip("Import Apple Health data from CSV or XML file (Ctrl+O)")
        import_action.triggered.connect(self._on_import_data)
        file_menu.addAction(import_action)
        
        # Save action
        save_action = QAction("&Save Configuration", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current configuration settings")
        save_action.setToolTip("Save current filter and configuration settings (Ctrl+S)")
        save_action.triggered.connect(self._on_save_configuration)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Export menu
        export_menu = file_menu.addMenu("&Export")
        
        # Export Report action
        export_report_action = QAction("&Generate Report...", self)
        export_report_action.setShortcut("Ctrl+E")
        export_report_action.setStatusTip("Generate health report or export data")
        export_report_action.setToolTip("Export health data in various formats (Ctrl+E)")
        export_report_action.triggered.connect(self._on_export_report)
        export_menu.addAction(export_report_action)
        
        # Quick Export submenu
        quick_export_menu = export_menu.addMenu("Quick Export")
        
        # PDF Report
        pdf_action = QAction("PDF Report", self)
        pdf_action.setStatusTip("Export as PDF report")
        pdf_action.triggered.connect(lambda: self._on_quick_export("pdf"))
        quick_export_menu.addAction(pdf_action)
        
        # Excel Export
        excel_action = QAction("Excel Workbook", self)
        excel_action.setStatusTip("Export as Excel file")
        excel_action.triggered.connect(lambda: self._on_quick_export("excel"))
        quick_export_menu.addAction(excel_action)
        
        # CSV Export
        csv_action = QAction("CSV Data", self)
        csv_action.setStatusTip("Export as CSV file")
        csv_action.triggered.connect(lambda: self._on_quick_export("csv"))
        quick_export_menu.addAction(csv_action)
        
        export_menu.addSeparator()
        
        # Backup action
        backup_action = QAction("Create &Backup...", self)
        backup_action.setStatusTip("Create complete data backup")
        backup_action.setToolTip("Create a complete backup of all health data")
        backup_action.triggered.connect(self._on_create_backup)
        export_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        # Erase All Data action
        erase_data_action = QAction("&Erase All Data...", self)
        erase_data_action.setStatusTip("Clear all data from the database and cache")
        erase_data_action.setToolTip("Completely remove all imported health data and cached results")
        erase_data_action.triggered.connect(self._on_erase_all_data)
        file_menu.addAction(erase_data_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.setToolTip("Close the Apple Health Monitor application (Ctrl+Q)")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Keyboard shortcuts action
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+?")
        shortcuts_action.setStatusTip("Show keyboard shortcuts reference")
        shortcuts_action.setToolTip("Display a list of all keyboard shortcuts (Ctrl+?)")
        shortcuts_action.triggered.connect(self._on_show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Apple Health Monitor")
        about_action.setToolTip("Show information about Apple Health Monitor")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_central_widget(self):
        """Create the central widget with comprehensive tab navigation.
        
        Sets up the main tab widget that serves as the primary interface
        for all application functionality. This includes creating all
        dashboard tabs, establishing transition mappings, and configuring
        the complete navigation system.
        
        Components created:
            - QTabWidget as the central container
            - All dashboard tabs (Config, Daily, Weekly, Monthly, etc.)
            - Tab-to-view mappings for transition management
            - Signal connections for tab change events
            - Keyboard navigation shortcuts (Ctrl+1-8, Alt+C/D/W/M/etc.)
            - View transition system with smooth animations
        
        Tab organization:
            0: Configuration - Data import and filtering
            1: Daily - Daily metrics and trends
            2: Weekly - Weekly aggregated data
            3: Monthly - Monthly patterns and calendar view
            4: Compare - Comparative analytics
            5: Insights - AI-powered health insights
            6: Trophy Case - Personal records and achievements
            7: Journal - Personal health journal
            8: Help - Keyboard shortcuts and documentation
        """
        logger.debug("Creating central widget with tabs")
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet(self.style_manager.get_tab_widget_style())
        self.tab_widget.setDocumentMode(True)  # For cleaner tab appearance
        self.setCentralWidget(self.tab_widget)
        
        # Ensure proper spacing around central widget
        self.centralWidget().setContentsMargins(0, 0, 0, 0)
        
        # Create tabs with error handling
        # Temporarily simplify tab creation to debug the issue
        tab_methods = [
            ("Configuration", self._create_configuration_tab),
            ("Daily Dashboard", self._create_daily_dashboard_tab),
            ("Weekly Dashboard", self._create_weekly_dashboard_tab),
            ("Monthly Dashboard", self._create_monthly_dashboard_tab),
            # ("Comparative Analytics", self._create_comparative_analytics_tab),
            # ("Health Insights", self._create_health_insights_tab),
            # ("Trophy Case", self._create_trophy_case_tab),
            # ("Journal", self._create_journal_tab),  # Temporarily disabled due to crash
            # ("Help", self._create_help_tab)
        ]
        
        for tab_name, create_method in tab_methods:
            try:
                self._report_init(f"Creating {tab_name} tab...")
                logger.info(f"Starting creation of {tab_name} tab")
                create_method()
                logger.info(f"Successfully created {tab_name} tab")
            except Exception as e:
                logger.error(f"Failed to create {tab_name} tab: {e}", exc_info=True)
                self._report_init(f"ERROR: Failed to create {tab_name} tab - {str(e)}")
                # Continue with other tabs even if one fails
                # Create placeholder tab
                error_widget = QWidget()
                error_label = QLabel(f"Error loading {tab_name} tab:\n{str(e)}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout = QVBoxLayout(error_widget)
                layout.addWidget(error_label)
                self.tab_widget.addTab(error_widget, tab_name)
        
        # Add placeholder tabs for now
        for tab_name in ["Comparative Analytics", "Health Insights", "Trophy Case", "Journal", "Help"]:
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel(f"{tab_name} - Under Development")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 18px; color: #666;")
            layout.addWidget(label)
            self.tab_widget.addTab(placeholder, tab_name)
        
        # Map tab indices to view types
        self.tab_to_view_map = {
            0: ViewType.CONFIG,      # Configuration
            1: ViewType.DAILY,       # Daily
            2: ViewType.WEEKLY,      # Weekly
            3: ViewType.MONTHLY,     # Monthly
            4: ViewType.DAILY,       # Comparative (using DAILY enum temporarily)
            5: ViewType.DAILY,       # Health Insights (using DAILY enum temporarily)
            6: ViewType.JOURNAL,     # Trophy Case (using JOURNAL enum temporarily)
            7: ViewType.JOURNAL,     # Journal
            8: ViewType.CONFIG       # Help (using CONFIG enum temporarily)
        }
        
        # Store reference to previous tab for transitions
        self.previous_tab_index = 0
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Connect transition manager signals
        self.transition_manager.transition_started.connect(self._on_transition_started)
        self.transition_manager.transition_completed.connect(self._on_transition_completed)
        self.transition_manager.transition_interrupted.connect(self._on_transition_interrupted)
        
        # Set up keyboard navigation
        self._setup_keyboard_navigation()
        logger.info("_create_central_widget completed successfully")
    
    def _create_configuration_tab(self):
        """Create the configuration tab with data management functionality.
        
        Initializes the configuration tab which serves as the primary interface
        for data import, filtering, and source management. The tab is wrapped
        in a scroll area to accommodate varying content sizes and screen
        resolutions.
        
        Features implemented:
            - CSV and XML data import with progress tracking
            - Date range filtering with calendar widgets
            - Device/source filtering with multi-select dropdowns
            - Health metric type filtering
            - Filter preset saving and loading
            - Real-time data statistics display
            
        Signal connections:
            - data_loaded: Emitted when data is successfully imported
            - filters_applied: Emitted when filters are applied to data
            
        The configuration tab uses the standard ConfigurationTab class
        which provides comprehensive data management functionality with
        optimized performance for large datasets.
        """
        # Use standard ConfigurationTab for now
        # The modern version is incomplete and doesn't have summary cards implemented
        ConfigTab = ConfigurationTab
        logger.info("Using standard ConfigurationTab")
        
        # Create configuration tab with scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.config_tab = ConfigurationTab()
        scroll_area.setWidget(self.config_tab)
        
        # Connect signals
        self.config_tab.data_loaded.connect(self._on_data_loaded)
        self.config_tab.filters_applied.connect(self._on_filters_applied)
        
        self.tab_widget.addTab(scroll_area, "Configuration")
        self.tab_widget.setTabToolTip(0, "Import data and configure filters")
    
    def _create_daily_dashboard_tab(self):
        """Create the daily dashboard tab with comprehensive daily metrics.
        
        Initializes the daily dashboard which provides detailed views of
        daily health metrics, trends, and personal records. Includes
        fallback handling if the dashboard widget cannot be imported.
        
        Features:
            - Daily metric visualization with interactive charts
            - Personal records tracking and display
            - Date navigation for historical data exploration
            - Metric selection and filtering capabilities
            - Refresh functionality for real-time updates
            
        Signal connections:
            - metric_selected: Handles metric selection events
            - date_changed: Responds to date navigation
            - refresh_requested: Handles manual refresh requests
            
        Fallback behavior:
            If DailyDashboardWidget import fails, creates a placeholder
            tab with appropriate messaging to maintain UI consistency.
        """
        try:
            from ..data_access import DataAccess
            from .daily_dashboard_widget import DailyDashboardWidget

            # Create data access instance (uses DatabaseManager singleton which respects portable mode)
            data_access = DataAccess()
            
            # Create the daily dashboard widget with parent and data_access
            self.daily_dashboard = DailyDashboardWidget(data_access=data_access, parent=self)
            
            # Connect signals
            if hasattr(self.daily_dashboard, 'metric_selected'):
                self.daily_dashboard.metric_selected.connect(self._handle_metric_selection)
            if hasattr(self.daily_dashboard, 'date_changed'):
                self.daily_dashboard.date_changed.connect(self._handle_date_change)
            if hasattr(self.daily_dashboard, 'refresh_requested'):
                self.daily_dashboard.refresh_requested.connect(self._refresh_daily_data)
            
            self._add_tab_hidden(self.daily_dashboard, "Daily", "View your daily health metrics and trends")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import DailyDashboardWidget: {e}")
            self._create_daily_dashboard_placeholder()
        except Exception as e:
            # Fallback to placeholder if any other error occurs
            logger.error(f"Failed to create daily dashboard: {e}", exc_info=True)
            self._create_daily_dashboard_placeholder()
    
    def _create_daily_dashboard_placeholder(self):
        """Create a placeholder daily dashboard tab."""
        daily_widget = QWidget(self)
        layout = QVBoxLayout(daily_widget)
        
        # Placeholder content
        label = QLabel("Daily Dashboard")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        
        placeholder = QLabel("Daily health metrics will appear here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B7355;
                padding: 10px;
            }
        """)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        self._add_tab_hidden(daily_widget, "Daily", "View your daily health metrics and trends")
    
    def _create_weekly_dashboard_tab(self):
        """Create the weekly dashboard tab with aggregated weekly metrics.
        
        Initializes the weekly dashboard which provides comprehensive views
        of weekly health summaries, patterns, and trends. Uses the standard
        WeeklyDashboardWidget for consistent functionality.
        
        Features:
            - Weekly metric aggregation and visualization
            - Week-over-week comparison capabilities
            - Pattern analysis and trend identification
            - Interactive charts with drill-down functionality
            - Week navigation with calendar integration
            
        Signal connections:
            - week_changed: Handles week navigation events
            - metric_selected: Responds to metric selection
            
        Fallback behavior:
            If WeeklyDashboardWidget import fails, creates a placeholder
            tab with descriptive messaging to maintain UI consistency.
            
        Note:
            Uses the standard version of WeeklyDashboardWidget as the
            modern version has known display issues.
        """
        try:
            # Use standard version for now (modern version has display issues)
            from ..data_access import DataAccess
            from .weekly_dashboard_widget import WeeklyDashboardWidget

            # Create data access instance (uses DatabaseManager singleton which respects portable mode)
            data_access = DataAccess()
            
            self.weekly_dashboard = WeeklyDashboardWidget(data_access=data_access, parent=self)
            logger.info("Using standard WeeklyDashboardWidget")
            
            # Connect signals
            self.weekly_dashboard.week_changed.connect(self._on_week_changed)
            self.weekly_dashboard.metric_selected.connect(self._on_metric_selected)
            
            self._add_tab_hidden(self.weekly_dashboard, "Weekly", "Analyze weekly health summaries and patterns")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import WeeklyDashboardWidget: {e}")
            self._create_weekly_dashboard_placeholder()
        except Exception as e:
            # Fallback to placeholder if any other error occurs
            logger.error(f"Failed to create weekly dashboard: {e}", exc_info=True)
            self._create_weekly_dashboard_placeholder()
    
    def _create_weekly_dashboard_placeholder(self):
        """Create a placeholder weekly dashboard tab."""
        weekly_widget = QWidget(self)
        layout = QVBoxLayout(weekly_widget)
        
        # Placeholder content
        label = QLabel("Weekly Dashboard")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        
        placeholder = QLabel("Weekly health summaries will appear here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B7355;
                padding: 10px;
            }
        """)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        self._add_tab_hidden(weekly_widget, "Weekly", "Analyze weekly health summaries and patterns")
    
    def _create_monthly_dashboard_tab(self):
        """Create the monthly dashboard tab with calendar heatmap visualization.
        
        Initializes the monthly dashboard which provides comprehensive monthly
        health trend analysis with an interactive calendar heatmap. This tab
        offers high-level pattern recognition and long-term trend analysis.
        
        Features:
            - Monthly health trend visualization
            - Interactive calendar heatmap with daily data points
            - Month-over-month comparison capabilities
            - Seasonal pattern analysis
            - Long-term trend identification
            - Month navigation with year-level overview
            
        Signal connections:
            - month_changed: Handles month navigation events
            - metric_changed: Responds to metric type changes
            
        Fallback behavior:
            If MonthlyDashboardWidget import fails, creates a placeholder
            tab with appropriate messaging about the calendar heatmap
            functionality to maintain user expectations.
            
        The monthly dashboard is particularly useful for identifying
        seasonal patterns and long-term health trends.
        """
        try:
            from ..analytics.cached_calculators import (
                CachedDailyMetricsCalculator,
                CachedMonthlyMetricsCalculator,
                CachedWeeklyMetricsCalculator,
            )
            from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
            from ..analytics.data_source_protocol import DataAccessAdapter
            from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
            from ..data_access import DataAccess
            from .monthly_dashboard_widget import MonthlyDashboardWidget

            # Create calculators for the monthly dashboard
            try:
                # Initialize data access and wrap it with adapter
                data_access = DataAccess()
                data_adapter = DataAccessAdapter(data_access)
                
                # Create cached daily calculator first (required by monthly calculator)
                daily_calculator = DailyMetricsCalculator(data_adapter)
                cached_daily_calculator = CachedDailyMetricsCalculator(daily_calculator)
                
                # Create cached monthly calculator with the daily calculator
                monthly_calculator = MonthlyMetricsCalculator(daily_calculator)
                cached_monthly_calculator = CachedMonthlyMetricsCalculator(monthly_calculator)
                
                # Create the monthly dashboard widget with cached calculator and parent
                self.monthly_dashboard = MonthlyDashboardWidget(monthly_calculator=cached_monthly_calculator, parent=self)
                logger.info("Using MonthlyDashboardWidget with calculator")
            except Exception as calc_error:
                logger.warning(f"Could not create calculators: {calc_error}")
                # Create without calculator - will use direct database access
                self.monthly_dashboard = MonthlyDashboardWidget(parent=self)
                logger.info("Using MonthlyDashboardWidget without calculator")
            
            # Connect signals if needed
            self.monthly_dashboard.month_changed.connect(self._on_month_changed)
            self.monthly_dashboard.metric_changed.connect(self._on_metric_changed)
            
            self._add_tab_hidden(self.monthly_dashboard, "Monthly", "Review monthly health trends and calendar heatmap")
            
        except ImportError as e:
            # If import fails, create placeholder
            logger.warning(f"MonthlyDashboardWidget import error: {e}")
            self._create_monthly_dashboard_placeholder()
        except Exception as e:
            # Log any other exceptions
            logger.error(f"Error creating MonthlyDashboardWidget: {e}", exc_info=True)
            self._create_monthly_dashboard_placeholder()
            
    def _create_monthly_dashboard_placeholder(self):
        """Create a placeholder monthly dashboard tab."""
        monthly_widget = QWidget(self)
        layout = QVBoxLayout(monthly_widget)
        
        # Placeholder content
        label = QLabel("Monthly Dashboard")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        
        placeholder = QLabel("Monthly health trends with calendar heatmap will appear here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B7355;
                padding: 10px;
            }
        """)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        self._add_tab_hidden(monthly_widget, "Monthly", "Review monthly health trends and progress")
    
    def _create_comparative_analytics_tab(self):
        """Create the comparative analytics tab with advanced comparison features.
        
        Initializes the comparative analytics tab which provides sophisticated
        analysis capabilities including personal history comparisons, seasonal
        trend analysis, and demographic insights (anonymized).
        
        Features:
            - Personal progress tracking over time
            - Historical data comparison with multiple time periods
            - Seasonal trend analysis and pattern recognition
            - Metric correlation analysis
            - Background trend processing integration
            - Interactive comparison visualizations
            
        Components initialized:
            - ComparativeAnalyticsEngine: Core analysis functionality
            - Background trend processor integration
            - ComparativeAnalyticsWidget: User interface components
            
        Signal connections:
            - Engine connections for real-time analysis updates
            - Background processor integration for trend calculations
            
        Fallback behavior:
            If imports fail, creates a placeholder tab explaining the
            comparative analytics features (personal progress tracking,
            seasonal trends) to maintain user understanding.
            
        Note:
            Peer group comparison features have been removed to focus
            on personal health analytics.
        """
        try:
            # Try to import the comparative analytics widget
            from ..analytics.comparative_analytics import ComparativeAnalyticsEngine
            from .comparative_visualization import ComparativeAnalyticsWidget

            # from ..analytics.peer_group_comparison import PeerGroupManager  # Removed group comparison feature
            # Create the comparative analytics engine
            self.comparative_engine = ComparativeAnalyticsEngine(
                daily_calculator=self.config_tab.daily_calculator if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'daily_calculator') else None,
                weekly_calculator=self.config_tab.weekly_calculator if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'weekly_calculator') else None,
                monthly_calculator=self.config_tab.monthly_calculator if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'monthly_calculator') else None,
                background_processor=self.background_trend_processor if hasattr(self, 'background_trend_processor') else None
            )
            
            # Set the comparative engine in the background processor
            if self.background_trend_processor and hasattr(self.background_trend_processor, 'set_comparative_engine'):
                self.background_trend_processor.set_comparative_engine(self.comparative_engine)
            
            # Peer group manager removed
            # self.peer_group_manager = PeerGroupManager()
            
            # Create the widget
            self.comparative_widget = ComparativeAnalyticsWidget()
            self.comparative_widget.set_comparative_engine(self.comparative_engine)
            
            self.tab_widget.addTab(self.comparative_widget, "Compare")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Compare your metrics with personal history and seasonal trends")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import ComparativeAnalyticsWidget: {e}")
            self._create_comparative_analytics_placeholder()
            
    def _create_comparative_analytics_placeholder(self):
        """Create a placeholder comparative analytics tab."""
        comparative_widget = QWidget(self)
        layout = QVBoxLayout(comparative_widget)
        
        # Placeholder content
        label = QLabel("Comparative Analytics")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        
        placeholder = QLabel("Compare your health metrics with personal history and seasonal trends")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B7355;
                padding: 10px;
            }
        """)
        layout.addWidget(placeholder)
        
        features = QLabel(
            "• Personal progress tracking\n"
            "• Anonymous demographic comparisons\n"
            "• Seasonal trend analysis"
        )
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #8B7355;
                padding: 20px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(features)
        
        layout.addStretch()
        
        self.tab_widget.addTab(comparative_widget, "Compare")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Compare your metrics with personal history and seasonal trends")
    
    def _create_health_insights_tab(self):
        """Create the health insights tab with AI-powered recommendations.
        
        Initializes the health insights tab which provides personalized health
        insights, recommendations, and evidence-based analysis of health patterns.
        This tab leverages advanced analytics and medical evidence databases.
        
        Features:
            - AI-powered health insights generation
            - Evidence-based recommendations
            - Personalized health pattern analysis
            - Interactive insight exploration
            - WSJ-style professional visualizations
            - Refresh functionality for updated insights
            
        Components initialized:
            - EvidenceDatabase: Medical evidence and research integration
            - WSJStyleManager: Professional styling for insights
            - EnhancedHealthInsightsEngine: Core AI analysis engine
            - HealthInsightsWidget: User interface components
            
        Signal connections:
            - refresh_requested: Handles manual insight refresh
            - insight_selected: Responds to insight selection events
            
        Fallback behavior:
            If imports fail, creates a placeholder tab explaining the
            health insights functionality (personalized recommendations,
            pattern analysis) to maintain user expectations.
            
        The insights are generated based on personal health data patterns
        and validated against medical evidence databases.
        """
        try:
            from ..analytics.evidence_database import EvidenceDatabase
            from ..analytics.health_insights_engine import EnhancedHealthInsightsEngine
            from .charts.wsj_style_manager import WSJStyleManager
            from .health_insights_widget import HealthInsightsWidget

            # Create the insights engine
            evidence_db = EvidenceDatabase()
            wsj_style = WSJStyleManager()
            insights_engine = EnhancedHealthInsightsEngine(
                data_manager=None,  # Will be set when data is loaded
                evidence_db=evidence_db,
                style_manager=wsj_style
            )
            
            # Create the insights widget
            self.health_insights_widget = HealthInsightsWidget()
            self.health_insights_widget.set_insights_engine(insights_engine)
            
            # Connect signals
            self.health_insights_widget.insight_selected.connect(self._on_insight_selected)
            
            self._add_tab_hidden(self.health_insights_widget, "💡 Insights", "View personalized health insights and recommendations")
            
        except ImportError as e:
            logger.warning(f"Could not import HealthInsightsWidget: {e}")
            self._create_health_insights_placeholder()
    
    def _create_health_insights_placeholder(self):
        """Create a placeholder health insights tab."""
        insights_widget = QWidget(self)
        layout = QVBoxLayout(insights_widget)
        
        # Placeholder content
        label = QLabel("Health Insights & Recommendations")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 600;
                color: #5D4E37;
                padding: 20px;
            }
        """)
        layout.addWidget(label)
        
        placeholder = QLabel("Personalized health insights based on your data patterns will appear here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B7355;
                padding: 10px;
            }
        """)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        self.tab_widget.addTab(self.health_insights_widget, "💡 Insights")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View personalized health insights and recommendations")
    
    def _create_trophy_case_tab(self):
        """Create the trophy case tab for personal records and achievements.
        
        Initializes the trophy case tab which displays personal health records,
        achievements, milestones, and progress streaks. This gamification
        element helps motivate continued health monitoring and improvement.
        
        Features:
            - Personal health records display
            - Achievement badges and milestones
            - Progress streaks tracking
            - Interactive record exploration
            - Achievement sharing capabilities
            - Historical achievement timeline
            
        Components:
            - TrophyCaseWidget: Main interface for records display
            - PersonalRecordsTracker: Backend tracking system
            
        The trophy case integrates with the personal records tracker
        to provide real-time updates as new records are achieved and
        maintains historical tracking of all accomplishments.
        """
        try:
            logger.info("Trophy case tab: Starting creation")
            self.trophy_case_widget = TrophyCaseWidget(self.personal_records_tracker)
            logger.info("Trophy case tab: Widget created")
            
            # Connect signals (if needed)
            # self.trophy_case_widget.record_selected.connect(self._on_record_selected)
            # self.trophy_case_widget.share_requested.connect(self._on_share_requested)
            
            self.tab_widget.addTab(self.trophy_case_widget, "🏆 Records")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View personal records, achievements, and streaks")
            logger.info("Trophy case tab: Added to tab widget")
        except Exception as e:
            logger.error(f"Failed to create trophy case tab: {e}", exc_info=True)
            # Create a simple placeholder
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            label = QLabel("Trophy Case - Coming Soon")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            self.tab_widget.addTab(placeholder, "🏆 Records")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Trophy case feature under development")
    
    def _create_journal_tab(self):
        """Create the journal tab with editor and history views.
        
        Provides full journal functionality including:
        - Creating and editing journal entries
        - Browsing entry history with virtual scrolling
        - Searching past entries
        - Filtering by date and entry type
        - Exporting journal data
        
        The journal tab serves as a personal space for users to record
        qualitative health observations that complement the quantitative
        data from Apple Health.
        """
        try:
            logger.info("Journal tab: Starting imports")
            from ..data_access import DataAccess

            # First try the minimal version
            try:
                logger.info("Journal tab: Importing minimal version")
                from .journal_tab_minimal import JournalTabMinimal
                logger.info("Journal tab: Minimal import successful")
                
                # Create a DataAccess instance for the journal tab
                logger.info("Journal tab: Creating DataAccess instance")
                data_access = DataAccess()
                logger.info("Journal tab: DataAccess created successfully")
                
                logger.info("Journal tab: Creating JournalTabMinimal")
                self.journal_tab = JournalTabMinimal(data_access)
                logger.info("Journal tab: JournalTabMinimal created successfully")
                
            except Exception as e:
                logger.error(f"Failed with minimal version: {e}", exc_info=True)
                # Try the full version
                logger.info("Journal tab: Trying full JournalTabWidget")
                from .journal_tab_widget import JournalTabWidget
                logger.info("Journal tab: Full import successful")
                
                logger.info("Journal tab: Creating JournalTabWidget")
                self.journal_tab = JournalTabWidget(data_access)
                logger.info("Journal tab: JournalTabWidget created successfully")
            
            self.tab_widget.addTab(self.journal_tab, "Journal")
            self.tab_widget.setTabToolTip(
                self.tab_widget.count() - 1, 
                "Create and browse health journal entries (Alt+J)"
            )
            
            logger.info("Journal tab created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create journal tab: {e}")
            # Fallback to placeholder
            journal_widget = QWidget(self)
            layout = QVBoxLayout(journal_widget)
            
            error_label = QLabel("❌ Failed to load journal tab")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    color: #D32F2F;
                    padding: 20px;
                }
            """)
            layout.addWidget(error_label)
            layout.addStretch()
            
            self.tab_widget.addTab(journal_widget, "Journal")
            self.tab_widget.setTabToolTip(
                self.tab_widget.count() - 1, 
                "Journal feature unavailable"
            )
    
    def _create_help_tab(self):
        """Create the comprehensive help tab with keyboard shortcuts reference.
        
        Initializes the help tab which provides a complete reference for
        keyboard shortcuts, navigation tips, and usage guidance. The help
        system is designed to be accessible and easy to navigate.
        
        Help sections:
            - Navigation shortcuts (Tab switching, element navigation)
            - File operations (Import, Save, Refresh)
            - Configuration tab shortcuts (Browse, Import, Apply filters)
            - Date picker navigation (Arrow keys, Page Up/Down)
            - Multi-select dropdown shortcuts (Space, Ctrl+A, etc.)
            - General controls (Help, Escape, Enter)
            - Tips and tricks for efficient usage
            
        Features:
            - Organized sections with clear headings
            - Keyboard shortcut display with visual styling
            - Scrollable content for comprehensive coverage
            - Practical usage tips for power users
            - Accessibility-focused design
            
        The help tab serves as both a reference guide and a tutorial
        for users to maximize their efficiency with the application.
        """
        help_widget = QWidget(self)
        main_layout = QVBoxLayout(help_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Keyboard Shortcuts Reference")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #5D4E37;
                margin-bottom: 20px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Create scroll area for content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Content widget
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(24)
        
        # Navigation section
        nav_section = self._create_help_section(
            "Navigation", 
            [
                ("Tab / Shift+Tab", "Navigate between elements"),
                ("Ctrl+1 to Ctrl+9", "Switch to specific tab by number"),
                ("Alt+C/D/W/M/O/I/T/J/H", "Quick tab switching (Config/Daily/Weekly/Monthly/cOmpare/Insights/Trophy/Journal/Help)"),
                ("Ctrl+PageUp/PageDown", "Navigate to previous/next tab"),
                ("F1", "Quick access to Help tab")
            ]
        )
        content_layout.addWidget(nav_section)
        
        # File operations section
        file_section = self._create_help_section(
            "File Operations",
            [
                ("Ctrl+O", "Import data file (CSV or XML)"),
                ("Ctrl+S", "Save configuration"),
                ("Ctrl+Q", "Exit application")
            ]
        )
        content_layout.addWidget(file_section)
        
        # Configuration tab section
        config_section = self._create_help_section(
            "Configuration Tab",
            [
                ("Alt+B", "Browse for file"),
                ("Alt+I", "Import data"),
                ("Alt+A", "Apply filters"),
                ("Alt+R", "Reset filters")
            ]
        )
        content_layout.addWidget(config_section)
        
        # Date picker section
        date_section = self._create_help_section(
            "Date Picker Navigation",
            [
                ("Left/Right arrows", "Previous/Next day"),
                ("Up/Down arrows", "Previous/Next week"),
                ("Ctrl+Up/Down", "Previous/Next month"),
                ("Page Up/Down", "Previous/Next month"),
                ("Home/End", "First/Last day of month")
            ]
        )
        content_layout.addWidget(date_section)
        
        # Multi-select dropdowns section
        dropdown_section = self._create_help_section(
            "Multi-Select Dropdowns",
            [
                ("Space", "Toggle selected item"),
                ("Ctrl+A", "Select all items"),
                ("Ctrl+D", "Deselect all items"),
                ("Enter", "Confirm selection"),
                ("Escape", "Close dropdown"),
                ("Up/Down arrows", "Navigate items")
            ]
        )
        content_layout.addWidget(dropdown_section)
        
        # General controls section
        general_section = self._create_help_section(
            "General Controls",
            [
                ("Ctrl+?", "Show this help"),
                ("Enter/Space", "Activate buttons"),
                ("Escape", "Close dialogs"),
                ("F1", "Open help documentation")
            ]
        )
        content_layout.addWidget(general_section)
        
        # Tips section
        tips_section = self._create_tips_section()
        content_layout.addWidget(tips_section)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(help_widget, "Help")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Keyboard shortcuts and usage help")
    
    def _create_help_section(self, title, shortcuts):
        """Create a help section with title and shortcuts table."""
        section = QFrame(self)
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        section_title = QLabel(title)
        section_title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #FF8C42;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(section_title)
        
        # Shortcuts table
        for shortcut, description in shortcuts:
            shortcut_row = self._create_shortcut_row(shortcut, description)
            layout.addWidget(shortcut_row)
        
        return section
    
    def _create_shortcut_row(self, shortcut, description):
        """Create a single shortcut row."""
        row = QWidget(self)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(16)
        
        # Shortcut key(s)
        shortcut_label = QLabel(shortcut)
        shortcut_label.setStyleSheet("""
            QLabel {
                background-color: #FFF8F0;
                border: 1px solid #E8DCC8;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-weight: 600;
                color: #5D4E37;
                min-width: 140px;
            }
        """)
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(shortcut_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #5D4E37;
                font-size: 14px;
                padding: 6px 0;
            }
        """)
        row_layout.addWidget(desc_label, 1)
        
        return row
    
    def _create_tips_section(self):
        """Create a tips and tricks section."""
        section = QFrame(self)
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid rgba(255, 140, 66, 0.2);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Tips title
        tips_title = QLabel("💡 Tips for Efficient Usage")
        tips_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #FF8C42;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(tips_title)
        
        tips = [
            "Use Ctrl+1-5 for quick tab switching while working with data",
            "The date picker arrow keys make it easy to navigate date ranges",
            "Ctrl+A in dropdowns selects all items quickly",
            "Save frequently used filter combinations with Ctrl+S",
            "Use Tab to move through forms efficiently without the mouse",
            "Press Escape to quickly close any open dialogs or dropdowns"
        ]
        
        for tip in tips:
            tip_label = QLabel(f"• {tip}")
            tip_label.setStyleSheet("""
                QLabel {
                    color: #5D4E37;
                    font-size: 14px;
                    padding: 4px 0;
                    margin-left: 8px;
                }
            """)
            tip_label.setWordWrap(True)
            layout.addWidget(tip_label)
        
        return section
    
    def _setup_keyboard_navigation(self):
        """Set up comprehensive keyboard navigation and shortcuts.
        
        Configures a complete keyboard navigation system that provides
        efficient access to all application functionality without requiring
        mouse interaction. Implements accessibility best practices.
        
        Keyboard shortcuts implemented:
            Tab switching:
                - Ctrl+1-6: Switch to specific tabs by number
                - Alt+C/D/W/M/J/H: Switch using mnemonic letters
                - Ctrl+PageUp/PageDown: Navigate to previous/next tab
                - F1: Quick access to Help tab
                
            Tab order:
                - Logical tab order through all interactive elements
                - Proper focus indicators for accessibility
                - Tab wrapping for seamless navigation
                
        Accessibility features:
            - Proper ARIA roles and descriptions
            - High contrast focus indicators
            - Keyboard-only navigation support
            - Screen reader compatibility
            
        The navigation system ensures the application is fully accessible
        to users who rely on keyboard navigation or assistive technologies.
        """
        logger.debug("Setting up keyboard navigation")
        
        # Add tab switching shortcuts (Ctrl+1 through Ctrl+9)
        for i in range(min(9, self.tab_widget.count())):
            action = QAction(self)
            action.setShortcut(f"Ctrl+{i+1}")
            # Use default parameter to capture the value properly
            action.triggered.connect(lambda checked=False, index=i: self.tab_widget.setCurrentIndex(index))
            self.addAction(action)
        
        # Add Alt+Tab navigation shortcuts
        # Alt+C for Configuration, Alt+D for Daily, Alt+W for Weekly, 
        # Alt+M for Monthly, Alt+O for cOmpare, Alt+I for Insights,
        # Alt+T for Trophy, Alt+J for Journal, Alt+H for Help
        shortcuts = ['Alt+C', 'Alt+D', 'Alt+W', 'Alt+M', 'Alt+O', 'Alt+I', 'Alt+T', 'Alt+J', 'Alt+H']
        for i, shortcut in enumerate(shortcuts[:self.tab_widget.count()]):
            action = QAction(self)
            action.setShortcut(shortcut)
            # Use default parameter to capture the value properly
            action.triggered.connect(lambda checked=False, index=i: self.tab_widget.setCurrentIndex(index))
            self.addAction(action)
        
        # Add F1 shortcut for Help tab
        help_action = QAction(self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1))
        self.addAction(help_action)
        
        # Add tab navigation with Ctrl+PageUp/PageDown
        prev_tab_action = QAction(self)
        prev_tab_action.setShortcut("Ctrl+PageUp")
        prev_tab_action.triggered.connect(self._switch_to_previous_tab)
        self.addAction(prev_tab_action)
        
        next_tab_action = QAction(self)
        next_tab_action.setShortcut("Ctrl+PageDown")
        next_tab_action.triggered.connect(self._switch_to_next_tab)
        self.addAction(next_tab_action)
        
        # Set tab order for main window components
        self.setTabOrder(self.menuBar(), self.tab_widget)
        self.setTabOrder(self.tab_widget, self.statusBar())
    
    def _switch_to_previous_tab(self):
        """Switch to the previous tab."""
        current = self.tab_widget.currentIndex()
        if current > 0:
            self.tab_widget.setCurrentIndex(current - 1)
        else:
            # Wrap around to last tab
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
    
    def _switch_to_next_tab(self):
        """Switch to the next tab."""
        current = self.tab_widget.currentIndex()
        if current < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current + 1)
        else:
            # Wrap around to first tab
            self.tab_widget.setCurrentIndex(0)
    
    def _add_tab_hidden(self, widget, label, tooltip=""):
        """Add a tab to the tab widget and ensure it's hidden if not the first tab."""
        # Hide the widget if it's not the first tab
        if self.tab_widget.count() > 0:
            widget.setVisible(False)
        
        self.tab_widget.addTab(widget, label)
        if tooltip:
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, tooltip)
    
    def _ensure_only_current_tab_visible(self):
        """Ensure only the current tab is visible and all others are hidden."""
        current_index = self.tab_widget.currentIndex()
        logger.debug(f"Ensuring only tab {current_index} is visible")
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if widget:
                if i == current_index:
                    widget.setVisible(True)
                    # Special handling for scroll areas
                    if isinstance(widget, QScrollArea):
                        content = widget.widget()
                        if content:
                            content.setVisible(True)
                else:
                    widget.setVisible(False)
                    # Special handling for scroll areas
                    if isinstance(widget, QScrollArea):
                        content = widget.widget()
                        if content:
                            content.setVisible(False)
    
    def _create_status_bar(self):
        """Create the application status bar."""
        logger.debug("Creating status bar")
        
        # Get the status bar (QMainWindow provides this)
        status_bar = self.statusBar()
        status_bar.setStyleSheet(self.style_manager.get_status_bar_style())
        status_bar.showMessage("Ready")
        status_bar.setToolTip("Shows the current application status")
    
    def _on_tab_changed(self, index):
        """Handle tab change event with proper widget state management."""
        tab_name = self.tab_widget.tabText(index)
        logger.debug(f"Tab change requested: {self.previous_tab_index} -> {index} ({tab_name})")
        
        # Log current widget states for debugging
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if w:
                logger.debug(f"Tab {i}: visible={w.isVisible()}, enabled={w.isEnabled()}")
        
        # Store current widget state before switching
        if hasattr(self, 'previous_tab_index'):
            self._save_widget_state(self.previous_tab_index)
        
        # TEMPORARY: Disable all animations to fix refresh issues
        # TODO: Re-enable animations once core issues are resolved
        should_animate = False
        
        if should_animate:
            # Animation path (currently disabled)
            from_view = self.tab_to_view_map.get(self.previous_tab_index, ViewType.CONFIG)
            to_view = self.tab_to_view_map.get(index, ViewType.CONFIG)
            from_widget = self.tab_widget.widget(self.previous_tab_index)
            to_widget = self.tab_widget.widget(index)
            
            self.transition_manager.transition_to(
                from_widget, to_widget, from_view, to_view
            )
        else:
            # Use simplified immediate transition
            self._immediate_tab_switch(index, tab_name)
        
        # Update previous tab index
        self.previous_tab_index = index
    
    def _save_widget_state(self, tab_index: int):
        """Save the state of a widget before switching away."""
        widget = self.tab_widget.widget(tab_index)
        if not widget:
            return
            
        # Store any relevant state (scroll positions, selections, etc.)
        # This can be expanded based on specific widget needs
        state = {
            'index': tab_index,
            'visible': widget.isVisible(),
            'enabled': widget.isEnabled()
        }
        
        if isinstance(widget, QScrollArea):
            state['scroll_x'] = widget.horizontalScrollBar().value()
            state['scroll_y'] = widget.verticalScrollBar().value()
            
        logger.debug(f"Saved state for tab {tab_index}: {state}")
    
    def _immediate_tab_switch(self, index: int, tab_name: str):
        """Perform immediate tab switch without animations."""
        logger.debug(f"Performing immediate tab switch to {index} ({tab_name})")
        
        # Hide all tabs first to ensure clean state
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if widget and i != index:
                widget.setVisible(False)
                # Special handling for scroll areas
                if isinstance(widget, QScrollArea):
                    content = widget.widget()
                    if content:
                        content.setVisible(False)
        
        # Show the target tab
        widget = self.tab_widget.widget(index)
        if widget:
            widget.setVisible(True)
            # Special handling for scroll areas
            if isinstance(widget, QScrollArea):
                content = widget.widget()
                if content:
                    content.setVisible(True)
            
            # Ensure widget is properly updated
            widget.update()
            
        # Complete the transition
        self._complete_tab_change(index, tab_name)
    
    def _complete_tab_change(self, index: int, tab_name: str):
        """Complete tab change without animation - simplified version."""
        logger.debug(f"Completing tab change to: {tab_name}")
        self._update_trend_status()
        
        # Save the current tab index
        self.settings_manager.set_setting("MainWindow/lastActiveTab", index)
        
        # Unified refresh method without delays
        self._refresh_tab_data(index)
    
    def _refresh_tab_data(self, tab_index: int):
        """Unified tab refresh method without delays or complex logic."""
        widget = self.tab_widget.widget(tab_index)
        if not widget or not widget.isVisible():
            logger.debug(f"Tab {tab_index} not visible, skipping refresh")
            return
        
        # Check if we're in DataAccess mode (portable mode)
        if tab_index == 1 and hasattr(self, 'daily_dashboard'):
            # Daily tab
            if hasattr(self.daily_dashboard, 'data_access') and self.daily_dashboard.data_access:
                logger.debug("Daily tab - using DataAccess mode, triggering data load")
                if hasattr(self.daily_dashboard, '_load_daily_data'):
                    try:
                        self.daily_dashboard._load_daily_data()
                    except Exception as e:
                        logger.error(f"Error loading daily data: {e}")
                return
        elif tab_index == 2 and hasattr(self, 'weekly_dashboard'):
            # Weekly tab
            if hasattr(self.weekly_dashboard, 'data_access') and self.weekly_dashboard.data_access:
                logger.debug("Weekly tab - using DataAccess mode, triggering data load")
                if hasattr(self.weekly_dashboard, '_load_weekly_data'):
                    try:
                        self.weekly_dashboard._load_weekly_data()
                    except Exception as e:
                        logger.error(f"Error loading weekly data: {e}")
                return
            
        # Original logic for non-DataAccess mode
        # Get data without recreation
        data = self._get_current_data()
        if data is None:
            logger.warning(f"No data available for tab {tab_index}")
            return
        
        logger.debug(f"Refreshing tab {tab_index} with {len(data)} records")
        
        # Refresh specific tab
        if tab_index == 0:  # Config tab
            if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'refresh_display'):
                self.config_tab.refresh_display()
        elif tab_index == 1:  # Daily tab
            self._refresh_daily_with_data(data)
        elif tab_index == 2:  # Weekly tab
            self._refresh_weekly_with_data(data)
        elif tab_index == 3:  # Monthly tab
            self._refresh_monthly_with_data(data)
        elif tab_index == 4:  # Compare tab
            self._refresh_comparative_with_data(data)
    
    def _get_current_data(self):
        """Get current data from configuration tab."""
        if not hasattr(self, 'config_tab'):
            return None
            
        data = None
        if hasattr(self.config_tab, 'get_filtered_data'):
            data = self.config_tab.get_filtered_data()
        elif hasattr(self.config_tab, 'filtered_data'):
            data = self.config_tab.filtered_data
        elif hasattr(self.config_tab, 'data'):
            data = self.config_tab.data
            
        return data if data is not None and not data.empty else None
    
    def _get_or_create_calculators(self, data):
        """Get existing calculators or create new ones if data changed."""
        if data is None:
            return None
            
        # Check if data has changed
        data_hash = hash(str(data.shape) + str(data.columns.tolist()) + str(len(data)))
        
        if self._last_data_hash == data_hash and self._calculator_cache['daily_base'] is not None:
            logger.debug("Using cached calculators")
            return self._calculator_cache
        
        logger.debug("Creating new calculators due to data change")
        
        # Create new calculators only when data changes
        from ..analytics.cached_calculators import (
            CachedDailyMetricsCalculator,
            CachedMonthlyMetricsCalculator,
            CachedWeeklyMetricsCalculator,
        )
        from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
        from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
        from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator

        # Get local timezone
        local_tz = get_local_timezone()
        
        # Create base daily calculator
        daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
        self._calculator_cache['daily_base'] = daily_calculator
        
        # Create cached daily calculator
        self._calculator_cache['daily'] = CachedDailyMetricsCalculator(daily_calculator)
        
        # Create weekly calculator with the daily calculator
        weekly_calculator = WeeklyMetricsCalculator(daily_calculator)
        self._calculator_cache['weekly'] = CachedWeeklyMetricsCalculator(weekly_calculator)
        
        # Create monthly calculator with the daily calculator
        monthly_calculator = MonthlyMetricsCalculator(daily_calculator)
        self._calculator_cache['monthly'] = CachedMonthlyMetricsCalculator(monthly_calculator)
        
        self._last_data_hash = data_hash
        return self._calculator_cache
    
    def _refresh_daily_with_data(self, data):
        """Refresh daily dashboard with cached calculators."""
        logger.debug("Refreshing daily dashboard")
        if not hasattr(self, 'daily_dashboard'):
            return
            
        calculators = self._get_or_create_calculators(data)
        if not calculators:
            return
            
        # Set the cached calculator in the daily dashboard
        self.daily_dashboard.set_daily_calculator(calculators['daily'])
        
        # Set up cached data access for pre-computed summaries
        from ..analytics.cached_metrics_access import get_cached_metrics_access
        cached_data_access = get_cached_metrics_access()
        self.daily_dashboard.set_cached_data_access(cached_data_access)
        
        # Set personal records tracker
        self.daily_dashboard.set_personal_records(self.personal_records_tracker)
        
        logger.info(f"Daily dashboard refreshed with {len(data)} records")
    
    def _refresh_weekly_with_data(self, data):
        """Refresh weekly dashboard with cached calculators."""
        logger.debug("Refreshing weekly dashboard")
        if not hasattr(self, 'weekly_dashboard'):
            return
            
        calculators = self._get_or_create_calculators(data)
        if not calculators:
            return
            
        # Set the cached calculator in the weekly dashboard
        if hasattr(self.weekly_dashboard, 'set_weekly_calculator'):
            self.weekly_dashboard.set_weekly_calculator(calculators['weekly'])
        
        # Set up cached data access for pre-computed summaries
        from ..analytics.cached_data_access import CachedDataAccess
        cached_data_access = CachedDataAccess()
        if hasattr(self.weekly_dashboard, 'set_cached_data_access'):
            self.weekly_dashboard.set_cached_data_access(cached_data_access)
        
        logger.info(f"Weekly dashboard refreshed with {len(data)} records")
    
    def _refresh_monthly_with_data(self, data):
        """Refresh monthly dashboard with cached calculators."""
        logger.debug("Refreshing monthly dashboard")
        if not hasattr(self, 'monthly_dashboard'):
            return
            
        calculators = self._get_or_create_calculators(data)
        if not calculators:
            return
            
        # Set the cached calculator in the monthly dashboard
        if hasattr(self.monthly_dashboard, 'set_data_source'):
            self.monthly_dashboard.set_data_source(calculators['monthly'])
        
        # Set up cached data access for pre-computed summaries
        from ..analytics.cached_data_access import CachedDataAccess
        cached_data_access = CachedDataAccess()
        if hasattr(self.monthly_dashboard, 'set_cached_data_access'):
            self.monthly_dashboard.set_cached_data_access(cached_data_access)
        
        logger.info(f"Monthly dashboard refreshed with {len(data)} records")
    
    def _refresh_comparative_with_data(self, data):
        """Refresh comparative analytics with cached calculators."""
        logger.debug("Refreshing comparative analytics")
        if not hasattr(self, 'comparative_engine') or not hasattr(self, 'comparative_widget'):
            return
            
        calculators = self._get_or_create_calculators(data)
        if not calculators:
            return
            
        # Update comparative engine with cached calculators
        self.comparative_engine.daily_calculator = calculators['daily']
        self.comparative_engine.weekly_calculator = calculators['weekly']
        self.comparative_engine.monthly_calculator = calculators['monthly']
        
        # Re-set the engine in the widget to trigger updates
        self.comparative_widget.set_comparative_engine(self.comparative_engine)
        
        logger.info("Comparative analytics refreshed with new data")
    
    def _on_transition_started(self, from_view: ViewType, to_view: ViewType):
        """Handle transition start."""
        logger.debug(f"Transition started: {from_view.value} → {to_view.value}")
        self._update_trend_status()
    
    def _on_transition_completed(self, target_view: ViewType):
        """Handle transition completion - simplified version."""
        logger.debug(f"Transition completed: {target_view.value}")
        
        # Simply complete the tab change - refresh is handled by _complete_tab_change
        current_index = self.tab_widget.currentIndex()
        tab_name = self.tab_widget.tabText(current_index)
        self._complete_tab_change(current_index, tab_name)
    
    def _on_transition_interrupted(self):
        """Handle transition interruption."""
        logger.debug("Transition was interrupted")
        self.statusBar().showMessage("Transition interrupted")
    
    def toggle_accessibility_mode(self, enabled: bool):
        """Toggle accessibility mode for animations."""
        self.transition_manager.set_accessibility_mode(enabled)
        self.settings_manager.set_setting("accessibility/disable_animations", enabled)
        logger.info(f"Accessibility mode {'enabled' if enabled else 'disabled'}")
    
    def _on_import_data(self):
        """Handle data import action."""
        logger.info("Import data action triggered")
        # Switch to configuration tab and trigger import
        self.tab_widget.setCurrentIndex(0)  # Configuration tab is index 0
        if hasattr(self.config_tab, '_on_browse_clicked'):
            logger.info("Calling config_tab._on_browse_clicked()")
            self.config_tab._on_browse_clicked()
        else:
            logger.error("config_tab does not have _on_browse_clicked method")
    
    def _on_save_configuration(self):
        """Handle save configuration action."""
        logger.info("Save configuration action triggered")
        # Switch to configuration tab and trigger save preset
        self.tab_widget.setCurrentIndex(0)  # Configuration tab is index 0
        if hasattr(self.config_tab, '_on_save_preset_clicked'):
            self.config_tab._on_save_preset_clicked()
        else:
            QMessageBox.information(
                self,
                "Save Configuration",
                "Configuration saving functionality is available in the Configuration tab."
            )
    
    def _on_show_shortcuts(self):
        """Show keyboard shortcuts reference dialog."""
        logger.info("Keyboard shortcuts dialog requested")
        shortcuts_html = """
        <h2>Keyboard Shortcuts</h2>
        
        <h3>Navigation</h3>
        <table>
        <tr><td><b>Tab / Shift+Tab</b></td><td>Navigate between elements</td></tr>
        <tr><td><b>Ctrl+1 to Ctrl+6</b></td><td>Switch to specific tab</td></tr>
        <tr><td><b>Alt+C/D/W/M/J/H</b></td><td>Switch to Configuration/Daily/Weekly/Monthly/Journal/Help tab</td></tr>
        <tr><td><b>Ctrl+PageUp/PageDown</b></td><td>Navigate to previous/next tab</td></tr>
        </table>
        
        <h3>File Operations</h3>
        <table>
        <tr><td><b>Ctrl+O</b></td><td>Import data file (CSV or XML)</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save configuration</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit application</td></tr>
        </table>
        
        <h3>Configuration Tab</h3>
        <table>
        <tr><td><b>Alt+B</b></td><td>Browse for file</td></tr>
        <tr><td><b>Alt+I</b></td><td>Import data</td></tr>
        <tr><td><b>Alt+A</b></td><td>Apply filters</td></tr>
        <tr><td><b>Alt+R</b></td><td>Reset filters</td></tr>
        </table>
        
        <h3>Multi-Select Dropdowns</h3>
        <table>
        <tr><td><b>Space</b></td><td>Toggle selected item</td></tr>
        <tr><td><b>Ctrl+A</b></td><td>Select all items</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Deselect all items</td></tr>
        <tr><td><b>Enter</b></td><td>Confirm selection</td></tr>
        <tr><td><b>Escape</b></td><td>Close dropdown</td></tr>
        </table>
        
        <h3>General</h3>
        <table>
        <tr><td><b>Ctrl+?</b></td><td>Show this help</td></tr>
        <tr><td><b>F1</b></td><td>Open Help tab</td></tr>
        <tr><td><b>Enter/Space</b></td><td>Activate buttons</td></tr>
        <tr><td><b>Escape</b></td><td>Close dialogs</td></tr>
        </table>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(shortcuts_html)
        msg_box.setStyleSheet("""
            QMessageBox {
                min-width: 600px;
            }
            QMessageBox QLabel {
                min-width: 550px;
            }
        """)
        msg_box.exec()
    
    def _on_about(self):
        """Show about dialog."""
        logger.info("About dialog requested")
        QMessageBox.about(
            self,
            "About Apple Health Monitor",
            "<h2>Apple Health Monitor Dashboard</h2>"
            "<p>A warm and inviting dashboard for analyzing your Apple Health data.</p>"
            "<p>Built with PyQt6 and Python.</p>"
        )
    
    def _perform_data_erasure(self):
        """Perform the actual data erasure after confirmation.
        
        This method handles the complete data erasure process including:
        - Shutting down cache managers and background processors
        - Closing database connections
        - Deleting database files and cache directories
        - Resetting the UI to its initial state
        
        This is a shared method used by both the menu action and the configuration
        tab's clear data button to ensure consistent behavior.
        
        Returns:
            bool: True if successful, False if operation failed
        """
        logger.info("Starting data erasure process")
        
        # Create progress dialog
        from PyQt6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Erasing all data...", None, 0, 0, self)
        progress.setWindowTitle("Erasing Data")
        progress.setModal(True)
        progress.setCancelButton(None)  # Remove cancel button since operation cannot be canceled
        progress.setMinimumDuration(0)  # Show immediately
        progress.show()
        QApplication.processEvents()
        
        try:
            # 1. Shutdown cache manager and background processes
            try:
                from ..analytics.cache_manager import shutdown_cache_manager
                shutdown_cache_manager()
                logger.info("Shutdown cache manager")
                
                # Force garbage collection to clear any lingering references
                import gc
                gc.collect()
                
                # Small delay to ensure file handles are released
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not shutdown cache manager: {e}")
            
            # 2. Shutdown any background processors with timeout protection
            # Check if any tabs have background processors
            from PyQt6.QtCore import QTimer
            shutdown_start_time = time.time()
            
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'background_processor') and tab.background_processor:
                    try:
                        # Set a reasonable timeout for background processor shutdown
                        processor_start_time = time.time()
                        tab.background_processor.shutdown()
                        
                        # Check if shutdown took too long
                        shutdown_duration = time.time() - processor_start_time
                        if shutdown_duration > 3.0:  # More than 3 seconds
                            logger.warning(f"Background processor shutdown for tab {i} took {shutdown_duration:.1f} seconds")
                        else:
                            logger.info(f"Shutdown background processor for tab {i} in {shutdown_duration:.1f} seconds")
                            
                    except Exception as e:
                        logger.warning(f"Could not shutdown background processor for tab {i}: {e}")
            
            total_shutdown_time = time.time() - shutdown_start_time
            if total_shutdown_time > 5.0:  # More than 5 seconds total
                logger.warning(f"Total background processor shutdown took {total_shutdown_time:.1f} seconds")
            
            # Update progress dialog
            progress.setLabelText("Closing database connections...")
            QApplication.processEvents()
            
            # 3. Close database connections
            if hasattr(db_manager, 'close'):
                db_manager.close()
                logger.info("Closed database connections")
            
            # 4. Small delay to ensure all connections are closed
            progress.setLabelText("Ensuring database connections are closed...")
            QApplication.processEvents()
            time.sleep(0.5)
            
            # 5. Clear health data from database while preserving structure and user settings
            progress.setLabelText("Clearing health data from database...")
            QApplication.processEvents()
            try:
                deleted_counts = db_manager.clear_all_health_data()
                total_deleted = sum(deleted_counts.values())
                logger.info(f"Cleared {total_deleted} health records from database")
                for table, count in deleted_counts.items():
                    if count > 0:
                        logger.info(f"  - Deleted {count} records from {table}")
            except Exception as e:
                logger.error(f"Failed to clear health data: {e}")
                raise
            
            # 6. Delete analytics cache database with retry
            progress.setLabelText("Deleting analytics cache...")
            QApplication.processEvents()
            
            # Function to delete cache database and associated files
            def delete_cache_files(base_path: str) -> bool:
                """Delete cache database and associated WAL/SHM files."""
                deleted = False
                files_to_delete = [
                    base_path,
                    f"{base_path}-wal",
                    f"{base_path}-shm"
                ]
                
                for file_path in files_to_delete:
                    if os.path.exists(file_path):
                        for attempt in range(5):  # Increased retry attempts
                            try:
                                os.remove(file_path)
                                logger.info(f"Deleted {file_path}")
                                deleted = True
                                break
                            except PermissionError as e:
                                if attempt < 4:
                                    logger.warning(f"File locked: {file_path}, retrying... (attempt {attempt + 1}/5)")
                                    # Progressively longer waits
                                    time.sleep(0.5 * (attempt + 1))
                                    # Try garbage collection to release handles
                                    import gc
                                    gc.collect()
                                else:
                                    logger.warning(f"Could not delete {file_path} (file locked): {e}")
                            except Exception as e:
                                logger.error(f"Unexpected error deleting {file_path}: {e}")
                                break
                
                return deleted
            
            # Delete cache in DATA_DIR
            analytics_cache_db = os.path.join(DATA_DIR, "analytics_cache.db")
            delete_cache_files(analytics_cache_db)
            
            # Also check in current directory
            delete_cache_files("analytics_cache.db")
            
            # 7. Delete cache directory
            progress.setLabelText("Deleting cache directories...")
            QApplication.processEvents()
            
            # Helper function to safely delete directory on Windows
            def safe_rmtree(path):
                """Safely remove directory tree, handling Windows file locks."""
                if not os.path.exists(path):
                    return
                    
                # First try normal deletion
                try:
                    shutil.rmtree(path)
                    return True
                except Exception as e:
                    logger.warning(f"First attempt to delete {path} failed: {e}")
                
                # If that fails, try to remove files individually
                try:
                    # Walk through directory and delete files first
                    for root, dirs, files in os.walk(path, topdown=False):
                        for name in files:
                            file_path = os.path.join(root, name)
                            try:
                                os.chmod(file_path, 0o777)  # Make writable
                                os.remove(file_path)
                            except Exception as e:
                                logger.warning(f"Could not delete file {file_path}: {e}")
                        
                        # Then try to remove empty directories
                        for name in dirs:
                            dir_path = os.path.join(root, name)
                            try:
                                os.chmod(dir_path, 0o777)  # Make writable
                                os.rmdir(dir_path)
                            except Exception as e:
                                logger.warning(f"Could not delete directory {dir_path}: {e}")
                    
                    # Finally try to remove the root directory
                    try:
                        os.chmod(path, 0o777)  # Make writable
                        os.rmdir(path)
                        return True
                    except Exception as e:
                        logger.warning(f"Could not delete root directory {path}: {e}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Failed to manually delete {path}: {e}")
                    return False
            
            cache_dir = os.path.join(DATA_DIR, "cache")
            if os.path.exists(cache_dir):
                if safe_rmtree(cache_dir):
                    logger.info(f"Deleted cache directory: {cache_dir}")
                else:
                    logger.warning(f"Could not completely delete cache directory: {cache_dir}")
                
            # Also check for cache in current directory
            if os.path.exists("cache"):
                if safe_rmtree("cache"):
                    logger.info("Deleted cache directory from current directory")
                else:
                    logger.warning("Could not completely delete cache directory from current directory")
            
            # 8. Clear filter configurations from database
            progress.setLabelText("Clearing filter configurations...")
            QApplication.processEvents()
            if hasattr(self.config_tab, 'filter_config_manager'):
                # Clear filter configs - already handled by clear_all_health_data() above
                # but do it again in case it uses a separate database
                self.config_tab.filter_config_manager.clear_all_presets()
                logger.info("Cleared filter configurations")
            
            # 9. Reset UI
            progress.setLabelText("Resetting user interface...")
            QApplication.processEvents()
            if hasattr(self.config_tab, 'data'):
                self.config_tab.data = None
                self.config_tab.filtered_data = None
                self.config_tab.data_available = False
                
                # Clear filter dropdowns
                if hasattr(self.config_tab, 'device_dropdown'):
                    self.config_tab.device_dropdown.clear()
                if hasattr(self.config_tab, 'metric_dropdown'):
                    self.config_tab.metric_dropdown.clear()
                
                # Disable filter controls
                if hasattr(self.config_tab, '_enable_filter_controls'):
                    self.config_tab._enable_filter_controls(False)
                
                # Reset summary cards
                if hasattr(self.config_tab, 'total_records_card'):
                    self.config_tab.total_records_card.update_content({'value': "-"})
                if hasattr(self.config_tab, 'filtered_records_card'):
                    self.config_tab.filtered_records_card.update_content({'value': "-"})
                if hasattr(self.config_tab, 'data_source_card'):
                    self.config_tab.data_source_card.update_content({'value': "None"})
                if hasattr(self.config_tab, 'filter_status_card'):
                    self.config_tab.filter_status_card.update_content({'value': "N/A"})
                
                # Clear statistics
                if hasattr(self.config_tab, '_update_custom_statistics'):
                    self.config_tab._update_custom_statistics(None)
                
                # Update progress label
                if hasattr(self.config_tab, 'progress_label'):
                    self.config_tab.progress_label.setText("All health data cleared")
                
            # Update UI to reflect empty state
            if hasattr(self.config_tab, 'refresh_display'):
                self.config_tab.refresh_display()
                
            # Disable other tabs since no data is loaded
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
            
            # Switch to configuration tab
            self.tab_widget.setCurrentIndex(0)
            
            # Close progress dialog before showing success message
            progress.close()
            
            # Show success message
            QMessageBox.information(
                self,
                "Data Erased",
                "All health data has been successfully erased.\n\n"
                "Your user preferences and database structure have been preserved.\n"
                "You can now import new health data."
            )
            
            # Update status bar
            self.statusBar().showMessage("All data erased successfully")
            logger.info("All data erased successfully")
            
            # Emit signal if available
            if hasattr(self.config_tab, 'data_cleared'):
                self.config_tab.data_cleared.emit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to erase data: {e}")
            # Close progress dialog before showing error message
            progress.close()
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to erase all data:\n\n{str(e)}"
            )
            return False
        finally:
            # Ensure the progress dialog is closed (defensive programming)
            if progress and hasattr(progress, 'close'):
                try:
                    progress.close()
                except:
                    pass  # Ignore any errors during cleanup
    
    def _on_erase_all_data(self):
        """Handle erase all data action."""
        logger.info("Erase all data action triggered")
        
        # Show warning dialog with Yes/No options
        reply = QMessageBox.warning(
            self,
            "Erase All Data",
            "<h3>Warning: This action cannot be undone!</h3>"
            "<p>This will permanently delete:</p>"
            "<ul>"
            "<li>All imported health data from the database</li>"
            "<li>All cached calculations and analytics</li>"
            "<li>All filter presets and configurations</li>"
            "<li>All achievement and personal records</li>"
            "</ul>"
            "<p>Your user preferences and database structure will be preserved.</p>"
            "<p><b>Are you sure you want to continue?</b></p>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._perform_data_erasure()
        else:
            logger.info("User cancelled erase all data operation")
    
    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        size = event.size()
        logger.debug(f"Window resized to {size.width()}x{size.height()}")
        
        # Adapt layout based on size if needed
        if size.width() < 1200:
            # Could implement compact mode here
            pass
    
    def _on_data_loaded(self, data):
        """Handle data loaded signal from configuration tab.
        
        CRITICAL FIX: Now refreshes ALL dashboard tabs, not just the current one.
        This ensures data is propagated to all tabs when imported or when filters change.
        """
        # If data is None, fetch it from config tab
        if data is None:
            data = self.config_tab.get_filtered_data()
            if data is None:
                logger.warning("No data available after signal emission")
                return
        
        logger.info(f"Data loaded: {len(data) if data is not None else 0} records")
        self.statusBar().showMessage(f"Loaded {len(data):,} health records")
        
        # Enable other tabs when data is loaded
        if data is not None and not data.empty:
            logger.info("Enabling all dashboard tabs and refreshing data")
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
            
            # CRITICAL FIX: Refresh ALL tabs, not just current tab
            logger.debug("Refreshing all dashboard tabs with new data")
            try:
                # Refresh daily dashboard
                logger.debug("Refreshing daily dashboard")
                self._refresh_daily_data()
                
                # Refresh weekly dashboard  
                logger.debug("Refreshing weekly dashboard")
                self._refresh_weekly_data()
                
                # Refresh monthly dashboard
                logger.debug("Refreshing monthly dashboard")
                self._refresh_monthly_data()
                
                # Update comparative analytics engine with new calculators
                logger.debug("Refreshing comparative analytics")
                self._refresh_comparative_data()
                
                logger.info("Successfully refreshed all dashboard tabs")
                
            except Exception as e:
                logger.error(f"Error refreshing dashboard tabs: {e}", exc_info=True)
                self.statusBar().showMessage(f"Data loaded with some errors: {str(e)}")
                
        else:
            logger.warning("No data loaded or data is empty - disabling dashboard tabs")
            # Disable other tabs if no data
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
    
    def _handle_metric_selection(self, metric_name: str):
        """Handle metric selection from daily dashboard.
        
        Args:
            metric_name: The name of the selected metric
        """
        logger.debug(f"Metric selected: {metric_name}")
    
    def _handle_date_change(self, new_date: date):
        """Handle date change from daily dashboard.
        
        Args:
            new_date: The newly selected date
        """
        logger.debug(f"Date changed to: {new_date}")
    
    def _refresh_daily_data(self):
        """Refresh data in the daily dashboard."""
        logger.debug("Refreshing daily dashboard data")
        if hasattr(self, 'daily_dashboard'):
            # Get current data from configuration tab
            data = None
            if hasattr(self, 'config_tab'):
                if hasattr(self.config_tab, 'get_filtered_data'):
                    data = self.config_tab.get_filtered_data()
                elif hasattr(self.config_tab, 'filtered_data'):
                    data = self.config_tab.filtered_data
                    
                if data is not None and not data.empty:
                    # Create cached daily calculator with the data
                    from ..analytics.cached_calculators import CachedDailyMetricsCalculator
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator

                    # Get local timezone
                    local_tz = get_local_timezone()
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    cached_daily_calculator = CachedDailyMetricsCalculator(daily_calculator)
                    
                    # Set the cached calculator in the daily dashboard
                    self.daily_dashboard.set_daily_calculator(cached_daily_calculator)
                    
                    # Set up cached data access for pre-computed summaries
                    from ..analytics.cached_metrics_access import get_cached_metrics_access
                    cached_data_access = get_cached_metrics_access()
                    self.daily_dashboard.set_cached_data_access(cached_data_access)
                    
                    # Create and set personal records tracker
                    if not hasattr(self, 'personal_records_tracker'):
                        self.personal_records_tracker = PersonalRecordsTracker(db_manager)
                    self.daily_dashboard.set_personal_records(self.personal_records_tracker)
                    
                    logger.info(f"Set daily calculator with {len(data)} records")
                else:
                    logger.warning("No data available to refresh daily dashboard")
        
        # Trigger background trend calculation for all metrics
        if self.background_trend_processor and hasattr(self, 'config_tab'):
            data = None
            if hasattr(self.config_tab, 'get_filtered_data'):
                data = self.config_tab.get_filtered_data()
            elif hasattr(self.config_tab, 'filtered_data'):
                data = self.config_tab.filtered_data
                
            if data is not None:
                logger.info("Triggering background trend calculation for all metrics")
                # Get unique metrics from the data
                if hasattr(data, 'columns') and 'type' in data.columns:
                    unique_metrics = data['type'].unique().tolist()
                    for metric in unique_metrics:
                        if hasattr(self.background_trend_processor, 'VALID_METRICS'):
                            if metric in self.background_trend_processor.VALID_METRICS:
                                self.background_trend_processor.queue_trend_calculation(
                                    metric, priority=5, force_refresh=True
                                )
                        else:
                            # Queue without validation if VALID_METRICS not available
                            self.background_trend_processor.queue_trend_calculation(
                                metric, priority=5, force_refresh=True
                            )
                else:
                    # Queue all known metrics
                    if hasattr(self.background_trend_processor, 'queue_all_metrics'):
                        self.background_trend_processor.queue_all_metrics(priority=5)
        
        # Trigger health insights generation if available
        if hasattr(self, 'health_insights_widget') and data is not None:
            # Prepare user data for health insights
            user_data = {
                'data': data,
                'timezone': get_local_timezone() if 'get_local_timezone' in locals() else None
            }
            self.health_insights_widget.load_insights(user_data)
    
    def _refresh_weekly_data(self):
        """Refresh data in the weekly dashboard."""
        logger.debug("Refreshing weekly dashboard data")
        if hasattr(self, 'weekly_dashboard'):
            # Get current data from configuration tab
            data = None
            if hasattr(self, 'config_tab'):
                if hasattr(self.config_tab, 'get_filtered_data'):
                    data = self.config_tab.get_filtered_data()
                elif hasattr(self.config_tab, 'filtered_data'):
                    data = self.config_tab.filtered_data
                    
                if data is not None and not data.empty:
                    # Create cached calculators
                    from ..analytics.cached_calculators import (
                        CachedDailyMetricsCalculator,
                        CachedWeeklyMetricsCalculator,
                    )
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator

                    # Get local timezone
                    local_tz = get_local_timezone()
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    cached_daily_calculator = CachedDailyMetricsCalculator(daily_calculator)
                    
                    # Create cached weekly calculator with the daily calculator
                    weekly_calculator = WeeklyMetricsCalculator(daily_calculator)
                    cached_weekly_calculator = CachedWeeklyMetricsCalculator(weekly_calculator)
                    
                    # Set the cached calculator in the weekly dashboard
                    if hasattr(self.weekly_dashboard, 'set_weekly_calculator'):
                        self.weekly_dashboard.set_weekly_calculator(cached_weekly_calculator)
                    
                    # Set up cached data access for pre-computed summaries
                    from ..analytics.cached_data_access import CachedDataAccess
                    cached_data_access = CachedDataAccess()
                    if hasattr(self.weekly_dashboard, 'set_cached_data_access'):
                        self.weekly_dashboard.set_cached_data_access(cached_data_access)
                    
                    logger.info(f"Set weekly calculator with {len(data)} records")
                else:
                    logger.warning("No data available to refresh weekly dashboard")
    
    def _refresh_monthly_data(self):
        """Refresh data in the monthly dashboard."""
        logger.debug("Refreshing monthly dashboard data")
        if hasattr(self, 'monthly_dashboard'):
            # Force the widget to be visible first
            self.monthly_dashboard.show()
            self.monthly_dashboard.raise_()
            QApplication.processEvents()
            
            # Get current data from configuration tab
            data = None
            if hasattr(self, 'config_tab'):
                if hasattr(self.config_tab, 'get_filtered_data'):
                    data = self.config_tab.get_filtered_data()
                elif hasattr(self.config_tab, 'filtered_data'):
                    data = self.config_tab.filtered_data
                    
                if data is not None and not data.empty:
                    # Create cached calculators
                    from ..analytics.cached_calculators import (
                        CachedDailyMetricsCalculator,
                        CachedMonthlyMetricsCalculator,
                    )
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator

                    # Get local timezone
                    local_tz = get_local_timezone()
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    cached_daily_calculator = CachedDailyMetricsCalculator(daily_calculator)
                    
                    # Create cached monthly calculator with the daily calculator
                    monthly_calculator = MonthlyMetricsCalculator(daily_calculator)
                    cached_monthly_calculator = CachedMonthlyMetricsCalculator(monthly_calculator)
                    
                    # Set the cached calculator in the monthly dashboard
                    if hasattr(self.monthly_dashboard, 'set_data_source'):
                        self.monthly_dashboard.set_data_source(cached_monthly_calculator)
                    
                    # Set up cached data access for pre-computed summaries
                    from ..analytics.cached_data_access import CachedDataAccess
                    cached_data_access = CachedDataAccess()
                    if hasattr(self.monthly_dashboard, 'set_cached_data_access'):
                        self.monthly_dashboard.set_cached_data_access(cached_data_access)
                    
                    logger.info(f"Set monthly calculator with {len(data)} records")
                else:
                    logger.warning("No data available to refresh monthly dashboard")
            
            # Trigger the showEvent manually to ensure full refresh
            if hasattr(self.monthly_dashboard, 'showEvent'):
                from PyQt6.QtGui import QShowEvent
                self.monthly_dashboard.showEvent(QShowEvent())
            
            # Force a repaint
            self.monthly_dashboard.update()
            QApplication.processEvents()
    
    def _refresh_comparative_data(self):
        """Refresh the comparative analytics tab with new data."""
        logger.debug("Refreshing comparative analytics data")
        
        if hasattr(self, 'comparative_engine') and hasattr(self, 'comparative_widget'):
            # Update the comparative engine with new calculators
            if hasattr(self, 'config_tab'):
                # Get or create calculators
                data = None
                
                # First check if we have filtered data
                if hasattr(self.config_tab, 'filtered_data') and self.config_tab.filtered_data is not None:
                    data = self.config_tab.filtered_data
                # Then check if we have loaded data
                elif hasattr(self.config_tab, 'data') and self.config_tab.data is not None:
                    data = self.config_tab.data
                # Try to load data if not already loaded
                else:
                    try:
                        from ..config import DATA_DIR

                        # Check if database exists
                        db_path = os.path.join(DATA_DIR, "health_data.db")
                        if os.path.exists(db_path) and hasattr(self.config_tab, 'data_loader'):
                            logger.info("Loading data from database for comparative analytics")
                            # Ensure data is loaded
                            if hasattr(self.config_tab, '_ensure_data_loaded'):
                                self.config_tab._ensure_data_loaded()
                                data = self.config_tab.data
                            else:
                                # Direct load if method doesn't exist
                                self.config_tab.data = self.config_tab.data_loader.get_all_records()
                                data = self.config_tab.data
                    except Exception as e:
                        logger.error(f"Failed to load data for comparative analytics: {e}")
                
                if data is not None and not data.empty:
                    # Create cached calculators
                    from ..analytics.cached_calculators import (
                        CachedDailyMetricsCalculator,
                        CachedMonthlyMetricsCalculator,
                        CachedWeeklyMetricsCalculator,
                    )
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
                    from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator

                    # Get local timezone
                    local_tz = get_local_timezone()
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    cached_daily_calculator = CachedDailyMetricsCalculator(daily_calculator)
                    
                    weekly_calculator = WeeklyMetricsCalculator(daily_calculator)
                    cached_weekly_calculator = CachedWeeklyMetricsCalculator(weekly_calculator)
                    
                    monthly_calculator = MonthlyMetricsCalculator(data)
                    cached_monthly_calculator = CachedMonthlyMetricsCalculator(monthly_calculator)
                    
                    # Update comparative engine with cached calculators
                    self.comparative_engine.daily_calculator = cached_daily_calculator
                    self.comparative_engine.weekly_calculator = cached_weekly_calculator
                    self.comparative_engine.monthly_calculator = cached_monthly_calculator
                    
                    # Re-set the engine in the widget to trigger updates
                    self.comparative_widget.set_comparative_engine(self.comparative_engine)
                    
                    logger.info("Updated comparative analytics with new data")
                else:
                    logger.info("No data available yet - comparative analytics will update when data is loaded")
    
    def _on_filters_applied(self, filters):
        """Handle filters applied signal from configuration tab."""
        logger.info(f"Filters applied: {filters}")
        self.statusBar().showMessage("Filters applied successfully")
        
        # TODO: Pass filtered data to other tabs
        # This will be implemented when other tabs are created
        
    def _on_month_changed(self, year: int, month: int):
        """Handle month change signal from monthly dashboard."""
        logger.info(f"Month changed to: {year}-{month:02d}")
        self.statusBar().showMessage(f"Viewing {year}-{month:02d}")
        
    def _on_metric_changed(self, metric: str):
        """Handle metric change signal from monthly dashboard."""
        logger.info(f"Metric changed to: {metric}")
        self.statusBar().showMessage(f"Displaying {metric} data")
    
    def _on_week_changed(self, start_date: date, end_date: date):
        """Handle week change signal from weekly dashboard."""
        logger.info(f"Week changed to: {start_date} - {end_date}")
        self.statusBar().showMessage(f"Viewing week of {start_date.strftime('%B %d')}")
    
    def _on_metric_selected(self, metric: str):
        """Handle metric selection signal from weekly dashboard."""
        logger.info(f"Weekly metric selected: {metric}")
        self.statusBar().showMessage(f"Weekly view: {metric}")
    
    def _on_insight_selected(self, insight):
        """Handle insight selection."""
        logger.info(f"Insight selected: {insight.title}")
        # Could navigate to relevant data view or show detailed dialog
        self.statusBar().showMessage(f"Selected: {insight.title}")
    
    def _prepare_data_for_insights(self, data):
        """Convert DataFrame to format expected by insights engine."""
        # Group data by metric type
        user_data = {}
        
        if 'type' in data.columns:
            # Common health metrics mapping
            metric_mapping = {
                'HKQuantityTypeIdentifierStepCount': 'daily_steps',
                'HKQuantityTypeIdentifierSleepAnalysis': 'sleep_duration',
                'HKQuantityTypeIdentifierRestingHeartRate': 'resting_heart_rate',
                'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_calories',
                'HKQuantityTypeIdentifierBodyMass': 'body_weight',
                'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv'
            }
            
            for metric_type, metric_name in metric_mapping.items():
                metric_data = data[data['type'] == metric_type].copy()
                if not metric_data.empty:
                    # Ensure proper columns
                    if 'startDate' in metric_data.columns:
                        metric_data['date'] = pd.to_datetime(metric_data['startDate'])
                    if 'value' in metric_data.columns:
                        metric_data[metric_name] = metric_data['value']
                    
                    user_data[metric_name] = metric_data[['date', metric_name]]
        
        return user_data
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            # Check if any dialogs are open
            for widget in self.findChildren(QMessageBox):
                if widget.isVisible():
                    widget.close()
                    return
            
            # Check if any dropdown is open
            for widget in self.findChildren(QComboBox):
                if widget.view().isVisible():
                    widget.hidePopup()
                    return
        
        super().keyPressEvent(event)
    
    def _update_trend_status(self):
        """Update the status bar with background trend processing information."""
        try:
            if self.background_trend_processor:
                status = self.background_trend_processor.get_processing_status()
                
                # Format the status message
                queue_size = status.get('queue_size', 0)
                processing = status.get('processing', [])
                cached_count = len(status.get('cached_metrics', []))
                
                if processing:
                    # Show what's currently being processed
                    metric_names = ', '.join([self._format_metric_name(m) for m in processing[:2]])
                    if len(processing) > 2:
                        metric_names += f" (+{len(processing) - 2} more)"
                    msg = f"📊 Processing trends: {metric_names}"
                elif queue_size > 0:
                    msg = f"📊 {queue_size} trend{'s' if queue_size != 1 else ''} queued for processing"
                else:
                    msg = f"✓ All trends calculated ({cached_count} metrics cached)"
                
                self.statusBar().showMessage(msg)
            else:
                # No background processor available
                self.statusBar().showMessage("Ready")
        except Exception as e:
            logger.error(f"Error updating trend status: {e}")
            self.statusBar().showMessage("Ready")
    
    def _format_metric_name(self, metric: str) -> str:
        """Format metric identifier to readable name."""
        # Simple formatting - remove prefix and make readable
        name = metric.replace('HKQuantityTypeIdentifier', '')
        name = name.replace('HKCategoryTypeIdentifier', '')
        # Convert camelCase to spaced words
        import re
        name = re.sub(r'([A-Z])', r' \1', name).strip()
        return name
    
    def showEvent(self, event):
        """Handle window show event."""
        logger.info("Main window showEvent triggered")
        super().showEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closeEvent triggered")
        logger.info(f"Event spontaneous: {event.spontaneous()}")
        logger.info(f"Event type: {event.type()}")
        
        # Log stack trace to see what's calling close
        import traceback
        logger.info("Close event stack trace:")
        for line in traceback.format_stack():
            logger.info(line.strip())
        
        logger.info("Main window closing, saving state")
        
        # Stop the status update timer
        self.status_update_timer.stop()
        
        # Save window state before closing
        self.settings_manager.save_window_state(self)
        
        # Shutdown background trend processor
        if self.background_trend_processor:
            logger.info("Shutting down background trend processor")
            self.background_trend_processor.shutdown()
        
        # Accept the close event
        event.accept()
    
    def _on_export_report(self):
        """Handle export report action."""
        logger.info("Export report action triggered")
        
        # Check if data is loaded
        if not hasattr(self, 'config_tab') or not hasattr(self.config_tab, 'get_filtered_data'):
            QMessageBox.warning(
                self,
                "No Data",
                "Please load data first before exporting."
            )
            return
            
        data = self.config_tab.get_filtered_data()
        if data is None or data.empty:
            QMessageBox.warning(
                self,
                "No Data",
                "No data available to export. Please load and filter data first."
            )
            return
            
        # Create export system if not already created
        if not hasattr(self, 'export_system'):
            self._initialize_export_system()
            
        # Get available metrics
        available_metrics = self._get_available_metrics(data)
        
        # Import and show export dialog
        from .export_dialog import ExportDialog
        
        dialog = ExportDialog(
            self.export_system,
            available_metrics,
            self
        )
        
        if dialog.exec():
            self.statusBar().showMessage("Export completed successfully")
            
    def _on_quick_export(self, export_type: str):
        """Handle quick export actions."""
        logger.info(f"Quick export triggered: {export_type}")
        
        # Check if data is loaded
        if not hasattr(self, 'config_tab') or not hasattr(self.config_tab, 'get_filtered_data'):
            QMessageBox.warning(
                self,
                "No Data",
                "Please load data first before exporting."
            )
            return
            
        data = self.config_tab.get_filtered_data()
        if data is None or data.empty:
            QMessageBox.warning(
                self,
                "No Data",
                "No data available to export. Please load and filter data first."
            )
            return
            
        # Create export system if not already created
        if not hasattr(self, 'export_system'):
            self._initialize_export_system()
            
        # Import necessary classes
        from datetime import datetime, timedelta
        from pathlib import Path

        from PyQt6.QtWidgets import QFileDialog, QProgressDialog

        from ..analytics.export_reporting_system import (
            ExportConfiguration,
            ExportFormat,
            ReportTemplate,
        )

        # Create configuration for quick export
        format_map = {
            'pdf': ExportFormat.PDF,
            'excel': ExportFormat.EXCEL,
            'csv': ExportFormat.CSV
        }
        
        export_format = format_map.get(export_type, ExportFormat.PDF)
        
        # Get date range from data
        if 'startDate' in data.columns:
            dates = pd.to_datetime(data['startDate'])
            date_range = (dates.min().to_pydatetime(), dates.max().to_pydatetime())
        else:
            date_range = (datetime.now() - timedelta(days=30), datetime.now())
            
        # Get available metrics
        available_metrics = self._get_available_metrics(data)
        
        # Create export configuration
        config = ExportConfiguration(
            format=export_format,
            date_range=date_range,
            metrics=available_metrics,
            include_charts=(export_format == ExportFormat.PDF),
            include_insights=(export_format == ExportFormat.PDF),
            template=ReportTemplate.COMPREHENSIVE
        )
        
        # Get save location
        filter_map = {
            'pdf': "PDF Files (*.pdf)",
            'excel': "Excel Files (*.xlsx)",
            'csv': "CSV Files (*.csv)"
        }
        
        filename = f"health_export_{datetime.now().strftime('%Y%m%d')}"
        extension_map = {'pdf': '.pdf', 'excel': '.xlsx', 'csv': '.csv'}
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {export_type.upper()} Export",
            filename + extension_map[export_type],
            filter_map[export_type]
        )
        
        if not file_path:
            return
            
        # Create progress dialog
        progress = QProgressDialog("Generating export...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # Generate export
            result = self.export_system.generate_report(config)
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(result)
                
            progress.setValue(100)
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Export saved successfully to:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to generate export:\n{str(e)}"
            )
        finally:
            progress.close()
            
    def _on_create_backup(self):
        """Handle create backup action."""
        logger.info("Create backup action triggered")
        
        # Create export system if not already created
        if not hasattr(self, 'export_system'):
            self._initialize_export_system()
            
        from datetime import datetime

        from PyQt6.QtWidgets import QFileDialog, QProgressDialog

        # Get save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup",
            f"health_backup_{datetime.now().strftime('%Y%m%d')}.zip",
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
            
        # Create progress dialog
        progress = QProgressDialog("Creating backup...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # Create backup
            backup_data = self.export_system.create_backup(include_settings=True)
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(backup_data)
                
            progress.setValue(100)
            
            QMessageBox.information(
                self,
                "Backup Complete",
                f"Backup created successfully:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )
        finally:
            progress.close()
            
    def _initialize_export_system(self):
        """Initialize the export and reporting system."""
        logger.info("Initializing export system")
        
        # Import necessary modules
        from ..analytics.export_reporting_system import WSJExportReportingSystem
        from ..analytics.health_insights_engine import HealthInsightsEngine
        from ..ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite
        from ..ui.charts.wsj_style_manager import WSJStyleManager

        # Create WSJ style manager
        wsj_style_manager = WSJStyleManager()
        
        # Create visualization suite
        viz_suite = WSJHealthVisualizationSuite(
            data_manager=self.config_tab,  # Assuming config_tab has data access methods
            style_manager=wsj_style_manager
        )
        
        # Create insights engine
        insights_engine = HealthInsightsEngine(db_manager)
        
        # Create export system
        self.export_system = WSJExportReportingSystem(
            data_manager=self.config_tab,
            viz_suite=viz_suite,
            insights_engine=insights_engine,
            style_manager=wsj_style_manager
        )
        
        logger.info("Export system initialized successfully")
        
    def _get_available_metrics(self, data: pd.DataFrame) -> List[str]:
        """Extract available metrics from the loaded data."""
        metrics = []
        
        if 'type' in data.columns:
            # Map Apple Health types to readable names
            metric_mapping = {
                'HKQuantityTypeIdentifierStepCount': 'step_count',
                'HKQuantityTypeIdentifierSleepAnalysis': 'sleep_analysis',
                'HKQuantityTypeIdentifierRestingHeartRate': 'resting_heart_rate',
                'HKQuantityTypeIdentifierActiveEnergyBurned': 'active_energy',
                'HKQuantityTypeIdentifierBodyMass': 'body_mass',
                'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'heart_rate_variability',
                'HKQuantityTypeIdentifierWalkingHeartRateAverage': 'walking_heart_rate',
                'HKQuantityTypeIdentifierVO2Max': 'vo2_max',
                'HKQuantityTypeIdentifierBodyFatPercentage': 'body_fat_percentage',
                'HKQuantityTypeIdentifierLeanBodyMass': 'lean_body_mass'
            }
            
            # Get unique types from data
            unique_types = data['type'].unique()
            
            for health_type in unique_types:
                if health_type in metric_mapping:
                    metrics.append(metric_mapping[health_type])
                    
        return metrics
    
    def _perform_database_health_check(self):
        """Perform comprehensive database health check during initialization.
        
        This method validates database connectivity, table integrity, and basic
        functionality as part of the G084 infrastructure improvements.
        
        Logs health check results and provides early warning of data access issues
        that could prevent dashboard tabs from displaying data properly.
        """
        logger.info("Performing database health check (G084 infrastructure validation)")
        
        try:
            from ..data_access import DataAccess
            data_access = DataAccess()
            
            # Perform health check
            health_status = data_access.health_check()
            
            # Log results
            if health_status['database_connected']:
                logger.info("✓ Database connection successful")
            else:
                logger.error("✗ Database connection failed")
            
            if health_status['tables_exist']:
                logger.info("✓ All required tables exist")
            else:
                logger.error("✗ Missing required tables")
            
            if health_status['basic_operations']:
                logger.info("✓ Basic database operations working")
            else:
                logger.error("✗ Basic database operations failed")
            
            # Log any errors found
            if health_status['errors']:
                logger.warning(f"Database health check found {len(health_status['errors'])} issues:")
                for error in health_status['errors']:
                    logger.warning(f"  - {error}")
            
            # Get database statistics
            try:
                stats = data_access.get_database_stats()
                if stats:
                    logger.info(f"Database statistics: {stats.get('health_records_count', 0):,} health records")
                    if stats.get('health_records_count', 0) > 0:
                        logger.info("✓ Health data is available for dashboard display")
                    else:
                        logger.info("ⓘ No health data found - dashboards will be empty until data is imported")
                else:
                    logger.warning("Could not retrieve database statistics")
            except Exception as stats_error:
                logger.warning(f"Error retrieving database statistics: {stats_error}")
            
            # Overall health assessment
            if (health_status['database_connected'] and 
                health_status['tables_exist'] and 
                health_status['basic_operations']):
                logger.info("✓ Database health check PASSED - Ready for data aggregation display")
            else:
                logger.error("✗ Database health check FAILED - Data display may not work properly")
                
        except Exception as e:
            logger.error(f"Database health check failed with exception: {e}", exc_info=True)