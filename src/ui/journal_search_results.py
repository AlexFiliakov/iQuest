"""Journal search results display widget.

This module provides the search results visualization for journal entries,
including result items with highlights, infinite scrolling, and result actions.

The results widget supports:
    - Custom result item rendering with highlights
    - Infinite scrolling for large result sets
    - Result grouping by date
    - Click to open entry
    - Context menu actions
    - Empty state display

Example:
    Basic usage:
        >>> results_widget = SearchResultsWidget()
        >>> results_widget.resultClicked.connect(self.open_entry)
        >>> results_widget.display_results(search_results)
"""

from typing import List, Optional, Dict, Any
from datetime import date
from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStyledItemDelegate,
    QStyleOptionViewItem, QMenu, QApplication, QStyle
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QSize, QRect, QPoint, QModelIndex,
    QAbstractItemModel, QTimer
)
from PyQt6.QtGui import (
    QPainter, QFont, QFontMetrics, QColor, QPalette,
    QTextDocument, QTextOption, QAction
)
import logging

from ..style_manager import StyleManager
from ..analytics.journal_search_engine import SearchResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SearchResultDelegate(QStyledItemDelegate):
    """Custom delegate for rendering search result items.
    
    Handles custom painting of search results with:
    - Entry date and type badges
    - Highlighted snippet text
    - Match count indicator
    - Hover effects
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the delegate."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self._hover_index = None
        
    def paint(self, painter: QPainter, option: QStyleOptionViewItem,
              index: QModelIndex):
        """Paint a search result item.
        
        Args:
            painter: QPainter instance for drawing.
            option: Style options for the item.
            index: Model index of the item.
        """
        painter.save()
        
        # Get the search result data
        result = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            super().paint(painter, option, index)
            painter.restore()
            return
        
        # Handle selection/hover states
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(self.style_manager.colors.primary_light))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(self.style_manager.colors.surface_alt))
        else:
            painter.fillRect(option.rect, QColor(self.style_manager.colors.surface))
        
        # Set up fonts
        title_font = QFont(painter.font())
        title_font.setPointSize(11)
        title_font.setBold(True)
        
        snippet_font = QFont(painter.font())
        snippet_font.setPointSize(10)
        
        metadata_font = QFont(painter.font())
        metadata_font.setPointSize(9)
        
        # Calculate positions
        padding = 12
        x = option.rect.x() + padding
        y = option.rect.y() + padding
        width = option.rect.width() - (2 * padding)
        
        # Draw date and type
        painter.setFont(title_font)
        date_text = result.entry_date.strftime("%B %d, %Y")
        painter.setPen(QColor(self.style_manager.colors.text_primary))
        painter.drawText(x, y + title_font.pointSize(), date_text)
        
        # Draw entry type badge
        type_rect = QRect(
            x + painter.fontMetrics().horizontalAdvance(date_text) + 8,
            y,
            60, 20
        )
        self._draw_type_badge(painter, type_rect, result.entry_type)
        
        # Draw relevance score (if in debug mode)
        if logger.isEnabledFor(logging.DEBUG):
            score_text = f"Score: {result.score:.2f}"
            score_rect = QRect(
                option.rect.right() - 80 - padding,
                y,
                80, 20
            )
            painter.setFont(metadata_font)
            painter.setPen(QColor(self.style_manager.colors.text_secondary))
            painter.drawText(score_rect, Qt.AlignmentFlag.AlignRight, score_text)
        
        # Draw snippet with highlights
        y += 28
        snippet_rect = QRect(x, y, width, option.rect.height() - y - padding)
        self._draw_highlighted_snippet(painter, snippet_rect, result.snippet, snippet_font)
        
        painter.restore()
        
    def _draw_type_badge(self, painter: QPainter, rect: QRect, entry_type: str):
        """Draw entry type badge.
        
        Args:
            painter: QPainter instance.
            rect: Rectangle for the badge.
            entry_type: Type of journal entry.
        """
        # Badge colors based on type
        colors = {
            'daily': '#4CAF50',
            'weekly': '#2196F3', 
            'monthly': '#FF9800'
        }
        
        color = colors.get(entry_type, '#757575')
        
        # Draw rounded rectangle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(rect, 10, 10)
        
        # Draw text
        painter.setPen(QColor('#FFFFFF'))
        font = QFont(painter.font())
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, entry_type.upper())
        
    def _draw_highlighted_snippet(self, painter: QPainter, rect: QRect,
                                 snippet: str, font: QFont):
        """Draw snippet text with HTML highlights.
        
        Args:
            painter: QPainter instance.
            rect: Rectangle for the text.
            snippet: Snippet HTML with <mark> tags.
            font: Font to use for text.
        """
        # Use QTextDocument for HTML rendering
        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setHtml(snippet)
        
        # Apply custom styles for highlights
        doc.setDefaultStyleSheet(f"""
            mark {{
                background-color: {self.style_manager.colors.warning};
                color: {self.style_manager.colors.text_primary};
                padding: 2px;
            }}
        """)
        
        # Set text options
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WordWrap)
        doc.setDefaultTextOption(option)
        
        # Limit width and draw
        doc.setTextWidth(rect.width())
        painter.translate(rect.topLeft())
        doc.drawContents(painter, QRect(0, 0, rect.width(), rect.height()))
        painter.translate(-rect.topLeft())
        
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Calculate size hint for a result item.
        
        Args:
            option: Style options.
            index: Model index.
            
        Returns:
            Recommended size for the item.
        """
        return QSize(option.rect.width(), 80)


