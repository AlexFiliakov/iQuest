# Source-Specific Metrics Implementation

## Problem
The Monthly tab was double-counting statistics when the same metric type had data from multiple sources. For example:
- Steps from iPhone: 5,000
- Steps from Apple Watch: 3,000
- Total shown: 8,000 (incorrect - likely includes overlap)

## Solution
Implemented source-specific metric selection in the format: `<type> - <source>`

### Changes Made

1. **Updated Metric Loading**
   - Modified `_load_available_metrics()` to query each source separately
   - Creates tuples of (metric_type, source) for each combination
   - Also includes "All Sources" option for aggregated view
   - Example: "Steps - iPhone (9)", "Steps - Apple Watch", "Steps (All Sources)"

2. **Enhanced Dropdown Display**
   - Combo box now shows: `{Metric Name} - {Source}` or `{Metric Name} (All Sources)`
   - Sorted by metric name, then by source for easy navigation

3. **Source-Specific Data Queries**
   - Added `_get_source_specific_daily_value()` method
   - Queries database with source filtering: `WHERE sourceName = ?`
   - Prevents double-counting by only summing data from the specified source

4. **Backward Compatibility**
   - Internal data structure uses tuples: (metric_type, source)
   - External signals still emit just the metric type
   - "All Sources" option provides original aggregated behavior

### Database Query Example
```sql
SELECT SUM(CAST(value AS FLOAT)) as daily_total
FROM health_records
WHERE type = ?
AND DATE(startDate) = ?
AND sourceName = ?
AND value IS NOT NULL
```

### Benefits
- Accurate metrics without double-counting
- Users can compare data from different devices
- Transparency about data sources
- Option to view aggregated or source-specific data

### User Experience
Users will now see options like:
- Steps - iPhone (9)
- Steps - Apple Watch Series 7
- Steps (All Sources)
- Heart Rate - Apple Watch Series 7
- Heart Rate (All Sources)

This allows users to:
1. View data from a specific device only
2. Compare metrics between devices
3. Still see aggregated totals when desired