"""
Protocol definition for data sources used by analytics calculators.
Allows flexibility in data source implementations while maintaining type safety.
"""

from typing import Protocol, Tuple, Optional
from datetime import datetime
import pandas as pd


class DataSourceProtocol(Protocol):
    """Protocol for data sources that can provide health data for analysis."""
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Return data as a pandas DataFrame.
        
        The DataFrame should have the following columns:
        - creationDate: datetime (timezone-aware)
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
    
    def get_available_metrics(self) -> list[str]:
        """
        Return list of available metric types in the data.
        
        Returns:
            List of metric type names
        """
        ...