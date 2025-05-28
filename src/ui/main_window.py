"""Main window implementation with tab navigation for Apple Health Monitor Dashboard."""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QStatusBar, QMessageBox, QComboBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QKeyEvent

from utils.logging_config import get_logger
from .style_manager import StyleManager
from .settings_manager import SettingsManager
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
        
        # Initialize managers
        self.style_manager = StyleManager()
        self.settings_manager = SettingsManager()
        
        # Set up the window
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)  # Default size
        
        # Apply warm color theme
        self._apply_theme()
        
        # Create UI components
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Restore window state after UI is created
        self.settings_manager.restore_window_state(self)
        
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
        import_action.setToolTip("Import Apple Health data from a CSV file (Ctrl+O)")
        import_action.triggered.connect(self._on_import_csv)
        file_menu.addAction(import_action)
        
        # Save action
        save_action = QAction("&Save Configuration", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save current configuration settings")
        save_action.setToolTip("Save current filter and configuration settings (Ctrl+S)")
        save_action.triggered.connect(self._on_save_configuration)
        file_menu.addAction(save_action)
        
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
        self._create_help_tab()
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Set up keyboard navigation
        self._setup_keyboard_navigation()
    
    def _create_configuration_tab(self):
        """Create the configuration tab."""
        self.config_tab = ConfigurationTab()
        
        # Connect signals
        self.config_tab.data_loaded.connect(self._on_data_loaded)
        self.config_tab.filters_applied.connect(self._on_filters_applied)
        
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.setTabToolTip(0, "Import data and configure filters")
    
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
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "View your daily health metrics and trends")
    
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
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Analyze weekly health summaries and patterns")
    
    def _create_monthly_dashboard_tab(self):
        """Create the monthly dashboard tab with calendar heatmap."""
        try:
            from .monthly_dashboard_widget import MonthlyDashboardWidget
            
            # Create the monthly dashboard widget
            self.monthly_dashboard = MonthlyDashboardWidget()
            
            # Connect signals if needed
            self.monthly_dashboard.month_changed.connect(self._on_month_changed)
            self.monthly_dashboard.metric_changed.connect(self._on_metric_changed)
            
            self.tab_widget.addTab(self.monthly_dashboard, "Monthly")
            self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Review monthly health trends and calendar heatmap")
            
        except ImportError as e:
            # Fallback to placeholder if import fails
            logger.warning(f"Could not import MonthlyDashboardWidget: {e}")
            self._create_monthly_dashboard_placeholder()
            
    def _create_monthly_dashboard_placeholder(self):
        """Create a placeholder monthly dashboard tab."""
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
        self.tab_widget.setTabToolTip(self.tab_widget.count() - 1, "Add personal notes and health observations")
    
    def _create_help_tab(self):
        """Create the help tab with keyboard shortcuts reference."""
        help_widget = QWidget()
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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
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
                ("Ctrl+O", "Import CSV file"),
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
        section = QFrame()
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
        row = QWidget()
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
        section = QFrame()
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
        """Handle tab change event."""
        tab_name = self.tab_widget.tabText(index)
        logger.debug(f"Switched to tab: {tab_name}")
        self.status_bar.showMessage(f"Viewing {tab_name}")
        
        # Save the current tab index immediately
        self.settings_manager.set_setting("MainWindow/lastActiveTab", index)
    
    def _on_import_csv(self):
        """Handle CSV import action."""
        logger.info("Import CSV action triggered")
        # Switch to configuration tab and trigger import
        self.tab_widget.setCurrentIndex(0)  # Configuration tab is index 0
        if hasattr(self.config_tab, '_on_browse_clicked'):
            self.config_tab._on_browse_clicked()
    
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
        <tr><td><b>Ctrl+O</b></td><td>Import CSV file</td></tr>
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
        
    def _on_month_changed(self, year: int, month: int):
        """Handle month change signal from monthly dashboard."""
        logger.info(f"Month changed to: {year}-{month:02d}")
        self.status_bar.showMessage(f"Viewing {year}-{month:02d}")
        
    def _on_metric_changed(self, metric: str):
        """Handle metric change signal from monthly dashboard."""
        logger.info(f"Metric changed to: {metric}")
        self.status_bar.showMessage(f"Displaying {metric} data")
    
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
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closing, saving state")
        
        # Save window state before closing
        self.settings_manager.save_window_state(self)
        
        # Accept the close event
        event.accept()