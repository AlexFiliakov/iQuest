#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from utils.logging_config import setup_logging, get_logger
from utils.error_handler import ErrorContext, ConfigurationError

# Initialize logging for the application
setup_logging(log_level="INFO")
logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing main window")
        
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
        
        logger.debug("Main window initialization complete")


def main():
    """Run the application."""
    try:
        logger.info("Starting Apple Health Monitor Dashboard")
        
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("Apple Health Monitor")
        app.setOrganizationName("Apple Health Monitor Team")
        
        # Create and show main window
        with ErrorContext("Creating main window"):
            window = MainWindow()
            window.show()
        
        logger.info("Application started successfully")
        
        # Run the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()