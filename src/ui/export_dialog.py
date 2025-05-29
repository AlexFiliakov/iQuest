"""
Export dialog for configuring and generating health reports.

This module provides a user-friendly dialog for configuring export options
and generating various types of health reports and data exports.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QGroupBox, QFileDialog, QMessageBox, QProgressDialog,
    QRadioButton, QButtonGroup, QSpinBox, QTabWidget,
    QWidget, QGridLayout, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QIcon, QFont

from ..analytics.export_reporting_system import (
    WSJExportReportingSystem, ExportConfiguration, ExportFormat, 
    ReportTemplate, ExportProgressManager
)
from .adaptive_date_edit import AdaptiveDateEdit
from .style_manager import StyleManager


class ExportWorker(QThread):
    """Worker thread for handling export operations."""
    
    progress_updated = pyqtSignal(int, str)
    export_completed = pyqtSignal(str, bytes)
    export_failed = pyqtSignal(str)
    
    def __init__(self, export_system: WSJExportReportingSystem, 
                 config: ExportConfiguration):
        super().__init__()
        self.export_system = export_system
        self.config = config
        self._is_cancelled = False
        
    def run(self):
        """Execute the export operation."""
        try:
            # Connect progress signals
            self.export_system.export_progress.progress_updated.connect(
                self.progress_updated.emit
            )
            
            # Generate report
            result = self.export_system.generate_report(self.config)
            
            if not self._is_cancelled:
                # Determine filename
                filename = self._generate_filename()
                self.export_completed.emit(filename, result)
                
        except Exception as e:
            if not self._is_cancelled:
                self.export_failed.emit(str(e))
                
    def cancel(self):
        """Cancel the export operation."""
        self._is_cancelled = True
        self.export_system.export_progress.cancel()
        
    def _generate_filename(self) -> str:
        """Generate appropriate filename based on export configuration."""
        base_name = self.config.title or "health_report"
        base_name = base_name.lower().replace(' ', '_')
        
        date_str = datetime.now().strftime('%Y%m%d')
        
        extension_map = {
            ExportFormat.PDF: '.pdf',
            ExportFormat.CSV: '.csv',
            ExportFormat.EXCEL: '.xlsx',
            ExportFormat.JSON: '.json',
            ExportFormat.HTML: '.html',
            ExportFormat.PNG: '.png',
            ExportFormat.SVG: '.svg'
        }
        
        extension = extension_map.get(self.config.format, '')
        return f"{base_name}_{date_str}{extension}"


class ExportDialog(QDialog):
    """Dialog for configuring health data exports and reports."""
    
    export_requested = pyqtSignal(ExportConfiguration)
    
    def __init__(self, export_system: WSJExportReportingSystem, 
                 available_metrics: List[str], 
                 parent=None):
        super().__init__(parent)
        self.export_system = export_system
        self.available_metrics = available_metrics
        self.style_manager = StyleManager()
        
        self.setWindowTitle("Export Health Data")
        self.setModal(True)
        self.resize(800, 600)
        
        self._init_ui()
        self._apply_styling()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)
        
        # Quick Export tab
        self.quick_export_tab = self._create_quick_export_tab()
        self.tab_widget.addTab(self.quick_export_tab, "Quick Export")
        
        # Custom Report tab
        self.custom_report_tab = self._create_custom_report_tab()
        self.tab_widget.addTab(self.custom_report_tab, "Custom Report")
        
        # Backup tab
        self.backup_tab = self._create_backup_tab()
        self.tab_widget.addTab(self.backup_tab, "Backup")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self._on_preview)
        button_layout.addWidget(self.preview_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._on_export)
        self.export_button.setDefault(True)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
    def _create_quick_export_tab(self) -> QWidget:
        """Create the quick export tab."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        # Export type selection
        type_group = QGroupBox("Export Type")
        type_layout = QVBoxLayout(type_group)
        
        self.export_type_group = QButtonGroup()
        
        # Report options
        self.pdf_radio = QRadioButton("PDF Report - Professional health report with charts and insights")
        self.pdf_radio.setChecked(True)
        self.export_type_group.addButton(self.pdf_radio, 0)
        type_layout.addWidget(self.pdf_radio)
        
        self.html_radio = QRadioButton("HTML Summary - Email-friendly report with embedded charts")
        self.export_type_group.addButton(self.html_radio, 1)
        type_layout.addWidget(self.html_radio)
        
        # Data export options
        self.excel_radio = QRadioButton("Excel Workbook - Formatted data with multiple sheets")
        self.export_type_group.addButton(self.excel_radio, 2)
        type_layout.addWidget(self.excel_radio)
        
        self.csv_radio = QRadioButton("CSV File - Raw data for analysis in other tools")
        self.export_type_group.addButton(self.csv_radio, 3)
        type_layout.addWidget(self.csv_radio)
        
        self.json_radio = QRadioButton("JSON Export - Complete data with metadata")
        self.export_type_group.addButton(self.json_radio, 4)
        type_layout.addWidget(self.json_radio)
        
        # Chart export options
        self.png_radio = QRadioButton("PNG Charts - High-resolution images")
        self.export_type_group.addButton(self.png_radio, 5)
        type_layout.addWidget(self.png_radio)
        
        self.svg_radio = QRadioButton("SVG Charts - Scalable vector graphics")
        self.export_type_group.addButton(self.svg_radio, 6)
        type_layout.addWidget(self.svg_radio)
        
        layout.addWidget(type_group)
        
        # Template selection (for reports)
        self.template_group = QGroupBox("Report Template")
        template_layout = QVBoxLayout(self.template_group)
        
        self.template_combo = QComboBox(self)
        self.template_combo.addItems([
            "Comprehensive Health Report",
            "Medical Summary (for healthcare providers)",
            "Progress Tracking Report",
            "Weekly Summary",
            "Monthly Summary"
        ])
        template_layout.addWidget(self.template_combo)
        
        layout.addWidget(self.template_group)
        
        # Date range selection
        date_group = QGroupBox("Date Range")
        date_layout = QGridLayout(date_group)
        
        # Quick selection buttons
        self.last_week_btn = QPushButton("Last Week")
        self.last_week_btn.clicked.connect(lambda: self._set_date_range(7))
        date_layout.addWidget(self.last_week_btn, 0, 0)
        
        self.last_month_btn = QPushButton("Last Month")
        self.last_month_btn.clicked.connect(lambda: self._set_date_range(30))
        date_layout.addWidget(self.last_month_btn, 0, 1)
        
        self.last_3months_btn = QPushButton("Last 3 Months")
        self.last_3months_btn.clicked.connect(lambda: self._set_date_range(90))
        date_layout.addWidget(self.last_3months_btn, 0, 2)
        
        self.last_year_btn = QPushButton("Last Year")
        self.last_year_btn.clicked.connect(lambda: self._set_date_range(365))
        date_layout.addWidget(self.last_year_btn, 0, 3)
        
        # Custom date range
        date_layout.addWidget(QLabel("From:"), 1, 0)
        self.start_date_edit = AdaptiveDateEdit()
        self.start_date_edit.set_date(datetime.now() - timedelta(days=30))
        date_layout.addWidget(self.start_date_edit, 1, 1)
        
        date_layout.addWidget(QLabel("To:"), 1, 2)
        self.end_date_edit = AdaptiveDateEdit()
        self.end_date_edit.set_date(datetime.now())
        date_layout.addWidget(self.end_date_edit, 1, 3)
        
        layout.addWidget(date_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_insights_check = QCheckBox("Include AI-generated insights and recommendations")
        self.include_insights_check.setChecked(True)
        options_layout.addWidget(self.include_insights_check)
        
        self.include_charts_check = QCheckBox("Include visualizations and charts")
        self.include_charts_check.setChecked(True)
        options_layout.addWidget(self.include_charts_check)
        
        self.include_raw_data_check = QCheckBox("Include raw data (increases file size)")
        options_layout.addWidget(self.include_raw_data_check)
        
        layout.addWidget(options_group)
        
        # Connect signals
        self.export_type_group.buttonClicked.connect(self._on_export_type_changed)
        
        layout.addStretch()
        
        return widget
        
    def _create_custom_report_tab(self) -> QWidget:
        """Create the custom report tab."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Report Title:"))
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter custom report title...")
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # Metric selection
        metrics_group = QGroupBox("Select Metrics to Include")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # Select all/none buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_metrics)
        button_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self._select_no_metrics)
        button_layout.addWidget(select_none_btn)
        
        button_layout.addStretch()
        metrics_layout.addLayout(button_layout)
        
        # Metrics list
        self.metrics_list = QListWidget(self)
        self.metrics_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        for metric in self.available_metrics:
            item = QListWidgetItem(metric.replace('_', ' ').title())
            item.setData(Qt.ItemDataRole.UserRole, metric)
            self.metrics_list.addItem(item)
            
        metrics_layout.addWidget(self.metrics_list)
        layout.addWidget(metrics_group)
        
        # Custom sections
        sections_group = QGroupBox("Report Sections")
        sections_layout = QVBoxLayout(sections_group)
        
        self.executive_summary_check = QCheckBox("Executive Summary")
        self.executive_summary_check.setChecked(True)
        sections_layout.addWidget(self.executive_summary_check)
        
        self.detailed_analysis_check = QCheckBox("Detailed Analysis")
        self.detailed_analysis_check.setChecked(True)
        sections_layout.addWidget(self.detailed_analysis_check)
        
        self.recommendations_check = QCheckBox("Recommendations")
        self.recommendations_check.setChecked(True)
        sections_layout.addWidget(self.recommendations_check)
        
        self.appendix_check = QCheckBox("Data Appendix")
        sections_layout.addWidget(self.appendix_check)
        
        layout.addWidget(sections_group)
        
        # Resolution settings
        resolution_group = QGroupBox("Export Quality")
        resolution_layout = QHBoxLayout(resolution_group)
        
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox(self)
        self.resolution_combo.addItems([
            "Web (72 DPI)",
            "Print (300 DPI)",
            "High Quality (600 DPI)"
        ])
        self.resolution_combo.setCurrentIndex(1)  # Default to print
        resolution_layout.addWidget(self.resolution_combo)
        
        resolution_layout.addStretch()
        layout.addWidget(resolution_group)
        
        return widget
        
    def _create_backup_tab(self) -> QWidget:
        """Create the backup tab."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        # Backup description
        desc_label = QLabel(
            "Create a complete backup of your health data including all metrics, "
            "insights, and settings. The backup will be saved as a ZIP file that "
            "can be restored later."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Backup options
        options_group = QGroupBox("Backup Options")
        options_layout = QVBoxLayout(options_group)
        
        self.backup_all_data_check = QCheckBox("Include all historical data")
        self.backup_all_data_check.setChecked(True)
        options_layout.addWidget(self.backup_all_data_check)
        
        self.backup_settings_check = QCheckBox("Include application settings")
        self.backup_settings_check.setChecked(True)
        options_layout.addWidget(self.backup_settings_check)
        
        self.backup_insights_check = QCheckBox("Include generated insights")
        self.backup_insights_check.setChecked(True)
        options_layout.addWidget(self.backup_insights_check)
        
        layout.addWidget(options_group)
        
        # Backup info
        info_group = QGroupBox("Backup Information")
        info_layout = QVBoxLayout(info_group)
        
        self.backup_info_text = QTextEdit(self)
        self.backup_info_text.setReadOnly(True)
        self.backup_info_text.setMaximumHeight(150)
        self._update_backup_info()
        
        info_layout.addWidget(self.backup_info_text)
        layout.addWidget(info_group)
        
        # Create backup button
        self.create_backup_btn = QPushButton("Create Backup")
        self.create_backup_btn.clicked.connect(self._create_backup)
        layout.addWidget(self.create_backup_btn)
        
        layout.addStretch()
        
        return widget
        
    def _on_export_type_changed(self):
        """Handle export type selection change."""
        # Show/hide template selection based on export type
        selected_id = self.export_type_group.checkedId()
        
        # Show template for PDF and HTML reports
        self.template_group.setVisible(selected_id in [0, 1])
        
        # Update preview button availability
        self.preview_button.setEnabled(selected_id in [0, 1])
        
    def _set_date_range(self, days: int):
        """Set date range for quick selection."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        self.start_date_edit.set_date(start_date)
        self.end_date_edit.set_date(end_date)
        
    def _select_all_metrics(self):
        """Select all metrics in the list."""
        for i in range(self.metrics_list.count()):
            self.metrics_list.item(i).setSelected(True)
            
    def _select_no_metrics(self):
        """Deselect all metrics in the list."""
        for i in range(self.metrics_list.count()):
            self.metrics_list.item(i).setSelected(False)
            
    def _update_backup_info(self):
        """Update backup information display."""
        info = []
        info.append("Backup Contents:")
        
        if self.backup_all_data_check.isChecked():
            info.append("• All health metrics and historical data")
            
        if self.backup_settings_check.isChecked():
            info.append("• Application settings and preferences")
            
        if self.backup_insights_check.isChecked():
            info.append("• AI-generated insights and recommendations")
            
        info.append("")
        info.append("The backup will include data integrity verification")
        info.append("and can be restored to recover your data.")
        
        self.backup_info_text.setPlainText("\n".join(info))
        
    def _get_export_configuration(self) -> ExportConfiguration:
        """Create export configuration from dialog settings."""
        # Determine format
        format_map = {
            0: ExportFormat.PDF,
            1: ExportFormat.HTML,
            2: ExportFormat.EXCEL,
            3: ExportFormat.CSV,
            4: ExportFormat.JSON,
            5: ExportFormat.PNG,
            6: ExportFormat.SVG
        }
        
        export_format = format_map[self.export_type_group.checkedId()]
        
        # Determine template
        template_map = {
            0: ReportTemplate.COMPREHENSIVE,
            1: ReportTemplate.MEDICAL_SUMMARY,
            2: ReportTemplate.PROGRESS_TRACKING,
            3: ReportTemplate.WEEKLY_SUMMARY,
            4: ReportTemplate.MONTHLY_SUMMARY
        }
        
        template = template_map.get(self.template_combo.currentIndex(), 
                                   ReportTemplate.COMPREHENSIVE)
        
        # Get selected metrics
        if self.tab_widget.currentIndex() == 1:  # Custom report tab
            selected_metrics = []
            for i in range(self.metrics_list.count()):
                item = self.metrics_list.item(i)
                if item.isSelected():
                    selected_metrics.append(item.data(Qt.ItemDataRole.UserRole))
        else:
            # Quick export uses all available metrics
            selected_metrics = self.available_metrics
            
        # Determine resolution
        resolution_map = {
            0: "web",
            1: "print",
            2: "high"
        }
        
        resolution = resolution_map.get(self.resolution_combo.currentIndex(), "print")
        
        # Create configuration
        config = ExportConfiguration(
            format=export_format,
            date_range=(
                self.start_date_edit.get_date(),
                self.end_date_edit.get_date()
            ),
            metrics=selected_metrics,
            include_charts=self.include_charts_check.isChecked(),
            include_insights=self.include_insights_check.isChecked(),
            include_raw_data=self.include_raw_data_check.isChecked(),
            template=template,
            resolution=resolution,
            title=self.title_edit.text() or None
        )
        
        # Add custom sections for custom reports
        if self.tab_widget.currentIndex() == 1:
            config.custom_sections = {
                'executive_summary': self.executive_summary_check.isChecked(),
                'detailed_analysis': self.detailed_analysis_check.isChecked(),
                'recommendations': self.recommendations_check.isChecked(),
                'appendix': self.appendix_check.isChecked()
            }
            
        return config
        
    def _on_preview(self):
        """Handle preview button click."""
        # This would show a preview of the report
        # For now, show a message
        QMessageBox.information(
            self,
            "Preview",
            "Report preview will be implemented in a future update."
        )
        
    def _on_export(self):
        """Handle export button click."""
        # Get configuration
        config = self._get_export_configuration()
        
        # Validate configuration
        if not config.metrics:
            QMessageBox.warning(
                self,
                "No Metrics Selected",
                "Please select at least one metric to export."
            )
            return
            
        # Get save location
        filename_filter = self._get_filename_filter(config.format)
        default_name = self._generate_default_filename(config)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export",
            default_name,
            filename_filter
        )
        
        if not file_path:
            return
            
        config.output_path = Path(file_path)
        
        # Create progress dialog
        progress_dialog = QProgressDialog(
            "Generating export...",
            "Cancel",
            0,
            100,
            self
        )
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoReset(False)
        progress_dialog.setAutoClose(False)
        
        # Create worker thread
        self.export_worker = ExportWorker(self.export_system, config)
        
        # Connect signals
        self.export_worker.progress_updated.connect(
            lambda percent, msg: (
                progress_dialog.setValue(percent),
                progress_dialog.setLabelText(msg)
            )
        )
        
        self.export_worker.export_completed.connect(
            lambda filename, data: self._on_export_completed(
                filename, data, config.output_path, progress_dialog
            )
        )
        
        self.export_worker.export_failed.connect(
            lambda error: self._on_export_failed(error, progress_dialog)
        )
        
        progress_dialog.canceled.connect(self.export_worker.cancel)
        
        # Start export
        self.export_worker.start()
        
    def _create_backup(self):
        """Handle backup creation."""
        # Get backup location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup",
            f"health_backup_{datetime.now().strftime('%Y%m%d')}.zip",
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
            
        # Create progress dialog
        progress_dialog = QProgressDialog(
            "Creating backup...",
            "Cancel",
            0,
            100,
            self
        )
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        
        try:
            # Create backup
            backup_data = self.export_system.create_backup(
                include_settings=self.backup_settings_check.isChecked()
            )
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(backup_data)
                
            progress_dialog.setValue(100)
            
            QMessageBox.information(
                self,
                "Backup Complete",
                f"Backup successfully created:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )
            
    def _on_export_completed(self, filename: str, data: bytes, 
                           output_path: Path, progress_dialog: QProgressDialog):
        """Handle successful export completion."""
        try:
            # Save data to file
            with open(output_path, 'wb') as f:
                f.write(data)
                
            progress_dialog.close()
            
            # Show success message
            reply = QMessageBox.information(
                self,
                "Export Complete",
                f"Export successfully saved to:\n{output_path}\n\n"
                f"Would you like to open the file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Open file with default application
                import os
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(str(output_path))
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{output_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{output_path}"')
                    
            self.accept()
            
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save export:\n{str(e)}"
            )
            
    def _on_export_failed(self, error: str, progress_dialog: QProgressDialog):
        """Handle export failure."""
        progress_dialog.close()
        
        QMessageBox.critical(
            self,
            "Export Failed",
            f"Failed to generate export:\n{error}"
        )
        
    def _get_filename_filter(self, format: ExportFormat) -> str:
        """Get filename filter for save dialog."""
        filters = {
            ExportFormat.PDF: "PDF Files (*.pdf)",
            ExportFormat.CSV: "CSV Files (*.csv)",
            ExportFormat.EXCEL: "Excel Files (*.xlsx)",
            ExportFormat.JSON: "JSON Files (*.json)",
            ExportFormat.HTML: "HTML Files (*.html)",
            ExportFormat.PNG: "PNG Images (*.png)",
            ExportFormat.SVG: "SVG Images (*.svg)"
        }
        
        return filters.get(format, "All Files (*.*)")
        
    def _generate_default_filename(self, config: ExportConfiguration) -> str:
        """Generate default filename for export."""
        base_name = config.title or "health_export"
        base_name = base_name.lower().replace(' ', '_')
        
        date_str = datetime.now().strftime('%Y%m%d')
        
        extension_map = {
            ExportFormat.PDF: '.pdf',
            ExportFormat.CSV: '.csv',
            ExportFormat.EXCEL: '.xlsx',
            ExportFormat.JSON: '.json',
            ExportFormat.HTML: '.html',
            ExportFormat.PNG: '_charts.png',
            ExportFormat.SVG: '_charts.svg'
        }
        
        extension = extension_map.get(config.format, '')
        return f"{base_name}_{date_str}{extension}"
        
    def _apply_styling(self):
        """Apply WSJ-inspired styling to the dialog."""
        # Apply style manager settings
        self.style_manager.apply_theme(self)
        
        # Custom styling for this dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.style_manager.colors['background']};
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.style_manager.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            
            QPushButton {{
                min-width: 80px;
                min-height: 30px;
            }}
            
            QPushButton#export_button {{
                background-color: {self.style_manager.colors['primary']};
                color: white;
                font-weight: bold;
            }}
            
            QPushButton#export_button:hover {{
                background-color: {self.style_manager.colors['primary_dark']};
            }}
            
            QRadioButton, QCheckBox {{
                spacing: 8px;
            }}
            
            QListWidget {{
                border: 1px solid {self.style_manager.colors['border']};
                border-radius: 3px;
                background-color: white;
            }}
            
            QListWidget::item:selected {{
                background-color: {self.style_manager.colors['selection']};
                color: white;
            }}
        """)
        
        # Set button IDs for styling
        self.export_button.setObjectName("export_button")