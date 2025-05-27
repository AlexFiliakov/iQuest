"""Main window implementation with tab navigation for Apple Health Monitor Dashboard."""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QMenuBar, QMenu, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor

from utils.logging_config import get_logger
from .style_manager import StyleManager
from .configuration_tab import ConfigurationTab
from config import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
)

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tab-based navigation."""
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing main window with tab navigation")
        
        # Initialize style manager
        self.style_manager = StyleManager()
        
        # Set up the window
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)  # Optimal size
        
        # Apply warm color theme
        self._apply_theme()
        
        # Create UI components
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        logger.info("Main window initialization complete")
    
    def _apply_theme(self):
        """Apply the warm color theme to the window."""
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
        """Create the application menu bar."""
        logger.debug("Creating menu bar")
        
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(self.style_manager.get_menu_bar_style())
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Import action
        import_action = QAction("&Import CSV...", self)
        import_action.setShortcut("Ctrl+O")
        import_action.setStatusTip("Import Apple Health CSV data")
        import_action.triggered.connect(self._on_import_csv)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh current view")
        refresh_action.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Apple Health Monitor")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_central_widget(self):
        """Create the central widget with tab navigation."""
        logger.debug("Creating central widget with tabs")
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self.style_manager.get_tab_widget_style())
        self.setCentralWidget(self.tab_widget)
        
        # Create tabs
        self._create_configuration_tab()
        self._create_daily_dashboard_tab()
        self._create_weekly_dashboard_tab()
        self._create_monthly_dashboard_tab()
        self._create_journal_tab()
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _create_configuration_tab(self):
        """Create the configuration tab."""
        self.config_tab = ConfigurationTab()
        
        # Connect signals
        self.config_tab.data_loaded.connect(self._on_data_loaded)
        self.config_tab.filters_applied.connect(self._on_filters_applied)
        
        self.tab_widget.addTab(self.config_tab, "Configuration")
    
    def _create_daily_dashboard_tab(self):
        """Create the daily dashboard tab placeholder."""
        daily_widget = QWidget()
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
    
    def _create_weekly_dashboard_tab(self):
        """Create the weekly dashboard tab placeholder."""
        weekly_widget = QWidget()
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
    
    def _create_monthly_dashboard_tab(self):
        """Create the monthly dashboard tab placeholder."""
        monthly_widget = QWidget()
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
        
        placeholder = QLabel("Monthly health trends will appear here")
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
    
    def _create_journal_tab(self):
        """Create the journal tab placeholder."""
        journal_widget = QWidget()
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
    
    def _create_status_bar(self):
        """Create the application status bar."""
        logger.debug("Creating status bar")
        
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet(self.style_manager.get_status_bar_style())
        self.status_bar.showMessage("Ready")
    
    def _on_tab_changed(self, index):
        """Handle tab change event."""
        tab_name = self.tab_widget.tabText(index)
        logger.debug(f"Switched to tab: {tab_name}")
        self.status_bar.showMessage(f"Viewing {tab_name}")
    
    def _on_import_csv(self):
        """Handle CSV import action."""
        logger.info("Import CSV action triggered")
        # Placeholder for import functionality
        QMessageBox.information(
            self,
            "Import CSV",
            "CSV import functionality will be implemented in the Configuration tab."
        )
    
    def _on_refresh(self):
        """Handle refresh action."""
        logger.info("Refresh action triggered")
        current_tab = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.status_bar.showMessage(f"Refreshing {current_tab}...")
        # Placeholder for refresh functionality
    
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
        
        # Enable other tabs when data is loaded
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)
    
    def _on_filters_applied(self, filters):
        """Handle filters applied signal from configuration tab."""
        logger.info(f"Filters applied: {filters}")
        self.status_bar.showMessage("Filters applied successfully")
        
        # TODO: Pass filtered data to other tabs
        # This will be implemented when other tabs are created