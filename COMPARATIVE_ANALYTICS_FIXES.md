# Comparative Analytics Error Fixes

## Overview
Fixed two critical errors in the comparative analytics functionality:
1. `'NoneType' object has no attribute 'calculate_statistics'`
2. `'DatabaseManager' object has no attribute 'get_metric_data'`

## Fixes Applied

### 1. Fixed NoneType Error in comparative_analytics.py
Added proper error handling and try-except blocks around all `calculate_statistics` calls in the `compare_to_historical` method:

```python
# Before:
current_stats = self.daily_calc.calculate_statistics(metric, start_date, end_date)

# After:
try:
    current_stats = self.daily_calc.calculate_statistics(metric, start_date, end_date)
except AttributeError as e:
    logger.error(f"Error calling calculate_statistics: {e}")
    return HistoricalComparison()
```

This pattern was applied to all 6 statistics calculations:
- Current value calculation
- 7-day rolling average
- 30-day rolling average  
- 90-day rolling average
- 365-day rolling average
- Same period last year

### 2. Fixed DatabaseManager Error in comparative_visualization.py
Replaced the non-existent `get_metric_data` method call with the correct `calculate_statistics` method:

```python
# Before:
stats = calc.get_metric_stats(self.current_metric, start_date, end_date)

# After:
stats = calc.calculate_statistics(self.current_metric, start_date, end_date)
```

Also added proper error handling around the method calls to gracefully handle failures.

## Files Modified
1. `src/analytics/comparative_analytics.py`
   - Added try-except blocks to all `calculate_statistics` calls
   - Added proper null checks for daily calculator

2. `src/ui/comparative_visualization.py`
   - Fixed method name from `get_metric_stats` to `calculate_statistics`
   - Fixed the try-except block syntax issue
   - Added proper error handling for data retrieval

## Result
These fixes ensure that:
- The Personal Progress tab no longer crashes when the daily calculator is None
- The correct method is called on the daily calculator to retrieve statistics
- Errors are properly logged and handled gracefully
- The UI shows appropriate messages when data is unavailable