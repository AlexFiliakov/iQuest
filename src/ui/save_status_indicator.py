"""Save status indicator widget for visual feedback on auto-save operations.

This module provides a visual indicator widget that displays the current save
status of journal entries. It shows different states with appropriate icons
and animations to provide non-intrusive feedback to users.

The SaveStatusIndicator integrates with the AutoSaveManager to display:
    - Idle state when no changes are pending
    - Modified state when content has changed
    - Saving state with spinner animation
    - Saved state with timestamp
    - Error state with clickable details

Visual design follows the warm color palette with subtle animations for
state transitions and appropriate icons for each state.

Example:
    Basic usage with auto-save manager:
    
    >>> status_indicator = SaveStatusIndicator()
    >>> auto_save_manager.statusChanged.connect(status_indicator.set_status)
    >>> 
    >>> # Add to layout
    >>> status_bar_layout.addWidget(status_indicator)
    
    Manual status updates:
    
    >>> status_indicator.set_status("Saving...")
    >>> status_indicator.set_saved_status(QDateTime.currentDateTime())
    >>> status_indicator.set_error_status("Network error", "Could not connect")
"""

from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton,
    QGraphicsOpacityEffect, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QDateTime, QSize
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QMovie

from ..utils.logging_config import get_logger
from .style_manager import StyleManager

logger = get_logger(__name__)


