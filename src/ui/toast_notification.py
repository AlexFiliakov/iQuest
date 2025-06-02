"""Toast notification system for user feedback.

This module provides a modern toast notification system for the Apple Health
Monitor application. Toast notifications are semi-transparent, animated popups
that appear in the corner of the application to provide non-intrusive feedback
to users about operations, errors, and status updates.

The notification system supports:
    - Multiple notification types (success, warning, error, info)
    - Automatic stacking of multiple notifications
    - Smooth slide-in and fade-out animations
    - Click-to-dismiss functionality
    - Auto-hide after configurable duration
    - Icon support for visual distinction
    - Customizable colors and styling

Key features:
    - Non-blocking user feedback
    - Queueing system for multiple notifications
    - Smooth animations for professional appearance
    - Accessibility support with proper contrast
    - Memory-efficient with automatic cleanup

Example:
    Basic usage:
    
    >>> toast = ToastNotification.success("Entry saved successfully!")
    >>> toast.show()
    
    With parent widget and position:
    
    >>> toast = ToastNotification.error(
    ...     "Failed to save entry",
    ...     parent=main_window,
    ...     duration=5000
    ... )
    
    Custom notification:
    
    >>> toast = ToastNotification(
    ...     "Custom message",
    ...     notification_type=ToastNotification.Type.INFO,
    ...     icon_path="path/to/icon.png",
    ...     duration=3000
    ... )
"""

from typing import Optional, List, ClassVar
from enum import Enum
import weakref

from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QRect, QPoint,
    QEasingCurve, pyqtSignal, QParallelAnimationGroup,
    QSequentialAnimationGroup
)
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QColor, QMouseEvent

