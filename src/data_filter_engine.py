"""
Data Filtering Engine for Apple Health Monitor

This module provides a high-performance filtering engine for health data
with support for date ranges, source names, and health metric types.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
import time
from dataclasses import dataclass
import pandas as pd
import sqlite3

from .database import DatabaseManager
from .utils.logging_config import get_logger
from .utils.error_handler import DataImportError


logger = get_logger(__name__)


@dataclass
class FilterCriteria:
    """Data class to hold filter criteria."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    source_names: Optional[List[str]] = None
    health_types: Optional[List[str]] = None
    combine_logic: str = 'AND'  # 'AND' or 'OR' for combining filters


class QueryBuilder:
    """Builds optimized SQL queries for filtering health data."""
    
    def __init__(self):
        self.base_query = "SELECT * FROM health_records"
        self.conditions = []
        self.params = []
    
    def add_date_range(self, start_date: Optional[date], end_date: Optional[date]):
        """Add date range filtering to the query."""
        if start_date and end_date:
            self.conditions.append("creationDate BETWEEN ? AND ?")
            # Convert dates to datetime strings for SQLite
            self.params.extend([
                datetime.combine(start_date, datetime.min.time()).isoformat(),
                datetime.combine(end_date, datetime.max.time()).isoformat()
            ])
        elif start_date:
            self.conditions.append("creationDate >= ?")
            self.params.append(datetime.combine(start_date, datetime.min.time()).isoformat())
        elif end_date:
            self.conditions.append("creationDate <= ?")
            self.params.append(datetime.combine(end_date, datetime.max.time()).isoformat())
    
    def add_source_filter(self, source_names: Optional[List[str]]):
        """Add source name filtering to the query."""
        if source_names and len(source_names) > 0:
            placeholders = ','.join(['?' for _ in source_names])
            self.conditions.append(f"sourceName IN ({placeholders})")
            self.params.extend(source_names)
    
    def add_type_filter(self, health_types: Optional[List[str]]):
        """Add health type filtering to the query."""
        if health_types and len(health_types) > 0:
            placeholders = ','.join(['?' for _ in health_types])
            self.conditions.append(f"type IN ({placeholders})")
            self.params.extend(health_types)
    
    def build(self, order_by: str = "creationDate DESC", limit: Optional[int] = None) -> Tuple[str, List]:
        """Build the final SQL query."""
        query = self.base_query
        
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        
        query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query, self.params


