# Monthly Tab Future Data Fix

## Issue
The Monthly tab was displaying steps data for future dates (e.g., showing data for May 30-31, 2025 when the current date is May 29, 2025).

## Root Cause
The `_load_month_data()` method in both `monthly_dashboard_widget.py` and `monthly_dashboard_widget_modern.py` was iterating through all days in the current month without checking if those dates were in the future.

## Solution
Added date validation to skip future dates when loading monthly data:

1. **In `monthly_dashboard_widget.py`**:
   - Added `today = date.today()` to get current date
   - Added check `if current_date > today: continue` to skip future dates
   - Applied same fix to `_generate_sample_data()` method

2. **In `monthly_dashboard_widget_modern.py`**:
   - Applied identical fixes to both `_load_month_data()` and `_generate_sample_data()` methods

## Code Changes

### Before:
```python
for day in range(1, days_in_month + 1):
    current_date = date(self._current_year, self._current_month, day)
    # Get daily aggregate value...
```

### After:
```python
today = date.today()

for day in range(1, days_in_month + 1):
    current_date = date(self._current_year, self._current_month, day)
    
    # Skip future dates
    if current_date > today:
        continue
    
    # Get daily aggregate value...
```

## Testing
To verify the fix:
1. Navigate to the Monthly tab
2. Check that the calendar heatmap only shows data up to today's date
3. Verify that future dates (May 30-31) no longer show step counts
4. Test with different metrics (heart rate, sleep, distance) to ensure consistency

## Files Modified
- `/src/ui/monthly_dashboard_widget.py`
- `/src/ui/monthly_dashboard_widget_modern.py`