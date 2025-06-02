"""Journal export dialog for selecting export options.

This module provides a comprehensive export dialog that allows users to export
their journal entries in various formats (JSON, PDF) with customizable options.
The dialog includes date range selection, format-specific settings, and export
progress tracking.

The JournalExportDialog provides:
    - Format selection (JSON, PDF)
    - Date range picker with presets
    - Format-specific options
    - Export preview (entry count)
    - Progress tracking during export
    - Success/error notifications

Example:
    Basic usage:
    
    >>> dialog = JournalExportDialog(parent_widget)
    >>> if dialog.exec() == QDialog.DialogCode.Accepted:
    ...     # Export completed successfully
    ...     print(f"Exported to: {dialog.export_result.file_path}")
"""

import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QDate, QTimer,
    QPropertyAnimation, QEasingCurve, QRect
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QCheckBox, QSpinBox, QStackedWidget,
    QProgressBar, QDialogButtonBox, QFileDialog, QMessageBox,
    QRadioButton, QButtonGroup, QWidget, QFrame, QGridLayout
)
from PyQt6.QtGui import QIcon, QPalette, QColor

from ..data_access import JournalDAO
from ..models import JournalEntry
from ..exporters import JSONExporter, PDFExporter, ExportOptions, ExportResult
from ..utils.logging_config import get_logger
from .enhanced_date_edit import EnhancedDateEdit
from .style_manager import StyleManager

logger = get_logger(__name__)


