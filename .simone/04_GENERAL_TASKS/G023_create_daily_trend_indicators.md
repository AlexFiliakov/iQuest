---
task_id: G023
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G023: Create Daily Trend Indicators

## Description
Implement trend comparison logic for daily metrics (vs previous day) with animated arrow indicators, color gradients based on change magnitude, sparkline mini-charts for 7-day context, and detailed tooltips showing exact changes and historical context.

## Goals
- [ ] Implement trend comparison logic (vs previous day)
- [ ] Create animated arrow indicators with easing functions
- [ ] Design color gradients (green +10%, yellow ±5%, red -10%)
- [ ] Build sparkline mini-charts for 7-day context
- [ ] Add tooltips showing exact change and historical context
- [ ] Handle edge cases appropriately
- [ ] Add subtle pulse animation for significant changes

## Acceptance Criteria
- [ ] Trend indicators accurately show daily changes
- [ ] Smooth animations with configurable easing
- [ ] Color gradients clearly indicate change magnitude
- [ ] Sparklines provide quick visual context
- [ ] Tooltips display detailed change information
- [ ] First day shows "baseline" indicator
- [ ] Missing previous day uses last available
- [ ] Zero values show absolute change only
- [ ] Unit tests cover all calculation scenarios

## Technical Details

### Visual Design
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

- **Arrow Indicators**: 
  - Animated with easing functions (ease-in-out)
  - Size scales with change magnitude
  - Rotation for up/down/neutral
  
- **Color Gradients**:
  - Green: Improvement >10%
  - Yellow: Minor change ±5%
  - Red: Decline >10%
  - Smooth transitions between colors

- **Sparkline Charts**:
  - 7-day mini visualization
  - Highlight current day
  - Show trend line
  - Interactive hover states

### Edge Cases
- **First Day**: Display "Setting baseline" indicator
- **Missing Previous Day**: Use last available data point
- **Zero Values**: Show absolute change only, not percentage
- **Data Gaps**: Visual indicator for missing data

### UI Polish
- Pulse animation for changes >20%
- Smooth transitions between states
- Hover effects for additional info
- Keyboard navigation support

## Dependencies
- G019 (Daily Metrics Calculator)
- PyQt6 for UI components
- Matplotlib for sparklines
- QPropertyAnimation for animations

## Implementation Notes
```python
# Example structure
class DailyTrendIndicator(QWidget):
    def __init__(self, metric_name: str):
        super().__init__()
        self.metric_name = metric_name
        self.animator = QPropertyAnimation(self, b"rotation")
        
    def update_trend(self, current: float, previous: float):
        """Update trend indicator with new values"""
        change_percent = self.calculate_change(current, previous)
        self.animate_arrow(change_percent)
        self.update_color_gradient(change_percent)
        self.update_sparkline()
        
    def create_sparkline(self, data: List[float]) -> QPixmap:
        """Generate sparkline chart"""
        pass
        
    def show_detailed_tooltip(self):
        """Display detailed change information"""
        pass
```

## Testing Requirements
- Unit tests for trend calculations
- Visual regression tests for animations
- Edge case coverage
- Performance tests for sparkline generation
- Accessibility testing

## Notes
- Follow existing UI patterns from configuration_tab.py
- Ensure animations are smooth but not distracting
- Consider user preferences for animation speed
- Provide option to disable animations
- Document color choices for accessibility