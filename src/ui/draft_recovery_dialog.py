"""Draft recovery dialog for restoring unsaved journal entries.

This module provides a dialog for recovering draft journal entries that were
not properly saved due to application crashes or unexpected shutdowns. It
displays a list of recoverable drafts with previews and allows users to
recover, discard, or postpone the recovery.

The dialog integrates with the AutoSaveManager to find orphaned drafts and
provides a user-friendly interface for managing recovery options.

Key features:
    - Lists all recoverable drafts with metadata
    - Shows content preview for each draft
    - Provides options to recover, discard, or postpone
    - Supports batch operations on multiple drafts
    - Maintains recovery history

Example:
    Basic usage in journal editor:
    
    >>> recovery_dialog = DraftRecoveryDialog(drafts, parent=self)
    >>> result = recovery_dialog.exec()
    >>> if result == QDialog.DialogCode.Accepted:
    ...     recovered = recovery_dialog.get_recovered_drafts()
    ...     for draft in recovered:
    ...         self.restore_draft(draft)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox,
    QCheckBox, QDialogButtonBox, QSplitter, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QIcon

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class DraftItem(QListWidgetItem):
    """Custom list item for draft entries with metadata storage.
    
    Stores draft data and provides formatted display for the list widget.
    
    Attributes:
        draft_data (dict): The draft entry data
        is_selected (bool): Whether this draft is selected for recovery
    """
    
    def __init__(self, draft_data: Dict[str, Any]):
        """Initialize the draft item.
        
        Args:
            draft_data: Dictionary containing draft information
        """
        super().__init__()
        self.draft_data = draft_data
        self.is_selected = True  # Default to selected for recovery
        
        # Format display text
        entry_date = draft_data.get('entry_date', 'Unknown')
        entry_type = draft_data.get('entry_type', 'unknown').title()
        saved_at = draft_data.get('saved_at', '')
        
        # Parse and format saved_at timestamp
        if saved_at:
            try:
                dt = QDateTime.fromString(saved_at, Qt.DateFormat.ISODate)
                saved_str = dt.toString("MMM d, h:mm AP")
            except:
                saved_str = saved_at
        else:
            saved_str = "Unknown time"
            
        # Create display text
        display_text = f"{entry_type} - {entry_date}\nLast saved: {saved_str}"
        self.setText(display_text)
        
        # Add tooltip with more info
        content_preview = draft_data.get('content', '')[:100]
        if len(draft_data.get('content', '')) > 100:
            content_preview += "..."
        self.setToolTip(f"Preview: {content_preview}")
        
        # Style based on age
        self.update_style()
        
    def update_style(self):
        """Update item appearance based on selection state."""
        if self.is_selected:
            self.setCheckState(Qt.CheckState.Checked)
        else:
            self.setCheckState(Qt.CheckState.Unchecked)
            
    def toggle_selection(self):
        """Toggle the selection state of this draft."""
        self.is_selected = not self.is_selected
        self.update_style()


class DraftRecoveryDialog(QDialog):
    """Dialog for recovering unsaved journal drafts.
    
    Displays a list of recoverable drafts with previews and provides
    options to recover, discard, or postpone the recovery process.
    
    Attributes:
        drafts_recovered (pyqtSignal): Emitted when drafts are recovered
    
    Args:
        drafts (List[Dict]): List of draft entries to potentially recover
        parent (Optional[QWidget]): Parent widget
    """
    
    drafts_recovered = pyqtSignal(list)  # List of recovered draft data
    
    def __init__(self, drafts: List[Dict[str, Any]], parent: Optional[QWidget] = None):
        """Initialize the draft recovery dialog.
        
        Args:
            drafts: List of draft dictionaries with entry data
            parent: Parent widget
        """
        super().__init__(parent)
        self.drafts = drafts
        self.draft_items: List[DraftItem] = []
        self.setup_ui()
        self.populate_drafts()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Recover Unsaved Drafts")
        self.setMinimumSize(800, 600)
        
        # Apply warm color scheme
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF7F0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #5D4E37;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 6px;
                padding: 8px 16px;
                color: #5D4E37;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FFF5E6;
                border-color: #D4AF37;
            }
            QPushButton:pressed {
                background-color: #F5E6D3;
            }
            QPushButton#recoverButton {
                background-color: #FF8C42;
                color: white;
                border-color: #FF8C42;
            }
            QPushButton#recoverButton:hover {
                background-color: #FF7A2F;
            }
            QListWidget {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel("⚠")
        icon_label.setStyleSheet("font-size: 24px; color: #F4A261;")
        header_layout.addWidget(icon_label)
        
        header_text = QLabel(
            "Unsaved drafts were found from your previous session.\n"
            "Select which drafts you would like to recover:"
        )
        header_text.setWordWrap(True)
        header_layout.addWidget(header_text, 1)
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Draft list
        list_group = QGroupBox("Available Drafts")
        list_layout = QVBoxLayout(list_group)
        
        # Select all/none buttons
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_drafts)
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_drafts)
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(select_none_btn)
        select_layout.addStretch()
        list_layout.addLayout(select_layout)
        
        # Draft list
        self.draft_list = QListWidget()
        self.draft_list.itemClicked.connect(self.on_draft_clicked)
        self.draft_list.currentItemChanged.connect(self.on_draft_selected)
        list_layout.addWidget(self.draft_list)
        
        splitter.addWidget(list_group)
        
        # Right side: Preview
        preview_group = QGroupBox("Draft Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Metadata labels
        self.metadata_label = QLabel("Select a draft to preview")
        self.metadata_label.setStyleSheet("color: #8B7355; font-style: italic;")
        preview_layout.addWidget(self.metadata_label)
        
        # Content preview
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont('Inter', 12))
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_group)
        
        # Set splitter proportions (40% list, 60% preview)
        splitter.setSizes([320, 480])
        layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Later button
        later_btn = QPushButton("Ask Me Later")
        later_btn.setToolTip("Close without recovering drafts. You'll be asked again next time.")
        later_btn.clicked.connect(self.reject)
        button_layout.addWidget(later_btn)
        
        button_layout.addStretch()
        
        # Discard button
        discard_btn = QPushButton("Discard Selected")
        discard_btn.setToolTip("Permanently delete the selected drafts")
        discard_btn.clicked.connect(self.discard_selected)
        button_layout.addWidget(discard_btn)
        
        # Recover button
        recover_btn = QPushButton("Recover Selected")
        recover_btn.setObjectName("recoverButton")
        recover_btn.setToolTip("Recover the selected drafts")
        recover_btn.clicked.connect(self.recover_selected)
        button_layout.addWidget(recover_btn)
        
        layout.addLayout(button_layout)
        
    def populate_drafts(self):
        """Populate the draft list with available drafts."""
        self.draft_list.clear()
        self.draft_items.clear()
        
        for draft_data in self.drafts:
            item = DraftItem(draft_data)
            self.draft_items.append(item)
            self.draft_list.addItem(item)
            
        # Select first item if available
        if self.draft_items:
            self.draft_list.setCurrentRow(0)
            
    def on_draft_clicked(self, item: DraftItem):
        """Handle draft item click to toggle selection.
        
        Args:
            item: The clicked draft item
        """
        if isinstance(item, DraftItem):
            item.toggle_selection()
            
    def on_draft_selected(self, current: DraftItem, previous: Optional[DraftItem]):
        """Handle draft selection change to update preview.
        
        Args:
            current: The newly selected draft item
            previous: The previously selected draft item
        """
        if not isinstance(current, DraftItem):
            return
            
        # Update metadata display
        draft = current.draft_data
        entry_type = draft.get('entry_type', 'unknown').title()
        entry_date = draft.get('entry_date', 'Unknown')
        saved_at = draft.get('saved_at', '')
        word_count = len(draft.get('content', '').split())
        
        metadata_text = (
            f"{entry_type} Entry - {entry_date}\n"
            f"Words: {word_count:,} | "
            f"Last saved: {saved_at}"
        )
        self.metadata_label.setText(metadata_text)
        
        # Update content preview
        content = draft.get('content', '')
        self.preview_text.setPlainText(content)
        
    def select_all_drafts(self):
        """Select all drafts for recovery."""
        for item in self.draft_items:
            item.is_selected = True
            item.update_style()
            
    def select_no_drafts(self):
        """Deselect all drafts."""
        for item in self.draft_items:
            item.is_selected = False
            item.update_style()
            
    def get_selected_drafts(self) -> List[Dict[str, Any]]:
        """Get list of drafts selected for recovery.
        
        Returns:
            List of draft dictionaries that are selected
        """
        selected = []
        for item in self.draft_items:
            if item.is_selected:
                selected.append(item.draft_data)
        return selected
        
    def recover_selected(self):
        """Recover the selected drafts and close dialog."""
        selected = self.get_selected_drafts()
        if selected:
            self.drafts_recovered.emit(selected)
            logger.info(f"Recovering {len(selected)} drafts")
            self.accept()
        else:
            # No drafts selected, just close
            self.reject()
            
    def discard_selected(self):
        """Discard the selected drafts permanently."""
        selected = self.get_selected_drafts()
        if not selected:
            return
            
        # Remove selected items from the list
        for item in self.draft_items[:]:  # Copy list to avoid modification during iteration
            if item.is_selected:
                row = self.draft_list.row(item)
                self.draft_list.takeItem(row)
                self.draft_items.remove(item)
                
        # Clear preview if no items left
        if not self.draft_items:
            self.metadata_label.setText("No drafts available")
            self.preview_text.clear()
            
        logger.info(f"Discarded {len(selected)} drafts")
        
    def get_recovered_drafts(self) -> List[Dict[str, Any]]:
        """Get the list of drafts that were recovered.
        
        This should be called after the dialog is accepted to get
        the drafts that need to be restored.
        
        Returns:
            List of draft dictionaries to recover
        """
        if self.result() == QDialog.DialogCode.Accepted:
            return self.get_selected_drafts()
        return []