class ExportWorker(QThread):
    """Worker thread for handling export operations.
    
    Performs the actual export in a background thread to keep the UI
    responsive during potentially long export operations.
    
    Signals:
        progress: Export progress updates (0-100).
        finished: Export completed with result.
        error: Export failed with error message.
    """
    
    progress = pyqtSignal(float)
    finished = pyqtSignal(ExportResult)
    error = pyqtSignal(str)
    
    def __init__(self, exporter, entries: List[JournalEntry], 
                 output_path: str, parent=None):
        """Initialize export worker.
        
        Args:
            exporter: Configured exporter instance (JSON or PDF).
            entries: List of journal entries to export.
            output_path: Destination file path.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self.exporter = exporter
        self.entries = entries
        self.output_path = output_path
        
    def run(self):
        """Execute the export operation."""
        try:
            # Set up progress callback
            self.exporter.options.progress_callback = self.progress.emit
            
            # Perform export
            result = self.exporter.export(self.entries, self.output_path)
            
            if result.success:
                self.finished.emit(result)
            else:
                self.error.emit(result.error_message or "Export failed")
                
        except Exception as e:
            logger.error(f"Export worker error: {e}")
            self.error.emit(str(e))


class DateRangeSelector(QWidget):
    """Widget for selecting date ranges with presets.
    
    Provides an intuitive interface for selecting date ranges including
    preset options like "This month", "Last 30 days", etc., as well as
    custom date range selection.
    
    Signals:
        rangeChanged: Emitted when the date range changes.
    """
    
    rangeChanged = pyqtSignal(QDate, QDate)
    
    def __init__(self, parent=None):
        """Initialize date range selector."""
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Create the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preset selector
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Date Range:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "All entries",
            "This year",
            "Last 12 months",
            "Last 6 months",
            "Last 3 months",
            "Last 30 days",
            "This month",
            "Last month",
            "Custom range"
        ])
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        # Custom date range (hidden by default)
        self.custom_widget = QWidget()
        custom_layout = QGridLayout(self.custom_widget)
        custom_layout.setContentsMargins(0, 10, 0, 0)
        
        custom_layout.addWidget(QLabel("From:"), 0, 0)
        self.from_date = EnhancedDateEdit()
        self.from_date.setCalendarPopup(True)
        custom_layout.addWidget(self.from_date, 0, 1)
        
        custom_layout.addWidget(QLabel("To:"), 1, 0)
        self.to_date = EnhancedDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        custom_layout.addWidget(self.to_date, 1, 1)
        
        custom_layout.setColumnStretch(1, 1)
        self.custom_widget.setVisible(False)
        layout.addWidget(self.custom_widget)
        
        # Entry count preview
        self.count_label = QLabel("Calculating entry count...")
        self.count_label.setStyleSheet("color: #8B7355; font-style: italic;")
        layout.addWidget(self.count_label)
        
        # Update count timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_entry_count)
        self.update_timer.setSingleShot(True)
        
    def _connect_signals(self):
        """Connect widget signals."""
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.from_date.dateChanged.connect(self._on_date_changed)
        self.to_date.dateChanged.connect(self._on_date_changed)
        
    def _on_preset_changed(self, index: int):
        """Handle preset selection change."""
        preset_text = self.preset_combo.currentText()
        today = QDate.currentDate()
        
        if preset_text == "All entries":
            # Get actual date range from database
            self._set_all_entries_range()
        elif preset_text == "This year":
            start = QDate(today.year(), 1, 1)
            self._apply_range(start, today)
        elif preset_text == "Last 12 months":
            start = today.addMonths(-12)
            self._apply_range(start, today)
        elif preset_text == "Last 6 months":
            start = today.addMonths(-6)
            self._apply_range(start, today)
        elif preset_text == "Last 3 months":
            start = today.addMonths(-3)
            self._apply_range(start, today)
        elif preset_text == "Last 30 days":
            start = today.addDays(-30)
            self._apply_range(start, today)
        elif preset_text == "This month":
            start = QDate(today.year(), today.month(), 1)
            self._apply_range(start, today)
        elif preset_text == "Last month":
            last_month = today.addMonths(-1)
            start = QDate(last_month.year(), last_month.month(), 1)
            end = start.addMonths(1).addDays(-1)
            self._apply_range(start, end)
        elif preset_text == "Custom range":
            self.custom_widget.setVisible(True)
            self._on_date_changed()
        else:
            self.custom_widget.setVisible(False)
            
    def _set_all_entries_range(self):
        """Set date range to cover all journal entries."""
        try:
            # Get all entries to find date range
            all_entries = JournalDAO.get_all_journal_entries()
            if all_entries:
                min_date = min(e.entry_date for e in all_entries)
                max_date = max(e.entry_date for e in all_entries)
                self._apply_range(
                    QDate(min_date.year, min_date.month, min_date.day),
                    QDate(max_date.year, max_date.month, max_date.day)
                )
            else:
                # No entries, use current year
                today = QDate.currentDate()
                self._apply_range(QDate(today.year(), 1, 1), today)
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            today = QDate.currentDate()
            self._apply_range(QDate(today.year(), 1, 1), today)
            
    def _apply_range(self, start: QDate, end: QDate):
        """Apply a date range and hide custom widget."""
        self.custom_widget.setVisible(False)
        self.from_date.setDate(start)
        self.to_date.setDate(end)
        self.rangeChanged.emit(start, end)
        self._schedule_count_update()
        
    def _on_date_changed(self):
        """Handle custom date change."""
        if self.preset_combo.currentText() == "Custom range":
            self.rangeChanged.emit(self.from_date.date(), self.to_date.date())
            self._schedule_count_update()
            
    def _schedule_count_update(self):
        """Schedule entry count update with debouncing."""
        self.update_timer.stop()
        self.update_timer.start(500)  # Wait 500ms before updating
        
    def _update_entry_count(self):
        """Update the entry count label."""
        try:
            start_date = self.from_date.date().toPyDate()
            end_date = self.to_date.date().toPyDate()
            
            entries = JournalDAO.get_journal_entries(start_date, end_date)
            count = len(entries)
            
            if count == 0:
                self.count_label.setText("No entries in selected range")
            elif count == 1:
                self.count_label.setText("1 entry will be exported")
            else:
                self.count_label.setText(f"{count} entries will be exported")
                
        except Exception as e:
            logger.error(f"Error counting entries: {e}")
            self.count_label.setText("Error counting entries")
            
    def get_date_range(self) -> tuple[date, date]:
        """Get the selected date range.
        
        Returns:
            Tuple of (start_date, end_date) as Python date objects.
        """
        return (
            self.from_date.date().toPyDate(),
            self.to_date.date().toPyDate()
        )


class ExportOptionsWidget(QWidget):
    """Base widget for format-specific export options."""
    
    def __init__(self, parent=None):
        """Initialize options widget."""
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI (to be overridden by subclasses)."""
        pass
        
    def get_options(self) -> Dict[str, Any]:
        """Get the configured options.
        
        Returns:
            Dictionary of option key-value pairs.
        """
        return {}


