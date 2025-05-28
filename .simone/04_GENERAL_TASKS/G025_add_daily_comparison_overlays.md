---
task_id: G025
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G025: Add Daily Comparison Overlays

## Description
Implement multiple overlay types for daily analytics including weekly average (last 7 days), monthly average (last 30 days), personal best overlay, and same day last week/month comparisons. Include visual design with ghost lines, confidence bands, and interactive legends.

## Goals
- [ ] Implement weekly average overlay (last 7 days)
- [ ] Add monthly average overlay (last 30 days)
- [ ] Create personal best overlay
- [ ] Build same day last week/month comparison
- [ ] Design ghost lines with 40% opacity
- [ ] Add confidence bands for averages
- [ ] Create interactive legend to toggle overlays
- [ ] Implement smooth transitions between states
- [ ] Highlight when current exceeds averages
- [ ] Show statistical significance

## Acceptance Criteria
- [ ] All overlay types calculate correctly
- [ ] Ghost lines display at appropriate opacity
- [ ] Confidence bands show statistical ranges
- [ ] Interactive legend allows overlay toggling
- [ ] Smooth animations between overlay states
- [ ] Exceeding averages triggers highlighting
- [ ] Statistical significance indicated visually
- [ ] Context-aware messaging displayed
- [ ] Unit tests cover all calculations
- [ ] Performance remains smooth with multiple overlays

## Technical Details

### Overlay Types
1. **Weekly Average**:
   - Rolling 7-day average
   - Exclude current day from calculation
   - Show trend direction

2. **Monthly Average**:
   - Rolling 30-day average
   - Seasonal adjustment option
   - Confidence intervals

3. **Personal Best**:
   - All-time best for metric
   - Date achieved
   - Percentage comparison

4. **Historical Comparison**:
   - Same day last week
   - Same day last month
   - Same day last year (if available)

### Visual Design
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

- **Ghost Lines**:
  - 40% opacity for overlays
  - Dashed or dotted line styles
  - Distinct colors per overlay type
  - Smooth anti-aliasing

- **Confidence Bands**:
  - Show 95% confidence interval
  - Gradient fill between bands
  - Adjustable transparency
  - Statistical validity indicators

- **Interactive Legend**:
  - Click to toggle overlays
  - Hover for details
  - Drag to reorder
  - Keyboard accessible

### Smart Comparisons
- Automatic highlighting when exceeding averages
- Statistical significance testing (p < 0.05)
- Contextual messages ("Best week this month!")
- Trend indicators with comparisons

## Dependencies
- G019 (Daily Metrics Calculator)
- G023 (Daily Trend Indicators)
- Statistical libraries (SciPy)
- PyQt6 for UI components

## Implementation Notes
```python
# Example structure
class DailyComparisonOverlay:
    def __init__(self, chart_widget):
        self.chart = chart_widget
        self.overlays = {}
        self.legend = InteractiveLegend()
        
    def add_overlay(self, overlay_type: str, data: pd.Series):
        """Add a new overlay to the chart"""
        overlay = self.create_overlay(overlay_type, data)
        self.overlays[overlay_type] = overlay
        self.update_legend()
        
    def create_confidence_band(self, mean: float, std: float) -> Tuple[List, List]:
        """Create upper and lower confidence bands"""
        confidence_level = 1.96  # 95% confidence
        upper = mean + (confidence_level * std)
        lower = mean - (confidence_level * std)
        return upper, lower
        
    def check_significance(self, current: float, comparison: float, std: float) -> bool:
        """Check if difference is statistically significant"""
        z_score = abs(current - comparison) / std
        return z_score > 1.96  # p < 0.05
        
    def generate_context_message(self, metric: str, comparisons: Dict) -> str:
        """Generate contextual insight message"""
        pass
```

## Testing Requirements
- Unit tests for all overlay calculations
- Visual regression tests for rendering
- Statistical test validation
- Performance tests with multiple overlays
- Interaction tests for legend
- Edge case handling (insufficient data)

## Notes
- Ensure overlays don't clutter the main visualization
- Consider colorblind-friendly palette
- Provide option to export comparison data
- Cache overlay calculations for performance
- Document statistical methods used