"""
Import Progress Dialog for displaying real-time import progress.

This module provides a modal dialog that shows import progress with the ability
to cancel operations and display results.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from utils.logging_config import get_logger
from .style_manager import StyleManager
from .import_worker import ImportWorker

logger = get_logger(__name__)


class ImportProgressDialog(QDialog):
    """Dialog for displaying import progress with cancellation capability."""
    
    # Signals
    import_completed = pyqtSignal(dict)  # Emitted when import finishes successfully
    import_cancelled = pyqtSignal()     # Emitted when import is cancelled
    
    def __init__(self, file_path: str, import_type: str = "auto", parent=None):
        """
        Initialize the import progress dialog.
        
        Args:
            file_path: Path to the file being imported
            import_type: Type of import ("xml", "csv", or "auto")
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_path = file_path
        self.import_type = import_type
        self.worker = None
        self.start_time = None
        self.style_manager = StyleManager()
        
        # Setup dialog
        self._setup_dialog()
        self._create_ui()
        
        logger.info(f"ImportProgressDialog created for: {file_path}")
    
    def _setup_dialog(self):
        """Setup dialog properties."""
        self.setWindowTitle("Importing Health Data")
        self.setModal(True)
        self.setFixedSize(500, 300)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint
        )
        
        # Apply theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
            }}
        """)
    
    def _create_ui(self):
        """Create the dialog UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Importing Health Data")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #5D4E37;
                margin-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # File info
        file_info = QLabel(f"File: {Path(self.file_path).name}")
        file_info.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {self.style_manager.TEXT_SECONDARY};
                padding: 8px;
                background-color: {self.style_manager.TERTIARY_BG};
                border-radius: 6px;
            }}
        """)
        file_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(file_info)
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(12)
        
        # Progress label
        self.progress_label = QLabel("Preparing import...")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 500;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
        """)
        progress_layout.addWidget(self.progress_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                text-align: center;
                background-color: {self.style_manager.TERTIARY_BG};
                height: 24px;
                font-weight: 600;
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background-color: {self.style_manager.ACCENT_PRIMARY};
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Time and stats info
        self.stats_label = QLabel("Elapsed time: 00:00")
        self.stats_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        progress_layout.addWidget(self.stats_label)
        
        layout.addWidget(progress_frame)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel Import")
        self.cancel_button.setStyleSheet(self.style_manager.get_button_style("secondary"))
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Setup timer for elapsed time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_elapsed_time)
    
    def start_import(self):
        """Start the import process."""
        logger.info("Starting import process")
        
        # Create and setup worker
        self.worker = ImportWorker(self.file_path, self.import_type)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.import_completed.connect(self._on_import_completed)
        self.worker.import_error.connect(self._on_import_error)
        self.worker.finished.connect(self._on_worker_finished)
        
        # Start timer and worker
        from datetime import datetime
        self.start_time = datetime.now()
        self.timer.start(1000)  # Update every second
        self.worker.start()
        
        # Update UI
        self.progress_label.setText("Starting import...")
        self.cancel_button.setEnabled(True)
    
    def _on_progress_updated(self, percentage: int, message: str):
        """Handle progress updates from worker."""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        logger.debug(f"Import progress: {percentage}% - {message}")
    
    def _on_import_completed(self, result: Dict[str, Any]):
        """Handle successful import completion."""
        logger.info(f"Import completed successfully: {result}")
        
        # Stop timer
        self.timer.stop()
        
        # Update UI
        self.progress_bar.setValue(100)
        self.progress_label.setText("Import completed successfully!")
        self.cancel_button.setText("Close")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)
        
        # Show summary dialog
        self._show_import_summary(result)
        
        # Emit signal
        self.import_completed.emit(result)
    
    def _on_import_error(self, title: str, message: str):
        """Handle import errors."""
        logger.error(f"Import error: {title} - {message}")
        
        # Stop timer
        self.timer.stop()
        
        # Update UI
        self.progress_label.setText("Import failed!")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 500;
                color: {self.style_manager.ACCENT_ERROR};
            }}
        """)
        self.cancel_button.setText("Close")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.reject)
        
        # Show error dialog
        QMessageBox.critical(self, title, message)
    
    def _on_worker_finished(self):
        """Handle worker thread completion."""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        logger.debug("Import worker thread finished")
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.worker and self.worker.isRunning():
            logger.info("Cancelling import operation")
            
            # Cancel the worker
            self.worker.cancel_import()
            
            # Update UI
            self.progress_label.setText("Cancelling import...")
            self.cancel_button.setEnabled(False)
            
            # Set a timeout for force termination
            QTimer.singleShot(5000, self._force_cancel)
        else:
            self.reject()
    
    def _force_cancel(self):
        """Force cancel if worker doesn't respond."""
        if self.worker and self.worker.isRunning():
            logger.warning("Force terminating import worker")
            self.worker.terminate()
            self.worker.wait(2000)
        
        self.timer.stop()
        self.import_cancelled.emit()
        self.reject()
    
    def _update_elapsed_time(self):
        """Update the elapsed time display."""
        if self.start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.start_time
            minutes, seconds = divmod(elapsed.total_seconds(), 60)
            self.stats_label.setText(f"Elapsed time: {int(minutes):02d}:{int(seconds):02d}")
    
    def _show_import_summary(self, result: Dict[str, Any]):
        """Show import summary dialog."""
        summary_dialog = ImportSummaryDialog(result, self)
        summary_dialog.exec()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            # Ask user if they want to cancel the import
            reply = QMessageBox.question(
                self,
                "Cancel Import",
                "Import is still in progress. Do you want to cancel it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._on_cancel_clicked()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class ImportSummaryDialog(QDialog):
    """Dialog for displaying import results and statistics."""
    
    def __init__(self, result: Dict[str, Any], parent=None):
        """Initialize the import summary dialog."""
        super().__init__(parent)
        self.result = result
        self.style_manager = StyleManager()
        
        self._setup_dialog()
        self._create_ui()
    
    def _setup_dialog(self):
        """Setup dialog properties."""
        self.setWindowTitle("Import Summary")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Apply theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
            }}
        """)
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("✅ Import Completed Successfully!")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 700;
                color: {self.style_manager.ACCENT_SUCCESS};
                margin-bottom: 10px;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Statistics frame
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(12)
        
        # Statistics
        stats = [
            ("Records Imported", f"{self.result.get('record_count', 0):,}"),
            ("File Type", self.result.get('import_type', 'Unknown').upper()),
            ("Import Time", f"{self.result.get('import_time', 0):.1f} seconds"),
            ("File Size", self._format_file_size()),
        ]
        
        for label, value in stats:
            stat_row = QHBoxLayout()
            
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet(f"""
                QLabel {{
                    font-weight: 600;
                    color: {self.style_manager.TEXT_PRIMARY};
                }}
            """)
            stat_row.addWidget(label_widget)
            
            stat_row.addStretch()
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"""
                QLabel {{
                    color: {self.style_manager.ACCENT_PRIMARY};
                    font-weight: 600;
                }}
            """)
            stat_row.addWidget(value_widget)
            
            stats_layout.addLayout(stat_row)
        
        layout.addWidget(stats_frame)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet(self.style_manager.get_button_style("primary"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _format_file_size(self):
        """Format file size for display."""
        try:
            file_path = self.result.get('file_path', '')
            if file_path and os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                
                # Convert to appropriate unit
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} TB"
            else:
                return "Unknown"
        except Exception:
            return "Unknown"