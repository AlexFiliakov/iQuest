"""Enhanced calendar heatmap with journal entry indicators.

This module extends the base calendar heatmap to include journal entry
indicators. It overlays small icons on calendar cells to show when
journal entries exist for specific dates.

The enhanced heatmap maintains all existing functionality while adding:
    - Journal entry indicators with type-specific icons
    - Click handling to open journal entries
    - Real-time updates when entries are added/removed
    - Tooltip previews of journal content

Example:
    >>> heatmap = EnhancedCalendarHeatmap(monthly_calculator, data_access)
    >>> heatmap.journal_entry_requested.connect(self.open_journal_editor)
    >>> heatmap.update_data(metric_data)
"""

from typing import Dict, Optional, List, Tuple, Any
from datetime import date, datetime, timedelta
from PyQt6.QtCore import QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter

from .calendar_heatmap import CalendarHeatmapComponent, ViewMode
from ..journal_indicator import JournalIndicator
from ..journal_indicator_mixin import JournalIndicatorMixin
from ...analytics.journal_indicator_service import JournalIndicatorService
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedCalendarHeatmap(CalendarHeatmapComponent, JournalIndicatorMixin):
    """Calendar heatmap with integrated journal entry indicators.
    
    This enhanced version of the calendar heatmap displays journal entry
    indicators on dates that have associated entries. It supports all
    view modes of the base calendar while adding journal functionality.
    
    Signals:
        journal_entry_requested (pyqtSignal): Emitted when user clicks a journal indicator
        
    Args:
        monthly_calculator: Monthly metrics calculator
        data_access: Data access object for journal entries
        parent: Parent widget
    """
    
    def __init__(self, monthly_calculator=None, data_access=None, parent=None):
        """Initialize the enhanced calendar heatmap.
        
        Args:
            monthly_calculator: Monthly metrics calculator
            data_access: Data access object for journal entries
            parent: Parent widget
        """
        super().__init__(monthly_calculator, parent)
        
        # Initialize journal indicators if data_access provided
        if data_access:
            self.init_journal_indicators(data_access)
            self._has_journal_support = True
            
            # Track cell rectangles for indicator positioning
            self._cell_rects: Dict[date, QRect] = {}
            
            # Track rendered indicators to avoid duplicates
            self._rendered_indicators: Dict[str, JournalIndicator] = {}
        else:
            self._has_journal_support = False
            
    def paintEvent(self, event):
        """Override paint event to add journal indicators."""
        # Clear cell tracking for new paint
        if self._has_journal_support:
            self._cell_rects.clear()
            
        # Call parent paint event
        super().paintEvent(event)
        
        # Add journal indicators after main painting
        if self._has_journal_support:
            self._paint_journal_indicators()
            
    def _draw_month_cell(self, painter: QPainter, cell_rect: QRect, 
                        current_date: date, value: Optional[float],
                        is_current_month: bool = True):
        """Draw a single calendar cell and track its position.
        
        This method extends the parent's cell drawing to track cell
        positions for indicator placement.
        
        Args:
            painter: QPainter instance
            cell_rect: Rectangle for the cell
            current_date: Date for this cell
            value: Metric value for this date
            is_current_month: Whether this date is in the current month
        """
        # Call parent method if it exists, otherwise draw default
        if hasattr(super(), '_draw_month_cell'):
            super()._draw_month_cell(painter, cell_rect, current_date, value, is_current_month)
        else:
            # Default cell drawing (this might be handled differently in parent)
            color = self._get_color_for_value(value) if value is not None else self._colors['background']
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(cell_rect, 2, 2)
            
        # Track cell rectangle for indicator positioning
        if self._has_journal_support and is_current_month:
            self._cell_rects[current_date] = QRect(cell_rect)  # Make a copy
            
    def _paint_journal_indicators(self):
        """Paint journal indicators on tracked cells."""
        if not self._cell_rects:
            return
            
        # Get date range from tracked cells
        if self._cell_rects:
            dates = list(self._cell_rects.keys())
            start_date = min(dates)
            end_date = max(dates)
            
            # Get journal indicators for the date range
            indicators = self._indicator_service.get_indicators_for_date_range(
                start_date, end_date
            )
            
            # Create painter for indicators
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw indicators on cells
            for date_key, indicator_data in indicators.items():
                # Parse date from key
                if '_' in date_key:
                    date_str = date_key.split('_')[0]
                    entry_type = date_key.split('_')[1] if '_' in date_key else 'daily'
                else:
                    date_str = date_key
                    entry_type = indicator_data.entry_type
                    
                target_date = date.fromisoformat(date_str)
                
                # Find cell rectangle for this date
                if target_date in self._cell_rects:
                    cell_rect = self._cell_rects[target_date]
                    
                    # Create or update indicator widget
                    self._create_cell_indicator(cell_rect, target_date, indicator_data)
                    
    def _create_cell_indicator(self, cell_rect: QRect, target_date: date, indicator_data):
        """Create a journal indicator for a calendar cell.
        
        Args:
            cell_rect: Rectangle of the calendar cell
            target_date: Date for the indicator
            indicator_data: Journal indicator data
        """
        # Generate unique key for this indicator
        indicator_key = f"{target_date.isoformat()}_{indicator_data.entry_type}"
        
        # Check if indicator already exists
        if indicator_key in self._rendered_indicators:
            indicator = self._rendered_indicators[indicator_key]
            # Update existing indicator
            indicator.update_indicator(
                count=indicator_data.count,
                preview_text=indicator_data.preview_text
            )
            # Reposition if needed
            self._position_cell_indicator(indicator, cell_rect)
        else:
            # Create new indicator
            indicator = JournalIndicator(
                entry_type=indicator_data.entry_type,
                count=indicator_data.count,
                preview_text=indicator_data.preview_text,
                parent=self
            )
            
            # Position the indicator
            self._position_cell_indicator(indicator, cell_rect)
            
            # Connect click signal
            indicator.clicked.connect(
                lambda: self._on_indicator_clicked(target_date, indicator_data.entry_type)
            )
            
            # Store reference
            self._rendered_indicators[indicator_key] = indicator
            
            # Show the indicator
            indicator.show()
            indicator.raise_()
            
    def _position_cell_indicator(self, indicator: JournalIndicator, cell_rect: QRect):
        """Position an indicator within a calendar cell.
        
        Args:
            indicator: The journal indicator widget
            cell_rect: Rectangle of the calendar cell
        """
        # Position in top-right corner of cell with small margin
        margin = 2
        indicator_size = 12  # Smaller size for calendar cells
        
        # Resize indicator for calendar view
        indicator.setFixedSize(indicator_size, indicator_size)
        
        # Calculate position
        x = cell_rect.right() - indicator_size - margin
        y = cell_rect.top() + margin
        
        # Ensure indicator stays within cell bounds
        x = max(cell_rect.left() + margin, x)
        y = max(cell_rect.top() + margin, y)
        
        indicator.move(x, y)
        
    def update_data(self, metric_data: Dict[date, float], 
                   source_name: Optional[str] = None):
        """Update the heatmap with new metric data.
        
        Args:
            metric_data: Dictionary mapping dates to metric values
            source_name: Optional source device/app name
        """
        # Call parent update
        super().update_data(metric_data, source_name)
        
        # Refresh journal indicators if supported
        if self._has_journal_support:
            self.refresh_journal_indicators()
            
    def set_current_date(self, current_date: date):
        """Set the current date for month view.
        
        Args:
            current_date: The date to display
        """
        super().set_current_date(current_date)
        
        # Refresh indicators for new date
        if self._has_journal_support:
            self.refresh_journal_indicators()
            
    def refresh_journal_indicators(self):
        """Refresh all journal indicators on the calendar."""
        if not self._has_journal_support:
            return
            
        # Clear existing widget indicators
        for indicator in self._rendered_indicators.values():
            indicator.deleteLater()
        self._rendered_indicators.clear()
        
        # Trigger repaint to recreate indicators
        self.update()
        
    def clear_journal_indicators(self):
        """Remove all journal indicators from the calendar."""
        if not self._has_journal_support:
            return
            
        # Clear all indicators
        for indicator in self._rendered_indicators.values():
            indicator.deleteLater()
        self._rendered_indicators.clear()
        
    def _on_indicator_clicked(self, target_date: date, entry_type: str):
        """Handle journal indicator click.
        
        Args:
            target_date: Date of the clicked indicator
            entry_type: Type of journal entry
        """
        # Emit signal to open journal entry
        self.journal_entry_requested.emit(target_date, entry_type)
        
        logger.info(f"Journal indicator clicked: {entry_type} entry for {target_date}")
        
    def connect_to_journal_manager(self, journal_manager):
        """Connect to journal manager for real-time updates.
        
        Args:
            journal_manager: The journal manager instance
        """
        if not self._has_journal_support:
            return
            
        # Use mixin's connection method
        super().connect_to_journal_manager(journal_manager)
        
    def resizeEvent(self, event):
        """Handle resize events to reposition indicators."""
        super().resizeEvent(event)
        
        # Refresh indicators on resize
        if self._has_journal_support:
            self.update()  # This will trigger indicator repositioning