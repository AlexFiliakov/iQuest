"""Service for managing journal entry indicators across dashboard views.

This module provides efficient data access and caching for journal entry
indicators. It queries the database for journal entries and maintains a
cache to minimize database access when updating dashboard views.

The service supports:
    - Efficient batch queries for date ranges
    - Caching with automatic invalidation
    - Real-time updates when entries are added/modified/deleted
    - Preview text extraction for tooltips
    - Entry count aggregation by date

Example:
    Basic usage in a dashboard view:
    
    >>> service = JournalIndicatorService(data_access)
    >>> indicators = service.get_indicators_for_date_range(
    ...     start_date=date(2024, 1, 1),
    ...     end_date=date(2024, 1, 31)
    ... )
    >>> for date_key, indicator_data in indicators.items():
    ...     print(f"{date_key}: {indicator_data['count']} entries")
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime, timedelta
from collections import defaultdict
import threading
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from ..models import JournalEntry
from ..data_access import DataAccess
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class IndicatorData:
    """Data structure for journal entry indicators.
    
    Attributes:
        date_key (str): ISO format date string
        entry_type (str): Type of entry ('daily', 'weekly', 'monthly')
        count (int): Number of entries
        preview_text (str): Preview of the most recent entry
        entry_ids (List[int]): List of entry IDs for navigation
    """
    date_key: str
    entry_type: str
    count: int
    preview_text: str
    entry_ids: List[int]


class JournalIndicatorService(QObject):
    """Service for managing journal entry indicators with caching.
    
    This service provides efficient access to journal entry data for
    dashboard indicators. It maintains a cache of indicator data and
    handles real-time updates.
    
    Attributes:
        indicators_updated (pyqtSignal): Emitted when indicator data changes
        cache_refreshed (pyqtSignal): Emitted when cache is refreshed
        
    Args:
        data_access (DataAccess): Data access object for database operations
    """
    
    # Signals
    indicators_updated = pyqtSignal(str)  # date_key that was updated
    cache_refreshed = pyqtSignal()
    
    # Cache configuration
    CACHE_DURATION_MINUTES = 30
    PREVIEW_LENGTH = 150
    
    def __init__(self, data_access: DataAccess):
        """Initialize the journal indicator service.
        
        Args:
            data_access (DataAccess): Data access object for database operations
        """
        super().__init__()
        self.data_access = data_access
        
        # Cache storage
        self._cache: Dict[str, IndicatorData] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_lock = threading.RLock()
        
        # Track active date ranges for efficient updates
        self._active_ranges: List[Tuple[date, date]] = []
        
    def get_indicators_for_date_range(self, 
                                     start_date: date, 
                                     end_date: date,
                                     entry_type: Optional[str] = None) -> Dict[str, IndicatorData]:
        """Get journal indicators for a date range.
        
        Args:
            start_date (date): Start date of the range
            end_date (date): End date of the range
            entry_type (Optional[str]): Filter by entry type if specified
            
        Returns:
            Dict[str, IndicatorData]: Dictionary mapping date keys to indicator data
            
        Example:
            >>> indicators = service.get_indicators_for_date_range(
            ...     date(2024, 1, 1), date(2024, 1, 31), 'daily'
            ... )
        """
        with self._cache_lock:
            # Register this date range as active BEFORE refreshing cache
            self._register_active_range(start_date, end_date)
            
            # Check if cache needs refresh
            if self._should_refresh_cache():
                self._refresh_cache()
            
            # Filter cached data for requested range
            results = {}
            
            # If a specific entry type is requested, just check relevant keys
            if entry_type:
                # Check each date in range for the specific type
                current_date = start_date
                while current_date <= end_date:
                    date_key = self._get_date_key(current_date, entry_type)
                    if date_key in self._cache:
                        results[date_key] = self._cache[date_key]
                    current_date += timedelta(days=1)
            else:
                # Return all indicators in the date range
                for date_key, indicator in self._cache.items():
                    # Parse the date from the key
                    if '_' in date_key:
                        # Weekly or monthly entry
                        date_part = date_key.split('_')[0]
                    else:
                        # Daily entry
                        date_part = date_key
                        
                    try:
                        indicator_date = date.fromisoformat(date_part)
                        if start_date <= indicator_date <= end_date:
                            results[date_key] = indicator
                    except ValueError:
                        # Skip invalid dates
                        continue
                
            return results
            
    def get_indicator_for_date(self, target_date: date, entry_type: str) -> Optional[IndicatorData]:
        """Get journal indicator for a specific date and type.
        
        Args:
            target_date (date): The date to check
            entry_type (str): The entry type to look for
            
        Returns:
            Optional[IndicatorData]: Indicator data if entries exist, None otherwise
        """
        with self._cache_lock:
            # Ensure cache is fresh
            if self._should_refresh_cache():
                self._refresh_cache()
                
            # Generate appropriate date key based on entry type
            date_key = self._get_date_key(target_date, entry_type)
            return self._cache.get(date_key)
            
    def get_week_indicators(self, week_start: date) -> Dict[str, IndicatorData]:
        """Get all journal indicators for a week.
        
        Args:
            week_start (date): Monday of the week
            
        Returns:
            Dict[str, IndicatorData]: Indicators for the week
        """
        week_end = week_start + timedelta(days=6)
        return self.get_indicators_for_date_range(week_start, week_end)
        
    def get_month_indicators(self, year: int, month: int) -> Dict[str, IndicatorData]:
        """Get all journal indicators for a month.
        
        Args:
            year (int): Year
            month (int): Month (1-12)
            
        Returns:
            Dict[str, IndicatorData]: Indicators for the month
        """
        import calendar
        
        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        return self.get_indicators_for_date_range(first_day, last_day)
        
    def refresh_indicators(self, date_key: Optional[str] = None):
        """Refresh indicator data, optionally for a specific date.
        
        Args:
            date_key (Optional[str]): Specific date to refresh, or None for all
        """
        with self._cache_lock:
            if date_key:
                # Refresh specific date
                self._refresh_date_indicator(date_key)
                self.indicators_updated.emit(date_key)
            else:
                # Full refresh
                self._refresh_cache()
                self.cache_refreshed.emit()
                
    def on_entry_saved(self, entry: JournalEntry):
        """Handle journal entry saved event.
        
        Args:
            entry (JournalEntry): The saved journal entry
        """
        # Update cache for this entry's date
        date_key = self._get_date_key(entry.entry_date, entry.entry_type)
        
        with self._cache_lock:
            # Refresh the specific date
            self._refresh_date_indicator(date_key)
            
        # Emit update signal
        self.indicators_updated.emit(date_key)
        
    def on_entry_deleted(self, entry_date: date, entry_type: str):
        """Handle journal entry deleted event.
        
        Args:
            entry_date (date): Date of the deleted entry
            entry_type (str): Type of the deleted entry
        """
        # Update cache for this date
        date_key = self._get_date_key(entry_date, entry_type)
        
        with self._cache_lock:
            # Refresh or remove from cache
            self._refresh_date_indicator(date_key)
            
        # Emit update signal
        self.indicators_updated.emit(date_key)
        
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed.
        
        Returns:
            bool: True if cache needs refresh
        """
        if not self._cache_timestamp:
            return True
            
        age = datetime.now() - self._cache_timestamp
        return age.total_seconds() > (self.CACHE_DURATION_MINUTES * 60)
        
    def _refresh_cache(self):
        """Refresh the entire cache from database."""
        try:
            # Clear existing cache
            self._cache.clear()
            
            # Get all journal entries from active ranges
            all_entries = []
            for start_date, end_date in self._active_ranges:
                entries = self.data_access.get_journal_entries(start_date, end_date)
                all_entries.extend(entries)
                
            # If no active ranges, get recent entries (last 90 days)
            if not self._active_ranges:
                end_date = date.today()
                start_date = end_date - timedelta(days=90)
                all_entries = self.data_access.get_journal_entries(start_date, end_date)
                
            # Process entries into indicators
            self._process_entries_to_indicators(all_entries)
            
            # Update timestamp
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Cache refreshed with {len(self._cache)} indicators from {len(all_entries)} entries")
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
            
    def _refresh_date_indicator(self, date_key: str):
        """Refresh indicator for a specific date.
        
        Args:
            date_key (str): ISO format date string
        """
        try:
            # Parse date from key
            target_date = date.fromisoformat(date_key)
            
            # Query entries for this specific date
            entries = self.data_access.get_journal_entries(target_date, target_date)
            
            if entries:
                # Process entries for this date
                self._process_entries_to_indicators(entries)
            else:
                # Remove from cache if no entries
                self._cache.pop(date_key, None)
                
        except Exception as e:
            logger.error(f"Error refreshing date indicator for {date_key}: {e}")
            
    def _process_entries_to_indicators(self, entries: List[JournalEntry]):
        """Process journal entries into indicator data.
        
        Args:
            entries (List[JournalEntry]): List of journal entries to process
        """
        # Group entries by date and type
        grouped = defaultdict(list)
        
        for entry in entries:
            date_key = self._get_date_key(entry.entry_date, entry.entry_type)
            grouped[date_key].append(entry)
            
        # Create indicators for each group
        for date_key, date_entries in grouped.items():
            if not date_entries:
                continue
                
            # Sort by updated time (most recent first)
            date_entries.sort(
                key=lambda e: e.updated_at or e.created_at or datetime.min,
                reverse=True
            )
            
            # Get the most recent entry for preview
            latest_entry = date_entries[0]
            preview_text = self._extract_preview(latest_entry.content)
            
            # Create indicator data
            indicator = IndicatorData(
                date_key=date_key,
                entry_type=latest_entry.entry_type,
                count=len(date_entries),
                preview_text=preview_text,
                entry_ids=[e.id for e in date_entries if e.id]
            )
            
            self._cache[date_key] = indicator
            
    def _get_date_key(self, entry_date: date, entry_type: str) -> str:
        """Generate a cache key for a date and entry type.
        
        Args:
            entry_date (date): The entry date
            entry_type (str): The entry type
            
        Returns:
            str: Cache key
        """
        if entry_type == 'daily':
            return entry_date.isoformat()
        elif entry_type == 'weekly':
            # Use Monday of the week as key
            days_since_monday = entry_date.weekday()
            week_start = entry_date - timedelta(days=days_since_monday)
            return f"{week_start.isoformat()}_weekly"
        else:  # monthly
            # Use first day of month as key
            month_start = date(entry_date.year, entry_date.month, 1)
            return f"{month_start.isoformat()}_monthly"
            
    def _extract_preview(self, content: str) -> str:
        """Extract preview text from journal content.
        
        Args:
            content (str): Full journal content
            
        Returns:
            str: Preview text (truncated and cleaned)
        """
        if not content:
            return ""
            
        # Remove excessive whitespace
        preview = ' '.join(content.split())
        
        # Truncate to preview length
        if len(preview) > self.PREVIEW_LENGTH:
            preview = preview[:self.PREVIEW_LENGTH].rsplit(' ', 1)[0] + "..."
            
        return preview
        
    def _register_active_range(self, start_date: date, end_date: date):
        """Register a date range as active for caching.
        
        Args:
            start_date (date): Start of range
            end_date (date): End of range
        """
        # Check if range already exists or overlaps
        for existing_start, existing_end in self._active_ranges:
            if (start_date >= existing_start and end_date <= existing_end):
                # Already covered
                return
                
        # Add new range (could optimize by merging overlapping ranges)
        self._active_ranges.append((start_date, end_date))
        
        # Limit number of active ranges
        if len(self._active_ranges) > 10:
            # Remove oldest range
            self._active_ranges.pop(0)
            
    def clear_cache(self):
        """Clear all cached indicator data."""
        with self._cache_lock:
            self._cache.clear()
            self._cache_timestamp = None
            self._active_ranges.clear()
            
        logger.info("Journal indicator cache cleared")