# Weekly Tab Specification

## Overview
The Weekly Tab provides comprehensive weekly health data analysis with 7-day rolling statistics, week-over-week comparisons, and trend analysis. It serves as the primary interface for users to understand their weekly health patterns and progress.

## Core Features

### 1. Week Navigation
- **Week Selection**: Navigate between weeks using previous/next buttons
- **Current Week Indicator**: Highlights the current week with a "This Week" button
- **Week Display**: Shows week number and date range (Monday to Sunday, ISO standard)
- **Week Boundaries**: Uses Monday as the first day of the week (ISO 8601 standard)

### 2. Metric Selection
- **Dynamic Metric Detection**: Automatically detects available health metrics from imported data
- **Supported Metrics**:
  - Steps (`HKQuantityTypeIdentifierStepCount`)
  - Distance (`HKQuantityTypeIdentifierDistanceWalkingRunning`) 
  - Floors Climbed (`HKQuantityTypeIdentifierFlightsClimbed`)
  - Active Calories (`HKQuantityTypeIdentifierActiveEnergyBurned`)
  - Heart Rate (`HKQuantityTypeIdentifierHeartRate`)
  - Resting Heart Rate (`HKQuantityTypeIdentifierRestingHeartRate`)
  - Heart Rate Variability (`HKQuantityTypeIdentifierHeartRateVariabilitySDNN`)
  - Weight (`HKQuantityTypeIdentifierBodyMass`)
- **Metric Selector**: Dropdown allowing users to switch between available metrics

### 3. Weekly Summary Statistics
Displayed as a 2x3 grid of statistical cards:

#### Row 1:
- **Weekly Average**: Mean daily value for the selected metric
- **Weekly Total**: Sum of all daily values for the week
- **Best Day**: Highest daily value with day abbreviation

#### Row 2:
- **Worst Day**: Lowest daily value with day abbreviation
- **Trend**: Direction indicator (↑ up, ↓ down, → stable) with text description
- **Volatility**: Coefficient of variation as a percentage

### 4. Week-over-Week Comparison
- **Previous Week Comparison**: Shows percentage change from previous week
- **Trend Analysis**: Statistical trend detection using regression analysis
- **Visual Indicators**: Color-coded improvements/declines

### 5. Weekly Patterns Section
- **Section Title**: "Weekly Patterns" (not "Day-of-Week Patterns")
- **View Options**: Radio button selection between:
  - Daily Values (default)
  - Cumulative 
  - 7-Day Average
- **Trend Chart**: Line chart visualization using LineChart component
- **Interactive Elements**: View switching updates chart display

## Technical Implementation

### Data Flow
1. **Data Source**: Uses `DailyMetricsCalculator` as the primary data source
2. **Weekly Calculator**: `WeeklyMetricsCalculator` processes daily data into weekly metrics
3. **Data Transformation**: Converts raw health data into weekly aggregations
4. **Real-time Updates**: Refreshes when new data is loaded or filters are applied

### UI Components
- **Main Widget**: `WeeklyDashboardWidget` (standard version currently active)
- **Stat Cards**: `WeeklyStatCard` components for displaying statistics
- **Week Navigation**: Header with navigation controls and week display
- **Scrollable Content**: Vertical scroll area containing all sections

### Data Processing
- **Week Calculation**: Uses ISO 8601 week numbering (Monday start)
- **Data Method**: Uses `calculate_weekly_metrics()` from WeeklyMetricsCalculator
- **Column Mapping**: Maps 'startDate' to 'creationDate' for calculator compatibility
- **Metric Aggregation**: 
  - Average: Mean of daily values for the week
  - Total: Sum of all daily values
  - Best/Worst: Max/Min daily values with day identification
  - Trend: Direction based on first vs second half of week comparison
  - Volatility: Coefficient of variation (std dev / mean * 100)

### Cache-on-Import Integration (NEW)
- **Cached Data Access**: When `use_cached_data=True`, uses pre-computed weekly summaries
- **Implementation**: `cached_data_access.py` provides cache-only data layer
- **Cache Key Pattern**: `weekly_summary|{metric_type}|{year}-W{week}`
- **Pre-computed Metrics**: Weekly aggregations calculated during import
- **Performance**: Tab switching reduced from 2-5s to <100ms
- **SQL Query**: Uses ISO week aggregation with daily totals

