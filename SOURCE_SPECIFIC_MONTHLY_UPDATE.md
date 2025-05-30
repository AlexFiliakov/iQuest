# Source-Specific Monthly Tab Update

## Overview
Updated the Monthly tab to support selecting metrics by specific source device/app, not just "All Sources". This prevents double-counting when the same metric has data from multiple sources.

## Changes Made

### 1. Calendar Heatmap Component (`src/ui/charts/calendar_heatmap.py`)
- Modified `set_metric_data()` to accept an optional `source` parameter
- Added `_metric_source` attribute to track the selected source
- Updated tooltip to show source information: "Steps (iPhone): 10,234"
- Updated calendar title to include source: "Steps (iPhone) Calendar Heatmap"

### 2. Monthly Dashboard Widget (`src/ui/monthly_dashboard_widget.py`)
- Updated `_load_month_data()` to pass source information to the calendar heatmap
- Calendar now displays source-specific data when a specific source is selected
- Maintains backward compatibility - "All Sources" option still works as before

## User Experience

### Dropdown Display
Users see options like:
- Steps - iPhone (9)
- Steps - Apple Watch Series 7
- Steps (All Sources)
- Heart Rate - Apple Watch Series 7
- Heart Rate (All Sources)

### Calendar Display
- Title shows: "Steps (iPhone) Calendar Heatmap" when iPhone is selected
- Tooltip shows: "December 5, 2024\nSteps (iPhone): 8,543"
- Data displayed is filtered to only show values from the selected source

### Benefits
1. **Accurate Metrics**: No more double-counting from multiple devices
2. **Device Comparison**: Easy to compare data between devices
3. **Transparency**: Clear visibility of data sources
4. **Flexibility**: Option to view aggregated or source-specific data

## Technical Implementation

The implementation uses tuples `(metric_type, source)` internally to track both the metric and its source. The calendar heatmap component was enhanced to:
- Accept and store source information
- Display source in tooltips and titles
- Maintain full backward compatibility

## Testing
A test script was created to verify the functionality:
- Shows multiple sources in the dropdown
- Displays source-specific data in the calendar
- Shows source information in tooltips and titles

## Next Steps
The implementation is complete and ready for use. Users can now:
1. Select specific sources from the dropdown
2. View accurate, non-duplicated metrics
3. Compare data between different devices
4. Still access aggregated "All Sources" view when needed