# Calendar Heatmap Square Size Consistency Fix

## Problem
The calendar heatmap in the Monthly tab was displaying squares of different sizes across different months. This was because the cell size calculation was based on the number of weeks in each specific month, which varies from 4 to 6 weeks.

## Solution
Fixed the cell size calculation to always use the maximum possible number of weeks (6) when determining cell dimensions. This ensures that all months display with the same square size, regardless of how many weeks they actually contain.

### Changes Made

1. **In `_draw_month_grid` method** (calendar_heatmap.py:437-481):
   - Changed from calculating cell size based on `weeks_needed` to always using `MAX_WEEKS = 6`
   - Updated grid height allocation to always reserve space for 6 weeks
   - This ensures consistent cell sizing across all months

2. **In `_get_date_at_position_month_grid` method** (calendar_heatmap.py:843-881):
   - Applied the same MAX_WEEKS calculation for hit detection
   - Ensures mouse interaction works correctly with the fixed cell sizes

### Key Code Changes

```python
# Before: Cell size varied by month
cell_height_from_height = grid_height // weeks_needed

# After: Cell size is consistent
MAX_WEEKS = 6  # Maximum weeks any month can have
cell_height_from_height = grid_height // MAX_WEEKS
```

### Testing
Created `test_calendar_consistency.py` to verify:
- Navigate between different months
- Check that February (4-5 weeks) has same square size as months with 6 weeks
- Verify mouse interaction still works correctly

### Result
All calendar squares now maintain consistent size across all months, providing a better user experience when navigating between months in the Monthly dashboard.