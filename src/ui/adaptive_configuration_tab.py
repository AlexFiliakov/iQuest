"""Enhanced configuration tab with adaptive display logic integration."""

import os
from datetime import date, datetime, timedelta
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QCheckBox, QScrollArea,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeyEvent

from utils.logging_config import get_logger
from ..data_availability_service import DataAvailabilityService, TimeRange, AvailabilityLevel
from ..health_database import HealthDatabase
from .adaptive_date_edit import AdaptiveDateRangeWidget
from .adaptive_time_range_selector import AdaptiveTimeRangeSelector
from .adaptive_multi_select_combo import AdaptiveMultiSelectCombo
from .enhanced_date_edit import EnhancedDateEdit
from .import_progress_dialog import ImportProgressDialog
from .statistics_widget import StatisticsWidget
from .summary_cards import SummaryCard
from .style_manager import StyleManager
from .component_factory import ComponentFactory
from ..statistics_calculator import StatisticsCalculator
from ..filter_config_manager import FilterConfigManager
from config import DATA_DIR

logger = get_logger(__name__)


class AdaptiveConfigurationTab(QWidget):
    """Enhanced configuration tab with adaptive display logic."""
    
    # Signals
    data_loaded = pyqtSignal(object)
    filters_applied = pyqtSignal(dict)
    availability_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing Adaptive Configuration tab")
        
        # Initialize core services
        self.health_db = HealthDatabase()
        self.availability_service = DataAvailabilityService(self.health_db)
        
        # Initialize other components
        self.style_manager = StyleManager()
        self.component_factory = ComponentFactory()
        self.filter_config_manager = FilterConfigManager()
        self.statistics_calculator = StatisticsCalculator()
        
        # Data state
        self.data = None
        self.filtered_data = None
        self.current_metric_selection = []
        self.current_date_range = None
        
        # UI elements that need to be accessed
        self.file_path_input = None
        self.progress_bar = None
        self.progress_label = None
        self.adaptive_date_range = None
        self.time_range_selector = None
        self.metric_selector = None
        self.source_selector = None
        self.apply_button = None
        self.reset_button = None
        self.status_label = None
        self.availability_status_label = None
        self.statistics_widget = None
        
        # Create the UI
        self._create_ui()
        self._setup_adaptive_connections()
        
        # Initial availability scan
        QTimer.singleShot(1000, self._initial_availability_scan)
        
        logger.info("Adaptive Configuration tab initialized")
        
    def _create_ui(self):
        """Create the adaptive configuration tab UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Title with availability indicator
        title_layout = QHBoxLayout()
        title = QLabel("Smart Configuration")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #5D4E37;
                margin-bottom: 10px;
            }
        """)
        
        self.availability_indicator = QLabel("●")
        self.availability_indicator.setStyleSheet("color: red; font-size: 20px;")
        self.availability_indicator.setToolTip("Data availability status")
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.availability_indicator)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Create main splitter for layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Controls
        left_panel = self._create_control_panel()
        left_panel.setMaximumWidth(350)
        
        # Right panel - Data and Statistics
        right_panel = self._create_data_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)  # Fixed width for controls
        splitter.setStretchFactor(1, 1)  # Expandable for data
        
        main_layout.addWidget(splitter)
        
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with adaptive components."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # Import section
        layout.addWidget(self._create_import_section())
        
        # Time Range selection with adaptive logic
        layout.addWidget(self._create_adaptive_time_range_section())
        
        # Metric selection with availability indicators
        layout.addWidget(self._create_adaptive_metric_section())
        
        # Source selection
        layout.addWidget(self._create_source_section())
        
        # Filter actions
        layout.addWidget(self._create_filter_actions_section())
        
        # Availability status
        layout.addWidget(self._create_availability_status_section())
        
        layout.addStretch()
        return panel
        
    def _create_data_panel(self) -> QWidget:
        """Create the data display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # Statistics widget
        self.statistics_widget = StatisticsWidget()
        layout.addWidget(self.statistics_widget)
        
        # Summary cards for availability stats
        layout.addWidget(self._create_availability_summary_section())
        
        # Status display
        layout.addWidget(self._create_status_section())
        
        return panel
        
    def _create_import_section(self) -> QGroupBox:
        """Create the import section."""
        section = QGroupBox("Data Import")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select Apple Health export file...")
        self.file_path_input.setAccessibleName("File path input")
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._on_browse_clicked)
        browse_button.setAccessibleDescription("Browse for Apple Health export file")
        
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_button)
        
        # Import button
        import_button = QPushButton("Import Data")
        import_button.clicked.connect(self._on_import_clicked)
        import_button.setStyleSheet(self._get_primary_button_style())
        
        layout.addLayout(file_layout)
        layout.addWidget(import_button)
        
        return section
        
    def _create_adaptive_time_range_section(self) -> QGroupBox:
        """Create adaptive time range selection section."""
        section = QGroupBox("Smart Time Range Selection")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        # Quick range selector with availability
        self.time_range_selector = AdaptiveTimeRangeSelector(
            parent=self, 
            availability_service=self.availability_service
        )
        layout.addWidget(self.time_range_selector)
        
        # Custom date range with availability feedback
        custom_label = QLabel("Custom Date Range:")
        custom_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(custom_label)
        
        self.adaptive_date_range = AdaptiveDateRangeWidget(
            parent=self,
            availability_service=self.availability_service
        )
        layout.addWidget(self.adaptive_date_range)
        
        return section
        
    def _create_adaptive_metric_section(self) -> QGroupBox:
        """Create adaptive metric selection section."""
        section = QGroupBox("Smart Metric Selection")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        # Instructions
        instruction_label = QLabel("Select metrics (availability indicators shown):")
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # Adaptive metric selector
        self.metric_selector = AdaptiveMultiSelectCombo(
            parent=self,
            availability_service=self.availability_service
        )
        layout.addWidget(self.metric_selector)
        
        # Quick selection buttons
        button_layout = QHBoxLayout()
        
        full_data_button = QPushButton("Full Data Only")
        full_data_button.clicked.connect(self.metric_selector.checkFullDataOnly)
        full_data_button.setToolTip("Select only metrics with complete data")\n        
        any_data_button = QPushButton("Any Data")
        any_data_button.clicked.connect(self.metric_selector.checkAll)
        any_data_button.setToolTip("Select all metrics with any available data")
        
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.metric_selector.uncheckAll)
        
        button_layout.addWidget(full_data_button)
        button_layout.addWidget(any_data_button)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        return section
        
    def _create_source_section(self) -> QGroupBox:
        """Create source selection section."""
        section = QGroupBox("Data Sources")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        # Source selector (could be enhanced with availability too)
        self.source_selector = AdaptiveMultiSelectCombo(
            parent=self,
            availability_service=self.availability_service
        )
        self.source_selector.setPlaceholderText("Select data sources...")
        layout.addWidget(self.source_selector)
        
        return section
        
    def _create_filter_actions_section(self) -> QGroupBox:
        """Create filter action buttons."""
        section = QGroupBox("Actions")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        # Apply filters button
        self.apply_button = QPushButton("Apply Smart Filters")
        self.apply_button.clicked.connect(self._on_apply_filters)
        self.apply_button.setStyleSheet(self._get_primary_button_style())
        self.apply_button.setEnabled(False)
        
        # Reset button
        self.reset_button = QPushButton("Reset to Optimal")
        self.reset_button.clicked.connect(self._on_reset_to_optimal)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        save_preset_button = QPushButton("Save Preset")
        load_preset_button = QPushButton("Load Preset")
        
        preset_layout.addWidget(save_preset_button)
        preset_layout.addWidget(load_preset_button)
        
        layout.addWidget(self.apply_button)
        layout.addWidget(self.reset_button)
        layout.addLayout(preset_layout)
        
        return section
        
    def _create_availability_status_section(self) -> QGroupBox:
        """Create availability status display."""
        section = QGroupBox("Data Availability Status")
        section.setStyleSheet(self._get_group_style())
        layout = QVBoxLayout(section)
        
        self.availability_status_label = QLabel("Analyzing data availability...")
        self.availability_status_label.setWordWrap(True)
        self.availability_status_label.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border: 1px solid #DDD;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(self.availability_status_label)
        
        return section
        
    def _create_availability_summary_section(self) -> QGroupBox:
        """Create availability summary with cards."""
        section = QGroupBox("Availability Summary")
        section.setStyleSheet(self._get_group_style())
        layout = QHBoxLayout(section)
        
        # Availability summary cards
        self.metrics_available_card = SummaryCard(
            title="Metrics Available",
            value="0/0",
            subtitle="with data",
            color="#32CD32"
        )
        
        self.coverage_card = SummaryCard(
            title="Data Coverage",
            value="0%",
            subtitle="of selected period",
            color="#FFD700"
        )
        
        layout.addWidget(self.metrics_available_card)
        layout.addWidget(self.coverage_card)
        
        return section
        
    def _create_status_section(self) -> QWidget:
        """Create status display section."""
        section = QWidget()
        layout = QVBoxLayout(section)
        
        self.status_label = QLabel("No data loaded - Import data to begin")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: #F0F8FF;
                border: 1px solid #87CEEB;
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                color: #4682B4;
            }}
        """)
        layout.addWidget(self.status_label)
        
        return section
        
    def _setup_adaptive_connections(self):
        """Setup connections between adaptive components."""
        # Connect availability service updates
        self.availability_service.register_callback(self._on_availability_updated)
        
        # Connect time range selector
        self.time_range_selector.rangeSelected.connect(self._on_time_range_selected)
        self.time_range_selector.availabilityChanged.connect(self._update_availability_display)
        
        # Connect date range widget
        self.adaptive_date_range.rangeChanged.connect(self._on_custom_date_range_changed)
        self.adaptive_date_range.availabilityChanged.connect(self._update_availability_display)
        
        # Connect metric selector
        self.metric_selector.selectionChanged.connect(self._on_metric_selection_changed)
        self.metric_selector.availabilityChanged.connect(self._update_availability_display)
        
    def _initial_availability_scan(self):
        """Perform initial availability scan."""
        if self.health_db.validate_database():
            logger.info("Performing initial data availability scan")
            self.availability_service.scan_availability()
            self._populate_metric_options()
            self._populate_source_options()
            self._update_availability_indicator("available")
        else:
            self._update_availability_indicator("no_data")
            
    def _populate_metric_options(self):
        """Populate metric selector with available metrics."""
        try:
            available_metrics = self.health_db.get_available_types()
            logger.info(f"Found {len(available_metrics)} metric types")
            
            self.metric_selector.clear()
            for metric in available_metrics:
                self.metric_selector.addMetric(metric)
                
        except Exception as e:
            logger.error(f"Error populating metrics: {e}")
            
    def _populate_source_options(self):
        """Populate source selector with available sources."""
        try:
            available_sources = self.health_db.get_available_sources()
            logger.info(f"Found {len(available_sources)} data sources")
            
            self.source_selector.clear()
            for source in available_sources:
                self.source_selector.addItem(source)
                
        except Exception as e:
            logger.error(f"Error populating sources: {e}")
            
    def _on_time_range_selected(self, range_type: str):
        """Handle time range selection."""
        logger.info(f"Time range selected: {range_type}")
        
        # Update metric selectors for this time range
        for metric in self.metric_selector.checkedTexts():
            self.time_range_selector.set_metric_type(metric)
            self.adaptive_date_range.set_metric_type(metric)
            
        self._update_apply_button_state()
        
    def _on_custom_date_range_changed(self, start_date, end_date):
        """Handle custom date range changes."""
        logger.info(f"Date range changed: {start_date.toString()} to {end_date.toString()}")
        self.current_date_range = (start_date.toPython(), end_date.toPython())
        self._update_apply_button_state()
        
    def _on_metric_selection_changed(self, selected_metrics):
        """Handle metric selection changes."""
        logger.info(f"Metrics selected: {selected_metrics}")
        self.current_metric_selection = selected_metrics
        
        # Update time range components for selected metrics
        if selected_metrics:
            # Use first selected metric for time range availability
            primary_metric = selected_metrics[0]
            self.time_range_selector.set_metric_type(primary_metric)
            self.adaptive_date_range.set_metric_type(primary_metric)
            
        self._update_apply_button_state()
        self._update_availability_summary()
        
    def _on_availability_updated(self):
        """Handle availability service updates."""
        logger.debug("Availability data updated")
        self._update_availability_display()
        self.availability_updated.emit()
        
    def _update_availability_display(self):
        """Update all availability-related UI elements."""
        self._update_availability_indicator("available")
        self._update_availability_status()
        self._update_availability_summary()
        
    def _update_availability_indicator(self, status: str):
        """Update the main availability indicator."""
        if status == "available":
            self.availability_indicator.setStyleSheet("color: green; font-size: 20px;")
            self.availability_indicator.setToolTip("Data available")
        elif status == "partial":
            self.availability_indicator.setStyleSheet("color: orange; font-size: 20px;")
            self.availability_indicator.setToolTip("Limited data available")
        else:  # no_data
            self.availability_indicator.setStyleSheet("color: red; font-size: 20px;")
            self.availability_indicator.setToolTip("No data available")
            
    def _update_availability_status(self):
        """Update the availability status text."""
        if not hasattr(self, 'availability_status_label'):
            return
            
        try:
            cache_stats = self.availability_service.get_cache_stats()
            
            status_text = f"Cached metrics: {cache_stats['cached_metrics']}\\n"
            if cache_stats['last_scan']:
                status_text += f"Last scan: {cache_stats['last_scan'].strftime('%H:%M:%S')}\\n"
            status_text += f"Cache valid: {'Yes' if cache_stats['cache_valid'] else 'No'}"
            
            self.availability_status_label.setText(status_text)
            
        except Exception as e:
            logger.error(f"Error updating availability status: {e}")
            self.availability_status_label.setText("Error reading availability data")
            
    def _update_availability_summary(self):
        """Update availability summary cards."""
        if not hasattr(self, 'metrics_available_card'):
            return
            
        try:
            # Get availability stats from metric selector
            stats = self.metric_selector.getAvailabilityStats()
            
            total_metrics = stats['total']
            available_metrics = stats['full'] + stats['partial'] + stats['sparse']
            
            self.metrics_available_card.setValue(f"{available_metrics}/{total_metrics}")
            
            # Calculate coverage percentage
            if self.current_metric_selection:
                checked_metrics = self.metric_selector.getCheckedMetricsWithAvailability()
                full_data_count = sum(1 for _, level, _ in checked_metrics 
                                    if level == AvailabilityLevel.FULL)
                coverage_percent = (full_data_count / len(checked_metrics)) * 100 if checked_metrics else 0
                self.coverage_card.setValue(f"{coverage_percent:.0f}%")
            else:
                self.coverage_card.setValue("0%")
                
        except Exception as e:
            logger.error(f"Error updating availability summary: {e}")
            
    def _update_apply_button_state(self):
        """Update apply button state based on current selections."""
        has_metrics = bool(self.current_metric_selection)
        has_date_range = self.current_date_range is not None
        has_data = self.health_db.validate_database()
        
        self.apply_button.setEnabled(has_metrics and has_data)
        
    def _on_apply_filters(self):
        """Apply the selected filters with availability optimization."""
        logger.info("Applying smart filters")
        
        try:
            # Get selected metrics with availability info
            selected_metrics = self.metric_selector.getCheckedMetricsWithAvailability()
            
            if not selected_metrics:
                QMessageBox.warning(self, "No Metrics", "Please select at least one metric.")
                return
                
            # Apply filters and update UI
            self._apply_smart_filtering(selected_metrics)
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            QMessageBox.critical(self, "Filter Error", f"Error applying filters: {str(e)}")
            
    def _apply_smart_filtering(self, selected_metrics):
        """Apply smart filtering based on availability."""
        # Implementation would depend on your existing filtering logic
        # This is a placeholder for the actual filtering implementation
        logger.info(f"Applying smart filtering for {len(selected_metrics)} metrics")
        self.filters_applied.emit({
            'metrics': [name for name, _, _ in selected_metrics],
            'date_range': self.current_date_range,
            'availability_optimized': True
        })
        
    def _on_reset_to_optimal(self):
        """Reset to optimal selections based on data availability."""
        logger.info("Resetting to optimal selections")
        
        # Auto-select metrics with full data
        self.metric_selector.checkFullDataOnly()
        
        # Auto-select best time range
        self.time_range_selector.auto_select_best_range()
        
        # Update date range to suggested optimal
        if self.current_metric_selection:
            optimal_range = self.adaptive_date_range.suggest_optimal_range()
            if optimal_range:
                start_date, end_date = optimal_range
                self.adaptive_date_range.set_date_range(
                    QDate.fromString(start_date.isoformat(), Qt.DateFormat.ISODate),
                    QDate.fromString(end_date.isoformat(), Qt.DateFormat.ISODate)
                )
                
    def _on_browse_clicked(self):
        """Handle browse button click."""
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
            QMessageBox.warning(self, "No File Selected", "Please select a file to import.")
            return
            
        logger.info(f"Starting import of: {file_path}")
        self._start_import_with_progress(file_path)
        
    def _start_import_with_progress(self, file_path):
        """Start import with progress dialog."""
        progress_dialog = ImportProgressDialog(file_path, "auto", self)
        progress_dialog.import_completed.connect(self._on_import_completed)
        progress_dialog.import_cancelled.connect(self._on_import_cancelled)
        
        progress_dialog.start_import()
        progress_dialog.exec()
        
    def _on_import_completed(self, result):
        """Handle successful import completion."""
        logger.info(f"Import completed: {result}")
        
        # Refresh availability data
        QTimer.singleShot(500, self._refresh_after_import)
        
        self.status_label.setText(f"Import completed: {result.get('record_count', 0):,} records")
        
    def _on_import_cancelled(self):
        """Handle import cancellation."""
        logger.info("Import was cancelled")
        self.status_label.setText("Import cancelled")
        
    def _refresh_after_import(self):
        """Refresh UI after successful import."""
        # Invalidate availability cache and rescan
        self.availability_service.invalidate_cache()
        self.availability_service.scan_availability()
        
        # Repopulate options
        self._populate_metric_options()
        self._populate_source_options()
        
        # Update UI
        self._update_availability_display()
        self._update_apply_button_state()
        
    def _get_group_style(self) -> str:
        """Get consistent group box styling."""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #D2B48C;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                background-color: #FDFDF8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #8B4513;
            }
        """
        
    def _get_primary_button_style(self) -> str:
        """Get primary button styling."""
        return """
            QPushButton {
                background-color: #FF8C42;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E07A3A;
            }
            QPushButton:pressed {
                background-color: #D16829;
            }
            QPushButton:disabled {
                background-color: #CCC;
                color: #888;
            }
        """
        
    def cleanup(self):
        """Cleanup when widget is destroyed."""
        if hasattr(self, 'adaptive_date_range') and self.adaptive_date_range:
            self.adaptive_date_range.cleanup()
        if hasattr(self, 'time_range_selector') and self.time_range_selector:
            self.time_range_selector.cleanup()
        if hasattr(self, 'metric_selector') and self.metric_selector:
            self.metric_selector.cleanup()
        if hasattr(self, 'source_selector') and self.source_selector:
            self.source_selector.cleanup()
            
        # Cleanup availability service
        if hasattr(self, 'availability_service'):
            self.availability_service.unregister_callback(self._on_availability_updated)