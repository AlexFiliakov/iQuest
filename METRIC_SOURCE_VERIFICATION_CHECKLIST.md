# Metric and Source Selection Verification Checklist

This checklist ensures that all UI elements across tabs properly reflect the selected metric type and source device when filters are applied.

## Current Implementation Status

Based on code analysis:
- **Database Schema**: `health_records` table has `sourceName` field for source tracking
- **Filter System**: Configuration tab has device dropdown (`source_names`) and metric dropdown (`health_types`)
- **Signal Propagation**: `filters_applied` signal emits dict with 'devices' and 'metrics' arrays

## Verification Checklist by Tab

### 1. **Configuration Tab** ✓
- [x] Multi-select combo boxes for metrics and devices
- [x] Filter criteria includes `source_names` and `health_types`
- [x] `filters_applied` signal emits complete filter state
- [x] Statistics widget updates with filtered data

**Code Locations**:
- `src/ui/configuration_tab.py`: Lines 1551-1553 (filter collection)
- `src/ui/configuration_tab.py`: Lines 1606-1611 (FilterCriteria creation)

---

### 2. **Monthly Tab**

**Calendar Heatmap**:
- [ ] Verify heatmap updates when metric is changed
- [ ] Check that data aggregation respects source filter
- [ ] Ensure color scale adjusts to selected metric's range
- [ ] Tooltip shows correct metric name and source

**Summary Statistics**:
- [ ] Monthly average/total reflects filtered metric/source
- [ ] Min/max values update correctly
- [ ] Record count shows filtered data only

**Month Navigation**:
- [ ] Selection persists when navigating months
- [ ] Empty state message indicates selected metric/source

**Code Locations**:
- `src/ui/monthly_dashboard_widget.py`: Check `metric_changed` signal
- `src/ui/charts/calendar_heatmap.py`: Verify `update_data()` method

**Verification Steps**:
1. Select specific metric (e.g., "Steps") and source (e.g., "iPhone")
2. Navigate between months
3. Verify data shown matches selection

---

### 3. **Weekly Tab**

**Summary Cards**:
- [ ] Week total/average uses filtered data
- [ ] Daily average calculation respects filters
- [ ] Best day shows highest value for selected metric/source

**Week-over-Week Comparison**:
- [ ] Percentage change calculated from filtered data
- [ ] Previous week data also filtered
- [ ] Trend arrow reflects filtered comparison

**Day-of-Week Patterns**:
- [ ] Bar chart shows only selected metric/source data
- [ ] Pattern analysis uses filtered dataset

**Trend Chart**:
- [ ] Line chart displays selected metric over time
- [ ] Y-axis label shows metric name and unit
- [ ] Legend indicates source device if filtered

**Code Locations**:
- `src/ui/weekly_dashboard_widget.py`: Check `update_metric()` method
- `src/ui/week_over_week_widget.py`: Verify comparison logic

**Verification Steps**:
1. Select "Heart Rate" from "Apple Watch"
2. Check all visualizations show Watch data only
3. Change to "All Sources" and verify update

---

### 4. **Daily Tab**

**Metric Cards**:
- [ ] Primary metric card shows selected metric
- [ ] Value aggregation respects source filter
- [ ] Secondary cards update based on selection

**Detail Chart**:
- [ ] Hourly/minute data filtered by source
- [ ] Chart title includes metric name
- [ ] Y-axis shows appropriate unit

**Activity Timeline**:
- [ ] Timeline events filtered by selected metric/source
- [ ] Event descriptions include source info
- [ ] Color coding matches selected metric type

**Hourly Data**:
- [ ] Aggregation by hour uses filtered data
- [ ] Peak hours calculation based on selection

**Code Locations**:
- `src/ui/daily_dashboard_widget.py`: Check data loading methods
- `src/ui/activity_timeline_component.py`: Verify filter application

**Verification Steps**:
1. Select "Active Energy" from specific device
2. Verify hourly pattern matches device usage
3. Check timeline shows only relevant events

---

### 5. **Compare Tab**

**Historical Comparisons**:
- [ ] All time periods use same metric/source filter
- [ ] Period-over-period changes calculated correctly
- [ ] Comparison baseline respects filter

**Time Period Cards**:
- [ ] Today vs Yesterday shows filtered data
- [ ] This Week vs Last Week uses selection
- [ ] Monthly comparisons filter consistently

