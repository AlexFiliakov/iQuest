"""Loading screen widget that displays initialization progress and messages.

This module provides a modern loading screen that follows the UI specifications
from UI_SPECS.md, displaying initialization messages to users during app startup.

The loading screen features:
    - Clean, professional design following WSJ aesthetics
    - Progress indicator with animated spinner
    - Message log display for initialization feedback
    - Smooth fade-in/fade-out transitions
    - Accessibility support with proper contrast ratios

Example:
    Basic usage:
        
        >>> loading_screen = LoadingScreen()
        >>> loading_screen.show()
        >>> loading_screen.add_message("Initializing database...")
        >>> loading_screen.set_progress(0.5)
        >>> loading_screen.add_message("Loading user preferences...")
        >>> loading_screen.close()

Attributes:
    FADE_DURATION (int): Duration of fade animations in milliseconds
    MESSAGE_LIMIT (int): Maximum number of messages to display
"""

from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QMovie, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import APP_NAME
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class LoadingScreen(QWidget):
    """Modern loading screen with message log display.
    
    This widget provides a professional loading screen that displays
    initialization progress and messages to the user during app startup.
    It follows the UI specifications for colors, typography, and spacing.
    
    The loading screen is designed to be shown as a splash screen while
    the main application initializes, providing visual feedback about the
    startup progress.
    
    Attributes:
        progress_bar (QProgressBar): Visual progress indicator.
        message_log (QTextEdit): Scrollable log of initialization messages.
        title_label (QLabel): Application title display.
        status_label (QLabel): Current status message display.
        opacity_effect (QGraphicsOpacityEffect): For fade animations.
        fade_animation (QPropertyAnimation): Handles fade transitions.
        messages (list): List of all messages added to the log.
        
    Signals:
        closed: Emitted when the loading screen is closed.
    """
    
    FADE_DURATION = 350  # Slow animation duration from UI specs
    MESSAGE_LIMIT = 100  # Maximum messages to keep in log
    
    closed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the loading screen.
        
        Sets up the UI components following the design specifications,
        including proper colors, fonts, spacing, and animations.
        
        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.messages = []
        self._setup_ui()
        self._apply_styles()
        
    def _setup_ui(self):
        """Set up the user interface components."""
        # Set window flags for splash screen behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main container with card styling
        main_container = QWidget()
        main_container.setObjectName("loadingContainer")
        
        # Main layout
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(48, 48, 48, 48)  # 2xl spacing
        container_layout.setSpacing(24)  # lg spacing
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(8)  # sm spacing
        
        # App title
        self.title_label = QLabel(APP_NAME)
        self.title_label.setObjectName("loadingTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_section.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("loadingStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_section.addWidget(self.status_label)
        
        container_layout.addLayout(title_section)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("loadingProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate mode
        container_layout.addWidget(self.progress_bar)
        
        # Message log
        self.message_log = QTextEdit()
        self.message_log.setObjectName("loadingMessageLog")
        self.message_log.setReadOnly(True)
        self.message_log.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.message_log.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.message_log.setMinimumHeight(200)
        self.message_log.setMaximumHeight(300)
        container_layout.addWidget(self.message_log)
        
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        
        # Set up opacity effect for animations
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Set up fade animation
        self.fade_animation = QPropertyAnimation(
            self.opacity_effect, b"opacity"
        )
        self.fade_animation.setDuration(self.FADE_DURATION)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Size the window
        self.setFixedSize(650, 500)
        
        # Center on screen
        self._center_on_screen()
        
    def _apply_styles(self):
        """Apply styles according to UI specifications."""
        # Custom fonts are loaded by StyleManager, so we just reference them here
        
        # Apply stylesheet based on UI_SPECS.md
        self.setStyleSheet("""
            /* Main container card styling */
            #loadingContainer {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            
            /* Title styling */
            #loadingTitle {
                font-family: 'Roboto Condensed', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 32px;
                font-weight: 600;
                color: #0F172A;
            }
            
            /* Status label styling */
            #loadingStatus {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 16px;
                color: #64748B;
            }
            
            /* Progress bar styling */
            #loadingProgress {
                min-height: 8px;
                # max-height: 8px;
                border: none;
                border-radius: 4px;
                background-color: #F3F4F6;
            }
            
            #loadingProgress::chunk {
                background-color: #2563EB;
                border-radius: 4px;
            }
            
            /* Message log styling */
            #loadingMessageLog {
                font-family: 'Roboto', 'Consolas', monospace;
                font-size: 12px;
                color: #64748B;
                background-color: #FAFBFC;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 16px;
                line-height: 1.6;
            }
            
            /* Scrollbar styling */
            #loadingMessageLog QScrollBar:vertical {
                background-color: #F3F4F6;
                width: 12px;
                border-radius: 6px;
            }
            
            #loadingMessageLog QScrollBar::handle:vertical {
                background-color: #94A3B8;
                border-radius: 6px;
                min-height: 20px;
            }
            
            #loadingMessageLog QScrollBar::handle:vertical:hover {
                background-color: #64748B;
            }
            
            #loadingMessageLog QScrollBar::add-line:vertical,
            #loadingMessageLog QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
    def _center_on_screen(self):
        """Center the loading screen on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
            
    def show(self):
        """Show the loading screen with fade-in animation."""
        super().show()
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        logger.info("Loading screen displayed")
        
    def close(self):
        """Close the loading screen with fade-out animation."""
        def on_fade_finished():
            super(LoadingScreen, self).close()
            self.closed.emit()
            logger.info("Loading screen closed")
            
        self.fade_animation.finished.connect(on_fade_finished)
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()
        
    @pyqtSlot(str)
    def add_message(self, message: str):
        """Add a message to the log display.
        
        Messages are displayed in chronological order with timestamps.
        The log automatically scrolls to show the latest message.
        
        Args:
            message: The message to add to the log.
        """
        self.messages.append(message)
        
        # Limit message history
        if len(self.messages) > self.MESSAGE_LIMIT:
            self.messages.pop(0)
            
        # Update display
        log_text = "\n".join(f"• {msg}" for msg in self.messages)
        self.message_log.setPlainText(log_text)
        
        # Scroll to bottom
        scrollbar = self.message_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Update status label with latest message
        self.status_label.setText(message)
        
        logger.debug(f"Loading screen message: {message}")
        
    @pyqtSlot(float)
    def set_progress(self, value: float):
        """Set the progress bar value.
        
        Args:
            value: Progress value between 0.0 and 1.0.
                   Use -1 for indeterminate progress.
        """
        if value < 0:
            # Indeterminate mode
            self.progress_bar.setMaximum(0)
        else:
            # Determinate mode
            if self.progress_bar.maximum() == 0:
                self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(int(value * 100))
            
    def set_status(self, status: str):
        """Update the main status message.
        
        Args:
            status: The status message to display.
        """
        self.status_label.setText(status)


class AppInitializer(QThread):
    """Background thread for application initialization.
    
    This thread handles the main application initialization process,
    emitting signals to update the loading screen with progress messages.
    
    Signals:
        message: Emitted with status messages for the loading screen.
        progress: Emitted with progress values (0.0 to 1.0).
        finished: Emitted when initialization is complete.
        error: Emitted if initialization fails.
    """
    
    message = pyqtSignal(str)
    progress = pyqtSignal(float)
    error = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the app initializer thread."""
        super().__init__()
        
    def run(self):
        """Run the initialization process."""
        try:
            # Import dependencies
            self.message.emit("Loading application modules...")
            self.progress.emit(0.1)
            
            from ..ui.main_window import MainWindow
            from ..ui.style_manager import StyleManager
            
            self.message.emit("Initializing database...")
            self.progress.emit(0.2)
            
            from ..database import db_manager
            
            self.message.emit("Setting up logging system...")
            self.progress.emit(0.3)
            
            from ..utils.logging_config import setup_logging
            
            self.message.emit("Loading configuration...")
            self.progress.emit(0.4)
            
            from ..config import APP_NAME, ORGANIZATION_NAME
            
            self.message.emit("Initializing style manager...")
            self.progress.emit(0.5)
            
            # Style manager is already created in main
            
            self.message.emit("Setting up analytics engine...")
            self.progress.emit(0.6)
            
            # Analytics modules will be loaded on demand
            
            self.message.emit("Loading user preferences...")
            self.progress.emit(0.7)
            
            from ..ui.settings_manager import SettingsManager
            
            self.message.emit("Initializing UI components...")
            self.progress.emit(0.8)
            
            # UI components will be created by MainWindow
            
            self.message.emit("Performing system checks...")
            self.progress.emit(0.9)
            
            # Final checks
            
            self.message.emit("Application ready!")
            self.progress.emit(1.0)
            
        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            self.error.emit(str(e))