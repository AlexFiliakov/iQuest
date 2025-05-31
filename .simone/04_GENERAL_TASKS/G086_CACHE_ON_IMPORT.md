# G086: Cache on Import - Performance Optimization Hotfix

## Priority: HIGH (Performance Critical)
**Status**: Open  
**Created**: 2025-01-31  
**Category**: Performance, Architecture  

## Overview

Implement summary caching during the data import process to significantly improve application performance. This change will pre-compute all metric summaries during import, allowing tabs to use cached data exclusively, eliminating the need to load individual records from the database after initial import.

## Current Problems

1. **Monthly Dashboard Warning**: "No metrics found in database, using basic set" - indicates missing cache warming
2. **Performance Issues**: Each tab loads and processes raw data on access
3. **Memory Usage**: Loading full datasets into memory for each tab
4. **Redundant Calculations**: Multiple tabs computing similar summaries
5. **Slow Tab Switching**: Each tab change triggers database queries and computations

## Benefits of Cache-on-Import

1. **Instant Tab Loading**: Pre-computed summaries available immediately
2. **Reduced Memory Usage**: No need to load raw records after import
3. **Consistent Performance**: Same fast response regardless of data size
4. **Centralized Logic**: Single source of truth for metric calculations
5. **Better User Experience**: Responsive UI throughout application lifecycle

## Architecture Changes

### 1. Import Flow Enhancement
```
Current Flow:
Import Data → Store in DB → Load Raw Data per Tab → Compute Summaries

New Flow:
Import Data → Store in DB → Compute All Summaries → Cache Results → Tabs Use Cache
```

### 2. Cache Structure
```python
cached_summaries = {
    "daily": {
        "StepCount": {
            "2024-01-15": {"sum": 8542, "avg": 8542, "max": 8542, "min": 8542, "count": 1}
        }
    },
    "weekly": {
        "StepCount": {
            "2024-W03": {"sum": 59794, "avg": 8542, "max": 12453, "min": 5234, "count": 7}
        }
    },
    "monthly": {
        "StepCount": {
            "2024-01": {"sum": 264802, "avg": 8542, "max": 15234, "min": 3421, "count": 31}
        }
    }
}
```

## Implementation Plan

### Phase 1: Core Infrastructure

#### Subtask 1.1: Create Centralized Summary Calculator
**File**: `src/analytics/summary_calculator.py`
```python
class SummaryCalculator:
    """Centralized calculator for all metric summaries."""
    
    def calculate_all_summaries(self, db_path: str, progress_callback=None):
        """Calculate daily, weekly, and monthly summaries for all metrics."""
        # Implementation details below
```

**Implementation Guidance**:
- Consolidate logic from `daily_metrics_calculator.py`, `weekly_metrics_calculator.py`, and `monthly_metrics_calculator.py`
- Use SQL aggregation queries for efficiency
- Support progress callbacks for UI updates
- Batch process by metric type to optimize memory usage

#### Subtask 1.2: Enhance Cache Manager for Summaries
**File**: `src/analytics/cache_manager.py` (modifications)
```python
def cache_import_summaries(self, summaries: Dict[str, Any]):
    """Cache all summaries from import process."""
    # Store in L2 (SQLite) and L3 (compressed) for persistence
    # Use specific TTL: None (permanent until next import)
```

**Implementation Guidance**:
- Add dedicated methods for summary caching
- Implement bulk insert for SQLite cache
- Add compression for L3 cache storage
- Include metadata (import timestamp, record counts)

### Phase 2: Import Process Integration

#### Subtask 2.1: Modify Import Worker
**File**: `src/ui/import_worker.py` (modifications)
```python
def _finalize_import(self):
    """Add summary calculation after data import."""
    self.progress_updated.emit(95, "Calculating summaries...", self.record_count)
    
    # Calculate all summaries
    summary_calculator = SummaryCalculator()
    summaries = summary_calculator.calculate_all_summaries(
        self.db_path,
        progress_callback=self._summary_progress_callback
    )
    
    # Cache summaries
    cache_manager = get_cache_manager()
    cache_manager.cache_import_summaries(summaries)
    
    self.progress_updated.emit(100, "Import complete with cached summaries!", self.record_count)
```

