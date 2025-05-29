---
task_id: G058
status: completed
created: 2025-05-28
last_updated: 2025-05-28 20:05
complexity: high
sprint_ref: S05_M01_Visualization
dependencies: []
parallel_group: foundation
---

# Task G058: Visualization Component Architecture

## Description
Establish the foundational architecture for visualization components including chart abstraction layers, theming system, and performance optimization patterns. This creates the backbone for all subsequent visualization work.

## Goals
- [x] Design modular visualization component architecture
- [x] Implement chart abstraction layer with multiple backends
- [x] Create WSJ-style theming and styling system
- [x] Build performance optimization framework for large datasets
- [x] Establish responsive design patterns for health visualizations
- [x] Create accessibility standards for health data charts

## Acceptance Criteria
- [x] Chart components support multiple rendering backends (matplotlib, plotly)
- [x] Theme system provides consistent WSJ styling across all charts
- [x] Components handle datasets up to 100K data points efficiently
- [x] All charts are WCAG 2.1 AA compliant
- [x] Responsive design works on displays from 1024px to 4K
- [x] Performance targets: <200ms render time, <100MB memory usage
- [x] Component API is consistent and intuitive for developers

## Technical Details

### Architecture Overview
```python
class VisualizationArchitecture:
    """Core visualization architecture following WSJ design principles"""
    
    def __init__(self):
        # Core rendering abstraction
        self.renderer_factory = ChartRendererFactory()
        
        # WSJ theming system
        self.theme_manager = WSJThemeManager()
        
        # Performance optimization
        self.performance_optimizer = ChartPerformanceOptimizer()
        
        # Accessibility compliance
        self.accessibility_manager = ChartAccessibilityManager()
        
        # Responsive design
        self.responsive_manager = ResponsiveChartManager()
```

### WSJ Color Scheme Integration
```python
class WSJThemeManager:
    """WSJ-inspired color theme management"""
    
    # Core WSJ colors from project specs
    COLORS = {
        'background': '#F5E6D3',  # Tan background
        'primary': '#FF8C42',     # Orange for main elements
        'secondary': '#FFD166',   # Yellow for accents
        'text': '#6B4226',        # Brown text
        'grid': '#E8D4BC',        # Light tan for grid lines
        'border': '#D4B5A0',      # Medium tan for borders
        'success': '#7CB342',     # Green for positive trends
        'warning': '#F4511E',     # Red-orange for alerts
        'info': '#5C6BC0'         # Blue-purple for information
    }
    
    # Chart-specific color palettes
    CHART_PALETTES = {
        'categorical': ['#FF8C42', '#FFD166', '#7CB342', '#5C6BC0', '#F4511E'],
        'sequential': ['#FFE5CC', '#FFD166', '#FFC142', '#FF8C42', '#E67C32'],
        'diverging': ['#F4511E', '#FF8C42', '#F5E6D3', '#7CB342', '#5CAD2C']
    }
```

### Implementation Approaches - Pros and Cons

#### Approach 1: PyQt6 with Matplotlib Backend
**Pros:**
- Native Qt integration with existing app
- Mature library with extensive documentation
- Good performance for static charts
- Publication-quality output

**Cons:**
- Limited interactivity out of the box
- Requires custom work for smooth animations
- Memory intensive for large datasets

**Implementation:**
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

class MatplotlibChartWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.figure = plt.figure(facecolor='#F5E6D3')
        super().__init__(self.figure)
        self.setParent(parent)
        self._apply_wsj_style()
```

#### Approach 2: PyQt6 with Plotly/Dash Integration
**Pros:**
- Rich interactive features built-in
- Smooth animations and transitions
- Good performance with WebGL
- Easy export to HTML

**Cons:**
- Requires QWebEngineView (heavier)
- Less control over fine styling details
- Potential security concerns with web content

**Implementation:**
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go

class PlotlyChartWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_config = self._create_wsj_theme()
```

#### Approach 3: Custom QPainter-based Rendering
**Pros:**
- Complete control over rendering
- Best performance for real-time updates
- Minimal dependencies
- Perfect Qt integration

**Cons:**
- More development work required
- Need to implement chart types from scratch
- Complex for statistical visualizations

**Implementation:**
```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush

class CustomChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wsj_colors = WSJThemeManager.COLORS
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_chart(painter)
```

### Recommended Hybrid Approach
Based on the project requirements and WSJ examples, I recommend a hybrid approach:

1. **Primary: Matplotlib for static charts** (like WSJ examples)
   - Time series line charts
   - Bar charts for comparisons
   - Clean, publication-quality output

2. **Secondary: Custom QPainter for real-time updates**
   - Live data streaming
   - Smooth animations
   - Interactive tooltips

