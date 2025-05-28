# Database Specifications
## Apple Health Monitor Dashboard - M01

### 1. Overview
The application uses a lightweight SQLite database for persistent storage of user-generated content and application state. The health metrics data remains in CSV format for simplicity and is processed in-memory.

### 2. Database Schema

#### 2.1 Journal Entries Table
```sql
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE NOT NULL,
    entry_type VARCHAR(10) NOT NULL CHECK (entry_type IN ('daily', 'weekly', 'monthly')),
    week_start_date DATE,  -- For weekly entries
    month_year VARCHAR(7), -- For monthly entries (YYYY-MM format)
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entry_date, entry_type)
);

CREATE INDEX idx_journal_date ON journal_entries(entry_date);
CREATE INDEX idx_journal_type ON journal_entries(entry_type);
CREATE INDEX idx_journal_week ON journal_entries(week_start_date);
CREATE INDEX idx_journal_month ON journal_entries(month_year);
```

#### 2.2 User Preferences Table
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference_key VARCHAR(50) UNIQUE NOT NULL,
    preference_value TEXT,
    data_type VARCHAR(20) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default preferences
INSERT INTO user_preferences (preference_key, preference_value, data_type) VALUES
    ('last_csv_path', NULL, 'string'),
    ('last_date_range_start', NULL, 'date'),
    ('last_date_range_end', NULL, 'date'),
    ('selected_sources', '[]', 'json'),
    ('selected_types', '[]', 'json'),
    ('window_width', '1200', 'integer'),
    ('window_height', '800', 'integer'),
    ('window_x', NULL, 'integer'),
    ('window_y', NULL, 'integer'),
    ('theme_mode', 'light', 'string'),
    ('chart_animation', 'true', 'boolean'),
    ('favorite_metrics', '[]', 'json'),
    ('metric_units', '{}', 'json'),
    ('data_source_colors', '{}', 'json'),
    ('hide_empty_metrics', 'true', 'boolean');
```

#### 2.3 Recent Files Table
```sql
CREATE TABLE recent_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_size INTEGER,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_recent_files_accessed ON recent_files(last_accessed DESC);
```

#### 2.4 Cached Metrics Table
```sql
CREATE TABLE cached_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    source_name VARCHAR(100),
    health_type VARCHAR(100),
    aggregation_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    metric_data TEXT NOT NULL, -- JSON blob
    unit VARCHAR(20), -- Metric unit (e.g., 'count/min', 'lb', 'Cal')
    record_count INTEGER, -- Number of records in cache
    min_value REAL,
    max_value REAL,
    avg_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_cache_key ON cached_metrics(cache_key);
CREATE INDEX idx_cache_expires ON cached_metrics(expires_at);
CREATE INDEX idx_cache_metric_date ON cached_metrics(metric_type, date_range_start, date_range_end);
```

#### 2.5 Health Metrics Metadata Table
```sql
CREATE TABLE health_metrics_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'HeartRate', 'StepCount'
    display_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20), -- e.g., 'count/min', 'lb', 'Cal'
    category VARCHAR(50), -- e.g., 'Vitals', 'Activity', 'Body', 'Nutrition'
    color_hex VARCHAR(7), -- For chart consistency
    icon_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_category ON health_metrics_metadata(category);
```

#### 2.6 Data Sources Table
```sql
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'CASIO WATCHES', 'Renpho'
    source_category VARCHAR(50), -- e.g., 'Wearable', 'App', 'Scale'
    last_seen TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sources_active ON data_sources(is_active);
```

#### 2.7 Import History Table
```sql
CREATE TABLE import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64), -- SHA256 of file
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    date_range_start DATE,
    date_range_end DATE,
    unique_types INTEGER,
    unique_sources INTEGER,
    import_duration_ms INTEGER
);

CREATE INDEX idx_import_date ON import_history(import_date DESC);
```

### 3. Data Access Patterns

#### 3.1 Journal Operations
```python
# Create/Update journal entry
def save_journal_entry(date, entry_type, content):
    # Upsert logic based on date and type
    
# Retrieve journal entries for date range
def get_journal_entries(start_date, end_date, entry_type=None):
    # Query with optional type filter
    
# Search journal entries
def search_journal_entries(search_term):
    # Full-text search in content
