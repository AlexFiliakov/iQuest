---
task_id: G032
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G032: Implement Adaptive Display Logic

## Description
Detect available data ranges and dynamically hide/show time range options based on data availability. Create a data availability service that handles edge cases gracefully and provides intelligent UI adaptation.

## Goals
- [ ] Detect available data ranges across all metrics
- [ ] Hide/show time range options dynamically
- [ ] Create data availability service
- [ ] Handle edge cases gracefully
- [ ] Implement intelligent UI adaptation
- [ ] Provide feedback for unavailable ranges
- [ ] Support partial data scenarios

## Acceptance Criteria
- [ ] Data ranges detected accurately for all metrics
- [ ] UI options reflect actual data availability
- [ ] Unavailable options are disabled, not hidden
- [ ] Clear messaging for why options are unavailable
- [ ] Service updates when new data is imported
- [ ] Edge cases handled without crashes
- [ ] Partial data scenarios work correctly
- [ ] Unit tests cover adaptation logic

## Technical Details

### Data Availability Detection
- **Range Scanning**:
  - Min/max dates per metric
  - Data density analysis
  - Gap detection
  - Quality assessment

- **Availability Levels**:
  - Full: Complete data for range
  - Partial: Some gaps but usable
  - Sparse: Limited data points
  - None: No data available

- **Update Triggers**:
  - New data import
  - Data deletion
  - Filter changes
  - Metric selection

### UI Adaptation Rules
- **Time Range Options**:
  - Today: Requires current day data
  - Week: Needs 3+ days in last 7
  - Month: Needs 10+ days in last 30
  - Year: Needs 3+ months of data

- **Display States**:
  - Enabled: Full data available
  - Warning: Partial data (tooltip explains)
  - Disabled: Insufficient data
  - Hidden: Never show (configurable)

- **Smart Defaults**:
  - Select best available range
  - Prefer recent complete data
  - Fall back gracefully
  - Remember user preferences

### Edge Cases
- **No Data**: Show onboarding/import prompt
- **Single Day**: Show day view only
- **Gaps**: Indicate missing periods
- **Future Dates**: Handle gracefully
- **Timezone Issues**: Consistent handling

## Dependencies
- Database models from S02
- UI components from S02
- Data loader from S01

## Implementation Notes
```python
# Example structure
class DataAvailabilityService:
    def __init__(self, database: HealthDatabase):
        self.db = database
        self.availability_cache = {}
        self.update_callbacks = []
        
    def scan_availability(self) -> Dict[str, DataRange]:
        """Scan all metrics for data availability"""
        availability = {}
        
        for metric in self.db.get_all_metrics():
            availability[metric] = DataRange(
                start_date=self.db.get_min_date(metric),
                end_date=self.db.get_max_date(metric),
                total_points=self.db.get_data_count(metric),
                density=self.calculate_density(metric),
                gaps=self.detect_gaps(metric)
            )
            
        self.availability_cache = availability
        self.notify_updates()
        return availability
        
    def get_available_ranges(self, metric: str) -> List[TimeRange]:
        """Get list of available time ranges for metric"""
        if metric not in self.availability_cache:
            self.scan_availability()
            
        data_range = self.availability_cache[metric]
        available = []
        
        # Check each potential range
        if self.has_today_data(data_range):
            available.append(TimeRange.TODAY)
            
        if self.has_week_data(data_range):
            available.append(TimeRange.WEEK)
            
        if self.has_month_data(data_range):
            available.append(TimeRange.MONTH)
            
        if self.has_year_data(data_range):
            available.append(TimeRange.YEAR)
            
        return available
        
    def suggest_default_range(self, metric: str) -> TimeRange:
        """Suggest best default time range"""
        available = self.get_available_ranges(metric)
        
        # Prefer week view if available
        if TimeRange.WEEK in available:
            return TimeRange.WEEK
            
        # Fall back to longest available
        return available[-1] if available else None
```

### UI Integration
```python
class AdaptiveTimeRangeSelector(QWidget):
    def __init__(self, availability_service: DataAvailabilityService):
        super().__init__()
        self.availability = availability_service
        self.availability.register_callback(self.update_options)
        
    def update_options(self):
        """Update UI based on data availability"""
        current_metric = self.get_selected_metric()
        available_ranges = self.availability.get_available_ranges(current_metric)
        
        for button in self.range_buttons:
            range_type = button.property('range_type')
            
            if range_type in available_ranges:
                button.setEnabled(True)
                button.setToolTip("")
            else:
                button.setEnabled(False)
                reason = self.get_unavailable_reason(range_type, current_metric)
                button.setToolTip(f"Unavailable: {reason}")
```

## Testing Requirements
- Unit tests for availability detection
- Edge case testing (no data, single point)
- UI adaptation tests
- Performance tests with large datasets
- Cache invalidation tests
- Integration tests with data import

## Notes
- Consider caching availability data
- Provide clear user feedback
- Allow manual refresh of availability
- Document adaptation rules clearly
- Plan for future custom ranges