# Apple Health Monitor - Metric Discovery Specification

## Overview
This document outlines the methods responsible for discovering and caching available health metrics across all UI tabs in the Apple Health Monitor Dashboard.

## Core Metric Discovery Methods

### 1. Database Layer

#### `HealthDatabase.get_available_types()`
- **Location**: `/src/health_database.py:33`
- **Purpose**: Primary method for discovering all available metric types in the database
- **Query**: `SELECT DISTINCT type FROM health_records WHERE type IS NOT NULL ORDER BY type`
- **Returns**: List of unique metric type strings sorted alphabetically
- **Used By**: All UI tabs that need to populate metric selection dropdowns

#### `HealthDatabase.get_available_sources()`
- **Location**: `/src/health_database.py:160`
- **Purpose**: Discovers all data sources (iPhone, Apple Watch, etc.)
- **Query**: `SELECT DISTINCT source_name FROM health_records WHERE source_name IS NOT NULL ORDER BY source_name`
- **Returns**: List of unique source names

#### `HealthDatabase.get_types_for_source(source_name)`
- **Location**: `/src/health_database.py:175`
- **Purpose**: Gets metrics available for a specific data source
- **Returns**: List of metric types filtered by source

### 2. Data Filter Engine

#### `DataFilterEngine.get_distinct_types()`
- **Location**: `/src/data_filter_engine.py:194`
- **Purpose**: Alternative method for discovering metric types
- **Query**: Same as `HealthDatabase.get_available_types()`
- **Usage**: Primarily used in configuration/import tabs

#### `DataFilterEngine.get_distinct_sources()`
- **Location**: `/src/data_filter_engine.py:175`
- **Purpose**: Discovers available data sources
- **Usage**: Used for source-based filtering

### 3. Data Availability Service

#### `DataAvailabilityService.scan_availability()`
- **Location**: `/src/data_availability_service.py:165`
- **Purpose**: Comprehensive analysis of metric availability
- **Features**:
  - Calls `db.get_available_types()` internally
  - Analyzes data coverage, gaps, and density
  - Provides 5-minute caching
  - Supports callback notifications for UI updates
- **Returns**: Dictionary with availability metrics for each type

### 4. UI Component Methods by Tab

#### Daily Dashboard Tab
- **Component**: `DailyDashboardWidget` (if exists)
- **Expected Method**: Should have a method similar to `_load_available_metrics()`
- **Note**: Need to verify implementation

#### Weekly Dashboard Tab  
- **Component**: `WeeklyDashboardWidget`
- **Expected Method**: Should have a method similar to `_load_available_metrics()`
- **Note**: Need to verify implementation

#### Monthly Dashboard Tab
- **Component**: `MonthlyDashboardWidget`
- **Method**: `_load_available_metrics()`
- **Location**: `/src/ui/monthly_dashboard_widget.py:224`
- **Implementation**:
  ```python
  def _load_available_metrics(self):
      """Load available health metrics from database."""
      try:
          # Get available types from database
          available_types = self.health_db.get_available_types()
          
          # Get available sources
          available_sources = self.health_db.get_available_sources()
          
          # Process and match against display names
          # Populate combo boxes
      except Exception as e:
          logger.error(f"Error loading metrics: {e}")
  ```

#### Records/Personal Records Tab
- **Component**: Likely uses `PersonalRecordsTracker`
- **Location**: `/src/analytics/personal_records_tracker.py`
- **Expected Method**: Should query available metrics for record tracking
- **Note**: Need to verify UI implementation

#### Configuration Tab
- **Component**: `ConfigurationTab`
- **Location**: `/src/ui/configuration_tab.py`
- **Methods**: Uses `DataFilterEngine` methods for import/filter configuration

## Metric Processing Pipeline

### 1. Raw Type Discovery
- Database query returns raw type strings (e.g., "HKQuantityTypeIdentifierStepCount")

### 2. Type Processing
- Strip HK prefixes ("HKQuantityTypeIdentifier", "HKCategoryTypeIdentifier")
- Match against display name dictionaries
- Handle unknown types gracefully

### 3. Display Name Mapping
Common mappings include:
```python
METRIC_DISPLAY_NAMES = {
    "StepCount": "Steps",
    "HeartRate": "Heart Rate", 
    "ActiveEnergyBurned": "Active Calories",
    "DistanceWalkingRunning": "Walking + Running Distance",
    # ... etc
}
```

### 4. UI Population
- Processed metrics are added to combo boxes/dropdowns
- Metrics can be filtered by source if needed
- Selection triggers data loading for visualizations

## Caching Strategy

### Database Level
- No explicit caching at database query level
- Relies on SQLite's internal query caching

### Service Level
- `DataAvailabilityService` implements 5-minute cache
- Cache key: "availability_data"
- Invalidated on data imports

