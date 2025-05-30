"""Settings manager for persisting application state using QSettings."""

from PyQt6.QtCore import QSettings, QPoint, QSize, Qt
from PyQt6.QtWidgets import QMainWindow
from ..utils.logging_config import get_logger
from ..config import ORGANIZATION_NAME, APP_NAME

logger = get_logger(__name__)


class SettingsManager:
    """Manages application settings persistence using QSettings."""
    
    def __init__(self):
        """Initialize the settings manager."""
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        logger.info(f"SettingsManager initialized for {ORGANIZATION_NAME}/{APP_NAME}")
        logger.debug(f"Settings storage location: {self.settings.fileName()}")
    
    def save_window_state(self, window: QMainWindow):
        """Save the main window state including geometry and tab.
        
        Args:
            window: The main window instance to save state from
        """
        try:
            # Save window geometry
            self.settings.beginGroup("MainWindow")
            self.settings.setValue("geometry", window.saveGeometry())
            self.settings.setValue("windowState", window.saveState())
            self.settings.setValue("position", window.pos())
            self.settings.setValue("size", window.size())
            self.settings.setValue("maximized", window.isMaximized())
            
            # Save last active tab
            if hasattr(window, 'tab_widget'):
                self.settings.setValue("lastActiveTab", window.tab_widget.currentIndex())
                logger.debug(f"Saved active tab index: {window.tab_widget.currentIndex()}")
            
            self.settings.endGroup()
            self.settings.sync()
            
            logger.info("Window state saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save window state: {e}")
    
    def restore_window_state(self, window: QMainWindow):
        """Restore the main window state including geometry and tab.
        
        Args:
            window: The main window instance to restore state to
        """
        try:
            self.settings.beginGroup("MainWindow")
            
            # Restore window geometry with screen bounds checking
            geometry = self.settings.value("geometry")
            if geometry:
                window.restoreGeometry(geometry)
                logger.debug("Restored window geometry from settings")
            else:
                # Use default size and center on screen
                window.resize(
                    self.settings.value("size", QSize(1440, 900)),
                )
                self._center_window(window)
                logger.debug("Using default window size")
            
            # Restore window state (including toolbar positions if any)
            state = self.settings.value("windowState")
            if state:
                window.restoreState(state)
            
            # Handle maximized state
            was_maximized = self.settings.value("maximized", False, type=bool)
            if was_maximized:
                window.showMaximized()
                logger.debug("Restored maximized state")
            
            # Restore last active tab
            if hasattr(window, 'tab_widget'):
                last_tab = self.settings.value("lastActiveTab", 0, type=int)
                # Validate tab index and default to Configuration tab (0) if invalid
                if 0 <= last_tab < window.tab_widget.count():
                    try:
                        # Check if the tab widget exists and is accessible
                        tab_widget = window.tab_widget.widget(last_tab)
                        if tab_widget is not None:
                            window.tab_widget.setCurrentIndex(last_tab)
                            logger.debug(f"Restored active tab to index: {last_tab}")
                        else:
                            # Tab widget is None, default to Configuration
                            window.tab_widget.setCurrentIndex(0)
                            logger.warning(f"Tab at index {last_tab} is not accessible, defaulting to Configuration tab")
                    except Exception as e:
                        # Any error, default to Configuration tab
                        window.tab_widget.setCurrentIndex(0)
                        logger.error(f"Error restoring tab {last_tab}: {e}, defaulting to Configuration tab")
                else:
                    # Invalid tab index, default to Configuration
                    window.tab_widget.setCurrentIndex(0)
                    logger.warning(f"Invalid tab index {last_tab}, defaulting to Configuration tab")
            
            self.settings.endGroup()
            
            # Validate screen bounds after restoration
            self._validate_screen_bounds(window)
            
            logger.info("Window state restored successfully")
            
        except Exception as e:
            logger.error(f"Failed to restore window state: {e}")
            # Fall back to defaults
            window.resize(1440, 900)
            self._center_window(window)
    
    def _center_window(self, window: QMainWindow):
        """Center the window on the primary screen.
        
        Args:
            window: The window to center
        """
        from PyQt6.QtGui import QScreen
        
        screen = window.screen()
        if not screen:
            # Get primary screen
            app = window.windowHandle().screen()
            if app:
                screen = app
        
        if screen:
            geometry = screen.availableGeometry()
            window.move(
                (geometry.width() - window.width()) // 2 + geometry.x(),
                (geometry.height() - window.height()) // 2 + geometry.y()
            )
            logger.debug(f"Centered window on screen at {window.pos()}")
    
    def _validate_screen_bounds(self, window: QMainWindow):
        """Ensure window is visible on available screens.
        
        Args:
            window: The window to validate
        """
        from PyQt6.QtGui import QScreen
        from PyQt6.QtWidgets import QApplication
        
        # Get the window's current position and size
        pos = window.pos()
        size = window.size()
        window_rect = window.geometry()
        
        # Check if window is visible on any screen
        app = QApplication.instance()
        if not app:
            return
            
        screens = app.screens()
        is_visible = False
        
        for screen in screens:
            screen_rect = screen.availableGeometry()
            if screen_rect.intersects(window_rect):
                is_visible = True
                break
        
        if not is_visible:
            # Window is off-screen, move it to primary screen
            logger.warning("Window was off-screen, moving to primary screen")
            primary_screen = app.primaryScreen()
            if primary_screen:
                screen_rect = primary_screen.availableGeometry()
                
                # Adjust position to fit within screen bounds
                new_x = max(screen_rect.x(), min(pos.x(), screen_rect.right() - size.width()))
                new_y = max(screen_rect.y(), min(pos.y(), screen_rect.bottom() - size.height()))
                
                window.move(new_x, new_y)
                logger.debug(f"Moved window to {new_x}, {new_y}")
    
    def clear_settings(self):
        """Clear all saved settings."""
        self.settings.clear()
        self.settings.sync()
        logger.info("All settings cleared")
    
    def get_setting(self, key: str, default_value=None):
        """Get a specific setting value.
        
        Args:
            key: The setting key
            default_value: Value to return if key doesn't exist
            
        Returns:
            The setting value or default_value
        """
        return self.settings.value(key, default_value)
    
    def set_setting(self, key: str, value):
        """Set a specific setting value.
        
        Args:
            key: The setting key
            value: The value to store
        """
        self.settings.setValue(key, value)
        self.settings.sync()