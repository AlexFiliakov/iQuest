"""
Health Database wrapper for data availability queries.

Provides a clean interface for querying health data availability
and supports the DataAvailabilityService.
"""

from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import logging

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class HealthDatabase:
    """Wrapper class for health data queries."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    def get_available_types(self) -> List[str]:
        """Get all unique health record types."""
        try:
            query = "SELECT DISTINCT type FROM health_records WHERE type IS NOT NULL ORDER BY type"
            results = self.db_manager.execute_query(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting available types: {e}")
            return []
            
    def get_date_range_for_type(self, metric_type: str) -> Optional[Tuple[date, date]]:
        """Get the min and max dates for a specific metric type."""
        try:
            query = """
                SELECT MIN(DATE(startDate)) as min_date, MAX(DATE(startDate)) as max_date 
                FROM health_records 
                WHERE type = ? AND startDate IS NOT NULL
            """
            results = self.db_manager.execute_query(query, (metric_type,))
            
            if not results or not results[0][0] or not results[0][1]:
                return None
                
            min_date_str, max_date_str = results[0]
            min_date = datetime.strptime(min_date_str, '%Y-%m-%d').date()
            max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
            
            return (min_date, max_date)
            
        except Exception as e:
            logger.error(f"Error getting date range for type {metric_type}: {e}")
            return None
            
    def get_record_count_for_type(self, metric_type: str) -> int:
        """Get total record count for a specific metric type."""
        try:
            query = "SELECT COUNT(*) FROM health_records WHERE type = ?"
            results = self.db_manager.execute_query(query, (metric_type,))
            return results[0][0] if results else 0
        except Exception as e:
            logger.error(f"Error getting record count for type {metric_type}: {e}")
            return 0
            
    def get_dates_with_data(self, metric_type: str, start_date: date, end_date: date) -> List[date]:
        """Get list of dates that have data for a specific metric type within a date range."""
        try:
            query = """
                SELECT DISTINCT DATE(startDate) as record_date
                FROM health_records 
                WHERE type = ? 
                  AND DATE(startDate) >= ? 
                  AND DATE(startDate) <= ?
                  AND startDate IS NOT NULL
                ORDER BY record_date
            """
            params = (metric_type, start_date.isoformat(), end_date.isoformat())
            results = self.db_manager.execute_query(query, params)
            
            dates = []
            for row in results:
                if row[0]:
                    dates.append(datetime.strptime(row[0], '%Y-%m-%d').date())
                    
            return dates
            
        except Exception as e:
            logger.error(f"Error getting dates with data for {metric_type}: {e}")
            return []
            
    def get_date_range(self) -> Optional[Tuple[date, date]]:
        """Get the overall min and max dates across all health records."""
        try:
            query = """
                SELECT MIN(DATE(startDate)) as min_date, MAX(DATE(startDate)) as max_date 
                FROM health_records 
                WHERE startDate IS NOT NULL
            """
            results = self.db_manager.execute_query(query)
            
            if not results or not results[0][0] or not results[0][1]:
                return None
                
            min_date_str, max_date_str = results[0]
            min_date = datetime.strptime(min_date_str, '%Y-%m-%d').date()
            max_date = datetime.strptime(max_date_str, '%Y-%m-%d').date()
            
            return (min_date, max_date)
            
        except Exception as e:
            logger.error(f"Error getting overall date range: {e}")
            return None
            
    def get_available_sources(self) -> List[str]:
        """Get all unique source names."""
        try:
            query = "SELECT DISTINCT sourceName FROM health_records WHERE sourceName IS NOT NULL ORDER BY sourceName"
            results = self.db_manager.execute_query(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting available sources: {e}")
            return []
            
    def get_types_for_source(self, source_name: str) -> List[str]:
        """Get all metric types available for a specific source."""
        try:
            query = """
                SELECT DISTINCT type 
                FROM health_records 
                WHERE sourceName = ? AND type IS NOT NULL 
                ORDER BY type
            """
            results = self.db_manager.execute_query(query, (source_name,))
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting types for source {source_name}: {e}")
            return []
            
    def get_record_count_for_date_range(self, metric_type: str, start_date: date, end_date: date) -> int:
        """Get record count for a specific metric type within a date range."""
        try:
            query = """
                SELECT COUNT(*) 
                FROM health_records 
                WHERE type = ? 
                  AND DATE(startDate) >= ? 
                  AND DATE(startDate) <= ?
            """
            params = (metric_type, start_date.isoformat(), end_date.isoformat())
            results = self.db_manager.execute_query(query, params)
            return results[0][0] if results else 0
        except Exception as e:
            logger.error(f"Error getting record count for date range: {e}")
            return 0
            
    def has_data_for_date(self, metric_type: str, target_date: date) -> bool:
        """Check if there's any data for a specific metric type on a specific date."""
        try:
            query = """
                SELECT COUNT(*) 
                FROM health_records 
                WHERE type = ? AND DATE(startDate) = ?
            """
            params = (metric_type, target_date.isoformat())
            results = self.db_manager.execute_query(query, params)
            return results[0][0] > 0 if results else False
        except Exception as e:
            logger.error(f"Error checking data for date {target_date}: {e}")
            return False
            
    def get_data_summary(self) -> Dict[str, any]:
        """Get a summary of all available data."""
        try:
            summary = {}
            
            # Get total record count
            total_query = "SELECT COUNT(*) FROM health_records"
            total_results = self.db_manager.execute_query(total_query)
            summary['total_records'] = total_results[0][0] if total_results else 0
            
            # Get available types count
            summary['available_types'] = len(self.get_available_types())
            
            # Get available sources count  
            summary['available_sources'] = len(self.get_available_sources())
            
            # Get date range
            date_range = self.get_date_range()
            summary['date_range'] = {
                'start': date_range[0].isoformat() if date_range and date_range[0] else None,
                'end': date_range[1].isoformat() if date_range and date_range[1] else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
            
    def validate_database(self) -> bool:
        """Validate that the health_records table exists and has data."""
        try:
            # Check if table exists
            table_query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='health_records'
            """
            table_results = self.db_manager.execute_query(table_query)
            
            if not table_results:
                logger.warning("health_records table does not exist")
                return False
                
            # Check if table has data
            count_query = "SELECT COUNT(*) FROM health_records"
            count_results = self.db_manager.execute_query(count_query)
            record_count = count_results[0][0] if count_results else 0
            
            logger.info(f"Database validation: {record_count} health records found")
            return record_count > 0
            
        except Exception as e:
            logger.error(f"Error validating database: {e}")
            return False