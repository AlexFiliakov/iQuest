"""Conflict resolution dialog for journal entry conflicts.

This module provides a dialog for resolving conflicts when multiple users or
sessions attempt to modify the same journal entry. It displays both versions
side-by-side and allows the user to choose which version to keep or cancel
the operation.

The dialog provides:
    - Side-by-side comparison of conflicting content
    - Clear visual distinction between versions
    - Options to keep either version or cancel
    - Diff highlighting (if content is similar)
    - Entry metadata display (last modified time)

Example:
    >>> dialog = ConflictResolutionDialog(
    ...     current_content="Original entry text",
    ...     new_content="Modified entry text",
    ...     entry_date=date.today(),
    ...     entry_type='daily',
    ...     parent=main_window
    ... )
    >>> 
    >>> result = dialog.exec()
    >>> if result == ConflictResolutionDialog.KeepMine:
    ...     # User chose to keep their version
    ...     save_content(new_content)
"""

from typing import Optional
from datetime import date, datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialogButtonBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QTextCharFormat, QColor

from .style_manager import StyleManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ConflictResolutionDialog(QDialog):
    """Dialog for resolving journal entry conflicts.
    
    This dialog presents two versions of a journal entry side-by-side and
    allows the user to choose which version to keep. It's designed to handle
    concurrent edit conflicts gracefully.
    
    Attributes:
        KeepTheirs (int): Result code for keeping the current/database version
        KeepMine (int): Result code for keeping the new/local version
        Cancel (int): Result code for cancelling the operation
    """
    
    # Result codes
    KeepTheirs = 1
    KeepMine = 2
    Cancel = 0
    
    def __init__(
        self,
        current_content: str,
        new_content: str,
        entry_date: date,
        entry_type: str,
        current_updated: Optional[datetime] = None,
        parent: Optional['QWidget'] = None
    ):
        """Initialize the conflict resolution dialog.
        
        Args:
            current_content: The content currently in the database
            new_content: The new content attempting to be saved
            entry_date: The date of the journal entry
            entry_type: The type of journal entry
            current_updated: When the current version was last updated
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.current_content = current_content
        self.new_content = new_content
        self.entry_date = entry_date
        self.entry_type = entry_type
        self.current_updated = current_updated
        self.style_manager = StyleManager()
        
        self.setup_ui()
        self.highlight_differences()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Journal Entry Conflict")
        self.setModal(True)
        self.resize(800, 600)
        
        # Apply styling
        self.setStyleSheet(self.style_manager.get_dialog_style())
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header_label = QLabel(
            f"Conflict detected for {self.entry_type} entry on {self.entry_date}\n"
            "Another version of this entry exists. Please choose which version to keep:"
        )
        header_label.setWordWrap(True)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #5D4E37;
                padding: 8px;
                background-color: #FFF5E6;
                border: 1px solid #E8DCC8;
                border-radius: 4px;
            }
        """)
        layout.addWidget(header_label)
        
        # Content comparison
        content_layout = QHBoxLayout()
        
        # Current version (from database)
        current_frame = self.create_version_frame(
            "Current Version (from database)",
            self.current_content,
            self.current_updated
        )
        self.current_text_edit = current_frame.findChild(QTextEdit)
        content_layout.addWidget(current_frame)
        
        # New version (local changes)
        new_frame = self.create_version_frame(
            "Your Version (new changes)",
            self.new_content,
            datetime.now()
        )
        self.new_text_edit = new_frame.findChild(QTextEdit)
        content_layout.addWidget(new_frame)
        
        layout.addLayout(content_layout, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Keep current button
        keep_current_btn = QPushButton("Keep Current Version")
        keep_current_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C9BD1;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5A89C1;
            }
        """)
        keep_current_btn.clicked.connect(self.keep_current)
        button_layout.addWidget(keep_current_btn)
        
        # Keep new button
        keep_new_btn = QPushButton("Keep My Version")
        keep_new_btn.setStyleSheet("""
            QPushButton {
                background-color: #95C17B;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #85B16B;
            }
        """)
        keep_new_btn.clicked.connect(self.keep_new)
        button_layout.addWidget(keep_new_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8DCC8;
                color: #5D4E37;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #D8CCB8;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def create_version_frame(
        self,
        title: str,
        content: str,
        updated_time: Optional[datetime]
    ) -> QFrame:
        """Create a frame for displaying a version of the content.
        
        Args:
            title: The frame title
            content: The content to display
            updated_time: When this version was last updated
            
        Returns:
            QFrame: The configured frame widget
        """
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #5D4E37;
                padding: 4px;
            }
        """)
        layout.addWidget(title_label)
        
        # Timestamp
        if updated_time:
            time_label = QLabel(f"Last modified: {updated_time.strftime('%Y-%m-%d %H:%M:%S')}")
            time_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #8B7B65;
                    padding: 4px;
                }
            """)
            layout.addWidget(time_label)
            
        # Content
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont('Inter', 12))
        text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E8DCC8;
                border-radius: 4px;
                padding: 8px;
                background-color: #FAFAFA;
            }
        """)
        layout.addWidget(text_edit)
        
        # Stats
        char_count = len(content)
        word_count = len(content.split()) if content.strip() else 0
        stats_label = QLabel(f"{char_count:,} characters • {word_count:,} words")
        stats_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #8B7B65;
                padding: 4px;
            }
        """)
        layout.addWidget(stats_label)
        
        return frame
        
    def highlight_differences(self):
        """Highlight the differences between the two versions."""
        # Simple word-based diff highlighting
        current_words = self.current_content.split()
        new_words = self.new_content.split()
        
        # Find common prefix and suffix
        prefix_len = 0
        suffix_len = 0
        
        min_len = min(len(current_words), len(new_words))
        
        # Find common prefix
        for i in range(min_len):
            if current_words[i] == new_words[i]:
                prefix_len = i + 1
            else:
                break
                
        # Find common suffix
        for i in range(min_len - prefix_len):
            if current_words[-(i+1)] == new_words[-(i+1)]:
                suffix_len = i + 1
            else:
                break
                
        # Highlight different sections
        if prefix_len < len(current_words) - suffix_len:
            # There are differences to highlight
            self._apply_highlighting(
                self.current_text_edit,
                current_words,
                prefix_len,
                len(current_words) - suffix_len
            )
            
        if prefix_len < len(new_words) - suffix_len:
            self._apply_highlighting(
                self.new_text_edit,
                new_words,
                prefix_len,
                len(new_words) - suffix_len
            )
            
    def _apply_highlighting(
        self,
        text_edit: QTextEdit,
        words: list,
        start_idx: int,
        end_idx: int
    ):
        """Apply highlighting to different sections.
        
        Args:
            text_edit: The text edit widget to highlight
            words: List of words in the content
            start_idx: Start index of differences
            end_idx: End index of differences
        """
        # Create format for highlighting
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFE4B5"))  # Light orange
        
        # Calculate character positions
        char_start = len(' '.join(words[:start_idx])) + (1 if start_idx > 0 else 0)
        char_end = len(' '.join(words[:end_idx]))
        
        # Apply formatting
        cursor = text_edit.textCursor()
        cursor.setPosition(char_start)
        cursor.setPosition(char_end, cursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(highlight_format)
        
    def keep_current(self):
        """User chose to keep the current version."""
        logger.info(f"User chose to keep current version for {self.entry_type} entry on {self.entry_date}")
        self.done(self.KeepTheirs)
        
    def keep_new(self):
        """User chose to keep the new version."""
        logger.info(f"User chose to keep new version for {self.entry_type} entry on {self.entry_date}")
        self.done(self.KeepMine)
        
    def get_choice(self) -> str:
        """Get the user's choice as a string.
        
        Returns:
            str: 'keep_theirs', 'keep_mine', or 'cancel'
        """
        result = self.result()
        if result == self.KeepTheirs:
            return 'keep_theirs'
        elif result == self.KeepMine:
            return 'keep_mine'
        else:
            return 'cancel'