class DataFilterEngine:
    """Main filtering engine for health data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the filter engine."""
        self.logger = logger
        self.db_manager = DatabaseManager()
        self.db_path = db_path
        self._performance_metrics = {
            'last_query_time': 0,
            'total_queries': 0,
            'average_query_time': 0
        }
    
    def filter_data(self, criteria: FilterCriteria, 
                   return_dataframe: bool = True,
                   limit: Optional[int] = None) -> pd.DataFrame:
        """
        Filter health data based on provided criteria.
        
        Args:
            criteria: FilterCriteria object with filter parameters
            return_dataframe: If True, return pandas DataFrame; else return raw rows
            limit: Maximum number of records to return
            
        Returns:
            Filtered data as DataFrame or list of rows
            
        Raises:
            DataImportError: If filtering fails
        """
        start_time = time.time()
        
        try:
            # Build the query
            builder = QueryBuilder()
            builder.add_date_range(criteria.start_date, criteria.end_date)
            builder.add_source_filter(criteria.source_names)
            builder.add_type_filter(criteria.health_types)
            
            query, params = builder.build(limit=limit)
            
            self.logger.debug(f"Executing filter query: {query[:100]}...")
            
            # Execute query
            if self.db_path:
                # Use specific database file
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
            else:
                # Use DatabaseManager
                rows = self.db_manager.execute_query(query, tuple(params))
            
            # Update performance metrics
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            self._update_performance_metrics(query_time)
            
            self.logger.info(f"Filter query completed in {query_time:.2f}ms, returned {len(rows)} records")
            
            # Convert to DataFrame if requested
            if return_dataframe and rows:
                df = pd.DataFrame([dict(row) for row in rows])
                
                # Parse date columns
                date_columns = ['creationDate', 'startDate', 'endDate']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
                
                # Convert value to numeric
                if 'value' in df.columns:
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df['value'] = df['value'].fillna(1.0)
                
                return df
            elif return_dataframe:
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=['creationDate', 'type', 'value', 'sourceName'])
            else:
                return rows
                
        except Exception as e:
            self.logger.error(f"Error filtering data: {e}")
            raise DataImportError(f"Failed to filter data: {str(e)}") from e
    
    def get_distinct_sources(self) -> List[str]:
        """Get list of distinct source names from the database."""
        try:
            query = "SELECT DISTINCT sourceName FROM health_records WHERE sourceName IS NOT NULL ORDER BY sourceName"
            
            if self.db_path:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
            else:
                rows = self.db_manager.execute_query(query)
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting distinct sources: {e}")
            return []
    
    def get_distinct_types(self) -> List[str]:
        """Get list of distinct health types from the database."""
        try:
            query = "SELECT DISTINCT type FROM health_records WHERE type IS NOT NULL ORDER BY type"
            
            if self.db_path:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    rows = cursor.fetchall()
            else:
                rows = self.db_manager.execute_query(query)
            
            return [row[0] for row in rows]
            
        except Exception as e:
            self.logger.error(f"Error getting distinct types: {e}")
            return []
    
    def get_data_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """Get the minimum and maximum dates in the database."""
        try:
            query = """
                SELECT 
                    MIN(creationDate) as min_date,
                    MAX(creationDate) as max_date
                FROM health_records
            """
            
            if self.db_path:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    row = cursor.fetchone()
            else:
                rows = self.db_manager.execute_query(query)
                row = rows[0] if rows else None
            
            if row and row[0] and row[1]:
                min_date = datetime.fromisoformat(row[0]).date()
                max_date = datetime.fromisoformat(row[1]).date()
                return min_date, max_date
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error getting date range: {e}")
            return None, None
    
    def _update_performance_metrics(self, query_time_ms: float):
        """Update internal performance metrics."""
        self._performance_metrics['last_query_time'] = query_time_ms
        self._performance_metrics['total_queries'] += 1
        
        # Update running average
        current_avg = self._performance_metrics['average_query_time']
        total_queries = self._performance_metrics['total_queries']
        new_avg = ((current_avg * (total_queries - 1)) + query_time_ms) / total_queries
        self._performance_metrics['average_query_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        return self._performance_metrics.copy()
    
    def optimize_for_filters(self, criteria: FilterCriteria):
        """
        Analyze filter usage and suggest or create indexes for optimization.
        
        Args:
            criteria: FilterCriteria to optimize for
        """
        suggestions = []
        
        # Check if we're filtering by date range frequently
        if criteria.start_date or criteria.end_date:
            # Index already exists: idx_creation_date
            suggestions.append("Date range filtering is optimized with existing index")
        
        # Check if we're filtering by source names
        if criteria.source_names:
            # Create index if it doesn't exist
            try:
                create_index_query = """
                    CREATE INDEX IF NOT EXISTS idx_source_name 
                    ON health_records(sourceName)
                """
                if self.db_path:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(create_index_query)
                else:
                    self.db_manager.execute_command(create_index_query)
                suggestions.append("Created index on sourceName for optimization")
            except Exception as e:
                self.logger.warning(f"Could not create sourceName index: {e}")
        
        # Check if we're filtering by types
        if criteria.health_types:
            # Index already exists: idx_type
            suggestions.append("Type filtering is optimized with existing index")
        
        # Composite index for common filter combinations
        if criteria.start_date and criteria.health_types:
            try:
                create_index_query = """
                    CREATE INDEX IF NOT EXISTS idx_type_date_composite 
                    ON health_records(type, creationDate)
                """
                if self.db_path:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(create_index_query)
                else:
                    self.db_manager.execute_command(create_index_query)
                suggestions.append("Created composite index for type+date filtering")
            except Exception as e:
                self.logger.warning(f"Could not create composite index: {e}")
        
        self.logger.info(f"Optimization suggestions: {suggestions}")
        return suggestions


# Example usage
if __name__ == "__main__":
    # Initialize the filter engine
    engine = DataFilterEngine()
    
    # Create filter criteria
    criteria = FilterCriteria(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        source_names=["iPhone", "Apple Watch"],
        health_types=["StepCount", "HeartRate"]
    )
    
    # Filter data
    filtered_df = engine.filter_data(criteria, limit=1000)
    print(f"Filtered {len(filtered_df)} records")
    
    # Get performance metrics
    metrics = engine.get_performance_metrics()
    print(f"Average query time: {metrics['average_query_time']:.2f}ms")