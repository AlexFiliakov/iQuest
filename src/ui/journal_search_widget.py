"""Integrated journal search widget combining search bar, results, and engine.

This module provides the complete search experience for journal entries by
integrating the search bar, results display, and search engine components.

The widget provides:
    - Unified search interface
    - Search execution and result display
    - Progress indication during search
    - Integration with journal editor
    - Search analytics tracking

Example:
    Basic usage:
        >>> search_widget = JournalSearchWidget()
        >>> search_widget.entryRequested.connect(self.open_entry)
        >>> layout.addWidget(search_widget)
"""

from typing import Optional, Dict, List, Any
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar,
    QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QIcon

from .journal_search_bar import JournalSearchBar
from .journal_search_results import SearchResultsWidget
from ..analytics.journal_search_engine import JournalSearchEngine, SearchResult
from ..database import DatabaseManager
from ..style_manager import StyleManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SearchWorker(QThread):
    """Background worker for executing searches."""
    
    resultsReady = pyqtSignal(list)  # List of SearchResult
    errorOccurred = pyqtSignal(str)
    progressUpdate = pyqtSignal(int, str)  # percent, message
    
    def __init__(self, search_engine: JournalSearchEngine):
        """Initialize the search worker.
        
        Args:
            search_engine: The search engine instance to use.
        """
        super().__init__()
        self.search_engine = search_engine
        self.query = ""
        self.filters = None
        self.limit = 50
        self._is_cancelled = False
        
    def set_search_params(self, query: str, filters: Optional[Dict[str, Any]] = None,
                         limit: int = 50):
        """Set search parameters for the next search.
        
        Args:
            query: Search query string.
            filters: Optional search filters.
            limit: Maximum results to return.
        """
        self.query = query
        self.filters = filters
        self.limit = limit
        self._is_cancelled = False
        
    def cancel(self):
        """Cancel the current search operation."""
        self._is_cancelled = True
        
    def run(self):
        """Execute the search in background thread."""
        try:
            self.progressUpdate.emit(20, "Parsing query...")
            if self._is_cancelled:
                return
                
            self.progressUpdate.emit(40, "Searching entries...")
            if self._is_cancelled:
                return
                
            # Execute search
            results = self.search_engine.search(
                self.query,
                self.filters,
                self.limit
            )
            
            if self._is_cancelled:
                return
                
            self.progressUpdate.emit(80, "Processing results...")
            
            # Emit results
            self.resultsReady.emit(results)
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            self.errorOccurred.emit(str(e))


