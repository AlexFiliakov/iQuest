# Data Models

This document details the domain models and database schema used in the Apple Health Monitor Dashboard application.

## Domain Model Overview

```mermaid
classDiagram
    class HealthRecord {
        +int id
        +str record_type
        +str source_name
        +str source_version
        +str unit
        +datetime creation_date
        +datetime start_date
        +datetime end_date
        +float value
        +str device
        +dict metadata
        +__post_init__() None
        +to_dict() dict
        +from_dict(data: dict) HealthRecord
    }
    
    class JournalEntry {
        +int id
        +date entry_date
        +str entry_type
        +str content
        +str mood
        +int energy_level
        +List~str~ tags
        +datetime created_at
        +datetime updated_at
        +dict custom_fields
        +__post_init__() None
        +to_dict() dict
        +from_dict(data: dict) JournalEntry
    }
    
    class UserPreference {
        +str key
        +Any value
        +str value_type
        +str category
        +datetime updated_at
        +str description
        +to_dict() dict
        +from_dict(data: dict) UserPreference
        +serialize_value() str
        +deserialize_value(value: str) Any
    }
    
    class ImportHistory {
        +int id
        +str file_name
        +str file_type
        +int file_size
        +datetime import_date
        +str status
        +int records_imported
        +int records_failed
        +float duration_seconds
        +dict error_details
        +to_dict() dict
        +get_summary() str
    }
    
    class CachedMetric {
        +str cache_key
        +str metric_type
        +date start_date
        +date end_date
        +dict filters
        +Any value
        +datetime created_at
        +datetime expires_at
        +int access_count
        +is_expired() bool
        +to_dict() dict
        +generate_key(params: dict) str
    }
    
    class AggregatedData {
        +str metric_type
        +str aggregation_period
        +date period_start
        +date period_end
        +float min_value
        +float max_value
        +float avg_value
        +float sum_value
        +int count
        +float std_dev
        +dict percentiles
        +to_dict() dict
        +calculate_stats(values: List[float]) None
    }
    
    class DataAvailability {
        +str metric_type
        +date first_date
        +date last_date
        +int total_records
        +int total_days
        +float coverage_percentage
        +List~date~ missing_dates
        +dict source_breakdown
        +to_dict() dict
        +calculate_coverage() float
        +find_gaps() List[DateRange]
    }
```

## Database Schema

```mermaid
erDiagram
    health_records {
        INTEGER id PK
        TEXT record_type
        TEXT source_name
        TEXT source_version
        TEXT unit
        TIMESTAMP creation_date
        TIMESTAMP start_date
        TIMESTAMP end_date
        REAL value
        TEXT device
        TEXT metadata
    }
    
    journal_entries {
        INTEGER id PK
        DATE entry_date
        TEXT entry_type
        TEXT content
        TEXT mood
        INTEGER energy_level
        TEXT tags
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TEXT custom_fields
    }
    
    user_preferences {
        TEXT key PK
        TEXT value
        TEXT value_type
        TEXT category
        TIMESTAMP updated_at
        TEXT description
    }
    
    import_history {
        INTEGER id PK
        TEXT file_name
        TEXT file_type
        INTEGER file_size
        TIMESTAMP import_date
        TEXT status
        INTEGER records_imported
        INTEGER records_failed
        REAL duration_seconds
        TEXT error_details
    }
    
    cached_metrics {
        TEXT cache_key PK
        TEXT metric_type
        DATE start_date
        DATE end_date
        TEXT filters
        TEXT value
        TIMESTAMP created_at
        TIMESTAMP expires_at
        INTEGER access_count
    }
    
    aggregated_data {
        TEXT metric_type
        TEXT aggregation_period
        DATE period_start
        DATE period_end
        REAL min_value
        REAL max_value
        REAL avg_value
        REAL sum_value
        INTEGER count
        REAL std_dev
        TEXT percentiles
    }
    
    data_availability {
        TEXT metric_type PK
        DATE first_date
        DATE last_date
        INTEGER total_records
        INTEGER total_days
        REAL coverage_percentage
        TEXT missing_dates
        TEXT source_breakdown
    }
    
    health_records ||--o{ aggregated_data : "aggregates into"
    health_records ||--o{ cached_metrics : "cached as"
    health_records ||--o{ data_availability : "tracked by"
    journal_entries }o--|| user_preferences : "uses settings"
```

## Model Relationships and Business Logic

