# API Specifications
## Apple Health Monitor Dashboard - M01

### 1. Overview
This document defines the internal application programming interfaces for the Apple Health Monitor Dashboard. These APIs facilitate communication between the UI layer, data processing layer, and persistence layer.

### 2. Architecture Overview

```
┌─────────────────┐
│   UI Layer      │
│  (Dashboard)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Service Layer   │
│  (Business      │
│   Logic)        │
└────────┬────────┘
         │
┌────────▼────────┐
│  Data Layer     │
│ (CSV + SQLite)  │
└─────────────────┘
```

### 3. Core Service APIs

#### 3.1 Data Import Service
```python
class DataImportService:
    """Handles CSV file import and validation"""
    
    def import_csv(self, file_path: str) -> ImportResult:
        """
        Import Apple Health CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            ImportResult: Object containing status, row count, and errors
            
        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidFormatError: If CSV format is invalid
        """
        
    def validate_csv_schema(self, dataframe: pd.DataFrame) -> ValidationResult:
        """
        Validate CSV has required columns
        
        Required columns: creationDate, sourceName, type, unit, value
        """
        
    def get_import_progress(self) -> ImportProgress:
        """
        Get current import progress for large files
        
        Returns:
            ImportProgress: Current row, total rows, percentage
        """
```

#### 3.2 Data Filter Service
```python
class DataFilterService:
    """Manages data filtering and subsetting"""
    
    def apply_filters(self, 
                     data: pd.DataFrame,
                     date_range: DateRange,
                     sources: List[str] = None,
                     types: List[str] = None) -> pd.DataFrame:
        """
        Apply filters to dataset
        
        Args:
            data: Source dataframe
            date_range: Start and end dates
            sources: List of sourceName values to include
            types: List of type values to include
            
        Returns:
            Filtered dataframe
        """
        
    def get_available_filters(self, data: pd.DataFrame) -> FilterOptions:
        """
        Get unique values for filter dropdowns
        
        Returns:
            FilterOptions: Available sources, types, date range
        """
        
    def save_filter_preset(self, name: str, filters: FilterConfig) -> bool:
        """Save filter configuration for reuse"""
        
    def load_filter_preset(self, name: str) -> FilterConfig:
        """Load saved filter configuration"""
```

#### 3.3 Metrics Calculation Service
```python
class MetricsService:
    """Calculates statistical metrics for health data"""
    
    def calculate_daily_metrics(self, 
                               data: pd.DataFrame,
                               metric_type: str,
                               date: datetime) -> DailyMetrics:
        """
        Calculate metrics for a specific day
        
        Returns:
            DailyMetrics: avg, min, max, count, std_dev
        """
        
    def calculate_weekly_metrics(self,
                                data: pd.DataFrame,
                                metric_type: str,
                                week_start: datetime) -> WeeklyMetrics:
        """
        Calculate metrics for a week
        
        Returns:
            WeeklyMetrics: avg, min, max, daily_values, trend
        """
        
    def calculate_monthly_metrics(self,
                                 data: pd.DataFrame,
                                 metric_type: str,
                                 year: int,
                                 month: int) -> MonthlyMetrics:
        """
        Calculate metrics for a month
        
        Returns:
            MonthlyMetrics: avg, min, max, daily_values, weekly_avgs
        """
        
    def compare_periods(self,
                       current: MetricsBase,
                       previous: MetricsBase) -> Comparison:
        """
        Compare two time periods
        
        Returns:
            Comparison: percentage_change, direction, significance
        """
```

#### 3.4 Journal Service
```python
class JournalService:
    """Manages journal entries"""
    
    def save_entry(self,
                   date: datetime,
                   entry_type: str,
                   content: str) -> JournalEntry:
        """
        Save or update journal entry
        
        Args:
            date: Entry date
            entry_type: 'daily', 'weekly', or 'monthly'
            content: Journal text
            
        Returns:
            Saved JournalEntry object
        """
        
    def get_entry(self,
                  date: datetime,
                  entry_type: str) -> Optional[JournalEntry]:
        """Retrieve journal entry for specific date/type"""
        
    def get_entries_range(self,
                         start_date: datetime,
                         end_date: datetime,
                         entry_type: str = None) -> List[JournalEntry]:
        """Get all entries in date range"""
        
    def search_entries(self, search_term: str) -> List[JournalEntry]:
        """Full-text search of journal entries"""
        
    def export_entries(self,
                      format: str = 'json',
                      date_range: DateRange = None) -> bytes:
        """Export journal entries in specified format"""
```

