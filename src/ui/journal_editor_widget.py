"""Journal editor widget for creating and managing health journal entries.

This module provides a comprehensive journal editor interface for the Apple Health
Monitor Dashboard. It supports daily, weekly, and monthly journal entries with
rich text editing capabilities, search functionality, and entry management.

The JournalEditorWidget integrates with the existing journal system, providing:
    - Rich text editor with formatting options
    - Entry type selection (daily, weekly, monthly)
    - Smart date selection based on entry type
    - Auto-save functionality
    - Search and browse recent entries
    - Character/word count display
    - Keyboard shortcuts for efficiency

Key features:
    - Three entry types with appropriate date selectors
    - Auto-save with visual feedback
    - Full-text search across all entries
    - Recent entries list with quick navigation
    - Character and word count tracking
    - Keyboard shortcuts for common actions
    - Empty state design for new users
    - Confirmation dialogs for unsaved changes

Example:
    Basic usage in main window:
    
    >>> journal_widget = JournalEditorWidget(data_access)
    >>> journal_widget.entry_saved.connect(self.on_journal_saved)
    >>> journal_widget.entry_deleted.connect(self.on_journal_deleted)
    >>> main_tabs.addTab(journal_widget, "Journal")
    
    Programmatic entry creation:
    
    >>> journal_widget.create_new_entry('daily', date.today())
    >>> journal_widget.set_content("Today's health journal entry...")
    >>> journal_widget.save_entry()
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QSplitter, QListWidget, QListWidgetItem,
    QGroupBox, QLineEdit, QMessageBox, QFrame, QToolBar, QStackedWidget,
    QCalendarWidget, QSpinBox, QButtonGroup, QCheckBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate, QDateTime, QSize, QPropertyAnimation
from PyQt6.QtGui import (
    QFont, QKeySequence, QTextCharFormat, QTextCursor, 
    QIcon, QAction, QTextDocument, QPainter, QPalette, QColor,
    QShortcut
)

from ..models import JournalEntry
from ..data_access import DataAccess
from ..utils.logging_config import get_logger
from .enhanced_date_edit import EnhancedDateEdit
from .style_manager import StyleManager
from .journal_manager import JournalManager
from .toast_notification import ToastNotification
from .conflict_resolution_dialog import ConflictResolutionDialog
from .auto_save_manager import AutoSaveManager
from .save_status_indicator import SaveStatusIndicator
from .journal_export_dialog import JournalExportDialog

logger = get_logger(__name__)


class SegmentedControl(QWidget):
    """Custom segmented control widget for modern toggle button selection.
    
    This widget provides a modern segmented control interface similar to iOS/macOS
    with smooth animations and keyboard navigation support.
    
    Attributes:
        selectionChanged (pyqtSignal): Emitted when selection changes with the selected text
    
    Example:
        >>> control = SegmentedControl(["Daily", "Weekly", "Monthly"])
        >>> control.selectionChanged.connect(self.on_type_changed)
        >>> control.setSelectedIndex(0)  # Select "Daily"
    """
    
    selectionChanged = pyqtSignal(str)
    
    def __init__(self, options: List[str], parent: Optional[QWidget] = None):
        """Initialize the segmented control.
        
        Args:
            options (List[str]): List of option labels
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self.options = options
        self.buttons: List[QPushButton] = []
        self.current_index = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Create buttons
        for i, option in enumerate(self.options):
            button = QPushButton(option)
            button.setCheckable(True)
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            
            # Apply styling
            self.style_button(button, i)
            
            # Connect signals
            button.clicked.connect(lambda checked, idx=i: self.on_button_clicked(idx))
            
            # Add to group and layout
            self.button_group.addButton(button, i)
            self.buttons.append(button)
            layout.addWidget(button)
            
        # Select first option by default
        if self.buttons:
            self.buttons[0].setChecked(True)
            
    def style_button(self, button: QPushButton, index: int):
        """Apply styling to a button based on its position.
        
        Args:
            button (QPushButton): The button to style
            index (int): The button's index in the control
        """
        # Determine border radius based on position
        if index == 0:
            # First button - rounded left
            border_radius = "8px 0px 0px 8px"
        elif index == len(self.options) - 1:
            # Last button - rounded right
            border_radius = "0px 8px 8px 0px"
        else:
            # Middle button - no rounding
            border_radius = "0px"
            
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: {border_radius};
                padding: 8px 16px;
                color: #5D4E37;
                font-weight: 500;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #FFF5E6;
            }}
            QPushButton:checked {{
                background-color: #FF8C42;
                color: #FFFFFF;
                border-color: #FF8C42;
            }}
            QPushButton:focus {{
                outline: 2px solid #FF8C42;
                outline-offset: 2px;
            }}
        """)
        
    def on_button_clicked(self, index: int):
        """Handle button click.
        
        Args:
            index (int): The index of the clicked button
        """
        if index != self.current_index:
            self.current_index = index
            self.selectionChanged.emit(self.options[index])
            
    def setSelectedIndex(self, index: int):
        """Set the selected index programmatically.
        
        Args:
            index (int): The index to select
        """
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            self.current_index = index
            
    def setSelectedText(self, text: str):
        """Set the selected option by text.
        
        Args:
            text (str): The option text to select
        """
        try:
            index = self.options.index(text)
            self.setSelectedIndex(index)
        except ValueError:
            logger.warning(f"Option '{text}' not found in segmented control")
            
    def selectedText(self) -> str:
        """Get the currently selected text.
        
        Returns:
            str: The selected option text
        """
        return self.options[self.current_index] if self.options else ""
        
    def keyPressEvent(self, event):
        """Handle keyboard navigation.
        
        Args:
            event: The key press event
        """
        if event.key() == Qt.Key.Key_Left and self.current_index > 0:
            self.setSelectedIndex(self.current_index - 1)
            self.buttons[self.current_index].setFocus()
        elif event.key() == Qt.Key.Key_Right and self.current_index < len(self.buttons) - 1:
            self.setSelectedIndex(self.current_index + 1)
            self.buttons[self.current_index].setFocus()
        else:
            super().keyPressEvent(event)


class JournalEditorWidget(QWidget):
    """Character limit for journal entries."""
    CHARACTER_LIMIT = 10000
    """Comprehensive journal editor widget with rich text editing and entry management.
    
    This widget provides a full-featured journal editor for creating and managing
    health journal entries. It supports three types of entries (daily, weekly, monthly)
    with appropriate date selection and rich text editing capabilities.
    
    The interface is divided into three main sections:
        - Entry list: Browse and search recent journal entries
        - Editor: Rich text editor with formatting toolbar
        - Metadata: Entry type, date selection, and statistics
    
    Attributes:
        entry_saved (pyqtSignal): Emitted when an entry is saved
        entry_deleted (pyqtSignal): Emitted when an entry is deleted
        entry_selected (pyqtSignal): Emitted when an entry is selected
        
    Args:
        data_access (DataAccess): Data access object for database operations
        parent (Optional[QWidget]): Parent widget
    """
    
    # Signals
    entry_saved = pyqtSignal(JournalEntry)
    entry_deleted = pyqtSignal(int)  # entry_id
    entry_selected = pyqtSignal(JournalEntry)
    
    def __init__(self, data_access: DataAccess, parent: Optional[QWidget] = None):
        """Initialize the journal editor widget.
        
        Args:
            data_access (DataAccess): Data access object for database operations
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self.data_access = data_access
        self.style_manager = StyleManager()
        self.journal_manager = JournalManager(data_access)
        self.current_entry: Optional[JournalEntry] = None
        self.is_modified = False
        self._current_version: Optional[int] = None  # For optimistic locking
        
        # Initialize auto-save manager
        self.auto_save_manager = AutoSaveManager(data_access, self)
        self.auto_save_manager.saveRequested.connect(self._perform_auto_save)
        self.auto_save_manager.saveCompleted.connect(self._on_auto_save_completed)
        self.auto_save_manager.draftRecovered.connect(self._on_draft_recovered)
        
        # Load auto-save settings if available
        self._load_auto_save_settings()
        
        # Connect journal manager signals
        self.journal_manager.entrySaved.connect(self._on_entry_saved)
        self.journal_manager.entryDeleted.connect(self._on_entry_deleted)
        self.journal_manager.errorOccurred.connect(self._on_error_occurred)
        self.journal_manager.conflictDetected.connect(self._on_conflict_detected)
        
        # Set conflict handler
        self.journal_manager.set_conflict_handler(self._handle_conflict)
        
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tab_order()
        self.load_recent_entries()
        
    def setup_ui(self):
        """Set up the user interface components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        self.toolbar = self.create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Create main splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Entry list and search
        left_panel = self.create_left_panel()
        self.splitter.addWidget(left_panel)
        
        # Right panel: Editor and metadata
        right_panel = self.create_right_panel()
        self.splitter.addWidget(right_panel)
        
        # Set splitter sizes (30% left, 70% right)
        self.splitter.setSizes([300, 700])
        main_layout.addWidget(self.splitter)
        
        # Status bar
        self.status_bar = self.create_status_bar()
        main_layout.addWidget(self.status_bar)
        
        # Apply styling
        self.setStyleSheet(self.style_manager.get_widget_style("journal_editor"))
        
    def create_toolbar(self) -> QToolBar:
        """Create the main toolbar with formatting actions.
        
        Returns:
            QToolBar: Configured toolbar with formatting actions
        """
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        
        # New entry action
        new_action = QAction("New Entry", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_entry)
        toolbar.addAction(new_action)
        
        # Save action
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_entry)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Text formatting actions
        bold_action = QAction("Bold", self)
        bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        bold_action.setCheckable(True)
        bold_action.triggered.connect(self.toggle_bold)
        toolbar.addAction(bold_action)
        
        italic_action = QAction("Italic", self)
        italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        italic_action.setCheckable(True)
        italic_action.triggered.connect(self.toggle_italic)
        toolbar.addAction(italic_action)
        
        underline_action = QAction("Underline", self)
        underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        underline_action.setCheckable(True)
        underline_action.triggered.connect(self.toggle_underline)
        toolbar.addAction(underline_action)
        
        toolbar.addSeparator()
        
        # Export action
        export_action = QAction("Export", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_entries)
        toolbar.addAction(export_action)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_entry)
        toolbar.addAction(delete_action)
        
        return toolbar
        
    def create_left_panel(self) -> QWidget:
        """Create the left panel with entry list and search.
        
        Returns:
            QWidget: Configured left panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Search box
        search_group = QGroupBox("Search Entries")
        search_layout = QVBoxLayout(search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search journal entries...")
        self.search_input.textChanged.connect(self.search_entries)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_group)
        
        # Recent entries list
        entries_group = QGroupBox("Recent Entries")
        entries_layout = QVBoxLayout(entries_group)
        
        self.entries_list = QListWidget()
        self.entries_list.itemClicked.connect(self.load_selected_entry)
        entries_layout.addWidget(self.entries_list)
        
        layout.addWidget(entries_group, 1)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with editor and metadata.
        
        Returns:
            QWidget: Configured right panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Entry metadata
        metadata_group = QGroupBox("Entry Details")
        metadata_layout = QHBoxLayout(metadata_group)
        
        # Entry type selector using custom SegmentedControl
        metadata_layout.addWidget(QLabel("Type:"))
        self.entry_type_control = SegmentedControl(["Daily", "Weekly", "Monthly"])
        self.entry_type_control.selectionChanged.connect(self.on_entry_type_changed)
        metadata_layout.addWidget(self.entry_type_control)
        
        metadata_layout.addWidget(QLabel("Date:"))
        
        # Date selection stack (different widgets for different entry types)
        self.date_stack = QStackedWidget()
        
        # Daily date selector
        self.daily_date_edit = EnhancedDateEdit()
        self.daily_date_edit.setDate(QDate.currentDate())
        self.date_stack.addWidget(self.daily_date_edit)
        
        # Weekly date selector
        weekly_widget = QWidget()
        weekly_layout = QHBoxLayout(weekly_widget)
        weekly_layout.setContentsMargins(0, 0, 0, 0)
        self.weekly_date_edit = EnhancedDateEdit()
        self.weekly_date_edit.setDate(QDate.currentDate())
        self.weekly_date_edit.dateChanged.connect(self.update_week_label)
        weekly_layout.addWidget(self.weekly_date_edit)
        self.week_label = QLabel()
        weekly_layout.addWidget(self.week_label)
        self.date_stack.addWidget(weekly_widget)
        
        # Monthly date selector
        monthly_widget = QWidget()
        monthly_layout = QHBoxLayout(monthly_widget)
        monthly_layout.setContentsMargins(0, 0, 0, 0)
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(datetime.now().month)
        monthly_layout.addWidget(self.month_spin)
        monthly_layout.addWidget(QLabel("/"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(datetime.now().year)
        monthly_layout.addWidget(self.year_spin)
        self.date_stack.addWidget(monthly_widget)
        
        metadata_layout.addWidget(self.date_stack)
        metadata_layout.addStretch()
        
        layout.addWidget(metadata_group)
        
        # Text editor
        editor_group = QGroupBox("Journal Entry")
        editor_layout = QVBoxLayout(editor_group)
        
        self.text_editor = QTextEdit()
        self.text_editor.setAcceptRichText(True)
        self.text_editor.textChanged.connect(self.on_text_changed)
        
        # Set up text editor styling
        self.text_editor.setFont(QFont('Inter', 14))
        self.text_editor.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                padding: 16px;
                color: #5D4E37;
            }
            QTextEdit:focus {
                border-color: #FF8C42;
            }
        """)
        
        editor_layout.addWidget(self.text_editor)
        
        layout.addWidget(editor_group, 1)
        
        return panel
        
    def create_status_bar(self) -> QWidget:
        """Create the status bar with character/word count.
        
        Returns:
            QWidget: Configured status bar widget
        """
        status_bar = QFrame()
        status_bar.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(status_bar)
        
        # Character count
        self.char_count_label = QLabel("Characters: 0")
        layout.addWidget(self.char_count_label)
        
        layout.addWidget(QLabel("|"))
        
        # Word count
        self.word_count_label = QLabel("Words: 0")
        layout.addWidget(self.word_count_label)
        
        layout.addWidget(QLabel("|"))
        
        # Auto-save toggle
        self.auto_save_checkbox = QCheckBox("Auto-save")
        self.auto_save_checkbox.setChecked(True)
        self.auto_save_checkbox.toggled.connect(self._on_auto_save_toggled)
        layout.addWidget(self.auto_save_checkbox)
        
        layout.addStretch()
        
        # Save status indicator
        self.save_status_indicator = SaveStatusIndicator()
        self.auto_save_manager.statusChanged.connect(self.save_status_indicator.set_status)
        layout.addWidget(self.save_status_indicator)
        
        return status_bar
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        # Quick save
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_entry)
        
        # New entry
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_entry)
        
        # Search focus
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.search_input.setFocus())
        
        # Navigate entries
        QShortcut(QKeySequence("Ctrl+Up"), self, self.select_previous_entry)
        QShortcut(QKeySequence("Ctrl+Down"), self, self.select_next_entry)
        
    def setup_tab_order(self):
        """Set up proper tab order for keyboard navigation."""
        # Tab order: Entry type → Date selection → Text editor → Search
        self.setTabOrder(self.entry_type_control, self.daily_date_edit)
        self.setTabOrder(self.daily_date_edit, self.text_editor)
        self.setTabOrder(self.text_editor, self.search_input)
        self.setTabOrder(self.search_input, self.entries_list)
        
    def load_recent_entries(self):
        """Load recent journal entries into the list."""
        try:
            # Get entries from the last 90 days
            end_date = date.today()
            start_date = end_date - timedelta(days=90)
            
            entries = self.data_access.get_journal_entries(start_date, end_date)
            
            self.entries_list.clear()
            for entry in sorted(entries, key=lambda e: e.entry_date, reverse=True):
                self.add_entry_to_list(entry)
                
            # Show empty state if no entries
            if not entries:
                self.show_empty_state()
                
        except Exception as e:
            logger.error(f"Error loading recent entries: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load recent entries: {str(e)}")
            
    def add_entry_to_list(self, entry: JournalEntry):
        """Add a journal entry to the list widget.
        
        Args:
            entry (JournalEntry): The journal entry to add
        """
        # Create list item with formatted display
        item_text = f"{entry.entry_type.title()} - {entry.entry_date}"
        if entry.content:
            # Add preview of content (first 50 characters)
            preview = entry.content[:50].replace('\n', ' ')
            if len(entry.content) > 50:
                preview += "..."
            item_text += f"\n{preview}"
            
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, entry)
        
        # Style based on entry type
        if entry.entry_type == 'daily':
            item.setBackground(Qt.GlobalColor.white)
        elif entry.entry_type == 'weekly':
            item.setBackground(Qt.GlobalColor.lightGray)
        else:  # monthly
            item.setBackground(Qt.GlobalColor.darkGray)
            item.setForeground(Qt.GlobalColor.white)
            
        self.entries_list.addItem(item)
        
    def show_empty_state(self):
        """Show empty state when no entries exist."""
        self.text_editor.setHtml(
            "<div style='text-align: center; color: #666; padding: 20px;'>"
            "<h2>Welcome to Your Health Journal</h2>"
            "<p>Start documenting your health journey by creating your first entry.</p>"
            "<p>Choose an entry type above and begin writing!</p>"
            "</div>"
        )
        
    def new_entry(self):
        """Create a new journal entry."""
        # Check for unsaved changes
        if self.is_modified and not self.confirm_discard_changes():
            return
            
        # Reset editor
        self.current_entry = None
        self._current_version = None
        self.text_editor.clear()
        self.is_modified = False
        self.update_counts()
        self.save_status_indicator.set_idle_status()
        
        # Reset to daily entry with today's date
        self.entry_type_control.setSelectedText("Daily")
        self.daily_date_edit.setDate(QDate.currentDate())
        
        # Focus on text editor
        self.text_editor.setFocus()
        
    def save_entry(self):
        """Save the current journal entry using JournalManager."""
        # Get entry data
        entry_type = self.entry_type_control.selectedText().lower()
        content = self.text_editor.toPlainText().strip()
        
        # Get appropriate date based on entry type
        if entry_type == 'daily':
            entry_date = self.daily_date_edit.date()
        elif entry_type == 'weekly':
            entry_date = self.weekly_date_edit.date()
        else:  # monthly
            year = self.year_spin.value()
            month = self.month_spin.value()
            entry_date = QDate(year, month, 1)
            
        # Get version for optimistic locking (only if updating existing entry)
        expected_version = None
        if self.current_entry and hasattr(self, '_current_version'):
            expected_version = self._current_version
            
        # Save using JournalManager
        self.journal_manager.save_entry(
            entry_date=entry_date,
            entry_type=entry_type,
            content=content,
            callback=self._on_save_complete,
            expected_version=expected_version
        )
            
    def delete_entry(self):
        """Delete the current journal entry with enhanced confirmation dialog."""
        if not self.current_entry:
            toast = ToastNotification.warning("No entry selected to delete", self)
            toast.show()
            return
            
        # Create custom deletion confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Show entry preview in the message
        preview = self.current_entry.content[:100]
        if len(self.current_entry.content) > 100:
            preview += "..."
            
        msg_box.setText(
            f"Are you sure you want to delete this {self.current_entry.entry_type} entry?\n\n"
            f"Date: {self.current_entry.entry_date}\n"
            f"Preview: {preview}"
        )
        msg_box.setInformativeText("This action cannot be undone.")
        
        # Custom buttons
        delete_btn = msg_box.addButton("Delete Entry", QMessageBox.ButtonRole.DestructiveRole)
        export_btn = msg_box.addButton("Export First", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.StandardButton.Cancel)
        
        msg_box.setDefaultButton(cancel_btn)
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == delete_btn:
            # Proceed with deletion
            self._perform_deletion()
        elif clicked_button == export_btn:
            # Export entry first
            self.export_entries()
            # User can delete after export if desired
        # else: cancelled, do nothing
        
    def _perform_deletion(self):
        """Actually perform the deletion of the current entry."""
        if not self.current_entry:
            return
            
        # Get entry details
        entry_type = self.current_entry.entry_type
        entry_date = QDate(self.current_entry.entry_date)
        
        # Use JournalManager to delete
        self.journal_manager.delete_entry(
            entry_date=entry_date,
            entry_type=entry_type,
            callback=lambda success: self._on_delete_complete(success)
        )
        
    def _on_delete_complete(self, success: bool):
        """Handle delete operation completion.
        
        Args:
            success: Whether the deletion was successful
        """
        if success:
            # Clear the editor
            self.new_entry()
            # Refresh the entry list
            self.load_recent_entries()
            
            # Emit signal if we have an entry ID
            if self.current_entry and self.current_entry.id:
                self.entry_deleted.emit(self.current_entry.id)
    
    def export_entries(self):
        """Open the export dialog to export journal entries.
        
        Shows the journal export dialog which allows users to select
        export format (JSON/PDF), date range, and export options.
        """
        try:
            # Check if we need to save current changes first
            if self.is_modified:
                reply = QMessageBox.question(
                    self,
                    "Save Changes?",
                    "You have unsaved changes. Would you like to save them before exporting?",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    self.save_entry()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
                    
            # Open export dialog
            dialog = JournalExportDialog(self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Export completed successfully
                if dialog.export_result:
                    toast = ToastNotification.success(
                        f"Successfully exported {dialog.export_result.entries_exported} entries",
                        self
                    )
                    toast.show()
                    
        except Exception as e:
            logger.error(f"Error opening export dialog: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to open export dialog: {str(e)}"
            )
                
    def on_text_changed(self):
        """Handle text changes in the editor with character limit enforcement."""
        text = self.text_editor.toPlainText()
        
        # Enforce character limit
        if len(text) > self.CHARACTER_LIMIT:
            # Block the signal to prevent infinite recursion
            self.text_editor.blockSignals(True)
            
            # Get cursor position
            cursor = self.text_editor.textCursor()
            position = cursor.position()
            
            # Truncate text
            truncated_text = text[:self.CHARACTER_LIMIT]
            self.text_editor.setPlainText(truncated_text)
            
            # Restore cursor position (at the limit)
            cursor.setPosition(min(position, self.CHARACTER_LIMIT))
            self.text_editor.setTextCursor(cursor)
            
            # Re-enable signals
            self.text_editor.blockSignals(False)
            
            # Show warning
            QMessageBox.warning(self, "Character Limit", 
                               f"Journal entries are limited to {self.CHARACTER_LIMIT:,} characters.")
        
        self.is_modified = True
        self.update_counts()
        
        # Notify auto-save manager of content change
        if self.auto_save_manager.enabled:
            entry_type = self.entry_type_control.selectedText().lower()
            entry_date = self._get_current_entry_date()
            if entry_date:
                self.auto_save_manager.on_content_changed(
                    entry_date.isoformat(),
                    entry_type,
                    text
                )
        
    def update_counts(self):
        """Update character and word counts with limit indicator."""
        text = self.text_editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        
        # Update character count with limit and color coding
        remaining = self.CHARACTER_LIMIT - char_count
        char_text = f"Characters: {char_count:,} / {self.CHARACTER_LIMIT:,}"
        
        # Color coding based on character count
        if char_count <= 7000:
            color = "#95C17B"  # Green
        elif char_count <= 9000:
            color = "#FFD166"  # Yellow
        elif char_count <= 9800:
            color = "#F4A261"  # Orange
        else:
            color = "#E76F51"  # Red
            
        self.char_count_label.setText(char_text)
        self.char_count_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        self.word_count_label.setText(f"Words: {word_count:,}")
        
    def on_entry_type_changed(self, entry_type: str):
        """Handle entry type changes.
        
        Args:
            entry_type (str): The new entry type
        """
        # Update date selector
        if entry_type == "Daily":
            self.date_stack.setCurrentIndex(0)
        elif entry_type == "Weekly":
            self.date_stack.setCurrentIndex(1)
            self.update_week_label()
        else:  # Monthly
            self.date_stack.setCurrentIndex(2)
            
    def update_week_label(self):
        """Update the week range label for weekly entries."""
        selected_date = self.weekly_date_edit.date().toPython()
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        self.week_label.setText(f"({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})")
        
    def search_entries(self, search_text: str):
        """Search journal entries based on text.
        
        Args:
            search_text (str): The search query
        """
        if not search_text:
            self.load_recent_entries()
            return
            
        try:
            entries = self.data_access.search_journal_entries(search_text)
            
            self.entries_list.clear()
            for entry in entries:
                self.add_entry_to_list(entry)
                
            if not entries:
                item = QListWidgetItem("No entries found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.entries_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error searching entries: {e}")
            
    def load_selected_entry(self, item: QListWidgetItem):
        """Load the selected entry into the editor.
        
        Args:
            item (QListWidgetItem): The selected list item
        """
        # Check for unsaved changes
        if self.is_modified and not self.confirm_discard_changes():
            return
            
        entry = item.data(Qt.ItemDataRole.UserRole)
        if not entry:
            return
            
        self.current_entry = entry
        
        # Set entry type
        self.entry_type_control.setSelectedText(entry.entry_type.title())
        
        # Set date based on entry type
        if entry.entry_type == 'daily':
            self.daily_date_edit.setDate(QDate(entry.entry_date))
        elif entry.entry_type == 'weekly':
            self.weekly_date_edit.setDate(QDate(entry.entry_date))
            self.update_week_label()
        else:  # monthly
            self.year_spin.setValue(entry.entry_date.year)
            self.month_spin.setValue(entry.entry_date.month)
            
        # Set content
        self.text_editor.setPlainText(entry.content)
        
        # Reset modified flag
        self.is_modified = False
        self.update_counts()
        
        # Update save status
        if entry.updated_at:
            self.save_status_indicator.set_saved_status(
                QDateTime.fromString(entry.updated_at.isoformat(), Qt.DateFormat.ISODate)
            )
        else:
            self.save_status_indicator.set_idle_status()
            
        # Store the version for optimistic locking
        self._current_version = getattr(entry, 'version', 1)
        logger.debug(f"Loaded entry with version {self._current_version}")
            
        # Emit signal
        self.entry_selected.emit(entry)
        
    def confirm_discard_changes(self) -> bool:
        """Confirm if user wants to discard unsaved changes.
        
        Returns:
            bool: True if user confirms, False otherwise
        """
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
        
    def select_previous_entry(self):
        """Select the previous entry in the list."""
        current_row = self.entries_list.currentRow()
        if current_row > 0:
            self.entries_list.setCurrentRow(current_row - 1)
            self.load_selected_entry(self.entries_list.currentItem())
            
    def select_next_entry(self):
        """Select the next entry in the list."""
        current_row = self.entries_list.currentRow()
        if current_row < self.entries_list.count() - 1:
            self.entries_list.setCurrentRow(current_row + 1)
            self.load_selected_entry(self.entries_list.currentItem())
            
    def toggle_bold(self):
        """Toggle bold formatting on selected text."""
        fmt = QTextCharFormat()
        fmt.setFontWeight(
            QFont.Weight.Bold if self.text_editor.fontWeight() != QFont.Weight.Bold 
            else QFont.Weight.Normal
        )
        self.merge_format(fmt)
        
    def toggle_italic(self):
        """Toggle italic formatting on selected text."""
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.text_editor.fontItalic())
        self.merge_format(fmt)
        
    def toggle_underline(self):
        """Toggle underline formatting on selected text."""
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.text_editor.fontUnderline())
        self.merge_format(fmt)
        
    def merge_format(self, format: QTextCharFormat):
        """Merge text format with current selection.
        
        Args:
            format (QTextCharFormat): The format to apply
        """
        cursor = self.text_editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(format)
        self.text_editor.mergeCurrentCharFormat(format)
        
    def _get_current_entry_date(self) -> Optional[date]:
        """Get the currently selected entry date based on entry type.
        
        Returns:
            Optional[date]: The selected date or None if invalid
        """
        entry_type = self.entry_type_control.selectedText().lower()
        
        try:
            if entry_type == 'daily':
                return self.daily_date_edit.date().toPython()
            elif entry_type == 'weekly':
                return self.weekly_date_edit.date().toPython()
            else:  # monthly
                year = self.year_spin.value()
                month = self.month_spin.value()
                return date(year, month, 1)
        except Exception as e:
            logger.error(f"Error getting current entry date: {e}")
            return None
            
    def _on_auto_save_toggled(self, checked: bool):
        """Handle auto-save toggle.
        
        Args:
            checked: Whether auto-save is enabled
        """
        self.auto_save_manager.set_enabled(checked)
        if checked:
            # Trigger content change notification to restart timer
            self.on_text_changed()
            
    def _perform_auto_save(self, entry_date: str, entry_type: str, content: str):
        """Perform the actual auto-save operation.
        
        Args:
            entry_date: ISO format date string
            entry_type: Type of entry
            content: Entry content
        """
        # Convert date string back to QDate for save_entry
        qdate = QDate.fromString(entry_date, Qt.DateFormat.ISODate)
        
        # Update the appropriate date widget
        if entry_type == 'daily':
            self.daily_date_edit.setDate(qdate)
        elif entry_type == 'weekly':
            self.weekly_date_edit.setDate(qdate)
        else:  # monthly
            date_obj = qdate.toPython()
            self.year_spin.setValue(date_obj.year)
            self.month_spin.setValue(date_obj.month)
            
        # Perform save
        self.save_entry()
        
    def _on_auto_save_completed(self, success: bool, message: str):
        """Handle auto-save completion.
        
        Args:
            success: Whether the save was successful
            message: Status message
        """
        if success:
            logger.debug(f"Auto-save completed: {message}")
        else:
            logger.error(f"Auto-save failed: {message}")
            
    def _on_draft_recovered(self, draft_data: dict):
        """Handle recovered draft notification.
        
        Args:
            draft_data: Dictionary containing recovered draft information
        """
        from .draft_recovery_dialog import DraftRecoveryDialog
        
        drafts = draft_data.get('drafts', [])
        if not drafts:
            return
            
        # Show recovery dialog
        recovery_dialog = DraftRecoveryDialog(drafts, parent=self)
        recovery_dialog.drafts_recovered.connect(self._restore_drafts)
        
        result = recovery_dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Get recovered drafts
            recovered = recovery_dialog.get_recovered_drafts()
            if recovered:
                # Restore the first draft (or let user choose if multiple)
                self._restore_draft(recovered[0])
                
                # Mark drafts as recovered in the database
                for draft in recovered:
                    if 'id' in draft:
                        self.auto_save_manager.recover_draft(draft['id'])
                        
        # If rejected (Later button), drafts remain in the database for next time
        
    def _restore_drafts(self, drafts: List[Dict[str, Any]]):
        """Handle multiple drafts recovered signal.
        
        Args:
            drafts: List of draft dictionaries to restore
        """
        if drafts:
            # For now, just restore the first one
            # In the future, could allow switching between multiple recovered drafts
            self._restore_draft(drafts[0])
            
    def _restore_draft(self, draft: Dict[str, Any]):
        """Restore a single draft to the editor.
        
        Args:
            draft: Draft dictionary with entry data
        """
        try:
            # Check for unsaved changes first
            if self.is_modified and not self.confirm_discard_changes():
                return
                
            # Set entry type
            entry_type = draft.get('entry_type', 'daily')
            self.entry_type_control.setSelectedText(entry_type.title())
            
            # Set date
            entry_date_str = draft.get('entry_date', '')
            if entry_date_str:
                try:
                    entry_date = QDate.fromString(entry_date_str, Qt.DateFormat.ISODate)
                    if not entry_date.isValid():
                        # Try parsing as Python date string
                        from datetime import datetime
                        dt = datetime.fromisoformat(entry_date_str)
                        entry_date = QDate(dt.year, dt.month, dt.day)
                        
                    if entry_type == 'daily':
                        self.daily_date_edit.setDate(entry_date)
                    elif entry_type == 'weekly':
                        self.weekly_date_edit.setDate(entry_date)
                        self.update_week_label()
                    else:  # monthly
                        self.year_spin.setValue(entry_date.year())
                        self.month_spin.setValue(entry_date.month())
                except Exception as e:
                    logger.error(f"Error parsing draft date: {e}")
                    
            # Set content
            content = draft.get('content', '')
            self.text_editor.setPlainText(content)
            
            # Update UI state
            self.is_modified = True  # Mark as modified so it will be saved
            self.update_counts()
            
            # Show success notification
            toast = ToastNotification.info(
                f"Draft recovered from {draft.get('saved_at', 'previous session')}", 
                self
            )
            toast.show()
            
            logger.info(f"Restored {entry_type} draft for {entry_date_str}")
            
        except Exception as e:
            logger.error(f"Error restoring draft: {e}")
            toast = ToastNotification.error("Failed to restore draft", self)
            toast.show()
            
    def _load_auto_save_settings(self):
        """Load auto-save settings from settings manager if available."""
        try:
            # Try to get settings from parent's settings manager
            parent = self.parent()
            while parent:
                if hasattr(parent, 'settings_manager'):
                    settings_manager = parent.settings_manager
                    
                    # Load settings
                    enabled = settings_manager.get_setting("auto_save_enabled", True)
                    self.auto_save_manager.set_enabled(enabled)
                    self.auto_save_checkbox.setChecked(enabled)
                    
                    delay = settings_manager.get_setting("auto_save_delay", 3)
                    self.auto_save_manager.set_debounce_delay(delay * 1000)
                    
                    max_wait = settings_manager.get_setting("auto_save_max_wait", 30)
                    self.auto_save_manager.set_max_wait_time(max_wait * 1000)
                    
                    logger.debug(f"Loaded auto-save settings: enabled={enabled}, delay={delay}s")
                    break
                    
                parent = parent.parent()
                
        except Exception as e:
            logger.warning(f"Could not load auto-save settings: {e}")
            # Settings will use defaults
            
    def update_auto_save_settings(self, settings: Dict[str, Any]):
        """Update auto-save settings from settings panel.
        
        Args:
            settings: Dictionary of auto-save settings
        """
        if 'enabled' in settings:
            self.auto_save_manager.set_enabled(settings['enabled'])
            self.auto_save_checkbox.setChecked(settings['enabled'])
            
        if 'delay_seconds' in settings:
            self.auto_save_manager.set_debounce_delay(settings['delay_seconds'] * 1000)
            
        if 'max_wait_seconds' in settings:
            self.auto_save_manager.set_max_wait_time(settings['max_wait_seconds'] * 1000)
            
        logger.info(f"Updated auto-save settings: {settings}")
        
    def closeEvent(self, event):
        """Handle widget close event."""
        if self.is_modified and not self.confirm_discard_changes():
            event.ignore()
        else:
            # Clean up auto-save manager
            self.auto_save_manager.cleanup()
            event.accept()
            
    def _on_save_complete(self, success: bool, entry_id: Optional[int]):
        """Handle save operation completion.
        
        Args:
            success: Whether the save was successful
            entry_id: The ID of the saved entry
        """
        if success:
            # Update UI
            self.is_modified = False
            
            # Update save status indicator
            self.save_status_indicator.set_saved_status(QDateTime.currentDateTime())
            
            # Show success notification
            toast = ToastNotification.success("Journal entry saved successfully!", self)
            toast.show()
            
            # Refresh entry list
            self.load_recent_entries()
            
            # Update current entry and version
            if self.current_entry:
                self.current_entry.updated_at = datetime.now()
                # Increment version for next save
                if hasattr(self, '_current_version'):
                    self._current_version += 1
                else:
                    self._current_version = 2
            
    def _on_entry_saved(self, date_str: str, entry_type: str):
        """Handle entry saved signal from JournalManager.
        
        Args:
            date_str: ISO format date string
            entry_type: Type of entry saved
        """
        logger.info(f"Entry saved: {entry_type} for {date_str}")
        
    def _on_entry_deleted(self, date_str: str, entry_type: str):
        """Handle entry deleted signal from JournalManager.
        
        Args:
            date_str: ISO format date string
            entry_type: Type of entry deleted
        """
        logger.info(f"Entry deleted: {entry_type} for {date_str}")
        
        # Show success notification
        toast = ToastNotification.info("Journal entry deleted", self)
        toast.show()
        
    def _on_error_occurred(self, error_message: str):
        """Handle error signal from JournalManager.
        
        Args:
            error_message: The error message to display
        """
        # Show error notification
        toast = ToastNotification.error(error_message, self, duration=5000)
        toast.show()
        
    def _on_conflict_detected(self, date_str: str, current_content: str, new_content: str):
        """Handle conflict detection from JournalManager.
        
        Args:
            date_str: ISO format date string
            current_content: Content currently in database
            new_content: New content attempting to save
        """
        logger.warning(f"Conflict detected for entry on {date_str}")
        
    def _handle_conflict(self, current_content: str, new_content: str) -> str:
        """Handle save conflicts with user dialog.
        
        Args:
            current_content: Content currently in database
            new_content: New content attempting to save
            
        Returns:
            str: User's choice ('keep_mine', 'keep_theirs', or 'cancel')
        """
        # Get current entry date and type
        entry_type = self.entry_type_control.selectedText().lower()
        
        if entry_type == 'daily':
            entry_date = self.daily_date_edit.date().toPython()
        elif entry_type == 'weekly':
            entry_date = self.weekly_date_edit.date().toPython()
        else:  # monthly
            year = self.year_spin.value()
            month = self.month_spin.value()
            entry_date = date(year, month, 1)
            
        # Show conflict resolution dialog
        dialog = ConflictResolutionDialog(
            current_content=current_content,
            new_content=new_content,
            entry_date=entry_date,
            entry_type=entry_type,
            parent=self
        )
        
        result = dialog.exec()
        return dialog.get_choice()