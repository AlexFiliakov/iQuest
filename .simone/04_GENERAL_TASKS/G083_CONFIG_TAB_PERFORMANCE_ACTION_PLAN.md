# Configuration Tab Performance Optimization - Action Plan

## Overview
This action plan provides step-by-step implementation guidance for optimizing the Configuration tab's performance, addressing the 3-5 second freeze and high memory usage issues.

## Priority 1: Immediate Performance Gains (Day 1-2)

### Task 1.1: Replace Full Data Load with SQL Aggregations
**File**: `src/data_loader.py`

**Add Methods**:
```python
def get_record_statistics(self) -> Dict[str, Any]:
    """Get summary statistics using SQL aggregation queries."""
    conn = sqlite3.connect(self.db_path)
    try:
        # Total records
        total = conn.execute("SELECT COUNT(*) FROM health_records").fetchone()[0]
        
        # Date range
        dates = conn.execute(
            "SELECT MIN(creationDate), MAX(creationDate) FROM health_records"
        ).fetchone()
        
        # Type counts
        type_counts = conn.execute(
            "SELECT type, COUNT(*) as count FROM health_records GROUP BY type"
        ).fetchall()
        
        # Source counts
        source_counts = conn.execute(
            "SELECT sourceName, COUNT(*) as count FROM health_records GROUP BY sourceName"
        ).fetchall()
        
        return {
            'total_records': total,
            'earliest_date': dates[0],
            'latest_date': dates[1],
            'type_counts': dict(type_counts),
            'source_counts': dict(source_counts)
        }
    finally:
        conn.close()

def get_filter_options(self) -> Dict[str, List[str]]:
    """Get unique filter values without loading all data."""
    conn = sqlite3.connect(self.db_path)
    try:
        types = [row[0] for row in conn.execute(
            "SELECT DISTINCT type FROM health_records ORDER BY type"
        )]
        sources = [row[0] for row in conn.execute(
            "SELECT DISTINCT sourceName FROM health_records ORDER BY sourceName"
        )]
        return {'types': types, 'sources': sources}
    finally:
        conn.close()
```

### Task 1.2: Modify Configuration Tab Loading
**File**: `src/ui/configuration_tab.py`

**Changes**:
1. Remove auto-load trigger (line ~138):
```python
# Comment out or remove:
# QTimer.singleShot(100, self._check_existing_data)
```

2. Refactor `_load_from_sqlite()` (line ~1877):
```python
def _load_from_sqlite(self):
    """Load statistics from database using efficient queries."""
    try:
        self.loading_label.setText("Loading statistics...")
        
        # Use new efficient methods
        stats = self.data_loader.get_record_statistics()
        filter_options = self.data_loader.get_filter_options()
        
        # Update UI with statistics
        self._update_statistics_display(stats)
        self._populate_filter_dropdowns(filter_options)
        
        self.loading_label.setText("Ready")
        self.enable_ui_elements(True)
        
    except Exception as e:
        self.loading_label.setText(f"Error: {str(e)}")
        logger.error(f"Failed to load statistics: {e}")
```

### Task 1.3: Add Database Indexes
**File**: `src/database.py`

**Add Index Creation**:
```python
def create_indexes(self):
    """Create indexes for performance optimization."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Create indexes if not exists
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_source ON health_records(sourceName)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_date ON health_records(creationDate)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)"
    )
    
    conn.commit()
    conn.close()
```

## Priority 2: Caching Implementation (Day 2-3)

### Task 2.1: Integrate CacheManager
**File**: `src/ui/configuration_tab.py`

**Implementation**:
```python
from src.analytics.cache_manager import CacheManager

class ConfigurationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cache_manager = CacheManager()
        self.cache_ttl = 3600  # 1 hour
        
    def _get_cached_statistics(self) -> Optional[Dict]:
        """Get statistics from cache if available."""
        return self.cache_manager.get("config_tab_stats")
        
    def _cache_statistics(self, stats: Dict):
        """Cache statistics with TTL."""
        self.cache_manager.set("config_tab_stats", stats, ttl=self.cache_ttl)
        
    def _invalidate_cache(self):
        """Invalidate cache when data changes."""
        self.cache_manager.delete("config_tab_stats")
```