class JournalSearchWidget(QWidget):
    """Complete journal search interface widget.
    
    Integrates search bar, results display, and search engine to provide
    a unified search experience.
    
    Signals:
        entryRequested(int): Emitted when user wants to open an entry
        searchStarted(str): Emitted when search begins
        searchCompleted(int): Emitted when search completes with result count
    """
    
    entryRequested = pyqtSignal(int)
    searchStarted = pyqtSignal(str)
    searchCompleted = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the search widget."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.db = DatabaseManager()
        self.search_engine = JournalSearchEngine()
        self.search_worker = SearchWorker(self.search_engine)
        self._current_query = ""
        self._current_offset = 0
        self._has_more_results = True
        self._setup_ui()
        self._connect_signals()
        self._load_search_suggestions()
        
    def _setup_ui(self):
        """Set up the search widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search bar
        self.search_bar = JournalSearchBar()
        layout.addWidget(self.search_bar)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.style_manager.colors.border};
                border-radius: 4px;
                text-align: center;
                background-color: {self.style_manager.colors.surface};
            }}
            QProgressBar::chunk {{
                background-color: {self.style_manager.colors.primary};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Results widget
        self.results_widget = SearchResultsWidget()
        layout.addWidget(self.results_widget, 1)
        
    def _connect_signals(self):
        """Connect internal signals."""
        # Search bar signals
        self.search_bar.searchRequested.connect(self._on_search_requested)
        self.search_bar.filtersChanged.connect(self._on_filters_changed)
        self.search_bar.clearRequested.connect(self._clear_search)
        
        # Results widget signals
        self.results_widget.resultClicked.connect(self.entryRequested)
        self.results_widget.loadMoreRequested.connect(self._load_more_results)
        
        # Search worker signals
        self.search_worker.resultsReady.connect(self._on_results_ready)
        self.search_worker.errorOccurred.connect(self._on_search_error)
        self.search_worker.progressUpdate.connect(self._update_progress)
        
    def _load_search_suggestions(self):
        """Load initial search suggestions from history."""
        try:
            # Get recent searches for suggestions
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT query
                    FROM search_history
                    ORDER BY searched_at DESC
                    LIMIT 20
                """)
                
                suggestions = [row['query'] for row in cursor.fetchall()]
                self.search_bar.update_suggestions(suggestions)
                
        except Exception as e:
            logger.error(f"Failed to load search suggestions: {e}")
            
    @pyqtSlot(str)
    def _on_search_requested(self, query: str):
        """Handle search request from search bar.
        
        Args:
            query: The search query.
        """
        if not query.strip():
            return
            
        # Cancel any ongoing search
        if self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait()
            
        # Update state
        self._current_query = query
        self._current_offset = 0
        self._has_more_results = True
        
        # Get filters
        filters = self.search_bar.get_filters()
        
        # Show progress
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Emit signal
        self.searchStarted.emit(query)
        
        # Start search
        self.search_worker.set_search_params(query, filters, limit=50)
        self.search_worker.start()
        
    @pyqtSlot(dict)
    def _on_filters_changed(self, filters: Dict[str, Any]):
        """Handle filter changes.
        
        Args:
            filters: Updated filter configuration.
        """
        # Re-run current search with new filters if we have a query
        if self._current_query:
            self._on_search_requested(self._current_query)
            
    @pyqtSlot(list)
    def _on_results_ready(self, results: List[SearchResult]):
        """Handle search results from worker.
        
        Args:
            results: List of search results.
        """
        # Hide progress
        self.progress_bar.hide()
        
        # Display results
        append = self._current_offset > 0
        self.results_widget.display_results(results, append=append)
        
        # Update result count
        total_count = len(results) + self._current_offset
        self.search_bar.update_result_count(total_count)
        
        # Update suggestions based on query
        if results and self._current_offset == 0:
            self._update_suggestions_from_results(results)
            
        # Check if more results available
        self._has_more_results = len(results) == 50
        
        # Update offset for pagination
        self._current_offset += len(results)
        
        # Emit completion signal
        self.searchCompleted.emit(total_count)
        
        # Set query for empty state
        if not results and self._current_offset == 0:
            self.results_widget.set_search_query(self._current_query)
            
    @pyqtSlot(str)
    def _on_search_error(self, error_message: str):
        """Handle search errors.
        
        Args:
            error_message: The error message.
        """
        # Hide progress
        self.progress_bar.hide()
        
        # Show error message
        QMessageBox.warning(
            self,
            "Search Error",
            f"An error occurred during search:\n{error_message}"
        )
        
    @pyqtSlot(int, str)
    def _update_progress(self, percent: int, message: str):
        """Update progress bar.
        
        Args:
            percent: Progress percentage.
            message: Progress message.
        """
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{message} ({percent}%)")
        
    def _clear_search(self):
        """Clear search results and reset state."""
        self._current_query = ""
        self._current_offset = 0
        self._has_more_results = True
        self.results_widget.clear_results()
        self.search_bar.update_result_count(0)
        
    def _load_more_results(self):
        """Load more results for infinite scrolling."""
        if not self._has_more_results or not self._current_query:
            return
            
        if self.search_worker.isRunning():
            return
            
        # Get filters
        filters = self.search_bar.get_filters()
        
        # Adjust filters for pagination
        if filters:
            filters = filters.copy()
        else:
            filters = {}
            
        # Start search with offset
        self.search_worker.set_search_params(
            self._current_query,
            filters,
            limit=50
        )
        self.search_worker.start()
        
    def _update_suggestions_from_results(self, results: List[SearchResult]):
        """Update search suggestions based on results.
        
        Args:
            results: Search results to analyze.
        """
        try:
            # Get query suggestions from search engine
            suggestions = self.search_engine.suggest_queries(
                self._current_query[:3],  # Use first 3 chars
                limit=10
            )
            
            # Add current query if it got results
            if results and self._current_query not in suggestions:
                suggestions.insert(0, self._current_query)
                
            self.search_bar.update_suggestions(suggestions)
            
        except Exception as e:
            logger.error(f"Failed to update suggestions: {e}")
            
    def focus_search(self):
        """Focus the search input field."""
        self.search_bar.focus_search()
        
    def set_initial_query(self, query: str):
        """Set and execute an initial search query.
        
        Args:
            query: The search query to execute.
        """
        self.search_bar.search_input.setText(query)
        self._on_search_requested(query)
        
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search usage statistics.
        
        Returns:
            Dictionary with search statistics.
        """
        return self.search_engine.get_search_stats()