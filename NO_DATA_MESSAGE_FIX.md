# No Data Message AttributeError Fix

## Issue
The Daily dashboard widget was throwing an `AttributeError: 'DailyDashboardWidget' object has no attribute 'no_data_message'` when trying to display a "no data" message for a specific date.

## Root Cause
The `_show_no_data_for_date` method was trying to access `self.no_data_message` and `self.no_data_date` attributes outside of the conditional block that creates them. This caused an error when the overlay had been created by `_show_no_data_message` (which doesn't create these specific attributes) or when the attributes weren't properly initialized.

## Solution Applied

### 1. Fixed attribute checking in `_show_no_data_for_date`
```python
# Changed from:
if not hasattr(self, 'no_data_overlay'):

# To:
if not hasattr(self, 'no_data_overlay') or not hasattr(self, 'no_data_message'):
```

This ensures that both the overlay AND the required label attributes exist before trying to use them.

### 2. Improved error message handling
```python
def _show_error_message(self, error: str):
    """Show error message overlay."""
    logger.error(f"Showing error: {error}")
    # For now, just log the error and show a simple message box
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.warning(self, "Error Loading Data", f"Failed to load daily data:\n{error}")
```

Added a proper error dialog instead of just logging the error.

## Testing
Run the test script to verify the fix:
```bash
python test_no_data_message_fix.py
```

This script tests:
1. Loading with no calculator (shows "No Data Loaded")
2. Showing no data for a specific date
3. Hiding the no data message
4. Showing error messages

## Expected Behavior
- No more AttributeError when displaying "no data" messages
- Proper overlay creation and display for both scenarios:
  - No data loaded at all
  - No data for a specific date
- Error messages are shown in a dialog box
- The overlay can be hidden and shown without errors

## Technical Details
The fix ensures that the overlay widget and its child labels are created together. The `_show_no_data_for_date` method now checks for both the overlay widget AND the specific label attributes before trying to use them. This prevents the AttributeError that occurred when the overlay existed but the labels didn't.