class JSONOptionsWidget(ExportOptionsWidget):
    """Options widget for JSON export."""
    
    def _setup_ui(self):
        """Create JSON-specific options."""
        layout = QVBoxLayout(self)
        
        # Pretty print option
        self.pretty_print_check = QCheckBox("Pretty print (human readable)")
        self.pretty_print_check.setChecked(True)
        layout.addWidget(self.pretty_print_check)
        
        # Include metadata
        self.include_metadata_check = QCheckBox("Include export metadata")
        self.include_metadata_check.setChecked(True)
        layout.addWidget(self.include_metadata_check)
        
        # Include statistics
        self.include_stats_check = QCheckBox("Include statistics summary")
        self.include_stats_check.setChecked(True)
        layout.addWidget(self.include_stats_check)
        
        # Excel compatibility
        self.excel_compat_check = QCheckBox("Add BOM for Excel compatibility")
        layout.addWidget(self.excel_compat_check)
        
        layout.addStretch()
        
    def get_options(self) -> Dict[str, Any]:
        """Get JSON export options."""
        return {
            'pretty_print': self.pretty_print_check.isChecked(),
            'include_metadata': self.include_metadata_check.isChecked(),
            'include_statistics': self.include_stats_check.isChecked(),
            'add_bom': self.excel_compat_check.isChecked()
        }


class PDFOptionsWidget(ExportOptionsWidget):
    """Options widget for PDF export."""
    
    def _setup_ui(self):
        """Create PDF-specific options."""
        layout = QVBoxLayout(self)
        
        # Page elements
        elements_group = QGroupBox("Include Elements")
        elements_layout = QVBoxLayout(elements_group)
        
        self.include_cover_check = QCheckBox("Cover page")
        self.include_cover_check.setChecked(True)
        elements_layout.addWidget(self.include_cover_check)
        
        self.include_toc_check = QCheckBox("Table of contents")
        self.include_toc_check.setChecked(True)
        elements_layout.addWidget(self.include_toc_check)
        
        self.parse_markdown_check = QCheckBox("Parse markdown formatting")
        self.parse_markdown_check.setChecked(True)
        elements_layout.addWidget(self.parse_markdown_check)
        
        layout.addWidget(elements_group)
        
        # Page settings
        page_group = QGroupBox("Page Settings")
        page_layout = QGridLayout(page_group)
        
        page_layout.addWidget(QLabel("Page size:"), 0, 0)
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["Letter", "A4"])
        page_layout.addWidget(self.page_size_combo, 0, 1)
        
        layout.addWidget(page_group)
        layout.addStretch()
        
    def get_options(self) -> Dict[str, Any]:
        """Get PDF export options."""
        return {
            'include_cover': self.include_cover_check.isChecked(),
            'include_toc': self.include_toc_check.isChecked(),
            'parse_markdown': self.parse_markdown_check.isChecked(),
            'page_size': self.page_size_combo.currentText().lower()
        }


