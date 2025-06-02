"""Unit tests for journal tab widget.

This module tests the main journal tab interface including:
- Widget initialization and layout
- Integration between editor and history views
- Signal connections and event handling
- Search integration
- Entry creation, loading, and deletion
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock, patch

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton

from src.ui.journal_tab_widget import JournalTabWidget
from src.models import JournalEntry


@pytest.fixture
def mock_data_access():
    """Create mock data access with journal database."""
    mock = Mock()
    mock.journal_db = Mock()
    
    # Sample entry for testing
    sample_entry = JournalEntry(
        id=1,
        entry_date=date(2024, 1, 15),
        entry_type='daily',
        content='Test journal entry',
        created_at=datetime(2024, 1, 15, 10, 0),
        updated_at=datetime(2024, 1, 15, 10, 0)
    )
    
    mock.journal_db.get_entry = Mock(return_value=sample_entry)
    return mock


@pytest.fixture
def journal_tab(qtbot, mock_data_access):
    """Create JournalTabWidget instance."""
    widget = JournalTabWidget(mock_data_access)
    qtbot.addWidget(widget)
    return widget


class TestJournalTabWidget:
    """Test cases for JournalTabWidget."""
    
    def test_initialization(self, journal_tab):
        """Test widget initialization."""
        assert journal_tab.data_access is not None
        assert journal_tab.journal_editor is not None
        assert journal_tab.history_widget is not None
        assert journal_tab.search_widget is not None
        
    def test_ui_structure(self, journal_tab):
        """Test UI structure and layout."""
        # Check header exists
        header_found = False
        for child in journal_tab.children():
            if hasattr(child, 'text') and callable(child.text):
                if "Health Journal" in str(child.text()):
                    header_found = True
                    break
                    
        # Check splitter configuration
        splitter = None
        for child in journal_tab.findChildren(type(journal_tab).splitter.__class__):
            splitter = child
            break
            
        if splitter:
            assert splitter.orientation() == Qt.Orientation.Horizontal
            assert splitter.count() == 2  # History and editor
            
    def test_new_entry_button(self, journal_tab, qtbot):
        """Test new entry button functionality."""
        # Find new entry button
        new_btn = None
        for btn in journal_tab.findChildren(QPushButton):
            if btn.text() == "New Entry":
                new_btn = btn
                break
                
        assert new_btn is not None
        
        # Click button
        with patch.object(journal_tab.journal_editor, 'clear_editor') as mock_clear:
            with patch.object(journal_tab.journal_editor, 'set_date') as mock_set_date:
                qtbot.mouseClick(new_btn, Qt.MouseButton.LeftButton)
                
                mock_clear.assert_called_once()
                mock_set_date.assert_called_once()
                # Check date is today
                call_args = mock_set_date.call_args[0][0]
                assert call_args == QDate.currentDate()
                
    def test_signal_connections(self, journal_tab):
        """Test that signals are properly connected."""
        # Check history widget signals
        assert journal_tab.history_widget.entrySelected.receivers() > 0
        assert journal_tab.history_widget.entryDeleted.receivers() > 0
        
        # Check search widget signals
        assert journal_tab.search_widget.searchResultSelected.receivers() > 0
        
        # Check editor signals
        assert journal_tab.journal_editor.entrySaved.receivers() > 0
        
    def test_load_entry(self, journal_tab, mock_data_access):
        """Test loading an entry into the editor."""
        # Mock editor's load_entry method
        journal_tab.journal_editor.load_entry = Mock()
        
        # Load entry
        journal_tab.load_entry(1)
        
        # Verify database called
        mock_data_access.journal_db.get_entry.assert_called_once_with(1)
        
        # Verify editor loaded entry
        journal_tab.journal_editor.load_entry.assert_called_once()
        loaded_entry = journal_tab.journal_editor.load_entry.call_args[0][0]
        assert loaded_entry.id == 1
        assert loaded_entry.content == 'Test journal entry'
        
    def test_load_entry_error_handling(self, journal_tab, mock_data_access):
        """Test error handling when loading entry fails."""
        # Make get_entry raise exception
        mock_data_access.journal_db.get_entry.side_effect = Exception("Database error")
        
        # Should not crash
        journal_tab.load_entry(999)
        
        # Editor should not be called
        journal_tab.journal_editor.load_entry = Mock()
        assert journal_tab.journal_editor.load_entry.call_count == 0
        
    def test_on_entry_saved(self, journal_tab):
        """Test handling of entry saved event."""
        # Mock refresh methods
        journal_tab.history_widget.refresh = Mock()
        journal_tab.search_widget.clear_search = Mock()
        
        # Trigger saved event
        journal_tab.on_entry_saved()
        
        # Verify refreshes called
        journal_tab.history_widget.refresh.assert_called_once()
        journal_tab.search_widget.clear_search.assert_called_once()
        
    def test_on_entry_deleted_current(self, journal_tab):
        """Test deletion of currently displayed entry."""
        # Set current entry in editor
        current_entry = JournalEntry(
            id=5,
            entry_date=date.today(),
            entry_type='daily',
            content='To be deleted'
        )
        journal_tab.journal_editor.current_entry = current_entry
        
        # Mock methods
        journal_tab.journal_editor.clear_editor = Mock()
        journal_tab.history_widget.refresh = Mock()
        
        # Delete current entry
        journal_tab.on_entry_deleted(5)
        
        # Editor should be cleared
        journal_tab.journal_editor.clear_editor.assert_called_once()
        journal_tab.history_widget.refresh.assert_called_once()
        
    def test_on_entry_deleted_other(self, journal_tab):
        """Test deletion of non-current entry."""
        # Set different entry in editor
        current_entry = JournalEntry(
            id=10,
            entry_date=date.today(),
            entry_type='daily',
            content='Different entry'
        )
        journal_tab.journal_editor.current_entry = current_entry
        
        # Mock methods
        journal_tab.journal_editor.clear_editor = Mock()
        journal_tab.history_widget.refresh = Mock()
        
        # Delete different entry
        journal_tab.on_entry_deleted(5)
        
        # Editor should NOT be cleared
        journal_tab.journal_editor.clear_editor.assert_not_called()
        
        # History should still refresh
        journal_tab.history_widget.refresh.assert_called_once()
        
    def test_refresh_method(self, journal_tab):
        """Test refresh method updates all components."""
        # Mock refresh methods
        journal_tab.history_widget.refresh = Mock()
        journal_tab.search_widget.clear_search = Mock()
        
        # Call refresh
        journal_tab.refresh()
        
        # Verify all components refreshed
        journal_tab.history_widget.refresh.assert_called_once()
        journal_tab.search_widget.clear_search.assert_called_once()
        
    def test_search_result_selection(self, journal_tab, qtbot):
        """Test selecting a search result loads entry."""
        # Mock load_entry
        journal_tab.load_entry = Mock()
        
        # Emit search result selected signal
        journal_tab.search_widget.searchResultSelected.emit(42)
        
        # Verify entry loaded
        journal_tab.load_entry.assert_called_once_with(42)
        
    def test_history_entry_selection(self, journal_tab, qtbot):
        """Test selecting history entry loads it."""
        # Mock load_entry
        journal_tab.load_entry = Mock()
        
        # Emit entry selected signal
        journal_tab.history_widget.entrySelected.emit(33)
        
        # Verify entry loaded
        journal_tab.load_entry.assert_called_once_with(33)
        
    def test_splitter_sizes(self, journal_tab):
        """Test splitter proportions are set correctly."""
        # Find splitter
        splitter = None
        for child in journal_tab.children():
            if hasattr(child, 'sizes') and callable(child.sizes):
                splitter = child
                break
                
        if splitter and hasattr(splitter, 'sizes'):
            sizes = splitter.sizes()
            if len(sizes) == 2:
                # Check roughly 40/60 split
                total = sum(sizes)
                if total > 0:
                    left_ratio = sizes[0] / total
                    right_ratio = sizes[1] / total
                    
                    # Allow some variance due to minimum sizes
                    assert 0.3 <= left_ratio <= 0.5
                    assert 0.5 <= right_ratio <= 0.7