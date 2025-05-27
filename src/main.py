#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Health Monitor Dashboard")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add placeholder label
        label = QLabel("Apple Health Monitor Dashboard\n\nComing Soon!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #FF8C42;
                padding: 50px;
            }
        """)
        layout.addWidget(label)


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Apple Health Monitor")
    app.setOrganizationName("Apple Health Monitor Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()