"""Unit tests for journal search bar widget.

This module tests the search bar functionality including:
- Search input with debouncing
- Filter panel controls
- Search suggestions and auto-complete
- Result count display
- Keyboard shortcuts
- Signal emission
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock, patch

from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QCompleter, QMenu

from src.ui.journal_search_bar import JournalSearchBar, SearchFilterPanel


class TestSearchFilterPanel:
    """Test the search filter panel."""
    
    def test_panel_initialization(self, qtbot):
        """Test filter panel initialization."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        assert panel.date_from is not None
        assert panel.date_to is not None
        assert hasattr(panel, 'type_checkboxes')
        assert hasattr(panel, 'sort_combo')
        
    def test_default_date_range(self, qtbot):
        """Test default date range is last month to today."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Check default dates
        today = QDate.currentDate()
        month_ago = today.addMonths(-1)
        
        assert panel.date_from.date() == month_ago
        assert panel.date_to.date() == today
        
    def test_entry_type_checkboxes(self, qtbot):
        """Test entry type filter checkboxes."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Check all types exist
        assert 'daily' in panel.type_checkboxes
        assert 'weekly' in panel.type_checkboxes
        assert 'monthly' in panel.type_checkboxes
        
        # Check all checked by default
        for checkbox in panel.type_checkboxes.values():
            assert checkbox.isChecked()
            
    def test_get_filters(self, qtbot):
        """Test getting filter configuration."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Set some filters
        panel.date_from.setDate(QDate(2024, 1, 1))
        panel.date_to.setDate(QDate(2024, 1, 31))
        panel.type_checkboxes['weekly'].setChecked(False)
        panel.sort_combo.setCurrentText("Oldest First")
        
        filters = panel.get_filters()
        
        assert filters['date_from'] == date(2024, 1, 1)
        assert filters['date_to'] == date(2024, 1, 31)
        assert filters['entry_types'] == ['daily', 'monthly']
        assert filters['sort_order'] == 'oldest'
        
    def test_filter_change_signal(self, qtbot):
        """Test filter change signal emission."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Connect signal spy
        signal_spy = []
        panel.filtersChanged.connect(signal_spy.append)
        
        # Change a filter
        panel.type_checkboxes['daily'].setChecked(False)
        
        # Check signal emitted
        assert len(signal_spy) == 1
        filters = signal_spy[0]
        assert 'daily' not in filters['entry_types']
        
    def test_reset_filters(self, qtbot):
        """Test resetting filters to defaults."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Change filters
        panel.type_checkboxes['daily'].setChecked(False)
        panel.sort_combo.setCurrentIndex(1)
        
        # Reset
        panel.reset_filters()
        
        # Check defaults restored
        assert panel.type_checkboxes['daily'].isChecked()
        assert panel.sort_combo.currentIndex() == 0
        
    def test_clear_date_filter(self, qtbot):
        """Test clearing date filters."""
        panel = SearchFilterPanel()
        qtbot.addWidget(panel)
        
        # Set custom dates
        panel.date_from.setDate(QDate(2023, 1, 1))
        panel.date_to.setDate(QDate(2023, 12, 31))
        
        # Clear using button
        clear_btn = panel.findChild(type(panel).clear_dates_btn.__class__, "clear_dates_btn")
        if clear_btn:
            qtbot.mouseClick(clear_btn, Qt.MouseButton.LeftButton)
            
            # Check dates cleared (set to null or very early/late dates)
            filters = panel.get_filters()
            assert filters.get('date_from') is None or filters['date_from'] == date.min
            assert filters.get('date_to') is None or filters['date_to'] == date.max


class TestJournalSearchBar:
    """Test the main search bar widget."""
    
    def test_search_bar_initialization(self, qtbot):
        """Test search bar initialization."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        assert search_bar.search_input is not None
        assert search_bar.filter_button is not None
        assert search_bar.clear_button is not None
        assert search_bar.result_label is not None
        assert search_bar._debounce_timer is not None
        
    def test_placeholder_text(self, qtbot):
        """Test search input placeholder."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        placeholder = search_bar.search_input.placeholderText()
        assert "Search journal entries" in placeholder
        
    def test_search_debouncing(self, qtbot):
        """Test search input debouncing."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Connect signal spy
        signal_spy = []
        search_bar.searchRequested.connect(signal_spy.append)
        
        # Type rapidly
        search_bar.search_input.setText("t")
        search_bar.search_input.setText("te")
        search_bar.search_input.setText("tes")
        search_bar.search_input.setText("test")
        
        # No signal yet (debouncing)
        assert len(signal_spy) == 0
        
        # Wait for debounce timer
        qtbot.wait(350)  # 300ms debounce + buffer
        
        # Now signal should be emitted once
        assert len(signal_spy) == 1
        assert signal_spy[0] == "test"
        
    def test_immediate_search_on_enter(self, qtbot):
        """Test immediate search when pressing Enter."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Connect signal spy
        signal_spy = []
        search_bar.searchRequested.connect(signal_spy.append)
        
        # Type and press Enter
        search_bar.search_input.setText("immediate search")
        qtbot.keyClick(search_bar.search_input, Qt.Key.Key_Return)
        
        # Should emit immediately
        assert len(signal_spy) == 1
        assert signal_spy[0] == "immediate search"
        
    def test_clear_button_functionality(self, qtbot):
        """Test clear button clears search."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Set search text
        search_bar.search_input.setText("test search")
        search_bar.update_result_count(5)
        
        # Connect signal spy
        clear_signal = []
        search_bar.clearRequested.connect(clear_signal.append)
        
        # Click clear
        qtbot.mouseClick(search_bar.clear_button, Qt.MouseButton.LeftButton)
        
        # Check cleared
        assert search_bar.search_input.text() == ""
        assert len(clear_signal) == 1
        
    def test_filter_button_menu(self, qtbot):
        """Test filter button shows menu."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Check menu exists
        assert search_bar.filter_button.menu() is not None
        
        # Show menu
        search_bar.filter_button.showMenu()
        
        # Check filter panel in menu
        menu = search_bar.filter_button.menu()
        assert menu.isVisible()
        
    def test_result_count_display(self, qtbot):
        """Test result count label update."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Initially hidden
        assert not search_bar.result_label.isVisible()
        
        # Update count
        search_bar.update_result_count(42)
        
        # Check visible and text
        assert search_bar.result_label.isVisible()
        assert "42 results" in search_bar.result_label.text()
        
        # Update with 1 result
        search_bar.update_result_count(1)
        assert "1 result" in search_bar.result_label.text()
        
        # Hide on 0 results
        search_bar.update_result_count(0)
        assert not search_bar.result_label.isVisible()
        
    def test_search_suggestions(self, qtbot):
        """Test search suggestions/auto-complete."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Update suggestions
        suggestions = ["exercise", "exercise routine", "exercise goals"]
        search_bar.update_suggestions(suggestions)
        
        # Check completer configured
        completer = search_bar.search_input.completer()
        assert completer is not None
        
        # Check suggestions in model
        model = completer.model()
        assert model.rowCount() == 3
        
    def test_keyboard_shortcuts(self, qtbot):
        """Test keyboard shortcuts."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Test Escape clears search
        search_bar.search_input.setText("test")
        qtbot.keyClick(search_bar.search_input, Qt.Key.Key_Escape)
        assert search_bar.search_input.text() == ""
        
    def test_get_filters_from_panel(self, qtbot):
        """Test getting filters from filter panel."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Set some filters in panel
        search_bar.filter_panel.type_checkboxes['monthly'].setChecked(False)
        
        filters = search_bar.get_filters()
        
        assert 'monthly' not in filters['entry_types']
        assert 'daily' in filters['entry_types']
        assert 'weekly' in filters['entry_types']
        
    def test_focus_search_method(self, qtbot):
        """Test focus_search method."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        # Focus something else first
        search_bar.filter_button.setFocus()
        assert not search_bar.search_input.hasFocus()
        
        # Focus search
        search_bar.focus_search()
        
        # Check focused and selected
        assert search_bar.search_input.hasFocus()
        
    def test_empty_search_not_emitted(self, qtbot):
        """Test that empty searches are not emitted."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        signal_spy = []
        search_bar.searchRequested.connect(signal_spy.append)
        
        # Set empty text and trigger
        search_bar.search_input.setText("   ")
        search_bar._on_search_triggered()
        
        # Should not emit
        assert len(signal_spy) == 0
        
    def test_filter_change_updates(self, qtbot):
        """Test that filter changes emit signal."""
        search_bar = JournalSearchBar()
        qtbot.addWidget(search_bar)
        
        filter_signal = []
        search_bar.filtersChanged.connect(filter_signal.append)
        
        # Change filter in panel
        search_bar.filter_panel.sort_combo.setCurrentIndex(1)
        
        # Should emit
        assert len(filter_signal) == 1
        assert filter_signal[0]['sort_order'] != 'newest'  # Changed from default