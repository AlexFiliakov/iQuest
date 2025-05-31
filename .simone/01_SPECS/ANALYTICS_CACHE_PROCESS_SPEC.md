# Analytics Cache Process Specification

## Overview

The Apple Health Monitor Dashboard implements a sophisticated multi-tier caching system to optimize performance for analytics queries. This document provides a comprehensive specification of the cache architecture, workflows, and implementation details.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Cache Tiers](#cache-tiers)
3. [Cache Key Generation](#cache-key-generation)
4. [Cache Workflow](#cache-workflow)
5. [Invalidation Strategies](#invalidation-strategies)
6. [Background Refresh System](#background-refresh-system)
7. [Integration Points](#integration-points)
8. [Performance Monitoring](#performance-monitoring)
9. [Configuration](#configuration)
10. [Implementation Examples](#implementation-examples)

## Architecture Overview

The analytics cache system uses a three-tier architecture designed to balance memory usage, performance, and data persistence:

```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
┌────────▼────────┐
│   L1: Memory    │  ← In-memory LRU cache (fastest)
│   (LRU Cache)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   L2: SQLite    │  ← Persistent indexed cache
│   (Database)    │
└────────┬────────┘
         │
┌────────▼────────┐
│   L3: Disk      │  ← Compressed file storage (largest)
│ (Compressed)    │
└─────────────────┘
```

## Cache Tiers

### L1: Memory Cache (LRU)
- **Purpose**: Ultra-fast access for frequently used data
- **Implementation**: Python LRU cache with size and memory limits
- **Default Configuration**:
  - Max entries: 1,000
  - Max memory: 500MB
  - TTL: 15 minutes
- **Eviction**: Least Recently Used (LRU) algorithm

### L2: SQLite Cache
- **Purpose**: Persistent storage for medium-term data retention
- **Implementation**: SQLite database with indexed queries
- **Default Configuration**:
  - TTL: 24 hours
  - Auto-vacuum enabled
  - WAL mode for concurrency
- **Features**:
  - Corruption recovery
  - Batch operations
  - Query optimization

### L3: Disk Cache
- **Purpose**: Long-term storage for infrequently accessed data
- **Implementation**: GZIP-compressed pickle files
- **Default Configuration**:
  - TTL: 7 days
  - Compression level: 6
  - Metadata in JSON format
- **Storage**: Organized by cache key prefixes

## Cache Key Generation

### Key Format
```
<operation>|<metric>|<parameters>|<filters>
```

### Examples
```
# Daily statistics
daily_stats|StepCount|2024-01-15|none

# Weekly rolling average
weekly_rolling|HeartRate|7|2024-01-01|2024-01-31

# Monthly summary with multiple metrics
monthly_summary|[StepCount,Distance,FlightsClimbed]|2024|01

# Pattern with filters
correlation|StepCount:HeartRate|2024-01-01|2024-12-31|threshold:0.5
```

### Key Components
1. **Operation**: Type of calculation (e.g., daily_stats, monthly_summary)
2. **Metric**: Health metric name or list of metrics
3. **Parameters**: Date ranges, window sizes, etc.
4. **Filters**: Additional query parameters

## Cache Workflow

### Read Path
```
1. Request arrives at CachedCalculator
   ↓
2. Generate cache key from parameters
   ↓
3. Check L1 (Memory)
   ├─ Hit → Return data
   └─ Miss → Continue
   ↓
4. Check L2 (SQLite)
   ├─ Hit → Promote to L1 → Return data
   └─ Miss → Continue
   ↓
5. Check L3 (Disk)
   ├─ Hit → Promote to L2 & L1 → Return data
   └─ Miss → Continue
   ↓
6. Compute result
   ↓
7. Store in cache tiers
   ↓
8. Return data
```

### Write Path
```
1. Compute result
   ↓
2. Check size constraints
   ├─ > 1MB → Skip L1
   └─ ≤ 1MB → Continue
   ↓
3. Store in L1 (if eligible)
   ↓
4. Store in L2 (always)
   ↓
5. Store in L3 (if configured)
   ↓
6. Update access metadata
```

## Invalidation Strategies

### 1. Pattern-Based Invalidation
```python
# Invalidate all entries for a specific metric
cache_manager.invalidate_pattern("metric:StepCount")

# Invalidate date range
cache_manager.invalidate_pattern("date_range:2024-01-01:2024-01-31")

# Invalidate by operation type
cache_manager.invalidate_pattern("daily_stats|*")
```

### 2. Dependency-Based Invalidation
```python
# Set dependencies when caching
cache_manager.set("key", data, dependencies=["base_data_v1"])

# Invalidating dependency cascades to all dependent entries
cache_manager.invalidate_dependency("base_data_v1")
```

### 3. Time-Based Expiration
- Automatic cleanup of expired entries
- Per-tier TTL configuration
- Background cleanup process

### 4. Manual Invalidation
```python
# Clear specific key
cache_manager.delete("specific_key")

# Clear entire cache
cache_manager.clear_all()

# Clear specific tier
cache_manager.clear_tier("l1")
```

## Background Refresh System

### Refresh Monitor Architecture
```
┌─────────────────┐
│ Access Tracker  │ ← Monitors cache access patterns
└────────┬────────┘
         │
┌────────▼────────┐
│ Refresh Queue   │ ← Priority queue of refresh tasks
└────────┬────────┘
         │
┌────────▼────────┐
│ Worker Threads  │ ← Execute refresh computations
└─────────────────┘
```

### Refresh Criteria
1. **Access Count**: Minimum 3 hits to qualify
2. **TTL Threshold**: Refresh at 75% of TTL elapsed
3. **Priority**: Based on access frequency
4. **Concurrency**: Max 2 concurrent refreshes

### Refresh Process
```python
# Automatic registration during cache hits
if access_count >= MIN_ACCESS_COUNT:
    refresh_monitor.schedule_refresh(key, compute_fn, ttl)

# Background worker execution
while True:
    task = refresh_queue.get()
    if task.should_refresh():
        new_data = task.compute_fn()
        cache_manager.set(task.key, new_data)
```

## Integration Points

### 1. Data Import Integration
```python
# During import process
with cache_manager.batch_context() as batch:
    for summary in calculated_summaries:
        batch.cache_summary(summary)
```

### 2. Dashboard Tab Integration
```python
class CachedDataAccess:
    """Reads exclusively from L2 cache after import"""
    
    def get_daily_summary(self, date):
        key = f"import_{import_id}|daily|{date}"
        return self.cache_manager.get_from_l2(key)
```

### 3. Calculator Integration
```python
@analytics_cache(cache_tiers=['l1', 'l2'], ttl=3600)
def calculate_monthly_stats(metric, year, month):
    # Expensive calculation
    return stats
```

## Performance Monitoring

### Cache Metrics Structure
```python
@dataclass
class CacheMetrics:
    # Hit/Miss Tracking
    l1_hits: int
    l1_misses: int
    l2_hits: int
    l2_misses: int
    l3_hits: int
    l3_misses: int
    
    # Operation Counts
    total_requests: int
    cache_sets: int
    invalidations: int
    
    # Resource Usage
    memory_usage_mb: float
    sqlite_size_mb: float
    disk_cache_size_mb: float
    
    # Performance
    avg_l1_response_ms: float
    avg_l2_response_ms: float
    avg_l3_response_ms: float
```

### Monitoring Dashboard
```python
metrics = cache_manager.get_metrics()
print(f"Overall Hit Rate: {metrics.overall_hit_rate:.2%}")
print(f"L1 Hit Rate: {metrics.l1_hit_rate:.2%}")
print(f"Memory Usage: {metrics.memory_usage_mb:.1f}MB")
```

## Configuration

### Environment Variables
```bash
# Cache sizes
CACHE_L1_MAX_SIZE=1000
CACHE_L1_MAX_MEMORY_MB=500

# TTL settings (seconds)
CACHE_L1_TTL=900      # 15 minutes
CACHE_L2_TTL=86400    # 24 hours
CACHE_L3_TTL=604800   # 7 days

# Background refresh
CACHE_REFRESH_ENABLED=true
CACHE_REFRESH_THRESHOLD=0.75
CACHE_REFRESH_MIN_HITS=3
```

### Programmatic Configuration
```python
cache_config = CacheConfiguration(
    l1_config=L1Config(
        max_size=1000,
        max_memory_mb=500,
        ttl_seconds=900
    ),
    l2_config=L2Config(
        ttl_seconds=86400,
        vacuum_interval=3600
    ),
    l3_config=L3Config(
        ttl_seconds=604800,
        compression_level=6
    ),
    refresh_config=RefreshConfig(
        enabled=True,
        threshold=0.75,
        min_access_count=3
    )
)
```

## Implementation Examples

### Example 1: Basic Cache Usage
```python
from src.analytics.cache_manager import get_cache_manager

cache = get_cache_manager()

# Simple get/set
data = cache.get("my_key")
if data is None:
    data = expensive_calculation()
    cache.set("my_key", data, ttl=3600)
```

### Example 2: Cached Calculator
```python
class CachedMonthlyMetricsCalculator:
    def __init__(self, base_calculator, cache_manager):
        self.calculator = base_calculator
        self.cache = cache_manager
    
    def get_monthly_summary(self, metrics, year, month):
        cache_key = f"monthly_summary|{','.join(metrics)}|{year}|{month:02d}"
        
        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # Calculate if not cached
        result = self.calculator.calculate_monthly_summary(metrics, year, month)
        
        # Cache with appropriate TTL
        ttl = 7200 if month == datetime.now().month else 21600
        self.cache.set(cache_key, result, ttl=ttl)
        
        return result
```

### Example 3: Batch Import Caching
```python
def cache_import_summaries(summaries, import_id):
    """Cache pre-computed summaries during import"""
    with cache_manager.get_l2_connection() as conn:
        cursor = conn.cursor()
        
        # Prepare batch data
        cache_entries = []
        for date, summary in summaries.items():
            key = f"import_{import_id}|daily|{date}"
            value = pickle.dumps(summary)
            expires = datetime.now() + timedelta(hours=24)
            cache_entries.append((key, value, expires))
        
        # Bulk insert
        cursor.executemany(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            cache_entries
        )
        conn.commit()
```

### Example 4: Cache Warmup
```python
def warmup_common_queries():
    """Pre-populate cache with common queries"""
    warmup_tasks = [
        ("daily_stats|StepCount|today", calculate_today_steps),
        ("weekly_summary|current", calculate_current_week),
        ("monthly_trends|current", calculate_current_month)
    ]
    
    for key, compute_fn in warmup_tasks:
        if not cache_manager.exists(key):
            data = compute_fn()
            cache_manager.set(key, data)
```

## Best Practices

1. **Key Design**: Use hierarchical, predictable key patterns
2. **TTL Strategy**: Shorter TTL for current data, longer for historical
3. **Size Limits**: Monitor object sizes to prevent memory issues
4. **Batch Operations**: Use batch methods for bulk updates
5. **Error Handling**: Graceful degradation on cache failures
6. **Monitoring**: Regular review of hit rates and performance metrics

## Troubleshooting

### Common Issues

1. **Low Hit Rates**
   - Check key generation consistency
   - Verify TTL settings
   - Monitor invalidation patterns

2. **Memory Issues**
   - Review L1 cache size limits
   - Check for large object caching
   - Enable size-based filtering

3. **Slow Performance**
   - Ensure SQLite indexes are present
   - Check disk I/O for L3 cache
   - Monitor background refresh load

4. **Cache Corruption**
   - Automatic recovery for SQLite
   - Manual cleanup for disk cache
   - Check disk space availability

## Future Enhancements

1. **Distributed Caching**: Redis integration for multi-instance deployments
2. **Smart Prefetching**: ML-based prediction of future queries
3. **Compression Optimization**: Adaptive compression based on data type
4. **Cache Analytics**: Detailed usage patterns and optimization recommendations
5. **Dynamic TTL**: Adjust TTL based on access patterns and data volatility

---

*This specification documents the analytics cache process as implemented in the Apple Health Monitor Dashboard. For implementation details, refer to the source code in `src/analytics/cache_manager.py` and related modules.*