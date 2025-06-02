---
task_id: G091
status: open
complexity: Medium
last_updated: 2025-06-01T23:57:14Z
---

# Task: Fix Health Metric Cards Display and View Selector in Daily Tab

## Description

The Daily tab in the Apple Health Monitor Dashboard has a critical issue where the view selector (`self.view_selector.addItems(["All Metrics", "Activity", "Vitals", "Body"])`) doesn't properly filter the displayed metrics. When any option is selected, none of the metrics display due to a naming mismatch between the category mapping (which uses shorthand names like 'steps') and the metric cards dictionary (which uses database names like 'StepCount'). Additionally, the application only displays a predefined subset of metrics and uses a hardcoded SUM aggregation method that's inappropriate for many metric types (e.g., heart rate should use AVERAGE, not SUM).

## Context and Background

Based on comprehensive codebase analysis, the issue stems from three distinct naming conventions used throughout the application:

1. **Database names**: 'StepCount', 'HeartRate', 'ActiveEnergyBurned' (used as keys in `_metric_cards`)
2. **Shorthand names**: 'steps', 'heart_rate', 'active_calories' (used in category mapping)
3. **Display names**: 'Steps', 'Heart Rate', 'Active Calories' (shown to users)

The `_filter_metric_cards()` method in `daily_dashboard_widget.py` attempts to match shorthand names against database names, which always fails, causing all cards to become invisible when any filter is applied.

### Root Causes Identified

1. **Naming System Mismatch**: The category filter uses shorthand names while metric cards are keyed by database names
2. **Incorrect Aggregation**: All metrics use SUM aggregation regardless of metric type
3. **Limited Metric Display**: Only predefined metrics are shown instead of all available metrics
4. **No Aggregation Options**: Users cannot select different aggregation methods

## Goal / Objectives

1. **Fix the view selector** to properly filter metrics by category
2. **Display all available metrics** from all data sources instead of a predefined subset
3. **Replace category-based filtering** with aggregation method selection (Average, Minimum, Maximum, Sum, etc.)
4. **Implement metric-appropriate aggregation** based on the metric type
5. **Maintain performance** while supporting dynamic metric discovery

## Acceptance Criteria

- [ ] View selector successfully filters metrics when categories are selected
- [ ] All available health metrics from the database are displayed (not just predefined ones)
- [ ] View selector is repurposed to show aggregation methods instead of categories
- [ ] Each metric type uses appropriate default aggregation (SUM for activity, AVERAGE for vitals)
- [ ] Users can switch between different aggregation methods dynamically
- [ ] Performance remains acceptable with dynamic metric loading
- [ ] Existing UI styling and layout are preserved
- [ ] Changes follow existing code patterns and architecture

## Technical Approach

### Phase 1: Fix Immediate Display Issue

1. **Fix _filter_metric_cards() Method**
   - Convert shorthand names to database names before comparison
   - Use existing `_shorthand_to_db` mapping for conversion
   - Ensure proper visibility toggling

2. **Implement Dynamic Metric Discovery**
   - Query all available metric types from database
   - Remove hardcoded metric limitations
   - Support metrics from all data sources

### Phase 2: Replace Category Filter with Aggregation Selector

1. **Update View Selector Options**
   - Replace ["All Metrics", "Activity", "Vitals", "Body"] with aggregation methods
   - Options: ["Average", "Sum", "Minimum", "Maximum", "Latest", "Count"]
   - Store current aggregation method in widget state

2. **Implement Metric-Specific Aggregation Logic**
   - Create aggregation method mapping for each metric type
   - Default: SUM for activity metrics, AVERAGE for vitals/body metrics, if unknown default to SUM
   - Allow user override through view selector

3. **Update Data Loading Queries**
   - Modify SQL queries to use selected aggregation method
   - Ensure proper NULL handling for each aggregation type
   - Maintain performance with appropriate indexing

### Phase 3: Enhance Metric Display

1. **Support All Available Metrics**
   - Remove 8-metric limitation if feasible
   - Implement scrollable metric card area if needed
   - Use lazy loading for performance

2. **Add Metric Source Information**
   - Display data source alongside metric value
   - Handle multiple sources per metric appropriately

## Implementation Notes

### Key Files to Modify

1. **daily_dashboard_widget.py** (PRIMARY)
   - Fix `_filter_metric_cards()` method (lines 1699-1711)
   - Update `_create_metric_cards_section()` to change selector options
   - Modify `_load_daily_data()` to use dynamic aggregation
   - Update `_create_metric_cards()` to handle all available metrics

2. **Database Query Updates**
   - Replace hardcoded SUM with dynamic aggregation
   - Add aggregation method parameter to query methods
   - Ensure proper type casting for different aggregations

### Technical Guidance

**Key Integration Points:**
- `HealthDatabase.get_available_types()` - For dynamic metric discovery
- `_shorthand_to_db` mapping (lines 325-413) - For name conversion
- `_create_metric_cards()` (lines 979-1020) - For card creation
- `_load_daily_data()` (lines 1537-1607) - For data fetching

**Existing Patterns to Follow:**
- Use QThread for heavy database operations (see existing background workers)
- Apply styles via centralized StyleManager
- Follow Google-style docstrings for new methods
- Use existing error handling patterns with proper logging

**Testing Approach:**
- Unit tests for aggregation logic with various metric types

### Alternative Approaches Considered

1. **Keep Category-Based Filtering**
   - **Pros**: Maintains current UI paradigm, easier for users to understand
   - **Cons**: Doesn't address aggregation needs, requires maintaining category mappings
   - **Decision**: Rejected in favor of aggregation-based approach

2. **Dual Selectors (Category + Aggregation)**
   - **Pros**: Maximum flexibility, supports both use cases
   - **Cons**: More complex UI, potential user confusion, unknown categories for new metrics
   - **Decision**: Consider as future enhancement if user feedback indicates need

3. **Metric-Specific Aggregation Only**
   - **Pros**: Simpler implementation, no user choice needed
   - **Cons**: Less flexibility, users cannot explore data differently
   - **Decision**: Implement as default but allow user override

## Dependencies

### Internal Dependencies
- `src/ui/daily_dashboard_widget.py` - Primary implementation file
- `src/health_database.py` - Database access for metric discovery
- `src/models.py` - Data models for health records
- `src/ui/style_manager.py` - UI styling consistency

### External Dependencies
- PyQt6 widgets for UI components
- SQLite for database queries
- Existing caching infrastructure

## Subtasks

- [ ] Fix _filter_metric_cards() naming mismatch
- [ ] Implement dynamic metric discovery from database
- [ ] Replace category options with aggregation methods
- [ ] Create metric-specific default aggregation mapping
- [ ] Update SQL queries to use dynamic aggregation
- [ ] Test with various metric types and edge cases
- [ ] Update documentation for new functionality
- [ ] Create user guide for aggregation selector

## Risk Assessment

### Medium Risk
- **Performance impact** from dynamic metric loading
- **UI layout issues** with variable number of metrics
- **Breaking changes** for users expecting category filtering

### Mitigation Strategies
- Implement caching for metric discovery
- Use lazy loading for metric cards

## Expected Outcomes

### Immediate Benefits
- View selector becomes functional
- All imported metrics are accessible
- Appropriate aggregation for each metric type

### Long-term Benefits
- More flexible data exploration
- Support for new metric types without code changes
- Better user understanding of their health data

## Output Log

[2025-06-01 23:57:14] Task created - Fix health metric cards display and view selector