**Status Messages**:
- [ ] Messages indicate which metric is being compared
- [ ] Source device mentioned when specific source selected
- [ ] "All Sources" clearly indicated when no filter

**Code Locations**:
- `src/ui/comparative_visualization.py`: Check filter propagation
- `src/ui/metric_comparison_view.py`: Verify comparison logic

**Verification Steps**:
1. Select "Sleep" from "Apple Watch"
2. Verify all comparisons use Watch sleep data
3. Change to different metric and verify update

---

### 6. **Insights Tab**

**Insight Filtering**:
- [ ] Insights relevant to selected metric prioritized
- [ ] Source-specific insights when source selected
- [ ] General insights marked as "All Metrics"

**Focus Indicator**:
- [ ] Visual indicator shows when specific metric selected
- [ ] Clear "Focused on: [Metric]" message
- [ ] Option to clear focus and see all insights

**Insight Generation**:
- [ ] Anomaly detection uses filtered data
- [ ] Trend analysis respects source selection
- [ ] Correlations computed within filtered dataset

**Code Locations**:
- `src/ui/health_insights_widget.py`: Check insight filtering
- `src/analytics/health_insights_engine.py`: Verify data filtering

**Verification Steps**:
1. Select specific metric and source
2. Check insights are relevant to selection
3. Verify "All Insights" mode shows everything

---

### 7. **Records Tab**

**Record Filtering**:
- [ ] Personal records filtered by selected metric
- [ ] Source included in record description
- [ ] Date ranges respect current filter

**Achievements**:
- [ ] Achievement list filtered by metric type
- [ ] Progress bars use filtered data
- [ ] Streak calculations respect source filter

**Statistics Section**:
- [ ] All-time stats calculated from filtered data
- [ ] Distribution analysis uses selection
- [ ] Percentiles based on filtered dataset

**Code Locations**:
- `src/ui/trophy_case_widget.py`: Check record filtering
- `src/analytics/personal_records_tracker.py`: Verify filter application

**Verification Steps**:
1. Select "Distance" from specific device
2. Verify records show only that device's data
3. Check achievements are distance-related

---

## Cross-Tab Consistency Verification

### Selection Persistence:
- [ ] Metric/source selection preserved when switching tabs
- [ ] Clear visual indicator of current selection on all tabs
- [ ] Consistent filtering across all data queries

### Status Bar Updates:
- [ ] Main window status shows current metric/source
- [ ] Updates immediately when selection changes
- [ ] Shows "All Metrics" or "All Sources" when unfiltered

### Performance:
- [ ] Tab switches don't reload data unnecessarily
- [ ] Cached data respects current filter
- [ ] Background calculations use filtered dataset

---

## Implementation Recommendations

### 1. **Add Global Selection State**
```python
# In MainWindow
self.current_metric_filter = None  # or "All Metrics"
self.current_source_filter = None  # or "All Sources"
```

### 2. **Propagate Selection to All Tabs**
```python
def _on_filters_applied(self, filters):
    self.current_metric_filter = filters.get('metrics', [])
    self.current_source_filter = filters.get('devices', [])
    
    # Update all tabs
    for tab in self.dashboard_tabs:
        if hasattr(tab, 'update_filters'):
            tab.update_filters(filters)
```

### 3. **Add Selection Indicator Widget**
```python
class SelectionIndicator(QWidget):
    """Shows current metric/source selection"""
    def update_selection(self, metrics, sources):
        # Update display
```

### 4. **Consistent Data Access Pattern**
```python
def get_filtered_data(self, metric_filter=None, source_filter=None):
    """Standard method for all components to get filtered data"""
    # Apply consistent filtering
```

---

## Testing Protocol

### Manual Testing Steps:
1. **Single Metric, Single Source**: Select "Steps" from "iPhone" only
2. **Single Metric, All Sources**: Select "Heart Rate" from all devices
3. **Multiple Metrics, Single Source**: Select multiple metrics from one device
4. **All Metrics, Single Source**: Clear metric filter, select one device
5. **Complex Filter**: Date range + specific metric + specific source

### Automated Testing:
- Unit tests for each tab's filter handling
- Integration tests for cross-tab consistency
- Performance tests with large filtered datasets

### Edge Cases:
- No data for selected combination
- Single data point scenarios
- Missing source information
- Mixed metric units