3. **Tertiary: Plotly for complex interactivity**
   - 3D visualizations
   - Complex drill-downs
   - Export to web

### WSJ Color Scheme Integration
```python
class WSJThemeManager:
    """WSJ-inspired color theme management"""
    
    # Core WSJ colors from project specs
    COLORS = {
        'background': '#F5E6D3',  # Tan background
        'primary': '#FF8C42',     # Orange for main elements
        'secondary': '#FFD166',   # Yellow for accents
        'text': '#6B4226',        # Brown text
        'grid': '#E8D4BC',        # Light tan for grid lines
        'border': '#D4B5A0',      # Medium tan for borders
        'success': '#7CB342',     # Green for positive trends
        'warning': '#F4511E',     # Red-orange for alerts
        'info': '#5C6BC0'         # Blue-purple for information
    }
    
    # Chart-specific color palettes
    CHART_PALETTES = {
        'categorical': ['#FF8C42', '#FFD166', '#7CB342', '#5C6BC0', '#F4511E'],
        'sequential': ['#FFE5CC', '#FFD166', '#FFC142', '#FF8C42', '#E67C32'],
        'diverging': ['#F4511E', '#FF8C42', '#F5E6D3', '#7CB342', '#5CAD2C']
    }
```

### Implementation Approaches - Pros and Cons

#### Approach 1: PyQt6 with Matplotlib Backend
**Pros:**
- Native Qt integration with existing app
- Mature library with extensive documentation
- Good performance for static charts
- Publication-quality output

**Cons:**
- Limited interactivity out of the box
- Requires custom work for smooth animations
- Memory intensive for large datasets

**Implementation:**
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

class MatplotlibChartWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.figure = plt.figure(facecolor='#F5E6D3')
        super().__init__(self.figure)
        self.setParent(parent)
        self._apply_wsj_style()
```

#### Approach 2: PyQt6 with Plotly/Dash Integration
**Pros:**
- Rich interactive features built-in
- Smooth animations and transitions
- Good performance with WebGL
- Easy export to HTML

**Cons:**
- Requires QWebEngineView (heavier)
- Less control over fine styling details
- Potential security concerns with web content

**Implementation:**
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go

class PlotlyChartWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_config = self._create_wsj_theme()
```

#### Approach 3: Custom QPainter-based Rendering
**Pros:**
- Complete control over rendering
- Best performance for real-time updates
- Minimal dependencies
- Perfect Qt integration

**Cons:**
- More development work required
- Need to implement chart types from scratch
- Complex for statistical visualizations

**Implementation:**
```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush

class CustomChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wsj_colors = WSJThemeManager.COLORS
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_chart(painter)
```

### Recommended Hybrid Approach
Based on the project requirements and WSJ examples, I recommend a hybrid approach:

1. **Primary: Matplotlib for static charts** (like WSJ examples)
   - Time series line charts
   - Bar charts for comparisons
   - Clean, publication-quality output

2. **Secondary: Custom QPainter for real-time updates**
   - Live data streaming
   - Smooth animations
   - Interactive tooltips

3. **Tertiary: Plotly for complex interactivity**
   - 3D visualizations
   - Complex drill-downs
   - Export to web

### Component Hierarchy
```
BaseVisualizationComponent
├── TimeSeries
│   ├── LineChart
│   ├── AreaChart
│   └── StepChart
├── Categorical
│   ├── BarChart
│   ├── ColumnChart
│   └── HeatMap
├── Statistical
│   ├── BoxPlot
│   ├── Histogram
│   └── ScatterPlot
└── Composite
    ├── Dashboard
    ├── ComparisonChart
    └── MultiMetricView
```

## Dependencies
- None (foundation task)

## Parallel Work
- Can be developed in parallel with G059 (Real-time data binding)
- Prerequisite for all other visualization tasks

## Implementation Notes

### Best Practices from WSJ Examples

1. **Visual Hierarchy**
   - Bold, clear headlines (like "Trans-Atlantic Ties")
   - Subtle subheadings with context
   - Minimal chart decorations
   - Focus on data, not chrome