class JournalExportDialog(QDialog):
    """Main export dialog for journal entries.
    
    Provides a comprehensive interface for exporting journal entries with
    format selection, date range picking, and format-specific options.
    
    Attributes:
        export_result: The result of the export operation (if successful).
    """
    
    def __init__(self, parent=None):
        """Initialize export dialog.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.export_result: Optional[ExportResult] = None
        self.export_worker: Optional[ExportWorker] = None
        self._setup_ui()
        self._apply_styles()
        
    def _setup_ui(self):
        """Create the dialog UI."""
        self.setWindowTitle("Export Journal Entries")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Export Journal Entries")
        header_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #FF8C42;
            padding: 10px 0;
        """)
        layout.addWidget(header_label)
        
        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QHBoxLayout(format_group)
        
        self.format_group = QButtonGroup(self)
        self.json_radio = QRadioButton("JSON (Data backup)")
        self.pdf_radio = QRadioButton("PDF (Printable report)")
        self.json_radio.setChecked(True)
        
        self.format_group.addButton(self.json_radio, 0)
        self.format_group.addButton(self.pdf_radio, 1)
        
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.pdf_radio)
        format_layout.addStretch()
        layout.addWidget(format_group)
        
        # Date range selection
        range_group = QGroupBox("Date Range")
        range_layout = QVBoxLayout(range_group)
        self.date_range_selector = DateRangeSelector()
        range_layout.addWidget(self.date_range_selector)
        layout.addWidget(range_group)
        
        # Format-specific options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.options_stack = QStackedWidget()
        self.json_options = JSONOptionsWidget()
        self.pdf_options = PDFOptionsWidget()
        
        self.options_stack.addWidget(self.json_options)
        self.options_stack.addWidget(self.pdf_options)
        
        options_layout.addWidget(self.options_stack)
        layout.addWidget(options_group)
        
        # Progress bar (hidden initially)
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_label = QLabel("Exporting...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_widget.setVisible(False)
        layout.addWidget(self.progress_widget)
        
        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        layout.addWidget(self.button_box)
        
        # Connect signals
        self.format_group.idClicked.connect(self._on_format_changed)
        self.button_box.accepted.connect(self._on_export)
        self.button_box.rejected.connect(self.reject)
        
    def _apply_styles(self):
        """Apply consistent styling to the dialog."""
        # Apply warm color theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {StyleManager.COLORS['background']};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {StyleManager.COLORS['border']};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {StyleManager.COLORS['primary']};
            }}
            QPushButton {{
                background-color: {StyleManager.COLORS['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {StyleManager.COLORS['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {StyleManager.COLORS['secondary']};
            }}
            QProgressBar {{
                border: 2px solid {StyleManager.COLORS['border']};
                border-radius: 5px;
                text-align: center;
                background-color: white;
            }}
            QProgressBar::chunk {{
                background-color: {StyleManager.COLORS['primary']};
                border-radius: 3px;
            }}
        """)
        
    def _on_format_changed(self, button_id: int):
        """Handle format selection change."""
        self.options_stack.setCurrentIndex(button_id)
        
    def _on_export(self):
        """Handle export button click."""
        # Get file path
        file_filter = "JSON files (*.json)" if self.json_radio.isChecked() else "PDF files (*.pdf)"
        default_ext = ".json" if self.json_radio.isChecked() else ".pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Journal Entries",
            f"journal_export_{datetime.now().strftime('%Y%m%d')}{default_ext}",
            file_filter
        )
        
        if not file_path:
            return
            
        # Ensure proper extension
        if not file_path.endswith(default_ext):
            file_path += default_ext
            
        # Get entries for date range
        start_date, end_date = self.date_range_selector.get_date_range()
        
        try:
            entries = JournalDAO.get_journal_entries(start_date, end_date)
            
            if not entries:
                QMessageBox.warning(
                    self,
                    "No Entries",
                    "No journal entries found in the selected date range."
                )
                return
                
            # Start export
            self._start_export(entries, file_path)
            
        except Exception as e:
            logger.error(f"Error preparing export: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to prepare export: {str(e)}"
            )
            
    def _start_export(self, entries: List[JournalEntry], file_path: str):
        """Start the export process."""
        # Show progress
        self.progress_widget.setVisible(True)
        self.button_box.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Create appropriate exporter
        if self.json_radio.isChecked():
            options = ExportOptions(
                **self.json_options.get_options()
            )
            exporter = JSONExporter(options)
            self.progress_label.setText("Exporting to JSON...")
        else:
            options = ExportOptions(
                extra_options=self.pdf_options.get_options()
            )
            exporter = PDFExporter(options)
            self.progress_label.setText("Generating PDF...")
            
        # Create and start worker thread
        self.export_worker = ExportWorker(exporter, entries, file_path, self)
        self.export_worker.progress.connect(self._on_progress)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_export_error)
        self.export_worker.start()
        
    def _on_progress(self, value: float):
        """Handle progress updates."""
        self.progress_bar.setValue(int(value))
        
    def _on_export_finished(self, result: ExportResult):
        """Handle successful export completion."""
        self.export_result = result
        
        # Show success message
        size_kb = result.file_size / 1024
        message = (
            f"Successfully exported {result.entries_exported} entries.\n\n"
            f"File: {os.path.basename(result.file_path)}\n"
            f"Size: {size_kb:.1f} KB\n"
            f"Time: {result.export_duration:.1f} seconds"
        )
        
        if result.warnings:
            message += "\n\nWarnings:\n" + "\n".join(f"• {w}" for w in result.warnings)
            
        reply = QMessageBox.information(
            self,
            "Export Complete",
            message,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open,
            QMessageBox.StandardButton.Ok
        )
        
        # Open file location if requested
        if reply == QMessageBox.StandardButton.Open:
            folder = os.path.dirname(result.file_path)
            if os.path.exists(folder):
                import subprocess
                subprocess.Popen(f'explorer "{folder}"', shell=True)
                
        self.accept()
        
    def _on_export_error(self, error_message: str):
        """Handle export error."""
        self.progress_widget.setVisible(False)
        self.button_box.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Export Failed",
            f"Failed to export journal entries:\n\n{error_message}"
        )
        
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop any running export
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.terminate()
            self.export_worker.wait()
            
        super().closeEvent(event)