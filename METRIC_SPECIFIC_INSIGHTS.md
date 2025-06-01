# Metric-Specific Health Insights Feature

## Overview

The Health Insights Widget now supports metric-specific insights, allowing users to focus the analysis on particular health metrics and even specific data sources.

## Features Added

### 1. Metric Selector Combo Box
- Added a "Focus on:" dropdown in the header
- Displays "All Metrics" by default for cross-metric insights
- Dynamically populates with available metrics from the database

### 2. Source-Specific Options
- For metrics with multiple data sources (e.g., iPhone, Apple Watch)
- Shows indented source-specific options like "Steps (iPhone)"
- Allows focused analysis on data from specific devices

### 3. Visual Indicators
- Blue focus frame shows when specific metric is selected
- Summary section indicates the focused metric
- Progress messages reflect the selected metric

### 4. Data Filtering
- `InsightGenerationThread` filters user data based on selection
- Passes metric and source information to the insights engine
- Maintains metadata about applied filters

## Implementation Details

### Key Methods Added:

1. **`_init_metric_mappings()`**
   - Maps Apple Health identifiers to user-friendly names
   - Covers activity, heart, body, sleep, nutrition, and other metrics

2. **`_detect_available_metrics()`**
   - Queries the database for available metric types
   - Identifies unique sources for each metric
   - Populates the metric selector combo box

3. **`_filter_data_for_metric()`**
   - Filters user data to focus on selected metric
   - Applies source filtering when specified
   - Adds filter metadata for the insights engine

### UI Changes:

1. **Metric Combo Box**
   - Minimum width of 200px for readability
   - Tooltip explaining its purpose
   - Connected to refresh insights on change

2. **Focus Indicator**
   - Blue-bordered frame when metric is selected
   - Shows "Insights focused on: [Metric Name]"
   - Uses target emoji (🎯) for visual clarity

3. **Summary Enhancement**
   - Prepends focus information to summary
   - Maintains HTML formatting
   - Separates focus info with horizontal rule

## Usage

1. **View All Insights**: Select "All Metrics" (default)
2. **Focus on Metric**: Select a specific metric like "Steps" or "Heart Rate"
3. **Source-Specific**: Select options like "Steps (iPhone)" for device-specific insights
4. **Refresh**: Changes automatically trigger insight regeneration

## Benefits

- **Targeted Analysis**: Users can drill down into specific health aspects
- **Device Comparison**: Compare insights from different data sources
- **Reduced Noise**: Focus on relevant insights for specific concerns
- **Better Context**: Insights are more relevant when focused on specific metrics

## Future Enhancements

- Add metric category grouping in the dropdown
- Show metric data availability dates
- Add quick filters for common metric combinations
- Support for custom metric groups
- Export metric-specific insight reports