"""
Protocol definition for data sources used by analytics calculators.
Allows flexibility in data source implementations while maintaining type safety.
"""

from datetime import datetime
from typing import List, Optional, Protocol, Tuple

import pandas as pd


class DataSourceProtocol(Protocol):
    """Protocol for data sources that can provide health data for analysis."""
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Return data as a pandas DataFrame.
        
        The DataFrame should have the following columns:
        - startDate: datetime (timezone-aware)
        - type: str (metric type)
        - value: numeric
        
        Additional columns are allowed but not required.
        
        Returns:
            pd.DataFrame: Health data in standard format
        """
        ...
    
    def get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """
        Return the date range of available data.
        
        Returns:
            Tuple of (min_date, max_date) or None if no data
        """
        ...
    
    def get_available_metrics(self) -> List[str]:
        """
        Return list of available metric types in the data.
        
        Returns:
            List of metric type names
        """
        ...


class DataAccessAdapter:
    """Adapter to make DataAccess compatible with DataSourceProtocol.
    
    This adapter wraps the DataAccess class to provide the DataSourceProtocol
    interface required by analytics calculators.
    """
    
    def __init__(self, data_access):
        """Initialize with a DataAccess instance.
        
        Args:
            data_access: DataAccess instance providing database access
        """
        self.data_access = data_access
        self._df_cache = None
        self._cache_time = None
        
    def get_dataframe(self) -> pd.DataFrame:
        """Return health data as a pandas DataFrame.
        
        Queries the database for all health records and returns them
        in the standard format expected by calculators.
        
        Returns:
            pd.DataFrame with columns: startDate, type, value
        """
        from ..database import DatabaseManager

        # Use cached data if available and recent (within 1 minute)
        if self._df_cache is not None and self._cache_time is not None:
            if (datetime.now() - self._cache_time).total_seconds() < 60:
                return self._df_cache
        
        db = DatabaseManager()
        
        # Query health records from database
        # Note: We use startDate as the primary date field for health metrics
        # since it represents when the activity/measurement occurred
        query = """
            SELECT type, startDate, value
            FROM health_records
            WHERE value IS NOT NULL
            ORDER BY startDate
        """
        
        rows = db.execute_query(query)
        
        if not rows:
            # Return empty DataFrame with correct columns
            logger.warning("DataAccessAdapter: No rows returned from health_records query")
            return pd.DataFrame(columns=['startDate', 'type', 'value'])
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=['type', 'startDate', 'value'])
        
        # Convert startDate to datetime
        df['startDate'] = pd.to_datetime(df['startDate'])
        
        # Ensure value is numeric
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Cache the result
        self._df_cache = df
        self._cache_time = datetime.now()
        
        return df
    
    def get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Return the date range of available data.
        
        Returns:
            Tuple of (min_date, max_date) or None if no data
        """
        df = self.get_dataframe()
        if df.empty:
            return None
            
        return (df['startDate'].min(), df['startDate'].max())
    
    def get_available_metrics(self) -> List[str]:
        """Return list of available metric types in the data.
        
        Returns:
            List of unique metric type names
        """
        df = self.get_dataframe()
        if df.empty:
            return []
            
        return df['type'].unique().tolist()