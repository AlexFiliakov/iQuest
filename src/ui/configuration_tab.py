"""Configuration tab implementation for data import and filtering."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QDateEdit, QCheckBox, QScrollArea,
    QProgressBar, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeyEvent
import pandas as pd
import json
import os
import time

from utils.logging_config import get_logger
from data_loader import DataLoader, convert_xml_to_sqlite
from database import db_manager
from data_filter_engine import DataFilterEngine, FilterCriteria
from .style_manager import StyleManager
from .settings_manager import SettingsManager
from .multi_select_combo import CheckableComboBox
from .enhanced_date_edit import EnhancedDateEdit
from .import_progress_dialog import ImportProgressDialog
from config import DATA_DIR

logger = get_logger(__name__)


class ConfigurationTab(QWidget):
    """Configuration tab for importing data and setting filters."""
    
    # Signals
    data_loaded = pyqtSignal(object)  # Emitted when data is successfully loaded
    filters_applied = pyqtSignal(dict)  # Emitted when filters are applied
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing Configuration tab")
        
        # Initialize components
        self.style_manager = StyleManager()
        self.data_loader = DataLoader()
        self.data = None
        self.filtered_data = None
        
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
        
        # Presets file path
        self.presets_file = os.path.join(os.path.dirname(__file__), '..', '..', 'filter_presets.json')
        
        # Create the UI
        self._create_ui()
        
        # Set up keyboard navigation
        self._setup_keyboard_navigation()
        
        logger.info("Configuration tab initialized")
    
    def _create_ui(self):
        """Create the configuration tab UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Configuration Settings")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #5D4E37;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title)
        
        # Create sections
        main_layout.addWidget(self._create_import_section())
        main_layout.addWidget(self._create_filter_section())
        main_layout.addWidget(self._create_status_section())
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
    
    def _create_import_section(self):
        """Create the data import section."""
        group = QGroupBox("Import Data")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                padding-top: 32px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        
        # File selection row
        file_row = QHBoxLayout()
        file_row.setSpacing(12)
        
        file_label = QLabel("Data File:")
        file_label.setStyleSheet("font-weight: 500;")
        file_row.addWidget(file_label)
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select Apple Health export file (CSV or XML)...")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet(self.style_manager.get_input_style())
        file_row.addWidget(self.file_path_input, 1)
        
        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        browse_button.clicked.connect(self._on_browse_clicked)
        browse_button.setToolTip("Browse for Apple Health export file on your computer (Alt+B)")
        file_row.addWidget(browse_button)
        
        import_button = QPushButton("Import")
        import_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setToolTip("Import the selected CSV file into the application (Alt+I)")
        file_row.addWidget(import_button)
        
        # Add XML import button
        import_xml_button = QPushButton("Import XML")
        import_xml_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        import_xml_button.clicked.connect(self._on_import_xml_clicked)
        import_xml_button.setToolTip("Import XML export file and convert to database format")
        file_row.addWidget(import_xml_button)
        
        layout.addLayout(file_row)
        
        # Progress section
        progress_row = QVBoxLayout()
        progress_row.setSpacing(8)
        
        self.progress_label = QLabel("Ready to import data")
        self.progress_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        progress_row.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
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
                font-size: 18px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
                padding-top: 32px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: {self.style_manager.ACCENT_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(20)
        
        # Date range section
        date_section = QVBoxLayout()
        date_section.setSpacing(12)
        
        date_label = QLabel("Date Range")
        date_label.setStyleSheet("font-weight: 600; font-size: 16px;")
        date_section.addWidget(date_label)
        
        date_row = QHBoxLayout()
        date_row.setSpacing(16)
        
        start_label = QLabel("From:")
        date_row.addWidget(start_label)
        
        self.start_date_edit = EnhancedDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.start_date_edit.setAccessibleName("Start date filter")
        self.start_date_edit.setAccessibleDescription("Filter data from this date onwards")
        date_row.addWidget(self.start_date_edit)
        
        end_label = QLabel("To:")
        date_row.addWidget(end_label)
        
        self.end_date_edit = EnhancedDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setStyleSheet(self.style_manager.get_input_style())
        self.end_date_edit.setAccessibleName("End date filter")
        self.end_date_edit.setAccessibleDescription("Filter data up to this date")
        date_row.addWidget(self.end_date_edit)
        
        date_row.addStretch()
        date_section.addLayout(date_row)
        layout.addLayout(date_section)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: rgba(139, 115, 85, 0.2);")
        layout.addWidget(separator1)
        
        # Two columns for devices and metrics
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(24)
        
        # Devices column
        devices_section = self._create_devices_section()
        columns_layout.addWidget(devices_section, 1)
        
        # Metrics column
        metrics_section = self._create_metrics_section()
        columns_layout.addWidget(metrics_section, 1)
        
        layout.addLayout(columns_layout)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: rgba(139, 115, 85, 0.2);")
        layout.addWidget(separator2)
        
        # Filter presets section
        presets_section = QVBoxLayout()
        presets_section.setSpacing(12)
        
        presets_label = QLabel("Filter Presets")
        presets_label.setStyleSheet("font-weight: 600; font-size: 16px;")
        presets_section.addWidget(presets_label)
        
        presets_row = QHBoxLayout()
        presets_row.setSpacing(12)
        
        self.save_preset_button = QPushButton("Save Current")
        self.save_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.save_preset_button.clicked.connect(self._on_save_preset_clicked)
        self.save_preset_button.setEnabled(False)
        presets_row.addWidget(self.save_preset_button)
        
        self.load_preset_button = QPushButton("Load Preset")
        self.load_preset_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.load_preset_button.clicked.connect(self._on_load_preset_clicked)
        self.load_preset_button.setEnabled(False)
        presets_row.addWidget(self.load_preset_button)
        
        presets_row.addStretch()
        
        # Add reset app settings button
        self.reset_settings_button = QPushButton("Reset App Settings")
        self.reset_settings_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.reset_settings_button.clicked.connect(self._on_reset_settings_clicked)
        self.reset_settings_button.setToolTip("Reset all application settings including window position")
        presets_row.addWidget(self.reset_settings_button)
        presets_section.addLayout(presets_row)
        layout.addLayout(presets_section)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet("background-color: rgba(139, 115, 85, 0.2);")
        layout.addWidget(separator3)
        
        # Action buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch()
        
        self.reset_button = QPushButton("Reset Filters")
        self.reset_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.reset_button.setEnabled(False)
        button_row.addWidget(self.reset_button)
        
        self.apply_button = QPushButton("Apply Filters")
        self.apply_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        self.apply_button.clicked.connect(self._on_apply_filters_clicked)
        self.apply_button.setEnabled(False)
        button_row.addWidget(self.apply_button)
        
        layout.addLayout(button_row)
        
        return group
    
    def _create_devices_section(self):
        """Create the devices selection section."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        label = QLabel("Source Devices")
        label.setStyleSheet("font-weight: 600; font-size: 16px;")
        layout.addWidget(label)
        
        # Multi-select dropdown for devices
        self.device_dropdown = CheckableComboBox()
        self.device_dropdown.setPlaceholderText("Select devices...")
        self.device_dropdown.setEnabled(False)
        self.device_dropdown.setStyleSheet(self.style_manager.get_input_style() + """
            QComboBox {
                min-height: 36px;
            }
            QComboBox QAbstractItemView {
                max-height: 200px;
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
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        label = QLabel("Metric Types")
        label.setStyleSheet("font-weight: 600; font-size: 16px;")
        layout.addWidget(label)
        
        # Multi-select dropdown for metrics
        self.metric_dropdown = CheckableComboBox()
        self.metric_dropdown.setPlaceholderText("Select metrics...")
        self.metric_dropdown.setEnabled(False)
        self.metric_dropdown.setStyleSheet(self.style_manager.get_input_style() + """
            QComboBox {
                min-height: 36px;
            }
            QComboBox QAbstractItemView {
                max-height: 200px;
            }
        """)
        
        # Add placeholder items (will be replaced when data is loaded)
        default_metrics = ["Heart Rate", "Steps", "Sleep", "Workouts"]
        for metric in default_metrics:
            self.metric_dropdown.addItem(metric, checked=False)
        
        layout.addWidget(self.metric_dropdown)
        
        return section
    
    def _create_status_section(self):
        """Create the status display section."""
        section = QWidget()
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
            
            # Populate filters
            self._populate_filters()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
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
    
    def _update_status(self, message):
        """Update the status label."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.style_manager.TERTIARY_BG};
                border: 1px solid {self.style_manager.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                color: {self.style_manager.TEXT_PRIMARY};
                font-weight: 500;
            }}
        """)
    
    def get_filtered_data(self):
        """Get the current filtered data."""
        return self.filtered_data if self.filtered_data is not None else self.data
    
    def get_current_filters(self):
        """Get the current filter settings."""
        return {
            'start_date': self.start_date_edit.date().toPyDate(),
            'end_date': self.end_date_edit.date().toPyDate(),
            'devices': self.device_dropdown.checkedTexts(),
            'metrics': self.metric_dropdown.checkedTexts()
        }
    
    def _on_save_preset_clicked(self):
        """Handle save preset button click."""
        logger.info("Saving filter preset")
        
        # Get preset name from user
        from PyQt6.QtWidgets import QInputDialog
        preset_name, ok = QInputDialog.getText(
            self,
            "Save Filter Preset",
            "Enter a name for this preset:"
        )
        
        if ok and preset_name:
            try:
                # Load existing presets
                presets = {}
                if os.path.exists(self.presets_file):
                    with open(self.presets_file, 'r') as f:
                        presets = json.load(f)
                
                # Add current filters
                filters = self.get_current_filters()
                # Convert dates to strings for JSON serialization
                filters['start_date'] = filters['start_date'].isoformat()
                filters['end_date'] = filters['end_date'].isoformat()
                
                presets[preset_name] = filters
                
                # Save to file
                os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
                with open(self.presets_file, 'w') as f:
                    json.dump(presets, f, indent=2)
                
                QMessageBox.information(
                    self,
                    "Preset Saved",
                    f"Filter preset '{preset_name}' has been saved."
                )
                logger.info(f"Saved preset: {preset_name}")
                
            except Exception as e:
                logger.error(f"Failed to save preset: {e}")
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save preset: {str(e)}"
                )
    
    def _on_load_preset_clicked(self):
        """Handle load preset button click."""
        logger.info("Loading filter preset")
        
        try:
            # Check if presets file exists
            if not os.path.exists(self.presets_file):
                QMessageBox.information(
                    self,
                    "No Presets",
                    "No filter presets have been saved yet."
                )
                return
            
            # Load presets
            with open(self.presets_file, 'r') as f:
                presets = json.load(f)
            
            if not presets:
                QMessageBox.information(
                    self,
                    "No Presets",
                    "No filter presets have been saved yet."
                )
                return
            
            # Let user choose preset
            from PyQt6.QtWidgets import QInputDialog
            preset_name, ok = QInputDialog.getItem(
                self,
                "Load Filter Preset",
                "Select a preset to load:",
                list(presets.keys()),
                0,
                False
            )
            
            if ok and preset_name:
                preset = presets[preset_name]
                
                # Apply preset values
                from datetime import datetime
                self.start_date_edit.setDate(QDate.fromString(preset['start_date'], Qt.DateFormat.ISODate))
                self.end_date_edit.setDate(QDate.fromString(preset['end_date'], Qt.DateFormat.ISODate))
                
                # Set device selection
                self.device_dropdown.setCheckedItems(preset['devices'])
                
                # Set metric selection
                self.metric_dropdown.setCheckedItems(preset['metrics'])
                
                # Apply the loaded filters
                self._on_apply_filters_clicked()
                
                logger.info(f"Loaded preset: {preset_name}")
                
        except Exception as e:
            logger.error(f"Failed to load preset: {e}")
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load preset: {str(e)}"
            )
    
    def _on_import_xml_clicked(self):
        """Handle XML import button click."""
        file_path = self.file_path_input.text()
        if not file_path:
            # Open file dialog for XML
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Apple Health Export XML",
                "",
                "XML Files (*.xml);;All Files (*)"
            )
            if not file_path:
                return
            self.file_path_input.setText(file_path)
        
        if not file_path.lower().endswith('.xml'):
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select an XML file for XML import."
            )
            return
        
        logger.info(f"Starting XML import of: {file_path}")
        self._start_import_with_progress(file_path)
    
    
    def _load_from_sqlite(self):
        """Load data from SQLite database."""
        try:
            # Initialize database if needed
            db_manager.initialize_database()
            
            # Load data using DataLoader's SQLite functions
            from database import DB_FILE_NAME
            self.data_loader.db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
            
            # Get all records from SQLite
            self.data = self.data_loader.get_all_records()
            
            # Update UI
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            self.progress_label.setText("Data loaded from database successfully!")
            self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
            
            # Update status
            row_count = len(self.data) if self.data is not None else 0
            self._update_status(f"Loaded {row_count:,} records from database")
            
            # Populate filters
            self._populate_filters()
            
            # Enable filter controls
            self._enable_filter_controls(True)
            
            # Emit signal
            self.data_loaded.emit(self.data)
            
            logger.info(f"Database load completed: {row_count} records")
            
        except Exception as e:
            logger.error(f"Database load failed: {e}")
            raise
    
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
        self.reset_settings_button.setToolTip("Reset all application settings including window position")