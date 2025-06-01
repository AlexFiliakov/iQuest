"""Configuration tab implementation for data import and filtering.

This module provides the main configuration interface for the Apple Health
Monitor Dashboard. It handles all aspects of data management including import,
filtering, and statistical analysis with optimized performance for large
datasets.

The configuration tab serves as the primary entry point for users to:
    - Import Apple Health data from CSV or XML files
    - Apply sophisticated filtering to focus on specific data subsets
    - View real-time statistics and data previews
    - Manage filter presets for recurring analysis patterns
    - Monitor data loading and processing progress

Key features:
    - Deferred data loading for improved startup performance
    - SQL-optimized queries for large dataset handling
    - Comprehensive caching system for frequently accessed data
    - Modern responsive UI with accessibility support
    - Real-time progress tracking for long-running operations

Example:
    Basic usage:
        
        >>> config_tab = ConfigurationTab()
        >>> config_tab.data_loaded.connect(handle_data_loaded)
        >>> config_tab.filters_applied.connect(handle_filters_applied)
        
    Accessing filtered data:
        
        >>> filtered_data = config_tab.get_filtered_data()
        >>> if filtered_data is not None:
        ...     print(f"Loaded {len(filtered_data)} records")

Attributes:
    DATA_DIR (str): Directory for storing application data files
    ORGANIZATION_NAME (str): Organization name for settings storage
    APP_NAME (str): Application name for settings storage
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

from ..analytics.cache_manager import get_cache_manager
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
    
    This tab provides the comprehensive interface for data management in the
    Apple Health Monitor Dashboard. It implements a modern, responsive design
    with optimized performance for handling large Apple Health datasets.
    
    Core functionality:
        - Multi-format data import (CSV, XML) with progress tracking
        - Advanced filtering system with date ranges and multi-select options
        - Real-time statistics computation and display
        - Filter preset management for recurring analysis patterns
        - Deferred loading for improved performance
        - Comprehensive caching system for frequently accessed data
    
    UI organization:
        The tab uses a two-column responsive layout:
        - Left column: Import controls and filtering options
        - Right column: Summary cards and data statistics
        - Bottom section: Status information and progress tracking
    
    Performance optimizations:
        - SQL-based statistics computation for large datasets
        - Deferred data loading only when filters are applied
        - Comprehensive caching with TTL for frequently accessed data
        - Background processing for non-blocking operations
    
    Accessibility features:
        - Comprehensive keyboard navigation with shortcuts
        - Descriptive tooltips and status messages
        - Logical tab order for screen readers
        - High contrast styling for visual accessibility
    
    Signals:
        data_loaded (object): Emitted when data is successfully loaded.
            Args:
                data (pandas.DataFrame): The loaded health data
        filters_applied (dict): Emitted when filters are applied.
            Args:
                filters (dict): Applied filter parameters including dates,
                    devices, and metrics
    
    Attributes:
        data_loader (DataLoader): Handles CSV and database operations.
        filter_config_manager (FilterConfigManager): Manages filter presets.
        statistics_calculator (StatisticsCalculator): Computes data statistics.
        cache_manager (CacheManager): Handles performance caching.
        daily_calculator (DailyMetricsCalculator): Daily metrics computation.
        weekly_calculator (WeeklyMetricsCalculator): Weekly metrics computation.
        monthly_calculator (MonthlyMetricsCalculator): Monthly metrics computation.
        data (DataFrame): Currently loaded health data (lazy-loaded).
        filtered_data (DataFrame): Data after applying current filters.
        data_available (bool): Whether data exists without loading it.
        
    Example:
        Basic configuration tab usage:
        
        >>> config_tab = ConfigurationTab()
        >>> 
        >>> # Connect to data loading signal
        >>> config_tab.data_loaded.connect(lambda data: print(f"Loaded {len(data)} records"))
        >>> 
        >>> # Connect to filter application signal
        >>> config_tab.filters_applied.connect(lambda filters: print(f"Applied filters: {filters}"))
        >>> 
        >>> # Get currently filtered data
        >>> filtered_data = config_tab.get_filtered_data()
    """
    
    # Signals
    data_loaded = pyqtSignal(object)  # Emitted when data is successfully loaded
    filters_applied = pyqtSignal(dict)  # Emitted when filters are applied
    data_cleared = pyqtSignal()  # Emitted when all health data is cleared
    
    def __init__(self):
        """Initialize the configuration tab with comprehensive data management.
        
        Sets up the complete user interface and initializes all data management
        components with performance optimizations. The initialization process
        is designed for fast startup while providing full functionality.
        
        Initialization sequence:
            1. Initialize core managers (style, components, data loading)
            2. Initialize filtering and statistics components
            3. Initialize performance caching system
            4. Set up metric calculators (lazy initialization)
            5. Create responsive UI layout with accessibility features
            6. Configure comprehensive keyboard navigation
            7. Set up database availability checking (deferred data loading)
            8. Migrate legacy filter presets if they exist
        
        Performance features:
            - Deferred data loading for faster startup
            - Cache manager integration for frequently accessed data
            - SQL-optimized queries for large dataset handling
            - Background database availability checking
        
        Accessibility features:
            - Comprehensive keyboard shortcuts (Alt+B, Alt+I, Alt+A, Alt+R)
            - Logical tab order for screen reader navigation
            - Descriptive tooltips and status messages
            - High contrast styling for visual accessibility
        
        Raises:
            Exception: If critical components cannot be initialized
            
        Note:
            Data is not automatically loaded on startup for performance.
            Use _check_database_availability() to check for existing data.
        """
        super().__init__()
        logger.info("Initializing Configuration tab")
        
        # Initialize components
        self.style_manager = StyleManager()
        self.component_factory = ComponentFactory()
        self.data_loader = DataLoader()
        self.filter_config_manager = FilterConfigManager()
        self.statistics_calculator = StatisticsCalculator()
        self.cache_manager = get_cache_manager()  # Get singleton cache manager for performance
        
        # Initialize metric calculators as None - they'll be created when data is loaded
        self.daily_calculator = None
        self.weekly_calculator = None
        self.monthly_calculator = None
        
        self.data = None
        self.filtered_data = None
        self.statistics_widget = None
        self.data_available = False  # Track if data is available without loading it
        
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
        
        # OPTIMIZATION: Disabled auto-load on startup to improve performance
        # Data will be loaded on-demand when user applies filters
        # QTimer.singleShot(100, self._check_existing_data)
        
        # Instead, just check if database exists and show appropriate message
        QTimer.singleShot(100, self._check_database_availability)
        
        logger.info("Configuration tab initialized")
    
    def _create_ui(self):
        """Create the comprehensive configuration tab UI.
        
        Builds the complete user interface using a modern, responsive design
        with professional styling and accessibility features. The layout is
        optimized for both efficiency and visual appeal.
        
        UI structure:
            Main scroll area containing:
                - Optional status message area at the top
                - Single column vertical layout with sections:
                  1. Import Data section
                  2. Filter Data section  
                  3. Summary Cards section
                  4. Data Preview section
                  5. Data Statistics section
                  6. Data Sources section
        
        Design features:
            - Consistent spacing and margins for professional appearance
            - Modern card-based layout with subtle shadows
            - Responsive design that adapts to different screen sizes
            - Professional color palette with high contrast ratios
            - Smooth scrolling with custom styled scroll bars
        
        Accessibility features:
            - Logical visual hierarchy with proper heading structure
            - High contrast colors for visual accessibility
            - Keyboard-accessible interactive elements
            - Descriptive labels and tooltips for screen readers
        
        Performance optimizations:
            - Efficient layout management to minimize redraws
            - Lazy loading of complex widgets
            - Optimized styling to reduce rendering overhead
        """
        # Create main scroll area for the entire page
        main_scroll = QScrollArea(self)
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.style_manager.TERTIARY_BG};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        # Main container widget
        main_widget = QWidget()
        main_widget.setObjectName("configurationContent")
        main_widget.setStyleSheet(f"""
            QWidget#configurationContent {{
                background-color: {self.style_manager.SECONDARY_BG};
            }}
        """)
        
        # Main layout with appropriate spacing - single column
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(40, 24, 40, 24)  # Increased margins
        main_layout.setSpacing(32)  # Increased spacing between major sections
        
        # Title - larger and more prominent
        title = QLabel("Configuration")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 8px;
            }}
        """)
        main_layout.addWidget(title)
        
        # Status section at the top (initially hidden)
        self.status_section = self._create_status_section()
        self.status_section.setVisible(False)  # Hidden by default
        main_layout.addWidget(self.status_section)
        
        # Single column layout with maximum width constraint
        content_widget = QWidget()
        content_widget.setMaximumWidth(1200)  # Constrain width for readability
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(28)
        
        # Add all sections in vertical order
        # 1. Import Data section
        content_layout.addWidget(self._create_import_section())
        
        # 2. Filter Data section
        content_layout.addWidget(self._create_filter_section())
        
        # 3. Summary Cards section
        content_layout.addWidget(self._create_summary_cards_section())
        
        # 4-6. Data Preview, Statistics, and Sources sections
        content_layout.addWidget(self._create_statistics_section())
        
        content_layout.addStretch()
        
        # Center the content widget horizontally
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(content_widget)
        h_layout.addStretch()
        
        main_layout.addLayout(h_layout)
        
        # Set the main widget as the scroll area's content
        main_scroll.setWidget(main_widget)
        
        # Create the tab's layout and add the scroll area
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(main_scroll)
    
    def _create_import_section(self):
        """Create the data import section."""
        section = QFrame()
        section.setObjectName("importSection")
        section.setStyleSheet(f"""
            QFrame#importSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        
        # Add subtle shadow effect
        section.setGraphicsEffect(self.style_manager.create_shadow_effect(blur_radius=8, y_offset=1, opacity=10))
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Section title
        title = QLabel("Import Data")
        title.setObjectName("sectionTitle")
        title.setStyleSheet(f"""
            QLabel#sectionTitle {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 12px;
            }}
        """)
        layout.addWidget(title)
        
        # Remove group box - use direct layout instead
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(0, 0, 0, 0)
        
        # File input in a more compact vertical layout
        file_label = QLabel("Data File:")
        file_label.setStyleSheet("font-weight: 500; font-size: 12px;")
        group_layout.addWidget(file_label)
        
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
        
        group_layout.addLayout(file_row)
        
        # Import button row - more compact
        import_row = QHBoxLayout()
        import_row.setSpacing(4)
        import_row.setContentsMargins(0, 4, 0, 0)
        
        import_button = QPushButton("Import")
        import_button.setStyleSheet(self.style_manager.get_button_style("primary") + """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
        """)
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setToolTip("Import data from selected file (Alt+I)")
        import_button.setFixedWidth(60)
        import_row.addWidget(import_button)
        
        # Add Clear Data button
        clear_data_button = QPushButton("Clear Data")
        clear_data_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_ERROR};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
            QPushButton:disabled {{
                background-color: #FCA5A5;
                color: #FECACA;
            }}
        """)
        clear_data_button.clicked.connect(self._on_clear_data_clicked)
        clear_data_button.setToolTip("Clear all imported health data")
        clear_data_button.setFixedWidth(80)
        import_row.addWidget(clear_data_button)
        
        import_row.addStretch()
        group_layout.addLayout(import_row)
        
        # Progress section
        progress_row = QVBoxLayout()
        progress_row.setSpacing(12)
        
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
        
        group_layout.addLayout(progress_row)
        
        layout.addLayout(group_layout)
        return section
    
    def _create_filter_section(self):
        """Create the data filtering section."""
        section = QFrame()
        section.setObjectName("filterSection")
        section.setStyleSheet(f"""
            QFrame#filterSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        
        # Add subtle shadow effect
        section.setGraphicsEffect(self.style_manager.create_shadow_effect(blur_radius=8, y_offset=1, opacity=10))
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Section title
        title = QLabel("Filter Data")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 12px;
            }}
        """)
        layout.addWidget(title)
        
        # Date range section - compact
        date_label = QLabel("Date Range")
        date_label.setStyleSheet(f"font-weight: 500; font-size: 12px; color: {self.style_manager.TEXT_SECONDARY};")
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
        
        # Add minimal spacing
        layout.addSpacing(8)
        
        # Devices and metrics sections - stacked vertically for better space usage
        devices_section = self._create_devices_section()
        layout.addWidget(devices_section)
        
        # Metrics section
        metrics_section = self._create_metrics_section()
        layout.addWidget(metrics_section)
        
        # Add minimal spacing
        layout.addSpacing(8)
        
        # Filter presets section
        presets_section = QVBoxLayout()
        presets_section.setSpacing(12)
        
        presets_label = QLabel("Filter Presets")
        presets_label.setStyleSheet(f"font-weight: 500; font-size: 12px; color: {self.style_manager.TEXT_SECONDARY};")
        presets_section.addWidget(presets_label)
        
        presets_row = QHBoxLayout()
        presets_row.setSpacing(4)
        
        self.save_preset_button = QPushButton("Save")
        self.save_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
        """)
        self.save_preset_button.clicked.connect(self._on_save_preset_clicked)
        self.save_preset_button.setEnabled(False)
        self.save_preset_button.setFixedWidth(45)
        presets_row.addWidget(self.save_preset_button)
        
        self.load_preset_button = QPushButton("Load")
        self.load_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
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
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
        """)
        self.reset_settings_button.clicked.connect(self._on_reset_settings_clicked)
        self.reset_settings_button.setToolTip("Reset all application settings")
        self.reset_settings_button.setFixedWidth(45)
        presets_row.addWidget(self.reset_settings_button)
        presets_section.addLayout(presets_row)
        layout.addLayout(presets_section)
        
        # Add minimal spacing
        layout.addSpacing(8)
        
        # Action buttons - compact with reduced height
        button_row = QHBoxLayout()
        button_row.setSpacing(4)
        button_row.addStretch()
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(self.style_manager.get_button_style("secondary") + """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
        """)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.reset_button.setEnabled(False)
        self.reset_button.setFixedWidth(60)
        button_row.addWidget(self.reset_button)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setStyleSheet(self.style_manager.get_button_style("primary") + """
            QPushButton {
                padding: 4px 12px;
                font-size: 12px;
                min-height: 28px;
                max-height: 28px;
            }
        """)
        self.apply_button.clicked.connect(self._on_apply_filters_clicked)
        self.apply_button.setEnabled(False)
        self.apply_button.setFixedWidth(60)
        button_row.addWidget(self.apply_button)
        
        layout.addLayout(button_row)
        
        return section
    
    def _create_devices_section(self):
        """Create the devices selection section."""
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label = QLabel("Source Devices")
        label.setStyleSheet(f"font-weight: 500; font-size: 12px; color: {self.style_manager.TEXT_SECONDARY};")
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
        label.setStyleSheet(f"font-weight: 500; font-size: 12px; color: {self.style_manager.TEXT_SECONDARY};")
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
        # Main container without scroll area
        container = QWidget()
        container.setObjectName("statisticsSection")
        container.setStyleSheet(f"""
            QWidget#statisticsSection {{
                background-color: transparent;
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Data Preview Section
        preview_section = QFrame()
        preview_section.setObjectName("dataPreviewSection")
        preview_section.setStyleSheet(f"""
            QFrame#dataPreviewSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        preview_section.setGraphicsEffect(self.style_manager.create_shadow_effect(blur_radius=8, y_offset=1, opacity=10))
        
        preview_main_layout = QVBoxLayout(preview_section)
        preview_main_layout.setSpacing(12)
        preview_main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Section title
        preview_title = QLabel("Data Preview")
        preview_title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 4px;
            }}
        """)
        preview_main_layout.addWidget(preview_title)
        
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create data preview table with appropriate page size
        self.data_preview_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=10,  # Show 10 rows for better data visibility
                alternating_rows=True,
                grid_style='dotted'
            ),
            wsj_style=True
        )
        
        # Set proper height for data visibility
        self.data_preview_table.setMinimumHeight(250)
        # self.data_preview_table.setMaximumHeight(400)
        
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
                padding: 2px 4px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                color: white;
                padding: 3px 6px;
                border: none;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        
        preview_layout.addWidget(self.data_preview_table)
        preview_main_layout.addLayout(preview_layout)
        layout.addWidget(preview_section)
        
        # Data Statistics Section
        stats_section = QFrame()
        stats_section.setObjectName("dataStatsSection")
        stats_section.setStyleSheet(f"""
            QFrame#dataStatsSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        stats_section.setGraphicsEffect(self.style_manager.create_shadow_effect(blur_radius=8, y_offset=1, opacity=10))
        
        stats_main_layout = QVBoxLayout(stats_section)
        stats_main_layout.setSpacing(12)
        stats_main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Section title
        stats_title = QLabel("Data Statistics")
        stats_title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 4px;
            }}
        """)
        stats_main_layout.addWidget(stats_title)
        
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create custom statistics widget without internal scroll
        self.statistics_widget = self._create_custom_statistics_widget()
        stats_layout.addWidget(self.statistics_widget)
        
        stats_main_layout.addLayout(stats_layout)
        layout.addWidget(stats_section)
        
        return container
    
    def _create_custom_statistics_widget(self):
        """Create custom statistics widget without internal scrolling."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Summary section
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)
        
        # Total Records
        self.stats_total_label = QLabel("Total Records: -")
        self.stats_total_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 8px 16px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 6px;
            }}
        """)
        summary_layout.addWidget(self.stats_total_label)
        
        # Date Range
        self.stats_date_label = QLabel("Date Range: -")
        self.stats_date_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 8px 16px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 6px;
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
        
        # Vertical layout for Record Types and Data Sources
        # Record Types Section
        types_title = QLabel("Record Types")
        types_title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 4px;
            }}
        """)
        layout.addWidget(types_title)
        
        # Record types table - show all records without pagination if possible
        self.record_types_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=20,  # Show reasonable number of records with pagination
                alternating_rows=True,
                resizable_columns=True,
                movable_columns=False,
                selection_mode='row',
                multi_select=False
            ),
            wsj_style=True
        )
        self.record_types_table.setMinimumHeight(350)  # Proper height for data exploration
        # self.record_types_table.setMaximumHeight(500)  # Allow expansion if needed
        
        # Apply compact styling to record types table
        self.record_types_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 11px;
                gridline-color: rgba(139, 115, 85, 0.2);
                background-color: white;
                alternate-background-color: {self.style_manager.TERTIARY_BG};
            }}
            QTableWidget::item {{
                padding: 2px 4px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                color: white;
                padding: 3px 6px;
                border: none;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        
        # Make navigation controls compact
        if hasattr(self.record_types_table, 'pagination_widget'):
            self.record_types_table.pagination_widget.setStyleSheet(f"""
                QPushButton {{
                    padding: 2px 8px;
                    font-size: 10px;
                    max-height: 20px;
                }}
                QLabel {{
                    font-size: 10px;
                }}
                QComboBox, QSpinBox {{
                    font-size: 10px;
                    max-height: 20px;
                    padding: 0px 4px;
                }}
            """)
        
        layout.addWidget(self.record_types_table)
        
        # Add spacing between sections
        layout.addSpacing(20)
        
        # Data Sources Section
        sources_title = QLabel("Data Sources")
        sources_title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 4px;
            }}
        """)
        layout.addWidget(sources_title)
        
        # Data sources table - show all records without pagination if possible
        self.data_sources_table = self.component_factory.create_data_table(
            config=TableConfig(
                page_size=15,  # Show reasonable number of sources
                alternating_rows=True,
                resizable_columns=True,
                movable_columns=False,
                selection_mode='row',
                multi_select=False
            ),
            wsj_style=True
        )
        self.data_sources_table.setMinimumHeight(300)  # Proper height for source list
        # self.data_sources_table.setMaximumHeight(450)  # Allow expansion if needed
        
        # Apply compact styling to data sources table
        self.data_sources_table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 11px;
                gridline-color: rgba(139, 115, 85, 0.2);
                background-color: white;
                alternate-background-color: {self.style_manager.TERTIARY_BG};
            }}
            QTableWidget::item {{
                padding: 2px 4px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                color: white;
                padding: 3px 6px;
                border: none;
                font-weight: 600;
                font-size: 10px;
            }}
        """)
        
        # Make navigation controls compact
        if hasattr(self.data_sources_table, 'pagination_widget'):
            self.data_sources_table.pagination_widget.setStyleSheet(f"""
                QPushButton {{
                    padding: 2px 8px;
                    font-size: 10px;
                    max-height: 20px;
                }}
                QLabel {{
                    font-size: 10px;
                }}
                QComboBox, QSpinBox {{
                    font-size: 10px;
                    max-height: 20px;
                    padding: 0px 4px;
                }}
            """)
        
        layout.addWidget(self.data_sources_table)
        
        # Store the custom widget as statistics_widget for compatibility
        # This ensures that any code expecting statistics_widget gets the actual widget in the UI
        widget.update_statistics = lambda stats: self._update_custom_statistics(stats) if hasattr(self, '_update_custom_statistics') else None
        
        # Also create the original statistics widget but keep it hidden
        self.original_statistics_widget = StatisticsWidget()
        self.original_statistics_widget.setVisible(False)  # Hide original widget
        
        return widget
    
    def _create_summary_cards_section(self):
        """Create summary cards for data overview."""
        section = QFrame()
        section.setObjectName("summaryCardsSection")
        section.setStyleSheet(f"""
            QFrame#summaryCardsSection {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        section.setGraphicsEffect(self.style_manager.create_shadow_effect(blur_radius=8, y_offset=1, opacity=10))
        
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(16, 16, 16, 16)
        section_layout.setSpacing(12)
        
        # Add section title
        title_label = QLabel("Summary Cards")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {self.style_manager.ACCENT_PRIMARY};
                margin-bottom: 4px;
            }}
        """)
        section_layout.addWidget(title_label)
        
        # Cards layout - using grid for better responsive layout
        cards_grid = QHBoxLayout()
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setSpacing(16)  # Good spacing between cards
        
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
        
        # Set consistent card sizes
        for card in [self.total_records_card, self.filtered_records_card, 
                     self.data_source_card, self.filter_status_card]:
            card.setMinimumWidth(200)
            card.setMaximumWidth(300)
        
        cards_grid.addWidget(self.total_records_card)
        cards_grid.addWidget(self.filtered_records_card)
        cards_grid.addWidget(self.data_source_card)
        cards_grid.addWidget(self.filter_status_card)
        cards_grid.addStretch()
        
        section_layout.addLayout(cards_grid)
        
        # Ensure minimum height for the section
        section.setMinimumHeight(160)  # Appropriate height for cards
        
        # Ensure cards are visible
        self.total_records_card.show()
        self.filtered_records_card.show()
        self.data_source_card.show()
        self.filter_status_card.show()
        
        return section
    
    def _create_status_section(self):
        """Create the status display section."""
        section = QFrame()
        section.setObjectName("statusSection")
        section.setStyleSheet(f"""
            QFrame#statusSection {{
                background-color: #D4EDDA;
                border: 1px solid #C3E6CB;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
            }}
        """)
        
        layout = QHBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Status icon
        icon_label = QLabel("ℹ")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: #155724;
                font-weight: bold;
                margin-right: 8px;
            }}
        """)
        layout.addWidget(icon_label)
        
        self.status_label = QLabel("No data loaded")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: #155724;
                font-weight: 500;
            }}
        """)
        self.status_label.setToolTip("Shows the current status of loaded data and applied filters")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
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
            # Automatically start import when file is selected
            self._start_import_with_progress(file_path)
    
    def _on_import_clicked(self):
        """Handle import button click - automatically detect file type."""
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
            
            # Both CSV and XML imports now load from database
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
                try:
                    stats = self.statistics_calculator.calculate_from_dataframe(self.data)
                    self._update_custom_statistics(stats)
                except AttributeError as e:
                    logger.warning(f"Error updating statistics: {e}")
                    # Continue without failing the entire import
            
            # Load last used filters if available
            self._load_last_used_filters()
            
            # Initialize calculators with the loaded data
            self._initialize_calculators()
            
            # Mark data as available
            self.data_available = True
            
            # Emit signal if we have valid data
            if self.data is not None:
                try:
                    self.data_loaded.emit(self.data)
                except Exception as emit_error:
                    logger.error(f"Error emitting data_loaded signal: {emit_error}")
                    # Don't let signal emission errors break the import process
            
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
        """Load data from SQLite database - OPTIMIZED VERSION.
        
        This method now uses SQL aggregation queries instead of loading all records
        into memory. This significantly improves performance for large datasets.
        """
        try:
            logger.info("Loading statistics from SQLite database (optimized)")
            
            # Set database path
            db_path = os.path.join(DATA_DIR, "health_monitor.db")
            self.data_loader.db_path = db_path
            
            # Use cache manager with compute function for record statistics
            cache_key = f"config_tab_record_stats_{db_path}"
            
            # Define compute function for cache miss
            def compute_stats():
                logger.info("Computing fresh record statistics")
                return self.data_loader.get_record_statistics()
            
            # Get from cache or compute
            record_stats = self.cache_manager.get(
                cache_key, 
                compute_fn=compute_stats,
                ttl=3600  # Cache for 1 hour
            )
            
            if record_stats['total_records'] == 0:
                raise ValueError("No data found in database")
            
            row_count = record_stats['total_records']
            
            # Update UI
            self.progress_bar.setVisible(False)
            self.progress_label.setText("Data statistics loaded!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
            
            # Update status
            self._update_status(f"Database contains {row_count:,} records")
            
            # Update summary cards
            self.total_records_card.update_content({'value': f"{row_count:,}"})
            self.filtered_records_card.update_content({'value': f"{row_count:,}"})
            self.data_source_card.update_content({'value': "Database"})
            self.filter_status_card.update_content({'value': "Default"})
            
            # Populate filters (using optimized SQL queries)
            self._populate_filters_optimized()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
            # Update statistics display (using SQL-computed data)
            self._update_statistics_from_sql()
            
            # Load last used filters if available
            self._load_last_used_filters()
            
            # Mark data as available for filtering (but not loaded)
            self.data_available = True
            
            # Get current filtered data or all data for signal emission
            current_data = self.get_filtered_data()
            if current_data is None or (hasattr(current_data, 'empty') and current_data.empty):
                # Load all data if no filtered data exists
                try:
                    current_data = self.data_loader.get_all_records()
                    if current_data is not None:
                        self.data = current_data
                except Exception as e:
                    logger.warning(f"Could not load all records for signal emission: {e}")
                    current_data = None
            
            # Only emit signal if we have valid data
            if current_data is not None:
                try:
                    self.data_loaded.emit(current_data)
                except Exception as emit_error:
                    logger.error(f"Error emitting data_loaded signal: {emit_error}")
                    # Don't let signal emission errors break the load process
            
            logger.info(f"Database statistics loaded: {row_count:,} records")
            
            # Warm the monthly metrics cache in the background
            self._warm_monthly_metrics_cache_async()
            
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
            self.progress_label.setText("Database load failed!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_ERROR};")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load from database: {str(e)}"
            )
    
    def _load_data_for_filtering(self):
        """Load actual data only when filters are applied.
        
        This method is called when the user clicks 'Apply Filters' and we need
        the actual data to filter. This defers the expensive data loading operation.
        """
        if self.data is None:
            logger.info("Loading full data for filtering (first time)")
            try:
                # Show progress
                self.progress_label.setText("Loading data for filtering...")
                self.progress_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
                
                # Load data
                self.data = self.data_loader.get_all_records()
                
                # Hide progress
                self.progress_bar.setVisible(False)
                self.progress_label.setText("Data loaded!")
                
                # Initialize calculators with the loaded data
                self._initialize_calculators()
                
                # Emit data loaded signal if we have valid data
                if self.data is not None:
                    try:
                        self.data_loaded.emit(self.data)
                    except Exception as emit_error:
                        logger.error(f"Error emitting data_loaded signal: {emit_error}")
                        # Don't let signal emission errors break the filtering process
                
                logger.info(f"Loaded {len(self.data)} records for filtering")
                
            except Exception as e:
                logger.error(f"Failed to load data for filtering: {e}")
                self.progress_bar.setVisible(False)
                raise
    
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
        """Handle apply filters button click - OPTIMIZED VERSION.
        
        This method now loads data on-demand when filters are first applied,
        rather than loading all data when the tab is opened.
        """
        # Check if we have data available (either loaded or in database)
        if not self.data_available and self.data is None:
            QMessageBox.warning(self, "No Data", "Please import data before applying filters.")
            return
        
        logger.info("Applying filters")
        
        # Load data if not already loaded (deferred loading)
        if self.data is None and self.data_available:
            try:
                self._load_data_for_filtering()
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load data: {str(e)}")
                return
        
        # Now proceed with filtering as before
        if self.data is None:
            return
        
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
    
    def _on_clear_data_clicked(self):
        """Handle clear data button click."""
        logger.info("Clear data requested")
        
        # Get the main window instance to call the shared method
        main_window = self.window()
        if main_window and hasattr(main_window, '_perform_data_erasure'):
            # Use the same confirmation dialog format as the menu action
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
                # Call the shared method from main window
                main_window._perform_data_erasure()
            else:
                logger.info("User cancelled clear data operation")
        else:
            # Fallback if main window method not available
            logger.error("Main window _perform_data_erasure method not available")
            QMessageBox.critical(
                self,
                "Error",
                "Unable to clear data. Please use File > Erase All Data instead."
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
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QVBoxLayout
        
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
            config = self.filter_config_manager.get_last_used_config()
            
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
            if hasattr(self, 'stats_total_label'):
                self.stats_total_label.setText("Total Records: -")
            if hasattr(self, 'stats_date_label'):
                self.stats_date_label.setText("Date Range: -")
            if hasattr(self, 'record_types_table'):
                self.record_types_table.clear_data()
            if hasattr(self, 'data_sources_table'):
                self.data_sources_table.clear_data()
            return
        
        # Update summary labels
        if hasattr(self, 'stats_total_label'):
            self.stats_total_label.setText(f"Total Records: {stats.total_records:,}")
        
        if hasattr(self, 'stats_date_label'):
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
                self._apply_compact_table_styling(self.record_types_table)
        
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
                self._apply_compact_table_styling(self.data_sources_table)
        
        # Also update original statistics widget for compatibility
        if hasattr(self, 'original_statistics_widget') and hasattr(self.original_statistics_widget, 'update_statistics'):
            self.original_statistics_widget.update_statistics(stats)
    
    def _apply_compact_table_styling(self, table):
        """Apply compact styling to table navigation controls."""
        # Apply compact styling to pagination widget if it exists
        if hasattr(table, 'pagination_widget') and table.pagination_widget:
            table.pagination_widget.setStyleSheet(f"""
                QPushButton {{
                    padding: 2px 8px;
                    font-size: 10px;
                    max-height: 20px;
                }}
                QLabel {{
                    font-size: 10px;
                }}
                QComboBox, QSpinBox {{
                    font-size: 10px;
                    max-height: 20px;
                    padding: 0px 4px;
                }}
            """)
    
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
            preview_data = sample_data[preview_columns].copy()
            
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
                self._apply_compact_table_styling(self.data_preview_table)
    
    def _update_status(self, message):
        """Update the status label with a message."""
        if hasattr(self, 'status_label') and hasattr(self, 'status_section'):
            self.status_label.setText(message)
            # Show status section when there's a message
            if message and message.strip() and message != "No data loaded":
                self.status_section.setVisible(True)
            else:
                self.status_section.setVisible(False)
    
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
            from ..analytics import (
                DailyMetricsCalculator,
                MonthlyMetricsCalculator,
                WeeklyMetricsCalculator,
            )

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
    
    def refresh_display(self):
        """Refresh the display with current data."""
        if self.data is None or self.data.empty:
            return
            
        logger.info("Refreshing configuration tab display")
        
        # Update summary cards
        row_count = len(self.data)
        filtered_count = len(self.filtered_data) if self.filtered_data is not None else row_count
        
        self.total_records_card.update_content({'value': f"{row_count:,}"})
        self.filtered_records_card.update_content({'value': f"{filtered_count:,}"})
        
        # Update data source
        if hasattr(self.data_loader, 'db_path') and self.data_loader.db_path:
            self.data_source_card.update_content({'value': "Database"})
        else:
            self.data_source_card.update_content({'value': "CSV File"})
        
        # Update filter status
        if self.filtered_data is not None and len(self.filtered_data) != len(self.data):
            percentage = f"{filtered_count/row_count*100:.1f}%"
            self.filter_status_card.update_content({'value': f"Active ({percentage})"})
        else:
            self.filter_status_card.update_content({'value': "Default"})
        
        # Update data preview
        self._update_data_preview()
        
        # Calculate and display statistics
        data_to_analyze = self.filtered_data if self.filtered_data is not None else self.data
        try:
            stats = self.statistics_calculator.calculate_from_dataframe(data_to_analyze)
            self._update_custom_statistics(stats)
        except Exception as e:
            logger.warning(f"Error updating statistics: {e}")
        
        # Update status
        if self.filtered_data is not None:
            self._update_status(
                f"Showing {filtered_count:,} of {row_count:,} records "
                f"({filtered_count/row_count*100:.1f}%)"
            )
        else:
            self._update_status(f"Loaded {row_count:,} records")
    
    def _check_existing_data(self):
        """Check if data already exists in the database on startup."""
        try:
            # Check if database exists
            db_path = os.path.join(DATA_DIR, "health_monitor.db")
            if os.path.exists(db_path):
                logger.info("Found existing database, attempting to load data")
                # Set the file path input to indicate database
                self.file_path_input.setText(db_path)
                # Load data from database
                self._load_from_sqlite()
        except Exception as e:
            logger.warning(f"Could not load existing data on startup: {e}")
    
    def _populate_filters_optimized(self):
        """Populate filter options using SQL queries for better performance."""
        try:
            # Use cache manager for filter options
            cache_key = f"config_tab_filter_options_{self.data_loader.db_path}"
            
            # Define compute function for filter options
            def compute_filter_options():
                logger.info("Computing filter options from database")
                return self.data_loader.get_filter_options()
            
            # Get from cache or compute
            filter_options = self.cache_manager.get(
                cache_key,
                compute_fn=compute_filter_options,
                ttl=3600  # Cache for 1 hour
            )
            
            # Get unique devices and metrics from optimized method
            unique_devices = filter_options.get('sources', [])
            unique_metrics = filter_options.get('types', [])
            
            # Clear and repopulate device dropdown
            self.device_dropdown.clear()
            for device in unique_devices:
                self.device_dropdown.addItem(str(device), checked=True)  # Default to all selected
            
            # Clear and repopulate metric dropdown
            self.metric_dropdown.clear()
            for metric in unique_metrics:
                self.metric_dropdown.addItem(str(metric), checked=True)  # Default to all selected
            
            logger.info(f"Populated filters: {len(unique_devices)} devices, {len(unique_metrics)} metrics")
            
        except Exception as e:
            logger.error(f"Error populating filters: {e}")
            # Fall back to empty dropdowns
            self.device_dropdown.clear()
            self.metric_dropdown.clear()
    
    def _update_statistics_from_sql(self):
        """Update statistics display using SQL-computed data with caching."""
        try:
            db_path = self.data_loader.db_path
            
            # Try to get cached data
            type_counts_key = f"config_tab_type_counts_{db_path}"
            source_counts_key = f"config_tab_source_counts_{db_path}"
            
            # Get type counts (with caching)
            type_counts_df = self.cache_manager.get(
                type_counts_key,
                compute_fn=lambda: self.data_loader.get_type_counts(),
                ttl=3600
            )
            
            # Get source counts (with caching)
            source_counts_df = self.cache_manager.get(
                source_counts_key,
                compute_fn=lambda: self.data_loader.get_source_counts(),
                ttl=3600
            )
            
            # Get summary stats (already cached in _load_from_sqlite)
            stats_summary_key = f"config_tab_stats_{db_path}"
            stats_summary = self.cache_manager.get(
                stats_summary_key,
                compute_fn=lambda: self.data_loader.get_statistics_summary(),
                ttl=3600
            )
            
            # Update the custom statistics display
            if hasattr(self, 'stats_total_label'):
                self.stats_total_label.setText(f"Total Records: {stats_summary['total_records']:,}")
            
            if hasattr(self, 'stats_date_label'):
                date_range = stats_summary['date_range']
                if date_range[0] and date_range[1]:
                    try:
                        # Parse dates
                        start_date = pd.to_datetime(date_range[0])
                        end_date = pd.to_datetime(date_range[1])
                        date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                        self.stats_date_label.setText(f"Date Range: {date_str}")
                    except:
                        self.stats_date_label.setText("Date Range: Invalid dates")
                else:
                    self.stats_date_label.setText("Date Range: -")
            
            # Update record types table
            if hasattr(self, 'record_types_table') and not type_counts_df.empty:
                types_data = []
                for _, row in type_counts_df.iterrows():
                    types_data.append({
                        'Type': row['type'],
                        'Count': f"{row['count']:,}",
                        'Percentage': f"{row['percentage']:.1f}%"
                    })
                if types_data:
                    types_df = pd.DataFrame(types_data)
                    self.record_types_table.load_data(types_df)
                    self._apply_compact_table_styling(self.record_types_table)
            
            # Update data sources table
            if hasattr(self, 'data_sources_table') and not source_counts_df.empty:
                sources_data = []
                for _, row in source_counts_df.iterrows():
                    sources_data.append({
                        'Source': row['sourceName'],
                        'Count': f"{row['count']:,}",
                        'Percentage': f"{row['percentage']:.1f}%"
                    })
                if sources_data:
                    sources_df = pd.DataFrame(sources_data)
                    self.data_sources_table.load_data(sources_df)
                    self._apply_compact_table_styling(self.data_sources_table)
            
            logger.info("Statistics updated from SQL queries")
            
        except Exception as e:
            logger.error(f"Error updating statistics from SQL: {e}")
    
    def _check_database_availability(self):
        """Check if database exists and show statistics without loading all data."""
        try:
            # Check if database exists
            db_path = os.path.join(DATA_DIR, "health_monitor.db")
            if os.path.exists(db_path):
                logger.info("Found existing database, loading statistics only")
                
                # Create performance optimization indexes if needed
                try:
                    db_manager.create_indexes()
                except Exception as idx_err:
                    logger.warning(f"Could not create indexes: {idx_err}")
                
                # Set the file path input to indicate database
                self.file_path_input.setText(db_path)
                # Load statistics from database (not full data)
                self._load_from_sqlite()
        except Exception as e:
            logger.warning(f"Could not check database availability: {e}")
    
    def _warm_monthly_metrics_cache_async(self):
        """Warm the monthly metrics cache in the background after data import.
        
        This method runs the cache warming process asynchronously to avoid blocking
        the UI while pre-computing monthly statistics for all available metrics.
        """
        try:
            # Import here to avoid circular dependencies
            from concurrent.futures import ThreadPoolExecutor

            from ..analytics.cache_background_refresh import (
                identify_months_for_cache_population,
                warm_monthly_metrics_cache,
            )
            from ..analytics.cached_calculators import create_cached_monthly_calculator
            from ..database import DatabaseManager
            
            def warm_cache():
                """Execute cache warming in background thread."""
                try:
                    logger.info("Starting monthly metrics cache warming in background")
                    
                    # Create instances
                    db_manager = DatabaseManager()
                    cached_calculator = create_cached_monthly_calculator()
                    
                    # First, identify months to cache (last 12 months by default)
                    months_data = identify_months_for_cache_population(db_manager, months_back=12)
                    
                    if not months_data:
                        logger.info("No months identified for cache warming")
                        return
                    
                    # Log what we're about to cache
                    unique_types = set(m['type'] for m in months_data)
                    unique_months = set((m['year'], m['month']) for m in months_data)
                    logger.info(f"Warming cache for {len(unique_types)} metric types "
                              f"across {len(unique_months)} months")
                    
                    # Perform the cache warming
                    results = warm_monthly_metrics_cache(cached_calculator, db_manager, months_back=12)
                    
                    # Log results
                    success_count = sum(results.values())
                    logger.info(f"Monthly cache warming completed: "
                              f"{success_count}/{len(results)} entries cached successfully")
                    
                except Exception as e:
                    logger.error(f"Error during cache warming: {e}", exc_info=True)
            
            # Execute in background thread to avoid blocking UI
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cache-warmer")
            executor.submit(warm_cache)
            # Don't wait for completion - let it run in background
            executor.shutdown(wait=False)
            
            logger.info("Monthly cache warming task submitted to background thread")
            
        except Exception as e:
            # Don't fail the import if cache warming fails
            logger.warning(f"Could not start cache warming: {e}")