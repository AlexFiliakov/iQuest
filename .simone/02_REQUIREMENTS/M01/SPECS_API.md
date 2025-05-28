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
        
    def calculate_monthly_stats(self,
                               metric: str,
                               year: int,
                               month: int) -> MonthlyMetrics:
        """
        Calculate comprehensive statistics for a specific month
        
        Args:
            metric: The metric type to analyze
            year: Year of the month
            month: Month number (1-12)
        
        Returns:
            MonthlyMetrics: Comprehensive monthly metrics with distribution stats
        """
        
    def compare_year_over_year(self,
                              metric: str,
                              month: int,
                              target_year: int,
                              years_back: int = 1) -> MonthlyComparison:
        """
        Compare same month across multiple years
        
        Returns:
            MonthlyComparison: YoY comparison with statistical significance
        """
        
    def calculate_growth_rate(self,
                             metric: str,
                             periods: int,
                             end_year: int,
                             end_month: int) -> GrowthRateInfo:
        """
        Calculate compound monthly growth rate
        
        Returns:
            GrowthRateInfo: Growth analysis with confidence intervals
        """
        
    def analyze_distribution(self,
                            metric: str,
                            year: int,
                            month: int) -> DistributionStats:
        """
        Analyze distribution characteristics for monthly data
        
        Returns:
            DistributionStats: Skewness, kurtosis, normality tests
        """
        
    def compare_periods(self,
                       current: MetricsBase,
                       previous: MetricsBase) -> Comparison:
        """
        Compare two time periods
        
        Returns:
            Comparison: percentage_change, direction, significance
        """
        
    # Week-over-Week Trends API
    def calculate_week_change(self,
                             metric: str,
                             week1: int,
                             week2: int,
                             year: int) -> TrendResult:
        """
        Calculate change between two weeks with comprehensive analysis
        
        Args:
            metric: The metric type to analyze
            week1: First week number (usually previous week)
            week2: Second week number (usually current week)
            year: Year for the weeks
            
        Returns:
            TrendResult: Comprehensive week change analysis
        """
        
    def detect_momentum(self,
                       metric: str,
                       current_week: int,
                       year: int,
                       lookback_weeks: int = 4) -> MomentumIndicator:
        """
        Detect if trend is accelerating, decelerating, or steady
        
        Returns:
            MomentumIndicator: Momentum analysis with confidence
        """
        
    def get_current_streak(self,
                          metric: str,
                          current_week: int,
                          year: int,
                          max_lookback: int = 52) -> StreakInfo:
        """
        Calculate improvement/decline streaks
        
        Returns:
            StreakInfo: Streak tracking information
        """
        
    def predict_next_week(self,
                         metric: str,
                         current_week: int,
                         year: int,
                         method: str = "linear") -> Prediction:
        """
        Forecast next week's value with confidence interval
        
        Returns:
            Prediction: Forecast with confidence intervals
        """
        
    def generate_trend_narrative(self,
                                metric: str,
                                trend_result: TrendResult,
                                streak_info: StreakInfo,
                                momentum: MomentumIndicator) -> str:
        """
        Generate automatic trend narrative
        
        Returns:
            Generated narrative string
        """
        
    def get_trend_series(self,
                        metric: str,
                        weeks_back: int = 12,
                        end_week: Optional[int] = None,
                        end_year: Optional[int] = None) -> List[WeekTrendData]:
        """
        Get trend data series for visualization
        
        Returns:
            List of WeekTrendData objects for charts
        """
```

#### 3.4 Analytics Cache Service
```python
class AnalyticsCacheManager:
    """Multi-tier caching system for analytics calculations"""
    
    def get(self, 
            key: str, 
            compute_fn: Callable[[], Any],
            cache_tiers: List[str] = None,
            ttl: Optional[int] = None,
            dependencies: List[str] = None) -> Any:
        """
        Get from cache or compute with tier fallback
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if cache miss
            cache_tiers: Cache tiers to use (['l1', 'l2', 'l3'])
            ttl: Time-to-live in seconds
            dependencies: Cache dependencies for invalidation
            
        Returns:
            Cached or computed result
        """
        
    def set(self,
            key: str,
            value: Any,
            cache_tiers: List[str] = None,
            ttl: Optional[int] = None,
            dependencies: List[str] = None) -> None:
        """Store value in specified cache tiers"""
        
    def invalidate_pattern(self, pattern: str) -> Dict[str, int]:
        """Invalidate cache entries matching pattern"""
        
    def invalidate_dependencies(self, dependency: str) -> Dict[str, int]:
        """Invalidate cache entries with specific dependency"""
        
    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        
    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries across all tiers"""

class CachedCalculatorWrapper:
    """Cached wrapper for analytics calculators"""
    
    def __init__(self, calculator: Any):
        """Initialize with underlying calculator"""
        
    # Wrapped methods maintain same signatures but add caching
```

#### 3.5 Journal Service
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
class MonthlyMetrics:
    """Container for comprehensive monthly metrics."""
    month_start: datetime
    mode: str  # 'calendar' or 'rolling'
    avg: float
    median: float
    std: float
    min: float
    max: float
    count: int
    growth_rate: Optional[float] = None
    distribution_stats: Optional[DistributionStats] = None
    comparison_data: Optional[MonthlyComparison] = None

# Week-over-Week Trends Data Models
@dataclass
class TrendResult:
    """Container for trend analysis results."""
    percent_change: float
    absolute_change: float
    momentum: MomentumType
    streak: int
    confidence: float
    current_week_avg: float
    previous_week_avg: float
    trend_direction: str  # 'up', 'down', 'stable'

@dataclass 
class StreakInfo:
    """Container for streak tracking information."""
    current_streak: int
    best_streak: int
    streak_direction: str  # 'improving', 'declining', 'none'
    streak_start_date: Optional[date]
    is_current_streak_best: bool

@dataclass
class MomentumIndicator:
    """Container for momentum analysis."""
    momentum_type: MomentumType
    acceleration_rate: float
    change_velocity: float
    trend_strength: float
    confidence_level: float

@dataclass
class Prediction:
    """Container for predictive analysis results."""
    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    prediction_confidence: float
    methodology: str
    factors_considered: List[str]

@dataclass
class WeekTrendData:
    """Container for week trend visualization data."""
    week_start: date
    week_end: date
    value: float
    percent_change_from_previous: Optional[float]
    trend_direction: str
    momentum: MomentumType
    is_incomplete_week: bool
    missing_days: int

class MomentumType(Enum):
    """Types of momentum indicators."""
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    STEADY = "steady"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class DistributionStats:
    """Container for distribution analysis results."""
    skewness: float
    kurtosis: float
    normality_p_value: float
    is_normal: bool
    jarque_bera_stat: float
    jarque_bera_p_value: float

@dataclass 
class MonthlyComparison:
    """Container for year-over-year monthly comparison results."""
    current_month_avg: float
    previous_year_avg: float
    percent_change: float
    absolute_change: float
    current_month_days: int
    previous_year_days: int
    years_compared: int
    is_significant: bool

@dataclass
class GrowthRateInfo:
    """Container for compound growth rate analysis."""
    monthly_growth_rate: float
    annualized_growth_rate: float
    periods_analyzed: int
    confidence_interval: Tuple[float, float]
    r_squared: float
    is_significant: bool

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
- Multi-tier cache memory: L1 configurable (default 500MB), L2/L3 disk-based
- Thread pool size: 4 workers
- Background refresh workers: 2

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