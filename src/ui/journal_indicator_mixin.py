"""Mixin for adding journal entry indicators to dashboard widgets.

This module provides a mixin class that can be added to existing dashboard
widgets to easily integrate journal entry indicators. It handles indicator
positioning, updates, and click events.

The mixin provides:
    - Automatic indicator creation and positioning
    - Click handling to open journal entries
    - Real-time updates when entries change
    - Consistent behavior across all dashboard views

Example:
    Adding indicators to a daily dashboard:
    
    >>> class DailyDashboard(QWidget, JournalIndicatorMixin):
    ...     def __init__(self, data_access):
    ...         super().__init__()
    ...         self.init_journal_indicators(data_access)
    ...         
    ...     def on_date_cell_created(self, cell, cell_date):
    ...         self.add_journal_indicator_to_widget(cell, cell_date, 'daily')
"""

from typing import Dict, Optional, List, Tuple
from datetime import date
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QPoint, pyqtSignal

from .journal_indicator import JournalIndicator
from ..analytics.journal_indicator_service import JournalIndicatorService, IndicatorData
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class JournalIndicatorMixin:
    """Mixin class for adding journal indicators to dashboard widgets.
    
    This mixin provides methods for managing journal entry indicators
    on dashboard views. It should be mixed with QWidget-based classes.
    
    Signals:
        journal_entry_requested (pyqtSignal): Emitted when user clicks an indicator
    """
    
    # Signal for opening journal entries
    journal_entry_requested = pyqtSignal(date, str)  # date, entry_type
    
    def init_journal_indicators(self, data_access):
        """Initialize the journal indicator system.
        
        This method should be called in the __init__ of the host widget
        after calling super().__init__().
        
        Args:
            data_access: Data access object for database operations
        """
        # Initialize service
        self._indicator_service = JournalIndicatorService(data_access)
        self._indicator_service.indicators_updated.connect(self._on_indicators_updated)
        self._indicator_service.cache_refreshed.connect(self._on_cache_refreshed)
        
        # Track active indicators
        self._active_indicators: Dict[str, JournalIndicator] = {}
        
        # Track widget-to-date mapping for updates
        self._widget_date_map: Dict[QWidget, Tuple[date, str]] = {}
        
    def add_journal_indicator_to_widget(self, 
                                      widget: QWidget, 
                                      target_date: date,
                                      entry_type: str = 'daily',
                                      position: str = 'top-right'):
        """Add a journal indicator to a widget if entries exist.
        
        Args:
            widget (QWidget): The widget to add the indicator to
            target_date (date): The date to check for entries
            entry_type (str): Type of entry to check for
            position (str): Position of indicator ('top-right', 'top-left', etc.)
        """
        # Check for existing entries
        indicator_data = self._indicator_service.get_indicator_for_date(target_date, entry_type)
        
        if indicator_data:
            # Create and position indicator
            indicator = self._create_indicator(widget, indicator_data, position)
            
            # Store references
            date_key = indicator_data.date_key
            self._active_indicators[date_key] = indicator
            self._widget_date_map[widget] = (target_date, entry_type)
            
            # Connect click signal
            indicator.clicked.connect(
                lambda: self._on_indicator_clicked(target_date, entry_type)
            )
            
    def add_journal_indicators_to_calendar(self, 
                                         calendar_widget: QWidget,
                                         year: int,
                                         month: int):
        """Add journal indicators to a calendar widget for a month.
        
        Args:
            calendar_widget (QWidget): The calendar widget
            year (int): Year to display
            month (int): Month to display (1-12)
        """
        # Get all indicators for the month
        indicators = self._indicator_service.get_month_indicators(year, month)
        
        # Add indicators to calendar cells
        for date_key, indicator_data in indicators.items():
            # Parse date from key
            if '_' in date_key:
                date_str = date_key.split('_')[0]
            else:
                date_str = date_key
                
            target_date = date.fromisoformat(date_str)
            
            # Find the calendar cell for this date
            cell = self._find_calendar_cell(calendar_widget, target_date)
            if cell:
                self.add_journal_indicator_to_widget(
                    cell, target_date, indicator_data.entry_type
                )
                
    def refresh_journal_indicators(self):
        """Refresh all journal indicators on the current view."""
        # Clear existing indicators
        for indicator in self._active_indicators.values():
            indicator.deleteLater()
        self._active_indicators.clear()
        
        # Re-add indicators for all tracked widgets
        for widget, (target_date, entry_type) in self._widget_date_map.items():
            if widget and not widget.isHidden():
                self.add_journal_indicator_to_widget(widget, target_date, entry_type)
                
    def clear_journal_indicators(self):
        """Remove all journal indicators from the view."""
        for indicator in self._active_indicators.values():
            indicator.deleteLater()
        self._active_indicators.clear()
        self._widget_date_map.clear()
        
    def _create_indicator(self, 
                         parent_widget: QWidget,
                         indicator_data: IndicatorData,
                         position: str) -> JournalIndicator:
        """Create a journal indicator widget.
        
        Args:
            parent_widget (QWidget): Parent widget for the indicator
            indicator_data (IndicatorData): Data for the indicator
            position (str): Position string ('top-right', etc.)
            
        Returns:
            JournalIndicator: Created indicator widget
        """
        indicator = JournalIndicator(
            entry_type=indicator_data.entry_type,
            count=indicator_data.count,
            preview_text=indicator_data.preview_text,
            parent=parent_widget
        )
        
        # Position the indicator
        self._position_indicator(indicator, parent_widget, position)
        
        # Show the indicator
        indicator.show()
        indicator.raise_()  # Ensure it's on top
        
        return indicator
        
    def _position_indicator(self, 
                           indicator: JournalIndicator,
                           parent: QWidget,
                           position: str):
        """Position an indicator on its parent widget.
        
        Args:
            indicator (JournalIndicator): The indicator to position
            parent (QWidget): Parent widget
            position (str): Position string
        """
        # Calculate position based on string
        margin = 4
        indicator_size = indicator.DEFAULT_SIZE
        
        if position == 'top-right':
            x = parent.width() - indicator_size - margin
            y = margin
        elif position == 'top-left':
            x = margin
            y = margin
        elif position == 'bottom-right':
            x = parent.width() - indicator_size - margin
            y = parent.height() - indicator_size - margin
        elif position == 'bottom-left':
            x = margin
            y = parent.height() - indicator_size - margin
        elif position == 'center':
            x = (parent.width() - indicator_size) // 2
            y = (parent.height() - indicator_size) // 2
        else:
            # Default to top-right
            x = parent.width() - indicator_size - margin
            y = margin
            
        indicator.move(x, y)
        
    def _find_calendar_cell(self, calendar_widget: QWidget, target_date: date) -> Optional[QWidget]:
        """Find a calendar cell widget for a specific date.
        
        This is a placeholder that should be overridden by specific
        calendar implementations.
        
        Args:
            calendar_widget (QWidget): The calendar widget
            target_date (date): The date to find
            
        Returns:
            Optional[QWidget]: The cell widget if found
        """
        # This should be implemented by the specific calendar widget
        # For now, return None
        logger.warning("_find_calendar_cell not implemented for this calendar type")
        return None
        
    def _on_indicator_clicked(self, target_date: date, entry_type: str):
        """Handle indicator click event.
        
        Args:
            target_date (date): Date of the clicked indicator
            entry_type (str): Type of entry
        """
        logger.info(f"Journal indicator clicked for {entry_type} entry on {target_date}")
        
        # Emit signal to open journal entry
        self.journal_entry_requested.emit(target_date, entry_type)
        
    def _on_indicators_updated(self, date_key: str):
        """Handle indicators updated signal from service.
        
        Args:
            date_key (str): Date key that was updated
        """
        # Find and update the specific indicator
        if date_key in self._active_indicators:
            indicator = self._active_indicators[date_key]
            
            # Get updated data
            indicator_data = None
            for widget, (target_date, entry_type) in self._widget_date_map.items():
                if self._indicator_service._get_date_key(target_date, entry_type) == date_key:
                    indicator_data = self._indicator_service.get_indicator_for_date(
                        target_date, entry_type
                    )
                    break
                    
            if indicator_data:
                # Update existing indicator
                indicator.update_indicator(
                    count=indicator_data.count,
                    preview_text=indicator_data.preview_text
                )
            else:
                # Remove indicator if no entries
                indicator.deleteLater()
                del self._active_indicators[date_key]
                
    def _on_cache_refreshed(self):
        """Handle cache refreshed signal from service."""
        # Refresh all indicators
        self.refresh_journal_indicators()
        
    def connect_to_journal_manager(self, journal_manager):
        """Connect to journal manager for real-time updates.
        
        Args:
            journal_manager: The journal manager instance
        """
        if hasattr(journal_manager, 'entrySaved'):
            journal_manager.entrySaved.connect(
                lambda date_str, entry_type: self._on_entry_saved(date_str, entry_type)
            )
            
        if hasattr(journal_manager, 'entryDeleted'):
            journal_manager.entryDeleted.connect(
                lambda date_str, entry_type: self._on_entry_deleted(date_str, entry_type)
            )
            
    def _on_entry_saved(self, date_str: str, entry_type: str):
        """Handle journal entry saved event.
        
        Args:
            date_str (str): ISO format date string
            entry_type (str): Type of entry saved
        """
        # Convert date string to date object
        try:
            entry_date = date.fromisoformat(date_str)
            
            # Create a dummy entry for the service
            from ..models import JournalEntry
            dummy_entry = JournalEntry(
                entry_date=entry_date,
                entry_type=entry_type,
                content=""  # Content will be fetched by service
            )
            
            # Notify service
            self._indicator_service.on_entry_saved(dummy_entry)
            
        except Exception as e:
            logger.error(f"Error handling entry saved event: {e}")
            
    def _on_entry_deleted(self, date_str: str, entry_type: str):
        """Handle journal entry deleted event.
        
        Args:
            date_str (str): ISO format date string
            entry_type (str): Type of entry deleted
        """
        try:
            entry_date = date.fromisoformat(date_str)
            self._indicator_service.on_entry_deleted(entry_date, entry_type)
            
        except Exception as e:
            logger.error(f"Error handling entry deleted event: {e}")