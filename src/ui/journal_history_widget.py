"""Journal History Widget for browsing all journal entries.

This module provides a comprehensive history view for journal entries with:
- Multiple view modes (list, timeline, calendar)
- Virtual scrolling for performance with large datasets
- Filtering by date and entry type
- Entry preview without opening
- Integration with search and editor

Classes:
    JournalHistoryWidget: Main widget for journal history display
    JournalHistoryModel: Data model with virtual scrolling support
    JournalEntryDelegate: Custom rendering for entry cards
    FilterToolbar: Filtering and sorting controls
    ViewportManager: Virtual scrolling management

Example:
    >>> from src.data_access import DataAccess
    >>> data_access = DataAccess("health.db")
    >>> history_widget = JournalHistoryWidget(data_access.journal_db)
    >>> history_widget.show()
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from collections import defaultdict
import logging

from PyQt6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QTimer, QRect, QPoint,
    pyqtSignal, QSize, QRectF, QDateTime, QDate
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListView, QToolBar,
    QComboBox, QLabel, QStyledItemDelegate, QStyleOptionViewItem,
    QApplication, QSplitter, QTextBrowser, QPushButton, QFrame,
    QScrollArea, QGridLayout, QCalendarWidget, QGraphicsView,
    QGraphicsScene, QStackedWidget, QToolButton, QSizePolicy
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush,
    QIcon, QPixmap, QPalette, QTextDocument, QTextOption,
    QFontDatabase, QLinearGradient
)

from src.models import JournalEntry
from src.ui.journal_editor_widget import SegmentedControl
from src.ui.style_manager import ColorPalette

# Create instance for compatibility
ThemeColors = ColorPalette()
FONTS = {
    'DEFAULT_FAMILY': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
}

logger = logging.getLogger(__name__)


class ViewMode:
    """View mode constants."""
    LIST = "list"
    TIMELINE = "timeline"
    CALENDAR = "calendar"
    COMPACT = "compact"


@dataclass
class FilterSettings:
    """Filter settings for history view."""
    entry_type: Optional[str] = None  # None, 'daily', 'weekly', 'monthly'
    date_range: Optional[Tuple[date, date]] = None
    sort_order: str = "newest"  # 'newest', 'oldest'
    search_text: Optional[str] = None


class JournalHistoryWidget(QWidget):
    """Main widget for browsing journal entry history.
    
    Provides multiple view modes, filtering, and virtual scrolling
    for efficient display of large numbers of journal entries.
    
    Attributes:
        entrySelected (pyqtSignal): Emitted when entry selected (entry_id)
        entryDeleted (pyqtSignal): Emitted when entry deleted (entry_id)
        journal_db: Database interface for journal operations
        current_view_mode: Active view mode (list/timeline/calendar)
        filter_settings: Current filter configuration
    
    Example:
        >>> widget = JournalHistoryWidget(journal_db)
        >>> widget.entrySelected.connect(lambda id: print(f"Selected: {id}"))
        >>> widget.set_view_mode(ViewMode.TIMELINE)
    """
    
    entrySelected = pyqtSignal(int)  # entry_id
    entryDeleted = pyqtSignal(int)   # entry_id
    
    def __init__(self, journal_db, parent=None):
        """Initialize journal history widget.
        
        Args:
            journal_db: JournalDatabase instance for data access
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.journal_db = journal_db
        self.current_view_mode = ViewMode.LIST
        self.filter_settings = FilterSettings()
        self.setup_ui()
        self.load_entries()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Filter toolbar
        self.filter_toolbar = FilterToolbar()
        self.filter_toolbar.filtersChanged.connect(self.on_filters_changed)
        layout.addWidget(self.filter_toolbar)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # View stack for different modes
        self.view_stack = QStackedWidget()
        
        # List view
        self.list_view = QListView()
        self.model = JournalHistoryModel(self.journal_db)
        self.list_view.setModel(self.model)
        self.delegate = JournalEntryDelegate()
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.list_view.setUniformItemSizes(False)
        self.list_view.setSpacing(8)
        self.list_view.clicked.connect(self.on_entry_clicked)
        
        # Apply styling
        self.list_view.setStyleSheet(f"""
            QListView {{
                background-color: {ThemeColors.background};
                border: none;
                outline: none;
            }}
            QListView::item {{
                background-color: transparent;
                padding: 0px;
            }}
            QListView::item:selected {{
                background-color: transparent;
            }}
        """)
        
        self.view_stack.addWidget(self.list_view)
        
        # Timeline view (placeholder)
        self.timeline_view = QLabel("Timeline View - Coming Soon")
        self.timeline_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_stack.addWidget(self.timeline_view)
        
        # Calendar view (placeholder)
        self.calendar_view = QLabel("Calendar View - Coming Soon")
        self.calendar_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_stack.addWidget(self.calendar_view)
        
        splitter.addWidget(self.view_stack)
        
        # Preview panel
        self.preview_panel = PreviewPanel()
        self.preview_panel.editRequested.connect(self.on_edit_requested)
        self.preview_panel.deleteRequested.connect(self.on_delete_requested)
        self.preview_panel.setVisible(False)  # Hidden by default
        splitter.addWidget(self.preview_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
        splitter.setCollapsible(1, True)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.text_secondary};
                padding: 8px;
                background-color: {ThemeColors.surface};
                border-top: 1px solid {ThemeColors.border};
            }}
        """)
        layout.addWidget(self.status_label)
        
        self.update_status()
        
    def load_entries(self):
        """Load entries from database."""
        try:
            self.model.refresh()
            self.update_status()
        except Exception as e:
            logger.error(f"Error loading entries: {e}")
            
    def on_filters_changed(self, filters: dict):
        """Handle filter changes.
        
        Args:
            filters: Dictionary of filter settings
        """
        self.filter_settings.entry_type = filters.get('entry_type')
        self.filter_settings.date_range = filters.get('date_range')
        self.filter_settings.sort_order = filters.get('sort_order', 'newest')
        self.filter_settings.search_text = filters.get('search_text')
        
        self.model.set_filters(self.filter_settings)
        self.update_status()
        
    def on_entry_clicked(self, index: QModelIndex):
        """Handle entry click.
        
        Args:
            index: Model index of clicked entry
        """
        entry = index.data(JournalEntryRole.ENTRY)
        if entry:
            self.preview_panel.set_entry(entry)
            self.preview_panel.setVisible(True)
            
    def on_edit_requested(self, entry_id: int):
        """Handle edit request from preview.
        
        Args:
            entry_id: ID of entry to edit
        """
        self.entrySelected.emit(entry_id)
        
    def on_delete_requested(self, entry_id: int):
        """Handle delete request from preview.
        
        Args:
            entry_id: ID of entry to delete
        """
        # TODO: Add confirmation dialog
        try:
            self.journal_db.delete_entry(entry_id)
            self.entryDeleted.emit(entry_id)
            self.load_entries()
            self.preview_panel.setVisible(False)
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")
            
    def set_view_mode(self, mode: str):
        """Change view mode.
        
        Args:
            mode: One of ViewMode constants
        """
        self.current_view_mode = mode
        index_map = {
            ViewMode.LIST: 0,
            ViewMode.TIMELINE: 1,
            ViewMode.CALENDAR: 2
        }
        self.view_stack.setCurrentIndex(index_map.get(mode, 0))
        
    def update_status(self):
        """Update status bar text."""
        total = self.model.total_count
        visible = self.model.rowCount()
        
        if self.filter_settings.entry_type or self.filter_settings.date_range:
            status = f"Showing {visible} of {total} entries (filtered)"
        else:
            status = f"Showing {visible} of {total} entries"
            
        self.status_label.setText(status)
        
    def refresh(self):
        """Refresh the view."""
        self.load_entries()


class JournalEntryRole:
    """Custom data roles for journal entries."""
    ENTRY = Qt.ItemDataRole.UserRole + 1
    DATE = Qt.ItemDataRole.UserRole + 2
    TYPE = Qt.ItemDataRole.UserRole + 3
    PREVIEW = Qt.ItemDataRole.UserRole + 4
    WORD_COUNT = Qt.ItemDataRole.UserRole + 5


class JournalHistoryModel(QAbstractListModel):
    """Data model for journal history with virtual scrolling.
    
    Implements lazy loading and filtering for efficient handling
    of large numbers of journal entries.
    
    Attributes:
        journal_db: Database interface
        entries: Currently loaded entries
        filtered_entries: Entries after filtering
        chunk_size: Number of entries to load at once
        filters: Current filter settings
    """
    
    def __init__(self, journal_db, parent=None):
        """Initialize model.
        
        Args:
            journal_db: JournalDatabase instance
            parent: Optional parent object
        """
        super().__init__(parent)
        self.journal_db = journal_db
        self.entries = []
        self.filtered_entries = []
        self.chunk_size = 50
        self.filters = FilterSettings()
        self.total_count = 0
        self._loaded_count = 0
        
    def rowCount(self, parent=QModelIndex()):
        """Return number of visible rows.
        
        Args:
            parent: Parent index (unused)
            
        Returns:
            Number of currently loaded entries
        """
        return len(self.filtered_entries)
        
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Provide data for given index and role.
        
        Args:
            index: Model index
            role: Data role
            
        Returns:
            Requested data or None
        """
        if not index.isValid() or index.row() >= len(self.filtered_entries):
            return None
            
        entry = self.filtered_entries[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
        elif role == JournalEntryRole.ENTRY:
            return entry
        elif role == JournalEntryRole.DATE:
            return entry.entry_date
        elif role == JournalEntryRole.TYPE:
            return entry.entry_type
        elif role == JournalEntryRole.PREVIEW:
            return entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
        elif role == JournalEntryRole.WORD_COUNT:
            return len(entry.content.split())
            
        return None
        
    def canFetchMore(self, parent=QModelIndex()):
        """Check if more data can be fetched.
        
        Args:
            parent: Parent index (unused)
            
        Returns:
            True if more entries available
        """
        return self._loaded_count < self.total_count
        
    def fetchMore(self, parent=QModelIndex()):
        """Load next chunk of entries.
        
        Args:
            parent: Parent index (unused)
        """
        if not self.canFetchMore():
            return
            
        # Calculate how many to fetch
        remainder = self.total_count - self._loaded_count
        items_to_fetch = min(self.chunk_size, remainder)
        
        if items_to_fetch <= 0:
            return
            
        # Fetch next chunk
        try:
            new_entries = self._fetch_entries(
                offset=self._loaded_count,
                limit=items_to_fetch
            )
            
            if new_entries:
                begin_row = len(self.filtered_entries)
                self.beginInsertRows(QModelIndex(), begin_row, begin_row + len(new_entries) - 1)
                self.filtered_entries.extend(new_entries)
                self._loaded_count += len(new_entries)
                self.endInsertRows()
                
        except Exception as e:
            logger.error(f"Error fetching more entries: {e}")
            
    def set_filters(self, filters: FilterSettings):
        """Apply new filters.
        
        Args:
            filters: New filter settings
        """
        self.filters = filters
        self.refresh()
        
    def refresh(self):
        """Refresh all data with current filters."""
        self.beginResetModel()
        
        try:
            # Reset state
            self.entries.clear()
            self.filtered_entries.clear()
            self._loaded_count = 0
            
            # Get total count with filters
            self.total_count = self._get_filtered_count()
            
            # Load initial chunk
            if self.total_count > 0:
                initial_entries = self._fetch_entries(0, self.chunk_size)
                self.filtered_entries = initial_entries
                self._loaded_count = len(initial_entries)
                
        except Exception as e:
            logger.error(f"Error refreshing entries: {e}")
            
        self.endResetModel()
        
    def _get_filtered_count(self) -> int:
        """Get total count of entries matching filters.
        
        Returns:
            Total count of matching entries
        """
        # Build query conditions
        conditions = []
        params = []
        
        if self.filters.entry_type:
            conditions.append("entry_type = ?")
            params.append(self.filters.entry_type)
            
        if self.filters.date_range:
            start_date, end_date = self.filters.date_range
            conditions.append("entry_date BETWEEN ? AND ?")
            params.extend([start_date.isoformat(), end_date.isoformat()])
            
        # Get count from database
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) FROM journal_entries {where_clause}"
        
        return self.journal_db.execute_query(query, params)[0][0]
        
    def _fetch_entries(self, offset: int, limit: int) -> List[JournalEntry]:
        """Fetch entries from database.
        
        Args:
            offset: Starting position
            limit: Maximum entries to fetch
            
        Returns:
            List of journal entries
        """
        # Build query
        conditions = []
        params = []
        
        if self.filters.entry_type:
            conditions.append("entry_type = ?")
            params.append(self.filters.entry_type)
            
        if self.filters.date_range:
            start_date, end_date = self.filters.date_range
            conditions.append("entry_date BETWEEN ? AND ?")
            params.extend([start_date.isoformat(), end_date.isoformat()])
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Apply sort order
        order_by = "entry_date DESC" if self.filters.sort_order == "newest" else "entry_date ASC"
        
        query = f"""
            SELECT id, entry_date, entry_type, content, 
                   week_start_date, month_year, version, created_at, updated_at
            FROM journal_entries
            {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        # Execute query and convert to JournalEntry objects
        rows = self.journal_db.execute_query(query, params)
        entries = []
        
        for row in rows:
            # Extract week_start_date and month_year based on entry type
            week_start_date = None
            month_year = None
            
            if row[2] == 'weekly' and row[4]:  # entry_type is weekly
                week_start_date = datetime.fromisoformat(row[4]).date()
            elif row[2] == 'monthly' and row[5]:  # entry_type is monthly
                month_year = row[5]
                
            entry = JournalEntry(
                id=row[0],
                entry_date=datetime.fromisoformat(row[1]).date(),
                entry_type=row[2],
                content=row[3],
                week_start_date=week_start_date,
                month_year=month_year,
                version=row[6] if len(row) > 6 else 1,
                created_at=datetime.fromisoformat(row[7]) if len(row) > 7 else None,
                updated_at=datetime.fromisoformat(row[8]) if len(row) > 8 else None
            )
            entries.append(entry)
            
        return entries


class JournalEntryDelegate(QStyledItemDelegate):
    """Custom delegate for rendering journal entry cards.
    
    Provides rich visual representation of journal entries with
    date badges, type indicators, and content preview.
    """
    
    def __init__(self, parent=None):
        """Initialize delegate.
        
        Args:
            parent: Optional parent object
        """
        super().__init__(parent)
        self.card_margin = 8
        self.card_padding = 16
        self.card_radius = 8
        self.min_height = 120
        
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """Paint journal entry card.
        
        Args:
            painter: QPainter instance
            option: Style options
            index: Model index
        """
        entry = index.data(JournalEntryRole.ENTRY)
        if not entry:
            return
            
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate card rect
        card_rect = QRectF(
            option.rect.x() + self.card_margin,
            option.rect.y() + self.card_margin,
            option.rect.width() - 2 * self.card_margin,
            option.rect.height() - 2 * self.card_margin
        )
        
        # Draw card background
        if option.state & QStyleOptionViewItem.StateFlag.State_Selected:
            painter.setPen(QPen(QColor(ThemeColors.primary), 2))
            painter.setBrush(QBrush(QColor(ThemeColors.surface)))
        elif option.state & QStyleOptionViewItem.StateFlag.State_MouseOver:
            painter.setPen(QPen(QColor(ThemeColors.border), 1))
            painter.setBrush(QBrush(QColor(ThemeColors.primary_light)))
        else:
            painter.setPen(QPen(QColor(ThemeColors.border), 1))
            painter.setBrush(QBrush(QColor(ThemeColors.surface)))
            
        painter.drawRoundedRect(card_rect, self.card_radius, self.card_radius)
        
        # Content area
        content_rect = card_rect.adjusted(
            self.card_padding, self.card_padding,
            -self.card_padding, -self.card_padding
        )
        
        # Draw date badge
        date_font = QFont(FONTS['DEFAULT_FAMILY'])
        date_font.setWeight(QFont.Weight.Bold)
        date_font.setPointSize(10)
        painter.setFont(date_font)
        
        date_text = entry.entry_date.strftime("%b %d, %Y")
        date_metrics = QFontMetrics(date_font)
        date_rect = QRectF(
            content_rect.x(),
            content_rect.y(),
            date_metrics.horizontalAdvance(date_text) + 12,
            date_metrics.height() + 8
        )
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(ThemeColors.primary)))
        painter.drawRoundedRect(date_rect, 4, 4)
        
        painter.setPen(QPen(QColor(ThemeColors.surface)))
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignCenter, date_text)
        
        # Draw entry type icon
        type_font = QFont(FONTS['DEFAULT_FAMILY'])
        type_font.setPointSize(9)
        painter.setFont(type_font)
        painter.setPen(QPen(QColor(ThemeColors.text_secondary)))
        
        type_text = entry.entry_type.capitalize()
        type_rect = QRectF(
            content_rect.right() - 80,
            content_rect.y(),
            80,
            date_rect.height()
        )
        painter.drawText(type_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, type_text)
        
        # Draw preview text
        preview_font = QFont(FONTS['DEFAULT_FAMILY'])
        preview_font.setPointSize(10)
        painter.setFont(preview_font)
        painter.setPen(QPen(QColor(ThemeColors.text_primary)))
        
        preview_rect = QRectF(
            content_rect.x(),
            date_rect.bottom() + 8,
            content_rect.width(),
            content_rect.height() - date_rect.height() - 24
        )
        
        preview_text = index.data(JournalEntryRole.PREVIEW)
        painter.drawText(preview_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, preview_text)
        
        # Draw word count
        word_count = index.data(JournalEntryRole.WORD_COUNT)
        count_text = f"{word_count} words"
        
        count_font = QFont(FONTS['DEFAULT_FAMILY'])
        count_font.setPointSize(9)
        painter.setFont(count_font)
        painter.setPen(QPen(QColor(ThemeColors.text_secondary)))
        
        count_rect = QRectF(
            content_rect.x(),
            content_rect.bottom() - 20,
            content_rect.width(),
            20
        )
        painter.drawText(count_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, count_text)
        
        painter.restore()
        
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Calculate size hint for entry.
        
        Args:
            option: Style options
            index: Model index
            
        Returns:
            Recommended size for item
        """
        # Calculate height based on content
        preview_text = index.data(JournalEntryRole.PREVIEW)
        if preview_text:
            font = QFont(FONTS['DEFAULT_FAMILY'])
            font.setPointSize(10)
            metrics = QFontMetrics(font)
            
            # Account for wrapping
            text_width = option.rect.width() - 2 * self.card_margin - 2 * self.card_padding
            text_height = metrics.boundingRect(
                0, 0, text_width, 0,
                Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                preview_text
            ).height()
            
            # Total height: margins + padding + date badge + text + word count
            total_height = (
                2 * self.card_margin +
                2 * self.card_padding +
                30 +  # Date badge
                8 +   # Spacing
                text_height +
                20    # Word count
            )
            
            return QSize(option.rect.width(), max(self.min_height, total_height))
            
        return QSize(option.rect.width(), self.min_height)


