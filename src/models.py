"""Data models for Apple Health Monitor database entities as per SPECS_DB.md.

This module defines all data model classes used by the Apple Health Monitor Dashboard
for database persistence and data transfer. All models are implemented as dataclasses
with validation, serialization, and type conversion methods.

The models correspond to the database schema defined in SPECS_DB.md and include:
- JournalEntry: Daily, weekly, and monthly journal entries
- UserPreference: User preferences with type information
- RecentFile: Recently accessed file tracking
- CachedMetric: Health metrics cache for performance
- HealthMetricsMetadata: Display metadata for health metrics
- DataSource: Data source tracking and management
- ImportHistory: Import operation history tracking

Example:
    Creating and using a journal entry:
    
    >>> from datetime import date
    >>> entry = JournalEntry(
    ...     entry_date=date.today(),
    ...     entry_type='daily',
    ...     content='Feeling great today!'
    ... )
    >>> data = entry.to_dict()
    >>> restored = JournalEntry.from_dict(data)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json


@dataclass
class JournalEntry:
    """Model for journal entries supporting daily, weekly, and monthly entries.
    
    This dataclass represents journal entries that can be daily, weekly, or monthly.
    It includes validation to ensure proper data structure based on entry type.
    
    Attributes:
        entry_date (date): The primary date for this entry.
        entry_type (str): Type of entry ('daily', 'weekly', 'monthly').
        content (str): The actual journal content text.
        week_start_date (Optional[date]): Start date for weekly entries.
        month_year (Optional[str]): Year-month in YYYY-MM format for monthly entries.
        id (Optional[int]): Database primary key.
        version (int): Version number for optimistic locking.
        created_at (Optional[datetime]): Record creation timestamp.
        updated_at (Optional[datetime]): Record last update timestamp.
    
    Raises:
        ValueError: If entry_type is invalid or required fields are missing.
    
    Example:
        >>> from datetime import date
        >>> entry = JournalEntry(
        ...     entry_date=date(2024, 1, 15),
        ...     entry_type='daily',
        ...     content='Today was productive'
        ... )
    """
    
    entry_date: date
    entry_type: str  # 'daily', 'weekly', 'monthly'
    content: str
    week_start_date: Optional[date] = None
    month_year: Optional[str] = None  # YYYY-MM format
    id: Optional[int] = None
    version: int = 1  # Version for optimistic locking
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate data after initialization.
        
        Ensures that entry_type is valid and required fields are present
        based on the entry type.
        
        Raises:
            ValueError: If entry_type is not valid or required fields are missing.
        """
        valid_types = ['daily', 'weekly', 'monthly']
        if self.entry_type not in valid_types:
            raise ValueError(f"Entry type must be one of {valid_types}")
        
        # Validate week_start_date for weekly entries
        if self.entry_type == 'weekly' and not self.week_start_date:
            raise ValueError("week_start_date is required for weekly entries")
        
        # Validate month_year for monthly entries
        if self.entry_type == 'monthly' and not self.month_year:
            raise ValueError("month_year is required for monthly entries")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation suitable for database storage.
            
        Example:
            >>> entry = JournalEntry(date.today(), 'daily', 'Test content')
            >>> data = entry.to_dict()
            >>> print(data['entry_type'])  # 'daily'
        """
        return {
            'id': self.id,
            'entry_date': self.entry_date.isoformat() if isinstance(self.entry_date, date) else self.entry_date,
            'entry_type': self.entry_type,
            'week_start_date': self.week_start_date.isoformat() if self.week_start_date else None,
            'month_year': self.month_year,
            'content': self.content,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JournalEntry':
        """Create instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing journal entry data.
            
        Returns:
            JournalEntry: New JournalEntry instance.
            
        Example:
            >>> data = {'entry_date': '2024-01-15', 'entry_type': 'daily', 'content': 'Test'}
            >>> entry = JournalEntry.from_dict(data)
        """
        entry_date = data.get('entry_date')
        if isinstance(entry_date, str):
            entry_date = date.fromisoformat(entry_date)
        
        week_start_date = data.get('week_start_date')
        if week_start_date and isinstance(week_start_date, str):
            week_start_date = date.fromisoformat(week_start_date)
        
        return cls(
            id=data.get('id'),
            entry_date=entry_date,
            entry_type=data['entry_type'],
            week_start_date=week_start_date,
            month_year=data.get('month_year'),
            content=data['content'],
            version=data.get('version', 1),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class UserPreference:
    """Model for user preferences with type information."""
    
    preference_key: str
    preference_value: Optional[str]
    data_type: str  # 'string', 'integer', 'boolean', 'date', 'json'
    id: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate data type."""
        valid_types = ['string', 'integer', 'boolean', 'date', 'json']
        if self.data_type not in valid_types:
            raise ValueError(f"Data type must be one of {valid_types}")
    
    def get_typed_value(self) -> Any:
        """Get preference value converted to appropriate type."""
        if self.preference_value is None:
            return None
        
        if self.data_type == 'integer':
            return int(self.preference_value)
        elif self.data_type == 'boolean':
            return self.preference_value.lower() == 'true'
        elif self.data_type == 'date':
            return date.fromisoformat(self.preference_value)
        elif self.data_type == 'json':
            return json.loads(self.preference_value)
        else:  # string
            return self.preference_value
    
    def set_typed_value(self, value: Any):
        """Set preference value with type conversion."""
        if value is None:
            self.preference_value = None
        elif self.data_type == 'json':
            self.preference_value = json.dumps(value)
        elif self.data_type == 'date' and isinstance(value, date):
            self.preference_value = value.isoformat()
        elif self.data_type == 'boolean':
            self.preference_value = 'true' if value else 'false'
        else:
            self.preference_value = str(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'preference_key': self.preference_key,
            'preference_value': self.preference_value,
            'data_type': self.data_type,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreference':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id'),
            preference_key=data['preference_key'],
            preference_value=data.get('preference_value'),
            data_type=data['data_type'],
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class RecentFile:
    """Model for recently accessed files."""
    
    file_path: str
    file_size: Optional[int] = None
    is_valid: bool = True
    id: Optional[int] = None
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'is_valid': self.is_valid,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecentFile':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id'),
            file_path=data['file_path'],
            file_size=data.get('file_size'),
            is_valid=data.get('is_valid', True),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )


