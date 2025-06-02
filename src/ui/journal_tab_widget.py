"""Journal tab widget combining editor and history views.

This module provides the main journal tab interface that integrates:
- Journal editor for creating/editing entries
- History view for browsing past entries
- Search functionality
- Export capabilities

Classes:
    JournalTabWidget: Main container for journal functionality

Example:
    >>> from src.data_access import DataAccess
    >>> data_access = DataAccess("health.db")
    >>> journal_tab = JournalTabWidget(data_access)
    >>> journal_tab.show()
"""

import logging
from typing import Optional
from datetime import date

from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtGui import QIcon

from src.data_access import DataAccess
from src.ui.journal_editor_widget import JournalEditorWidget
from src.ui.journal_history_widget import JournalHistoryWidget
from src.ui.journal_search_widget import JournalSearchWidget
from src.ui.style_manager import ColorPalette, StyleManager

# Create alias for backward compatibility
ThemeColors = ColorPalette()
FONTS = {
    'DEFAULT_FAMILY': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
}

logger = logging.getLogger(__name__)


class JournalTabWidget(QWidget):
    """Main journal tab widget integrating editor and history.
    
    Provides a split view with history list on the left and editor on the right,
    along with search and export functionality.
    
    Attributes:
        data_access: Database access interface
        journal_editor: Editor widget for creating/editing entries
        history_widget: History view for browsing entries
        search_widget: Search functionality
        style_manager: StyleManager instance for consistent styling
    """
    
    def __init__(self, data_access: DataAccess, parent=None):
        """Initialize journal tab widget.
        
        Args:
            data_access: DataAccess instance for database operations
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.data_access = data_access
        self.style_manager = StyleManager()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header toolbar
        header = self._create_header()
        layout.addWidget(header)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - History view
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Search widget
        self.search_widget = JournalSearchWidget()
        left_layout.addWidget(self.search_widget)
        
        # History widget
        self.history_widget = JournalHistoryWidget(self.data_access)
        left_layout.addWidget(self.history_widget, 1)
        
        splitter.addWidget(left_container)
        
        # Right side - Editor
        self.journal_editor = JournalEditorWidget(self.data_access)
        splitter.addWidget(self.journal_editor)
        
        # Set splitter sizes (40% history, 60% editor)
        splitter.setSizes([400, 600])
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
    def _create_header(self) -> QWidget:
        """Create header toolbar.
        
        Returns:
            Header widget with title and actions
        """
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.surface};
                border-bottom: 2px solid {ThemeColors.border};
                padding: 12px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        
        # Title
        title = QLabel("📔 Health Journal")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {ThemeColors.text_primary};
                font-family: {FONTS['DEFAULT_FAMILY']};
            }}
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # New entry button
        new_btn = QPushButton("New Entry")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.primary};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: {FONTS['DEFAULT_FAMILY']};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.primary_hover};
            }}
        """)
        new_btn.clicked.connect(self.create_new_entry)
        layout.addWidget(new_btn)
        
        return header
        
    def connect_signals(self):
        """Connect widget signals."""
        # History selection
        self.history_widget.entrySelected.connect(self.load_entry)
        self.history_widget.entryDeleted.connect(self.on_entry_deleted)
        
        # Search results
        self.search_widget.searchResultSelected.connect(self.load_entry)
        
        # Editor save
        self.journal_editor.entrySaved.connect(self.on_entry_saved)
        
    def create_new_entry(self):
        """Create a new journal entry."""
        # Clear editor and set to today's date
        self.journal_editor.clear_editor()
        self.journal_editor.set_date(QDate.currentDate())
        self.journal_editor.content_editor.setFocus()
        
    def load_entry(self, entry_id: int):
        """Load entry into editor.
        
        Args:
            entry_id: ID of entry to load
        """
        try:
            entry = self.data_access.journal_db.get_entry(entry_id)
            if entry:
                self.journal_editor.load_entry(entry)
        except Exception as e:
            logger.error(f"Error loading entry {entry_id}: {e}")
            
    def on_entry_saved(self):
        """Handle entry saved event."""
        # Refresh history view
        self.history_widget.refresh()
        
        # Clear search if active
        self.search_widget.clear_search()
        
    def on_entry_deleted(self, entry_id: int):
        """Handle entry deleted event.
        
        Args:
            entry_id: ID of deleted entry
        """
        # Clear editor if showing deleted entry
        if (self.journal_editor.current_entry and 
            self.journal_editor.current_entry.id == entry_id):
            self.journal_editor.clear_editor()
            
        # Refresh history
        self.history_widget.refresh()
        
    def refresh(self):
        """Refresh all components."""
        self.history_widget.refresh()
        self.search_widget.clear_search()