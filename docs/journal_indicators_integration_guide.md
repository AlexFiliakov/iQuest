# Journal Entry Indicators Integration Guide

This guide explains how to integrate journal entry indicators into existing dashboard views in the Apple Health Monitor Dashboard.

## Overview

Journal entry indicators are visual elements that show when journal entries exist for specific time periods. They appear as small icons with optional badge counts on dashboard views, allowing users to quickly identify dates with associated notes.

## Core Components

### 1. JournalIndicator Widget (`src/ui/journal_indicator.py`)
- Visual indicator widget with type-specific icons
- Supports daily, weekly, and monthly entry types
- Shows badge count for multiple entries
- Provides interactive tooltips with entry preview
- Handles click events to open journal entries

### 2. JournalIndicatorService (`src/analytics/journal_indicator_service.py`)
- Manages indicator data with efficient caching
- Handles real-time updates when entries change
- Provides batch queries for date ranges
- Extracts preview text for tooltips

### 3. JournalIndicatorMixin (`src/ui/journal_indicator_mixin.py`)
- Easy integration for existing dashboard widgets
- Handles indicator positioning and lifecycle
- Manages click events and signals
- Provides consistent behavior across views

## Integration Steps

### Step 1: Add Mixin to Dashboard Widget

```python
from PyQt6.QtWidgets import QWidget
from src.ui.journal_indicator_mixin import JournalIndicatorMixin

class DailyDashboardWidget(QWidget, JournalIndicatorMixin):
    def __init__(self, data_access, parent=None):
        super().__init__(parent)
        
        # Initialize journal indicators
        self.init_journal_indicators(data_access)
        
        # Connect to journal editor signal
        self.journal_entry_requested.connect(self.open_journal_editor)
        
        # ... rest of initialization
```

### Step 2: Add Indicators to Date Elements

For individual date cells or cards:

```python
def create_date_cell(self, cell_date: date) -> QWidget:
    cell = QWidget()
    # ... configure cell
    
    # Add journal indicator if entries exist
    self.add_journal_indicator_to_widget(
        widget=cell,
        target_date=cell_date,
        entry_type='daily',  # or 'weekly', 'monthly'
        position='top-right'  # or 'top-left', 'bottom-right', etc.
    )
    
    return cell
```

### Step 3: Handle Journal Entry Requests

```python
def open_journal_editor(self, entry_date: date, entry_type: str):
    """Open journal editor for the specified date and type."""
    # Option 1: Emit signal to main window
    self.parent().open_journal_tab(entry_date, entry_type)
    
    # Option 2: Open dialog
    from src.ui.journal_editor_dialog import JournalEditorDialog
    dialog = JournalEditorDialog(
        self.data_access,
        entry_date=entry_date,
        entry_type=entry_type,
        parent=self
    )
    dialog.exec()
```

### Step 4: Connect to Journal Manager for Updates

```python
def set_journal_manager(self, journal_manager):
    """Connect to journal manager for real-time updates."""
    self.connect_to_journal_manager(journal_manager)
```

## Dashboard-Specific Integration

### Daily Dashboard

```python
class DailyDashboardWidget(QWidget, JournalIndicatorMixin):
    def __init__(self, data_access, parent=None):
        super().__init__(parent)
        self.init_journal_indicators(data_access)
        
    def update_metric_cards(self):
        """Update metric cards with indicators."""
        for card in self.metric_cards:
            # Add indicator to each metric card
            self.add_journal_indicator_to_widget(
                widget=card,
                target_date=self.current_date,
                entry_type='daily',
                position='top-right'
            )
```

### Weekly Dashboard

```python
class WeeklyDashboardWidget(QWidget, JournalIndicatorMixin):
    def create_week_view(self):
        """Create week view with indicators."""
        week_start = self.get_week_start(self.current_date)
        
        for day_offset in range(7):
            day_date = week_start + timedelta(days=day_offset)
            day_widget = self.create_day_widget(day_date)
            
            # Add daily indicator
            self.add_journal_indicator_to_widget(
                day_widget, day_date, 'daily', 'top-right'
            )
        
        # Add weekly indicator to week header
        self.add_journal_indicator_to_widget(
            self.week_header, week_start, 'weekly', 'top-left'
        )
```