**Implementation Guidance**:
- Add after XML/CSV import completion
- Show progress during summary calculation
- Handle errors gracefully (don't fail import if caching fails)
- Log summary statistics

#### Subtask 2.2: Update Configuration Tab
**File**: `src/ui/configuration_tab.py` (modifications)
- Remove `_warm_monthly_metrics_cache_async()` - no longer needed
- Update `_on_import_completed()` to expect pre-cached summaries
- Add status indicator for cached summary availability

### Phase 3: Tab Optimization

#### Subtask 3.1: Refactor Daily Dashboard
**File**: `src/ui/daily_dashboard_widget.py`
```python
def _load_daily_data(self, date: date):
    """Load daily data from cache instead of database."""
    cache_manager = get_cache_manager()
    
    # Get cached daily summary
    cache_key = f"daily_summary|{self.current_metric}|{date.isoformat()}"
    summary = cache_manager.get(cache_key)
    
    if summary:
        self._update_display(summary)
    else:
        self._show_no_data_message()
```

**Implementation Guidance**:
- Replace database queries with cache lookups
- Remove data processing logic (already done during import)
- Add fallback for missing cache (shouldn't happen normally)
- Simplify update methods

#### Subtask 3.2: Refactor Weekly Dashboard
**File**: `src/ui/weekly_dashboard_widget.py`
- Similar pattern to daily dashboard
- Use ISO week format for cache keys: `weekly_summary|{metric}|{year}-W{week:02d}`

#### Subtask 3.3: Refactor Monthly Dashboard
**File**: `src/ui/monthly_dashboard_widget.py`
- Update `_load_month_data()` to use cached summaries
- Remove `_get_source_specific_daily_value()` and `_get_daily_aggregate_from_db()`
- Simplify calendar heatmap data loading

### Phase 4: Refresh Mechanism

#### Subtask 4.1: Add Refresh Menu Action
**File**: `src/ui/main_window.py`
```python
def _create_view_menu(self):
    """Add refresh action to View menu."""
    refresh_action = QAction("Refresh Summaries", self)
    refresh_action.setShortcut("F5")
    refresh_action.triggered.connect(self._refresh_summaries)
```

**Implementation Guidance**:
- Show progress dialog during refresh
- Recalculate all summaries from database
- Update cache with new values
- Emit signals to update all open tabs

#### Subtask 4.2: Implement Refresh Logic
```python
def _refresh_summaries(self):
    """Manually refresh all cached summaries."""
    dialog = RefreshProgressDialog(self)
    dialog.refresh_completed.connect(self._on_refresh_completed)
    dialog.start_refresh()
```

### Phase 5: Testing Strategy

#### Unit Tests

##### Test 5.1: Summary Calculator Tests
**File**: `tests/unit/test_summary_calculator.py`
```python
def test_calculate_daily_summaries():
    """Test daily summary calculation accuracy."""
    # Create test data
    # Run calculator
    # Verify summaries match expected values
    
def test_calculate_with_missing_data():
    """Test handling of sparse data."""
    # Test gaps in daily data
    # Verify weekly/monthly summaries handle gaps correctly
```

##### Test 5.2: Cache Integration Tests
**File**: `tests/unit/test_cache_import_integration.py`
```python
def test_cache_persistence_after_import():
    """Verify summaries persist in cache after import."""
    # Perform import
    # Restart cache manager
    # Verify summaries still available
```

#### Integration Tests

##### Test 5.3: End-to-End Import Test
**File**: `tests/integration/test_import_with_caching.py`
```python
def test_full_import_with_summary_caching():
    """Test complete import flow with summary caching."""
    # Import test data
    # Verify summaries cached
    # Load each tab
    # Verify no database queries for summaries
    # Check performance metrics
```

##### Test 5.4: Tab Navigation Performance Test
**File**: `tests/performance/test_cached_tab_performance.py`
```python
def test_tab_switching_performance():
    """Verify tab switching uses cache effectively."""
    # Import large dataset
    # Measure tab switching times
    # Verify all times < 100ms
    # Check memory usage remains constant
```

## SQL Queries for Summary Calculation

### Daily Summaries
```sql
-- Optimized daily summary query
WITH daily_stats AS (
    SELECT 
        type,
        DATE(startDate) as date,
        sourceName,
        SUM(CAST(value AS FLOAT)) as sum_value,
        AVG(CAST(value AS FLOAT)) as avg_value,
        MAX(CAST(value AS FLOAT)) as max_value,
        MIN(CAST(value AS FLOAT)) as min_value,
        COUNT(*) as count
    FROM health_records
    WHERE value IS NOT NULL
    GROUP BY type, DATE(startDate), sourceName
)
SELECT 
    type,
    date,
    SUM(sum_value) as total_sum,
    AVG(avg_value) as total_avg,
    MAX(max_value) as total_max,
    MIN(min_value) as total_min,
    SUM(count) as total_count
FROM daily_stats
GROUP BY type, date
ORDER BY type, date;
```

### Weekly Summaries
```sql
-- Optimized weekly summary query
WITH daily_totals AS (
    SELECT 
        type,
        DATE(startDate) as date,
        SUM(CAST(value AS FLOAT)) as daily_sum
    FROM health_records
    WHERE value IS NOT NULL
    GROUP BY type, DATE(startDate)
)
SELECT 
    type,
    strftime('%Y-W%W', date) as week,
    SUM(daily_sum) as sum_value,
    AVG(daily_sum) as avg_value,
    MAX(daily_sum) as max_value,
    MIN(daily_sum) as min_value,
    COUNT(*) as days_with_data
FROM daily_totals
GROUP BY type, strftime('%Y-W%W', date)
ORDER BY type, week;
```

### Monthly Summaries
```sql
-- Optimized monthly summary query
WITH daily_totals AS (
    SELECT 
        type,
        DATE(startDate) as date,
        SUM(CAST(value AS FLOAT)) as daily_sum
    FROM health_records
    WHERE value IS NOT NULL
    GROUP BY type, DATE(startDate)
)
SELECT 
    type,
    strftime('%Y-%m', date) as month,
    SUM(daily_sum) as sum_value,
    AVG(daily_sum) as avg_value,
    MAX(daily_sum) as max_value,
    MIN(daily_sum) as min_value,
    COUNT(*) as days_with_data
FROM daily_totals
GROUP BY type, strftime('%Y-%m', date)
ORDER BY type, month;
```

## Migration Path

1. **Phase 1**: Implement without removing existing code
   - Add new summary calculator
   - Test in parallel with existing system

2. **Phase 2**: Switch to cached summaries
   - Update tabs to prefer cache
   - Keep fallback to old method

3. **Phase 3**: Remove legacy code
   - Delete old calculator methods
   - Clean up unused database queries

## Performance Metrics

### Expected Improvements
- Tab switching: 2-5 seconds → <100ms (95% reduction)
- Memory usage: 500MB-2GB → 100-200MB (80% reduction)
- Initial load after import: 5-10 seconds → <1 second (90% reduction)

### Monitoring
- Add performance logging for cache hits/misses
- Track summary calculation time during import
- Monitor memory usage before/after optimization

## Risk Mitigation

1. **Data Consistency**: Implement cache versioning to handle schema changes
2. **Import Failures**: Ensure partial cache population doesn't break app
3. **Memory Limits**: Batch process large datasets during summary calculation
4. **Backward Compatibility**: Support reading old databases without cached summaries

## Success Criteria

1. ✓ No raw data queries after initial import
2. ✓ All tabs load in <100ms
3. ✓ Memory usage reduced by >50%
4. ✓ Import process includes progress for summary calculation
5. ✓ Manual refresh available and functional
6. ✓ All existing features continue to work
7. ✓ Unit test coverage >90% for new code
8. ✓ Performance benchmarks pass

## Dependencies

- Existing cache infrastructure (`cache_manager.py`)
- Database schema remains stable
- Import process can be extended
- UI framework supports progress updates

## Next Steps

1. Create feature branch: `feature/cache-on-import`
2. Implement Phase 1 infrastructure
3. Add comprehensive unit tests
4. Integrate with import process
5. Update each dashboard tab
6. Performance testing
7. Documentation updates
8. Code review and merge

## Notes

- This is a breaking change for the data flow architecture
- Requires careful testing with various data sizes
- Consider feature flag for gradual rollout
- Update user documentation about refresh functionality