```

#### 3.2 Preference Operations
```python
# Get preference value
def get_preference(key, default=None):
    # Retrieve and cast based on data_type
    
# Set preference value
def set_preference(key, value):
    # Update with type validation
    
# Get all preferences
def get_all_preferences():
    # Return as dictionary
```

#### 3.3 Cache Operations
```python
# Store computed metrics with statistics
def cache_metrics(key, data, unit, stats, ttl_hours=24):
    # Store with expiration and statistics
    
# Retrieve cached metrics
def get_cached_metrics(key):
    # Return if not expired, else None
    
# Clean expired cache
def clean_expired_cache():
    # Delete expired entries
```

#### 3.4 Health Metrics Operations
```python
# Get or create metric metadata
def get_metric_metadata(metric_type):
    # Return metadata or create default
    
# Update metric metadata
def update_metric_metadata(metric_type, display_name, category, color):
    # Update display properties
    
# Get metrics by category
def get_metrics_by_category(category):
    # Return all metrics in category
```

#### 3.5 Data Source Operations
```python
# Register data source
def register_data_source(source_name, category):
    # Create or update source record
    
# Get active data sources
def get_active_sources():
    # Return sources with is_active=True
    
# Update source last seen
def update_source_activity(source_name):
    # Update last_seen timestamp
```

#### 3.6 Import History Operations
```python
# Record import
def record_import(file_path, stats):
    # Store import metadata
    
# Get import history
def get_import_history(limit=10):
    # Return recent imports
    
# Check if file imported
def is_file_imported(file_hash):
    # Check by hash to avoid duplicates
```

### 4. Database Management

#### 4.1 Initialization
```python
class DatabaseManager:
    def __init__(self, db_path='health_monitor.db'):
        self.connection = sqlite3.connect(db_path)
        self.initialize_schema()
        
    def initialize_schema(self):
        # Create tables if not exist
        # Run migrations if needed
```

#### 4.2 Migration Strategy
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration files: migrations/001_initial_schema.sql, etc.
```

#### 4.3 Backup Strategy
- Automatic backup before schema migrations
- User-triggered backup to specified location
- Export journal entries to JSON/CSV

### 5. Performance Considerations

#### 5.1 Connection Pooling
- Single connection for desktop application
- Thread-safe access with connection locking
- WAL mode for better concurrency

#### 5.2 Query Optimization
- Prepared statements for frequent queries
- Batch inserts for cache updates
- Indexed columns for common filters
- Pagination for large result sets (>1000 records)

#### 5.3 Storage Limits
- Journal entry content: Max 10,000 characters
- Cache retention: 7 days default
- Recent files list: Max 10 entries
- Database size monitoring and alerts
- CSV processing: Batch mode for files >100K records

#### 5.4 Data Processing Optimization
- Exclude empty device column from processing
- Use timezone-aware datetime handling
- Implement streaming for large CSV files
- Cache frequently accessed metric metadata

### 6. Data Integrity

#### 6.1 Constraints
- Unique constraints on date/type for journal entries
- Foreign key constraints disabled for flexibility
- Check constraints for valid entry types
- Unique constraint on metric_type in metadata
- Unique constraint on source_name in data sources

#### 6.2 Validation
- Date format validation before insert
- JSON validation for preference values
- File path existence check for recent files
- Timezone validation for health data timestamps
- Numeric value validation for health metrics
- Unit consistency checks

#### 6.3 Error Recovery
- Transaction rollback on errors
- Corrupted entry quarantine
- Database repair utilities
- Import rollback on failure
- Duplicate data detection via file hash

### 7. Security Considerations

#### 7.1 Data Protection
- No encryption at rest (non-sensitive data)
- SQL injection prevention via parameterized queries
- Input sanitization for journal entries

#### 7.2 Privacy
- No PII stored in database
- Health data remains in user-controlled CSV
- Optional journal entry export/deletion

### 8. Testing Strategy

#### 8.1 Unit Tests
- CRUD operations for each table
- Edge cases (empty data, nulls, duplicates)
- Migration rollback scenarios

#### 8.2 Integration Tests
- Multi-table transactions
- Cache expiration logic
- Concurrent access patterns

#### 8.3 Performance Tests
- Large journal entry sets (1000+ entries)
- Cache hit/miss ratios
- Query execution time benchmarks