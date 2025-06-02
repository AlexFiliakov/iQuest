"""Improved configuration tab with better layout and visual hierarchy.

This module provides an enhanced version of the configuration tab with:
- Consistent 8px grid spacing system
- Better form alignment using grid layouts
- Improved visual hierarchy with proper typography
- Enhanced color contrast for better readability
- Professional card-based sections with subtle shadows
"""

import json
import os
import time

import pandas as pd
from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config import DATA_DIR
from ..data_filter_engine import DataFilterEngine, FilterCriteria
from ..data_loader import DataLoader, convert_xml_to_sqlite
from ..database import db_manager
from ..filter_config_manager import FilterConfig, FilterConfigManager
from ..statistics_calculator import StatisticsCalculator
from ..utils.logging_config import get_logger
from ..analytics.cache_manager import get_cache_manager
from .component_factory import ComponentFactory
from .enhanced_date_edit import EnhancedDateEdit
from .import_progress_dialog import ImportProgressDialog
from .multi_select_combo import CheckableComboBox
from .settings_manager import SettingsManager
from .statistics_widget import StatisticsWidget
from .style_manager import StyleManager
from .summary_cards import SummaryCard
from .table_components import MetricTable, TableConfig

logger = get_logger(__name__)


class ConfigurationTabImproved(QWidget):
    """Improved configuration tab with better layout and visual design.
    
    Key improvements:
    - Consistent 8px grid spacing system throughout
    - Proper grid-based form layouts for perfect alignment
    - Enhanced visual hierarchy with better typography
    - Improved color contrast (WCAG AA compliant)
    - Professional card-based sections with depth
    - Clear primary vs secondary button styles
    - Better status message visibility
    """
    
    # Signals
    data_loaded = pyqtSignal(object)
    filters_applied = pyqtSignal(dict)
    data_cleared = pyqtSignal()
    
    def __init__(self):
        """Initialize the improved configuration tab."""
        super().__init__()
        logger.info("Initializing improved Configuration tab")
        
        # Initialize components
        self.style_manager = StyleManager()
        self.component_factory = ComponentFactory()
        self.data_loader = DataLoader()
        self.filter_config_manager = FilterConfigManager()
        self.statistics_calculator = StatisticsCalculator()
        self.cache_manager = get_cache_manager()
        
        # Initialize metric calculators as None
        self.daily_calculator = None
        self.weekly_calculator = None
        self.monthly_calculator = None
        
        self.data = None
        self.filtered_data = None
        self.statistics_widget = None
        self.data_available = False
        
        # UI elements references
        self.file_path_input = None
        self.progress_bar = None
        self.progress_label = None
        self.start_date_edit = None
        self.end_date_edit = None
        self.device_dropdown = None
        self.metric_dropdown = None
        self.apply_button = None
        self.reset_button = None
        self.status_label = None
        self.save_preset_button = None
        self.load_preset_button = None
        
        # Create the UI
        self._create_ui()
        
        # Set up keyboard navigation
        self._setup_keyboard_navigation()
        
        # Check database availability
        QTimer.singleShot(100, self._check_database_availability)
        
        logger.info("Improved configuration tab initialized")
    
    def _create_ui(self):
        """Create the improved UI with consistent grid spacing."""
        # Create main scroll area
        main_scroll = QScrollArea(self)
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: none;
            }}
            {self.style_manager.get_scrollbar_style()}
        """)
        
        # Main container with max width for readability
        main_widget = QWidget()
        main_widget.setObjectName("configurationContent")
        main_widget.setStyleSheet(f"""
            QWidget#configurationContent {{
                background-color: {self.style_manager.SECONDARY_BG};
            }}
        """)
        
        # Main layout with 8px grid spacing
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(
            self.style_manager.get_grid_spacing(5),  # 40px
            self.style_manager.get_grid_spacing(3),  # 24px
            self.style_manager.get_grid_spacing(5),  # 40px
            self.style_manager.get_grid_spacing(3)   # 24px
        )
        main_layout.setSpacing(self.style_manager.get_grid_spacing(4))  # 32px
        
        # Header section
        header_widget = self._create_header_section()
        main_layout.addWidget(header_widget)
        
        # Status section (initially hidden)
        self.status_section = self._create_status_section()
        self.status_section.setVisible(False)
        main_layout.addWidget(self.status_section)
        
        # Content container with max width
        content_widget = QWidget()
        content_widget.setMaximumWidth(1200)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(self.style_manager.get_grid_spacing(3))  # 24px
        
        # Add sections with consistent spacing
        content_layout.addWidget(self._create_import_section())
        content_layout.addWidget(self._create_filter_section())
        content_layout.addWidget(self._create_summary_cards_section())
        content_layout.addWidget(self._create_statistics_section())
        
        content_layout.addStretch()
        
        # Center content horizontally
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(content_widget)
        h_layout.addStretch()
        
        main_layout.addLayout(h_layout)
        
        # Set scroll area content
        main_scroll.setWidget(main_widget)
        
        # Tab layout
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(main_scroll)
    
    def _create_header_section(self):
        """Create header section with title and subtitle."""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(self.style_manager.get_grid_spacing(1))  # 8px
        
        # Title
        title = QLabel("Configuration")
        title.setStyleSheet(self.style_manager.get_heading_style(2))  # H2 = 28px
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Import and filter your Apple Health data")
        subtitle.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {self.style_manager.TEXT_SECONDARY};
                font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
            }}
        """)
        header_layout.addWidget(subtitle)
        
        return header
    
    def _create_status_section(self):
        """Create status message section."""
        status_frame = QFrame()
        status_frame.setObjectName("statusSection")
        status_frame.setStyleSheet(self.style_manager.get_info_message_style())
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(
            self.style_manager.get_grid_spacing(2),  # 16px
            self.style_manager.get_grid_spacing(1),  # 8px
            self.style_manager.get_grid_spacing(2),  # 16px
            self.style_manager.get_grid_spacing(1)   # 8px
        )
        
        self.status_label = QLabel("Loading database information...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        return status_frame
    
    def _create_import_section(self):
        """Create import section with grid-based layout."""
        section = self._create_section_card()
        layout = QVBoxLayout(section)
        layout.setSpacing(self.style_manager.get_grid_spacing(2))  # 16px
        
        # Section title and description
        title = QLabel("Import Data")
        title.setStyleSheet(self.style_manager.get_heading_style(4))  # H4 = 20px
        layout.addWidget(title)
        
        description = QLabel("Select your Apple Health export file (XML or CSV)")
        description.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {self.style_manager.TEXT_SECONDARY};
                margin-bottom: {self.style_manager.get_grid_spacing(1)}px;
            }}
        """)
        layout.addWidget(description)
        
        # Grid layout for form elements
        grid = QGridLayout()
        grid.setSpacing(self.style_manager.get_grid_spacing(1))  # 8px
        grid.setColumnStretch(1, 1)  # Make file input expand
        
        # Row 0: File selection
        file_label = QLabel("Data File:")
        file_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        file_label.setStyleSheet(self.style_manager.get_form_label_style())
        grid.addWidget(file_label, 0, 0)
        
        file_container = QHBoxLayout()
        file_container.setSpacing(self.style_manager.get_grid_spacing(1))
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("No file selected...")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet(self.style_manager.get_input_style())
        file_container.addWidget(self.file_path_input)
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        browse_button.clicked.connect(self._on_browse_clicked)
        browse_button.setToolTip("Browse for Apple Health export file (Alt+B)")
        file_container.addWidget(browse_button)
        
        grid.addLayout(file_container, 0, 1)
        
        # Row 1: Buttons
        button_container = QHBoxLayout()
        button_container.setSpacing(self.style_manager.get_grid_spacing(1))
        
        import_button = QPushButton("Import Data")
        import_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setToolTip("Import data from selected file (Alt+I)")
        button_container.addWidget(import_button)
        
        clear_button = QPushButton("Clear Data")
        clear_button.setStyleSheet(self.style_manager.get_button_style("danger"))
        clear_button.clicked.connect(self._on_clear_data_clicked)
        clear_button.setToolTip("Clear all imported health data")
        button_container.addWidget(clear_button)
        
        button_container.addStretch()
        grid.addLayout(button_container, 1, 1)
        
        layout.addLayout(grid)
        
        # Progress section
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(self.style_manager.get_grid_spacing(1))
        progress_layout.setContentsMargins(0, self.style_manager.get_grid_spacing(1), 0, 0)
        
        self.progress_label = QLabel("Ready to import data")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(self.style_manager.get_modern_progress_bar_style())
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_widget)
        
        return section
    
    def _create_filter_section(self):
        """Create filter section with proper grid alignment."""
        section = self._create_section_card()
        layout = QVBoxLayout(section)
        layout.setSpacing(self.style_manager.get_grid_spacing(2))  # 16px
        
        # Section title and description
        title = QLabel("Filter Data")
        title.setStyleSheet(self.style_manager.get_heading_style(4))  # H4 = 20px
        layout.addWidget(title)
        
        description = QLabel("Apply filters to focus on specific data")
        description.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {self.style_manager.TEXT_SECONDARY};
                margin-bottom: {self.style_manager.get_grid_spacing(1)}px;
            }}
        """)
        layout.addWidget(description)
        
        # Grid layout for filters
        grid = QGridLayout()
        grid.setSpacing(self.style_manager.get_grid_spacing(1))  # 8px
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        
        # Row 0: Date range
        date_label = QLabel("Date Range:")
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        date_label.setStyleSheet(self.style_manager.get_form_label_style())
        grid.addWidget(date_label, 0, 0)
        
        date_container = QHBoxLayout()
        date_container.setSpacing(self.style_manager.get_grid_spacing(1))
        
        self.start_date_edit = EnhancedDateEdit()
        self.start_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        date_container.addWidget(self.start_date_edit)
        
        to_label = QLabel("to")
        to_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        to_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {self.style_manager.TEXT_SECONDARY};
                padding: 0 {self.style_manager.get_grid_spacing(1)}px;
            }}
        """)
        date_container.addWidget(to_label)
        
        self.end_date_edit = EnhancedDateEdit()
        self.end_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_container.addWidget(self.end_date_edit)
        
        grid.addLayout(date_container, 0, 1, 1, 3)
        
        # Row 1: Device filter
        device_label = QLabel("Device:")
        device_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        device_label.setStyleSheet(self.style_manager.get_form_label_style())
        grid.addWidget(device_label, 1, 0)
        
        self.device_dropdown = CheckableComboBox()
        self.device_dropdown.setPlaceholderText("All devices")
        self.device_dropdown.setStyleSheet(self.style_manager.get_input_style())
        grid.addWidget(self.device_dropdown, 1, 1)
        
        # Row 1: Metric filter (same row as device)
        metric_label = QLabel("Metric:")
        metric_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        metric_label.setStyleSheet(self.style_manager.get_form_label_style())
        grid.addWidget(metric_label, 1, 2)
        
        self.metric_dropdown = CheckableComboBox()
        self.metric_dropdown.setPlaceholderText("All metrics")
        self.metric_dropdown.setStyleSheet(self.style_manager.get_input_style())
        grid.addWidget(self.metric_dropdown, 1, 3)
        
        layout.addLayout(grid)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(self.style_manager.get_grid_spacing(1))
        button_layout.setContentsMargins(0, self.style_manager.get_grid_spacing(1), 0, 0)
        
        self.apply_button = QPushButton("Apply Filters")
        self.apply_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        self.apply_button.clicked.connect(self._on_apply_filters)
        self.apply_button.setToolTip("Apply filters to data (Alt+A)")
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Reset Filters")
        self.reset_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.reset_button.clicked.connect(self._on_reset_filters)
        self.reset_button.setToolTip("Reset all filters (Alt+R)")
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # Preset buttons
        self.save_preset_button = QPushButton("Save Preset")
        self.save_preset_button.setStyleSheet(self.style_manager.get_button_style("ghost"))
        self.save_preset_button.clicked.connect(self._on_save_preset)
        button_layout.addWidget(self.save_preset_button)
        
        self.load_preset_button = QPushButton("Load Preset")
        self.load_preset_button.setStyleSheet(self.style_manager.get_button_style("ghost"))
        self.load_preset_button.clicked.connect(self._on_load_preset)
        button_layout.addWidget(self.load_preset_button)
        
        layout.addLayout(button_layout)
        
        return section
    
    def _create_summary_cards_section(self):
        """Create summary cards section."""
        section = self._create_section_card()
        layout = QVBoxLayout(section)
        layout.setSpacing(self.style_manager.get_grid_spacing(2))
        
        title = QLabel("Summary")
        title.setStyleSheet(self.style_manager.get_heading_style(4))
        layout.addWidget(title)
        
        # Cards container
        cards_container = QHBoxLayout()
        cards_container.setSpacing(self.style_manager.get_grid_spacing(2))
        
        # Create summary cards
        self.total_records_card = self._create_metric_card("Total Records", "0", self.style_manager.ACCENT_SECONDARY)
        self.date_range_card = self._create_metric_card("Date Range", "No data", self.style_manager.DATA_PURPLE)
        self.devices_card = self._create_metric_card("Devices", "0", self.style_manager.DATA_TEAL)
        self.metrics_card = self._create_metric_card("Metrics", "0", self.style_manager.DATA_ORANGE)
        
        cards_container.addWidget(self.total_records_card)
        cards_container.addWidget(self.date_range_card)
        cards_container.addWidget(self.devices_card)
        cards_container.addWidget(self.metrics_card)
        
        layout.addLayout(cards_container)
        
        return section
    
    def _create_metric_card(self, label, value, color):
        """Create a metric card with label and value."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: {self.style_manager.get_grid_spacing(1)}px;
                padding: {self.style_manager.get_grid_spacing(2)}px;
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
            }}
            QFrame:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                border-color: {color}33;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(self.style_manager.get_grid_spacing(1))
        
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setStyleSheet(f"""
            QLabel#metricValue {{
                font-size: 24px;
                font-weight: 600;
                color: {color};
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
            }}
        """)
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {self.style_manager.TEXT_SECONDARY};
                font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
            }}
        """)
        layout.addWidget(label_widget)
        
        # Store references for updates
        card.value_label = value_label
        card.label_widget = label_widget
        
        return card
    
    def _create_statistics_section(self):
        """Create statistics section."""
        section = self._create_section_card()
        layout = QVBoxLayout(section)
        layout.setSpacing(self.style_manager.get_grid_spacing(2))
        
        title = QLabel("Data Statistics")
        title.setStyleSheet(self.style_manager.get_heading_style(4))
        layout.addWidget(title)
        
        # Placeholder for statistics widget
        self.statistics_container = QWidget()
        self.statistics_layout = QVBoxLayout(self.statistics_container)
        self.statistics_layout.setContentsMargins(0, 0, 0, 0)
        
        # Empty state
        empty_label = QLabel("Apply filters to view data statistics")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {self.style_manager.TEXT_MUTED};
                padding: {self.style_manager.get_grid_spacing(4)}px;
            }}
        """)
        self.statistics_layout.addWidget(empty_label)
        
        layout.addWidget(self.statistics_container)
        
        return section
    
    def _create_section_card(self):
        """Create a card container for sections."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: {self.style_manager.RADIUS['lg']}px;
                padding: {self.style_manager.SPACING['md']}px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }}
        """)
        card.setGraphicsEffect(
            self.style_manager.create_shadow_effect(
                blur_radius=16,
                y_offset=4,
                opacity=8
            )
        )
        return card
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard shortcuts for better navigation."""
        # Alt+B for browse
        browse_action = QAction(self)
        browse_action.setShortcut("Alt+B")
        browse_action.triggered.connect(self._on_browse_clicked)
        self.addAction(browse_action)
        
        # Alt+I for import
        import_action = QAction(self)
        import_action.setShortcut("Alt+I")
        import_action.triggered.connect(self._on_import_clicked)
        self.addAction(import_action)
        
        # Alt+A for apply filters
        apply_action = QAction(self)
        apply_action.setShortcut("Alt+A")
        apply_action.triggered.connect(self._on_apply_filters)
        self.addAction(apply_action)
        
        # Alt+R for reset filters
        reset_action = QAction(self)
        reset_action.setShortcut("Alt+R")
        reset_action.triggered.connect(self._on_reset_filters)
        self.addAction(reset_action)
    
    def _check_database_availability(self):
        """Check if database exists without loading all data."""
        try:
            # Check if we have any data in the database
            query = "SELECT COUNT(*) as count FROM health_records LIMIT 1"
            result = db_manager.execute_query(query)
            
            if result and result[0]['count'] > 0:
                self.data_available = True
                self._update_status_message(
                    f"Database contains {result[0]['count']:,} health records. Apply filters to load data.",
                    "info"
                )
                self._update_dropdowns_from_database()
                self._update_summary_from_database()
            else:
                self.data_available = False
                self._update_status_message(
                    "No health data found. Import your Apple Health export to get started.",
                    "info"
                )
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            self.data_available = False
            self._update_status_message(
                "No health data found. Import your Apple Health export to get started.",
                "info"
            )
    
    def _update_status_message(self, message, message_type="info"):
        """Update status message with appropriate styling."""
        self.status_label.setText(message)
        
        # Apply appropriate style based on message type
        if message_type == "success":
            self.status_section.setStyleSheet(self.style_manager.get_success_message_style())
        elif message_type == "error":
            self.status_section.setStyleSheet(self.style_manager.get_error_message_style())
        else:  # info
            self.status_section.setStyleSheet(self.style_manager.get_info_message_style())
        
        self.status_section.setVisible(True)
    
    def _update_dropdowns_from_database(self):
        """Update dropdown options from database."""
        try:
            # Get unique devices
            devices_query = """
                SELECT DISTINCT device_name 
                FROM health_records 
                WHERE device_name IS NOT NULL 
                ORDER BY device_name
            """
            devices = db_manager.execute_query(devices_query)
            if devices:
                device_list = [d['device_name'] for d in devices]
                self.device_dropdown.addItems(device_list)
            
            # Get unique metrics
            metrics_query = """
                SELECT DISTINCT metric_type 
                FROM health_records 
                ORDER BY metric_type
            """
            metrics = db_manager.execute_query(metrics_query)
            if metrics:
                metric_list = [m['metric_type'] for m in metrics]
                self.metric_dropdown.addItems(metric_list)
                
        except Exception as e:
            logger.error(f"Error updating dropdowns: {e}")
    
    def _update_summary_from_database(self):
        """Update summary cards from database."""
        try:
            # Get summary statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_records,
                    MIN(timestamp) as min_date,
                    MAX(timestamp) as max_date,
                    COUNT(DISTINCT device_name) as device_count,
                    COUNT(DISTINCT metric_type) as metric_count
                FROM health_records
            """
            stats = db_manager.execute_query(stats_query)
            
            if stats and stats[0]['total_records'] > 0:
                stat = stats[0]
                
                # Update cards
                self.total_records_card.value_label.setText(f"{stat['total_records']:,}")
                
                # Format date range
                if stat['min_date'] and stat['max_date']:
                    min_date = pd.to_datetime(stat['min_date']).strftime('%b %Y')
                    max_date = pd.to_datetime(stat['max_date']).strftime('%b %Y')
                    self.date_range_card.value_label.setText(f"{min_date} - {max_date}")
                
                self.devices_card.value_label.setText(str(stat['device_count']))
                self.metrics_card.value_label.setText(str(stat['metric_count']))
                
        except Exception as e:
            logger.error(f"Error updating summary: {e}")
    
    # Placeholder methods for event handlers
    def _on_browse_clicked(self):
        """Handle browse button click."""
        pass
    
    def _on_import_clicked(self):
        """Handle import button click."""
        pass
    
    def _on_clear_data_clicked(self):
        """Handle clear data button click."""
        pass
    
    def _on_apply_filters(self):
        """Handle apply filters button click."""
        pass
    
    def _on_reset_filters(self):
        """Handle reset filters button click."""
        pass
    
    def _on_save_preset(self):
        """Handle save preset button click."""
        pass
    
    def _on_load_preset(self):
        """Handle load preset button click."""
        pass
    
    def get_filtered_data(self):
        """Get the currently filtered data."""
        return self.filtered_data