### Task 2.2: Modify Statistics Loading
**Update** `_load_from_sqlite()`:
```python
def _load_from_sqlite(self):
    """Load statistics with caching."""
    # Try cache first
    cached_stats = self._get_cached_statistics()
    if cached_stats:
        self._update_statistics_display(cached_stats['stats'])
        self._populate_filter_dropdowns(cached_stats['filters'])
        self.loading_label.setText("Ready (cached)")
        return
        
    # Load from database
    stats = self.data_loader.get_record_statistics()
    filter_options = self.data_loader.get_filter_options()
    
    # Cache the results
    self._cache_statistics({
        'stats': stats,
        'filters': filter_options,
        'timestamp': datetime.now()
    })
    
    # Update UI
    self._update_statistics_display(stats)
    self._populate_filter_dropdowns(filter_options)
```

## Priority 3: Background Loading (Day 3-4)

### Task 3.1: Create Background Loader Thread
**New File**: `src/ui/config_tab_loader.py`

```python
from PyQt6.QtCore import QThread, pyqtSignal
import time

class ConfigTabLoader(QThread):
    """Background thread for loading configuration tab data."""
    
    progress_update = pyqtSignal(int, str)
    statistics_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, data_loader, cache_manager):
        super().__init__()
        self.data_loader = data_loader
        self.cache_manager = cache_manager
        
    def run(self):
        """Load data in background."""
        try:
            # Check cache first
            self.progress_update.emit(10, "Checking cache...")
            cached = self.cache_manager.get("config_tab_stats")
            if cached:
                self.statistics_ready.emit(cached)
                return
                
            # Load statistics
            self.progress_update.emit(30, "Loading record counts...")
            stats = self.data_loader.get_record_statistics()
            
            # Load filter options
            self.progress_update.emit(60, "Loading filter options...")
            filters = self.data_loader.get_filter_options()
            
            # Package results
            result = {
                'stats': stats,
                'filters': filters,
                'timestamp': time.time()
            }
            
            # Cache results
            self.progress_update.emit(90, "Caching results...")
            self.cache_manager.set("config_tab_stats", result, ttl=3600)
            
            # Emit completion
            self.progress_update.emit(100, "Complete")
            self.statistics_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
```

### Task 3.2: Integrate Background Loading
**File**: `src/ui/configuration_tab.py`

**Add to `__init__`**:
```python
self.loader_thread = None
self.progress_bar = QProgressBar()
self.progress_bar.setVisible(False)
```

**Add Loading Methods**:
```python
def start_background_load(self):
    """Start loading data in background."""
    if self.loader_thread and self.loader_thread.isRunning():
        return
        
    self.progress_bar.setVisible(True)
    self.enable_ui_elements(False)
    
    self.loader_thread = ConfigTabLoader(self.data_loader, self.cache_manager)
    self.loader_thread.progress_update.connect(self._on_progress_update)
    self.loader_thread.statistics_ready.connect(self._on_statistics_ready)
    self.loader_thread.error_occurred.connect(self._on_error)
    self.loader_thread.start()
    
def _on_progress_update(self, progress: int, message: str):
    """Update progress bar."""
    self.progress_bar.setValue(progress)
    self.loading_label.setText(message)
    
def _on_statistics_ready(self, data: dict):
    """Handle loaded statistics."""
    self._update_statistics_display(data['stats'])
    self._populate_filter_dropdowns(data['filters'])
    self.progress_bar.setVisible(False)
    self.enable_ui_elements(True)
    self.loading_label.setText("Ready")
```

## Priority 4: Summary Tables (Day 5-6)

### Task 4.1: Create Summary Tables Schema
**New File**: `src/database_migrations/add_summary_tables.sql`

