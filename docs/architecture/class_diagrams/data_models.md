# Apple Health Monitor - Data Models

This diagram shows all data model classes, their attributes, and relationships.

```mermaid
classDiagram
    %% Base Model Interface
    class BaseModel {
        <<interface>>
        +to_dict() Dict
        +from_dict(data: Dict) BaseModel
    }

    %% Journal Entry Model
    class JournalEntry {
        +str entry_date
        +str entry_type
        +str content
        +str week_start_date
        +str month_year
        +int id
        +str created_at
        +str updated_at
        +__post_init__()
        +to_dict() Dict
        +from_dict(data: Dict) JournalEntry
    }

    %% User Preference Model
    class UserPreference {
        +str preference_key
        +str preference_value
        +str data_type
        +int id
        +str updated_at
        +__post_init__()
        +get_typed_value() Any
        +set_typed_value(value: Any)
        +to_dict() Dict
        +from_dict(data: Dict) UserPreference
    }

    %% Recent File Model
    class RecentFile {
        +str file_path
        +int file_size
        +bool is_valid
        +int id
        +str last_accessed
        +to_dict() Dict
        +from_dict(data: Dict) RecentFile
    }

    %% Cached Metric Model
    class CachedMetric {
        +str cache_key
        +str metric_type
        +str date_range_start
        +str date_range_end
        +str aggregation_type
        +str metric_data
        +str expires_at
        +str source_name
        +str health_type
        +str unit
        +int record_count
        +float min_value
        +float max_value
        +float avg_value
        +int id
        +str created_at
        +__post_init__()
        +is_expired() bool
        +to_dict() Dict
        +from_dict(data: Dict) CachedMetric
    }

    %% Health Metrics Metadata Model
    class HealthMetricsMetadata {
        +str metric_type
        +str display_name
        +str unit
        +str category
        +str color_hex
        +str icon_name
        +int id
        +str created_at
        +to_dict() Dict
        +from_dict(data: Dict) HealthMetricsMetadata
    }

    %% Data Source Model
    class DataSource {
        +str source_name
        +str source_category
        +str last_seen
        +bool is_active
        +int id
        +str created_at
        +to_dict() Dict
        +from_dict(data: Dict) DataSource
    }

    %% Import History Model
    class ImportHistory {
        +str file_path
        +str file_hash
        +int row_count
        +str date_range_start
        +str date_range_end
        +str unique_types
        +str unique_sources
        +int import_duration_ms
        +int id
        +str import_date
        +to_dict() Dict
        +from_dict(data: Dict) ImportHistory
    }

    %% Relationships
    BaseModel <|.. JournalEntry : implements
    BaseModel <|.. UserPreference : implements
    BaseModel <|.. RecentFile : implements
    BaseModel <|.. CachedMetric : implements
    BaseModel <|.. HealthMetricsMetadata : implements
    BaseModel <|.. DataSource : implements
    BaseModel <|.. ImportHistory : implements

    %% Annotations
    note for JournalEntry "Supports daily, weekly, and monthly entries"
    note for UserPreference "Type-safe preference storage with JSON support"
    note for CachedMetric "Performance optimization with TTL"
    note for HealthMetricsMetadata "Display configuration for health metrics"
```

## Model Relationships and Usage

```mermaid
flowchart TB
    subgraph "Data Import Flow"
        XML[XML File] --> IH[ImportHistory]
        CSV[CSV File] --> IH
        IH --> RF[RecentFile]
        IH --> DS[DataSource]
    end

    subgraph "Metric Processing"
        DS --> HMM[HealthMetricsMetadata]
        HMM --> CM[CachedMetric]
        CM --> |Expires| CM
    end

    subgraph "User Data"
        UP[UserPreference] --> |Filters| CM
        JE[JournalEntry] --> |Daily| JE
        JE --> |Weekly| JE
        JE --> |Monthly| JE
    end

    %% Styling
    classDef file fill:#f9f,stroke:#333,stroke-width:2px
    classDef model fill:#bbf,stroke:#333,stroke-width:2px
    classDef user fill:#bfb,stroke:#333,stroke-width:2px
    
    class XML,CSV file
    class IH,RF,DS,HMM,CM model
    class UP,JE user
```

## Database Schema

```mermaid
erDiagram
    journal_entries {
        INTEGER id PK
        TEXT entry_date
        TEXT entry_type
        TEXT content
        TEXT week_start_date
        TEXT month_year
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    user_preferences {
        INTEGER id PK
        TEXT preference_key UK
        TEXT preference_value
        TEXT data_type
        TIMESTAMP updated_at
    }

    recent_files {
        INTEGER id PK
        TEXT file_path UK
        INTEGER file_size
        INTEGER is_valid
        TIMESTAMP last_accessed
    }

    cached_metrics {
        INTEGER id PK
        TEXT cache_key UK
        TEXT metric_type
        TEXT date_range_start
        TEXT date_range_end
        TEXT aggregation_type
        TEXT metric_data
        TIMESTAMP expires_at
        TEXT source_name
        TEXT health_type
        TEXT unit
        INTEGER record_count
        REAL min_value
        REAL max_value
        REAL avg_value
        TIMESTAMP created_at
    }

    health_metrics_metadata {
        INTEGER id PK
        TEXT metric_type UK
        TEXT display_name
        TEXT unit
        TEXT category
        TEXT color_hex
        TEXT icon_name
        TIMESTAMP created_at
    }

    data_sources {
        INTEGER id PK
        TEXT source_name UK
        TEXT source_category
        TIMESTAMP last_seen
        INTEGER is_active
        TIMESTAMP created_at
    }

    import_history {
        INTEGER id PK
        TEXT file_path
        TEXT file_hash UK
        INTEGER row_count
        TEXT date_range_start
        TEXT date_range_end
        TEXT unique_types
        TEXT unique_sources
        INTEGER import_duration_ms
        TIMESTAMP import_date
    }

    %% Relationships
    import_history ||--o{ recent_files : "tracks"
    import_history ||--o{ data_sources : "discovers"
    data_sources ||--o{ health_metrics_metadata : "provides"
    health_metrics_metadata ||--o{ cached_metrics : "configures"
    user_preferences ||--o{ cached_metrics : "influences"
```

## Model Features

### Type Safety
All models use Python's `@dataclass` decorator with type hints:
- Automatic `__init__`, `__repr__`, and `__eq__` methods
- IDE support for type checking
- Runtime validation with `__post_init__`

### Serialization
All models implement consistent serialization:
- `to_dict()`: Convert model to dictionary for storage
- `from_dict()`: Create model instance from dictionary
- JSON-compatible data types

### Special Features

**JournalEntry**:
- Supports multiple entry types (daily, weekly, monthly)
- Automatic timestamp management
- Full-text search capability

**UserPreference**:
- Type-safe value storage
- JSON serialization for complex values
- Key-based lookup

**CachedMetric**:
- TTL-based expiration
- Aggregated statistics storage
- Performance optimization

**ImportHistory**:
- File deduplication via hash
- Import performance tracking
- Data range tracking