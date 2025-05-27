#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from utils.logging_config import setup_logging, get_logger
from utils.error_handler import ErrorContext, ConfigurationError
from ui.main_window import MainWindow
from ui.style_manager import StyleManager

# Initialize logging for the application
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def exception_hook(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them and showing user-friendly error dialog."""
    # Don't handle KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the exception
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Format error message for user
    error_msg = f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}"
    detailed_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Show error dialog if QApplication exists
    if QApplication.instance():
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Application Error")
        msg_box.setText(error_msg)
        msg_box.setDetailedText(detailed_msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


# Install the exception hook
sys.excepthook = exception_hook




def main():
    """Run the application."""
    try:
        logger.info("Starting Apple Health Monitor Dashboard")
        
        app = QApplication(sys.argv)
        
        # Set application metadata
        from config import APP_NAME, ORGANIZATION_NAME
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORGANIZATION_NAME)
        
        # Apply global styling
        style_manager = StyleManager()
        style_manager.apply_global_style(app)
        
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