"""Data Access Objects for Apple Health Monitor as per SPECS_DB.md."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import json
import hashlib

from database import DatabaseManager
from models import (
    JournalEntry, UserPreference, RecentFile, CachedMetric,
    HealthMetricsMetadata, DataSource, ImportHistory
)

logger = logging.getLogger(__name__)


class JournalDAO:
    """Data Access Object for journal entries."""
    
    @staticmethod
    def save_journal_entry(entry_date: date, entry_type: str, content: str,
                          week_start_date: Optional[date] = None,
                          month_year: Optional[str] = None) -> int:
        """Create or update a journal entry (upsert logic based on date and type)."""
        query = """
            INSERT INTO journal_entries 
            (entry_date, entry_type, week_start_date, month_year, content)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entry_date, entry_type) 
            DO UPDATE SET 
                content = excluded.content,
                week_start_date = excluded.week_start_date,
                month_year = excluded.month_year,
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
        """Retrieve journal entries for date range with optional type filter."""
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
        """Full-text search in journal content."""
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


class PreferenceDAO:
    """Data Access Object for user preferences."""
    
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
    """Data Access Object for recent files tracking."""
    
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
    """Data Access Object for cached metrics."""
    
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
    """Data Access Object for health metrics metadata."""
    
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
    """Data Access Object for data sources."""
    
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
    """Data Access Object for import history."""
    
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