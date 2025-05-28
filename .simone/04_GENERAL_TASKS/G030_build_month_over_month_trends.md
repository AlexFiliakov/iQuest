---
task_id: G030
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G030: Build Month-over-Month Trends

## Description
Calculate long-term progress metrics with visualizations including waterfall charts for cumulative changes, bump charts for ranking changes, stream graphs for composition over time, and small multiples for metric comparison. Include seasonal decomposition, change point detection, and auto-generated insight summaries.

## Goals
- [ ] Calculate long-term progress metrics
- [ ] Create waterfall charts for cumulative changes
- [ ] Build bump charts for ranking changes
- [ ] Implement stream graphs for composition over time
- [ ] Design small multiples for metric comparison
- [ ] Add seasonal decomposition (trend + seasonal + residual)
- [ ] Implement change point detection
- [ ] Calculate momentum scoring
- [ ] Generate forecast confidence intervals
- [ ] Auto-generate insight summaries
- [ ] Highlight significant milestones
- [ ] Compare to population averages

## Acceptance Criteria
- [ ] Month-over-month calculations are accurate
- [ ] Waterfall charts clearly show cumulative progress
- [ ] Bump charts display ranking changes smoothly
- [ ] Stream graphs show composition effectively
- [ ] Small multiples allow easy comparison
- [ ] Seasonal decomposition identifies patterns
- [ ] Change points detected accurately
- [ ] Momentum scores reflect actual trends
- [ ] Forecasts include confidence intervals
- [ ] Auto-generated insights are meaningful
- [ ] Integration tests pass with real data

## Technical Details

### Visualization Options
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

1. **Waterfall Charts**:
   - Show month-to-month changes
   - Cumulative total progression
   - Color coding (positive/negative)
   - Interactive tooltips

2. **Bump Charts**:
   - Ranking across metrics
   - Smooth line transitions
   - Highlight position changes
   - Time period selection

3. **Stream Graphs**:
   - Stacked area visualization
   - Show metric composition
   - Smooth interpolation
   - Interactive layers

4. **Small Multiples**:
   - Grid of mini charts
   - Consistent scales
   - Synchronized interactions
   - Quick comparison view

### Statistical Analysis
- **Seasonal Decomposition**:
  - Separate trend component
  - Identify seasonal patterns
  - Isolate random variation
  - STL or X-13ARIMA-SEATS

- **Change Point Detection**:
  - Identify significant shifts
  - Multiple detection algorithms
  - Statistical validation
  - Visual indicators

- **Momentum Scoring**:
  - Rate of change analysis
  - Acceleration/deceleration
  - Trend strength indicator
  - Predictive value

- **Forecast Intervals**:
  - 95% confidence bands
  - Multiple scenarios
  - Uncertainty visualization
  - Model selection

### Narrative Generation
- **Insight Templates**:
  - Significant changes
  - Record achievements
  - Trend descriptions
  - Recommendations

- **Milestone Detection**:
  - Personal records
  - Goal achievements
  - Consistency milestones
  - Improvement streaks

- **Population Comparison**:
  - Anonymous benchmarks
  - Percentile rankings
  - Age/demographic adjustments
  - Privacy preserved

## Dependencies
- G021 (Monthly Metrics Calculator)
- G029 (Calendar Heatmap Component)
- Time series analysis libraries (statsmodels)
- Natural language generation tools

## Implementation Notes
```python
# Example structure
class MonthOverMonthTrends:
    def __init__(self, calculator: MonthlyMetricsCalculator):
        self.calculator = calculator
        self.decomposer = SeasonalDecomposer()
        self.change_detector = ChangePointDetector()
        self.narrator = InsightNarrator()
        
    def analyze_trends(self, metric: str, months: int = 12) -> TrendAnalysis:
        """Comprehensive month-over-month analysis"""
        data = self.calculator.get_monthly_data(metric, months)
        
        return TrendAnalysis(
            waterfall_data=self.prepare_waterfall_data(data),
            rankings=self.calculate_metric_rankings(data),
            decomposition=self.decomposer.decompose(data),
            change_points=self.change_detector.detect(data),
            momentum=self.calculate_momentum_score(data),
            forecast=self.generate_forecast(data),
            insights=self.narrator.generate_insights(data)
        )
        
    def create_waterfall_chart(self, data: pd.Series) -> Chart:
        """Create waterfall visualization"""
        changes = data.diff()
        cumulative = changes.cumsum()
        # Build waterfall chart data
        pass
        
    def detect_milestones(self, data: pd.Series) -> List[Milestone]:
        """Identify significant achievements"""
        milestones = []
        # Check for records, streaks, goals
        return milestones
```

### Visualization Components
```python
class TrendVisualizationSuite:
    def __init__(self):
        self.charts = {
            'waterfall': WaterfallChart(),
            'bump': BumpChart(),
            'stream': StreamGraph(),
            'multiples': SmallMultiples()
        }
        
    def render_suite(self, analysis: TrendAnalysis) -> QWidget:
        """Render complete visualization suite"""
        pass
```

## Testing Requirements
- Unit tests for all statistical methods
- Visual regression tests for charts
- Change point detection validation
- Forecast accuracy testing
- Narrative quality assessment
- Performance tests with multi-year data

## Notes
- Consider different decomposition methods
- Allow customization of change sensitivity
- Provide export for all visualizations
- Cache expensive calculations
- Document statistical assumptions
- Plan for real-time updates