---
task_id: G028
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G028: Add Monthly Context to Weekly View

## Description
Calculate monthly averages for comparison with weekly data, showing percentile rank within month, best/worst week indicators, monthly goal progress tracking, and seasonal adjustment factors. Design with background shading for context and interactive drill-down capabilities.

## Goals
- [ ] Calculate monthly averages for comparison
- [ ] Show percentile rank within month
- [ ] Add best/worst week indicators
- [ ] Implement monthly goal progress tracking
- [ ] Apply seasonal adjustment factors
- [ ] Design background shading for context
- [ ] Create floating labels for key insights
- [ ] Build interactive drill-down to daily view
- [ ] Cache monthly aggregates for performance

## Acceptance Criteria
- [ ] Monthly averages calculated correctly
- [ ] Percentile ranks accurately reflect week position
- [ ] Best/worst weeks clearly highlighted
- [ ] Goal progress displayed with visual indicators
- [ ] Seasonal adjustments applied appropriately
- [ ] Background shading provides clear context
- [ ] Floating labels appear on hover/focus
- [ ] Drill-down navigation works smoothly
- [ ] Cache improves query performance >50%
- [ ] Unit tests cover all calculations

## Technical Details

### Context Layers
1. **Percentile Ranking**:
   - Week's position within month (0-100)
   - Visual indicator (gauge, bar)
   - Comparison to typical week

2. **Best/Worst Indicators**:
   - Highlight exceptional weeks
   - Reason for exceptional status
   - Historical context

3. **Goal Progress**:
   - Monthly targets vs actual
   - Projected month-end status
   - Daily required average to meet goal

4. **Seasonal Adjustments**:
   - Month-specific baselines
   - Year-over-year comparisons
   - Weather/season correlations

### Visual Design
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

- **Background Shading**:
  - Subtle gradient for context
  - Monthly average as baseline
  - Confidence bands as shading
  - Non-intrusive opacity

- **Floating Labels**:
  - Key insights on hover
  - Smart positioning
  - Fade in/out animations
  - Keyboard accessible

- **Interactive Drill-down**:
  - Click week to see daily breakdown
  - Smooth transition animation
  - Breadcrumb navigation
  - Maintain context during drill-down

### Performance
- **Caching Strategy**:
  - Pre-calculate monthly aggregates
  - Invalidate on new data
  - Background refresh
  - Memory-efficient storage

## Dependencies
- G020 (Weekly Metrics Calculator)
- G021 (Monthly Metrics Calculator)
- G022 (Analytics Caching Layer)
- PyQt6 for UI components

## Implementation Notes
```python
# Example structure
class MonthlyContextProvider:
    def __init__(self, cache_manager: AnalyticsCacheManager):
        self.cache = cache_manager
        self.monthly_calc = MonthlyMetricsCalculator()
        
    def get_week_context(self, week_num: int, year: int, metric: str) -> WeekContext:
        """Get monthly context for a specific week"""
        month = self.get_month_for_week(week_num, year)
        
        # Try cache first
        cache_key = f"monthly_context_{year}_{month}_{metric}"
        if cached := self.cache.get(cache_key):
            return cached
            
        # Calculate context
        context = WeekContext(
            percentile_rank=self.calculate_percentile(week_num, month, year, metric),
            is_best_week=self.check_if_best_week(week_num, month, year, metric),
            is_worst_week=self.check_if_worst_week(week_num, month, year, metric),
            goal_progress=self.calculate_goal_progress(week_num, month, year, metric),
            seasonal_factor=self.get_seasonal_adjustment(month, metric)
        )
        
        self.cache.set(cache_key, context, ttl=3600)
        return context
        
    def create_context_visualization(self, week_context: WeekContext) -> QWidget:
        """Create visual representation of monthly context"""
        widget = QWidget()
        # Add background shading
        # Add floating labels
        # Setup drill-down handlers
        return widget
```

## Testing Requirements
- Unit tests for context calculations
- Cache effectiveness tests
- Visual regression tests
- Interaction tests for drill-down
- Performance benchmarks
- Edge cases (partial months, year boundaries)

## Notes
- Ensure context doesn't overwhelm primary data
- Consider different month lengths in calculations
- Provide clear explanations for adjustments
- Allow users to toggle context layers
- Document calculation methods in UI