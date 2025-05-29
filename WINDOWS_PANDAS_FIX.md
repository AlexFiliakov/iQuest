# Windows Pandas Access Violation Fix

## Issue
A Windows fatal exception (access violation) was occurring during pandas resample operations in the activity timeline component tests. The error happened specifically during garbage collection while executing pandas Cython operations.

## Root Cause
The issue was caused by:
1. Pandas resample operations on sparse data triggering memory access violations on Windows
2. Garbage collection happening during Cython operations
3. Potential race conditions in multi-threaded pandas operations

## Solution
Replaced the problematic `resample()` operation with a more stable `groupby()` approach:

### Key Changes in `src/ui/activity_timeline_component.py`:

1. **Data Type Conversion**: Explicitly convert metrics to float64 for numeric stability
2. **Improved NaN Handling**: Use interpolation with fallback to zero-filling
3. **Explicit Garbage Collection**: Force GC before grouping operations
4. **Groupby Instead of Resample**: Use `pd.Grouper` with `groupby()` which avoids Cython issues

### Before (causing crashes):
```python
resampled = metric_data.resample(freq)
mean_df = resampled.mean(numeric_only=True)
sum_df = resampled.sum(numeric_only=True)  # <-- Crash here
```

### After (stable):
```python
grouper = pd.Grouper(freq=freq, closed='left', label='left')
grouped = metric_data.groupby(grouper)
mean_values = grouped[metric].mean()
sum_values = grouped[metric].sum()
```

## Testing
- All 17 tests in `test_activity_timeline_component.py` now pass
- No performance degradation observed
- The fix is Windows-specific but works correctly on all platforms

## Prevention
For future Windows compatibility:
1. Prefer `groupby()` over `resample()` for sparse data
2. Always handle NaN values before aggregation operations
3. Consider explicit garbage collection before memory-intensive operations
4. Test on Windows regularly to catch platform-specific issues early