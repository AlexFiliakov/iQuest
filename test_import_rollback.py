#!/usr/bin/env python3
"""
Test script to verify import rollback functionality.
"""

import sys
import os
import sqlite3
import shutil
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QFileDialog
from PyQt6.QtCore import QTimer

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.import_progress_dialog import ImportProgressDialog
from src.config import DATA_DIR


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Select a file to test import rollback")
        layout.addWidget(self.status_label)
        
        btn_xml = QPushButton("Test XML Import Rollback")
        btn_xml.clicked.connect(lambda: self.test_import("xml"))
        layout.addWidget(btn_xml)
        
        btn_csv = QPushButton("Test CSV Import Rollback")
        btn_csv.clicked.connect(lambda: self.test_import("csv"))
        layout.addWidget(btn_csv)
        
        self.setLayout(layout)
        self.setWindowTitle("Import Rollback Test")
        self.resize(400, 200)
        
    def test_import(self, file_type):
        # Select file
        if file_type == "xml":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select XML File", "", "XML Files (*.xml)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select CSV File", "", "CSV Files (*.csv)"
            )
            
        if not file_path:
            return
            
        # Check initial database state
        db_path = os.path.join(DATA_DIR, 'health_monitor.db')
        initial_count = self.get_record_count(db_path)
        self.status_label.setText(f"Initial record count: {initial_count}")
        
        # Create import dialog
        dialog = ImportProgressDialog(file_path, file_type, self)
        
        # Auto-cancel after 3 seconds to test rollback
        QTimer.singleShot(3000, lambda: self.cancel_import(dialog))
        
        # Connect to completion/cancellation signals
        dialog.import_cancelled.connect(lambda: self.check_rollback(initial_count))
        dialog.import_completed.connect(lambda result: self.on_import_complete(result))
        
        # Start import
        dialog.exec()
        
    def cancel_import(self, dialog):
        """Programmatically cancel the import."""
        if dialog.cancel_button.isEnabled():
            self.status_label.setText("Cancelling import to test rollback...")
            dialog.cancel_button.click()
            
    def get_record_count(self, db_path):
        """Get current record count from database."""
        if not os.path.exists(db_path):
            return 0
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM health_records")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
            
    def check_rollback(self, initial_count):
        """Check if rollback was successful."""
        db_path = os.path.join(DATA_DIR, 'health_monitor.db')
        final_count = self.get_record_count(db_path)
        
        if final_count == initial_count:
            self.status_label.setText(
                f"✅ Rollback successful! Count remained at {initial_count}"
            )
        else:
            self.status_label.setText(
                f"❌ Rollback failed! Count changed from {initial_count} to {final_count}"
            )
            
    def on_import_complete(self, result):
        """Handle successful import."""
        self.status_label.setText(
            f"Import completed: {result.get('record_count', 0)} records"
        )


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()