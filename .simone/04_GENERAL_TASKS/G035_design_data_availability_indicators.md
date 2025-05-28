---
task_id: G035
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G035: Design Data Availability Indicators

## Description
Create visual indicators for data coverage that show data availability at a glance. Implement coverage percentage calculations, design informative tooltips explaining gaps, and handle partial data scenarios gracefully with clear visual communication.

## Goals
- [ ] Create visual indicators for data coverage
- [ ] Implement coverage percentage calculations
- [ ] Design informative tooltips for data gaps
- [ ] Handle partial data scenarios gracefully
- [ ] Create consistent visual language
- [ ] Support multiple indicator styles
- [ ] Provide detailed breakdowns on demand

## Acceptance Criteria
- [ ] Visual indicators clearly show data availability
- [ ] Coverage percentages are accurate
- [ ] Tooltips provide helpful context
- [ ] Partial data is represented clearly
- [ ] Visual design is consistent across app
- [ ] Indicators update dynamically
- [ ] Accessibility requirements met
- [ ] UI/UX tests validate effectiveness

## Technical Details

### Visual Indicator Types
1. **Coverage Bars**:
   - Horizontal progress bars
   - Color-coded by coverage level
   - Segmented for time periods
   - Animated fill on load

2. **Dot Matrix**:
   - Grid of dots for days/hours
   - Filled dots = data available
   - Empty dots = missing data
   - Hover for specific dates

3. **Heat Strips**:
   - Continuous color gradient
   - Intensity = data density
   - Gaps shown as breaks
   - Compact for small spaces

4. **Badges**:
   - Percentage badges (95%)
   - Quality indicators (Good/Fair/Poor)
   - Warning icons for issues
   - Contextual colors

### Coverage Calculations
- **Simple Coverage**: (Days with data / Total days) × 100
- **Weighted Coverage**: Consider data points per day
- **Quality Score**: Factor in data completeness
- **Confidence Level**: Statistical reliability

### Tooltip Information
- **Summary**: "85% coverage (170 of 200 days)"
- **Gap Details**: "Missing: Dec 15-20, Jan 3-5"
- **Quality Info**: "Partial data on 12 days"
- **Suggestions**: "Import data for better insights"

### Partial Data Handling
- **Visual Representation**:
  - Striped patterns for partial days
  - Opacity for data confidence
  - Different colors for quality levels
  - Icons for specific issues

- **Threshold Definitions**:
  - Complete: >90% expected data points
  - Partial: 10-90% data points
  - Sparse: <10% data points
  - Missing: No data points

## Dependencies
- G032 (Adaptive Display Logic)
- PyQt6 for UI components
- Data availability service

## Implementation Notes
```python
# Example structure
class DataAvailabilityIndicator(QWidget):
    def __init__(self, indicator_type: str = 'bar'):
        super().__init__()
        self.indicator_type = indicator_type
        self.coverage_data = None
        self.setup_ui()
        
    def update_coverage(self, coverage_data: CoverageData):
        """Update indicator with new coverage data"""
        self.coverage_data = coverage_data
        self.calculate_metrics()
        self.update_visual()
        self.update_tooltip()
        
    def calculate_metrics(self) -> Dict:
        """Calculate coverage metrics"""
        return {
            'simple_coverage': self.calculate_simple_coverage(),
            'weighted_coverage': self.calculate_weighted_coverage(),
            'quality_score': self.calculate_quality_score(),
            'confidence_level': self.calculate_confidence(),
            'gap_summary': self.summarize_gaps()
        }
        
    def create_coverage_bar(self) -> QWidget:
        """Create horizontal coverage bar"""
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(self.coverage_data.percentage))
        
        # Apply color based on coverage level
        if self.coverage_data.percentage >= 90:
            bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif self.coverage_data.percentage >= 70:
            bar.setStyleSheet("QProgressBar::chunk { background-color: #FFA726; }")
        else:
            bar.setStyleSheet("QProgressBar::chunk { background-color: #EF5350; }")
            
        return bar
        
    def create_dot_matrix(self) -> QWidget:
        """Create dot matrix visualization"""
        matrix = DotMatrixWidget()
        
        for date in self.coverage_data.date_range:
            if self.coverage_data.has_data(date):
                quality = self.coverage_data.get_quality(date)
                matrix.add_dot(date, quality)
            else:
                matrix.add_empty_dot(date)
                
        return matrix
```

### Tooltip System
```python
class CoverageTooltip(QToolTip):
    def __init__(self, coverage_data: CoverageData):
        super().__init__()
        self.coverage_data = coverage_data
        
    def generate_content(self) -> str:
        """Generate detailed tooltip content"""
        lines = []
        
        # Summary line
        lines.append(f"<b>Coverage: {self.coverage_data.percentage:.1f}%</b>")
        lines.append(f"{self.coverage_data.days_with_data} of {self.coverage_data.total_days} days")
        
        # Quality breakdown
        if self.coverage_data.partial_days > 0:
            lines.append(f"<br><i>Partial data: {self.coverage_data.partial_days} days</i>")
            
        # Gap summary
        if self.coverage_data.gaps:
            lines.append("<br><b>Missing periods:</b>")
            for gap in self.coverage_data.gaps[:3]:  # Show first 3
                lines.append(f"• {gap.start.strftime('%b %d')} - {gap.end.strftime('%b %d')}")
            if len(self.coverage_data.gaps) > 3:
                lines.append(f"• ... and {len(self.coverage_data.gaps) - 3} more")
                
        # Suggestions
        if self.coverage_data.percentage < 80:
            lines.append("<br><i>💡 Import more data for better insights</i>")
            
        return "<br>".join(lines)
```

### Visual Styles
```python
class IndicatorStyles:
    # Color schemes
    COVERAGE_COLORS = {
        'excellent': '#4CAF50',  # Green
        'good': '#8BC34A',      # Light green
        'fair': '#FFA726',      # Orange
        'poor': '#EF5350',      # Red
        'none': '#9E9E9E'       # Gray
    }
    
    # Patterns for partial data
    PARTIAL_PATTERNS = {
        'stripes': 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,.1) 10px, rgba(0,0,0,.1) 20px)',
        'dots': 'radial-gradient(circle, rgba(0,0,0,.1) 1px, transparent 1px)',
        'checkerboard': 'repeating-conic-gradient(#000 0% 25%, transparent 0% 50%)'
    }
    
    @staticmethod
    def get_coverage_color(percentage: float) -> str:
        """Get color based on coverage percentage"""
        if percentage >= 90:
            return IndicatorStyles.COVERAGE_COLORS['excellent']
        elif percentage >= 75:
            return IndicatorStyles.COVERAGE_COLORS['good']
        elif percentage >= 50:
            return IndicatorStyles.COVERAGE_COLORS['fair']
        elif percentage > 0:
            return IndicatorStyles.COVERAGE_COLORS['poor']
        else:
            return IndicatorStyles.COVERAGE_COLORS['none']
```

## Testing Requirements
- Unit tests for coverage calculations
- Visual tests for all indicator types
- Tooltip content validation
- Accessibility testing (screen readers)
- Performance with large date ranges
- Color contrast validation
- User comprehension testing

## Notes
- Consider colorblind-friendly palettes
- Provide text alternatives for visual indicators
- Allow customization of thresholds
- Cache coverage calculations
- Plan for real-time updates
- Document visual language in style guide