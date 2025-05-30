# Sample Data Generation in Apple Health Monitor UI

This document catalogs all parts of the application UI that generate sample, mock, or test data instead of relying on user's actual health data.

## UI Components with Sample Data Generation

### 1. Demo and Example Components

#### `src/ui/month_over_month_demo.py`
- **Purpose**: Demonstration script for Month-over-Month Trends Analysis
- **Sample Data Generated**:
  - Mock monthly health metrics with realistic trends
  - Includes "Heart Rate (bpm)", "Step Count", "Sleep Duration", etc.
  - Uses `MockMonthlyMetricsCalculator.get_monthly_metrics()` 
  - Generates data with trend, seasonality, and noise patterns

#### `src/ui/charts/visualization_example.py`
- **Purpose**: Example implementation using visualization architecture
- **Sample Data Generated**:
  - 90 days of realistic heart rate data via `generate_sample_data()`
  - Daily variation, noise, and trends
  - Simulates real-time data updates with `update_data()`

#### `src/ui/accessibility/example_accessible_line_chart.py`
- **Purpose**: Accessibility demonstration for line charts
- **Sample Data Generated**:
  - Hardcoded weekly heart rate measurements
  - Monday-Sunday data: (72, 75, 71, 78, 74, 69, 70)

#### `src/examples/line_chart_demo.py`
- **Purpose**: Demo of reusable line chart component with WSJ styling
- **Sample Data Generated**:
  - Full year of health data (365 days) via `generate_sample_data()`
  - Heart rate: Base 70 bpm with seasonal variation and noise
  - Steps: Base 8000 with weekly patterns and randomness
  - Sleep: Base 7.5 hours with monthly cycles
  - Random series generation for multi-series demos

### 2. Fallback Data Generation

#### `src/ui/coverage_integration.py`
- **Purpose**: Coverage integration widget with demo functionality
- **Sample Data Generated**:
  - `update_with_sample_data()` - configurable coverage data
  - `create_sample_coverage_data()` - sample coverage metrics
  - Used for testing and demo scenarios

### 3. Chart Factory Components

#### `src/ui/charts/pyqtgraph_chart_factory.py`
- **Purpose**: Interactive chart factory
- **Sample Data Generated**:
  - Demo widgets when PyQtGraph library is unavailable
  - Fallback sample data for chart rendering

#### `src/ui/charts/wsj_health_visualization_suite.py`
- **Purpose**: WSJ-inspired visualization suite
- **Sample Data Generated**:
  - Performance testing data via `generate_sample_data()`
  - Used for chart rendering optimization and demos

### 4. User Data Components (No Sample Data)

These components explicitly avoid sample data:

#### `src/ui/trophy_case_widget.py`
- **Data Policy**: Never uses sample data
- **Implementation**: 
  - Line 508-511: Explicitly checks for empty user data
  - Line 517-521: No sample achievements generated
  - Always works from user's actual data only

#### `src/ui/comparative_visualization.py`
- **Data Policy**: Relies on user data through data access layer
- **No Sample Generation**: Uses actual health metrics only

#### `src/ui/configuration_tab.py`
- **Data Policy**: Configuration and import interface only
- **No Sample Generation**: Works with user's XML imports

## Sample Data Patterns

### Common Generation Patterns
1. **Realistic Ranges**: All sample data uses medically realistic ranges
2. **Temporal Patterns**: Daily, weekly, monthly, and seasonal variations
3. **Noise Addition**: Random variation to simulate real-world data
4. **Weekend Effects**: Different patterns for weekends vs weekdays
5. **Trending**: Long-term trends overlaid on short-term variation

### Fallback Scenarios
- **No User Data**: When database is empty
- **Demo Mode**: For screenshots and demonstrations  
- **Library Unavailable**: When optional chart libraries missing
- **Testing**: For UI component testing

## Recommendations

### Current State
- Most production UI components avoid sample data
- Sample data is primarily in demo/example files
- Fallback data is clearly marked and conditional

### Best Practices
1. **Clearly Label**: All sample data functions should be clearly named
2. **Conditional Use**: Only generate when no user data exists
3. **Realistic Data**: Maintain medical/health data realism
4. **User Indication**: Clearly show when sample data is displayed
5. **Easy Removal**: Sample data should be easily disabled for production

### Areas to Monitor
- Ensure demo files don't accidentally get used in production
- Monitor fallback conditions to prevent overuse of sample data
- Verify user data preference is always prioritized