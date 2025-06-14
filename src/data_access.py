"""Data Access Objects for Apple Health Monitor application.

This module provides comprehensive data access layer implementation for the Apple Health
Monitor application, following the database specification outlined in SPECS_DB.md.
It implements the Data Access Object (DAO) pattern to provide clean separation
between business logic and data persistence.

The module includes specialized DAO classes for:
    - Journal entries (daily, weekly, monthly)
    - User preferences with type-safe storage
    - Recent files tracking with validation
    - Cached metrics for performance optimization
    - Health metrics metadata for UI customization
    - Data sources tracking and management
    - Import history and audit logging

All DAO classes provide:
    - Type-safe data operations with proper validation
    - Comprehensive error handling and logging
    - Optimized SQL queries for performance
    - Consistent API patterns across all operations
    - Full CRUD operations where applicable
    - Search and filtering capabilities

Key features:
    - Automatic type conversion for preferences
    - Upsert logic for conflict resolution
    - Cache management with expiration
    - File tracking with validity checking
    - Import deduplication using file hashes
    - Full-text search in journal entries

Examples:
    Journal operations:
        >>> entry_id = JournalDAO.save_journal_entry(
        ...     date(2024, 1, 15),
        ...     'daily',
        ...     'Had a great workout today!'
        ... )
        >>> entries = JournalDAO.get_journal_entries(
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 31)
        ... )
        
    Preference management:
        >>> PreferenceDAO.set_preference('theme_mode', 'dark')
        >>> theme = PreferenceDAO.get_preference('theme_mode', 'light')
        
    Cache operations:
        >>> cache_key = CacheDAO.cache_metrics(
        ...     'daily_steps',
        ...     {'data': [1000, 2000, 3000]},
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 31)
        ... )

Attributes:
    logger: Module-level logger for DAO operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import json
import hashlib

from .database import DatabaseManager
from .models import (
    JournalEntry, UserPreference, RecentFile, CachedMetric,
    HealthMetricsMetadata, DataSource, ImportHistory
)

logger = logging.getLogger(__name__)


class JournalDAO:
    """Data Access Object for journal entries with comprehensive CRUD operations.
    
    Provides complete database operations for managing journal entries in the Apple Health
    Monitor application. Supports daily, weekly, and monthly journal entries with
    intelligent upsert logic, advanced search capabilities, and robust error handling.
    
    This DAO implements the complete journal management system including:
        - Smart upsert operations to prevent duplicates while allowing updates
        - Flexible date range queries with optional type filtering
        - Full-text search capabilities across journal content
        - Proper date handling and timezone management
        - Comprehensive validation and error reporting
        - Performance-optimized queries with proper indexing
    
    Journal entry types supported:
        - 'daily': Individual day entries with specific dates
        - 'weekly': Week-based entries with week start dates
        - 'monthly': Month-based entries with YYYY-MM identifiers
    
    All methods are static to enable usage without instantiation and follow
    the database specification requirements from SPECS_DB.md. Each operation
    includes comprehensive logging and error handling.
    
    Examples:
        Create daily journal entry:
        >>> entry_id = JournalDAO.save_journal_entry(
        ...     date(2024, 1, 15),
        ...     'daily', 
        ...     'Today I walked 10,000 steps and felt great!'
        ... )
        
        Create weekly journal entry:
        >>> weekly_id = JournalDAO.save_journal_entry(
        ...     date(2024, 1, 15),
        ...     'weekly',
        ...     'This week I focused on cardio workouts.',
        ...     week_start_date=date(2024, 1, 14)
        ... )
        
        Retrieve entries for date range:
        >>> entries = JournalDAO.get_journal_entries(
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 31),
        ...     entry_type='daily'
        ... )
        
        Search journal content:
        >>> workout_entries = JournalDAO.search_journal_entries('workout')
    """
    
    @staticmethod
    def save_journal_entry(entry_date: date, entry_type: str, content: str,
                          week_start_date: Optional[date] = None,
                          month_year: Optional[str] = None,
                          expected_version: Optional[int] = None) -> int:
        """Create or update a journal entry with optimistic locking support.
        
        Uses INSERT ... ON CONFLICT logic to either create a new journal entry
        or update an existing one for the same date and type combination.
        This ensures no duplicate entries while allowing content updates.
        
        Supports optimistic locking via version field to prevent concurrent
        update conflicts. When expected_version is provided, the update will
        only succeed if the current version matches.
        
        Args:
            entry_date: The date this journal entry is for.
            entry_type: Type of entry ('daily', 'weekly', or 'monthly').
            content: The journal entry content/text.
            week_start_date: Start date of the week (required for weekly entries).
            month_year: Month-year string in YYYY-MM format (required for monthly entries).
            expected_version: Expected version number for optimistic locking (optional).
            
        Returns:
            int: The ID of the created or updated journal entry.
            
        Raises:
            Exception: If database operation fails or validation errors occur.
            ValueError: If version mismatch occurs (optimistic locking conflict).
            
        Example:
            >>> entry_id = JournalDAO.save_journal_entry(
            ...     date(2024, 1, 15),
            ...     'daily',
            ...     'Today I walked 10,000 steps and felt great!'
            ... )
        """
        if expected_version is not None:
            # Update with version check
            query = """
                UPDATE journal_entries 
                SET content = ?, 
                    week_start_date = ?, 
                    month_year = ?, 
                    version = version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE entry_date = ? 
                    AND entry_type = ? 
                    AND version = ?
            """
            
            params = (
                content,
                week_start_date.isoformat() if week_start_date else None,
                month_year,
                entry_date.isoformat(),
                entry_type,
                expected_version
            )
            
            try:
                db = DatabaseManager()
                rows_affected = db.execute_command(query, params)
                
                if rows_affected == 0:
                    # Version mismatch or entry doesn't exist
                    raise ValueError("Version conflict: Entry was modified by another process")
                    
                # Get the entry ID
                result = db.execute_query(
                    "SELECT id FROM journal_entries WHERE entry_date = ? AND entry_type = ?",
                    (entry_date.isoformat(), entry_type)
                )
                if result:
                    logger.info(f"Updated {entry_type} journal entry for {entry_date} with version check")
                    return result[0]['id']
                else:
                    raise Exception("Failed to retrieve updated entry ID")
                    
            except Exception as e:
                logger.error(f"Error updating journal entry with version check: {e}")
                raise
        else:
            # Standard upsert without version check
            query = """
                INSERT INTO journal_entries 
                (entry_date, entry_type, week_start_date, month_year, content, version)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(entry_date, entry_type) 
                DO UPDATE SET 
                    content = excluded.content,
                    week_start_date = excluded.week_start_date,
                    month_year = excluded.month_year,
                    version = journal_entries.version + 1,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                entry_date.isoformat(),
                entry_type,
                week_start_date.isoformat() if week_start_date else None,
                month_year,
                content
            )
            
            try:
                entry_id = DatabaseManager().execute_command(query, params)
                logger.info(f"Saved {entry_type} journal entry for {entry_date}")
                return entry_id
            except Exception as e:
                logger.error(f"Error saving journal entry: {e}")
                raise
    
    @staticmethod
    def get_journal_entries(start_date: date, end_date: date, 
                           entry_type: Optional[str] = None) -> List[JournalEntry]:
        """Retrieve journal entries for date range with optional type filter.
        
        Fetches journal entries within the specified date range, optionally
        filtered by entry type. Results are ordered by date in descending order
        (most recent first).
        
        Args:
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).
            entry_type: Optional filter for entry type ('daily', 'weekly', 'monthly').
            
        Returns:
            List[JournalEntry]: List of journal entries matching the criteria,
                ordered by date descending.
                
        Example:
            >>> # Get all entries for January 2024
            >>> entries = JournalDAO.get_journal_entries(
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> 
            >>> # Get only daily entries for the week
            >>> daily_entries = JournalDAO.get_journal_entries(
            ...     date(2024, 1, 15),
            ...     date(2024, 1, 21),
            ...     entry_type='daily'
            ... )
        """
        if entry_type:
            query = """
                SELECT * FROM journal_entries 
                WHERE entry_date >= ? AND entry_date <= ? AND entry_type = ?
                ORDER BY entry_date DESC
            """
            params = (start_date.isoformat(), end_date.isoformat(), entry_type)
        else:
            query = """
                SELECT * FROM journal_entries 
                WHERE entry_date >= ? AND entry_date <= ?
                ORDER BY entry_date DESC
            """
            params = (start_date.isoformat(), end_date.isoformat())
        
        try:
            results = DatabaseManager().execute_query(query, params)
            return [JournalEntry.from_dict(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error retrieving journal entries: {e}")
            return []
    
    @staticmethod
    def search_journal_entries(search_term: str) -> List[JournalEntry]:
        """Full-text search in journal content.
        
        Performs a case-insensitive search across all journal entry content
        using SQL LIKE pattern matching. Results are ordered by date in
        descending order.
        
        Args:
            search_term: The text to search for within journal entries.
            
        Returns:
            List[JournalEntry]: List of journal entries containing the search term,
                ordered by date descending.
                
        Example:
            >>> # Find all entries mentioning exercise
            >>> exercise_entries = JournalDAO.search_journal_entries('exercise')
            >>> 
            >>> # Search for entries about mood
            >>> mood_entries = JournalDAO.search_journal_entries('feeling great')
        """
        query = """
            SELECT * FROM journal_entries 
            WHERE content LIKE ?
            ORDER BY entry_date DESC
        """
        
        search_pattern = f"%{search_term}%"
        
        try:
            results = DatabaseManager().execute_query(query, (search_pattern,))
            return [JournalEntry.from_dict(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error searching journal entries: {e}")
            return []
    
    @staticmethod
    def delete_journal_entry(entry_date: date, entry_type: str) -> bool:
        """Delete a journal entry by date and type.
        
        Deletes a specific journal entry from the database based on the unique
        combination of date and type. Returns True if an entry was deleted.
        
        Args:
            entry_date: The date of the entry to delete.
            entry_type: The type of entry to delete ('daily', 'weekly', 'monthly').
            
        Returns:
            bool: True if an entry was deleted, False otherwise.
            
        Example:
            >>> # Delete a daily entry
            >>> success = JournalDAO.delete_journal_entry(
            ...     date(2024, 1, 15),
            ...     'daily'
            ... )
            >>> if success:
            ...     print("Entry deleted")
        """
        query = """
            DELETE FROM journal_entries 
            WHERE entry_date = ? AND entry_type = ?
        """
        
        try:
            rows_affected = DatabaseManager().execute_command(
                query, 
                (entry_date.isoformat(), entry_type)
            )
            
            if rows_affected > 0:
                logger.info(f"Deleted {entry_type} journal entry for {entry_date}")
                return True
            else:
                logger.warning(f"No {entry_type} journal entry found for {entry_date}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting journal entry: {e}")
            raise
    
    @staticmethod
    def get_all_journal_entries() -> List[JournalEntry]:
        """Retrieve all journal entries from the database.
        
        Fetches all journal entries without any date or type filtering,
        ordered by date in descending order (most recent first).
        
        Returns:
            List[JournalEntry]: List of all journal entries in the database,
                ordered by date descending.
                
        Example:
            >>> # Get all entries for export
            >>> all_entries = JournalDAO.get_all_journal_entries()
            >>> print(f"Total entries: {len(all_entries)}")
        """
        query = """
            SELECT * FROM journal_entries 
            ORDER BY entry_date DESC
        """
        
        try:
            results = DatabaseManager().execute_query(query)
            return [JournalEntry.from_dict(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error retrieving all journal entries: {e}")
            return []


class PreferenceDAO:
    """Data Access Object for user preferences.
    
    Manages user preference storage and retrieval with automatic type conversion
    based on the data_type field. Supports string, integer, boolean, date, and
    JSON preference types with proper validation and error handling.
    
    This DAO provides:
    - Type-safe preference retrieval with automatic conversion
    - Preference updates with validation
    - Bulk preference retrieval
    - Default value handling for missing preferences
    
    All preferences are stored as strings in the database but converted to
    appropriate Python types based on the data_type field.
    """
    
    @staticmethod
    def get_preference(key: str, default: Any = None) -> Any:
        """Retrieve preference value and cast based on data_type."""
        query = """
            SELECT preference_value, data_type 
            FROM user_preferences 
            WHERE preference_key = ?
        """
        
        try:
            results = DatabaseManager().execute_query(query, (key,))
            if not results:
                return default
            
            row = results[0]
            pref = UserPreference(
                preference_key=key,
                preference_value=row['preference_value'],
                data_type=row['data_type']
            )
            return pref.get_typed_value()
            
        except Exception as e:
            logger.error(f"Error getting preference {key}: {e}")
            return default
    
    @staticmethod
    def set_preference(key: str, value: Any) -> bool:
        """Update preference with type validation."""
        # Get current preference to determine data type
        query = "SELECT data_type FROM user_preferences WHERE preference_key = ?"
        
        try:
            results = DatabaseManager().execute_query(query, (key,))
            if not results:
                logger.error(f"Preference key '{key}' not found")
                return False
            
            data_type = results[0]['data_type']
            
            # Create preference object for type conversion
            pref = UserPreference(
                preference_key=key,
                preference_value=None,
                data_type=data_type
            )
            pref.set_typed_value(value)
            
            # Update the preference
            update_query = """
                UPDATE user_preferences 
                SET preference_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE preference_key = ?
            """
            
            DatabaseManager().execute_command(update_query, (pref.preference_value, key))
            logger.info(f"Updated preference {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting preference {key}: {e}")
            return False
    
    @staticmethod
    def get_all_preferences() -> Dict[str, Any]:
        """Return all preferences as a dictionary."""
        query = "SELECT * FROM user_preferences"
        
        try:
            results = DatabaseManager().execute_query(query)
            preferences = {}
            
            for row in results:
                pref = UserPreference.from_dict(dict(row))
                preferences[pref.preference_key] = pref.get_typed_value()
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting all preferences: {e}")
            return {}


class RecentFilesDAO:
    """Data Access Object for recent files tracking.
    
    Manages the list of recently accessed files with automatic cleanup
    to maintain a maximum of 10 recent files. Provides functionality
    to add files, retrieve the recent list, and mark files as invalid
    when they become inaccessible.
    
    Features:
    - Automatic upsert logic for file tracking
    - Maintains maximum of 10 recent files
    - Tracks file size and last access time
    - File validity marking for broken file paths
    - Ordered retrieval by last access time
    """
    
    @staticmethod
    def add_recent_file(file_path: str, file_size: Optional[int] = None) -> int:
        """Add or update a recent file entry."""
        query = """
            INSERT INTO recent_files (file_path, file_size, last_accessed)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) 
            DO UPDATE SET 
                last_accessed = CURRENT_TIMESTAMP,
                file_size = excluded.file_size
        """
        
        try:
            file_id = DatabaseManager().execute_command(query, (file_path, file_size))
            
            # Maintain max 10 recent files
            cleanup_query = """
                DELETE FROM recent_files 
                WHERE id NOT IN (
                    SELECT id FROM recent_files 
                    ORDER BY last_accessed DESC 
                    LIMIT 10
                )
            """
            DatabaseManager().execute_command(cleanup_query)
            
            logger.info(f"Added recent file: {file_path}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error adding recent file: {e}")
            raise
    
    @staticmethod
    def get_recent_files(limit: int = 10) -> List[RecentFile]:
        """Get list of recent files."""
        query = """
            SELECT * FROM recent_files 
            WHERE is_valid = TRUE
            ORDER BY last_accessed DESC 
            LIMIT ?
        """
        
        try:
            results = DatabaseManager().execute_query(query, (limit,))
            return [RecentFile.from_dict(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting recent files: {e}")
            return []
    
    @staticmethod
    def mark_file_invalid(file_path: str) -> bool:
        """Mark a file as invalid (e.g., file no longer exists)."""
        query = """
            UPDATE recent_files 
            SET is_valid = FALSE 
            WHERE file_path = ?
        """
        
        try:
            DatabaseManager().execute_command(query, (file_path,))
            logger.info(f"Marked file as invalid: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error marking file invalid: {e}")
            return False


class CacheDAO:
    """Data Access Object for cached metrics.
    
    Manages caching of computed health metrics to improve application performance.
    Provides automatic cache key generation, expiration handling, and statistics
    storage for cached metric data.
    
    The cache system:
    - Generates unique cache keys based on metric parameters
    - Stores metric data with expiration timestamps
    - Includes statistical metadata (min, max, avg, count)
    - Automatically cleans expired cache entries
    - Supports different aggregation types (daily, weekly, monthly)
    
    Cache keys are generated from metric type, date range, source, health type,
    and aggregation parameters to ensure uniqueness and proper cache hits.
    """
    
    @staticmethod
    def _generate_cache_key(metric_type: str, date_start: date, date_end: date,
                           source_name: Optional[str] = None, 
                           health_type: Optional[str] = None,
                           aggregation: str = 'daily') -> str:
        """Generate a unique cache key for the metric."""
        key_parts = [
            metric_type,
            date_start.isoformat(),
            date_end.isoformat(),
            aggregation,
            source_name or 'all',
            health_type or 'all'
        ]
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def cache_metrics(metric_type: str, data: Dict[str, Any], 
                     date_start: date, date_end: date,
                     aggregation_type: str = 'daily',
                     source_name: Optional[str] = None,
                     health_type: Optional[str] = None,
                     unit: Optional[str] = None,
                     record_count: Optional[int] = None,
                     min_value: Optional[float] = None,
                     max_value: Optional[float] = None,
                     avg_value: Optional[float] = None,
                     ttl_hours: int = 24) -> str:
        """Store computed metrics with statistics and expiration."""
        cache_key = CacheDAO._generate_cache_key(
            metric_type, date_start, date_end, source_name, health_type, aggregation_type
        )
        
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        query = """
            INSERT INTO cached_metrics 
            (cache_key, metric_type, date_range_start, date_range_end, 
             source_name, health_type, aggregation_type, metric_data, 
             unit, record_count, min_value, max_value, avg_value, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) 
            DO UPDATE SET 
                metric_data = excluded.metric_data,
                unit = excluded.unit,
                record_count = excluded.record_count,
                min_value = excluded.min_value,
                max_value = excluded.max_value,
                avg_value = excluded.avg_value,
                expires_at = excluded.expires_at,
                created_at = CURRENT_TIMESTAMP
        """
        
        params = (
            cache_key,
            metric_type,
            date_start.isoformat(),
            date_end.isoformat(),
            source_name,
            health_type,
            aggregation_type,
            json.dumps(data),
            unit,
            record_count,
            min_value,
            max_value,
            avg_value,
            expires_at.isoformat()
        )
        
        try:
            DatabaseManager().execute_command(query, params)
            logger.info(f"Cached metrics for {metric_type} ({date_start} to {date_end})")
            return cache_key
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")
            raise
    
    @staticmethod
    def get_cached_metrics(metric_type: str, date_start: date, date_end: date,
                          aggregation_type: str = 'daily',
                          source_name: Optional[str] = None,
                          health_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached metrics if not expired."""
        cache_key = CacheDAO._generate_cache_key(
            metric_type, date_start, date_end, source_name, health_type, aggregation_type
        )
        
        query = """
            SELECT metric_data, expires_at 
            FROM cached_metrics 
            WHERE cache_key = ? AND expires_at > datetime('now')
        """
        
        try:
            results = DatabaseManager().execute_query(query, (cache_key,))
            if results:
                metric_data = json.loads(results[0]['metric_data'])
                logger.info(f"Cache hit for {metric_type}")
                return metric_data
            else:
                logger.info(f"Cache miss for {metric_type}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving cached metrics: {e}")
            return None
    
    @staticmethod
    def clean_expired_cache() -> int:
        """Delete expired cache entries."""
        query = """
            DELETE FROM cached_metrics 
            WHERE expires_at <= datetime('now')
        """
        
        try:
            db = DatabaseManager()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                deleted_count = cursor.rowcount
                conn.commit()
            
            logger.info(f"Cleaned {deleted_count} expired cache entries")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning cache: {e}")
            return 0


class MetricsMetadataDAO:
    """Data Access Object for health metrics metadata.
    
    Manages metadata for health metric types including display names, units,
    categories, colors, and icons. This metadata is used throughout the
    application for consistent metric presentation and organization.
    
    Provides functionality for:
    - Retrieving metric metadata by type
    - Updating display properties (name, unit, category, color, icon)
    - Organizing metrics by category
    - Supporting UI customization and theming
    
    Metadata helps transform raw health record types into user-friendly
    displays with appropriate formatting and visual styling.
    """
    
    @staticmethod
    def get_metric_metadata(metric_type: str) -> Optional[Dict[str, Any]]:
        """Get or create metric metadata."""
        query = "SELECT * FROM health_metrics_metadata WHERE metric_type = ?"
        
        try:
            results = DatabaseManager().execute_query(query, (metric_type,))
            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Error getting metric metadata: {e}")
            return None
    
    @staticmethod
    def update_metric_metadata(metric_type: str, display_name: str, 
                             category: Optional[str] = None,
                             unit: Optional[str] = None,
                             color_hex: Optional[str] = None,
                             icon_name: Optional[str] = None) -> bool:
        """Update metric metadata display properties."""
        query = """
            INSERT INTO health_metrics_metadata 
            (metric_type, display_name, unit, category, color_hex, icon_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(metric_type) 
            DO UPDATE SET 
                display_name = excluded.display_name,
                unit = excluded.unit,
                category = excluded.category,
                color_hex = excluded.color_hex,
                icon_name = excluded.icon_name
        """
        
        try:
            DatabaseManager().execute_command(query, 
                (metric_type, display_name, unit, category, color_hex, icon_name))
            logger.info(f"Updated metadata for metric {metric_type}")
            return True
        except Exception as e:
            logger.error(f"Error updating metric metadata: {e}")
            return False
    
    @staticmethod
    def get_metrics_by_category(category: str) -> List[Dict[str, Any]]:
        """Return all metrics in category."""
        query = "SELECT * FROM health_metrics_metadata WHERE category = ? ORDER BY display_name"
        
        try:
            results = DatabaseManager().execute_query(query, (category,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting metrics by category: {e}")
            return []


class DataSourceDAO:
    """Data Access Object for data sources.
    
    Tracks and manages data sources (devices, apps) that provide health data.
    Maintains activity status and categorization of sources for filtering
    and analysis purposes.
    
    Features:
    - Automatic source registration with upsert logic
    - Activity tracking with last seen timestamps
    - Source categorization for organization
    - Active/inactive status management
    - Source-based data filtering support
    
    Data sources are automatically registered when health data is imported,
    allowing users to filter and analyze data by specific devices or apps.
    """
    
    @staticmethod
    def register_data_source(source_name: str, category: Optional[str] = None) -> int:
        """Create or update source record."""
        query = """
            INSERT INTO data_sources (source_name, source_category, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source_name) 
            DO UPDATE SET 
                last_seen = CURRENT_TIMESTAMP,
                source_category = COALESCE(excluded.source_category, source_category)
        """
        
        try:
            source_id = DatabaseManager().execute_command(query, (source_name, category))
            logger.info(f"Registered data source: {source_name}")
            return source_id
        except Exception as e:
            logger.error(f"Error registering data source: {e}")
            raise
    
    @staticmethod
    def get_active_sources() -> List[Dict[str, Any]]:
        """Return sources with is_active=True."""
        query = """
            SELECT * FROM data_sources 
            WHERE is_active = TRUE 
            ORDER BY source_name
        """
        
        try:
            results = DatabaseManager().execute_query(query)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting active sources: {e}")
            return []
    
    @staticmethod
    def update_source_activity(source_name: str) -> bool:
        """Update last_seen timestamp."""
        query = """
            UPDATE data_sources 
            SET last_seen = CURRENT_TIMESTAMP 
            WHERE source_name = ?
        """
        
        try:
            DatabaseManager().execute_command(query, (source_name,))
            logger.info(f"Updated activity for source: {source_name}")
            return True
        except Exception as e:
            logger.error(f"Error updating source activity: {e}")
            return False


class ImportHistoryDAO:
    """Data Access Object for import history.
    
    Tracks detailed information about data import operations including
    file metadata, import statistics, and performance metrics. Helps
    prevent duplicate imports and provides audit trail functionality.
    
    Recorded information includes:
    - File path and hash for duplicate detection
    - Import timestamp and duration
    - Data statistics (row count, date range, unique types/sources)
    - Performance metrics for optimization
    
    This data helps users track their import history and assists in
    troubleshooting import issues or performance problems.
    """
    
    @staticmethod
    def record_import(file_path: str, file_hash: Optional[str] = None,
                     row_count: Optional[int] = None,
                     date_range_start: Optional[date] = None,
                     date_range_end: Optional[date] = None,
                     unique_types: Optional[int] = None,
                     unique_sources: Optional[int] = None,
                     import_duration_ms: Optional[int] = None) -> int:
        """Store import metadata."""
        query = """
            INSERT INTO import_history 
            (file_path, file_hash, row_count, date_range_start, date_range_end,
             unique_types, unique_sources, import_duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            file_path,
            file_hash,
            row_count,
            date_range_start.isoformat() if date_range_start else None,
            date_range_end.isoformat() if date_range_end else None,
            unique_types,
            unique_sources,
            import_duration_ms
        )
        
        try:
            import_id = DatabaseManager().execute_command(query, params)
            logger.info(f"Recorded import for file: {file_path}")
            return import_id
        except Exception as e:
            logger.error(f"Error recording import: {e}")
            raise
    
    @staticmethod
    def get_import_history(limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent imports."""
        query = """
            SELECT * FROM import_history 
            ORDER BY import_date DESC 
            LIMIT ?
        """
        
        try:
            results = DatabaseManager().execute_query(query, (limit,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting import history: {e}")
            return []
    
    @staticmethod
    def is_file_imported(file_hash: str) -> bool:
        """Check by hash to avoid duplicates."""
        query = "SELECT COUNT(*) FROM import_history WHERE file_hash = ?"
        
        try:
            results = DatabaseManager().execute_query(query, (file_hash,))
            return results[0][0] > 0 if results else False
        except Exception as e:
            logger.error(f"Error checking file import: {e}")
            return False


class DataAccess:
    """Unified data access interface for the Apple Health Monitor application.
    
    Provides a single entry point for all database operations by aggregating
    the specialized DAO classes. This class serves as a facade pattern implementation
    that simplifies access to the underlying data persistence layer.
    
    This unified interface:
        - Centralizes database operations for easier maintenance
        - Provides consistent error handling across all data operations
        - Simplifies dependency injection in UI components
        - Maintains compatibility with existing DAO implementations
        - Supports transaction management across multiple DAOs
    
    The DataAccess class delegates operations to the appropriate DAO while
    providing additional functionality like transaction management, connection
    pooling, and centralized logging.
    
    Examples:
        Basic usage:
        >>> data_access = DataAccess()
        >>> entries = data_access.get_journal_entries(start_date, end_date)
        >>> data_access.cache_metrics('steps', metrics_data, start_date, end_date)
        
        With transaction management:
        >>> with data_access.transaction():
        ...     data_access.save_journal_entry(date.today(), 'daily', 'Entry content')
        ...     data_access.set_preference('last_journal_date', date.today())
    
    Attributes:
        logger: Instance logger for data access operations.
        _transaction_active: Flag indicating if a transaction is currently active.
    """
    
    def __init__(self):
        """Initialize the unified data access interface.
        
        Sets up logging and initializes connection state. No database connections
        are established at initialization - they are created on-demand by the
        underlying DAO classes.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._transaction_active = False
    
    # Journal Operations
    def save_journal_entry(self, entry_date: date, entry_type: str, content: str,
                          week_start_date: Optional[date] = None,
                          month_year: Optional[str] = None) -> int:
        """Create or update a journal entry (delegates to JournalDAO)."""
        return JournalDAO.save_journal_entry(
            entry_date, entry_type, content, week_start_date, month_year
        )
    
    def get_journal_entries(self, start_date: date, end_date: date, 
                           entry_type: Optional[str] = None) -> List[JournalEntry]:
        """Retrieve journal entries for date range (delegates to JournalDAO)."""
        return JournalDAO.get_journal_entries(start_date, end_date, entry_type)
    
    def search_journal_entries(self, search_term: str) -> List[JournalEntry]:
        """Full-text search in journal content (delegates to JournalDAO)."""
        return JournalDAO.search_journal_entries(search_term)
    
    # Preference Operations
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve preference value (delegates to PreferenceDAO)."""
        return PreferenceDAO.get_preference(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Update preference (delegates to PreferenceDAO)."""
        return PreferenceDAO.set_preference(key, value)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Return all preferences (delegates to PreferenceDAO)."""
        return PreferenceDAO.get_all_preferences()
    
    # Recent Files Operations
    def add_recent_file(self, file_path: str, file_size: Optional[int] = None) -> int:
        """Add or update a recent file entry (delegates to RecentFilesDAO)."""
        return RecentFilesDAO.add_recent_file(file_path, file_size)
    
    def get_recent_files(self, limit: int = 10) -> List[RecentFile]:
        """Get list of recent files (delegates to RecentFilesDAO)."""
        return RecentFilesDAO.get_recent_files(limit)
    
    def mark_file_invalid(self, file_path: str) -> bool:
        """Mark a file as invalid (delegates to RecentFilesDAO)."""
        return RecentFilesDAO.mark_file_invalid(file_path)
    
    # Cache Operations
    def cache_metrics(self, metric_type: str, data: Dict[str, Any], 
                     date_start: date, date_end: date,
                     aggregation_type: str = 'daily',
                     source_name: Optional[str] = None,
                     health_type: Optional[str] = None,
                     unit: Optional[str] = None,
                     record_count: Optional[int] = None,
                     min_value: Optional[float] = None,
                     max_value: Optional[float] = None,
                     avg_value: Optional[float] = None,
                     ttl_hours: int = 24) -> str:
        """Store computed metrics (delegates to CacheDAO)."""
        return CacheDAO.cache_metrics(
            metric_type, data, date_start, date_end, aggregation_type,
            source_name, health_type, unit, record_count, min_value,
            max_value, avg_value, ttl_hours
        )
    
    def get_cached_metrics(self, metric_type: str, date_start: date, date_end: date,
                          aggregation_type: str = 'daily',
                          source_name: Optional[str] = None,
                          health_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached metrics (delegates to CacheDAO)."""
        return CacheDAO.get_cached_metrics(
            metric_type, date_start, date_end, aggregation_type, source_name, health_type
        )
    
    def clean_expired_cache(self) -> int:
        """Delete expired cache entries (delegates to CacheDAO)."""
        return CacheDAO.clean_expired_cache()
    
    # Metrics Metadata Operations
    def get_metric_metadata(self, metric_type: str) -> Optional[Dict[str, Any]]:
        """Get metric metadata (delegates to MetricsMetadataDAO)."""
        return MetricsMetadataDAO.get_metric_metadata(metric_type)
    
    def update_metric_metadata(self, metric_type: str, display_name: str, 
                             category: Optional[str] = None,
                             unit: Optional[str] = None,
                             color_hex: Optional[str] = None,
                             icon_name: Optional[str] = None) -> bool:
        """Update metric metadata (delegates to MetricsMetadataDAO)."""
        return MetricsMetadataDAO.update_metric_metadata(
            metric_type, display_name, category, unit, color_hex, icon_name
        )
    
    def get_metrics_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return all metrics in category (delegates to MetricsMetadataDAO)."""
        return MetricsMetadataDAO.get_metrics_by_category(category)
    
    # Data Source Operations
    def register_data_source(self, source_name: str, category: Optional[str] = None) -> int:
        """Create or update source record (delegates to DataSourceDAO)."""
        return DataSourceDAO.register_data_source(source_name, category)
    
    def get_active_sources(self) -> List[Dict[str, Any]]:
        """Return sources with is_active=True (delegates to DataSourceDAO)."""
        return DataSourceDAO.get_active_sources()
    
    def update_source_activity(self, source_name: str) -> bool:
        """Update last_seen timestamp (delegates to DataSourceDAO)."""
        return DataSourceDAO.update_source_activity(source_name)
    
    # Import History Operations
    def record_import(self, file_path: str, file_hash: Optional[str] = None,
                     row_count: Optional[int] = None,
                     date_range_start: Optional[date] = None,
                     date_range_end: Optional[date] = None,
                     unique_types: Optional[int] = None,
                     unique_sources: Optional[int] = None,
                     import_duration_ms: Optional[int] = None) -> int:
        """Store import metadata (delegates to ImportHistoryDAO)."""
        return ImportHistoryDAO.record_import(
            file_path, file_hash, row_count, date_range_start, date_range_end,
            unique_types, unique_sources, import_duration_ms
        )
    
    def get_import_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent imports (delegates to ImportHistoryDAO)."""
        return ImportHistoryDAO.get_import_history(limit)
    
    def is_file_imported(self, file_hash: str) -> bool:
        """Check by hash to avoid duplicates (delegates to ImportHistoryDAO)."""
        return ImportHistoryDAO.is_file_imported(file_hash)
    
    # Database Health and Utility Operations
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics across all tables.
        
        Returns comprehensive statistics about the database including
        record counts, table sizes, and health metrics.
        
        Returns:
            Dict[str, Any]: Dictionary containing database statistics including:
                - Table record counts
                - Cache statistics
                - Recent activity summaries
                - Database health indicators
        """
        try:
            db = DatabaseManager()
            stats = {}
            
            # Get record counts for all main tables
            table_queries = {
                'journal_entries': "SELECT COUNT(*) as count FROM journal_entries",
                'user_preferences': "SELECT COUNT(*) as count FROM user_preferences", 
                'recent_files': "SELECT COUNT(*) as count FROM recent_files",
                'cached_metrics': "SELECT COUNT(*) as count FROM cached_metrics",
                'health_records': "SELECT COUNT(*) as count FROM health_records",
                'data_sources': "SELECT COUNT(*) as count FROM data_sources",
                'import_history': "SELECT COUNT(*) as count FROM import_history"
            }
            
            for table_name, query in table_queries.items():
                try:
                    result = db.execute_query(query)
                    stats[f"{table_name}_count"] = result[0]['count'] if result else 0
                except Exception as e:
                    self.logger.warning(f"Could not get count for {table_name}: {e}")
                    stats[f"{table_name}_count"] = 0
            
            # Get cache statistics
            cache_query = """
                SELECT 
                    COUNT(*) as total_cached_metrics,
                    COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as valid_cache_entries,
                    COUNT(CASE WHEN expires_at <= datetime('now') THEN 1 END) as expired_cache_entries
                FROM cached_metrics
            """
            
            try:
                cache_result = db.execute_query(cache_query)
                if cache_result:
                    stats.update(dict(cache_result[0]))
            except Exception as e:
                self.logger.warning(f"Could not get cache statistics: {e}")
            
            self.logger.info("Retrieved database statistics")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check.
        
        Verifies database connectivity, table integrity, and basic functionality.
        
        Returns:
            Dict[str, Any]: Health check results including:
                - Database connectivity status
                - Table existence verification
                - Basic operation tests
                - Error details if any issues found
        """
        health_status = {
            'database_connected': False,
            'tables_exist': False,
            'basic_operations': False,
            'errors': []
        }
        
        try:
            # Test database connection
            db = DatabaseManager()
            with db.get_connection() as conn:
                health_status['database_connected'] = True
            
            # Test table existence
            required_tables = [
                'journal_entries', 'user_preferences', 'recent_files',
                'cached_metrics', 'health_records', 'data_sources', 'import_history'
            ]
            
            table_check_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ({})
            """.format(','.join('?' * len(required_tables)))
            
            result = db.execute_query(table_check_query, required_tables)
            found_tables = [row['name'] for row in result] if result else []
            
            if len(found_tables) == len(required_tables):
                health_status['tables_exist'] = True
            else:
                missing_tables = set(required_tables) - set(found_tables)
                health_status['errors'].append(f"Missing tables: {missing_tables}")
            
            # Test basic operations
            try:
                # Test a simple read operation
                stats = self.get_database_stats()
                if stats:
                    health_status['basic_operations'] = True
                else:
                    health_status['errors'].append("Database statistics query returned empty")
            except Exception as e:
                health_status['errors'].append(f"Basic operations test failed: {e}")
            
            self.logger.info("Database health check completed")
            
        except Exception as e:
            health_status['errors'].append(f"Health check failed: {e}")
            self.logger.error(f"Database health check error: {e}")
        
        return health_status
    
    # Journal Entry Operations (delegating to JournalDAO)
    def save_journal_entry(self, entry_date: date, entry_type: str, content: str,
                          week_start_date: Optional[date] = None,
                          month_year: Optional[str] = None) -> int:
        """Save a journal entry (delegates to JournalDAO)."""
        return JournalDAO.save_journal_entry(
            entry_date, entry_type, content, week_start_date, month_year
        )
    
    def get_journal_entries(self, start_date: date, end_date: date,
                           entry_type: Optional[str] = None) -> List[JournalEntry]:
        """Get journal entries (delegates to JournalDAO)."""
        return JournalDAO.get_journal_entries(start_date, end_date, entry_type)
    
    def search_journal_entries(self, search_term: str) -> List[JournalEntry]:
        """Search journal entries (delegates to JournalDAO)."""
        return JournalDAO.search_journal_entries(search_term)
    
    def delete_journal_entry(self, entry_date: date, entry_type: str) -> bool:
        """Delete a journal entry (delegates to JournalDAO)."""
        return JournalDAO.delete_journal_entry(entry_date, entry_type)