class SpinnerWidget(QLabel):
    """Animated spinner widget for save-in-progress indication.
    
    This widget displays a rotating spinner animation to indicate
    that a save operation is in progress.
    """
    
    def __init__(self, size: int = 16, parent: Optional[QWidget] = None):
        """Initialize the spinner widget.
        
        Args:
            size: Size of the spinner in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        
        # Create spinner animation
        self.movie = QMovie()  # We'll create a simple spinner programmatically
        self.rotation = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        """Start the spinner animation."""
        self.timer.start(50)  # 20 FPS
        self.show()
        
    def stop(self):
        """Stop the spinner animation."""
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        """Rotate the spinner."""
        self.rotation = (self.rotation + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Move to center
        painter.translate(self.size // 2, self.size // 2)
        painter.rotate(self.rotation)
        
        # Draw spinner arcs
        pen_width = 2
        radius = (self.size - pen_width) // 2
        
        # Draw partial circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FF8C42"))
        
        for i in range(8):
            angle = i * 45
            opacity = 1.0 - (i * 0.1)
            painter.setOpacity(opacity)
            painter.save()
            painter.rotate(angle)
            painter.drawEllipse(-pen_width//2, -radius, pen_width, pen_width)
            painter.restore()


class SaveStatusIndicator(QWidget):
    """Visual indicator for save status with animations and error handling.
    
    This widget provides clear visual feedback about the save status of
    journal entries, including animations between states and clickable
    error details.
    
    Attributes:
        errorClicked (pyqtSignal): Emitted when error icon is clicked
    
    States:
        - Idle: No icon, empty text
        - Modified: "●" icon, "Modified" text
        - Saving: Spinner animation, "Saving..." text
        - Saved: "✓" icon, "Saved at HH:MM" text
        - Error: "⚠" icon, "Save failed" text (clickable)
    """
    
    errorClicked = pyqtSignal()
    
    # Status states
    IDLE = "idle"
    MODIFIED = "modified"
    SAVING = "saving"
    SAVED = "saved"
    ERROR = "error"
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the save status indicator.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.current_state = self.IDLE
        self.error_details = ""
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Icon/spinner container
        self.icon_container = QWidget()
        self.icon_container.setFixedSize(20, 20)
        icon_layout = QHBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status icon
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.status_icon)
        
        # Spinner (hidden by default)
        self.spinner = SpinnerWidget(16)
        self.spinner.hide()
        icon_layout.addWidget(self.spinner)
        
        layout.addWidget(self.icon_container)
        
        # Status text
        self.status_text = QLabel()
        self.status_text.setFont(QFont("Inter", 11))
        layout.addWidget(self.status_text)
        
        # Error button (hidden by default)
        self.error_button = QToolButton()
        self.error_button.setIcon(self._create_icon("ℹ", QColor("#5D4E37")))
        self.error_button.setToolTip("Click for error details")
        self.error_button.clicked.connect(self.show_error_details)
        self.error_button.hide()
        layout.addWidget(self.error_button)
        
        # Apply base styling
        self.setStyleSheet("""
            SaveStatusIndicator {
                background-color: transparent;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel {
                color: #8B7355;
                background-color: transparent;
            }
            QToolButton {
                border: none;
                background-color: transparent;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: rgba(139, 115, 85, 0.1);
                border-radius: 4px;
            }
        """)
        
    def setup_animations(self):
        """Set up fade animations for smooth transitions."""
        # Opacity effect for the widget
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def set_status(self, status_text: str):
        """Set status based on text from auto-save manager.
        
        Args:
            status_text: Status text (e.g., "Modified", "Saving...", "Saved at HH:MM")
        """
        if status_text == "Modified":
            self.set_modified_status()
        elif status_text == "Saving...":
            self.set_saving_status()
        elif status_text.startswith("Saved at"):
            # Extract time from status text
            self.set_saved_status(QDateTime.currentDateTime())
        elif status_text == "Save failed":
            self.set_error_status("Save failed", self.error_details)
        elif status_text in ["Auto-save disabled", "Auto-save enabled"]:
            self.set_idle_status()
            self.status_text.setText(status_text)
        else:
            self.set_idle_status()
            
    def set_idle_status(self):
        """Set idle status (no changes)."""
        self._transition_to_state(self.IDLE)
        self.status_icon.clear()
        self.status_icon.show()
        self.spinner.stop()
        self.status_text.clear()
        self.error_button.hide()
        self.error_details = ""
        
    def set_modified_status(self):
        """Set modified status (unsaved changes)."""
        self._transition_to_state(self.MODIFIED)
        self.status_icon.setText("●")
        self.status_icon.setStyleSheet("color: #F4A261;")  # Orange dot
        self.status_icon.show()
        self.spinner.stop()
        self.status_text.setText("Modified")
        self.status_text.setStyleSheet("color: #F4A261;")
        self.error_button.hide()
        
    def set_saving_status(self):
        """Set saving status (save in progress)."""
        self._transition_to_state(self.SAVING)
        self.status_icon.hide()
        self.spinner.start()
        self.status_text.setText("Saving...")
        self.status_text.setStyleSheet("color: #8B7355;")
        self.error_button.hide()
        
    def set_saved_status(self, save_time: QDateTime):
        """Set saved status with timestamp.
        
        Args:
            save_time: Time when the save completed
        """
        self._transition_to_state(self.SAVED)
        self.status_icon.setText("✓")
        self.status_icon.setStyleSheet("color: #95C17B;")  # Green checkmark
        self.status_icon.show()
        self.spinner.stop()
        self.status_text.setText(f"Saved at {save_time.toString('HH:mm')}")
        self.status_text.setStyleSheet("color: #95C17B;")
        self.error_button.hide()
        
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self._fade_to_idle)
        
    def set_error_status(self, error_text: str, details: str = ""):
        """Set error status with optional details.
        
        Args:
            error_text: Brief error description
            details: Detailed error information
        """
        self._transition_to_state(self.ERROR)
        self.status_icon.setText("⚠")
        self.status_icon.setStyleSheet("color: #E76F51;")  # Red warning
        self.status_icon.show()
        self.spinner.stop()
        self.status_text.setText(error_text)
        self.status_text.setStyleSheet("color: #E76F51;")
        
        self.error_details = details
        if details:
            self.error_button.show()
        else:
            self.error_button.hide()
            
    def show_error_details(self):
        """Show detailed error information in a dialog."""
        if self.error_details:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Save Error Details")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText("The journal entry could not be saved.")
            msg_box.setDetailedText(self.error_details)
            msg_box.exec()
            
        self.errorClicked.emit()
        
    def _transition_to_state(self, new_state: str):
        """Transition to a new state with animation.
        
        Args:
            new_state: The new state to transition to
        """
        if new_state == self.current_state:
            return
            
        # Fade out
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.3)
        self.fade_animation.finished.connect(lambda: self._complete_transition(new_state))
        self.fade_animation.start()
        
    def _complete_transition(self, new_state: str):
        """Complete the state transition after fade out.
        
        Args:
            new_state: The new state to apply
        """
        self.current_state = new_state
        
        # Fade back in
        self.fade_animation.finished.disconnect()  # Disconnect previous connection
        self.fade_animation.setStartValue(0.3)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
    def _fade_to_idle(self):
        """Fade to idle state after saved status."""
        if self.current_state == self.SAVED:
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self.set_idle_status)
            self.fade_animation.start()
            
    def _create_icon(self, text: str, color: QColor) -> QIcon:
        """Create a simple text-based icon.
        
        Args:
            text: Text to display in icon
            color: Text color
            
        Returns:
            QIcon: Generated icon
        """
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(color)
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return QIcon(pixmap)