class FilterToolbar(QToolBar):
    """Toolbar for filtering and sorting journal entries.
    
    Emits filtersChanged signal when any filter is modified.
    
    Attributes:
        filtersChanged (pyqtSignal): Emitted with filter dictionary
    """
    
    filtersChanged = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize filter toolbar.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up toolbar UI."""
        self.setMovable(False)
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {ThemeColors.surface_alt};
                border-bottom: 1px solid {ThemeColors.border};
                padding: 8px;
                spacing: 8px;
            }}
        """)
        
        # View mode selector
        view_label = QLabel("View:")
        view_label.setStyleSheet(f"color: {ThemeColors.text_secondary};")
        self.addWidget(view_label)
        
        self.view_selector = SegmentedControl(["List", "Timeline", "Calendar"])
        self.view_selector.current_index = 0
        self.addWidget(self.view_selector)
        
        self.addSeparator()
        
        # Entry type filter
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"color: {ThemeColors.text_secondary};")
        self.addWidget(type_label)
        
        self.type_filter = SegmentedControl(["All", "Daily", "Weekly", "Monthly"])
        self.type_filter.current_index = 0
        self.type_filter.selectionChanged.connect(self.on_filters_changed)
        self.addWidget(self.type_filter)
        
        self.addSeparator()
        
        # Sort order
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet(f"color: {ThemeColors.text_secondary};")
        self.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Newest First", "Oldest First"])
        self.sort_combo.currentTextChanged.connect(self.on_filters_changed)
        self.addWidget(self.sort_combo)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
        
        # TODO: Add date range filter
        
    def on_filters_changed(self):
        """Handle filter change and emit signal."""
        filters = {
            'entry_type': self._get_entry_type(),
            'sort_order': 'newest' if self.sort_combo.currentIndex() == 0 else 'oldest',
            # TODO: Add date_range when implemented
        }
        self.filtersChanged.emit(filters)
        
    def _get_entry_type(self) -> Optional[str]:
        """Get selected entry type.
        
        Returns:
            Entry type string or None for all
        """
        index = self.type_filter.current_index
        type_map = {0: None, 1: 'daily', 2: 'weekly', 3: 'monthly'}
        return type_map.get(index)


