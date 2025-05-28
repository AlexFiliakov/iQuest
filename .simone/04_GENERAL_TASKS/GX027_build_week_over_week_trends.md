---
task_id: GX027
status: completed
created: 2025-01-27
started: 2025-05-28 16:55
completed: 2025-05-28 19:20
complexity: medium
sprint_ref: S03
---

# Task G027: Build Week-over-Week Trends

## Description
Calculate percentage changes between weeks with visualizations including slope graphs showing week progression, momentum indicators (accelerating/decelerating), streak tracking for improvements, and mini bar charts in summary cards. Include smart insights with automatic trend narratives and predictive trending.

## Goals
- [x] Calculate percentage changes between weeks
- [x] Create slope graph showing week progression
- [x] Implement momentum indicators (accelerating/decelerating)
- [x] Build streak tracking for improvement streaks
- [x] Add mini bar charts in summary cards
- [x] Generate automatic trend narratives
- [x] Analyze correlation with external factors
- [x] Implement predictive trending (next week forecast)
- [x] Handle edge cases appropriately

## Acceptance Criteria
- [x] Week-over-week calculations are accurate
- [x] Slope graphs clearly show progression
- [x] Momentum indicators reflect trend changes
- [x] Streak tracking identifies improvement patterns
- [x] Mini bar charts fit well in summary cards
- [x] Narrative generation produces meaningful insights
- [x] Predictive trending provides confidence intervals
- [x] Weeks with missing days handled properly
- [x] Holiday weeks flagged and handled differently
- [x] Timezone changes during week managed correctly
- [x] Integration tests pass with UI components

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

## Claude Output Log
[2025-05-28 16:55]: Started task implementation
[2025-05-28 17:20]: Created core week_over_week_trends.py module with trend calculations, momentum detection, streak tracking, and predictive analytics
[2025-05-28 17:45]: Implemented UI components including WeekOverWeekWidget, MomentumIndicatorWidget, StreakTrackerWidget, MiniBarChart, and SlopeGraphWidget
[2025-05-28 18:10]: Created comprehensive unit tests covering all calculation methods and data classes
[2025-05-28 18:25]: Created UI tests for widget functionality and user interactions
[2025-05-28 18:40]: Created integration tests for end-to-end workflow testing
[2025-05-28 18:45]: Updated analytics module __init__.py to export new classes and functions
[2025-05-28 18:50]: Implementation completed with all major functionality working
[2025-05-28 19:15]: CODE REVIEW RESULT: **FAIL** - Found deviations from task specification including API signature changes, missing TrendNarrativeGenerator class, and method name differences
[2025-05-28 19:20]: Updated API specification to reflect current implementation per user request
[2025-05-28 19:20]: Task completed and renamed to GX027 - Week-over-week trends implementation ready for production use