### UI Level
- Components may cache metric lists after initial load
- Refresh typically triggered by:
  - Tab switches
  - Data imports
  - Manual refresh actions

## Metric Identifier Mapping

### Standard Apple Health Identifiers
The system recognizes these Apple Health metric identifiers:

| Apple Health Identifier | Internal Name | Display Name |
|------------------------|---------------|--------------|
| HKQuantityTypeIdentifierStepCount | steps | Steps |
| HKQuantityTypeIdentifierDistanceWalkingRunning | distance | Distance (km) |
| HKQuantityTypeIdentifierFlightsClimbed | flights_climbed | Floors Climbed |
| HKQuantityTypeIdentifierActiveEnergyBurned | active_calories | Active Calories |
| HKQuantityTypeIdentifierHeartRate | heart_rate | Heart Rate |
| HKQuantityTypeIdentifierRestingHeartRate | resting_heart_rate | Resting HR |
| HKQuantityTypeIdentifierHeartRateVariabilitySDNN | hrv | HRV |
| HKQuantityTypeIdentifierBodyMass | weight | Weight |
| HKQuantityTypeIdentifierBodyFatPercentage | body_fat | Body Fat |

## Completeness Review

### ✅ Confirmed Implementation
- Monthly Dashboard Tab: Full implementation with `_load_available_metrics()`
- Configuration Tab: Uses `DataFilterEngine` methods
- Database Layer: Complete set of discovery methods
- Data Availability Service: Comprehensive caching and analysis

### ✅ Additional Confirmed Implementations

#### Daily Dashboard Tab
- **Component**: `DailyDashboardWidget`
- **Method**: `_detect_available_metrics()`
- **Location**: `/src/ui/daily_dashboard_widget.py`
- **Implementation**:
  - Reads unique types from `self.daily_calculator.data['type'].unique()`
  - Maps Apple Health identifiers to internal metric names
  - Populates `self._available_metrics` with found metrics
  - Sorts by priority defined in METRIC_CONFIG

#### Weekly Dashboard Tab
- **Component**: `WeeklyDashboardWidget`
- **Method**: `_detect_available_metrics()`
- **Location**: `/src/ui/weekly_dashboard_widget.py`
- **Implementation**:
  - Gets unique types from daily calculator data
  - Maps to display names and internal keys
  - Populates `self.metric_selector` QComboBox with discovered metrics

#### Trophy Case/Records Tab
- **Component**: `TrophyCaseWidget`
- **Method**: `update_metric_filter()`
- **Location**: `/src/ui/trophy_case_widget.py`
- **Implementation**:
  - Extracts unique metrics from all personal records
  - Populates metric filter dropdown with sorted metric list
  - Includes "All Metrics" option as default

### 📋 Recommendations
1. Standardize metric loading across all tabs using a common base method
2. Consider implementing a central MetricDiscoveryService to avoid duplication
3. Add metric metadata (units, data type, etc.) to improve UI display
4. Implement metric categorization for better organization in dropdowns

## Related Components

### Cache Manager
- **Location**: `/src/analytics/cache_manager.py`
- **Role**: General caching infrastructure used by various components

### Statistics Calculator
- **Location**: `/src/statistics_calculator.py`
- **Role**: Calculates statistics for discovered metrics

### Data Access Layer
- **Location**: `/src/data_access.py`
- **Role**: DAO pattern implementation for data persistence

## Data Flow Summary

### Import Phase
1. XML/CSV data imported via Configuration Tab
2. Data loaded into pandas DataFrame with 'type' column
3. Data stored in SQLite database (health_records table)

### Discovery Phase  
1. **Database Approach** (Monthly Tab):
   - `HealthDatabase.get_available_types()` queries distinct types
   - Results processed to remove HK prefixes
   - Matched against display name dictionary

2. **DataFrame Approach** (Daily/Weekly Tabs):
   - `data['type'].unique()` gets unique metric types
   - Mapped using hardcoded dictionaries
   - Filtered based on metric priorities

3. **Records Approach** (Trophy Case):
   - Iterates through personal records
   - Extracts metric names from record objects
   - Populates filter with actual metric values

### Population Phase
- Combo boxes/dropdowns populated with discovered metrics
- Display names shown to users
- Original identifiers stored as item data for queries

## Key Differences Between Tabs

1. **Monthly Dashboard**: Uses database queries for metric discovery
2. **Daily/Weekly Dashboards**: Use pandas DataFrame operations
3. **Trophy Case**: Uses already-processed personal records data
4. **Configuration Tab**: Uses DataFilterEngine for import filtering

## Next Steps

1. ✅ Daily and Weekly tab implementations verified
2. ✅ Records tab metric selection UI confirmed
3. Consider refactoring to centralize metric discovery
4. Add unit tests for metric discovery methods
5. ✅ Metric type transformations and display name mappings documented