class PreviewPanel(QWidget):
    """Panel for previewing journal entry details.
    
    Shows full entry metadata and provides quick actions.
    
    Attributes:
        editRequested (pyqtSignal): Emitted when edit requested (entry_id)
        deleteRequested (pyqtSignal): Emitted when delete requested (entry_id)
    """
    
    editRequested = pyqtSignal(int)
    deleteRequested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """Initialize preview panel.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.current_entry = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up preview panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Entry Preview")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.text_primary};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setStyleSheet(f"""
            QToolButton {{
                color: {ThemeColors.text_secondary};
                border: none;
                font-size: 20px;
                padding: 4px;
            }}
            QToolButton:hover {{
                color: {ThemeColors.text_primary};
                background-color: {ThemeColors.primary_light};
                border-radius: 4px;
            }}
        """)
        close_btn.clicked.connect(lambda: self.setVisible(False))
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Metadata section
        self.metadata_label = QLabel()
        self.metadata_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.text_secondary};
                padding: 8px 0;
            }}
        """)
        layout.addWidget(self.metadata_label)
        
        # Content viewer
        self.content_view = QTextBrowser()
        self.content_view.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {ThemeColors.surface};
                border: 1px solid {ThemeColors.border};
                border-radius: 8px;
                padding: 12px;
                color: {ThemeColors.text_primary};
            }}
        """)
        layout.addWidget(self.content_view, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.primary};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.primary_hover};
            }}
        """)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.error};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C62828;
            }}
        """)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def set_entry(self, entry: JournalEntry):
        """Set entry to preview.
        
        Args:
            entry: Journal entry to display
        """
        self.current_entry = entry
        
        if entry:
            # Update title
            self.title_label.setText(f"{entry.entry_type.capitalize()} Entry")
            
            # Update metadata
            created_str = entry.created_at.strftime("%B %d, %Y at %I:%M %p")
            updated_str = entry.updated_at.strftime("%B %d, %Y at %I:%M %p")
            word_count = len(entry.content.split())
            
            metadata = f"""
            <b>Date:</b> {entry.entry_date.strftime("%B %d, %Y")}<br>
            <b>Words:</b> {word_count}<br>
            <b>Created:</b> {created_str}<br>
            <b>Modified:</b> {updated_str}
            """
            self.metadata_label.setText(metadata.strip())
            
            # Update content
            self.content_view.setPlainText(entry.content)
            
    def on_edit_clicked(self):
        """Handle edit button click."""
        if self.current_entry:
            self.editRequested.emit(self.current_entry.id)
            
    def on_delete_clicked(self):
        """Handle delete button click."""
        if self.current_entry:
            self.deleteRequested.emit(self.current_entry.id)