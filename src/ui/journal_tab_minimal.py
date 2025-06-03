"""Minimal journal tab widget for testing."""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class JournalTabMinimal(QWidget):
    """Minimal journal tab without dependencies."""
    
    def __init__(self, data_access=None, parent=None):
        """Initialize minimal journal tab."""
        logger.info("JournalTabMinimal: Starting __init__")
        super().__init__(parent)
        logger.info("JournalTabMinimal: Parent constructor called")
        
        self.data_access = data_access
        self._setup_ui()
        logger.info("JournalTabMinimal: Initialization complete")
        
    def _setup_ui(self):
        """Set up the minimal UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📔 Health Journal (Minimal)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # Simple text editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Write your journal entry here...")
        layout.addWidget(self.editor)
        
        # Save button
        save_btn = QPushButton("Save Entry")
        save_btn.setStyleSheet("padding: 10px; font-size: 16px;")
        layout.addWidget(save_btn)
        
        layout.addStretch()