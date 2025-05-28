"""
Basic statistics calculator for health data.
Provides record counts, date ranges, and aggregations by type and source.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from collections import defaultdict


@dataclass
class BasicStatistics:
    """Container for basic health data statistics."""
    total_records: int
    date_range: Tuple[datetime, datetime]  # (earliest, latest)
    records_by_type: Dict[str, int]
    records_by_source: Dict[str, int]
    types_by_source: Dict[str, List[str]]  # source -> list of types
    
    def to_dict(self) -> dict:
        """Convert statistics to dictionary for serialization."""
        return {
            'total_records': self.total_records,
            'date_range': {
                'start': self.date_range[0].isoformat() if self.date_range[0] else None,
                'end': self.date_range[1].isoformat() if self.date_range[1] else None
            },
            'records_by_type': self.records_by_type,
            'records_by_source': self.records_by_source,
            'types_by_source': self.types_by_source
        }


class StatisticsCalculator:
    """Calculates basic statistics on health data."""
    
    def __init__(self, data_loader=None):
        """
        Initialize the calculator.
        
        Args:
            data_loader: DataLoader instance for database queries
        """
        self.data_loader = data_loader
    
    def calculate_from_dataframe(self, df: pd.DataFrame) -> BasicStatistics:
        """
        Calculate statistics from a pandas DataFrame.
        
        Args:
            df: DataFrame with columns: creationDate, type, sourceName, value
            
        Returns:
            BasicStatistics object with calculated values
        """
        if df.empty:
            return BasicStatistics(
                total_records=0,
                date_range=(None, None),
                records_by_type={},
                records_by_source={},
                types_by_source={}
            )
        
        # Total records
        total_records = len(df)
        
        # Date range - handle mixed date formats and timezones
        try:
            df['creationDate'] = pd.to_datetime(df['creationDate'], format='mixed', utc=True)
            date_range = (df['creationDate'].min(), df['creationDate'].max())
        except Exception as e:
            # If date parsing fails, try without format specification
            try:
                df['creationDate'] = pd.to_datetime(df['creationDate'], utc=True)
                date_range = (df['creationDate'].min(), df['creationDate'].max())
            except Exception:
                # If all parsing fails, return None for date range
                date_range = (None, None)
        
        # Records by type
        records_by_type = df['type'].value_counts().to_dict()
        
        # Records by source
        records_by_source = df['sourceName'].value_counts().to_dict()
        
        # Types by source
        types_by_source = defaultdict(list)
        grouped = df.groupby(['sourceName', 'type']).size()
        for (source, type_name), _ in grouped.items():
            if type_name not in types_by_source[source]:
                types_by_source[source].append(type_name)
        
        # Sort types within each source
        for source in types_by_source:
            types_by_source[source].sort()
        
        return BasicStatistics(
            total_records=total_records,
            date_range=date_range,
            records_by_type=records_by_type,
            records_by_source=records_by_source,
            types_by_source=dict(types_by_source)
        )
    
    def calculate_from_database(self, 
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               types: Optional[List[str]] = None,
                               sources: Optional[List[str]] = None) -> BasicStatistics:
        """
        Calculate statistics from database with optional filters.
        
        Args:
            start_date: Filter records after this date
            end_date: Filter records before this date
            types: Filter to specific record types
            sources: Filter to specific sources
            
        Returns:
            BasicStatistics object with calculated values
        """
        if not self.data_loader:
            raise ValueError("DataLoader not provided")
        
        # Build query with filters
        query = "SELECT creationDate, type, sourceName FROM health_records WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND creationDate >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND creationDate <= ?"
            params.append(end_date.isoformat())
        
        if types:
            placeholders = ','.join(['?' for _ in types])
            query += f" AND type IN ({placeholders})"
            params.extend(types)
        
        if sources:
            placeholders = ','.join(['?' for _ in sources])
            query += f" AND sourceName IN ({placeholders})"
            params.extend(sources)
        
        # Execute query and load into DataFrame
        df = pd.read_sql_query(query, self.data_loader.conn, params=params)
        
        return self.calculate_from_dataframe(df)
    
    def get_quick_summary(self, stats: BasicStatistics) -> str:
        """
        Generate a human-readable summary of the statistics.
        
        Args:
            stats: BasicStatistics object
            
        Returns:
            Formatted string summary
        """
        if stats.total_records == 0:
            return "No health records found."
        
        lines = [
            f"Total Records: {stats.total_records:,}",
            f"Date Range: {stats.date_range[0].strftime('%Y-%m-%d')} to {stats.date_range[1].strftime('%Y-%m-%d')}",
            f"",
            f"Top 5 Record Types:",
        ]
        
        # Top 5 types
        sorted_types = sorted(stats.records_by_type.items(), 
                            key=lambda x: x[1], reverse=True)[:5]
        for type_name, count in sorted_types:
            lines.append(f"  - {type_name}: {count:,}")
        
        lines.extend([
            f"",
            f"Data Sources ({len(stats.records_by_source)}):",
        ])
        
        # All sources
        sorted_sources = sorted(stats.records_by_source.items(), 
                              key=lambda x: x[1], reverse=True)
        for source_name, count in sorted_sources:
            lines.append(f"  - {source_name}: {count:,} records")
        
        return "\n".join(lines)