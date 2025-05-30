"""Modern configuration tab implementation for data import and filtering."""

import json
import os
import time

import pandas as pd
from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
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


class ModernConfigurationTab(QWidget):
    """Modern configuration tab with updated styling and improved layout."""
    
    # Signals
    data_loaded = pyqtSignal(object)
    filters_applied = pyqtSignal(dict)
    
    def __init__(self):
        """Initialize the configuration tab."""
        super().__init__()
        logger.info("Initializing Modern Configuration tab")
        
        # Initialize components
        self.style_manager = StyleManager()
        self.component_factory = ComponentFactory()
        self.data_loader = DataLoader()
        self.filter_config_manager = FilterConfigManager()
        self.statistics_calculator = StatisticsCalculator()
        
        # Initialize metric calculators as None
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
        
        logger.info("Modern Configuration tab initialized")
    
    def _create_ui(self):
        """Create the modern configuration tab UI."""
        # Main layout with modern spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Apply background color
        self.setStyleSheet(f"background-color: {self.style_manager.SECONDARY_BG};")
        
        # Title
        title = QLabel("Configuration")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {self.style_manager.TEXT_PRIMARY};
                margin-bottom: 8px;
            }}
        """)
        main_layout.addWidget(title)
        
        # Create responsive two-column layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # Left column - Import and Filter
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        left_column.addWidget(self._create_modern_import_section())
        left_column.addWidget(self._create_modern_filter_section())
        left_column.addStretch()
        
        # Right column - Statistics and Summary
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        right_column.addWidget(self._create_modern_summary_section())
        right_column.addWidget(self._create_modern_statistics_section())
        right_column.addStretch()
        
        content_layout.addLayout(left_column, 1)
        content_layout.addLayout(right_column, 1)
        
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self._create_modern_status_section())
        main_layout.addStretch()
    
    def _create_modern_import_section(self):
        """Create modern data import section."""
        section = QFrame()
        section.setObjectName("importSection")
        section.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        
        # Add shadow effect
        section.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Import Data")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(title)
        
        # File selection
        file_layout = QVBoxLayout()
        file_layout.setSpacing(8)
        
        file_label = QLabel("Data File")
        file_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        file_layout.addWidget(file_label)
        
        # File input row
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select Apple Health export file...")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            QLineEdit:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
        """)
        file_row.addWidget(self.file_path_input)
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.PRIMARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        browse_button.clicked.connect(self._on_browse_clicked)
        browse_button.setToolTip("Browse for Apple Health export file")
        browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        file_row.addWidget(browse_button)
        
        file_layout.addLayout(file_row)
        layout.addLayout(file_layout)
        
        # Import button
        import_button = QPushButton("Import Data")
        import_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
            QPushButton:pressed {{
                background-color: #1E40AF;
            }}
            QPushButton:disabled {{
                background-color: {self.style_manager.TEXT_MUTED};
            }}
        """)
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setToolTip("Import data from selected file")
        import_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(import_button)
        
        # Progress section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel("Ready to import data")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                color: {self.style_manager.TEXT_SECONDARY};
                font-size: 12px;
            }}
        """)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(self.style_manager.get_modern_progress_bar_style())
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        return section
    
    def _create_modern_filter_section(self):
        """Create modern data filtering section."""
        section = QFrame()
        section.setObjectName("filterSection")
        section.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        
        # Add shadow effect
        section.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Filter Data")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(title)
        
        # Date range
        date_layout = QVBoxLayout()
        date_layout.setSpacing(8)
        
        date_label = QLabel("Date Range")
        date_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        date_layout.addWidget(date_label)
        
        date_row = QHBoxLayout()
        date_row.setSpacing(8)
        
        self.start_date_edit = EnhancedDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setStyleSheet(self._get_modern_date_edit_style())
        date_row.addWidget(self.start_date_edit)
        
        date_separator = QLabel("→")
        date_separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_separator.setStyleSheet(f"color: {self.style_manager.TEXT_MUTED};")
        date_row.addWidget(date_separator)
        
        self.end_date_edit = EnhancedDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setStyleSheet(self._get_modern_date_edit_style())
        date_row.addWidget(self.end_date_edit)
        
        date_layout.addLayout(date_row)
        layout.addLayout(date_layout)
        
        # Device filter
        device_layout = QVBoxLayout()
        device_layout.setSpacing(8)
        
        device_label = QLabel("Devices")
        device_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        device_layout.addWidget(device_label)
        
        self.device_dropdown = CheckableComboBox()
        self.device_dropdown.setPlaceholderText("All Devices")
        self.device_dropdown.setStyleSheet(self._get_modern_combo_style())
        device_layout.addWidget(self.device_dropdown)
        
        layout.addLayout(device_layout)
        
        # Metric filter
        metric_layout = QVBoxLayout()
        metric_layout.setSpacing(8)
        
        metric_label = QLabel("Metrics")
        metric_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        metric_layout.addWidget(metric_label)
        
        self.metric_dropdown = CheckableComboBox()
        self.metric_dropdown.setPlaceholderText("All Metrics")
        self.metric_dropdown.setStyleSheet(self._get_modern_combo_style())
        metric_layout.addWidget(self.metric_dropdown)
        
        layout.addLayout(metric_layout)
        
        # Filter buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.apply_button = QPushButton("Apply Filters")
        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SUCCESS};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #0E9F6E;
            }}
            QPushButton:pressed {{
                background-color: #057A55;
            }}
            QPushButton:disabled {{
                background-color: {self.style_manager.TEXT_MUTED};
            }}
        """)
        self.apply_button.clicked.connect(self._on_apply_filters)
        self.apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
                border-color: {self.style_manager.TEXT_SECONDARY};
            }}
            QPushButton:pressed {{
                background-color: {self.style_manager.ACCENT_LIGHT};
            }}
        """)
        self.reset_button.clicked.connect(self._on_reset_filters)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return section
    
    def _create_modern_summary_section(self):
        """Create modern summary cards section."""
        section = QFrame()
        section.setObjectName("summarySection")
        section.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add section title
        title_label = QLabel("Summary Cards")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                padding: 8px 0px 4px 0px;
            }}
        """)
        layout.addWidget(title_label)
        
        # Create frame for cards
        cards_frame = QFrame()
        cards_frame.setObjectName("cardsFrame")
        cards_frame.setStyleSheet("background-color: transparent;")
        
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 10, 0, 10)
        cards_layout.setSpacing(16)
        
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
        
        # Add cards to layout
        cards_layout.addWidget(self.total_records_card)
        cards_layout.addWidget(self.filtered_records_card)
        cards_layout.addWidget(self.data_source_card)
        cards_layout.addWidget(self.filter_status_card)
        cards_layout.addStretch()
        
        layout.addWidget(cards_frame)
        
        # Ensure minimum height for the section
        section.setMinimumHeight(180)
        
        return section
    
    def _create_modern_statistics_section(self):
        """Create modern statistics display section."""
        section = QFrame()
        section.setObjectName("statsSection")
        section.setStyleSheet(self.style_manager.get_modern_card_style(padding=20))
        
        # Add shadow effect
        section.setGraphicsEffect(self.style_manager.create_shadow_effect())
        
        layout = QVBoxLayout(section)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel("Data Statistics")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(title)
        
        # Placeholder for statistics
        self.statistics_widget = QLabel("Statistics will appear here after data import")
        self.statistics_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statistics_widget.setStyleSheet(f"""
            QLabel {{
                color: {self.style_manager.TEXT_MUTED};
                font-size: 13px;
                padding: 20px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.statistics_widget)
        
        return section
    
    def _create_modern_status_section(self):
        """Create modern status bar section."""
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-top: 1px solid {self.style_manager.ACCENT_LIGHT};
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(16, 8, 16, 8)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.style_manager.TEXT_SECONDARY};
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Filter preset buttons
        self.save_preset_button = QPushButton("Save Preset")
        self.save_preset_button.setStyleSheet(self._get_modern_ghost_button_style())
        self.save_preset_button.clicked.connect(self._on_save_preset)
        self.save_preset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.save_preset_button)
        
        self.load_preset_button = QPushButton("Load Preset")
        self.load_preset_button.setStyleSheet(self._get_modern_ghost_button_style())
        self.load_preset_button.clicked.connect(self._on_load_preset)
        self.load_preset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.load_preset_button)
        
        return status_frame
    
    def _get_modern_date_edit_style(self):
        """Get modern date edit style."""
        return f"""
            QDateEdit {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            QDateEdit:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QDateEdit:focus {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
                border-width: 2px;
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.style_manager.TEXT_SECONDARY};
                margin-right: 8px;
            }}
        """
    
    def _get_modern_combo_style(self):
        """Get modern combo box style."""
        return f"""
            QComboBox {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid {self.style_manager.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: {self.style_manager.TEXT_PRIMARY};
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QComboBox:focus {{
                border-color: {self.style_manager.ACCENT_SECONDARY};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.style_manager.TEXT_SECONDARY};
                margin-right: 8px;
            }}
        """
    
    def _get_modern_ghost_button_style(self):
        """Get modern ghost button style."""
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                color: {self.style_manager.ACCENT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: rgba(37, 99, 235, 0.1);
                border-radius: 6px;
            }}
            QPushButton:pressed {{
                background-color: rgba(37, 99, 235, 0.2);
            }}
        """
    
    def _setup_keyboard_navigation(self):
        """Set up keyboard navigation and shortcuts."""
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
    
    # Placeholder methods for functionality
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
    
    def _start_import_with_progress(self, file_path):
        """Start import with progress dialog."""
        # Create and show import progress dialog
        from .import_progress_dialog import ImportProgressDialog
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
            
            # Update summary cards if they exist
            if hasattr(self, 'total_records_card'):
                self.total_records_card.update_content({'value': f"{row_count:,}"})
            if hasattr(self, 'filtered_records_card'):
                self.filtered_records_card.update_content({'value': f"{row_count:,}"})
            if hasattr(self, 'data_source_card'):
                self.data_source_card.update_content({'value': "CSV File"})
            if hasattr(self, 'filter_status_card'):
                self.filter_status_card.update_content({'value': "Default"})
            
            # Populate filters
            self._populate_filters()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
            # Emit data loaded signal
            self.data_loaded.emit(self.data)
            
            logger.info(f"Successfully loaded {row_count:,} records")
            
        except Exception as e:
            logger.error(f"Error in import completion handler: {e}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error processing imported data: {str(e)}"
            )
    
    def _on_import_cancelled(self):
        """Handle import cancellation."""
        logger.info("Import cancelled by user")
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Import cancelled")
        self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_WARNING};")
    
    def _load_from_sqlite(self):
        """Load data from SQLite database."""
        try:
            logger.info("Loading data from SQLite database")
            # Set database path
            db_path = os.path.join(DATA_DIR, "health_data.db")
            self.data_loader.db_path = db_path
            
            # Load data using the correct method
            self.data = self.data_loader.get_all_records()
            
            if self.data is not None and not self.data.empty:
                row_count = len(self.data)
                self._update_status(f"Loaded {row_count:,} records from database")
                
                # Update summary cards if they exist
                if hasattr(self, 'total_records_card'):
                    self.total_records_card.update_content({'value': f"{row_count:,}"})
                if hasattr(self, 'data_source_card'):
                    self.data_source_card.update_content({'value': "Database"})
                
                # Populate filters
                self._populate_filters()
                
                # Enable filter controls
                self._enable_filter_controls(True)
                
                # Emit data loaded signal
                self.data_loaded.emit(self.data)
                
                logger.info(f"Successfully loaded {row_count:,} records from database")
            else:
                logger.warning("No data found in database")
                self._update_status("No data found in database")
                
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Error loading data from database: {str(e)}"
            )
    
    def _populate_filters(self):
        """Populate filter dropdowns with available options."""
        if self.data is None:
            return
            
        try:
            # Populate device dropdown
            if self.device_dropdown and 'device' in self.data.columns:
                devices = self.data['device'].unique().tolist()
                self.device_dropdown.clear()
                self.device_dropdown.addItems(sorted(devices))
            
            # Populate metric dropdown
            if self.metric_dropdown and 'type' in self.data.columns:
                metrics = self.data['type'].unique().tolist()
                self.metric_dropdown.clear()
                self.metric_dropdown.addItems(sorted(metrics))
                
        except Exception as e:
            logger.error(f"Error populating filters: {e}")
    
    def _enable_filter_controls(self, enabled: bool):
        """Enable or disable filter controls."""
        if self.start_date_edit:
            self.start_date_edit.setEnabled(enabled)
        if self.end_date_edit:
            self.end_date_edit.setEnabled(enabled)
        if self.device_dropdown:
            self.device_dropdown.setEnabled(enabled)
        if self.metric_dropdown:
            self.metric_dropdown.setEnabled(enabled)
        if self.apply_button:
            self.apply_button.setEnabled(enabled)
    
    def _update_status(self, message: str):
        """Update status label if it exists."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(message)
    
    def get_filtered_data(self):
        """Get the current filtered data."""
        return self.filtered_data if self.filtered_data is not None else self.data