## User Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    Week Navigation Header                    │
│  ◀ [Week 22] May 26 - June 1, 2025 ▶  [This Week]         │
├─────────────────────────────────────────────────────────────┤
│                  Week at a Glance                          │
│  Metric: [Steps ▼]                                         │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │📊 Avg   │ │Σ Total  │ │🏆 Best  │                      │
│  │ 8,234   │ │ 57,640  │ │ 12,456  │                      │
│  │daily avg│ │wkly tot │ │   Mon   │                      │
│  └─────────┘ └─────────┘ └─────────┘                      │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │📉 Worst │ │📈 Trend │ │📊 Vol   │                      │
│  │  4,521  │ │    ↑    │ │  15.2%  │                      │
│  │   Wed   │ │   up    │ │coef var │                      │
│  └─────────┘ └─────────┘ └─────────┘                      │
├─────────────────────────────────────────────────────────────┤
│              Week-over-Week Comparison                      │
│  [Week-over-week comparison widget]                        │
├─────────────────────────────────────────────────────────────┤
│                Weekly Patterns                             │
│  View: ( ) Daily Values (•) Cumulative ( ) 7-Day Average  │
│  [Line chart showing selected view pattern]                │
└─────────────────────────────────────────────────────────────┘
```

## State Management

### Widget States
- **No Data**: Shows instructional overlay when no health data is loaded
- **Loading**: Brief loading state during data processing
- **Active**: Normal operational state with data displayed
- **Error**: Graceful error handling with user-friendly messages

### Data Refresh Triggers
- **Tab Activation**: Refreshes when weekly tab becomes active
- **Data Import**: Updates when new health data is imported
- **Filter Changes**: Responds to data filter modifications
- **Week Navigation**: Updates when user navigates between weeks
- **Metric Selection**: Refreshes when user selects different metrics

## Error Handling

### Graceful Degradation
- **Missing Data**: Shows appropriate messages for weeks with no data
- **Calculation Errors**: Handles edge cases (divide by zero, missing values)
- **UI Resilience**: Maintains layout integrity even with missing components

### User Feedback
- **Loading States**: Visual indicators during data processing
- **Error Messages**: Clear, actionable error descriptions
- **No Data States**: Instructional guidance for users with empty datasets

## Performance Considerations

### Optimization Features
- **Lazy Loading**: Sections load on demand
- **Caching**: Weekly calculations are cached for performance
- **Background Processing**: Heavy calculations run asynchronously
- **UI Responsiveness**: Non-blocking operations maintain UI responsiveness

### Memory Management
- **Data Cleanup**: Proper cleanup of temporary calculations
- **Widget Lifecycle**: Appropriate resource management
- **Update Batching**: Batch UI updates to reduce repaints

## Accessibility Features

### Visual Accessibility
- **High Contrast**: Support for high contrast themes
- **Font Scaling**: Respects system font size preferences
- **Color Independence**: Information conveyed through multiple visual channels

### Interaction Accessibility
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **Focus Management**: Clear focus indicators and logical tab order

## Integration Points

### Main Application
- **Tab System**: Integrates with main application tab widget
- **Data Pipeline**: Connects to configuration tab data source
- **Settings**: Respects user preferences and settings

### Other Tabs
- **Daily Tab**: Provides drill-down capability to daily details
- **Monthly Tab**: Offers higher-level aggregation view
- **Comparison Tab**: Enables cross-metric and cross-timeframe analysis

## Future Enhancements

### Planned Features
- **Goal Integration**: Weekly goal tracking and progress
- **Insights Generation**: AI-powered weekly insights and recommendations
- **Export Capabilities**: PDF and image export of weekly summaries
- **Custom Metrics**: User-defined calculated metrics

### Technical Improvements
- **Modern UI**: Migration to modern dashboard widget version (currently disabled due to display issues)
- **Performance**: Further optimization of data processing
- **Chart Enhancements**: Additional chart types and interactive features
- **Customization**: User-configurable dashboard layouts

## Current Known Issues

### Display Problems (Recently Fixed)
- **TypeError in charts**: Fixed QPoint/QPointF type mismatch in mouse events
- **Data refresh**: Fixed data loading from configuration tab
- **No data overlay**: Fixed import issues with Qt attributes
- **Widget visibility**: Added forced UI updates and repaints

### Modern Widget Issues
- **Modern Version**: Currently disabled due to display problems
- **Fallback**: Uses standard WeeklyDashboardWidget as primary implementation