```sql
-- Summary statistics table
CREATE TABLE IF NOT EXISTS statistics_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_records INTEGER NOT NULL,
    unique_types INTEGER NOT NULL,
    unique_sources INTEGER NOT NULL,
    earliest_date TEXT,
    latest_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Type statistics table
CREATE TABLE IF NOT EXISTS type_statistics (
    type TEXT PRIMARY KEY,
    record_count INTEGER NOT NULL DEFAULT 0,
    earliest_date TEXT,
    latest_date TEXT,
    avg_value REAL,
    min_value REAL,
    max_value REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Source statistics table
CREATE TABLE IF NOT EXISTS source_statistics (
    source_name TEXT PRIMARY KEY,
    record_count INTEGER NOT NULL DEFAULT 0,
    types_count INTEGER NOT NULL DEFAULT 0,
    earliest_date TEXT,
    latest_date TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create update trigger
CREATE TRIGGER update_statistics_timestamp 
AFTER UPDATE ON statistics_summary
BEGIN
    UPDATE statistics_summary SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### Task 4.2: Add Summary Update Methods
**File**: `src/data_loader.py`

```python
def update_summary_tables(self):
    """Update summary statistics tables."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    try:
        # Update main summary
        cursor.execute("""
            INSERT OR REPLACE INTO statistics_summary 
            (id, total_records, unique_types, unique_sources, earliest_date, latest_date)
            SELECT 
                1,
                COUNT(*),
                COUNT(DISTINCT type),
                COUNT(DISTINCT sourceName),
                MIN(creationDate),
                MAX(creationDate)
            FROM health_records
        """)
        
        # Update type statistics
        cursor.execute("""
            INSERT OR REPLACE INTO type_statistics
            (type, record_count, earliest_date, latest_date, avg_value, min_value, max_value)
            SELECT 
                type,
                COUNT(*),
                MIN(creationDate),
                MAX(creationDate),
                AVG(CAST(value AS REAL)),
                MIN(CAST(value AS REAL)),
                MAX(CAST(value AS REAL))
            FROM health_records
            GROUP BY type
        """)
        
        conn.commit()
    finally:
        conn.close()
```

## Testing and Validation

### Performance Benchmarks
Create test file: `tests/performance/test_config_tab_performance.py`

```python
import time
import pytest
from src.ui.configuration_tab import ConfigurationTab

class TestConfigTabPerformance:
    @pytest.mark.performance
    def test_initial_load_time(self, large_dataset):
        """Test that config tab loads within target time."""
        start_time = time.time()
        
        tab = ConfigurationTab()
        tab.start_background_load()
        
        # Wait for load to complete
        while tab.loader_thread and tab.loader_thread.isRunning():
            time.sleep(0.01)
            
        load_time = time.time() - start_time
        assert load_time < 0.5, f"Load time {load_time}s exceeds 500ms target"
        
    @pytest.mark.performance
    def test_cached_load_time(self, large_dataset):
        """Test that cached loads are near instant."""
        # First load
        tab = ConfigurationTab()
        tab.start_background_load()
        while tab.loader_thread and tab.loader_thread.isRunning():
            time.sleep(0.01)
            
        # Second load (should be cached)
        start_time = time.time()
        tab2 = ConfigurationTab()
        tab2.start_background_load()
        while tab2.loader_thread and tab2.loader_thread.isRunning():
            time.sleep(0.01)
            
        cached_load_time = time.time() - start_time
        assert cached_load_time < 0.1, f"Cached load {cached_load_time}s exceeds 100ms"
```

## Monitoring Implementation

Add to `src/ui/configuration_tab.py`:

```python
import logging
from functools import wraps

def monitor_performance(operation_name):
    """Decorator to monitor operation performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Performance: {operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Performance: {operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

# Apply to key methods
@monitor_performance("config_tab_load")
def _load_from_sqlite(self):
    # ... existing code ...
```

## Rollout Plan

### Phase 1 (Immediate):
1. Deploy SQL aggregation queries
2. Add database indexes
3. Remove auto-load behavior

### Phase 2 (Next Sprint):
1. Implement caching layer
2. Add background loading
3. Deploy progress indicators

### Phase 3 (Future):
1. Create summary tables
2. Implement triggers
3. Add real-time updates

## Success Metrics

Track these metrics post-deployment:
1. Average load time (target: <500ms)
2. Memory usage (target: <50MB)
3. User engagement with Config tab
4. Error rates
5. Cache hit rates

## Rollback Procedures

If issues arise:
1. **Immediate**: Revert to DataFrame loading (existing code)
2. **Cache Issues**: Disable caching via config flag
3. **Thread Issues**: Fall back to synchronous loading
4. **SQL Issues**: Use existing pandas calculations

Each optimization can be toggled independently for granular control.

## References
.simone/06_NOTES/CONFIG_TAB_PERFORMANCE_ANALYSIS.md
.simone/06_NOTES/CONFIG_TAB_OPTIMIZATION_REVIEW.md
.simone/06_NOTES/CONFIG_TAB_PERFORMANCE_OPTIMIZATION_STRATEGY.md
