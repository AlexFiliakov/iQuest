# Monthly Dashboard Historical Data Fix

## Issue
The Monthly dashboard was displaying randomly generated sample data instead of actual historical health data from the database.

## Root Cause
1. The `MonthlyDashboardWidget` was created without any data source/calculator
2. The UI was calling `get_daily_aggregate()` which didn't exist in `MonthlyMetricsCalculator`
3. The data flow from database → calculators → UI was broken
4. When the method call failed, the code fell back to `_generate_sample_data()` which created random values

## Solution
Implemented proper data flow and method to retrieve historical data:

### 1. Added `get_daily_aggregate` Method
In `monthly_metrics_calculator.py`, added:
```python
def get_daily_aggregate(self, metric: str, date: date) -> Optional[float]:
    """Get daily aggregate value for a specific metric and date."""
    try:
        # Use the daily calculator to get the value
        daily_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', date, date
        )
        
        if daily_data.empty:
            return None
            
        # Return the first (and only) value
        return float(daily_data.iloc[0])
        
    except Exception as e:
        logger.warning(f"Error getting daily aggregate for {metric} on {date}: {e}")
        return None
```

### 2. Fixed Data Flow in main_window.py
Updated `_refresh_monthly_data()` to properly create calculators:
```python
# Create daily calculator first
daily_calculator = DailyMetricsCalculator(data)

# Create monthly calculator with the daily calculator
monthly_calculator = MonthlyMetricsCalculator(daily_calculator)

# Set the calculator in the monthly dashboard
self.monthly_dashboard.set_data_source(monthly_calculator)
```

### 3. Data Flow Architecture
The proper data flow is now:
1. Configuration tab loads data from SQLite database
2. When Monthly tab is selected, `_refresh_monthly_data()` is called
3. Creates `DailyMetricsCalculator` with the filtered data
4. Creates `MonthlyMetricsCalculator` with the daily calculator
5. Sets the monthly calculator as the data source
6. Monthly dashboard calls `get_daily_aggregate()` for each day
7. Real historical data is displayed in the calendar heatmap

## Verification
To verify the fix works:
1. Import health data (CSV or XML)
2. Navigate to the Monthly tab
3. Observe that the calendar heatmap shows actual historical values
4. Values should match your imported data, not random numbers
5. Different metrics (steps, heart rate, etc.) should show appropriate ranges

## Files Modified
- `/src/analytics/monthly_metrics_calculator.py` - Added `get_daily_aggregate` method
- `/src/ui/main_window.py` - Fixed `_refresh_monthly_data` to create proper calculator chain
- `/src/ui/monthly_dashboard_widget.py` - Already had future date filtering from previous fix

## Notes
- The fix maintains compatibility with existing code
- Falls back gracefully if data is unavailable
- Properly handles timezone conversions through the daily calculator
- The monthly calculator now correctly delegates to the daily calculator for data access