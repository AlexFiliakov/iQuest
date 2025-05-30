# Dynamic Metrics Implementation for Monthly Dashboard

## Summary
Updated the Monthly Dashboard widget to dynamically load and display all available health metrics from the database instead of showing only 4 hardcoded metrics.

## Changes Made

### 1. Database Integration
- Added `HealthDatabase` import to query available metric types
- Created `_load_available_metrics()` method to fetch all metric types from the database
- Filters metrics to only include those with display name mappings

### 2. Comprehensive Metric Mappings
- Created `_init_metric_mappings()` method with:
  - Display name mappings for 40+ health metrics
  - Unit mappings for proper formatting
  - Support for all major Apple Health metric categories:
    - Activity & Fitness (Steps, Distance, Calories, etc.)
    - Cardiovascular (Heart Rate, Blood Pressure, HRV, etc.)
    - Body Measurements (Weight, BMI, Body Fat %, etc.)
    - Mobility & Balance (Walking Speed, Asymmetry, etc.)
    - Respiratory (Respiratory Rate, VO2 Max)
    - Sleep Analysis
    - Nutrition (Calories, Protein, Vitamins, Water, etc.)
    - Environmental (Audio Exposure)
    - Mindfulness

### 3. Dynamic Combo Box Population
- Updated metric combo box to load metrics from database
- Uses display names for user-friendly selection
- Stores metric keys as item data for proper handling

### 4. Improved Data Handling
- Updated `_on_metric_changed()` to use combo box item data
- Modified `_load_month_data()` to handle all metric types with proper HK prefixes
- Added `_convert_value_for_display()` for unit conversions:
  - Distance: meters to kilometers
  - Sleep: seconds to hours
  - Height: meters to centimeters
  - Speed: m/s to km/h
  - Time: seconds to minutes

### 5. Enhanced Statistics Display
- Updated `_update_summary_stats()` with intelligent formatting:
  - Integer values for counts (steps, flights)
  - Decimal values for measurements
  - Proper unit display for all metrics
  - Special handling for percentages and BMI

### 6. Sample Data Generation
- Extended `_generate_sample_data()` with realistic ranges for all metrics
- Supports both integer and float value generation

## Benefits
- Users can now view monthly data for ALL their imported health metrics
- Automatic discovery of available metrics from database
- Consistent and intuitive display names
- Proper unit conversions and formatting
- Extensible design for adding new metrics

## Technical Details
- The system removes "HKQuantityTypeIdentifier" and "HKCategoryTypeIdentifier" prefixes when displaying metrics
- Metrics are sorted alphabetically by display name for better UX
- Unknown metrics are logged for future addition
- Fallback to default metrics if database query fails