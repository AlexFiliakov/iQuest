#!/usr/bin/env python3
"""Test script for viewing the modernized import dialogs."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from src.ui.import_progress_dialog import ImportProgressDialog, ImportSummaryDialog
from src.ui.style_manager import StyleManager


class TestWindow(QMainWindow):
    """Test window for showing dialogs."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Test")
        self.setFixedSize(400, 300)
        
        # Apply style
        self.style_manager = StyleManager()
        self.setStyleSheet(self.style_manager.get_main_window_style())
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Button to show import dialog
        import_btn = QPushButton("Show Import Progress Dialog")
        import_btn.setStyleSheet(self.style_manager.get_button_style("primary"))
        import_btn.clicked.connect(self.show_import_dialog)
        layout.addWidget(import_btn)
        
        # Button to show success dialog
        success_btn = QPushButton("Show Import Success Dialog")
        success_btn.setStyleSheet(self.style_manager.get_button_style("secondary"))
        success_btn.clicked.connect(self.show_success_dialog)
        layout.addWidget(success_btn)
        
        layout.addStretch()
    
    def show_import_dialog(self):
        """Show the import progress dialog."""
        dialog = ImportProgressDialog("test_export.xml", "xml", self)
        
        # Simulate progress updates
        def update_progress():
            current = dialog.progress_bar.value()
            if current < 100:
                new_value = min(current + 10, 100)
                dialog._on_progress_updated(new_value, f"Processing records... {new_value}%", new_value * 100)
                if new_value < 100:
                    QTimer.singleShot(500, update_progress)
                else:
                    # Show completion
                    result = {
                        'record_count': 10000,
                        'import_type': 'xml',
                        'import_time': 12.5,
                        'file_path': 'test_export.xml'
                    }
                    dialog._on_import_completed(result)
        
        dialog.start_import()
        QTimer.singleShot(500, update_progress)
        dialog.exec()
    
    def show_success_dialog(self):
        """Show the import success dialog directly."""
        result = {
            'record_count': 10000,
            'import_type': 'xml',
            'import_time': 12.5,
            'file_path': 'test_export.xml'
        }
        dialog = ImportSummaryDialog(result, self)
        dialog.exec()


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Apply global style
    style_manager = StyleManager()
    style_manager.apply_global_style(app)
    
    # Show test window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()