2. **Typography**
   - Sans-serif fonts for clarity
   - Consistent font sizes
   - High contrast text (#6B4226 on #F5E6D3)
   - Clear data labels

3. **Data Presentation**
   - Show exact values when precision matters
   - Use visual proportions (pie charts) for parts-of-whole
   - Combine multiple related metrics in one view
   - Add context (rankings, comparisons)

4. **Color Usage**
   - Limited palette (2-3 colors per chart)
   - Semantic colors (red for decrease, blue for increase)
   - High contrast between data series
   - Consistent color meanings across charts

### Practical Implementation Guide

```python
# src/ui/visualizations/wsj_chart_factory.py
class WSJChartFactory:
    """Factory for creating WSJ-styled charts"""
    
    @staticmethod
    def create_time_series_chart(data: pd.DataFrame, 
                                metric: str,
                                config: ChartConfig) -> TimeSeriesChart:
        """Create WSJ-styled time series chart"""
        
        chart = TimeSeriesChart()
        
        # Apply WSJ styling
        chart.set_background_color('#F5E6D3')
        chart.set_grid_style(color='#E8D4BC', style='dotted', alpha=0.5)
        
        # Configure axes
        chart.x_axis.set_label_style(color='#6B4226', size=10)
        chart.y_axis.set_label_style(color='#6B4226', size=10)
        
        # Set data with WSJ color
        chart.add_series(
            data=data,
            metric=metric,
            color='#FF8C42',
            line_width=2.5
        )
        
        # Add subtle annotations for key points
        chart.annotate_extremes(style='wsj_minimal')
        
        return chart

# src/ui/visualizations/wsj_dashboard_builder.py        
class WSJDashboardBuilder:
    """Builder for WSJ-styled multi-chart dashboards"""
    
    def build_daily_overview(self, data: pd.DataFrame) -> Dashboard:
        """Build daily health overview dashboard"""
        
        dashboard = Dashboard()
        dashboard.set_layout('grid', rows=2, cols=2)
        dashboard.set_background('#F5E6D3')
        
        # Heart rate chart (top-left)
        hr_chart = WSJChartFactory.create_time_series_chart(
            data, 'heart_rate', 
            ChartConfig(title='Heart Rate', subtitle='24-hour pattern')
        )
        dashboard.add_chart(hr_chart, row=0, col=0)
        
        # Steps chart (top-right) 
        steps_chart = WSJChartFactory.create_bar_chart(
            data, 'steps',
            ChartConfig(title='Daily Steps', subtitle='vs. goal')
        )
        dashboard.add_chart(steps_chart, row=0, col=1)
        
        # Sleep chart (bottom-left)
        sleep_chart = WSJChartFactory.create_timeline_chart(
            data, 'sleep_stages',
            ChartConfig(title='Sleep Quality', subtitle='stages & duration')
        )
        dashboard.add_chart(sleep_chart, row=1, col=0)
        
        # Activity chart (bottom-right)
        activity_chart = WSJChartFactory.create_donut_chart(
            data, 'activity_calories',
            ChartConfig(title='Activity Breakdown', subtitle='by type')
        )
        dashboard.add_chart(activity_chart, row=1, col=1)
        
        return dashboard
```

### Complete Implementation Example

```python
class WSJVisualizationComponent:
    """Base class for all WSJ-styled health visualization components."""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.accessibility_manager = ChartAccessibilityManager()
        self.performance_optimizer = ChartPerformanceOptimizer()
        
        # Configure matplotlib for WSJ style
        self._configure_matplotlib_style()
        
    def _configure_matplotlib_style(self):
        """Configure matplotlib with WSJ styling"""
        import matplotlib.pyplot as plt
        
        plt.rcParams.update({
            # Figure
            'figure.facecolor': '#F5E6D3',
            'figure.edgecolor': '#D4B5A0',
            
            # Axes
            'axes.facecolor': '#F5E6D3',
            'axes.edgecolor': '#D4B5A0',
            'axes.labelcolor': '#6B4226',
            'axes.grid': True,
            'axes.spines.top': False,
            'axes.spines.right': False,
            
            # Grid
            'grid.color': '#E8D4BC',
            'grid.linestyle': ':',
            'grid.alpha': 0.5,
            
            # Text
            'text.color': '#6B4226',
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans'],
            
            # Lines
            'lines.linewidth': 2.5,
            'lines.antialiased': True,
            
            # Patches
            'patch.facecolor': '#FF8C42',
            'patch.edgecolor': '#E67C32'
        })
        
    def render(self, data: pd.DataFrame, config: ChartConfig) -> ChartResult:
        """Render chart with full WSJ optimization stack."""
        
        # Apply performance optimizations
        optimized_data = self.performance_optimizer.optimize_data(data)
        
        # Apply WSJ theming
        styled_config = self.theme_manager.apply_theme(config)
        
        # Ensure accessibility compliance
        accessible_config = self.accessibility_manager.enhance_config(styled_config)
        
        # Render with backend
        return self._render_with_backend(optimized_data, accessible_config)
        
    def make_responsive(self, container_size: Tuple[int, int]) -> None:
        """Apply responsive design based on container size."""
        width, height = container_size
        
        if width < 1024:  # Tablet
            self._apply_tablet_layout()
        elif width < 1440:  # Small desktop
            self._apply_small_desktop_layout()
        elif width < 2560:  # Standard desktop
            self._apply_standard_desktop_layout()
        else:  # Large desktop
            self._apply_large_desktop_layout()
```

### Best Practices from WSJ Examples

1. **Visual Hierarchy**
   - Bold, clear headlines (like "Trans-Atlantic Ties")
   - Subtle subheadings with context
   - Minimal chart decorations
   - Focus on data, not chrome

2. **Typography**
   - Sans-serif fonts for clarity
   - Consistent font sizes
   - High contrast text (#6B4226 on #F5E6D3)
   - Clear data labels

3. **Data Presentation**
   - Show exact values when precision matters
   - Use visual proportions (pie charts) for parts-of-whole
   - Combine multiple related metrics in one view
   - Add context (rankings, comparisons)

4. **Color Usage**
   - Limited palette (2-3 colors per chart)
   - Semantic colors (red for decrease, blue for increase)
   - High contrast between data series
   - Consistent color meanings across charts

### Practical Implementation Guide

```python
# src/ui/visualizations/wsj_chart_factory.py
class WSJChartFactory:
    """Factory for creating WSJ-styled charts"""
    
    @staticmethod
    def create_time_series_chart(data: pd.DataFrame, 
                                metric: str,
                                config: ChartConfig) -> TimeSeriesChart:
        """Create WSJ-styled time series chart"""
        
        chart = TimeSeriesChart()
        
        # Apply WSJ styling
        chart.set_background_color('#F5E6D3')
        chart.set_grid_style(color='#E8D4BC', style='dotted', alpha=0.5)
        
        # Configure axes
        chart.x_axis.set_label_style(color='#6B4226', size=10)
        chart.y_axis.set_label_style(color='#6B4226', size=10)
        
        # Set data with WSJ color
        chart.add_series(
            data=data,
            metric=metric,
            color='#FF8C42',
            line_width=2.5
        )
        
        # Add subtle annotations for key points
        chart.annotate_extremes(style='wsj_minimal')
        
        return chart

# src/ui/visualizations/wsj_dashboard_builder.py        
class WSJDashboardBuilder:
    """Builder for WSJ-styled multi-chart dashboards"""
    
    def build_daily_overview(self, data: pd.DataFrame) -> Dashboard:
        """Build daily health overview dashboard"""
        
        dashboard = Dashboard()
        dashboard.set_layout('grid', rows=2, cols=2)
        dashboard.set_background('#F5E6D3')
        
        # Heart rate chart (top-left)
        hr_chart = WSJChartFactory.create_time_series_chart(
            data, 'heart_rate', 
            ChartConfig(title='Heart Rate', subtitle='24-hour pattern')
        )
        dashboard.add_chart(hr_chart, row=0, col=0)
        
        # Steps chart (top-right) 
        steps_chart = WSJChartFactory.create_bar_chart(
            data, 'steps',
            ChartConfig(title='Daily Steps', subtitle='vs. goal')
        )
        dashboard.add_chart(steps_chart, row=0, col=1)
        
        # Sleep chart (bottom-left)
        sleep_chart = WSJChartFactory.create_timeline_chart(
            data, 'sleep_stages',
            ChartConfig(title='Sleep Quality', subtitle='stages & duration')
        )
        dashboard.add_chart(sleep_chart, row=1, col=0)
        
        # Activity chart (bottom-right)
        activity_chart = WSJChartFactory.create_donut_chart(
            data, 'activity_calories',
            ChartConfig(title='Activity Breakdown', subtitle='by type')
        )
        dashboard.add_chart(activity_chart, row=1, col=1)
        
        return dashboard
```
## Claude Output Log
[2025-05-28 18:06]: Task status updated to in_progress
[2025-05-28 18:13]: Created chart renderer factory with support for matplotlib, qpainter, pyqtgraph, and plotly backends
[2025-05-28 18:13]: Implemented QPainter chart widget for high-performance real-time rendering
[2025-05-28 18:20]: Created chart performance optimizer with LTTB downsampling and adaptive viewport sampling
[2025-05-28 18:20]: Implemented accessibility manager ensuring WCAG 2.1 AA compliance
[2025-05-28 18:20]: Built responsive chart manager supporting phone to ultra-wide displays
[2025-05-28 18:25]: Created enhanced base chart integrating all components
[2025-05-28 18:25]: Implemented comprehensive example showing usage of the new architecture
[2025-05-28 20:03]: CODE REVIEW RESULT: **PASS**
- **Scope:** Task G058 - Visualization Component Architecture
- **Findings:** No deviations found. All requirements met.
- **Summary:** Implementation perfectly aligns with specifications. All colors match SPECS_UI.md, WCAG compliance is properly enforced, all required features are implemented.
- **Recommendation:** Proceed with task completion.
[2025-05-28 20:05]: Task completed successfully. All acceptance criteria met.
