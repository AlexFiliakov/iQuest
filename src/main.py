#!/usr/bin/env python3
"""Main entry point for Apple Health Monitor Dashboard."""

import os
import sys
import argparse

# Fix Python path before any local imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Now import version
try:
    from version import __version__
except ImportError:
    from src.version import __version__

# For WSL environments, handle Qt platform plugins
if sys.platform.startswith('linux'):
    # WSL-specific Qt configuration
    if 'microsoft' in os.uname().release.lower() or 'WSL' in os.environ.get('WSL_DISTRO_NAME', ''):
        print("Running in WSL environment")
        # Force XCB platform and set library path for Qt plugins
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        os.environ['QT_DEBUG_PLUGINS'] = '1'  # Enable plugin debugging
        
        # Try to handle missing xcb-cursor library
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/usr/lib/x86_64-linux-gnu/qt6/plugins'
        
        # Disable Wayland
        os.environ.pop('WAYLAND_DISPLAY', None)
        
        print(f"Qt platform: {os.environ.get('QT_QPA_PLATFORM')}")
        print(f"Display: {os.environ.get('DISPLAY', 'Not set')}")

# Path already fixed at the top of the file

import traceback

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox, QProxyStyle, QStyle

from src.ui.loading_screen import AppInitializer, LoadingScreen
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Apple Health Monitor Dashboard')
    parser.add_argument('--version', action='version', 
                       version=f'Apple Health Monitor Dashboard v{__version__}')
    args = parser.parse_args()
    
    try:
        module_logger.info("Starting Apple Health Monitor Dashboard")
        
        # PyQt6 handles high DPI scaling automatically
        # Set the rounding policy for fractional scale factors
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        app = QApplication(sys.argv)
        
        # Prevent app from quitting when last window is closed
        app.setQuitOnLastWindowClosed(True)
        
        # Log when app is about to quit
        def on_about_to_quit():
            module_logger.info("Application is about to quit")
            import traceback
            module_logger.info("Quit stack trace:")
            for line in traceback.format_stack():
                module_logger.info(line.strip())
        
        app.aboutToQuit.connect(on_about_to_quit)

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
        
        # Variable to hold main window reference - made global to prevent garbage collection
        global main_window
        main_window = None
        
        # Keep reference to prevent any windows from being garbage collected
        app._windows = []
        
        # Define finish_initialization at the top level to ensure it stays in scope
        def finish_initialization():
            """Complete initialization and show main window."""
            global main_window
            module_logger.info("finish_initialization called")
            loading_screen.add_message("Your health adventure awaits, brave soul!")
            loading_screen.set_progress(1.0)
            
            # Close loading screen and show main window
            def show_main_window():
                global main_window
                module_logger.info(f"About to show main window: {main_window}")
                loading_screen.close()
                if main_window:
                    # Ensure main window is recognized as the primary window
                    main_window.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
                    
                    # Prevent premature app exit
                    app.setQuitOnLastWindowClosed(False)
                    
                    main_window.show()
                    main_window.raise_()  # Bring to front
                    main_window.activateWindow()  # Make it active
                    
                    # Re-enable quit on last window closed after showing
                    QTimer.singleShot(500, lambda: app.setQuitOnLastWindowClosed(True))
                    
                    module_logger.info("Main window shown successfully")
                    module_logger.info(f"Main window visible: {main_window.isVisible()}")
                    module_logger.info(f"Main window size: {main_window.size()}")
                    module_logger.info(f"Main window position: {main_window.pos()}")
                    module_logger.info(f"Top level windows: {[w.title() for w in app.topLevelWindows()]}")
                    
                    # Ensure the window is properly displayed
                    app.processEvents()
                    
                    # Check window status after a delay
                    def check_window_status():
                        if main_window:
                            module_logger.info(f"Window check - visible: {main_window.isVisible()}")
                            module_logger.info(f"Window check - active: {main_window.isActiveWindow()}")
                            module_logger.info(f"Window check - minimized: {main_window.isMinimized()}")
                            module_logger.info(f"App has {len(app.topLevelWindows())} top level windows")
                        else:
                            module_logger.error("Main window is None during status check!")
                    
                    QTimer.singleShot(1000, check_window_status)
                else:
                    module_logger.error("Main window is None!")
                    
            # Short delay to show completion
            QTimer.singleShot(300, show_main_window)
        
        def initialize_application():
            """Initialize the application in steps with loading feedback."""
            global main_window
            
            try:
                loading_screen.add_message("Teaching pixels how to look fabulous...")
                loading_screen.set_progress(0.1)
                try:
                    style_manager = StyleManager()
                except Exception as e:
                    module_logger.error(f"Failed to create StyleManager: {e}", exc_info=True)
                    loading_screen.add_message(f"ERROR: Failed to create StyleManager - {str(e)}")
                    raise
                app.processEvents()  # Allow UI to update
                
                loading_screen.add_message("Applying mystical CSS potions...")
                loading_screen.set_progress(0.15)
                style_manager.apply_global_style(app)
                app.processEvents()
                
                loading_screen.add_message("Waking up the sleeping data dragon...")
                loading_screen.set_progress(0.2)
                try:
                    from src.database import db_manager
                    module_logger.info(f"Database manager imported: {db_manager}")
                except Exception as e:
                    module_logger.error(f"Failed to import database manager: {e}", exc_info=True)
                    loading_screen.add_message(f"ERROR: Failed to import database - {str(e)}")
                    raise
                app.processEvents()
                
                loading_screen.add_message("Organizing the chaos of 1s and 0s...")
                loading_screen.set_progress(0.25)
                from src.models import JournalEntry, UserPreference
                app.processEvents()
                
                loading_screen.add_message("Teaching calculators to count past potato...")
                loading_screen.set_progress(0.3)
                from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
                app.processEvents()
                
                loading_screen.add_message("Summoning the monthly math spirits...")
                loading_screen.set_progress(0.35)
                from src.analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
                app.processEvents()
                
                loading_screen.add_message("Installing a photographic memory chip...")
                loading_screen.set_progress(0.4)
                from src.analytics.cache_manager import AnalyticsCacheManager
                app.processEvents()
                
                loading_screen.add_message("Training detectives to spot shenanigans...")
                loading_screen.set_progress(0.45)
                from src.analytics.anomaly_detection_system import AnomalyDetectionSystem
                app.processEvents()
                
                loading_screen.add_message("Assembling a panel of very judgmental health gurus...")
                loading_screen.set_progress(0.5)
                from src.analytics.health_score.health_score_calculator import HealthScoreCalculator
                app.processEvents()
                
                loading_screen.add_message("Giving buttons their morning coffee...")
                loading_screen.set_progress(0.55)
                from src.ui.charts import CalendarHeatmapComponent, LineChart
                from src.ui.configuration_tab import ConfigurationTab
                app.processEvents()
                
                loading_screen.add_message("Teaching charts to make Wall Street jealous...")
                loading_screen.set_progress(0.6)
                from src.ui.charts.wsj_health_visualization_suite import WSJHealthVisualizationSuite
                app.processEvents()
                
                loading_screen.add_message("Assembling a dashboard that judges your life choices...")
                loading_screen.set_progress(0.65)
                from src.ui.daily_dashboard_widget import DailyDashboardWidget
                from src.ui.monthly_dashboard_widget import MonthlyDashboardWidget
                from src.ui.weekly_dashboard_widget import WeeklyDashboardWidget
                app.processEvents()
                
                loading_screen.add_message("Building a bridge between you and your data...")
                loading_screen.set_progress(0.7)
                from src.data_access import DataAccess
                app.processEvents()
                
                loading_screen.add_message("🏰Constructing your personal health fortress...")
                loading_screen.set_progress(0.75)
                
                try:
                    with ErrorContext("Creating main window"):
                        main_window = MainWindow(initialization_callback=loading_screen.add_message)
                        module_logger.info(f"Main window created: {main_window}")
                        app._windows.append(main_window)  # Keep reference
                except Exception as e:
                    module_logger.error(f"Failed to create main window: {e}", exc_info=True)
                    loading_screen.add_message(f"ERROR: Failed to create main window - {str(e)}")
                    # Show error dialog
                    QMessageBox.critical(
                        None,
                        "Initialization Error",
                        f"Failed to create main window:\n\n{str(e)}\n\nPlease check the logs for more details."
                    )
                    raise
                    
                loading_screen.add_message("Putting the finishing touches on your destiny...")
                loading_screen.set_progress(0.9)
                
                module_logger.info("About to call finish_initialization")
                module_logger.info(f"Main window initialized: {main_window}")
                
                # Process events to ensure UI is responsive
                app.processEvents()
                
                # Add a direct call as a test
                module_logger.info("Calling finish_initialization directly")
                try:
                    finish_initialization()
                except Exception as e:
                    module_logger.error(f"Direct call failed: {e}", exc_info=True)
                    loading_screen.close()
                    QMessageBox.critical(None, "Error", f"Failed to show main window: {e}")
                    app.quit()
                
            except Exception as e:
                module_logger.error(f"Initialization failed: {e}", exc_info=True)
                loading_screen.add_message(f"FATAL ERROR: {str(e)}")
                
                # Show error dialog with full details
                error_details = traceback.format_exc()
                QMessageBox.critical(
                    None,
                    "Application Initialization Failed",
                    f"Failed to initialize application:\n\n{str(e)}\n\nCheck the logs for full details.",
                    QMessageBox.StandardButton.Ok
                )
                
                loading_screen.close()
                raise e
        
        # Start initialization after event loop begins
        def start_init():
            module_logger.info("Event loop started, beginning initialization")
            initialize_application()
        
        QTimer.singleShot(100, start_init)
        
        # Add logging to track app lifecycle
        def on_last_window_closed():
            module_logger.info("Last window closed signal received")
        
        app.lastWindowClosed.connect(on_last_window_closed)
        
        # Also log when app is about to quit (in addition to the earlier handler)
        def on_app_quit():
            module_logger.info("App quit signal received")
        app.aboutToQuit.connect(on_app_quit)
        
        module_logger.info("Starting application event loop")
        exit_code = app.exec()
        module_logger.info(f"Application event loop ended with code: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        module_logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
