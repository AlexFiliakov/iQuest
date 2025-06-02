"""Journal search bar widget with advanced filtering capabilities.

This module provides the search interface for journal entries, including
a search input field, filter controls, and search suggestions.

The search bar supports:
    - Live search with debouncing
    - Search suggestions from history
    - Advanced filter panel
    - Result count display
    - Search progress indication
    - Keyboard shortcuts

Example:
    Basic usage:
        >>> search_bar = JournalSearchBar()
        >>> search_bar.searchRequested.connect(self.on_search)
        >>> search_bar.filtersChanged.connect(self.on_filters_changed)
"""

from typing import Optional, Dict, List, Any
from datetime import date, datetime
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QCompleter, QMenu, QWidgetAction,
    QDateEdit, QCheckBox, QGridLayout, QFrame
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QStringListModel, QDate,
    QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
)
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from .style_manager import StyleManager
from .enhanced_date_edit import EnhancedDateEdit
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SearchFilterPanel(QFrame):
    """Advanced filter panel for search refinement.
    
    Provides date range filtering, entry type selection, and sort options.
    """
    
    filtersChanged = pyqtSignal(dict)  # Emits filter configuration
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the filter panel."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Set up the filter panel UI."""
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Date range section
        date_label = QLabel("Date Range:")
        date_label.setStyleSheet(f"color: {self.style_manager.colors.text_secondary}; font-weight: 600;")
        layout.addWidget(date_label, 0, 0)
        
        self.date_from = EnhancedDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("MMM d, yyyy")
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        layout.addWidget(self.date_from, 0, 1)
        
        date_to_label = QLabel("to")
        date_to_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(date_to_label, 0, 2)
        
        self.date_to = EnhancedDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("MMM d, yyyy")
        self.date_to.setDate(QDate.currentDate())
        layout.addWidget(self.date_to, 0, 3)
        
        # Entry type section
        type_label = QLabel("Entry Types:")
        type_label.setStyleSheet(f"color: {self.style_manager.colors.text_secondary}; font-weight: 600;")
        layout.addWidget(type_label, 1, 0)
        
        type_container = QWidget()
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(16)
        
        self.type_checkboxes = {}
        for entry_type in ['daily', 'weekly', 'monthly']:
            checkbox = QCheckBox(entry_type.capitalize())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_filter_changed)
            self.type_checkboxes[entry_type] = checkbox
            type_layout.addWidget(checkbox)
        
        type_layout.addStretch()
        layout.addWidget(type_container, 1, 1, 1, 3)
        
        # Sort options
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet(f"color: {self.style_manager.colors.text_secondary}; font-weight: 600;")
        layout.addWidget(sort_label, 2, 0)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevance", "Date (Newest)", "Date (Oldest)"])
        self.sort_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.sort_combo, 2, 1)
        
        # Filter presets
        preset_label = QLabel("Presets:")
        preset_label.setStyleSheet(f"color: {self.style_manager.colors.text_secondary}; font-weight: 600;")
        layout.addWidget(preset_label, 3, 0)
        
        preset_container = QWidget()
        preset_layout = QHBoxLayout(preset_container)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        preset_layout.setSpacing(8)
        
        presets = [
            ("This Week", self._apply_this_week),
            ("This Month", self._apply_this_month),
            ("Last 30 Days", self._apply_last_30_days),
            ("All Time", self._apply_all_time)
        ]
        
        for preset_name, preset_func in presets:
            btn = QPushButton(preset_name)
            btn.clicked.connect(preset_func)
            btn.setStyleSheet(self.style_manager.get_button_style('secondary'))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        layout.addWidget(preset_container, 3, 1, 1, 3)
        
        # Connect signals
        self.date_from.dateChanged.connect(self._on_filter_changed)
        self.date_to.dateChanged.connect(self._on_filter_changed)
        
    def _apply_styling(self):
        """Apply consistent styling to the panel."""
        self.setStyleSheet(f"""
            SearchFilterPanel {{
                background-color: {self.style_manager.colors.surface};
                border: 1px solid {self.style_manager.colors.border};
                border-radius: 8px;
            }}
        """)
        
    def _on_filter_changed(self):
        """Handle filter changes and emit updated configuration."""
        filters = self.get_filters()
        self.filtersChanged.emit(filters)
        
    def get_filters(self) -> Dict[str, Any]:
        """Get current filter configuration.
        
        Returns:
            Dictionary with filter settings.
        """
        # Get selected entry types
        selected_types = [
            entry_type for entry_type, checkbox in self.type_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        # Get sort order
        sort_text = self.sort_combo.currentText()
        if sort_text == "Date (Newest)":
            sort_by = "date_desc"
        elif sort_text == "Date (Oldest)":
            sort_by = "date_asc"
        else:
            sort_by = "relevance"
        
        return {
            'date_from': self.date_from.date().toPyDate(),
            'date_to': self.date_to.date().toPyDate(),
            'entry_types': selected_types,
            'sort_by': sort_by
        }
    
    def _apply_this_week(self):
        """Apply 'This Week' preset."""
        today = QDate.currentDate()
        start_of_week = today.addDays(-today.dayOfWeek() + 1)
        self.date_from.setDate(start_of_week)
        self.date_to.setDate(today)
        
    def _apply_this_month(self):
        """Apply 'This Month' preset."""
        today = QDate.currentDate()
        start_of_month = QDate(today.year(), today.month(), 1)
        self.date_from.setDate(start_of_month)
        self.date_to.setDate(today)
        
    def _apply_last_30_days(self):
        """Apply 'Last 30 Days' preset."""
        today = QDate.currentDate()
        self.date_from.setDate(today.addDays(-30))
        self.date_to.setDate(today)
        
    def _apply_all_time(self):
        """Apply 'All Time' preset."""
        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_to.setDate(QDate.currentDate())


class JournalSearchBar(QWidget):
    """Main search bar widget for journal entries.
    
    Provides search input with suggestions, filter button, and result count.
    
    Signals:
        searchRequested(str): Emitted when user initiates a search
        filtersChanged(dict): Emitted when filters are updated
        clearRequested(): Emitted when user clears the search
    """
    
    searchRequested = pyqtSignal(str)
    filtersChanged = pyqtSignal(dict)
    clearRequested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the search bar."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self._filter_panel = None
        self._filter_menu = None
        self._search_timer = QTimer()
        self._search_timer.timeout.connect(self._perform_search)
        self._search_timer.setSingleShot(True)
        self._setup_ui()
        self._apply_styling()
        self._setup_shortcuts()
        
    def _setup_ui(self):
        """Set up the search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search journal entries...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._perform_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        
        # Set up completer for suggestions
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.search_input.setCompleter(self.completer)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._perform_search)
        
        # Filter button
        self.filter_button = QPushButton("Filters")
        self.filter_button.setCheckable(True)
        self.filter_button.clicked.connect(self._toggle_filters)
        
        # Result count label
        self.result_label = QLabel()
        self.result_label.setStyleSheet(f"color: {self.style_manager.colors.text_secondary};")
        self.result_label.hide()  # Initially hidden
        
        # Add widgets to layout
        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.search_button)
        layout.addWidget(self.filter_button)
        layout.addWidget(self.result_label)
        
    def _apply_styling(self):
        """Apply warm color styling to the search bar."""
        # Search input styling
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.style_manager.colors.surface_alt};
                border: 2px solid {self.style_manager.colors.border};
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 14px;
                color: {self.style_manager.colors.text_primary};
            }}
            QLineEdit:focus {{
                border-color: {self.style_manager.colors.primary};
                background-color: {self.style_manager.colors.surface};
            }}
        """)
        
        # Button styling
        self.search_button.setStyleSheet(self.style_manager.get_button_style())
        self.filter_button.setStyleSheet(self.style_manager.get_button_style('secondary'))
        
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+F to focus search
        focus_action = QAction(self)
        focus_action.setShortcut(QKeySequence.StandardKey.Find)
        focus_action.triggered.connect(self.focus_search)
        self.addAction(focus_action)
        
        # Escape to clear search
        clear_action = QAction(self)
        clear_action.setShortcut(Qt.Key.Key_Escape)
        clear_action.triggered.connect(self.clear_search)
        self.search_input.addAction(clear_action)
        
    def _on_text_changed(self, text: str):
        """Handle text changes with debouncing."""
        self._search_timer.stop()
        if text:
            self._search_timer.start(300)  # 300ms debounce
        else:
            self.clearRequested.emit()
            self.update_result_count(0)
            
    def _perform_search(self):
        """Perform the search operation."""
        query = self.search_input.text().strip()
        if query:
            self.searchRequested.emit(query)
            
    def _toggle_filters(self):
        """Toggle the filter panel visibility."""
        if not self._filter_panel:
            self._create_filter_panel()
            
        if self._filter_menu:
            if self._filter_menu.isVisible():
                self._filter_menu.hide()
                self.filter_button.setChecked(False)
            else:
                # Position menu below the filter button
                pos = self.filter_button.mapToGlobal(self.filter_button.rect().bottomLeft())
                self._filter_menu.popup(pos)
                self.filter_button.setChecked(True)
                
    def _create_filter_panel(self):
        """Create the filter panel and menu."""
        self._filter_panel = SearchFilterPanel()
        self._filter_panel.filtersChanged.connect(self.filtersChanged)
        
        # Create menu to hold the panel
        self._filter_menu = QMenu(self)
        self._filter_menu.setStyleSheet(f"""
            QMenu {{
                background-color: transparent;
                border: none;
                padding: 0;
            }}
        """)
        
        # Add panel as widget action
        action = QWidgetAction(self._filter_menu)
        action.setDefaultWidget(self._filter_panel)
        self._filter_menu.addAction(action)
        
        # Update button state when menu closes
        self._filter_menu.aboutToHide.connect(lambda: self.filter_button.setChecked(False))
        
    def update_suggestions(self, suggestions: List[str]):
        """Update search suggestions.
        
        Args:
            suggestions: List of suggested search queries.
        """
        model = QStringListModel(suggestions)
        self.completer.setModel(model)
        
    def update_result_count(self, count: int):
        """Update the result count display.
        
        Args:
            count: Number of search results.
        """
        if count == 0:
            self.result_label.hide()
            self.result_label.setText("")
        else:
            self.result_label.show()
            if count == 1:
                self.result_label.setText("1 result")
            else:
                self.result_label.setText(f"{count} results")
            
    def focus_search(self):
        """Focus the search input field."""
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()
        
    def get_filters(self) -> Dict[str, Any]:
        """Get current filter configuration.
        
        Returns:
            Dictionary with filter settings or None if no filters active.
        """
        if self._filter_panel:
            return self._filter_panel.get_filters()
        return None