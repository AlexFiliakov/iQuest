#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import os
import sys

# 1. Locate project root (one level up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 2. Prepend it so 'src' package can be found when running from inside src/
sys.path.insert(0, project_root)

import traceback

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox, QProxyStyle, QStyle

from src.ui.loading_screen import LoadingScreen, AppInitializer
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

        # Show loading screen
        loading_screen = LoadingScreen()
        loading_screen.show()
        
        # Process events to ensure loading screen is displayed
        app.processEvents()
        
        # Variable to hold main window reference
        window = None
        
        def initialize_application():
            """Initialize the application in steps with loading feedback."""
            nonlocal window
            
            try:
                loading_screen.add_message("Initializing style manager...")
                loading_screen.set_progress(0.1)
                style_manager = StyleManager()
                app.processEvents()  # Allow UI to update
                
                loading_screen.add_message("Applying global styles...")
                loading_screen.set_progress(0.15)
                style_manager.apply_global_style(app)
                app.processEvents()
                
                loading_screen.add_message("Initializing database connection...")
                loading_screen.set_progress(0.2)
                from src.database import db_manager
                app.processEvents()
                
                loading_screen.add_message("Setting up data models...")
                loading_screen.set_progress(0.25)
                from src.models import JournalEntry, UserPreference
                app.processEvents()
                
                loading_screen.add_message("Loading daily metrics calculator...")
                loading_screen.set_progress(0.3)
                from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
                app.processEvents()
                
                loading_screen.add_message("Loading monthly metrics calculator...")
                loading_screen.set_progress(0.35)
                from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
                app.processEvents()
                
                loading_screen.add_message("Initializing cache manager...")
                loading_screen.set_progress(0.4)
                from src.analytics.cache_manager import AnalyticsCacheManager
                app.processEvents()
                
                loading_screen.add_message("Loading anomaly detection system...")
                loading_screen.set_progress(0.45)
                from src.analytics.anomaly_detection_system import AnomalyDetectionSystem
                app.processEvents()
                
                loading_screen.add_message("Setting up health score calculator...")
                loading_screen.set_progress(0.5)
                from src.analytics.health_score.health_score_calculator import HealthScoreCalculator
                app.processEvents()
                
                loading_screen.add_message("Loading UI components...")
                loading_screen.set_progress(0.55)
                from src.ui.configuration_tab import ConfigurationTab
                from src.ui.charts import LineChart, CalendarHeatmapComponent
                app.processEvents()
                
                loading_screen.add_message("Initializing visualization system...")
                loading_screen.set_progress(0.6)
                from src.ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite
                app.processEvents()
                
                loading_screen.add_message("Loading dashboard components...")
                loading_screen.set_progress(0.65)
                from src.ui.daily_dashboard_widget import DailyDashboardWidget
                from src.ui.weekly_dashboard_widget import WeeklyDashboardWidget
                from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
                app.processEvents()
                
                loading_screen.add_message("Setting up data access layer...")
                loading_screen.set_progress(0.7)
                from src.data_access import DataAccess
                app.processEvents()
                
                loading_screen.add_message("Creating main window...")
                loading_screen.set_progress(0.75)
                
                with ErrorContext("Creating main window"):
                    window = MainWindow(initialization_callback=loading_screen.add_message)
                    
                loading_screen.add_message("Finalizing initialization...")
                loading_screen.set_progress(0.9)
                
                # Short delay to ensure users see the final message
                QTimer.singleShot(500, lambda: finish_initialization())
                
            except Exception as e:
                loading_screen.close()
                raise e
                
        def finish_initialization():
            """Complete initialization and show main window."""
            loading_screen.add_message("Application ready!")
            loading_screen.set_progress(1.0)
            
            # Close loading screen and show main window
            def show_main_window():
                loading_screen.close()
                if window:
                    window.show()
                    module_logger.info("Application started successfully")
                    
            # Short delay to show completion
            QTimer.singleShot(300, show_main_window)
        
        # Start initialization after event loop begins
        QTimer.singleShot(100, initialize_application)
        
        sys.exit(app.exec())

    except Exception as e:
        module_logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
