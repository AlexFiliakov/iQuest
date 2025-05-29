"""Configuration tab implementation for data import and filtering."""

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


class ConfigurationTab(QWidget):
    """Configuration tab for importing data and setting filters.
    
    This tab provides the main interface for data management in the Apple Health
    Monitor Dashboard. It handles:
    
    - CSV and XML data import with progress tracking
    - Date range filtering for data analysis
    - Device/source filtering to focus on specific data sources
    - Health metric type filtering
    - Filter preset saving and loading
    - Real-time statistics display
    - Database integration for persistent settings
    
    The tab features a clean, organized layout with distinct sections for
    import operations, filtering controls, and data statistics. It provides
    immediate feedback through progress bars, status messages, and summary cards.
    
    Signals:
        data_loaded (object): Emitted when data is successfully loaded with the DataFrame.
        filters_applied (dict): Emitted when filters are applied with filter parameters.
    
    Attributes:
        data_loader (DataLoader): Handles CSV and database loading operations.
        filter_config_manager (FilterConfigManager): Manages filter presets.
        statistics_calculator (StatisticsCalculator): Computes data statistics.
        data (DataFrame): Currently loaded health data.
        filtered_data (DataFrame): Data after applying current filters.
    """
    
    # Signals
    data_loaded = pyqtSignal(object)  # Emitted when data is successfully loaded
    filters_applied = pyqtSignal(dict)  # Emitted when filters are applied
    
    def __init__(self):
        """Initialize the configuration tab.
        
        Sets up the user interface, initializes data management components,
        creates filter controls, configures keyboard navigation, and loads
        any existing filter presets from the database.
        
        The initialization process:
        1. Initialize managers and data components
        2. Create the main UI layout with import and filter sections
        3. Set up signal connections for user interactions
        4. Configure keyboard navigation and accessibility
        5. Migrate legacy filter presets if they exist
        """
        super().__init__()
        logger.info("Initializing Configuration tab")
        
        # Initialize components
        self.style_manager = StyleManager()
        self.component_factory = ComponentFactory()
        self.data_loader = DataLoader()
        self.filter_config_manager = FilterConfigManager()
        self.statistics_calculator = StatisticsCalculator()
        
        # Initialize metric calculators as None - they'll be created when data is loaded
        self.daily_calculator = None
        self.weekly_calculator = None
        self.monthly_calculator = None
        
        self.data = None
        self.filtered_data = None
        self.statistics_widget = None
        
        # UI elements that need to be accessed
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
        
        # Legacy presets file path for migration
        self.legacy_presets_file = os.path.join(os.path.dirname(__file__), '..', '..', 'filter_presets.json')
        
        # Create the UI
        self._create_ui()
        
        # Set up keyboard navigation
        self._setup_keyboard_navigation()
        
        logger.info("Configuration tab initialized")
    
    def _create_ui(self):
        """Create the configuration tab UI.
        
        Builds the complete user interface with the following sections:
        - Title header with application branding
        - Data import section with file selection and progress tracking
        - Filter controls section with date ranges and multi-select options
        - Statistics display section with summary cards and metrics table
        
        Uses consistent spacing, margins, and styling for a professional appearance.
        """
        # Main layout with tighter spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)  # Very tight margins
        main_layout.setSpacing(12)  # Tighter spacing
        
        # Title - smaller
        title = QLabel("Configuration")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #5D4E37;
                margin-bottom: 4px;
            }
        """)
        main_layout.addWidget(title)
        
        # Create two-column layout for better space usage
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        left_column.addWidget(self._create_import_section())
        left_column.addWidget(self._create_filter_section())
        left_column.addStretch()
        
        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(12)
        right_column.addWidget(self._create_summary_cards_section())
        right_column.addWidget(self._create_statistics_section())
        right_column.addStretch()
        
        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 1)
        
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self._create_status_section())
        main_layout.addStretch()
    
    def _create_import_section(self):
        """Create the data import section."""
        group = QGroupBox("Import Data")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 6px;
                padding: 8px;
                padding-top: 20px;
                margin: 0px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # File input in a more compact vertical layout
        file_label = QLabel("Data File:")
        file_label.setStyleSheet("font-weight: 500; font-size: 12px;")
        layout.addWidget(file_label)
        
        # File selection row
        file_row = QHBoxLayout()
        file_row.setSpacing(6)
        file_row.setContentsMargins(0, 0, 0, 0)
        
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText("No file selected...")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet(self.style_manager.get_input_style() + """
            QLineEdit {
                font-size: 11px;
            }
        """)
        file_row.addWidget(self.file_path_input, 1)
        
        browse_button = QPushButton("...")
        browse_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        browse_button.clicked.connect(self._on_browse_clicked)
        browse_button.setToolTip("Browse for Apple Health export file (Alt+B)")
        browse_button.setFixedWidth(30)
        file_row.addWidget(browse_button)
        
        layout.addLayout(file_row)
        
        # Import buttons row - more compact
        import_row = QHBoxLayout()
        import_row.setSpacing(4)
        import_row.setContentsMargins(0, 4, 0, 0)
        
        import_button = QPushButton("CSV")
        import_button.setStyleSheet(self.style_manager.get_button_style("primary") + """
            QPushButton {
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setToolTip("Import CSV file (Alt+I)")
        import_button.setFixedWidth(50)
        import_row.addWidget(import_button)
        
        # Add XML import button
        import_xml_button = QPushButton("XML")
        import_xml_button.setStyleSheet(self.style_manager.get_button_style("primary") + """
            QPushButton {
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        import_xml_button.clicked.connect(self._on_import_xml_clicked)
        import_xml_button.setToolTip("Import XML file")
        import_xml_button.setFixedWidth(50)
        import_row.addWidget(import_xml_button)
        
        import_row.addStretch()
        layout.addLayout(import_row)
        
        # Progress section
        progress_row = QVBoxLayout()
        progress_row.setSpacing(8)
        
        self.progress_label = QLabel("Ready to import data")
        self.progress_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        progress_row.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                text-align: center;
                background-color: {self.style_manager.TERTIARY_BG};
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                border-radius: 6px;
            }}
        """)
        self.progress_bar.setToolTip("Shows import progress - XML imports may take several minutes")
        progress_row.addWidget(self.progress_bar)
        
        layout.addLayout(progress_row)
        
        return group
    
    def _create_filter_section(self):
        """Create the data filtering section."""
        group = QGroupBox("Filter Data")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 6px;
                padding: 8px;
                padding-top: 20px;
                margin: 0px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Date range section - compact
        date_label = QLabel("Date Range")
        date_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(date_label)
        
        date_row = QHBoxLayout()
        date_row.setSpacing(8)
        date_row.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("From:")
        start_label.setStyleSheet("font-size: 11px;")
        date_row.addWidget(start_label)
        
        self.start_date_edit = EnhancedDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.start_date_edit.setAccessibleName("Start date filter")
        self.start_date_edit.setAccessibleDescription("Filter data from this date onwards")
        self.start_date_edit.setMaximumWidth(150)
        date_row.addWidget(self.start_date_edit)
        
        end_label = QLabel("To:")
        end_label.setStyleSheet("font-size: 11px;")
        date_row.addWidget(end_label)
        
        self.end_date_edit = EnhancedDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.end_date_edit.setAccessibleName("End date filter")
        self.end_date_edit.setAccessibleDescription("Filter data up to this date")
        self.end_date_edit.setMaximumWidth(150)
        date_row.addWidget(self.end_date_edit)
        
        date_row.addStretch()
        layout.addLayout(date_row)
        
        # Add spacing instead of separator
        layout.addSpacing(16)
        
        # Devices and metrics sections - stacked vertically for better space usage
        devices_section = self._create_devices_section()
        layout.addWidget(devices_section)
        
        # Metrics section
        metrics_section = self._create_metrics_section()
        layout.addWidget(metrics_section)
        
        # Add spacing instead of separator
        layout.addSpacing(16)
        
        # Filter presets section
        presets_section = QVBoxLayout()
        presets_section.setSpacing(12)
        
        presets_label = QLabel("Filter Presets")
        presets_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        presets_section.addWidget(presets_label)
        
        presets_row = QHBoxLayout()
        presets_row.setSpacing(4)
        
        self.save_preset_button = QPushButton("Save")
        self.save_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        self.save_preset_button.clicked.connect(self._on_save_preset_clicked)
        self.save_preset_button.setEnabled(False)
        self.save_preset_button.setFixedWidth(45)
        presets_row.addWidget(self.save_preset_button)
        
        self.load_preset_button = QPushButton("Load")
        self.load_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        self.load_preset_button.clicked.connect(self._on_load_preset_clicked)
        self.load_preset_button.setEnabled(False)
        self.load_preset_button.setFixedWidth(45)
        presets_row.addWidget(self.load_preset_button)
        
        presets_row.addStretch()
        
        # Add reset app settings button
        self.reset_settings_button = QPushButton("Reset")
        self.reset_settings_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 2px 8px;
                font-size: 11px;
            }
        """)
        self.reset_settings_button.clicked.connect(self._on_reset_settings_clicked)
        self.reset_settings_button.setToolTip("Reset all application settings")
        self.reset_settings_button.setFixedWidth(45)
        presets_row.addWidget(self.reset_settings_button)
        presets_section.addLayout(presets_row)
        layout.addLayout(presets_section)
        
        # Add spacing instead of separator
        layout.addSpacing(16)
        
        # Action buttons - compact
        button_row = QHBoxLayout()
        button_row.setSpacing(4)
        button_row.addStretch()
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 3px 10px;
                font-size: 11px;
            }
        """)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.reset_button.setEnabled(False)
        self.reset_button.setFixedWidth(60)
        button_row.addWidget(self.reset_button)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setStyleSheet(self.style_manager.get_button_style("primary") + """
            QPushButton {
                padding: 3px 10px;
                font-size: 11px;
            }
        """)
        self.apply_button.clicked.connect(self._on_apply_filters_clicked)
        self.apply_button.setEnabled(False)
        self.apply_button.setFixedWidth(60)
        button_row.addWidget(self.apply_button)
        
        layout.addLayout(button_row)
        
        return group
    
    def _create_devices_section(self):
        """Create the devices selection section."""
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label = QLabel("Source Devices")
        label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(label)
        
        # Multi-select dropdown for devices
        self.device_dropdown = CheckableComboBox()
        self.device_dropdown.setPlaceholderText("Select devices...")
        self.device_dropdown.setEnabled(False)
        self.device_dropdown.setStyleSheet(self.style_manager.get_input_style() + """
            QComboBox {
                min-height: 24px;
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                max-height: 150px;
            }
        """)
        
        # Add placeholder items (will be replaced when data is loaded)
        default_devices = ["iPhone", "Apple Watch", "iPad", "Other Apps"]
        for device in default_devices:
            self.device_dropdown.addItem(device, checked=False)
        
        layout.addWidget(self.device_dropdown)
        
        return section
    
    def _create_metrics_section(self):
        """Create the metrics selection section."""
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label = QLabel("Metric Types")
        label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(label)
        
        # Multi-select dropdown for metrics
        self.metric_dropdown = CheckableComboBox()
        self.metric_dropdown.setPlaceholderText("Select metrics...")
        self.metric_dropdown.setEnabled(False)
        self.metric_dropdown.setStyleSheet(self.style_manager.get_input_style() + """
            QComboBox {
                min-height: 24px;
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                max-height: 150px;
            }
        """)
        
        # Add placeholder items (will be replaced when data is loaded)
        default_metrics = ["Heart Rate", "Steps", "Sleep", "Workouts"]
        for metric in default_metrics:
            self.metric_dropdown.addItem(metric, checked=False)
        
        layout.addWidget(self.metric_dropdown)
        
        return section
    
    def _create_statistics_section(self):
        """Create the statistics display section."""
        # Main container without GroupBox for better integration
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Data Preview Section
        preview_group = QGroupBox("Data Preview")
        preview_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                padding: 12px;
                padding-top: 24px;
                margin-bottom: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create data preview table with larger page size
        self.data_preview_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=5,  # Reduced for space
                alternating_rows=True,
                grid_style='dotted'
            ),
            wsj_style=True
        )
        
        # Set minimum height for better visibility
        self.data_preview_table.setMinimumHeight(120)
        
        # Apply custom styling for better readability
        self.data_preview_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 11px;
                gridline-color: rgba(139, 115, 85, 0.2);
                background-color: white;
                alternate-background-color: {self.style_manager.TERTIARY_BG};
                selection-background-color: {self.style_manager.ACCENT_LIGHT};
            }}
            QTableWidget::item {{
                padding: 4px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                color: white;
                padding: 6px;
                border: none;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
        
        preview_layout.addWidget(self.data_preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Data Statistics Section
        stats_group = QGroupBox("Data Statistics")
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                padding: 12px;
                padding-top: 24px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(12, 12, 12, 12)
        
        # Create custom statistics widget without internal scroll
        self.statistics_widget = self._create_custom_statistics_widget()
        stats_layout.addWidget(self.statistics_widget)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        return container
    
    def _create_custom_statistics_widget(self):
        """Create custom statistics widget without internal scrolling."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Summary section
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        
        # Total Records
        self.stats_total_label = QLabel("Total Records: -")
        self.stats_total_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 12px 20px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 8px;
            }}
        """)
        summary_layout.addWidget(self.stats_total_label)
        
        # Date Range
        self.stats_date_label = QLabel("Date Range: -")
        self.stats_date_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 12px 20px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 8px;
            }}
        """)
        summary_layout.addWidget(self.stats_date_label)
        summary_layout.addStretch()
        
        layout.addLayout(summary_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: rgba(139, 115, 85, 0.2);")
        layout.addWidget(separator)
        
        # Two-column layout for Record Types and Data Sources
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)
        
        # Record Types Column
        types_column = QWidget()
        types_layout = QVBoxLayout(types_column)
        types_layout.setContentsMargins(0, 0, 0, 0)
        
        types_title = QLabel("Record Types")
        types_title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 8px;
            }}
        """)
        types_layout.addWidget(types_title)
        
        # Record types table
        self.record_types_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=15,  # Show more records
                alternating_rows=True,
                resizable_columns=True,
                movable_columns=False,
                selection_mode='row',
                multi_select=False
            ),
            wsj_style=True
        )
        self.record_types_table.setMinimumHeight(250)
        self.record_types_table.setMaximumHeight(400)
        types_layout.addWidget(self.record_types_table)
        
        columns_layout.addWidget(types_column, 1)
        
        # Data Sources Column
        sources_column = QWidget()
        sources_layout = QVBoxLayout(sources_column)
        sources_layout.setContentsMargins(0, 0, 0, 0)
        
        sources_title = QLabel("Data Sources")
        sources_title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 8px;
            }}
        """)
        sources_layout.addWidget(sources_title)
        
        # Data sources table
        self.data_sources_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=15,  # Show more records
                alternating_rows=True,
                resizable_columns=True,
                movable_columns=False,
                selection_mode='row',
                multi_select=False
            ),
            wsj_style=True
        )
        self.data_sources_table.setMinimumHeight(250)
        self.data_sources_table.setMaximumHeight(400)
        sources_layout.addWidget(self.data_sources_table)
        
        columns_layout.addWidget(sources_column, 1)
        
        layout.addLayout(columns_layout)
        
        # Store original statistics widget for compatibility
        self.statistics_widget = StatisticsWidget()
        self.statistics_widget.setVisible(False)  # Hide original widget
        
        return widget
    
    def _create_summary_cards_section(self):
        """Create summary cards for data overview."""
        section = QWidget(self)
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(16)  # Add spacing between cards
        
        # Create summary cards with WSJ styling
        self.total_records_card = self.component_factory.create_metric_card(
            title="Total Records",
            value="-",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        self.filtered_records_card = self.component_factory.create_metric_card(
            title="Filtered Records",
            value="-",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        self.data_source_card = self.component_factory.create_metric_card(
            title="Data Source",
            value="None",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        self.filter_status_card = self.component_factory.create_metric_card(
            title="Filter Status",
            value="No filters",
            card_type="simple",
            size="medium",
            wsj_style=True
        )
        
        layout.addWidget(self.total_records_card)
        layout.addWidget(self.filtered_records_card)
        layout.addWidget(self.data_source_card)
        layout.addWidget(self.filter_status_card)
        layout.addStretch()
        
        return section
    
    def _create_status_section(self):
        """Create the status display section."""
        section = QWidget(self)
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("No data loaded")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        self.status_label.setToolTip("Shows the current status of loaded data and applied filters")
        layout.addWidget(self.status_label)
        
        return section
    
    def _on_browse_clicked(self):
        """Handle browse button click."""
        logger.debug("Browse button clicked")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Apple Health Export File",
            "",
            "Supported Files (*.csv *.xml);;CSV Files (*.csv);;XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            self.file_path_input.setText(file_path)
            logger.info(f"Selected file: {file_path}")
    
    def _on_import_clicked(self):
        """Handle import button click."""
        file_path = self.file_path_input.text()
        if not file_path:
            QMessageBox.warning(
                self,
                "No File Selected",
                "Please select a file to import."
            )
            return
        
        # Check file extension
        if not file_path.lower().endswith(('.csv', '.xml')):
            QMessageBox.warning(
                self,
                "Unsupported File Type",
                "Please select a CSV or XML file to import."
            )
            return
        
        logger.info(f"Starting import of: {file_path}")
        self._start_import_with_progress(file_path)
    
    def _on_import_xml_clicked(self):
        """Handle import XML button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Apple Health XML Export",
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            logger.info(f"Starting XML import of: {file_path}")
            self._start_import_with_progress(file_path)
    
    def _start_import_with_progress(self, file_path):
        """Start import with progress dialog."""
        # Create and show import progress dialog
        progress_dialog = ImportProgressDialog(file_path, "auto", self)
        progress_dialog.import_completed.connect(self._on_import_completed)
        progress_dialog.import_cancelled.connect(self._on_import_cancelled)
        
        # Start the import process
        progress_dialog.start_import()
        
        # Show dialog
        progress_dialog.exec()
    
    def _on_import_completed(self, result):
        """Handle successful import completion."""
        try:
            logger.info(f"Import completed successfully: {result}")
            
            # Load data based on import type
            if result['import_type'] == 'csv' and 'data' in result:
                # CSV data is already loaded
                self.data = result['data']
            else:
                # For XML imports, load from database
                self._load_from_sqlite()
                return  # _load_from_sqlite handles the rest
            
            # Update UI
            row_count = result.get('record_count', 0)
            self.progress_bar.setVisible(False)
            self.progress_label.setText("Data imported successfully!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
            
            # Update status
            self._update_status(f"Loaded {row_count:,} records")
            
            # Update summary cards
            self.total_records_card.update_content({'value': f"{row_count:,}"})
            self.filtered_records_card.update_content({'value': f"{row_count:,}"})
            self.data_source_card.update_content({'value': "CSV File"})
            self.filter_status_card.update_content({'value': "Default"})
            
            # Populate filters
            self._populate_filters()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
            # Update data preview
            self._update_data_preview()
            
            # Calculate and display statistics
            if self.data is not None and not self.data.empty:
                stats = self.statistics_calculator.calculate_from_dataframe(self.data)
                self._update_custom_statistics(stats)
            
            # Load last used filters if available
            self._load_last_used_filters()
            
            # Initialize calculators with the loaded data
            self._initialize_calculators()
            
            # Emit signal
            self.data_loaded.emit(self.data)
            
            logger.info(f"Import UI updated: {row_count} records")
            
        except Exception as e:
            logger.error(f"Failed to finalize import: {e}")
            self.progress_label.setText("Import failed!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_ERROR};")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to finalize import: {str(e)}"
            )
    
    def _on_import_cancelled(self):
        """Handle import cancellation."""
        logger.info("Import was cancelled by user")
        self.progress_label.setText("Import cancelled")
        self.progress_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
    
    def _load_from_sqlite(self):
        """Load data from SQLite database."""
        try:
            logger.info("Loading data from SQLite database")
            
            # Set database path
            db_path = os.path.join(DATA_DIR, "health_data.db")
            self.data_loader.db_path = db_path
            
            # Load data
            self.data = self.data_loader.load_from_sqlite()
            
            if self.data is None or self.data.empty:
                raise ValueError("No data found in database")
            
            row_count = len(self.data)
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("Data loaded from database!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
            
            # Update status
            self._update_status(f"Loaded {row_count:,} records from database")
            
            # Update summary cards
            self.total_records_card.update_content({'value': f"{row_count:,}"})
            self.filtered_records_card.update_content({'value': f"{row_count:,}"})
            self.data_source_card.update_content({'value': "Database"})
            self.filter_status_card.update_content({'value': "Default"})
            
            # Populate filters
            self._populate_filters()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
            # Update data preview
            self._update_data_preview()
            
            # Calculate and display statistics
            stats = self.statistics_calculator.calculate_from_dataframe(self.data)
            self._update_custom_statistics(stats)
            
            # Load last used filters if available
            self._load_last_used_filters()
            
            # Initialize calculators
            self._initialize_calculators()
            
            # Emit signal
            self.data_loaded.emit(self.data)
            
            logger.info(f"Database load complete: {row_count} records")
            
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
            self.progress_label.setText("Database load failed!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_ERROR};")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load from database: {str(e)}"
            )
    
    def _populate_filters(self):
        """Populate filter options from loaded data."""
        if self.data is None:
            return
        
        # Use DataFilterEngine to get distinct values for better performance
        filter_engine = DataFilterEngine(self.data_loader.db_path if hasattr(self.data_loader, 'db_path') else None)
        
        # Get unique devices and metrics from the filter engine
        unique_devices = filter_engine.get_distinct_sources()
        unique_metrics = filter_engine.get_distinct_types()
        
        # Clear and repopulate device dropdown
        self.device_dropdown.clear()
        for device in unique_devices:
            self.device_dropdown.addItem(str(device), checked=True)  # Default to all selected
        
        # Clear and repopulate metric dropdown
        self.metric_dropdown.clear()
        for metric in unique_metrics:
            self.metric_dropdown.addItem(str(metric), checked=True)  # Default to all selected
        
        logger.info(f"Populated filters: {len(unique_devices)} devices, {len(unique_metrics)} metrics")
    
    def _enable_filter_controls(self, enabled):
        """Enable or disable filter controls."""
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.save_preset_button.setEnabled(enabled)
        self.load_preset_button.setEnabled(enabled)
        self.device_dropdown.setEnabled(enabled)
        self.metric_dropdown.setEnabled(enabled)
    
    def _on_apply_filters_clicked(self):
        """Handle apply filters button click."""
        if self.data is None:
            return
        
        logger.info("Applying filters")
        
        # Get filter settings
        filters = {
            'start_date': self.start_date_edit.date().toPyDate(),
            'end_date': self.end_date_edit.date().toPyDate(),
            'devices': self.device_dropdown.checkedTexts(),
            'metrics': self.metric_dropdown.checkedTexts()
        }
        
        # Apply filters
        start_time = time.time()
        self.filtered_data = self._apply_filters(filters)
        filter_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Update status with performance info
        original_count = len(self.data)
        filtered_count = len(self.filtered_data) if self.filtered_data is not None else 0
        self._update_status(
            f"Showing {filtered_count:,} of {original_count:,} records "
            f"({filtered_count/original_count*100:.1f}%) - Filtered in {filter_time:.0f}ms"
        )
        
        # Update summary cards
        self.filtered_records_card.update_content({'value': f"{filtered_count:,}"})
        percentage = f"{filtered_count/original_count*100:.1f}%"
        self.filter_status_card.update_content({'value': f"Active ({percentage})"})
        
        # Update statistics for filtered data
        if self.filtered_data is not None and not self.filtered_data.empty:
            stats = self.statistics_calculator.calculate_from_dataframe(self.filtered_data)
            self._update_custom_statistics(stats)
        
        # Show feedback
        self.apply_button.setText("Filters Applied ✓")
        self.apply_button.setStyleSheet(self.style_manager.get_button_style("primary") + f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SUCCESS};
            }}
        """)
        
        # Reset button text after delay
        QTimer.singleShot(2000, lambda: self.apply_button.setText("Apply Filters"))
        QTimer.singleShot(2000, lambda: self.apply_button.setStyleSheet(
            self.style_manager.get_button_style("primary")
        ))
        
        # Save as last used filters
        self._save_as_last_used(filters)
        
        # Emit signal
        self.filters_applied.emit(filters)
        
        logger.info(f"Filters applied: {filtered_count}/{original_count} records")
    
    def _apply_filters(self, filters):
        """Apply filters to the data using the DataFilterEngine."""
        if self.data is None:
            return None
        
        # Create filter criteria
        criteria = FilterCriteria(
            start_date=filters['start_date'],
            end_date=filters['end_date'],
            source_names=filters['devices'] if filters['devices'] else None,
            health_types=filters['metrics'] if filters['metrics'] else None
        )
        
        # Use the filter engine
        filter_engine = DataFilterEngine(self.data_loader.db_path if hasattr(self.data_loader, 'db_path') else None)
        
        try:
            # Apply filters using the engine
            filtered = filter_engine.filter_data(criteria)
            
            # Log performance metrics
            metrics = filter_engine.get_performance_metrics()
            logger.info(f"Filter query completed in {metrics['last_query_time']:.2f}ms")
            
            return filtered
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            QMessageBox.warning(self, "Filter Error", f"Failed to apply filters: {str(e)}")
            return self.data
    
    def _on_reset_clicked(self):
        """Handle reset filters button click."""
        logger.info("Resetting filters")
        
        # Reset date range
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # Check all devices
        self.device_dropdown.checkAll()
        
        # Check all metrics
        self.metric_dropdown.checkAll()
        
        # Apply reset
        self._on_apply_filters_clicked()
    
    def _on_reset_settings_clicked(self):
        """Handle reset app settings button click."""
        logger.info("Reset app settings requested")
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Reset Application Settings",
            "This will reset all application settings including:\n"
            "• Window size and position\n"
            "• Last active tab\n"
            "• Other saved preferences\n\n"
            "The application will need to be restarted for changes to take effect.\n\n"
            "Are you sure you want to reset all settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Create settings manager instance and clear settings
                settings_manager = SettingsManager()
                settings_manager.clear_settings()
                
                QMessageBox.information(
                    self,
                    "Settings Reset",
                    "All application settings have been reset.\n"
                    "Please restart the application for changes to take effect."
                )
                logger.info("Application settings reset successfully")
                
            except Exception as e:
                logger.error(f"Failed to reset settings: {e}")
                QMessageBox.critical(
                    self,
                    "Reset Error",
                    f"Failed to reset application settings: {str(e)}"
                )
    
    def _on_save_preset_clicked(self):
        """Handle save preset button click."""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get preset name from user
        preset_name, ok = QInputDialog.getText(
            self,
            "Save Filter Preset",
            "Enter a name for this filter preset:"
        )
        
        if ok and preset_name:
            try:
                # Create filter config
                config = FilterConfig(
                    preset_name=preset_name,
                    start_date=self.start_date_edit.date().toPyDate(),
                    end_date=self.end_date_edit.date().toPyDate(),
                    source_names=self.device_dropdown.checkedTexts() if self.device_dropdown.checkedTexts() else None,
                    health_types=self.metric_dropdown.checkedTexts() if self.metric_dropdown.checkedTexts() else None
                )
                
                # Save to database
                self.filter_config_manager.save_preset(config)
                
                QMessageBox.information(
                    self,
                    "Preset Saved",
                    f"Filter preset '{preset_name}' saved successfully!"
                )
                logger.info(f"Saved filter preset: {preset_name}")
                
            except Exception as e:
                logger.error(f"Failed to save preset: {e}")
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save filter preset: {str(e)}"
                )
    
    def _on_load_preset_clicked(self):
        """Handle load preset button click."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox
        
        try:
            # Get available presets
            presets = self.filter_config_manager.list_presets()
            
            if not presets:
                QMessageBox.information(
                    self,
                    "No Presets",
                    "No filter presets have been saved yet."
                )
                return
            
            # Create selection dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Load Filter Preset")
            dialog.setMinimumWidth(300)
            
            layout = QVBoxLayout(dialog)
            
            # Add list widget
            list_widget = QListWidget()
            for preset in presets:
                list_widget.addItem(preset['preset_name'])
            list_widget.setCurrentRow(0)
            layout.addWidget(list_widget)
            
            # Add buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            # Show dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_item = list_widget.currentItem()
                if selected_item:
                    preset_name = selected_item.text()
                    self._load_preset(preset_name)
                    
        except Exception as e:
            logger.error(f"Failed to load preset list: {e}")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load filter presets: {str(e)}"
            )
    
    def _load_preset(self, preset_name):
        """Load a specific filter preset."""
        try:
            config = self.filter_config_manager.load_preset(preset_name)
            
            if config:
                # Apply preset values
                self.start_date_edit.setDate(QDate(config.start_date))
                self.end_date_edit.setDate(QDate(config.end_date))
                
                # Update device selection
                self.device_dropdown.uncheckAll()
                if config.source_names:
                    for device in config.source_names:
                        for i in range(self.device_dropdown.count()):
                            if self.device_dropdown.itemText(i) == device:
                                self.device_dropdown.setItemChecked(i, True)
                else:
                    self.device_dropdown.checkAll()
                
                # Update metric selection
                self.metric_dropdown.uncheckAll()
                if config.health_types:
                    for metric in config.health_types:
                        for i in range(self.metric_dropdown.count()):
                            if self.metric_dropdown.itemText(i) == metric:
                                self.metric_dropdown.setItemChecked(i, True)
                else:
                    self.metric_dropdown.checkAll()
                
                # Apply the loaded filters
                self._on_apply_filters_clicked()
                
                logger.info(f"Loaded filter preset: {preset_name}")
            else:
                raise ValueError(f"Preset '{preset_name}' not found")
                
        except Exception as e:
            logger.error(f"Failed to load preset '{preset_name}': {e}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load preset '{preset_name}': {str(e)}"
            )
    
    def _load_last_used_filters(self):
        """Load and apply last used filter configuration."""
        try:
            config = self.filter_config_manager.get_last_used()
            
            if config:
                # Apply last used values
                self.start_date_edit.setDate(QDate(config.start_date))
                self.end_date_edit.setDate(QDate(config.end_date))
                
                # Only update selections if they differ from defaults
                if config.source_names is not None:
                    self.device_dropdown.uncheckAll()
                    for device in config.source_names:
                        for i in range(self.device_dropdown.count()):
                            if self.device_dropdown.itemText(i) == device:
                                self.device_dropdown.setItemChecked(i, True)
                
                if config.health_types is not None:
                    self.metric_dropdown.uncheckAll()
                    for metric in config.health_types:
                        for i in range(self.metric_dropdown.count()):
                            if self.metric_dropdown.itemText(i) == metric:
                                self.metric_dropdown.setItemChecked(i, True)
                
                # Don't auto-apply, just load the values
                logger.info("Loaded last used filter configuration")
            else:
                # No last used config, ensure all items are checked
                self.device_dropdown.checkAll()
                self.metric_dropdown.checkAll()
                logger.info("Loaded default filter configuration")
        except Exception as e:
            logger.warning(f"Failed to load last used filters: {e}")
    
    def _save_as_last_used(self, filters):
        """Save current filters as last used configuration."""
        try:
            config = FilterConfig(
                preset_name="__last_used__",
                start_date=filters['start_date'],
                end_date=filters['end_date'],
                source_names=filters['devices'] if filters['devices'] else None,
                health_types=filters['metrics'] if filters['metrics'] else None,
                is_last_used=True
            )
            
            self.filter_config_manager.save_as_last_used(config)
            logger.debug("Saved current filters as last used")
        except Exception as e:
            logger.warning(f"Failed to save last used filters: {e}")
    
    def _setup_keyboard_navigation(self):
        """Set up tab order and keyboard shortcuts."""
        logger.debug("Setting up keyboard navigation for Configuration tab")
        
        # Set up logical tab order for import section
        self.setTabOrder(self.file_path_input, self.findChild(QPushButton, "Browse..."))
        
        # Set up tab order for filter section
        self.setTabOrder(self.start_date_edit, self.end_date_edit)
        self.setTabOrder(self.end_date_edit, self.device_dropdown)
        self.setTabOrder(self.device_dropdown, self.metric_dropdown)
        self.setTabOrder(self.metric_dropdown, self.save_preset_button)
        self.setTabOrder(self.save_preset_button, self.load_preset_button)
        self.setTabOrder(self.load_preset_button, self.reset_settings_button)
        self.setTabOrder(self.reset_settings_button, self.reset_button)
        self.setTabOrder(self.reset_button, self.apply_button)
        
        # Add keyboard shortcuts for buttons
        # Alt+B for Browse
        browse_action = QAction(self)
        browse_action.setShortcut("Alt+B")
        browse_action.triggered.connect(self._on_browse_clicked)
        self.addAction(browse_action)
        
        # Alt+I for Import
        import_action = QAction(self)
        import_action.setShortcut("Alt+I")
        import_action.triggered.connect(self._on_import_clicked)
        self.addAction(import_action)
        
        # Alt+A for Apply Filters
        apply_action = QAction(self)
        apply_action.setShortcut("Alt+A")
        apply_action.triggered.connect(self._on_apply_filters_clicked)
        self.addAction(apply_action)
        
        # Alt+R for Reset Filters
        reset_action = QAction(self)
        reset_action.setShortcut("Alt+R")
        reset_action.triggered.connect(self._on_reset_clicked)
        self.addAction(reset_action)
        
        # Add tooltips for accessibility
        self.file_path_input.setToolTip("Path to Apple Health export file")
        self.start_date_edit.setToolTip("Filter data from this date (inclusive)")
        self.end_date_edit.setToolTip("Filter data up to this date (inclusive)")
        self.device_dropdown.setToolTip("Select which devices to include in the data")
        self.metric_dropdown.setToolTip("Select which health metrics to include")
        self.apply_button.setToolTip("Apply the selected filters to the data (Alt+A)")
        self.reset_button.setToolTip("Reset all filters to default values (Alt+R)")
        self.save_preset_button.setToolTip("Save the current filter configuration")
        self.load_preset_button.setToolTip("Load a previously saved filter configuration")
    
    def _update_custom_statistics(self, stats):
        """Update the custom statistics display."""
        if not stats:
            self.stats_total_label.setText("Total Records: -")
            self.stats_date_label.setText("Date Range: -")
            self.record_types_table.clear_data() if hasattr(self, 'record_types_table') else None
            self.data_sources_table.clear_data() if hasattr(self, 'data_sources_table') else None
            return
        
        # Update summary labels
        self.stats_total_label.setText(f"Total Records: {stats.total_records:,}")
        
        if stats.date_range[0] and stats.date_range[1]:
            try:
                date_str = f"{stats.date_range[0].strftime('%Y-%m-%d')} to {stats.date_range[1].strftime('%Y-%m-%d')}"
                self.stats_date_label.setText(f"Date Range: {date_str}")
            except:
                self.stats_date_label.setText("Date Range: Invalid dates")
        else:
            self.stats_date_label.setText("Date Range: -")
        
        # Update record types table
        if hasattr(self, 'record_types_table') and stats.records_by_type:
            types_data = []
            for type_name, count in sorted(stats.records_by_type.items(), 
                                         key=lambda x: x[1], reverse=True):
                types_data.append({
                    'Type': type_name,
                    'Count': f"{count:,}",
                    'Percentage': f"{(count/stats.total_records)*100:.1f}%"
                })
            if types_data:
                types_df = pd.DataFrame(types_data)
                self.record_types_table.load_data(types_df)
        
        # Update data sources table
        if hasattr(self, 'data_sources_table') and stats.records_by_source:
            sources_data = []
            for source_name, count in sorted(stats.records_by_source.items(), 
                                           key=lambda x: x[1], reverse=True):
                sources_data.append({
                    'Source': source_name,
                    'Count': f"{count:,}",
                    'Percentage': f"{(count/stats.total_records)*100:.1f}%"
                })
            if sources_data:
                sources_df = pd.DataFrame(sources_data)
                self.data_sources_table.load_data(sources_df)
        
        # Also update original statistics widget for compatibility
        if hasattr(self, 'statistics_widget'):
            self.statistics_widget.update_statistics(stats)
    
    def _update_data_preview(self):
        """Update the data preview table with sample data."""
        if self.data is None or self.data.empty:
            if hasattr(self, 'data_preview_table'):
                self.data_preview_table.clear_data()
            return
        
        # Get a sample of the data
        sample_size = min(10, len(self.data))
        sample_data = self.data.head(sample_size).copy()
        
        # Select relevant columns for preview
        preview_columns = []
        for col in ['type', 'sourceName', 'value', 'unit', 'creationDate', 'startDate', 'endDate']:
            if col in sample_data.columns:
                preview_columns.append(col)
        
        if preview_columns:
            preview_data = sample_data[preview_columns]
            
            # Format dates for better readability
            for col in ['creationDate', 'startDate', 'endDate']:
                if col in preview_data.columns:
                    try:
                        preview_data[col] = pd.to_datetime(preview_data[col]).dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
            
            # Load into preview table
            if hasattr(self, 'data_preview_table'):
                self.data_preview_table.load_data(preview_data)
    
    def _update_status(self, message):
        """Update the status label with a message."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
    
    def _on_statistics_filter_requested(self, filter_type, filter_value):
        """Handle filter request from statistics widget."""
        # This method handles clicks on statistics items to filter data
        pass
    
    def _initialize_calculators(self):
        """Initialize metric calculators with loaded data."""
        if self.data is None or self.data.empty:
            logger.warning("Cannot initialize calculators without data")
            return
            
        try:
            from ..analytics import DailyMetricsCalculator, WeeklyMetricsCalculator, MonthlyMetricsCalculator
            
            # Create daily calculator with the loaded data
            self.daily_calculator = DailyMetricsCalculator(self.data)
            
            # Create weekly calculator using the daily calculator
            self.weekly_calculator = WeeklyMetricsCalculator(self.daily_calculator)
            
            # Create monthly calculator using the daily calculator
            self.monthly_calculator = MonthlyMetricsCalculator(self.daily_calculator)
            
            logger.info("Metric calculators initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize calculators: {e}")
            # Keep calculators as None if initialization fails
            self.daily_calculator = None
            self.weekly_calculator = None
            self.monthly_calculator = None
    
    def get_filtered_data(self):
        """Get the current filtered data or full data if no filters applied."""
        return self.filtered_data if self.filtered_data is not None else self.data