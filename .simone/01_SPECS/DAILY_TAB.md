# Daily Tab Specification

## Overview
The Daily Tab provides a comprehensive view of daily health metrics with real-time updates, trend analysis, and interactive visualizations. It serves as the primary dashboard for viewing and analyzing health data on a day-by-day basis.

## Current Implementation Status
- **Status**: Implemented with recent bug fixes
- **Last Updated**: May 2025
- **Key Issues Resolved**: Data loading, timezone handling, date filtering

## Core Features

### 1. Date Navigation
- **Current Date Display**: Shows "Today's Summary" for current date, day name for other dates
- **Navigation Controls**:
  - Previous/Next day buttons (◀/▶)
  - Date picker with calendar popup
  - "Today" button to quickly return to current date
  - Next day button disabled for future dates
- **Date Format**: Displays as "Month Day, Year" with relative descriptions (Yesterday, Tomorrow, etc.)

### 2. Health Metrics Display

#### Metric Cards Grid
- **Layout**: 4 columns, up to 8 metric cards maximum
- **Supported Metrics**:
  - Steps (priority 1)
  - Distance in km (priority 2) 
  - Floors climbed (priority 3)
  - Active calories (priority 4)
  - Heart rate (priority 5)
  - Resting heart rate (priority 6)
  - HRV (priority 7)
  - Sleep hours (priority 8)
  - Weight (priority 9)
  - Body fat percentage (priority 10)

#### Card Features
- **Visual Design**: 120px fixed height, rounded corners (12px), shadow effects, hover states with color transitions
- **Content**: Display name, current value with unit, trend indicator (DailyTrendIndicator component)
- **Interactivity**: Clickable with pointing hand cursor to select for detailed view
- **Trend Indicators**: Show percentage change vs previous day for steps and active_calories only
- **Value Formatting**: Large values (≥100) shown as integers, smaller values with 1 decimal place

### 3. Summary Section
Four summary cards (SummaryCard components) showing:
- **Activity Score**: Based on steps (50%) and calories (50%), calculated as min(100, (value/target)*100)
- **Goals Progress**: Average progress toward daily targets (steps: 10,000, calories: 500, floors: 10)
- **Personal Bests**: Count of new records achieved today using PersonalRecordsTracker
- **Health Status**: Overall health score starting at 70 with adjustments for heart rate, HRV, and activity

### 4. Activity Timeline
- **Visualization**: Horizontal timeline showing hourly activity data
- **Primary Metric**: Steps data by hour
- **Height**: Fixed at 200px
- **Data**: Shows only hours with recorded activity

### 5. Detailed View Section
- **Metric Selector**: Dropdown with icons and display names for available metrics
- **Chart Display**: LineChart component showing hourly data for selected metric (300px minimum height)
- **Interactive**: Updates automatically when metric selection changes via QTimer.singleShot
- **Chart Features**: Grid lines enabled, proper y-range scaling (0.9x min to 1.1x max), axis labels
- **Data Processing**: Only shows hours with recorded activity (value > 0)

## Data Integration

### Data Sources
- **Primary**: DailyMetricsCalculator with timezone support
- **Apple Health Types Mapped**:
  - `HKQuantityTypeIdentifierStepCount` → steps
  - `HKQuantityTypeIdentifierDistanceWalkingRunning` → distance
  - `HKQuantityTypeIdentifierFlightsClimbed` → flights_climbed
  - `HKQuantityTypeIdentifierActiveEnergyBurned` → active_calories
  - `HKQuantityTypeIdentifierHeartRate` → heart_rate
  - `HKQuantityTypeIdentifierRestingHeartRate` → resting_heart_rate
  - `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` → hrv
  - `HKQuantityTypeIdentifierBodyMass` → weight
  - `HKQuantityTypeIdentifierBodyFatPercentage` → body_fat

