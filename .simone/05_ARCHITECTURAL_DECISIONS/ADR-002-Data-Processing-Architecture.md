# ADR-002: Data Processing Architecture

## Status
Accepted

## Context
The application needs to process potentially large CSV files (100MB+) containing Apple Health data with millions of records. We need an architecture that:
- Handles large files without freezing the UI
- Provides fast filtering and aggregation
- Minimizes memory usage
- Allows for future scalability

## Decision
We will use a **hybrid in-memory/streaming approach** with pandas for data processing, combined with SQLite for persistent storage of derived metrics and user data.

## Rationale

### Options Considered

#### 1. Full In-Memory Processing
**Approach:** Load entire CSV into pandas DataFrame

**Pros:**
- Fastest query performance
- Simple implementation
- Full pandas functionality available

**Cons:**
- High memory usage (2-3x file size)
- Long initial load times
- Risk of out-of-memory errors

#### 2. Pure Streaming/Chunked Processing
**Approach:** Process CSV in chunks, never loading full dataset

**Pros:**
- Minimal memory usage
- Can handle any file size

**Cons:**
- Much slower for repeated queries
- Complex implementation
- Limited analytical capabilities

#### 3. Database-First Approach
**Approach:** Import CSV into SQLite, query from database

**Pros:**
- Consistent memory usage
- Good query performance
- Built-in persistence

**Cons:**
- Slow initial import
- Less flexible for complex analytics
- Additional storage requirements

#### 4. Hybrid Approach (Selected)
**Approach:** Smart caching with streaming fallback

**Implementation:**
```python
class DataProcessor:
    def __init__(self, memory_limit_mb=500):
        self.memory_limit = memory_limit_mb
        self.data_cache = {}
        self.metrics_db = SQLiteCache()
    
    def process_file(self, csv_path):
        file_size = os.path.getsize(csv_path)
        estimated_memory = file_size * 2.5
        
        if estimated_memory < self.memory_limit:
            # Small file: Load entirely
            return pd.read_csv(csv_path, parse_dates=['startDate'])
        else:
            # Large file: Stream and cache aggregates
            return self.stream_process(csv_path)
```

### Decision Factors

1. **User Experience**: Most users will have <100MB files that fit in memory
2. **Performance**: In-memory operations are 10-100x faster than disk
3. **Flexibility**: Pandas provides rich analytical capabilities
4. **Scalability**: Streaming fallback handles edge cases
5. **Caching**: SQLite stores computed metrics for fast retrieval

## Architecture Details

### Data Flow
```
CSV File → Size Check → Small: Load to Memory → Process
                    ↓
                    → Large: Stream Process → Cache Metrics → Display
                                          ↓
                                      SQLite Cache
```

### Caching Strategy
```python
# Cache key generation
def generate_cache_key(filters, metric_type, aggregation):
    return hashlib.md5(
        f"{filters}{metric_type}{aggregation}".encode()
    ).hexdigest()

# Cache storage
cached_metrics = {
    'cache_key': 'abc123...',
    'data': {...},
    'expires_at': datetime.now() + timedelta(hours=24)
}
```

## Consequences

### Positive
- Optimal performance for typical use cases
- Graceful degradation for large files
- Efficient memory usage
- Fast repeated queries via caching
- Future-proof architecture

### Negative
- More complex implementation
- Cache invalidation complexity
- Potential cache size growth
- Different code paths to maintain

### Mitigation
- Clear cache size limits (50MB default)
- Automatic cache expiration (24 hours)
- User-controllable cache clearing
- Comprehensive testing of both paths
- Performance monitoring and alerts

## Implementation Guidelines

### Memory Management
```python
# Monitor memory usage
import psutil

def check_memory_usage():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    return memory_mb

# Adaptive loading
def load_with_memory_check(file_path, chunk_size=10000):
    if check_memory_usage() > MEMORY_THRESHOLD:
        return pd.read_csv(file_path, chunksize=chunk_size)
    else:
        return pd.read_csv(file_path)
```

### Performance Optimization
1. Use categorical dtypes for repeated strings
2. Parse dates on load to avoid repeated conversion
3. Index DataFrames by date for faster filtering
4. Use numba for custom aggregations if needed

## References
- [Pandas Memory Optimization](https://pandas.pydata.org/docs/user_guide/scale.html)
- [Working with Large Datasets](https://realpython.com/python-pandas-tricks/)
- [SQLite Performance Tips](https://www.sqlite.org/fastinsert.html)