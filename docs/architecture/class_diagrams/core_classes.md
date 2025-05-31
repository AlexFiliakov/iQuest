# Core Classes

This document details the core classes responsible for database operations, data access patterns, and fundamental data processing in the Apple Health Monitor Dashboard.

## Database Management Classes

```mermaid
classDiagram
    class DatabaseManager {
        -str db_path
        -Connection _connection
        -Lock _lock
        -DatabaseManager _instance
        +get_instance() DatabaseManager
        +get_connection() Connection
        +execute_query(query: str, params: tuple) Cursor
        +execute_many(query: str, params: list) None
        +backup_database() None
        +close() None
        -_initialize_database() None
        -_create_tables() None
    }
    
    class HealthDatabase {
        -str db_path
        -Connection conn
        -Lock lock
        +__init__(db_path: str)
        +create_tables() None
        +insert_health_record(record: dict) None
        +insert_journal_entry(entry: dict) None
        +get_health_records(filters: dict) List[dict]
        +get_journal_entries(date_range: tuple) List[dict]
        +update_user_preference(key: str, value: Any) None
        +get_user_preferences() dict
        +close() None
    }
    
    class DataAccess {
        -DatabaseManager db_manager
        -Logger logger
        +save_health_records(records: List[HealthRecord]) None
        +get_health_records(filters: dict) List[HealthRecord]
        +save_journal_entry(entry: JournalEntry) int
        +get_journal_entries(start_date: date, end_date: date) List[JournalEntry]
        +save_user_preference(preference: UserPreference) None
        +get_user_preferences() List[UserPreference]
        +save_import_history(history: ImportHistory) None
        +get_import_history() List[ImportHistory]
        +save_cached_metric(metric: CachedMetric) None
        +get_cached_metric(key: str) Optional[CachedMetric]
        -_record_to_model(record: dict) HealthRecord
        -_model_to_record(model: HealthRecord) dict
    }
    
    DatabaseManager <-- HealthDatabase : uses
    DatabaseManager <-- DataAccess : uses
    
    note for DatabaseManager "Singleton pattern for thread-safe database access"
    note for DataAccess "DAO pattern implementation"
```

## Data Loading and Processing Classes

```mermaid
classDiagram
    class DataLoader {
        -DataAccess data_access
        -XMLStreamingProcessor xml_processor
        -Logger logger
        -Queue import_queue
        +load_csv_file(file_path: str, progress_callback: Callable) DataFrame
        +load_xml_file(file_path: str, progress_callback: Callable) None
        +process_dataframe(df: DataFrame, source: str) None
        +get_import_statistics() dict
        -_validate_csv_structure(df: DataFrame) bool
        -_process_batch(batch: List[dict]) None
        -_update_progress(current: int, total: int, callback: Callable) None
    }
    
    class XMLStreamingProcessor {
        -DataAccess data_access
        -XMLValidator validator
        -int batch_size
        -List~dict~ current_batch
        -dict statistics
        +__init__(data_access: DataAccess)
        +process_file(file_path: str, callback: Callable) None
        +get_statistics() dict
        -_handle_start_element(name: str, attrs: dict) None
        -_handle_end_element(name: str) None
        -_handle_character_data(data: str) None
        -_flush_batch() None
    }
    
    class XMLValidator {
        -List~str~ required_fields
        -dict field_types
        +validate_structure(root: Element) ValidationResult
        +validate_record(record: dict) ValidationResult
        +validate_date_format(date_str: str) bool
        +validate_numeric_value(value: str, field: str) bool
        -_check_required_fields(record: dict) List[str]
        -_validate_field_types(record: dict) List[str]
    }
    
    class DataFilterEngine {
        -DataAccess data_access
        -dict active_filters
        -Logger logger
        +apply_filters(data: DataFrame, filters: dict) DataFrame
        +filter_by_date_range(df: DataFrame, start: date, end: date) DataFrame
        +filter_by_source(df: DataFrame, sources: List[str]) DataFrame
        +filter_by_type(df: DataFrame, types: List[str]) DataFrame
        +get_available_filters(df: DataFrame) dict
        -_optimize_query(filters: dict) str
        -_build_query_conditions(filters: dict) List[str]
    }
    
    DataLoader --> XMLStreamingProcessor : uses
    DataLoader --> DataAccess : saves data
    XMLStreamingProcessor --> XMLValidator : validates
    XMLStreamingProcessor --> DataAccess : batch saves
    DataFilterEngine --> DataAccess : queries
    
    note for XMLStreamingProcessor "SAX parser for memory efficiency"
    note for DataFilterEngine "Optimized query building"
```