### Data Processing
- **Timezone Handling**: Uses `time.tzname[0]` for local timezone, passed to DailyMetricsCalculator constructor
- **Date Normalization**: Uses `pd.to_datetime(data['creationDate']).dt.normalize().dt.date` for consistent comparison
- **Aggregation**: Groups multiple readings per day using mean for most metrics, sum for cumulative metrics
- **Caching**: Two-level caching - statistics cache (`_stats_cache`) and hourly data cache (`_hourly_cache`)
- **Cache Invalidation**: Automatically clears cache when `_current_date` changes

## User Experience

### Loading States
- **No Data Loaded**: Shows message directing user to Configuration tab
- **No Data for Date**: Shows date-specific message with navigation hints
- **Loading**: Smooth transitions between dates

### Performance Optimizations
- **Debounced Updates**: 50ms delay to prevent excessive recalculation during navigation
- **Smart Caching**: Caches statistics and hourly data per date with automatic invalidation
- **Lazy Loading**: Timeline and chart data only loaded when widgets are visible
- **Auto-refresh**: Updates every 60 seconds (60000ms) when viewing today
- **Event Processing**: Uses QApplication.processEvents() for smooth UI updates

### Error Handling
- **Missing Data**: Graceful handling with "--" placeholders
- **Calculation Errors**: Logged and handled without UI crashes
- **Invalid Dates**: Validation prevents selection of future dates

## Technical Architecture

### Key Classes
- **DailyDashboardWidget**: Main container widget
- **MetricCard**: Individual metric display components
- **DailyMetricsCalculator**: Core data processing engine
- **ActivityTimelineComponent**: Timeline visualization
- **LineChart**: Detailed metric charting

### Signal/Slot Connections
- `metric_selected`: Emitted when metric card clicked
- `date_changed`: Emitted when date navigation occurs
- `refresh_requested`: Emitted to trigger data refresh

### State Management
- **Current Date**: Tracked in `_current_date`
- **Available Metrics**: Auto-detected from data in `_available_metrics`
- **Cache**: Statistics and hourly data cached per date
- **Selected Metric**: Tracked for detailed view updates

## Recent Bug Fixes (May 2025)

### Data Loading Issues
- **Problem**: Daily tab showing "No Data..." for all days
- **Root Cause**: Timezone conversion and date comparison issues
- **Fix**: 
  - Added timezone parameter to DailyMetricsCalculator
  - Fixed date type comparisons in `_filter_metric_data`
  - Proper date normalization using `normalize().dt.date`

### Main Window Integration
- **Problem**: Calculator creation without timezone
- **Fix**: Pass local timezone when creating calculators in main_window.py
- **Locations**: Lines 1431 (_refresh_daily_data), 1497 (_refresh_weekly_data), 1563 (_refresh_comparative_data)

### UI Refresh Issues
- **Problem**: Data not updating when switching to Daily tab
- **Fix**: Force refresh in `showEvent()` with cache clearing
- **Implementation**: Clear cache and reload data immediately when tab becomes visible (lines 1572-1586)
- **Additional Fix**: Added QMessageBox import to daily_dashboard_widget.py (line 20)

## Configuration

### View Filtering
- **All Metrics**: Shows all available metrics
- **Activity**: Steps, distance, floors, calories
- **Vitals**: Heart rate, resting HR, HRV
- **Body**: Weight, body fat percentage

### Goal Targets (Configurable)
- Steps: 10,000 daily
- Active Calories: 500 daily
- Floors Climbed: 10 daily

## Future Enhancements

### Planned Features
- Custom goal setting
- Weekly/monthly trend overlays
- Export functionality for daily data
- Medication and symptom tracking integration
- Social comparison features

### Performance Improvements
- Virtualized scrolling for large date ranges
- Background data pre-loading
- Progressive chart rendering

## Dependencies
- PyQt6 for UI framework
- pandas for data manipulation
- numpy for statistical calculations
- Custom chart components for visualizations

## Testing
- Comprehensive test suite in `test_daily_data_loading.py`
- Debug utilities in `debug_daily_data.py`
- Visual regression tests for UI components