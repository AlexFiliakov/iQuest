#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import os
import sys

# 1. Locate project root (one level up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 2. Prepend it so 'src' package can be found when running from inside src/
sys.path.insert(0, project_root)

import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QProxyStyle, QStyle

from src.ui.main_window import MainWindow
from src.ui.style_manager import StyleManager
from src.utils.error_handler import ConfigurationError, ErrorContext
from src.utils.logging_config import get_logger, setup_logging

# Initialize logging for the application
logger = setup_logging(log_level="INFO")
module_logger = get_logger(__name__)


def exception_hook(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them and showing user-friendly error dialog.

    This function replaces the default Python exception handler to provide
    better error reporting for the GUI application. It logs all exceptions
    and shows user-friendly error dialogs when the application is running.

    Args:
        exc_type: The exception type.
        exc_value: The exception instance.
        exc_traceback: The traceback object.

    Note:
        KeyboardInterrupt exceptions are passed through to the default handler.
    """
    # Don't handle KeyboardInterrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception
    module_logger.critical(
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
    """Run the application.

    This is the main entry point for the Apple Health Monitor Dashboard.
    It initializes the Qt application, applies styling, creates the main
    window, and starts the event loop.

    The function handles application-level configuration including:
    - Setting application metadata
    - Configuring tooltip timing
    - Applying global styling
    - Creating and showing the main window
    - Starting the Qt event loop

    Raises:
        SystemExit: If the application fails to start or encounters a critical error.
    """
    try:
        module_logger.info("Starting Apple Health Monitor Dashboard")
        
        # PyQt6 handles high DPI scaling automatically
        # Set the rounding policy for fractional scale factors
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        app = QApplication(sys.argv)

        # install proxy style to customize tooltip delays
        class TooltipDelayStyle(QProxyStyle):
            def styleHint(self, hint, option=None, widget=None, returnData=None):
                if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
                    return 700
                if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
                    return 10000
                return super().styleHint(hint, option, widget, returnData)

        app.setStyle(TooltipDelayStyle(app.style()))

        # Set application metadata
        from src.config import APP_NAME, ORGANIZATION_NAME
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORGANIZATION_NAME)

        # Apply global styling
        style_manager = StyleManager()
        style_manager.apply_global_style(app)

        # Create and show main window
        with ErrorContext("Creating main window"):
            window = MainWindow()
            window.show()

        module_logger.info("Application started successfully")
        sys.exit(app.exec())

    except Exception as e:
        module_logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
