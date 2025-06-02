"""Unit tests for the journal editor widget.

This module contains comprehensive tests for the JournalEditorWidget class,
including character limit enforcement, unsaved changes detection, keyboard
shortcuts, and date/type selection functionality.
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QKeySequence

from src.ui.journal_editor_widget import JournalEditorWidget
from src.models import JournalEntry


@pytest.fixture
def app(qtbot):
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def mock_data_access():
    """Create mock data access object."""
    mock = Mock()
    mock.get_journal_entries.return_value = []
    mock.save_journal_entry.return_value = 1
    mock.delete_journal_entry.return_value = True
    return mock


@pytest.fixture
def journal_widget(qapp, qtbot, mock_data_access):
    """Create JournalEditorWidget instance."""
    widget = JournalEditorWidget(mock_data_access)
    qtbot.addWidget(widget)
    return widget


@pytest.mark.ui
@pytest.mark.skip(reason="JournalManager singleton causes segfaults in test environment")
class TestJournalEditorWidget:
    """Test cases for JournalEditorWidget."""
    
    def test_initialization(self, journal_widget):
        """Test widget initialization."""
        assert journal_widget.CHARACTER_LIMIT == 10000
        assert journal_widget.current_entry is None
        assert journal_widget.is_modified is False
        assert journal_widget.auto_save_timer.interval() == 30000
        
    def test_character_limit_enforcement(self, journal_widget, qtbot):
        """Test that character limit is enforced."""
        # Type text up to limit
        test_text = "a" * 9999
        journal_widget.text_editor.setPlainText(test_text)
        assert len(journal_widget.text_editor.toPlainText()) == 9999
        
        # Try to exceed limit
        with patch.object(QMessageBox, 'warning') as mock_warning:
            journal_widget.text_editor.setPlainText(test_text + "b" * 10)
            
            # Check text is truncated
            assert len(journal_widget.text_editor.toPlainText()) == 10000
            
            # Check warning was shown
            mock_warning.assert_called_once()
            
    def test_character_count_display(self, journal_widget):
        """Test character count display and color coding."""
        # Test green range (0-7000)
        journal_widget.text_editor.setPlainText("a" * 5000)
        journal_widget.update_counts()
        assert "5,000 / 10,000" in journal_widget.char_count_label.text()
        assert "#95C17B" in journal_widget.char_count_label.styleSheet()
        
        # Test yellow range (7001-9000)
        journal_widget.text_editor.setPlainText("a" * 8000)
        journal_widget.update_counts()
        assert "#FFD166" in journal_widget.char_count_label.styleSheet()
        
        # Test orange range (9001-9800)
        journal_widget.text_editor.setPlainText("a" * 9500)
        journal_widget.update_counts()
        assert "#F4A261" in journal_widget.char_count_label.styleSheet()
        
        # Test red range (9801-10000)
        journal_widget.text_editor.setPlainText("a" * 9900)
        journal_widget.update_counts()
        assert "#E76F51" in journal_widget.char_count_label.styleSheet()
        
    def test_entry_type_selection(self, journal_widget):
        """Test entry type selection changes date widgets."""
        # Select daily
        journal_widget.entry_type_combo.setCurrentText("Daily")
        assert journal_widget.date_stack.currentWidget() == journal_widget.daily_date_edit
        
        # Select weekly
        journal_widget.entry_type_combo.setCurrentText("Weekly")
        assert journal_widget.date_stack.currentWidget() == journal_widget.weekly_container
        
        # Select monthly
        journal_widget.entry_type_combo.setCurrentText("Monthly")
        assert journal_widget.date_stack.currentWidget() == journal_widget.monthly_container
        
    def test_unsaved_changes_detection(self, journal_widget):
        """Test unsaved changes detection."""
        # Initially no changes
        assert not journal_widget.is_modified
        
        # Make changes
        journal_widget.text_editor.setPlainText("Test content")
        assert journal_widget.is_modified
        
        # Save entry
        with patch.object(journal_widget.data_access, 'save_journal_entry', return_value=1):
            journal_widget.save_entry()
            assert not journal_widget.is_modified
            
    def test_unsaved_changes_warning(self, journal_widget):
        """Test unsaved changes warning dialog."""
        # Make changes
        journal_widget.text_editor.setPlainText("Test content")
        journal_widget.is_modified = True
        
        # Test confirmation dialog
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            result = journal_widget.confirm_discard_changes()
            assert result is True
            
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            result = journal_widget.confirm_discard_changes()
            assert result is False
            
    def test_keyboard_shortcuts(self, journal_widget, qtbot):
        """Test keyboard shortcuts work correctly."""
        # Test Ctrl+S saves entry
        journal_widget.text_editor.setPlainText("Test content")
        
        with patch.object(journal_widget, 'save_entry') as mock_save:
            qtbot.keyClick(journal_widget, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
            mock_save.assert_called_once()
            
        # Test Ctrl+N creates new entry
        with patch.object(journal_widget, 'new_entry') as mock_new:
            qtbot.keyClick(journal_widget, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
            mock_new.assert_called_once()
            
        # Test Ctrl+F focuses search
        qtbot.keyClick(journal_widget, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
        assert journal_widget.search_input.hasFocus()
        
    def test_save_entry(self, journal_widget, mock_data_access):
        """Test saving journal entry."""
        # Set up entry data
        journal_widget.entry_type_combo.setCurrentText("Daily")
        journal_widget.daily_date_edit.setDate(QDate.currentDate())
        journal_widget.text_editor.setPlainText("Test journal entry")
        
        # Save entry
        journal_widget.save_entry()
        
        # Verify save was called
        mock_data_access.save_journal_entry.assert_called_once()
        call_args = mock_data_access.save_journal_entry.call_args[1]
        assert call_args['entry_type'] == 'daily'
        assert call_args['content'] == 'Test journal entry'
        assert isinstance(call_args['entry_date'], date)
        
    def test_delete_entry(self, journal_widget, mock_data_access):
        """Test deleting journal entry."""
        # Create a test entry
        test_entry = JournalEntry(
            id=1,
            entry_date=date.today(),
            entry_type='daily',
            content='Test content',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        journal_widget.current_entry = test_entry
        
        # Delete with confirmation
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            journal_widget.delete_entry()
            
        # Verify delete was called
        mock_data_access.delete_journal_entry.assert_called_once_with(1)
        
    def test_auto_save(self, journal_widget):
        """Test auto-save functionality."""
        # Enable auto-save and make changes
        journal_widget.text_editor.setPlainText("Test content")
        journal_widget.is_modified = True
        
        # Trigger auto-save
        with patch.object(journal_widget, 'save_entry') as mock_save:
            journal_widget.auto_save()
            mock_save.assert_called_once()
            
        # Check auto-save label updated
        assert "Auto-saved" in journal_widget.auto_save_label.text()
        
    def test_search_functionality(self, journal_widget, mock_data_access):
        """Test search functionality."""
        # Create test entries
        test_entries = [
            JournalEntry(
                id=1,
                entry_date=date.today(),
                entry_type='daily',
                content='First test entry with keyword',
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            JournalEntry(
                id=2,
                entry_date=date.today(),
                entry_type='weekly',
                content='Second entry without match',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Mock search results
        mock_data_access.search_journal_entries.return_value = [test_entries[0]]
        
        # Perform search
        journal_widget.search_input.setText("keyword")
        journal_widget.search_entries()
        
        # Verify search was called
        mock_data_access.search_journal_entries.assert_called_once_with("keyword")
        
        # Check results displayed
        assert journal_widget.entries_list.count() == 1
        
    def test_responsive_layout(self, journal_widget):
        """Test widget is responsive to resizing."""
        # Check splitter exists and is configured
        assert journal_widget.splitter is not None
        assert journal_widget.splitter.orientation() == Qt.Orientation.Horizontal
        
        # Check initial sizes
        sizes = journal_widget.splitter.sizes()
        assert len(sizes) == 2
        assert sizes[0] == 300  # Left panel
        assert sizes[1] == 700  # Right panel
        
    def test_tab_navigation(self, journal_widget, qtbot):
        """Test tab navigation order."""
        # Focus on entry type combo
        journal_widget.entry_type_combo.setFocus()
        assert journal_widget.entry_type_combo.hasFocus()
        
        # Tab to date editor
        qtbot.keyClick(journal_widget, Qt.Key.Key_Tab)
        assert journal_widget.daily_date_edit.hasFocus()
        
        # Tab to text editor
        qtbot.keyClick(journal_widget, Qt.Key.Key_Tab)
        assert journal_widget.text_editor.hasFocus()
        
        # Tab to search input
        qtbot.keyClick(journal_widget, Qt.Key.Key_Tab)
        assert journal_widget.search_input.hasFocus()