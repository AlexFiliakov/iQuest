"""Feedback collection dialog for Apple Health Monitor.

This module provides a user-friendly dialog for collecting feedback, bug reports,
and feature requests directly from within the application. It supports different
feedback types and can optionally include system information.

Example:
    >>> dialog = FeedbackDialog(parent_window)
    >>> if dialog.exec() == QDialog.DialogCode.Accepted:
    ...     feedback_data = dialog.get_feedback_data()
    ...     print(f"Received {feedback_data['type']} feedback")
"""

from typing import Dict, Optional, Any
import platform
import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTextEdit, QLineEdit, QPushButton, QCheckBox, QGroupBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices

from src.version import __version__


class FeedbackDialog(QDialog):
    """Dialog for collecting user feedback.
    
    Provides a structured form for users to submit feedback, including:
    - Feedback type (bug report, feature request, general feedback)
    - Detailed description
    - Contact information (optional)
    - System information (optional)
    
    Attributes:
        feedback_submitted (pyqtSignal): Emitted when feedback is submitted
    """
    
    feedback_submitted = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the feedback dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Send Feedback")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("We'd love to hear from you!")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Feedback type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Feedback Type:"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Bug Report",
            "Feature Request",
            "General Feedback",
            "Performance Issue",
            "Documentation"
        ])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_text = QTextEdit()
        self.description_text.setPlaceholderText(
            "Please describe your feedback in detail...\n\n"
            "For bug reports, include:\n"
            "- What you were doing when the issue occurred\n"
            "- What you expected to happen\n"
            "- What actually happened\n"
            "- Steps to reproduce the issue"
        )
        self.description_text.setMinimumHeight(200)
        layout.addWidget(self.description_text)
        
        # Contact info (optional)
        contact_group = QGroupBox("Contact Information (Optional)")
        contact_layout = QVBoxLayout(contact_group)
        
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        email_layout.addWidget(self.email_input)
        contact_layout.addLayout(email_layout)
        
        self.allow_contact = QCheckBox("You may contact me about this feedback")
        contact_layout.addWidget(self.allow_contact)
        
        layout.addWidget(contact_group)
        
        # System info
        self.include_system_info = QCheckBox("Include system information")
        self.include_system_info.setChecked(True)
        self.include_system_info.setToolTip(
            "Includes: OS version, app version, Python version"
        )
        layout.addWidget(self.include_system_info)
        
        # Privacy note
        privacy_note = QLabel(
            "📌 Your privacy is important to us. Feedback is sent directly to "
            "GitHub Issues or via email. No personal health data is included."
        )
        privacy_note.setWordWrap(True)
        privacy_note.setStyleSheet("color: #666; font-size: 11px; margin: 10px 0;")
        layout.addWidget(privacy_note)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._submit_feedback)
        button_box.rejected.connect(self.reject)
        
        # Add GitHub button
        github_button = QPushButton("Open GitHub Issues")
        github_button.clicked.connect(self._open_github)
        button_box.addButton(github_button, QDialogButtonBox.ButtonRole.HelpRole)
        
        layout.addWidget(button_box)
        
    def _connect_signals(self):
        """Connect widget signals."""
        self.type_combo.currentTextChanged.connect(self._update_placeholder)
        
    def _update_placeholder(self, feedback_type: str):
        """Update description placeholder based on feedback type."""
        placeholders = {
            "Bug Report": (
                "Please describe the bug in detail...\n\n"
                "1. What were you doing when the issue occurred?\n"
                "2. What did you expect to happen?\n"
                "3. What actually happened?\n"
                "4. Can you reproduce the issue? If so, how?\n"
                "5. Any error messages?"
            ),
            "Feature Request": (
                "Please describe the feature you'd like to see...\n\n"
                "1. What problem would this feature solve?\n"
                "2. How would you like it to work?\n"
                "3. Have you seen this in other applications?\n"
                "4. How important is this feature to you?"
            ),
            "General Feedback": (
                "Share your thoughts about Apple Health Monitor...\n\n"
                "What do you like? What could be improved?\n"
                "How has it helped you understand your health data?"
            ),
            "Performance Issue": (
                "Please describe the performance issue...\n\n"
                "1. What operation is slow?\n"
                "2. How long does it take?\n"
                "3. How much data do you have?\n"
                "4. When did this start happening?"
            ),
            "Documentation": (
                "Help us improve our documentation...\n\n"
                "1. What information were you looking for?\n"
                "2. What was unclear or missing?\n"
                "3. What would have been helpful?"
            )
        }
        
        self.description_text.setPlaceholderText(
            placeholders.get(feedback_type, "Please provide your feedback...")
        )
        
    def _get_system_info(self) -> Dict[str, str]:
        """Collect system information.
        
        Returns:
            Dictionary containing system information
        """
        return {
            "app_version": __version__,
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "timestamp": datetime.now().isoformat()
        }
        
    def get_feedback_data(self) -> Dict[str, Any]:
        """Get the complete feedback data.
        
        Returns:
            Dictionary containing all feedback information
        """
        data = {
            "type": self.type_combo.currentText(),
            "description": self.description_text.toPlainText(),
            "email": self.email_input.text() if self.allow_contact.isChecked() else "",
            "allow_contact": self.allow_contact.isChecked(),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.include_system_info.isChecked():
            data["system_info"] = self._get_system_info()
            
        return data
        
    def _validate_feedback(self) -> bool:
        """Validate the feedback form.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.description_text.toPlainText().strip():
            QMessageBox.warning(
                self,
                "Missing Description",
                "Please provide a description of your feedback."
            )
            return False
            
        if self.allow_contact.isChecked() and not self.email_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing Email",
                "Please provide an email address or uncheck 'You may contact me'."
            )
            return False
            
        return True
        
    def _submit_feedback(self):
        """Handle feedback submission."""
        if not self._validate_feedback():
            return
            
        feedback_data = self.get_feedback_data()
        
        # In a real implementation, this would send to a server or create a GitHub issue
        # For now, we'll show a success message and emit the signal
        self.feedback_submitted.emit(feedback_data)
        
        QMessageBox.information(
            self,
            "Thank You!",
            "Your feedback has been recorded. We appreciate you taking the time "
            "to help improve Apple Health Monitor.\n\n"
            "For immediate assistance, please visit our GitHub Issues page."
        )
        
        self.accept()
        
    def _open_github(self):
        """Open GitHub issues page in browser."""
        url = "https://github.com/yourusername/apple-health-monitor/issues"
        QDesktopServices.openUrl(QUrl(url))


class FeedbackButton(QPushButton):
    """Convenience button for opening feedback dialog.
    
    Can be easily added to any window or toolbar.
    
    Example:
        >>> feedback_btn = FeedbackButton(main_window)
        >>> toolbar.addWidget(feedback_btn)
    """
    
    def __init__(self, parent=None):
        """Initialize the feedback button.
        
        Args:
            parent: Parent widget
        """
        super().__init__("Send Feedback", parent)
        self.setToolTip("Send feedback, report bugs, or request features")
        self.clicked.connect(self._show_feedback_dialog)
        
    def _show_feedback_dialog(self):
        """Show the feedback dialog."""
        dialog = FeedbackDialog(self.window())
        dialog.feedback_submitted.connect(self._handle_feedback)
        dialog.exec()
        
    def _handle_feedback(self, feedback_data: Dict[str, Any]):
        """Handle submitted feedback.
        
        Args:
            feedback_data: The feedback data dictionary
        """
        # In a real implementation, this would send the feedback
        # to a server or create a GitHub issue via API
        print(f"Feedback received: {feedback_data['type']}")
        
        # Log feedback locally for now
        # This could be extended to save to a local file or database
        # for later batch submission