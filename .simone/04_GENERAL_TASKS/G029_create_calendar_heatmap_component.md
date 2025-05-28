---
task_id: G029
status: open
created: 2025-01-27
complexity: high
sprint_ref: S03
---

# Task G029: Create Calendar Heatmap Component

## Description
Design calendar grid layout with multiple view options including traditional month grid, GitHub-style contribution graph, and circular/spiral year view. Implement interactive features like drill-down, hover details, brush selection, and touch gestures with perceptually uniform color scales.

## Goals
- [ ] Design traditional month grid calendar view
- [ ] Create GitHub-style contribution graph
- [ ] Build circular/spiral year view option
- [ ] Implement click to drill down to daily view
- [ ] Add hover for detailed stats
- [ ] Create brush selection for date ranges
- [ ] Support pinch/zoom on touch devices
- [ ] Use perceptually uniform color scales (viridis)
- [ ] Add adaptive color ranges per metric
- [ ] Implement today marker with pulse animation
- [ ] Show data quality indicators using opacity
- [ ] Add patterns for colorblind accessibility

## Acceptance Criteria
- [ ] All three view modes render correctly
- [ ] Smooth transitions between view modes
- [ ] Interactive features work on all devices
- [ ] Color scales are perceptually uniform
- [ ] Today marker is clearly visible
- [ ] Data quality reflected in visualization
- [ ] Colorblind patterns available
- [ ] Touch gestures work smoothly
- [ ] Visual regression tests pass
- [ ] Performance acceptable with 5 years data

## Technical Details

### View Modes
1. **Traditional Month Grid**:
   - Standard calendar layout
   - Week starts configurable (Sun/Mon)
   - Month navigation arrows
   - Year overview option

2. **GitHub-Style Graph**:
   - 52 weeks × 7 days grid
   - Scrollable for multiple years
   - Contribution intensity colors
   - Streak indicators

3. **Circular/Spiral View**:
   - 365-day spiral or circle
   - Seasons as quadrants
   - Radial time representation
   - Zoomable center detail

### Interactive Features
- **Drill-down**:
  - Click date to see hourly breakdown
  - Smooth zoom animation
  - Context preservation
  - Back navigation

- **Hover Details**:
  - Tooltip with full stats
  - Comparison to averages
  - Mini chart preview
  - Keyboard accessible

- **Brush Selection**:
  - Click and drag date range
  - Visual feedback during selection
  - Range statistics display
  - Export selected data

- **Touch Gestures**:
  - Pinch to zoom
  - Swipe to navigate months
  - Long press for details
  - Smooth momentum scrolling

### Visual Excellence
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

- **Color Scales**:
  - Viridis (default): Perceptually uniform
  - Plasma: High contrast option
  - Cividis: Colorblind friendly
  - Custom scales per metric

- **Adaptive Ranges**:
  - Auto-adjust to data distribution
  - Manual override option
  - Outlier handling
  - Consistent across views

- **Today Marker**:
  - Subtle pulse animation
  - High contrast border
  - Optional date label
  - Timezone aware

- **Data Quality**:
  - Opacity for confidence
  - Hatching for missing data
  - Icons for data issues
  - Legend explanation

### Accessibility
- **Colorblind Support**:
  - Pattern overlays (diagonal lines, dots)
  - Shape indicators
  - Text labels option
  - High contrast mode

## Dependencies
- G021 (Monthly Metrics Calculator)
- D3.js or similar for advanced visualizations
- PyQt6 for component framework
- Touch gesture library

## Implementation Notes
```python
# Example structure
class CalendarHeatmapComponent(QWidget):
    def __init__(self):
        super().__init__()
        self.view_mode = 'month'  # 'month', 'github', 'spiral'
        self.color_scale = 'viridis'
        self.data_range = None
        self.selection_handler = SelectionHandler()
        
    def set_view_mode(self, mode: str):
        """Switch between calendar view modes"""
        self.animate_transition(self.view_mode, mode)
        self.view_mode = mode
        self.render()
        
    def render_month_view(self):
        """Render traditional calendar grid"""
        pass
        
    def render_github_view(self):
        """Render GitHub-style contribution graph"""
        pass
        
    def render_spiral_view(self):
        """Render circular/spiral year view"""
        pass
        
    def apply_color_scale(self, value: float) -> QColor:
        """Map value to color using selected scale"""
        normalized = self.normalize_value(value)
        return self.color_scales[self.color_scale](normalized)
        
    def enable_touch_gestures(self):
        """Setup touch gesture recognizers"""
        self.grabGesture(Qt.PinchGesture)
        self.grabGesture(Qt.SwipeGesture)
```

### Performance Optimization
- Virtual scrolling for large date ranges
- Level-of-detail rendering
- GPU acceleration where available
- Efficient date calculations
- Smart caching of rendered tiles

## Testing Requirements
- Visual regression tests for all view modes
- Touch gesture testing on devices
- Color scale accuracy validation
- Performance tests with 5+ years data
- Accessibility compliance tests
- Browser compatibility (if web-based)

## Notes
- Consider cultural calendar differences
- Provide export options (PNG, SVG, data)
- Allow customization of week start day
- Consider integration with external calendars
- Document color scale choices
- Plan for future animation preferences