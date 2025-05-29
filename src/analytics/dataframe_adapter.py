"""
Adapter for converting various data sources to pandas DataFrames.
Provides backward compatibility while enabling flexible data source usage.
"""

from typing import Union, Optional, Tuple
from datetime import datetime
import pandas as pd
import logging

from .data_source_protocol import DataSourceProtocol


logger = logging.getLogger(__name__)


class DataFrameAdapter:
    """
    Adapter that converts various data sources to pandas DataFrame format.
    
    Supports:
    - Direct pandas DataFrame input (backward compatibility)
    - DataSourceProtocol implementations
    - Future extensibility for other data formats
    """
    
    def __init__(self, data: Union[pd.DataFrame, DataSourceProtocol]):
        """
        Initialize adapter with data source.
        
        Args:
            data: Either a pandas DataFrame or an object implementing DataSourceProtocol
        """
        self._original_source = data
        self._df: Optional[pd.DataFrame] = None
        self._load_data()
    
    def _load_data(self):
        """Load data from the source into internal DataFrame."""
        if isinstance(self._original_source, pd.DataFrame):
            # Direct DataFrame - make a copy to avoid mutations
            self._df = self._original_source.copy()
            logger.debug("Loaded data from pandas DataFrame")
        elif hasattr(self._original_source, 'get_dataframe'):
            # DataSourceProtocol implementation
            try:
                self._df = self._original_source.get_dataframe()
                logger.debug(f"Loaded data from {type(self._original_source).__name__}")
            except Exception as e:
                logger.error(f"Failed to load data from source: {e}")
                raise ValueError(f"Failed to load data from source: {e}")
        else:
            raise TypeError(
                f"Unsupported data source type: {type(self._original_source)}. "
                "Expected pandas DataFrame or DataSourceProtocol implementation."
            )
        
        # Validate required columns
        self._validate_dataframe()
    
    def _validate_dataframe(self):
        """Validate that the DataFrame has required columns."""
        required_columns = {'creationDate', 'type', 'value'}
        missing_columns = required_columns - set(self._df.columns)
        
        if missing_columns:
            raise ValueError(
                f"DataFrame missing required columns: {missing_columns}. "
                f"Required columns are: {required_columns}"
            )
        
        # Ensure data types are correct
        if not pd.api.types.is_datetime64_any_dtype(self._df['creationDate']):
            logger.warning("creationDate column is not datetime type, attempting conversion")
            self._df['creationDate'] = pd.to_datetime(self._df['creationDate'], errors='coerce')
        
        if not pd.api.types.is_numeric_dtype(self._df['value']):
            logger.warning("value column is not numeric type, attempting conversion")
            self._df['value'] = pd.to_numeric(self._df['value'], errors='coerce')
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Get the adapted DataFrame.
        
        Returns:
            pd.DataFrame: The health data in standard format
        """
        return self._df.copy()
    
    def get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the date range of the data.
        
        Returns:
            Tuple of (min_date, max_date) or None if no valid dates
        """
        if self._df.empty or 'creationDate' not in self._df.columns:
            return None
        
        valid_dates = self._df['creationDate'].dropna()
        if valid_dates.empty:
            return None
        
        return (valid_dates.min(), valid_dates.max())
    
    def get_available_metrics(self) -> list[str]:
        """
        Get list of available metric types.
        
        Returns:
            List of unique metric types in the data
        """
        if self._df.empty or 'type' not in self._df.columns:
            return []
        
        return self._df['type'].dropna().unique().tolist()
    
    @property
    def is_empty(self) -> bool:
        """Check if the adapted data is empty."""
        return self._df.empty
    
    def __len__(self) -> int:
        """Return the number of rows in the adapted data."""
        return len(self._df)
    
    def get_metric_data(self, metric: str, date_range: Optional[Tuple[datetime, datetime]] = None) -> pd.DataFrame:
        """
        Get data for a specific metric within an optional date range.
        
        Args:
            metric: The metric type to retrieve
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            DataFrame with metric data, indexed by date
        """
        # Filter by metric type
        metric_df = self._df[self._df['type'] == metric].copy()
        
        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (metric_df['creationDate'] >= start_date) & (metric_df['creationDate'] <= end_date)
            metric_df = metric_df[mask]
        
        # Create time-indexed DataFrame with just the values
        if not metric_df.empty:
            result = metric_df[['creationDate', 'value']].copy()
            result.set_index('creationDate', inplace=True)
            result.sort_index(inplace=True)
            return result
        
        return pd.DataFrame()