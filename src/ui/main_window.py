"""Main window implementation with tab navigation for Apple Health Monitor Dashboard."""

from typing import List
from datetime import date
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QStatusBar, QMessageBox, QComboBox, QScrollArea, QFrame,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QKeyEvent

import pandas as pd

from ..utils.logging_config import get_logger
from .style_manager import StyleManager
from .settings_manager import SettingsManager
from .configuration_tab import ConfigurationTab
from .trophy_case_widget import TrophyCaseWidget
from .view_transitions import ViewTransitionManager, ViewType
from ..analytics.personal_records_tracker import PersonalRecordsTracker
# from ..analytics.background_trend_processor import BackgroundTrendProcessor
from ..database import db_manager
from ..config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
)

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tab-based navigation.
    
    This is the primary window of the Apple Health Monitor Dashboard application.
    It provides a tab-based interface for different views and functionalities:
    
    - Configuration: Data import and filtering settings
    - Daily Dashboard: Daily health metrics visualization
    - Weekly Dashboard: Weekly aggregated health data
    - Monthly Dashboard: Monthly health trends and patterns
    - Comparative Analytics: Cross-metric analysis and comparisons
    - Trophy Case: Personal records and achievements
    - Journal: Daily, weekly, and monthly reflection entries
    - Help: Application documentation and shortcuts
    
    The window supports keyboard navigation, view transitions, theming,
    and persistent window state management.
    
    Attributes:
        style_manager (StyleManager): Manages application styling and themes.
        settings_manager (SettingsManager): Handles window state persistence.
        transition_manager (ViewTransitionManager): Manages smooth view transitions.
        personal_records_tracker (PersonalRecordsTracker): Tracks health achievements.
        tab_widget (QTabWidget): The main tab container widget.
        config_tab (ConfigurationTab): The configuration tab instance.
    """
    
    def __init__(self):
        """Initialize the main window.
        
        Sets up the window structure, applies theming, creates all tabs,
        configures keyboard navigation, and restores the previous window state.
        The initialization follows this sequence:
        1. Initialize managers (style, settings, transitions, records)
        2. Set window properties (title, size, minimum dimensions)
        3. Apply warm color theme
        4. Create UI components (menu bar, tabs, status bar)
        5. Restore previous window state
        """
        super().__init__()
        logger.info("Initializing main window with tab navigation")
        
        # Initialize managers
        self.style_manager = StyleManager()
        self.settings_manager = SettingsManager()
        
        # Initialize transition manager (check accessibility settings)
        accessibility_mode = self.settings_manager.get_setting("accessibility/disable_animations", False)
        self.transition_manager = ViewTransitionManager(accessibility_mode=accessibility_mode)
        
        # Initialize personal records tracker
        self.personal_records_tracker = PersonalRecordsTracker(db_manager)
        
        # Initialize background trend processor
        self.background_trend_processor = None
        try:
            from ..analytics.background_trend_processor import BackgroundTrendProcessor
            self.background_trend_processor = BackgroundTrendProcessor(db_manager)
            logger.info("Background trend processor initialized")
        except ImportError as e:
            logger.warning(f"Could not initialize background trend processor: {e}")
        
        # Set up the window
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        # Set default size appropriate for 1920x1080 at 150% scale
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # Apply warm color theme
        self._apply_theme()
        
        # Create UI components
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Restore window state after UI is created
        self.settings_manager.restore_window_state(self)
        
        # Set up status update timer
        self.status_update_timer = QTimer(self)
        self.status_update_timer.timeout.connect(self._update_trend_status)
        self.status_update_timer.start(2000)  # Update every 2 seconds
        
        logger.info("Main window initialization complete")
    
    def _apply_theme(self):
        """Apply the warm color theme to the window.
        
        Sets up the application's visual styling with a warm, welcoming
        color palette. The theme includes:
        - Warm background colors (light beige/cream tones)
        - Earth tone text colors (brown)
        - Orange accent colors for highlights
        - Consistent styling across all UI elements
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
        """Create the application menu bar.
        
        Sets up the main menu structure with the following menus:
        - File: Import, Save, Exit
        - View: Refresh and view options
        - Help: Keyboard shortcuts, About
        
        All menu items include keyboard shortcuts, tooltips, and status tips
        for better accessibility and user experience.
        """
        logger.debug("Creating menu bar")
        
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(self.style_manager.get_menu_bar_style())
        
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
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh current view")
        refresh_action.setToolTip("Refresh the current dashboard view (F5)")
        refresh_action.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_action)
        
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
        """Create the central widget with tab navigation.
        
        Sets up the main tab widget containing all application views.
        Establishes tab-to-view mappings for transition management,
        connects signal handlers for tab changes and transitions,
        and configures keyboard navigation for the tab system.
        """
        logger.debug("Creating central widget with tabs")
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet(self.style_manager.get_tab_widget_style())
        self.setCentralWidget(self.tab_widget)
        
        # Create tabs
        self._create_configuration_tab()
        self._create_daily_dashboard_tab()
        self._create_weekly_dashboard_tab()
        self._create_monthly_dashboard_tab()
        self._create_comparative_analytics_tab()
        self._create_health_insights_tab()
        self._create_trophy_case_tab()
        self._create_journal_tab()
        self._create_help_tab()
        
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
    
    def _create_configuration_tab(self):
        """Create the configuration tab.
        
        Initializes the configuration tab which handles data import,
        filtering options, and data source management. Connects the
        tab's signals to main window handlers for data loading and
        filter changes.
        """
        # Use standard ConfigurationTab for now
        # The modern version is incomplete and doesn't have summary cards implemented
        ConfigTab = ConfigurationTab
        logger.info("Using standard ConfigurationTab")
        
        # Create configuration tab with scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.config_tab = ConfigTab()
        scroll_area.setWidget(self.config_tab)
        
        # Connect signals
        self.config_tab.data_loaded.connect(self._on_data_loaded)
        self.config_tab.filters_applied.connect(self._on_filters_applied)
        
        self.tab_widget.addTab(scroll_area, "Configuration")
        self.tab_widget.setTabToolTip(0, "Import data and configure filters")
    
    def _create_daily_dashboard_tab(self):
        """Create the daily dashboard tab."""
        try:
            from .daily_dashboard_widget import DailyDashboardWidget
            
            # Create the daily dashboard widget
            self.daily_dashboard = DailyDashboardWidget()
            
            # Connect signals
            if hasattr(self.daily_dashboard, 'metric_selected'):
                self.daily_dashboard.metric_selected.connect(self._handle_metric_selection)
            if hasattr(self.daily_dashboard, 'date_changed'):
                self.daily_dashboard.date_changed.connect(self._handle_date_change)
            if hasattr(self.daily_dashboard, 'refresh_requested'):
                self.daily_dashboard.refresh_requested.connect(self._refresh_daily_data)
            
            self.tab_widget.addTab(self.daily_dashboard, "Daily")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View your daily health metrics and trends")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import DailyDashboardWidget: {e}")
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
        
        self.tab_widget.addTab(daily_widget, "Daily")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View your daily health metrics and trends")
    
    def _create_weekly_dashboard_tab(self):
        """Create the weekly dashboard tab."""
        try:
            # Use standard version for now (modern version has display issues)
            from .weekly_dashboard_widget import WeeklyDashboardWidget
            self.weekly_dashboard = WeeklyDashboardWidget()
            logger.info("Using standard WeeklyDashboardWidget")
            
            # Connect signals
            self.weekly_dashboard.week_changed.connect(self._on_week_changed)
            self.weekly_dashboard.metric_selected.connect(self._on_metric_selected)
            
            self.tab_widget.addTab(self.weekly_dashboard, "Weekly")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Analyze weekly health summaries and patterns")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import WeeklyDashboardWidget: {e}")
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
        
        self.tab_widget.addTab(weekly_widget, "Weekly")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Analyze weekly health summaries and patterns")
    
    def _create_monthly_dashboard_tab(self):
        """Create the monthly dashboard tab with calendar heatmap."""
        try:
            # Try the modern version first
            try:
                from .monthly_dashboard_widget import MonthlyDashboardWidget
                # Create the monthly dashboard widget
                self.monthly_dashboard = MonthlyDashboardWidget()
                logger.info("Using MonthlyDashboardWidget")
            except ImportError:
                # If modern version not available, create placeholder
                logger.warning("MonthlyDashboardWidget not available, using placeholder")
                self._create_monthly_dashboard_placeholder()
                return
            
            # Connect signals if needed
            self.monthly_dashboard.month_changed.connect(self._on_month_changed)
            self.monthly_dashboard.metric_changed.connect(self._on_metric_changed)
            
            self.tab_widget.addTab(self.monthly_dashboard, "Monthly")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Review monthly health trends and calendar heatmap")
            
        except Exception as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not create MonthlyDashboardWidget: {e}")
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
        
        self.tab_widget.addTab(monthly_widget, "Monthly")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Review monthly health trends and progress")
    
    def _create_comparative_analytics_tab(self):
        """Create the comparative analytics tab."""
        try:
            # Try to import the comparative analytics widget
            from .comparative_visualization import ComparativeAnalyticsWidget
            from ..analytics.comparative_analytics import ComparativeAnalyticsEngine
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
        """Create the health insights tab."""
        try:
            from .health_insights_widget import HealthInsightsWidget
            from ..analytics.health_insights_engine import EnhancedHealthInsightsEngine
            from ..analytics.evidence_database import EvidenceDatabase
            from .charts.wsj_style_manager import WSJStyleManager
            
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
            self.health_insights_widget.refresh_requested.connect(self._refresh_health_insights)
            self.health_insights_widget.insight_selected.connect(self._on_insight_selected)
            
            self.tab_widget.addTab(self.health_insights_widget, "💡 Insights")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View personalized health insights and recommendations")
            
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
        
        self.tab_widget.addTab(insights_widget, "💡 Insights")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View personalized health insights and recommendations")
    
    def _create_trophy_case_tab(self):
        """Create the trophy case tab."""
        self.trophy_case_widget = TrophyCaseWidget(self.personal_records_tracker)
        
        # Connect signals (if needed)
        # self.trophy_case_widget.record_selected.connect(self._on_record_selected)
        # self.trophy_case_widget.share_requested.connect(self._on_share_requested)
        
        self.tab_widget.addTab(self.trophy_case_widget, "🏆 Records")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View personal records, achievements, and streaks")
    
    def _create_journal_tab(self):
        """Create the journal tab placeholder."""
        journal_widget = QWidget(self)
        layout = QVBoxLayout(journal_widget)
        
        # Placeholder content
        label = QLabel("Health Journal")
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
        
        placeholder = QLabel("Add notes and observations here")
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
        
        self.tab_widget.addTab(journal_widget, "Journal")
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Add personal notes and health observations")
    
    def _create_help_tab(self):
        """Create the help tab with keyboard shortcuts reference."""
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
                ("Ctrl+1 to Ctrl+5", "Switch to specific tab (1=Config, 2=Daily, 3=Weekly, 4=Monthly, 5=Journal)"),
                ("Alt+C/D/W/M/J", "Quick tab switching (Config/Daily/Weekly/Monthly/Journal)"),
                ("Ctrl+PageUp/PageDown", "Navigate to previous/next tab")
            ]
        )
        content_layout.addWidget(nav_section)
        
        # File operations section
        file_section = self._create_help_section(
            "File Operations",
            [
                ("Ctrl+O", "Import data file (CSV or XML)"),
                ("Ctrl+S", "Save configuration"),
                ("Ctrl+Q", "Exit application"),
                ("F5", "Refresh current view")
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
        """Set up keyboard navigation and shortcuts."""
        logger.debug("Setting up keyboard navigation")
        
        # Add tab switching shortcuts (now 6 tabs including Help)
        for i in range(min(6, self.tab_widget.count())):
            action = QAction(self)
            action.setShortcut(f"Ctrl+{i+1}")
            # Use default parameter to capture the value properly
            action.triggered.connect(lambda checked=False, index=i: self.tab_widget.setCurrentIndex(index))
            self.addAction(action)
        
        # Add Alt+Tab navigation shortcuts
        # Alt+C for Configuration, Alt+D for Daily, etc., Alt+H for Help
        shortcuts = ['Alt+C', 'Alt+D', 'Alt+W', 'Alt+M', 'Alt+J', 'Alt+H']
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
    
    def _create_status_bar(self):
        """Create the application status bar."""
        logger.debug("Creating status bar")
        
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(self.style_manager.get_status_bar_style())
        self.status_bar.showMessage("Ready")
        self.status_bar.setToolTip("Shows the current application status")
    
    def _on_tab_changed(self, index):
        """Handle tab change event with smooth transitions."""
        tab_name = self.tab_widget.tabText(index)
        logger.debug(f"Tab change requested: {tab_name}")
        
        # Get view types for transition
        from_view = self.tab_to_view_map.get(self.previous_tab_index, ViewType.CONFIG)
        to_view = self.tab_to_view_map.get(index, ViewType.CONFIG)
        
        # Get widgets for transition
        from_widget = self.tab_widget.widget(self.previous_tab_index)
        to_widget = self.tab_widget.widget(index)
        
        # Only perform transition for dashboard tabs (Daily, Weekly, Monthly)
        dashboard_tabs = [1, 2, 3]  # Daily, Weekly, Monthly indices
        should_animate = (self.previous_tab_index in dashboard_tabs and 
                         index in dashboard_tabs and
                         from_widget is not None and 
                         to_widget is not None)
        
        # Disable animations for Daily tab temporarily to fix refresh issue
        if index == 1:  # Daily tab index
            should_animate = False
        
        if should_animate:
            # Perform animated transition
            self.transition_manager.transition_to(
                from_widget, to_widget, from_view, to_view
            )
        else:
            # Immediate transition for non-dashboard tabs
            self._complete_tab_change(index, tab_name)
        
        # Update previous tab index
        self.previous_tab_index = index
    
    def _complete_tab_change(self, index: int, tab_name: str):
        """Complete tab change without animation."""
        logger.debug(f"Switched to tab: {tab_name}")
        self._update_trend_status()
        
        # Save the current tab index immediately
        self.settings_manager.set_setting("MainWindow/lastActiveTab", index)
        
        # Force the widget to become visible and process pending events
        widget = self.tab_widget.widget(index)
        if widget:
            widget.show()
            widget.raise_()
            QApplication.processEvents()
        
        # Refresh data for dashboard tabs when switching without animation
        if index == 0:  # Config tab
            # Refresh config tab display if data is loaded
            if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'refresh_display'):
                self.config_tab.refresh_display()
        elif index == 1:  # Daily tab
            # Add a small delay to ensure tab is fully visible
            QTimer.singleShot(50, self._refresh_daily_data)
        elif index == 2:  # Weekly tab
            self._refresh_weekly_data()
        elif index == 3:  # Monthly tab
            self._refresh_monthly_data()
        elif index == 4:  # Compare tab
            self._refresh_comparative_data()
    
    def _on_transition_started(self, from_view: ViewType, to_view: ViewType):
        """Handle transition start."""
        logger.debug(f"Transition started: {from_view.value} → {to_view.value}")
        self._update_trend_status()
    
    def _on_transition_completed(self, target_view: ViewType):
        """Handle transition completion."""
        logger.debug(f"Transition completed: {target_view.value}")
        
        # Update status bar
        current_index = self.tab_widget.currentIndex()
        tab_name = self.tab_widget.tabText(current_index)
        self._complete_tab_change(current_index, tab_name)
        
        # Refresh data for dashboard tabs when transitioning to them
        if current_index == 0:  # Config tab index
            # Refresh config tab display if data is loaded
            if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'refresh_display'):
                self.config_tab.refresh_display()
        elif current_index == 1:  # Daily tab index
            self._refresh_daily_data()
        elif current_index == 2:  # Weekly tab index
            self._refresh_weekly_data()
        elif current_index == 3:  # Monthly tab index
            self._refresh_monthly_data()
        elif current_index == 4:  # Compare tab index
            self._refresh_comparative_data()
    
    def _on_transition_interrupted(self):
        """Handle transition interruption."""
        logger.debug("Transition was interrupted")
        self.status_bar.showMessage("Transition interrupted")
    
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
    
    def _on_refresh(self):
        """Handle refresh action."""
        logger.info("Refresh action triggered")
        current_tab = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.status_bar.showMessage(f"Refreshing {current_tab}...")
        # Placeholder for refresh functionality
    
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
        <tr><td><b>F5</b></td><td>Refresh current view</td></tr>
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
            "</ul>"
            "<p><b>Are you sure you want to continue?</b></p>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import os
                import shutil
                from ..config import DATA_DIR
                # Create progress dialog
                progress = QMessageBox(self)
                progress.setWindowTitle("Erasing Data")
                progress.setText("Erasing all data...")
                progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
                progress.show()
                QApplication.processEvents()
                
                # 1. Close database connections
                if hasattr(db_manager, 'close'):
                    db_manager.close()
                    logger.info("Closed database connections")
                
                # 2. Delete database file
                db_path = os.path.join(DATA_DIR, "health_data.db")
                if os.path.exists(db_path):
                    os.remove(db_path)
                    logger.info(f"Deleted database file: {db_path}")
                
                # 3. Delete analytics cache database
                analytics_cache_db = os.path.join(DATA_DIR, "analytics_cache.db")
                if os.path.exists(analytics_cache_db):
                    os.remove(analytics_cache_db)
                    logger.info(f"Deleted analytics cache database: {analytics_cache_db}")
                
                # Also check in current directory
                if os.path.exists("analytics_cache.db"):
                    os.remove("analytics_cache.db")
                    logger.info("Deleted analytics cache database from current directory")
                
                # 4. Delete cache directory
                cache_dir = os.path.join(DATA_DIR, "cache")
                if os.path.exists(cache_dir):
                    shutil.rmtree(cache_dir)
                    logger.info(f"Deleted cache directory: {cache_dir}")
                    
                # Also check for cache in current directory
                if os.path.exists("cache"):
                    shutil.rmtree("cache")
                    logger.info("Deleted cache directory from current directory")
                
                # 5. Clear filter configurations from database
                if hasattr(self.config_tab, 'filter_config_manager'):
                    # This will recreate the database but with empty tables
                    self.config_tab.filter_config_manager.clear_all_presets()
                    logger.info("Cleared filter configurations")
                
                # 6. Reset UI
                if hasattr(self.config_tab, 'data'):
                    self.config_tab.data = None
                    self.config_tab.filtered_data = None
                    
                # Update UI to reflect empty state
                if hasattr(self.config_tab, 'refresh_display'):
                    self.config_tab.refresh_display()
                    
                # Disable other tabs since no data is loaded
                for i in range(1, self.tab_widget.count()):
                    self.tab_widget.setTabEnabled(i, False)
                
                # Switch to configuration tab
                self.tab_widget.setCurrentIndex(0)
                
                progress.close()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Data Erased",
                    "All data has been successfully erased.\n\n"
                    "You can now import new health data."
                )
                
                # Update status bar
                self.status_bar.showMessage("All data erased successfully")
                logger.info("All data erased successfully")
                
            except Exception as e:
                logger.error(f"Failed to erase data: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to erase all data:\n\n{str(e)}"
                )
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
        """Handle data loaded signal from configuration tab."""
        logger.info(f"Data loaded: {len(data) if data is not None else 0} records")
        self.status_bar.showMessage(f"Loaded {len(data):,} health records")
        
        # Refresh all dashboard tabs when data is loaded
        current_tab = self.tab_widget.currentIndex()
        
        # Refresh the current tab first
        if current_tab == 1:
            self._refresh_daily_data()
        elif current_tab == 2:
            self._refresh_weekly_data()
        elif current_tab == 3:
            self._refresh_monthly_data()
            
        # Enable other tabs when data is loaded
        if data is not None and not data.empty:
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
            
            # Always refresh weekly data to ensure it's ready
            self._refresh_weekly_data()
            
            # Update comparative analytics engine with new calculators
            self._refresh_comparative_data()
    
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
                    # Create daily calculator with the data
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    import time
                    # Get local timezone
                    local_tz = time.tzname[0]
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    
                    # Set the calculator in the daily dashboard
                    self.daily_dashboard.set_daily_calculator(daily_calculator)
                    
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
            self._refresh_health_insights()
    
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
                    # Create daily calculator first
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
                    import time
                    # Get local timezone
                    local_tz = time.tzname[0]
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    
                    # Create weekly calculator with the daily calculator
                    weekly_calculator = WeeklyMetricsCalculator(daily_calculator)
                    
                    # Set the calculator in the weekly dashboard
                    if hasattr(self.weekly_dashboard, 'set_weekly_calculator'):
                        self.weekly_dashboard.set_weekly_calculator(weekly_calculator)
                    
                    logger.info(f"Set weekly calculator with {len(data)} records")
                else:
                    logger.warning("No data available to refresh weekly dashboard")
    
    def _refresh_monthly_data(self):
        """Refresh data in the monthly dashboard."""
        logger.debug("Refreshing monthly dashboard data")
        if hasattr(self, 'monthly_dashboard'):
            # Get current data from configuration tab
            data = None
            if hasattr(self, 'config_tab'):
                if hasattr(self.config_tab, 'get_filtered_data'):
                    data = self.config_tab.get_filtered_data()
                elif hasattr(self.config_tab, 'filtered_data'):
                    data = self.config_tab.filtered_data
                    
                if data is not None and not data.empty:
                    # Create daily calculator first
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
                    import time
                    # Get local timezone
                    local_tz = time.tzname[0]
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    
                    # Create monthly calculator with the daily calculator
                    monthly_calculator = MonthlyMetricsCalculator(daily_calculator)
                    
                    # Set the calculator in the monthly dashboard
                    if hasattr(self.monthly_dashboard, 'set_data_source'):
                        self.monthly_dashboard.set_data_source(monthly_calculator)
                    
                    logger.info(f"Set monthly calculator with {len(data)} records")
                else:
                    logger.warning("No data available to refresh monthly dashboard")
    
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
                    # Create calculators
                    from ..analytics.daily_metrics_calculator import DailyMetricsCalculator
                    from ..analytics.weekly_metrics_calculator import WeeklyMetricsCalculator
                    from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
                    import time
                    # Get local timezone
                    local_tz = time.tzname[0]
                    
                    daily_calculator = DailyMetricsCalculator(data, timezone=local_tz)
                    weekly_calculator = WeeklyMetricsCalculator(daily_calculator)
                    monthly_calculator = MonthlyMetricsCalculator(data)
                    
                    # Update comparative engine
                    self.comparative_engine.daily_calculator = daily_calculator
                    self.comparative_engine.weekly_calculator = weekly_calculator
                    self.comparative_engine.monthly_calculator = monthly_calculator
                    
                    # Re-set the engine in the widget to trigger updates
                    self.comparative_widget.set_comparative_engine(self.comparative_engine)
                    
                    logger.info("Updated comparative analytics with new data")
                else:
                    logger.info("No data available yet - comparative analytics will update when data is loaded")
    
    def _on_filters_applied(self, filters):
        """Handle filters applied signal from configuration tab."""
        logger.info(f"Filters applied: {filters}")
        self.status_bar.showMessage("Filters applied successfully")
        
        # TODO: Pass filtered data to other tabs
        # This will be implemented when other tabs are created
        
    def _on_month_changed(self, year: int, month: int):
        """Handle month change signal from monthly dashboard."""
        logger.info(f"Month changed to: {year}-{month:02d}")
        self.status_bar.showMessage(f"Viewing {year}-{month:02d}")
        
    def _on_metric_changed(self, metric: str):
        """Handle metric change signal from monthly dashboard."""
        logger.info(f"Metric changed to: {metric}")
        self.status_bar.showMessage(f"Displaying {metric} data")
    
    def _on_week_changed(self, start_date: date, end_date: date):
        """Handle week change signal from weekly dashboard."""
        logger.info(f"Week changed to: {start_date} - {end_date}")
        self.status_bar.showMessage(f"Viewing week of {start_date.strftime('%B %d')}")
    
    def _on_metric_selected(self, metric: str):
        """Handle metric selection signal from weekly dashboard."""
        logger.info(f"Weekly metric selected: {metric}")
        self.status_bar.showMessage(f"Weekly view: {metric}")
    
    def _refresh_health_insights(self):
        """Refresh health insights based on current data."""
        logger.info("Refreshing health insights")
        
        # Get current data from configuration tab
        if hasattr(self, 'config_tab') and hasattr(self.config_tab, 'get_filtered_data'):
            data = self.config_tab.get_filtered_data()
            
            if data is not None and not data.empty:
                # Convert data to format expected by insights engine
                user_data = self._prepare_data_for_insights(data)
                
                # Load insights
                if hasattr(self, 'health_insights_widget'):
                    self.health_insights_widget.load_insights(user_data)
                    self.status_bar.showMessage("Generating health insights...")
            else:
                self.status_bar.showMessage("No data available for insights")
        else:
            self.status_bar.showMessage("Load data first to generate insights")
    
    def _on_insight_selected(self, insight):
        """Handle insight selection."""
        logger.info(f"Insight selected: {insight.title}")
        # Could navigate to relevant data view or show detailed dialog
        self.status_bar.showMessage(f"Selected: {insight.title}")
    
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
                    if 'creationDate' in metric_data.columns:
                        metric_data['date'] = pd.to_datetime(metric_data['creationDate'])
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
                
                self.status_bar.showMessage(msg)
            else:
                # No background processor available
                self.status_bar.showMessage("Ready")
        except Exception as e:
            logger.error(f"Error updating trend status: {e}")
            self.status_bar.showMessage("Ready")
    
    def _format_metric_name(self, metric: str) -> str:
        """Format metric identifier to readable name."""
        # Simple formatting - remove prefix and make readable
        name = metric.replace('HKQuantityTypeIdentifier', '')
        name = name.replace('HKCategoryTypeIdentifier', '')
        # Convert camelCase to spaced words
        import re
        name = re.sub(r'([A-Z])', r' \1', name).strip()
        return name
    
    def closeEvent(self, event):
        """Handle window close event."""
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
            self.status_bar.showMessage("Export completed successfully")
            
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
        from ..analytics.export_reporting_system import ExportConfiguration, ExportFormat, ReportTemplate
        from datetime import datetime, timedelta
        from PyQt6.QtWidgets import QFileDialog, QProgressDialog
        from pathlib import Path
        
        # Create configuration for quick export
        format_map = {
            'pdf': ExportFormat.PDF,
            'excel': ExportFormat.EXCEL,
            'csv': ExportFormat.CSV
        }
        
        export_format = format_map.get(export_type, ExportFormat.PDF)
        
        # Get date range from data
        if 'creationDate' in data.columns:
            dates = pd.to_datetime(data['creationDate'])
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
            
        from PyQt6.QtWidgets import QFileDialog, QProgressDialog
        from datetime import datetime
        
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
        from ..ui.charts.wsj_style_manager import WSJStyleManager
        from ..analytics.health_insights_engine import HealthInsightsEngine
        from ..ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite
        
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