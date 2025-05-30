# Daily Tab Refresh Fix

## Issue
The Daily tab was not refreshing properly when switching to it from other tabs. Visuals from prior tabs would persist without refreshing, and Daily information was not displaying correctly.

## Root Cause
1. Tab switching animations were interfering with the refresh process
2. The Daily dashboard widget was not properly clearing its content before redrawing
3. The refresh was happening too quickly before the tab was fully visible

## Solution Applied

### 1. Main Window Changes (`src/ui/main_window.py`)

#### Disabled animations for Daily tab
```python
# In _on_tab_changed method
# Disable animations for Daily tab temporarily to fix refresh issue
if index == 1:  # Daily tab index
    should_animate = False
```

#### Enhanced tab change completion
```python
# In _complete_tab_change method
# Force the widget to become visible and process pending events
widget = self.tab_widget.widget(index)
if widget:
    widget.show()
    widget.raise_()
    QApplication.processEvents()

# Add a small delay to ensure tab is fully visible
if index == 1:  # Daily tab
    QTimer.singleShot(50, self._refresh_daily_data)
```

### 2. Daily Dashboard Widget Changes (`src/ui/daily_dashboard_widget.py`)

#### Clear existing content in set_daily_calculator
```python
# Clear any existing metric cards before creating new ones
self._metric_cards.clear()
self._available_metrics = []

# Hide any existing no data message
self._hide_no_data_message()
```

#### Always recreate metric cards
```python
# In _load_daily_data method
# Always recreate metric cards to ensure fresh display
logger.info("Creating metric cards")
self._create_metric_cards()
self._populate_detail_selector()
```

#### Enhanced refresh process
```python
def _refresh_data(self):
    """Refresh all data displays."""
    logger.info("Refreshing daily dashboard data")
    # Clear the display first
    self.update()
    QApplication.processEvents()
    # Then reload data
    self._load_daily_data()
    self.refresh_requested.emit()
```

#### Clear content on show event
```python
def showEvent(self, event):
    """Handle widget show event to ensure UI is refreshed."""
    super().showEvent(event)
    # Clear any leftover content from other tabs
    self._hide_no_data_message()
    # Force a refresh when the widget is shown
    if self.daily_calculator:
        self._load_daily_data()
        self.update()
        QApplication.processEvents()
        # Schedule another update after a short delay to ensure complete rendering
        QTimer.singleShot(100, self._delayed_refresh)
    else:
        self._show_no_data_message()
```

## Testing
Run the test script to verify the fix:
```bash
python test_daily_tab_refresh_fix.py
```

## Expected Behavior
1. When switching to the Daily tab, it should:
   - Clear any existing content
   - Show a brief loading state
   - Redraw all metric cards, charts, and timelines
   - Display the correct data for the current date

2. No visuals from other tabs should persist
3. The Daily dashboard should be fully functional with all metrics displayed correctly

## Additional Notes
- The fix temporarily disables animations for the Daily tab to ensure proper refresh
- A small delay (50ms) is added to ensure the tab is fully visible before refreshing
- The widget is forced to update and process events to ensure complete rendering
- A delayed refresh (100ms) is scheduled to handle any remaining rendering issues