### Monthly Dashboard / Calendar

```python
class MonthlyDashboardWidget(QWidget, JournalIndicatorMixin):
    def populate_calendar(self):
        """Populate calendar with indicators."""
        year = self.current_date.year
        month = self.current_date.month
        
        # Add indicators for all dates in month
        self.add_journal_indicators_to_calendar(
            self.calendar_widget, year, month
        )
        
        # Add monthly indicator to month header
        month_start = date(year, month, 1)
        self.add_journal_indicator_to_widget(
            self.month_header, month_start, 'monthly', 'top-right'
        )
```

## Enhanced Calendar Heatmap

For calendar heatmap views, use the enhanced version:

```python
from src.ui.charts.calendar_heatmap_enhanced import EnhancedCalendarHeatmap

# Create heatmap with journal support
heatmap = EnhancedCalendarHeatmap(
    monthly_calculator=self.monthly_calculator,
    data_access=self.data_access
)

# Connect to journal editor
heatmap.journal_entry_requested.connect(self.open_journal_editor)

# Connect to journal manager for updates
heatmap.connect_to_journal_manager(self.journal_manager)
```

## Customization Options

### Position Options
- `'top-right'` - Default, good for cards
- `'top-left'` - Alternative position
- `'bottom-right'` - For bottom-aligned layouts
- `'bottom-left'` - Less common
- `'center'` - For overlay effects

### Styling

The indicators use the warm color scheme by default:
- Default color: `#8B7355` (warm brown)
- Hover color: `#FF8C42` (warm orange)
- Badge color: `#FF8C42`

To customize, modify the color constants in `JournalIndicator`:

```python
# In your custom indicator subclass
class CustomJournalIndicator(JournalIndicator):
    ICON_COLOR = "#YourColor"
    ICON_HOVER_COLOR = "#YourHoverColor"
    BADGE_COLOR = "#YourBadgeColor"
```

## Performance Considerations

1. **Caching**: The service caches indicator data for 30 minutes by default
2. **Batch Queries**: Use date range queries for efficiency
3. **Lazy Loading**: Indicators are only created for visible elements
4. **Real-time Updates**: Only affected indicators are refreshed on changes

## Accessibility

The indicators include:
- ARIA labels describing entry count and type
- Keyboard navigation support (Tab/Enter/Space)
- High contrast colors meeting WCAG AA standards
- Tooltips with preview text

## Testing

Example test for indicator integration:

```python
def test_dashboard_shows_journal_indicators(qtbot, mock_data_access):
    """Test that dashboard displays journal indicators."""
    # Create dashboard
    dashboard = DailyDashboardWidget(mock_data_access)
    qtbot.addWidget(dashboard)
    
    # Set date with journal entry
    dashboard.set_date(date(2024, 1, 15))
    
    # Check indicator exists
    indicators = dashboard.findChildren(JournalIndicator)
    assert len(indicators) > 0
    
    # Test click
    qtbot.mouseClick(indicators[0], Qt.LeftButton)
    # Verify journal editor opened
```

## Troubleshooting

### Indicators Not Appearing
1. Check data_access is properly initialized
2. Verify journal entries exist for the date range
3. Ensure `add_journal_indicator_to_widget` is called after widget is sized

### Position Issues
1. Ensure parent widget has defined size before adding indicator
2. Use `update()` or `refresh_journal_indicators()` after layout changes
3. Check z-order with `indicator.raise_()` if needed

### Performance Issues
1. Use batch queries for multiple dates
2. Increase cache duration if appropriate
3. Limit preview text length for large entries

## Future Enhancements

1. **Animation**: Pulse animation for new entries
2. **Grouping**: Combine nearby indicators in dense views
3. **Filtering**: Show/hide indicators by entry type
4. **Quick Preview**: Hover to show full preview in popup
5. **Drag & Drop**: Drag indicators to move entries between dates