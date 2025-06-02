# G092: Add Source Name to Cache Architecture

**ID**: G092  
**Type**: Hotfix  
**Priority**: Critical  
**Created**: 2025-01-06  
**Status**: Not Started  
**Complexity**: Medium  
**Estimated Hours**: 8-12  

## Context and Background

The current caching architecture aggregates all health data sources together, preventing users from viewing source-specific metrics (e.g., "Steps from iPhone" vs "Steps from Apple Watch"). While the database schema includes a `source_name` column in the `cached_metrics` table, it is not being populated or utilized by the caching algorithms.

This limitation affects all the Daily, Weekly and Monthly dashboards, which can only display "(All Sources)" when using cached data access, despite users expecting to see source-specific options as they do when accessing the database directly.

**References**:
- Issue identified in Daily/Weekly/Monthly dashboard metric selection
- `cached_metrics` table has unused `source_name` column (database.py:383-401)
- Cache infrastructure supports source filtering but doesn't use it

## Requirements and Goals

### Primary Requirements
1. **Populate `source_name` in cached metrics** during data import
2. **Cache both aggregated and source-specific summaries** for each metric
3. **Enable source-based cache retrieval** in CachedMetricsAccess
5. **Optimize performance** to handle increased cache size

### Goals
- Users can select source-specific metrics in Daily/Monthly dashboards when using cached access
- Cache performance remains acceptable despite increased data volume
- Existing functionality continues to work without disruption

## Acceptance Criteria

1. **Data Population**:
   - [ ] `cached_metrics` table contains entries with `source_name` populated
   - [ ] Each metric has both aggregated (source_name=NULL) and source-specific entries
   - [ ] Import process successfully caches all source combinations

2. **Retrieval Functionality**:
   - [ ] `CachedMetricsAccess.get_daily_summary()` accepts optional `source_name` parameter
   - [ ] Daily dashboard shows source-specific options when using cached access
   - [ ] Weekly dashboard shows source-specific options when using cached access
   - [ ] Monthly dashboard shows source-specific options when using cached access

## Technical Approach

### Approach: Minimal Change - Add Source Loop to Existing Flow

**Implementation**:
1. Modify `summary_calculator.py` to calculate summaries grouped by source
2. Update import worker to loop through sources and cache each separately
3. Add source parameter to cache retrieval methods
4. Update UI components to pass source filter when needed

**Pros**:
- Minimal code changes required
- Leverages existing cache infrastructure
- Easy to implement and test
- Low risk of breaking existing functionality

**Cons**:
- May result in slower import times (N sources × M metrics)
- Increased cache size (multiplied by number of sources)
- Requires careful handling of aggregated "All Sources" data

### Recommended Approach: Approach 1 with Optimizations

Start with Approach 1 for its simplicity and lower risk, but include these optimizations:
- Use bulk insert operations for cache entries
- Calculate aggregated data once and reuse for "All Sources"
- Implement source filtering at the SQL level for efficiency
- Add database indexes on (metric_type, date, source_name)

## Implementation Steps

### Phase 1: Database and Infrastructure Updates
1. **Add indexes** to cached_metrics table:
   ```sql
   CREATE INDEX idx_cached_metrics_lookup 
   ON cached_metrics(metric_type, date, source_name, summary_type);
   ```

2. **Update CacheDAO** (`data_access.py`):
   - Modify `get_cached_metrics()` to filter by source_name
   - Ensure `cache_metrics()` properly stores source_name
   - Update cache key generation to include source

### Phase 2: Summary Calculation Updates
3. **Create source-aware summary calculation** (`summary_calculator.py`):
   - Add `calculate_summaries_by_source()` method
   - Maintain existing `calculate_summaries()` for backward compatibility
   - Optimize queries to minimize database round trips

4. **Update import worker** (`import_worker.py`):
   - Modify `_populate_cached_metrics_table()` to cache per-source data
   - Cache both individual sources and aggregated "All Sources"
   - Use transactions for batch inserts

### Phase 3: Access Layer Updates
5. **Update CachedMetricsAccess** (`cached_metrics_access.py`):
   - Add `source_name` parameter to all retrieval methods
   - Maintain backward compatibility with default None
   - Update `get_available_metrics()` to return source information

6. **Update CachedDataAccess** (`cached_data_access.py`):
   - Modify `get_available_metrics()` to return List[Tuple[str, Optional[str]]]
   - Add `get_available_sources()` method
   - Ensure compatibility with existing UI code

### Phase 4: UI Integration
7. **Update dashboard widgets**:
   - Modify `_detect_available_metrics()` to use new source data
   - Ensure proper source filtering in data retrieval

### Phase 5: Testing and Migration
8. **Create comprehensive tests**:
   - Unit tests for source-aware caching

## Dependencies

- **Database**: Existing `cached_metrics` table structure
- **Import System**: Current import worker and summary calculator
- **UI Components**: Daily, Weekly, and Monthly dashboard widgets
- **Testing**: Existing test infrastructure and fixtures

## Testing Strategy

### Unit Tests
- Test source-aware summary calculation with multiple sources
- Verify cache key generation includes source
- Test retrieval with and without source filtering
- Ensure backward compatibility

## Documentation Updates

1. Update cache architecture documentation
2. Add source filtering examples to API docs
3. Update import process documentation

## Risk Mitigation

1. **Performance Impact**: 
   - Monitor import times in staging
   - Implement progress indicators
   - Consider phased rollout

2. **Cache Size Growth**:
   - Calculate expected size increase
   - Implement cache size limits
   - Consider compression options

## Success Metrics

- Source-specific metrics available in UI when using cache
- Zero regression in existing functionality
- User satisfaction with source filtering capability

## Notes

This hotfix addresses a critical limitation in the current caching architecture that prevents users from analyzing their health data by source. The implementation should prioritize reliability and performance while maintaining the existing user experience for those who don't need source filtering.