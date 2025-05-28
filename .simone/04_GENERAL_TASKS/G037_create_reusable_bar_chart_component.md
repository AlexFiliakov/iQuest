---
task_id: G037
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G037: Create Reusable Bar Chart Component

## Description
Build a base bar chart component that supports daily/weekly comparisons with grouping logic, value labels, legends, and follows the warm color theme. Create a flexible component for various bar chart needs across the application.

## Goals
- [ ] Build base bar chart component
- [ ] Support daily/weekly comparisons
- [ ] Implement grouping logic
- [ ] Add value labels and legends
- [ ] Support stacked and grouped bars
- [ ] Add animation capabilities
- [ ] Create hover interactions
- [ ] Implement export functionality

## Acceptance Criteria
- [ ] Bar charts render correctly for various data types
- [ ] Grouping logic works for time-based data
- [ ] Value labels are readable and well-positioned
- [ ] Legends are clear and interactive
- [ ] Stacked/grouped modes work correctly
- [ ] Animations are smooth
- [ ] Hover effects provide additional info
- [ ] Visual regression tests pass
- [ ] Performance good with 100+ bars

## Technical Details

### Chart Types
- **Inspired by the Wall Street Journal**: Create analytics in the style of Wall Street Journal (see for example `examples/wall street journal chart example 1.jpg` and `examples/wall street journal chart example 2.jpg`)

1. **Simple Bar Chart**:
   - Single data series
   - Vertical or horizontal
   - Value labels on bars
   - Color coding

2. **Grouped Bar Chart**:
   - Multiple series side-by-side
   - Consistent spacing
   - Group labels
   - Legend for series

3. **Stacked Bar Chart**:
   - Series stacked vertically
   - Total height shows sum
   - Segment labels
   - Percentage option

### Component Features
```python
# Example structure
class BarChart(QWidget):
    def __init__(self, config: BarChartConfig = None):
        super().__init__()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.config = config or BarChartConfig()
        self.bar_containers = []
        self.setup_ui()
        
    def plot(self, data: pd.DataFrame, chart_type: str = 'simple', **kwargs):
        """Plot bar chart with specified type"""
        self.ax = self.figure.add_subplot(111)
        self.apply_theme()
        
        if chart_type == 'simple':
            self._plot_simple_bars(data, **kwargs)
        elif chart_type == 'grouped':
            self._plot_grouped_bars(data, **kwargs)
        elif chart_type == 'stacked':
            self._plot_stacked_bars(data, **kwargs)
            
        self.add_value_labels()
        self.configure_legend()
        self.setup_interactions()
        self.canvas.draw()
        
    def _plot_grouped_bars(self, data: pd.DataFrame, **kwargs):
        """Plot grouped bar chart"""
        n_groups = len(data.index)
        n_bars = len(data.columns)
        width = 0.8 / n_bars
        
        colors = self.config.get_color_sequence(n_bars)
        
        for i, column in enumerate(data.columns):
            positions = np.arange(n_groups) + i * width
            bars = self.ax.bar(
                positions,
                data[column],
                width,
                label=column,
                color=colors[i],
                alpha=0.8
            )
            self.bar_containers.append(bars)
            
        # Center x-tick labels
        self.ax.set_xticks(np.arange(n_groups) + width * (n_bars - 1) / 2)
        self.ax.set_xticklabels(data.index)
```

### Value Labels
```python
class ValueLabelManager:
    def __init__(self, ax: Axes, config: BarChartConfig):
        self.ax = ax
        self.config = config
        
    def add_labels(self, bars: BarContainer, format_str: str = '{:.0f}'):
        """Add value labels to bars"""
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only label positive values
                label = format_str.format(height)
                
                # Smart positioning
                y_pos = height + self.config.label_offset
                if y_pos > self.ax.get_ylim()[1] * 0.95:
                    # Place inside bar if too close to top
                    y_pos = height - self.config.label_offset
                    color = 'white'
                else:
                    color = self.config.label_color
                    
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    y_pos,
                    label,
                    ha='center',
                    va='bottom' if y_pos > height else 'top',
                    fontsize=self.config.label_font_size,
                    color=color
                )
```

### Interactive Features
```python
class InteractiveBarChart(BarChart):
    def setup_interactions(self):
        """Setup hover and click interactions"""
        self.hover_annotation = None
        self.selected_bars = []
        
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
    def on_hover(self, event):
        """Handle hover events"""
        if event.inaxes != self.ax:
            self.clear_hover()
            return
            
        # Find bar under cursor
        for container in self.bar_containers:
            for bar in container:
                if bar.contains(event)[0]:
                    self.show_hover_info(bar, event)
                    return
                    
        self.clear_hover()
        
    def show_hover_info(self, bar: Rectangle, event):
        """Show detailed information on hover"""
        if self.hover_annotation:
            self.hover_annotation.remove()
            
        # Get bar data
        x_val = bar.get_x() + bar.get_width() / 2
        y_val = bar.get_height()
        
        # Create annotation
        text = f"Value: {y_val:.1f}\n"
        if hasattr(bar, 'label'):
            text += f"Category: {bar.label}"
            
        self.hover_annotation = self.ax.annotate(
            text,
            xy=(x_val, y_val),
            xytext=(20, 20),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc=self.config.tooltip_bg),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
        
        self.canvas.draw_idle()
```

### Animation Support
```python
class AnimatedBarChart(BarChart):
    def animate_bars(self, duration: int = 1000):
        """Animate bars growing from zero"""
        # Store final heights
        final_heights = []
        for container in self.bar_containers:
            heights = [bar.get_height() for bar in container]
            final_heights.append(heights)
            # Set all bars to zero height
            for bar in container:
                bar.set_height(0)
                
        # Animate to final heights
        self.animation = BarGrowthAnimation(
            self.bar_containers,
            final_heights,
            duration
        )
        self.animation.start()
```

### Configuration
```python
@dataclass
class BarChartConfig:
    # Colors
    color_palette: List[str] = field(default_factory=lambda: [
        '#FF8C42', '#FFD166', '#F77F00', '#FCBF49', '#EAE2B7'
    ])
    
    # Bar styling
    bar_width: float = 0.8
    bar_alpha: float = 0.8
    edge_color: str = 'none'
    
    # Labels
    show_value_labels: bool = True
    label_font_size: int = 10
    label_color: str = '#333333'
    label_offset: float = 0.02  # Percentage of y-range
    
    # Legend
    show_legend: bool = True
    legend_location: str = 'upper right'
    
    # Grid
    show_grid: bool = True
    grid_alpha: float = 0.3
    
    # Animation
    animate: bool = True
    animation_duration: int = 800
    
    # Interactivity
    enable_hover: bool = True
    enable_selection: bool = True
    tooltip_bg: str = '#FFFEF7'
```

## Testing Requirements
- Unit tests for all chart types
- Visual regression tests
- Value label positioning tests
- Animation smoothness tests
- Interaction testing
- Performance with many bars
- Export quality validation

## Notes
- Ensure bars don't overlap
- Handle negative values properly
- Consider accessibility for colors
- Provide sorting options
- Plan for responsive sizing
- Document usage examples