```mermaid
classDiagram
    class HealthMetricType {
        <<enumeration>>
        STEPS
        HEART_RATE
        BLOOD_PRESSURE
        WEIGHT
        SLEEP
        CALORIES
        EXERCISE
        BLOOD_GLUCOSE
        RESPIRATORY_RATE
        +get_unit() str
        +get_display_name() str
        +requires_device() bool
    }
    
    class AggregationPeriod {
        <<enumeration>>
        HOURLY
        DAILY
        WEEKLY
        MONTHLY
        YEARLY
        +get_date_format() str
        +get_display_format() str
        +truncate_date(date: datetime) datetime
    }
    
    class JournalMood {
        <<enumeration>>
        EXCELLENT
        GOOD
        NEUTRAL
        POOR
        TERRIBLE
        +get_emoji() str
        +get_color() str
        +get_score() int
    }
    
    class ImportStatus {
        <<enumeration>>
        PENDING
        IN_PROGRESS
        COMPLETED
        FAILED
        PARTIAL
        +is_terminal() bool
        +can_retry() bool
    }
    
    class CacheStrategy {
        <<interface>>
        +should_cache(metric: str) bool
        +get_ttl(metric: str) int
        +get_cache_key(params: dict) str
        +invalidate_pattern(pattern: str) None
    }
    
    class ValidationResult {
        +bool is_valid
        +List~str~ errors
        +List~str~ warnings
        +dict metadata
        +add_error(message: str) None
        +add_warning(message: str) None
        +merge(other: ValidationResult) None
    }
    
    HealthRecord --> HealthMetricType : type
    AggregatedData --> AggregationPeriod : period
    JournalEntry --> JournalMood : mood
    ImportHistory --> ImportStatus : status
    CachedMetric ..> CacheStrategy : follows
    
    note for HealthMetricType "Defines all supported health metrics"
    note for CacheStrategy "Interface for caching strategies"
```

## Analytics Models

```mermaid
classDiagram
    class MetricStatistics {
        +str metric_type
        +date period_start
        +date period_end
        +float mean
        +float median
        +float mode
        +float std_dev
        +float variance
        +float skewness
        +float kurtosis
        +dict percentiles
        +int sample_size
        +calculate_z_score(value: float) float
        +is_outlier(value: float) bool
    }
    
    class TrendInfo {
        +str direction
        +float slope
        +float r_squared
        +float p_value
        +str trend_type
        +float strength
        +List~float~ residuals
        +predict_next(periods: int) List[float]
        +get_confidence_interval() tuple
    }
    
    class CorrelationResult {
        +str metric1
        +str metric2
        +float correlation
        +float p_value
        +str correlation_type
        +int sample_size
        +float confidence_lower
        +float confidence_upper
        +is_significant(alpha: float) bool
        +get_strength() str
    }
    
    class AnomalyInfo {
        +datetime timestamp
        +str metric_type
        +float actual_value
        +float expected_value
        +float deviation
        +str anomaly_type
        +float severity_score
        +dict context
        +get_description() str
        +requires_attention() bool
    }
    
    class HealthScore {
        +date calculation_date
        +float overall_score
        +dict component_scores
        +dict weights
        +List~str~ factors
        +str trend
        +dict recommendations
        +calculate_weighted_score() float
        +get_grade() str
        +get_improvement_areas() List[str]
    }
    
    MetricStatistics --> TrendInfo : analyzes
    MetricStatistics --> CorrelationResult : correlates
    MetricStatistics --> AnomalyInfo : detects
    HealthScore --> MetricStatistics : uses
    
    note for HealthScore "Composite health assessment"
    note for AnomalyInfo "Detected anomalies with context"
```

## Data Transformation Models

```mermaid
classDiagram
    class DataTransform {
        <<interface>>
        +transform(data: DataFrame) DataFrame
        +inverse_transform(data: DataFrame) DataFrame
        +get_params() dict
    }
    
    class NormalizationTransform {
        -float min_val
        -float max_val
        +fit(data: Series) None
        +transform(data: DataFrame) DataFrame
        +inverse_transform(data: DataFrame) DataFrame
    }
    
    class AggregationTransform {
        -str method
        -str period
        +transform(data: DataFrame) DataFrame
        +get_aggregation_func() Callable
    }
    
    class FilterTransform {
        -dict criteria
        +transform(data: DataFrame) DataFrame
        +add_filter(field: str, condition: Any) None
        +remove_filter(field: str) None
    }
    
    class PivotTransform {
        -str index
        -str columns
        -str values
        -str aggfunc
        +transform(data: DataFrame) DataFrame
        +validate_columns(df: DataFrame) bool
    }
    
    DataTransform <|.. NormalizationTransform
    DataTransform <|.. AggregationTransform
    DataTransform <|.. FilterTransform
    DataTransform <|.. PivotTransform
    
    note for DataTransform "Transform pipeline pattern"
```

## Key Model Features

### Data Validation
- All models include validation in `__post_init__`
- Type checking and range validation
- Business rule enforcement

### Serialization
- `to_dict()` and `from_dict()` for all models
- JSON-compatible serialization
- Preserves type information

### Caching Support
- Models designed for efficient caching
- Immutable where appropriate
- Cache key generation built-in

### Extensibility
- Custom fields support in Journal and Preferences
- Metadata fields for future expansion
- Backwards compatibility considered