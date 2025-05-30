# Erase All Data Feature Implementation

## Summary
Added a new menu option "File > Erase All Data..." that allows users to completely clear all imported health data, cached analytics, and filter configurations from the application.

## Changes Made

### 1. Menu Item Addition
**File**: `src/ui/main_window.py`
- Added "Erase All Data..." menu item to the File menu
- Positioned between Export options and Exit
- Includes status tip and tooltip for clarity

### 2. Confirmation Dialog
- Shows a warning dialog with detailed information about what will be deleted:
  - All imported health data from the database
  - All cached calculations and analytics
  - All filter presets and configurations
- Uses Yes/No buttons with No as default to prevent accidental deletion

### 3. Implementation Details
**Method**: `_on_erase_all_data()` in `MainWindow`

The method performs the following actions when user confirms:
1. Closes database connections
2. Deletes the SQLite database file (`health_data.db`)
3. Clears all caches using CacheManager
4. Removes the cache directory
5. Clears filter configurations
6. Resets the UI to empty state
7. Disables dashboard tabs (since no data is loaded)
8. Switches to Configuration tab
9. Shows success message

### 4. Supporting Method
**File**: `src/filter_config_manager.py`
- Added `clear_all_presets()` method to delete all filter configurations from the database

## User Experience
1. User selects "File > Erase All Data..."
2. Warning dialog appears explaining what will be deleted
3. User must click "Yes" to proceed (No is default)
4. Progress indicator shows while data is being erased
5. Success message confirms completion
6. UI returns to initial empty state, ready for new data import

## Safety Features
- Clear warning about permanent deletion
- No as default button to prevent accidental deletion
- Detailed list of what will be deleted
- Proper error handling and logging
- UI state properly reset after deletion

## Technical Notes
- Uses existing CacheManager for cache clearing
- Properly closes database connections before deletion
- Removes both database file and cache directory
- Updates UI to reflect empty state
- Maintains application stability after data erasure