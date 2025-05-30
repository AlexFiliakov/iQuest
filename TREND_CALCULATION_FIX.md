# Trend Calculation Database Error Fix

## Overview
Fixed the error: `'DatabaseManager' object has no attribute 'get_metric_data'` that was occurring during trend calculations.

## Root Cause
The `BackgroundTrendProcessor` was trying to call a non-existent method `get_metric_data()` on the DatabaseManager object. The DatabaseManager doesn't have this method - instead, it provides generic query methods like `execute_query()`.

## Fixes Applied

### 1. Fixed Database Query in background_trend_processor.py
Replaced the non-existent method call with a proper SQL query:

```python
# Before:
data = self.database.get_metric_data(
    metric=metric,
    start_date=start_date,
    end_date=end_date
)

# After:
query = """
    SELECT type, creationDate, value, unit, sourceName
    FROM health_records
    WHERE type = ?
    AND creationDate >= ?
    AND creationDate <= ?
    ORDER BY creationDate
"""
params = (metric, start_date.isoformat(), end_date.isoformat())
rows = self.database.execute_query(query, params)

# Convert to expected format
data = []
for row in rows:
    data.append({
        'date': datetime.fromisoformat(row['creationDate']),
        'value': float(row['value']),
        'unit': row['unit'],
        'source': row['sourceName']
    })
```

### 2. Fixed Method Name for Historical Comparison
Also fixed an incorrect method call to the comparative analytics engine:

```python
# Before:
historical_comparison = self.comparative_engine.get_historical_comparison(
    metric=metric,
    current_date=end_date
)

# After:
historical_comparison = self.comparative_engine.compare_to_historical(
    metric=metric,
    current_date=end_date
)
```

## Files Modified
- `src/analytics/background_trend_processor.py`
  - Lines 155-180: Replaced get_metric_data() with proper SQL query
  - Line 195: Fixed method name from get_historical_comparison to compare_to_historical

## Result
- Trend calculations now properly query the health_records table
- The data is correctly formatted for the trend analysis engine
- Historical comparisons use the correct method name
- The error should no longer occur when calculating trends

## Additional Notes
There are other files that also use `get_metric_data()` which might need similar fixes:
- correlation_discovery.py
- export_reporting_system.py
- wsj_health_visualization_suite.py

These should be addressed if they cause similar errors.