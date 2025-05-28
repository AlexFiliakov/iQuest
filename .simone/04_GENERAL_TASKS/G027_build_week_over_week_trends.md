---
task_id: G027
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G027: Build Week-over-Week Trends

## Description
Calculate percentage changes between weeks with visualizations including slope graphs showing week progression, momentum indicators (accelerating/decelerating), streak tracking for improvements, and mini bar charts in summary cards. Include smart insights with automatic trend narratives and predictive trending.

## Goals
- [ ] Calculate percentage changes between weeks
- [ ] Create slope graph showing week progression
- [ ] Implement momentum indicators (accelerating/decelerating)
- [ ] Build streak tracking for improvement streaks
- [ ] Add mini bar charts in summary cards
- [ ] Generate automatic trend narratives
- [ ] Analyze correlation with external factors
- [ ] Implement predictive trending (next week forecast)
- [ ] Handle edge cases appropriately

## Acceptance Criteria
- [ ] Week-over-week calculations are accurate
- [ ] Slope graphs clearly show progression
- [ ] Momentum indicators reflect trend changes
- [ ] Streak tracking identifies improvement patterns
- [ ] Mini bar charts fit well in summary cards
- [ ] Narrative generation produces meaningful insights
- [ ] Predictive trending provides confidence intervals
- [ ] Weeks with missing days handled properly
- [ ] Holiday weeks flagged and handled differently
- [ ] Timezone changes during week managed correctly
- [ ] Integration tests pass with UI components

## Technical Details

### Trend Visualizations
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)
  
- **Slope Graph**:
  - Lines connecting week values
  - Color coding for increases/decreases
  - Interactive hover for details
  - Smooth transitions on update

- **Momentum Indicators**:
  - Acceleration: Increasing rate of change
  - Deceleration: Decreasing rate of change
  - Steady: Consistent change rate
  - Visual indicators (arrows, colors)

- **Streak Tracking**:
  - Consecutive weeks of improvement
  - Best streak highlighting
  - Current streak status
  - Streak breakage alerts

- **Mini Bar Charts**:
  - Compact visualization in cards
  - Last 4-8 weeks shown
  - Color coding for trends
  - Sparkline alternative

### Smart Insights
- **Automatic Narratives**:
  - Template-based generation
  - Contextual variations
  - Positive reinforcement
  - Actionable suggestions

- **External Correlations**:
  - Weather impact analysis
  - Holiday effects
  - Seasonal patterns
  - User-defined events

- **Predictive Trending**:
  - Simple linear projection
  - Confidence intervals
  - Scenario analysis
  - Achievability scoring

### Edge Cases
- **Missing Days**: 
  - Weighted calculations based on available days
  - Visual indicator for incomplete weeks
  - Confidence adjustment

- **Holiday Weeks**:
  - Automatic detection of holidays
  - Adjusted expectations
  - Special handling in trends

- **Timezone Changes**:
  - DST transition handling
  - Travel timezone shifts
  - Consistent week boundaries

## Dependencies
- G020 (Weekly Metrics Calculator)
- G026 (Day of Week Pattern Analysis)
- Natural language generation library
- Time series forecasting tools

## Implementation Notes
```python
# Example structure
class WeekOverWeekTrends:
    def __init__(self, calculator: WeeklyMetricsCalculator):
        self.calculator = calculator
        self.narrative_generator = TrendNarrativeGenerator()
        
    def calculate_week_change(self, metric: str, week1: int, week2: int) -> TrendResult:
        """Calculate change between two weeks"""
        week1_data = self.calculator.get_week_data(metric, week1)
        week2_data = self.calculator.get_week_data(metric, week2)
        
        # Handle missing days
        if week1_data.missing_days > 0:
            confidence = self.adjust_confidence(week1_data.missing_days)
            
        return TrendResult(
            percent_change=self.calculate_percent_change(week1_data, week2_data),
            momentum=self.calculate_momentum(metric),
            streak=self.get_current_streak(metric),
            confidence=confidence
        )
        
    def detect_momentum(self, changes: List[float]) -> str:
        """Detect if trend is accelerating or decelerating"""
        if len(changes) < 3:
            return "insufficient_data"
            
        acceleration = changes[-1] - changes[-2]
        if acceleration > 0.1:
            return "accelerating"
        elif acceleration < -0.1:
            return "decelerating"
        return "steady"
        
    def predict_next_week(self, metric: str) -> Prediction:
        """Forecast next week's value with confidence interval"""
        pass
```

## Testing Requirements
- Unit tests for all calculation methods
- Edge case testing (holidays, missing data)
- Narrative generation quality tests
- Prediction accuracy validation
- Visual regression tests
- Performance tests with year-long data

## Notes
- Consider user preferences for narrative tone
- Allow customization of streak definitions
- Provide export functionality for trends
- Cache calculations for performance
- Document prediction methodology clearly