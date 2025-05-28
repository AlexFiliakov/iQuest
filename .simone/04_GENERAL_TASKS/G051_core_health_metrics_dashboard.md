---
task_id: G051
status: open
created: 2025-05-28
complexity: high
sprint_ref: S04_M01_Core_Analytics
---

# Task G051: Core Health Metrics Dashboard

## Description
Create comprehensive dashboard for core health metrics (activity, heart rate, sleep, body measurements) with interactive visualizations, trend analysis, and comparative views. This serves as the foundation for the main analytics interface.

## Goals
- [ ] Design unified dashboard layout for core health metrics
- [ ] Implement activity metrics section (steps, distance, calories)
- [ ] Create heart rate analysis panel with zones and trends
- [ ] Build sleep analytics with efficiency and pattern analysis
- [ ] Add body measurements tracking with weight, BMI trends
- [ ] Integrate interactive time range selection
- [ ] Implement metric comparison and correlation views

## Acceptance Criteria
- [ ] Dashboard displays all 4 core health metric categories
- [ ] Each metric section shows current value, trend, and historical data
- [ ] Interactive time range selector (1D, 7D, 30D, 90D, 1Y, All)
- [ ] Responsive layout adapts to different metric combinations
- [ ] Real-time updates when filters change
- [ ] Consistent warm color scheme throughout
- [ ] Loading states and empty data handling
- [ ] Export functionality for dashboard views

## Technical Details

### Dashboard Structure
- **Activity Panel**: Steps, distance, active energy, exercise minutes
- **Heart Panel**: Resting HR, active HR, HR zones, variability
- **Sleep Panel**: Sleep duration, efficiency, deep/REM phases
- **Body Panel**: Weight, BMI, body fat percentage trends

### Interactive Features
- Time range selector with preset and custom ranges
- Metric correlation matrix with hover details
- Drill-down capability from summary to detailed view
- Side-by-side metric comparison
- Goal tracking indicators

### Performance Requirements
- Dashboard renders in < 500ms for 1 year of data
- Smooth animations and transitions
- Efficient data aggregation and caching
- Memory usage optimization for large datasets

## Dependencies
- Daily/Weekly/Monthly calculators (G019-G021)
- Chart components (G036, G037)
- Data filtering engine (G016)
- Summary card components (G038)

## Implementation Notes
```python
class CoreHealthDashboard:
    def __init__(self, data_manager, ui_parent):
        self.data_manager = data_manager
        self.ui_parent = ui_parent
        self.metric_panels = {}
        
    def create_activity_panel(self) -> QWidget:
        """Activity metrics: steps, distance, calories"""
        pass
        
    def create_heart_panel(self) -> QWidget:
        """Heart rate analysis and zones"""
        pass
        
    def create_sleep_panel(self) -> QWidget:
        """Sleep duration, efficiency, phases"""
        pass
        
    def create_body_panel(self) -> QWidget:
        """Weight, BMI, body composition trends"""
        pass
        
    def update_time_range(self, start_date, end_date):
        """Update all panels with new time range"""
        pass
```

## Notes
- Use consistent metric icons and colors across panels
- Implement progressive disclosure for detailed metrics
- Consider metric availability and show appropriate fallbacks
- Follow Apple Health design patterns for familiarity