class EmptyStateWidget(QWidget):
    """Widget shown when there are no search results."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the empty state widget."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the empty state UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Icon or illustration could go here
        
        # Title
        title = QLabel("No results found")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {self.style_manager.colors.text_primary};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        self.subtitle = QLabel("Try adjusting your search terms or filters")
        self.subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {self.style_manager.colors.text_secondary};
        """)
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle)
        
        # Search tips
        tips = QLabel(
            "Tips:\n"
            "• Use quotes for exact phrases: \"morning routine\"\n"
            "• Use * for wildcards: exerc*\n"
            "• Exclude terms with -: workout -skip"
        )
        tips.setStyleSheet(f"""
            font-size: 12px;
            color: {self.style_manager.colors.text_secondary};
            padding: 20px;
            background-color: {self.style_manager.colors.surface_alt};
            border-radius: 8px;
        """)
        tips.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(tips)
        
    def set_query(self, query: str):
        """Update empty state for specific query.
        
        Args:
            query: The search query that returned no results.
        """
        self.subtitle.setText(f'No results found for "{query}"')


class SearchResultsWidget(QListWidget):
    """Widget for displaying search results with infinite scroll.
    
    Signals:
        resultClicked(int): Emitted when a result is clicked (entry_id)
        loadMoreRequested(): Emitted when scrolled near bottom
        copyRequested(str): Emitted when user copies snippet
    """
    
    resultClicked = pyqtSignal(int)
    loadMoreRequested = pyqtSignal()
    copyRequested = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the results widget."""
        super().__init__(parent)
        self.style_manager = StyleManager()
        self._results = []
        self._empty_state = None
        self._loading_more = False
        self._setup_ui()
        self._setup_scrolling()
        
    def _setup_ui(self):
        """Set up the results widget UI."""
        # Set custom delegate
        self.setItemDelegate(SearchResultDelegate(self))
        
        # Configure list widget
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSpacing(4)
        self.setUniformItemSizes(False)
        
        # Styling
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.style_manager.colors.background};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: {self.style_manager.colors.surface};
                border: 1px solid {self.style_manager.colors.border};
                border-radius: 8px;
                margin: 4px;
                padding: 8px;
            }}
            QListWidget::item:selected {{
                background-color: {self.style_manager.colors.primary_light};
                border-color: {self.style_manager.colors.primary};
            }}
            QListWidget::item:hover {{
                background-color: {self.style_manager.colors.surface_alt};
            }}
        """)
        
        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _setup_scrolling(self):
        """Set up infinite scrolling behavior."""
        scrollbar = self.verticalScrollBar()
        scrollbar.valueChanged.connect(self._check_scroll_position)
        
    def _check_scroll_position(self, value: int):
        """Check if scrolled near bottom for infinite loading.
        
        Args:
            value: Current scroll position.
        """
        scrollbar = self.verticalScrollBar()
        if not self._loading_more and value > scrollbar.maximum() * 0.8:
            self._loading_more = True
            self.loadMoreRequested.emit()
            
    def display_results(self, results: List[SearchResult], append: bool = False):
        """Display search results.
        
        Args:
            results: List of search results to display.
            append: Whether to append to existing results.
        """
        if not append:
            self.clear()
            self._results = []
            
        self._results.extend(results)
        self._loading_more = False
        
        # Add result items
        for result in results:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, result)
            item.setSizeHint(QSize(self.width(), 80))
            self.addItem(item)
            
        # Show empty state if no results
        if not self._results:
            self._show_empty_state()
        else:
            self._hide_empty_state()
            
    def _show_empty_state(self):
        """Show the empty state widget."""
        if not self._empty_state:
            self._empty_state = EmptyStateWidget(self)
            
        # Position in center
        self._empty_state.resize(self.width() - 40, 300)
        self._empty_state.move(
            20,
            (self.height() - self._empty_state.height()) // 2
        )
        self._empty_state.show()
        
    def _hide_empty_state(self):
        """Hide the empty state widget."""
        if self._empty_state:
            self._empty_state.hide()
            
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle result item click.
        
        Args:
            item: The clicked item.
        """
        result = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(result, SearchResult):
            self.resultClicked.emit(result.entry_id)
            
    def _show_context_menu(self, position: QPoint):
        """Show context menu for result item.
        
        Args:
            position: Position where menu was requested.
        """
        item = self.itemAt(position)
        if not item:
            return
            
        result = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            return
            
        menu = QMenu(self)
        
        # Open action
        open_action = QAction("Open Entry", self)
        open_action.triggered.connect(lambda: self.resultClicked.emit(result.entry_id))
        menu.addAction(open_action)
        
        # Copy snippet action
        copy_action = QAction("Copy Snippet", self)
        copy_action.triggered.connect(lambda: self._copy_snippet(result))
        menu.addAction(copy_action)
        
        # Copy date action
        copy_date_action = QAction("Copy Date", self)
        copy_date_action.triggered.connect(
            lambda: QApplication.clipboard().setText(result.entry_date.isoformat())
        )
        menu.addAction(copy_date_action)
        
        menu.exec(self.mapToGlobal(position))
        
    def _copy_snippet(self, result: SearchResult):
        """Copy snippet text without HTML tags.
        
        Args:
            result: The search result.
        """
        # Remove HTML tags
        import re
        clean_snippet = re.sub(r'<[^>]+>', '', result.snippet)
        QApplication.clipboard().setText(clean_snippet)
        self.copyRequested.emit(clean_snippet)
        
    def set_search_query(self, query: str):
        """Set the current search query for empty state.
        
        Args:
            query: The search query.
        """
        if self._empty_state:
            self._empty_state.set_query(query)
            
    def clear_results(self):
        """Clear all search results."""
        self.clear()
        self._results = []
        self._hide_empty_state()
        
    def resizeEvent(self, event):
        """Handle resize events to adjust empty state.
        
        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        if self._empty_state and self._empty_state.isVisible():
            self._empty_state.resize(self.width() - 40, 300)
            self._empty_state.move(
                20,
                (self.height() - self._empty_state.height()) // 2
            )