## Statistics and Analytics Core

```mermaid
classDiagram
    class StatisticsCalculator {
        -DataAccess data_access
        -Logger logger
        +calculate_basic_stats(data: Series) BasicStats
        +calculate_distribution(data: Series) Distribution
        +calculate_percentiles(data: Series) dict
        +calculate_moving_average(data: Series, window: int) Series
        +calculate_trend(data: Series) TrendInfo
        +perform_hypothesis_test(data1: Series, data2: Series) TestResult
        -_remove_outliers(data: Series, method: str) Series
        -_normalize_data(data: Series) Series
    }
    
    class PredictiveAnalytics {
        -DataAccess data_access
        -Dict models
        -Logger logger
        +train_model(metric: str, data: DataFrame) Model
        +predict_future(metric: str, periods: int) DataFrame
        +detect_patterns(data: Series) List[Pattern]
        +calculate_seasonality(data: Series) SeasonalInfo
        +forecast_trend(data: Series, days: int) Series
        -_select_best_model(data: Series) str
        -_validate_predictions(actual: Series, predicted: Series) float
    }
    
    class DataAvailabilityService {
        -DataAccess data_access
        -Cache availability_cache
        +check_data_coverage(start: date, end: date) CoverageInfo
        +get_available_metrics() List[str]
        +get_date_range_for_metric(metric: str) tuple
        +calculate_completeness(metric: str, period: str) float
        +find_data_gaps(metric: str) List[DateRange]
        -_build_availability_matrix() DataFrame
        -_cache_availability_info() None
    }
    
    class FilterConfigManager {
        -DataAccess data_access
        -dict current_config
        -Logger logger
        +save_filter_config(name: str, config: dict) None
        +load_filter_config(name: str) dict
        +get_saved_configs() List[str]
        +apply_saved_config(name: str) dict
        +delete_config(name: str) None
        +export_config(name: str, path: str) None
        +import_config(path: str) str
    }
    
    StatisticsCalculator --> DataAccess : queries data
    PredictiveAnalytics --> DataAccess : queries data
    DataAvailabilityService --> DataAccess : checks coverage
    FilterConfigManager --> DataAccess : persists configs
    
    note for PredictiveAnalytics "ML-based forecasting"
    note for DataAvailabilityService "Tracks data completeness"
```

## Configuration and Application Core

```mermaid
classDiagram
    class Config {
        <<module>>
        +APP_NAME: str
        +VERSION: str
        +WINDOW_TITLE: str
        +MIN_WINDOW_SIZE: tuple
        +DEFAULT_WINDOW_SIZE: tuple
        +DB_PATH: str
        +CACHE_DIR: str
        +LOG_DIR: str
        +DATE_FORMAT: str
        +DATETIME_FORMAT: str
        +COLORS: dict
        +CHART_STYLE: dict
        +get_app_dir() Path
        +get_data_dir() Path
        +ensure_directories() None
    }
    
    class MainApplication {
        -QApplication app
        -MainWindow main_window
        -DatabaseManager db_manager
        -Logger logger
        +__init__(argv: list)
        +run() int
        +setup_exception_handling() None
        +setup_logging() None
        +check_single_instance() bool
        -_cleanup() None
        -_handle_exception(exc_type, exc_value, exc_traceback) None
    }
    
    class Version {
        <<module>>
        +__version__: str
        +__version_info__: tuple
        +get_version() str
        +get_version_info() dict
        +check_for_updates() Optional[str]
    }
    
    MainApplication --> Config : uses configuration
    MainApplication --> DatabaseManager : initializes
    MainApplication --> Version : version info
    
    note for Config "Centralized configuration"
    note for MainApplication "Application entry point"
```

## Key Design Patterns

### Singleton Pattern
- **DatabaseManager**: Ensures single database connection across the application
- Thread-safe implementation with locks

### Data Access Object (DAO) Pattern
- **DataAccess**: Abstracts database operations from business logic
- Provides model-to-database mapping

### Factory Pattern
- **XMLStreamingProcessor**: Creates appropriate parser based on file type
- **DataLoader**: Creates appropriate loader for CSV/XML

### Observer Pattern
- Progress callbacks in data loading operations
- Real-time UI updates during long operations

### Strategy Pattern
- **DataFilterEngine**: Different filtering strategies based on criteria
- **StatisticsCalculator**: Multiple statistical methods