@dataclass
class CachedMetric:
    """Model for cached health metrics."""
    
    cache_key: str
    metric_type: str
    date_range_start: date
    date_range_end: date
    aggregation_type: str  # 'daily', 'weekly', 'monthly'
    metric_data: Dict[str, Any]
    expires_at: datetime
    source_name: Optional[str] = None
    health_type: Optional[str] = None
    unit: Optional[str] = None
    record_count: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate data after initialization."""
        valid_aggregations = ['daily', 'weekly', 'monthly']
        if self.aggregation_type not in valid_aggregations:
            raise ValueError(f"Aggregation type must be one of {valid_aggregations}")
        
        if self.date_range_start > self.date_range_end:
            raise ValueError("date_range_start must be before or equal to date_range_end")
    
    def is_expired(self) -> bool:
        """Check if the cached metric has expired."""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'metric_type': self.metric_type,
            'date_range_start': self.date_range_start.isoformat() if isinstance(self.date_range_start, date) else self.date_range_start,
            'date_range_end': self.date_range_end.isoformat() if isinstance(self.date_range_end, date) else self.date_range_end,
            'source_name': self.source_name,
            'health_type': self.health_type,
            'aggregation_type': self.aggregation_type,
            'metric_data': json.dumps(self.metric_data),
            'unit': self.unit,
            'record_count': self.record_count,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedMetric':
        """Create instance from dictionary."""
        date_range_start = data.get('date_range_start')
        if isinstance(date_range_start, str):
            date_range_start = date.fromisoformat(date_range_start)
        
        date_range_end = data.get('date_range_end')
        if isinstance(date_range_end, str):
            date_range_end = date.fromisoformat(date_range_end)
        
        expires_at = data.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        metric_data = data.get('metric_data')
        if isinstance(metric_data, str):
            metric_data = json.loads(metric_data)
        
        return cls(
            id=data.get('id'),
            cache_key=data['cache_key'],
            metric_type=data['metric_type'],
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            source_name=data.get('source_name'),
            health_type=data.get('health_type'),
            aggregation_type=data['aggregation_type'],
            metric_data=metric_data,
            unit=data.get('unit'),
            record_count=data.get('record_count'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            avg_value=data.get('avg_value'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            expires_at=expires_at
        )


@dataclass
class HealthMetricsMetadata:
    """Model for health metrics metadata."""
    
    metric_type: str
    display_name: str
    unit: Optional[str] = None
    category: Optional[str] = None
    color_hex: Optional[str] = None
    icon_name: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'display_name': self.display_name,
            'unit': self.unit,
            'category': self.category,
            'color_hex': self.color_hex,
            'icon_name': self.icon_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthMetricsMetadata':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id'),
            metric_type=data['metric_type'],
            display_name=data['display_name'],
            unit=data.get('unit'),
            category=data.get('category'),
            color_hex=data.get('color_hex'),
            icon_name=data.get('icon_name'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )


@dataclass
class DataSource:
    """Model for data sources."""
    
    source_name: str
    source_category: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'source_name': self.source_name,
            'source_category': self.source_category,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSource':
        """Create instance from dictionary."""
        last_seen = data.get('last_seen')
        if last_seen and isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen)
            
        return cls(
            id=data.get('id'),
            source_name=data['source_name'],
            source_category=data.get('source_category'),
            last_seen=last_seen,
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )


@dataclass
class ImportHistory:
    """Model for import history tracking."""
    
    file_path: str
    file_hash: Optional[str] = None
    row_count: Optional[int] = None
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    unique_types: Optional[int] = None
    unique_sources: Optional[int] = None
    import_duration_ms: Optional[int] = None
    id: Optional[int] = None
    import_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'import_date': self.import_date.isoformat() if self.import_date else None,
            'row_count': self.row_count,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'unique_types': self.unique_types,
            'unique_sources': self.unique_sources,
            'import_duration_ms': self.import_duration_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImportHistory':
        """Create instance from dictionary."""
        date_range_start = data.get('date_range_start')
        if date_range_start and isinstance(date_range_start, str):
            date_range_start = date.fromisoformat(date_range_start)
            
        date_range_end = data.get('date_range_end')
        if date_range_end and isinstance(date_range_end, str):
            date_range_end = date.fromisoformat(date_range_end)
            
        import_date = data.get('import_date')
        if import_date and isinstance(import_date, str):
            import_date = datetime.fromisoformat(import_date)
            
        return cls(
            id=data.get('id'),
            file_path=data['file_path'],
            file_hash=data.get('file_hash'),
            import_date=import_date,
            row_count=data.get('row_count'),
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            unique_types=data.get('unique_types'),
            unique_sources=data.get('unique_sources'),
            import_duration_ms=data.get('import_duration_ms')
        )