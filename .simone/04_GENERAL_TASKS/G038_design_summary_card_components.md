---
task_id: G038
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G038: Design Summary Card Components

## Description
Create metric highlight cards that display key statistics with dynamic content updates, responsive layouts, and trend indicators. Design reusable card components that provide at-a-glance insights across the application.

## Goals
- [ ] Create metric highlight cards
- [ ] Implement dynamic content updates
- [ ] Design responsive layouts
- [ ] Add trend indicators
- [ ] Support multiple card sizes
- [ ] Create smooth update animations
- [ ] Add interactive elements
- [ ] Implement card templates

## Acceptance Criteria
- [ ] Cards display metrics clearly and attractively
- [ ] Dynamic updates work smoothly
- [ ] Cards resize responsively
- [ ] Trend indicators are intuitive
- [ ] Multiple card sizes available
- [ ] Animations enhance user experience
- [ ] Interactive elements work correctly
- [ ] UI component tests pass
- [ ] Cards maintain consistent styling

## Technical Details

### Card Types
1. **Simple Metric Card**:
   - Large primary value
   - Metric name
   - Trend indicator
   - Optional subtitle

2. **Comparison Card**:
   - Current vs previous
   - Percentage change
   - Visual indicator
   - Time period label

3. **Mini Chart Card**:
   - Small sparkline/bar
   - Current value
   - Min/max indicators
   - Trend summary

4. **Goal Progress Card**:
   - Progress bar/ring
   - Current vs target
   - Completion percentage
   - Estimated completion

### Component Structure
```python
# Example structure
class SummaryCard(QWidget):
    def __init__(self, card_type: str = 'simple', size: str = 'medium'):
        super().__init__()
        self.card_type = card_type
        self.size = size
        self.value_animator = QPropertyAnimation(self, b"value")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup card UI based on type"""
        self.layout = QVBoxLayout()
        
        # Card container with styling
        self.card_frame = QFrame()
        self.card_frame.setObjectName("summaryCard")
        self.apply_card_style()
        
        # Content based on card type
        if self.card_type == 'simple':
            self.setup_simple_card()
        elif self.card_type == 'comparison':
            self.setup_comparison_card()
        elif self.card_type == 'mini_chart':
            self.setup_mini_chart_card()
        elif self.card_type == 'goal_progress':
            self.setup_goal_card()
            
    def update_content(self, data: Dict, animate: bool = True):
        """Update card content with optional animation"""
        if animate:
            self.animate_update(data)
        else:
            self.direct_update(data)
```

### Card Layouts
```python
class SimpleMetricCard(SummaryCard):
    def setup_simple_card(self):
        """Setup simple metric card layout"""
        # Metric name (top)
        self.title_label = QLabel()
        self.title_label.setObjectName("cardTitle")
        
        # Main value (center, large)
        self.value_label = QLabel()
        self.value_label.setObjectName("cardValue")
        
        # Trend indicator (bottom)
        self.trend_widget = TrendIndicatorWidget()
        
        # Subtitle (optional)
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("cardSubtitle")
        
        # Layout
        layout = QVBoxLayout(self.card_frame)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label, 1, Qt.AlignCenter)
        layout.addWidget(self.trend_widget)
        layout.addWidget(self.subtitle_label)
        
class ComparisonCard(SummaryCard):
    def setup_comparison_card(self):
        """Setup comparison card with current vs previous"""
        grid = QGridLayout(self.card_frame)
        
        # Current value
        self.current_label = QLabel("Current")
        self.current_value = QLabel()
        
        # Previous value
        self.previous_label = QLabel("Previous")
        self.previous_value = QLabel()
        
        # Change indicator
        self.change_widget = ChangeIndicatorWidget()
        
        # Layout in grid
        grid.addWidget(self.current_label, 0, 0)
        grid.addWidget(self.current_value, 1, 0)
        grid.addWidget(self.previous_label, 0, 1)
        grid.addWidget(self.previous_value, 1, 1)
        grid.addWidget(self.change_widget, 2, 0, 1, 2)
```

### Trend Indicators
```python
class TrendIndicatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.trend_value = 0
        self.setup_ui()
        
    def set_trend(self, current: float, previous: float):
        """Set trend based on values"""
        if previous == 0:
            self.trend_value = 0
        else:
            self.trend_value = ((current - previous) / previous) * 100
            
        self.update_display()
        
    def update_display(self):
        """Update visual display of trend"""
        # Arrow direction
        if self.trend_value > 0:
            arrow = "↑"
            color = "#4CAF50"  # Green
        elif self.trend_value < 0:
            arrow = "↓"
            color = "#F44336"  # Red
        else:
            arrow = "→"
            color = "#9E9E9E"  # Gray
            
        # Update label
        self.label.setText(f"{arrow} {abs(self.trend_value):.1f}%")
        self.label.setStyleSheet(f"color: {color};")
```

### Dynamic Updates
```python
class AnimatedSummaryCard(SummaryCard):
    value = pyqtProperty(float)
    
    def animate_update(self, data: Dict):
        """Animate card content update"""
        # Animate main value
        if 'value' in data:
            self.value_animator.setStartValue(self.current_value)
            self.value_animator.setEndValue(data['value'])
            self.value_animator.setDuration(500)
            self.value_animator.valueChanged.connect(self.update_value_display)
            self.value_animator.start()
            
        # Fade transition for other elements
        self.fade_transition = QPropertyAnimation(self.card_frame, b"opacity")
        self.fade_transition.setStartValue(1.0)
        self.fade_transition.setKeyValueAt(0.5, 0.3)
        self.fade_transition.setEndValue(1.0)
        self.fade_transition.setDuration(300)
        self.fade_transition.finished.connect(
            lambda: self.update_secondary_content(data)
        )
        self.fade_transition.start()
```

### Responsive Sizing
```python
class ResponsiveSummaryCard(SummaryCard):
    SIZE_CONFIGS = {
        'small': {
            'min_width': 150,
            'min_height': 100,
            'title_font': 12,
            'value_font': 24,
            'padding': 10
        },
        'medium': {
            'min_width': 200,
            'min_height': 150,
            'title_font': 14,
            'value_font': 32,
            'padding': 15
        },
        'large': {
            'min_width': 300,
            'min_height': 200,
            'title_font': 16,
            'value_font': 48,
            'padding': 20
        }
    }
    
    def apply_size_config(self):
        """Apply size-specific configuration"""
        config = self.SIZE_CONFIGS[self.size]
        
        self.setMinimumSize(config['min_width'], config['min_height'])
        
        # Update font sizes
        title_font = QFont()
        title_font.setPointSize(config['title_font'])
        self.title_label.setFont(title_font)
        
        value_font = QFont()
        value_font.setPointSize(config['value_font'])
        value_font.setBold(True)
        self.value_label.setFont(value_font)
```

### Card Styling
```css
/* Card styles */
#summaryCard {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #E0E0E0;
    padding: 15px;
}

#summaryCard:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
    transition: all 0.2s ease;
}

#cardTitle {
    color: #666666;
    font-weight: 500;
}

#cardValue {
    color: #FF8C42;
    font-weight: bold;
}

#cardSubtitle {
    color: #999999;
    font-size: 12px;
}
```

## Testing Requirements
- Unit tests for all card types
- Visual regression tests
- Animation testing
- Responsive layout tests
- Dynamic update tests
- Performance with many cards
- Accessibility validation

## Notes
- Keep cards visually consistent
- Ensure text remains readable
- Consider dark mode support
- Provide customization options
- Document card templates
- Plan for card collections/grids