#### 3.5 Chart Service
```python
class ChartService:
    """Generates chart configurations for UI"""
    
    def create_time_series_chart(self,
                                data: pd.DataFrame,
                                metric_type: str,
                                period: str) -> ChartConfig:
        """
        Create time series chart configuration
        
        Args:
            data: Filtered data
            metric_type: Health metric to plot
            period: 'daily', 'weekly', 'monthly'
            
        Returns:
            ChartConfig: Chart type, data, styling options
        """
        
    def create_comparison_chart(self,
                               current: MetricsBase,
                               comparisons: List[MetricsBase]) -> ChartConfig:
        """Create comparison bar/line chart"""
        
    def create_heatmap_chart(self,
                            data: pd.DataFrame,
                            metric_type: str,
                            year: int,
                            month: int) -> ChartConfig:
        """Create calendar heatmap for monthly view"""
        
    def export_chart(self,
                    chart_config: ChartConfig,
                    format: str = 'png',
                    dpi: int = 300) -> bytes:
        """Export chart as image"""
```

### 4. Data Models

#### 4.1 Core Models
```python
@dataclass
class DateRange:
    start: datetime
    end: datetime
    
    def validate(self) -> bool:
        """Ensure start <= end"""

@dataclass
class ImportResult:
    success: bool
    row_count: int
    errors: List[str]
    warnings: List[str]
    duration_seconds: float

@dataclass
class MetricsBase:
    average: float
    minimum: float
    maximum: float
    count: int
    std_deviation: float
    
@dataclass
class DailyMetrics(MetricsBase):
    date: datetime
    hourly_distribution: Dict[int, float]  # hour -> value
    
@dataclass
class WeeklyMetrics(MetricsBase):
    week_start: datetime
    daily_values: Dict[datetime, float]
    trend_direction: str  # 'up', 'down', 'stable'
    
@dataclass
class MonthlyMetrics(MetricsBase):
    year: int
    month: int
    daily_values: Dict[int, float]  # day -> value
    weekly_averages: List[float]

@dataclass
class JournalEntry:
    id: int
    entry_date: datetime
    entry_type: str
    content: str
    created_at: datetime
    updated_at: datetime
```

#### 4.2 Configuration Models
```python
@dataclass
class FilterConfig:
    date_range: DateRange
    sources: List[str]
    types: List[str]
    
@dataclass
class ChartConfig:
    chart_type: str  # 'line', 'bar', 'heatmap'
    data: Dict[str, Any]
    title: str
    x_label: str
    y_label: str
    color_scheme: List[str]
    animations: bool = True
```

### 5. Event System

#### 5.1 Event Types
```python
class EventType(Enum):
    DATA_IMPORTED = "data_imported"
    FILTERS_CHANGED = "filters_changed"
    METRICS_CALCULATED = "metrics_calculated"
    JOURNAL_SAVED = "journal_saved"
    CHART_GENERATED = "chart_generated"
    ERROR_OCCURRED = "error_occurred"
```

#### 5.2 Event Bus
```python
class EventBus:
    """Central event management"""
    
    def subscribe(self, 
                  event_type: EventType,
                  callback: Callable) -> str:
        """Subscribe to events"""
        
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        
    def publish(self,
                event_type: EventType,
                data: Any) -> None:
        """Publish event to subscribers"""
```

### 6. Error Handling

#### 6.1 Custom Exceptions
```python
class HealthMonitorException(Exception):
    """Base exception for application"""
    
class InvalidFormatError(HealthMonitorException):
    """CSV format validation failed"""
    
class DataProcessingError(HealthMonitorException):
    """Error during data processing"""
    
class FilterError(HealthMonitorException):
    """Invalid filter configuration"""
    
class MetricsError(HealthMonitorException):
    """Error calculating metrics"""
```

#### 6.2 Error Response Format
```python
@dataclass
class ErrorResponse:
    error_code: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    recoverable: bool
```

### 7. Performance Specifications

#### 7.1 Response Time SLAs
- Data import: < 1 second per 10,000 rows
- Filter application: < 200ms
- Metrics calculation: < 500ms
- Chart generation: < 1 second
- Journal operations: < 100ms

#### 7.2 Resource Limits
- Maximum concurrent operations: 5
- Memory usage per operation: < 100MB
- Cache size limit: 50MB
- Thread pool size: 4 workers

### 8. Testing Interfaces

#### 8.1 Mock Data Generator
```python
class MockDataGenerator:
    """Generate test data for development"""
    
    def generate_health_data(self,
                           start_date: datetime,
                           end_date: datetime,
                           metrics: List[str],
                           sources: List[str]) -> pd.DataFrame:
        """Generate realistic health data"""
        
    def generate_journal_entries(self,
                               count: int) -> List[JournalEntry]:
        """Generate sample journal entries"""
```

#### 8.2 Service Test Interfaces
```python
class ServiceTestBase:
    """Base class for service testing"""
    
    def setup_test_data(self) -> None:
        """Initialize test data"""
        
    def teardown_test_data(self) -> None:
        """Clean up test data"""
        
    def assert_performance(self,
                          operation: Callable,
                          max_duration: float) -> None:
        """Assert operation completes within time limit"""
```