from .style_manager import StyleManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ToastNotification(QWidget):
    """Modern toast notification widget with animations and stacking.
    
    This widget provides non-intrusive notifications that appear in the corner
    of the application window. Multiple notifications stack vertically with
    smooth animations. Each notification auto-hides after a duration but can
    also be dismissed by clicking.
    
    Attributes:
        Type (Enum): Notification types (SUCCESS, WARNING, ERROR, INFO)
        clicked (pyqtSignal): Emitted when notification is clicked
        closed (pyqtSignal): Emitted when notification closes
    """
    
    class Type(Enum):
        """Notification types with associated colors."""
        SUCCESS = ("#95C17B", "✓")  # Green
        WARNING = ("#FFD166", "⚠")  # Yellow
        ERROR = ("#E76F51", "✕")    # Red
        INFO = ("#6C9BD1", "ℹ")     # Blue
        
    # Class variables for managing notifications
    _active_notifications: ClassVar[List[weakref.ref]] = []
    _notification_spacing: ClassVar[int] = 10
    _edge_margin: ClassVar[int] = 20
    
    # Signals
    clicked = pyqtSignal()
    closed = pyqtSignal()
    
    def __init__(
        self,
        message: str,
        notification_type: Type = Type.INFO,
        parent: Optional[QWidget] = None,
        duration: int = 3000,
        icon_path: Optional[str] = None
    ):
        """Initialize the toast notification.
        
        Args:
            message: The notification message to display
            notification_type: Type of notification (affects color and icon)
            parent: Parent widget (defaults to main window)
            duration: Duration in milliseconds before auto-hide (0 = no auto-hide)
            icon_path: Optional path to custom icon
        """
        # Find parent if not provided
        if parent is None:
            app = QApplication.instance()
            if app:
                parent = app.activeWindow()
                
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.icon_path = icon_path
        self._is_hovered = False
        self._opacity = 0.95
        
        # Setup UI
        self.setup_ui()
        
        # Setup animations
        self.setup_animations()
        
        # Configure widget
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Add to active notifications
        self._register_notification()
        
        # Auto-hide timer
        if self.duration > 0:
            self.hide_timer = QTimer()
            self.hide_timer.timeout.connect(self.hide_animated)
            self.hide_timer.setSingleShot(True)
            
    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        
        # Icon label
        self.icon_label = QLabel()
        color, symbol = self.notification_type.value
        self.icon_label.setText(symbol)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 20px;
                font-weight: bold;
            }}
        """)
        main_layout.addWidget(self.icon_label)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        main_layout.addWidget(self.message_label, 1)
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.hide_animated)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        main_layout.addWidget(self.close_button)
        
        # Set size constraints
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
    def setup_animations(self):
        """Set up the animation effects."""
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Slide animation
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        
        # Show animation group
        self.show_animation = QParallelAnimationGroup()
        self.show_animation.addAnimation(self.slide_animation)
        self.show_animation.addAnimation(self.fade_animation)
        
        # Hide animation
        self.hide_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hide_animation.setDuration(200)
        self.hide_animation.setStartValue(self._opacity)
        self.hide_animation.setEndValue(0)
        self.hide_animation.finished.connect(self._on_hide_finished)
        
    def paintEvent(self, event):
        """Paint the notification background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, 8, 8)
        
        # Draw shadow
        shadow_color = QColor(0, 0, 0, 50)
        painter.fillPath(path.translated(2, 2), shadow_color)
        
        # Draw background
        color, _ = self.notification_type.value
        bg_color = QColor(color)
        painter.fillPath(path, bg_color)
        
    def show(self):
        """Show the notification with animation."""
        # Calculate position
        self._calculate_position()
        
        # Set initial state
        self.opacity_effect.setOpacity(0)
        
        # Configure show animation
        self.slide_animation.setStartValue(self.pos() + QPoint(50, 0))
        self.slide_animation.setEndValue(self.pos())
        
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(self._opacity)
        
        # Show widget
        super().show()
        
        # Start animation
        self.show_animation.start()
        
        # Start auto-hide timer
        if hasattr(self, 'hide_timer'):
            self.hide_timer.start(self.duration)
            
        logger.debug(f"Showing {self.notification_type.name} notification: {self.message}")
        
    def hide_animated(self):
        """Hide the notification with animation."""
        if hasattr(self, 'hide_timer'):
            self.hide_timer.stop()
            
        self.hide_animation.start()
        
    def _on_hide_finished(self):
        """Handle hide animation completion."""
        self._unregister_notification()
        self.closed.emit()
        self.hide()
        self.deleteLater()
        
    def _calculate_position(self):
        """Calculate the position for this notification."""
        if not self.parent():
            return
            
        parent_rect = self.parent().rect()
        
        # Start from top-right corner
        x = parent_rect.right() - self.width() - self._edge_margin
        y = self._edge_margin
        
        # Adjust for other notifications
        active_notifications = self._get_active_notifications()
        for notif in active_notifications:
            if notif is not self and notif.isVisible():
                y = max(y, notif.y() + notif.height() + self._notification_spacing)
                
        self.move(x, y)
        
    def _register_notification(self):
        """Register this notification in the active list."""
        self._active_notifications.append(weakref.ref(self))
        self._cleanup_notifications()
        
    def _unregister_notification(self):
        """Remove this notification from the active list."""
        self._active_notifications = [
            ref for ref in self._active_notifications
            if ref() is not None and ref() is not self
        ]
        self._reposition_notifications()
        
    def _cleanup_notifications(self):
        """Remove dead references from the notification list."""
        self._active_notifications = [
            ref for ref in self._active_notifications
            if ref() is not None
        ]
        
    def _get_active_notifications(self) -> List['ToastNotification']:
        """Get list of active notification objects."""
        self._cleanup_notifications()
        return [ref() for ref in self._active_notifications if ref() is not None]
        
    def _reposition_notifications(self):
        """Reposition all active notifications after one is removed."""
        active = self._get_active_notifications()
        y = self._edge_margin
        
        for notif in active:
            if notif.isVisible():
                # Animate to new position
                anim = QPropertyAnimation(notif, b"pos")
                anim.setDuration(200)
                anim.setStartValue(notif.pos())
                anim.setEndValue(QPoint(notif.x(), y))
                anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
                anim.start()
                
                y += notif.height() + self._notification_spacing
                
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            self.hide_animated()
            
    def enterEvent(self, event):
        """Handle mouse enter events."""
        self._is_hovered = True
        if hasattr(self, 'hide_timer'):
            self.hide_timer.stop()
            
        # Slightly increase opacity on hover
        self.opacity_effect.setOpacity(1.0)
        
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self._is_hovered = False
        if hasattr(self, 'hide_timer') and self.duration > 0:
            # Restart timer with remaining time
            self.hide_timer.start(1000)  # Give 1 second after hover
            
        # Restore normal opacity
        self.opacity_effect.setOpacity(self._opacity)
        
    @classmethod
    def success(cls, message: str, parent: Optional[QWidget] = None, 
                duration: int = 3000) -> 'ToastNotification':
        """Create and return a success notification.
        
        Args:
            message: Success message to display
            parent: Parent widget
            duration: Auto-hide duration in milliseconds
            
        Returns:
            ToastNotification: Configured success notification
        """
        return cls(message, cls.Type.SUCCESS, parent, duration)
        
    @classmethod
    def error(cls, message: str, parent: Optional[QWidget] = None,
              duration: int = 5000) -> 'ToastNotification':
        """Create and return an error notification.
        
        Args:
            message: Error message to display
            parent: Parent widget
            duration: Auto-hide duration in milliseconds (longer for errors)
            
        Returns:
            ToastNotification: Configured error notification
        """
        return cls(message, cls.Type.ERROR, parent, duration)
        
    @classmethod
    def warning(cls, message: str, parent: Optional[QWidget] = None,
                duration: int = 4000) -> 'ToastNotification':
        """Create and return a warning notification.
        
        Args:
            message: Warning message to display
            parent: Parent widget
            duration: Auto-hide duration in milliseconds
            
        Returns:
            ToastNotification: Configured warning notification
        """
        return cls(message, cls.Type.WARNING, parent, duration)
        
    @classmethod
    def info(cls, message: str, parent: Optional[QWidget] = None,
             duration: int = 3000) -> 'ToastNotification':
        """Create and return an info notification.
        
        Args:
            message: Info message to display
            parent: Parent widget
            duration: Auto-hide duration in milliseconds
            
        Returns:
            ToastNotification: Configured info notification
        """
        return cls(message, cls.Type.INFO, parent, duration)