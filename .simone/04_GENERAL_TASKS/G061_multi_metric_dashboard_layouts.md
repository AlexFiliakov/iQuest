---
task_id: G061
status: open
created: 2025-05-28
complexity: medium
sprint_ref: S05_M01_Visualization
dependencies: [G058]
parallel_group: interactive
---

# Task G061: Multi-Metric Dashboard Layouts

## Description
Create flexible dashboard layouts that display multiple health metrics simultaneously with intelligent positioning, responsive design, and coordinated interactions. Focus on WSJ-style grid layouts with health data storytelling.

## Goals
- [ ] Design flexible grid layout system for health dashboards
- [ ] Implement responsive breakpoints for different screen sizes
- [ ] Create metric correlation displays with synchronized views
- [ ] Build dashboard templates for common health scenarios
- [ ] Add drag-and-drop dashboard customization
- [ ] Implement layout persistence and sharing

## Acceptance Criteria
- [ ] Supports 1-12 chart grid layouts with automatic sizing
- [ ] Responsive design works on 1024px to 4K displays
- [ ] Charts maintain aspect ratios and readability at all sizes
- [ ] Synchronized interactions across all dashboard charts
- [ ] Layout customization saves to user preferences
- [ ] Dashboard exports work for sharing and reporting
- [ ] Performance remains smooth with up to 12 active charts

## Technical Details

### Dashboard Layout Architecture
```python
class HealthDashboardManager:
    """Manages multi-metric health dashboard layouts"""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.layout_engine = ResponsiveLayoutEngine()
        self.interaction_coordinator = DashboardInteractionCoordinator()
        self.template_manager = DashboardTemplateManager()
        
    def create_dashboard(self, metrics: List[str], 
                        layout_config: LayoutConfig) -> HealthDashboard:
        """Create new multi-metric dashboard"""
        pass
        
    def apply_template(self, template_name: str, 
                      data_context: HealthDataContext) -> HealthDashboard:
        """Apply pre-built dashboard template"""
        pass
```

### Responsive Grid System
- **Breakpoints**: 1024px (tablet), 1440px (desktop), 2560px (large)
- **Grid Units**: 12-column flexible grid with health-optimized aspect ratios
- **Chart Sizing**: Intelligent minimum sizes based on chart type and data density
- **Typography Scaling**: Responsive text sizing for readability

### Dashboard Templates
1. **Daily Overview**: Steps, heart rate, sleep, active calories
2. **Activity Focus**: Workouts, active energy, exercise minutes, zones
3. **Health Monitoring**: Heart rate variability, resting HR, blood pressure
4. **Sleep Analysis**: Sleep stages, efficiency, heart rate during sleep
5. **Trend Analysis**: Week/month comparisons across key metrics

### WSJ-Style Layout Principles

Based on the WSJ chart examples:

1. **Information Density**
   - Multiple related metrics in single view
   - Efficient use of space without crowding
   - Clear visual hierarchy

2. **Grid System**
   ```python
   class WSJGridSystem:
       # Based on 12-column grid like WSJ
       GRID_COLUMNS = 12
       GUTTER_WIDTH = 16  # pixels
       MARGIN = 24  # pixels
       
       # Responsive breakpoints
       BREAKPOINTS = {
           'mobile': 768,
           'tablet': 1024,
           'desktop': 1440,
           'wide': 1920
       }
   ```

3. **Chart Sizing Rules**
   - Primary chart: 8-12 columns
   - Secondary charts: 4-6 columns
   - Supporting metrics: 2-4 columns
   - Maintain golden ratio (1.618) when possible

### Implementation Approaches - Pros and Cons

#### Approach 1: CSS Grid with Qt WebEngine
**Pros:**
- Modern, flexible layout system
- Easy responsive design
- Familiar to web developers
- Natural for Plotly integration

**Cons:**
- Requires QWebEngineView
- Heavier resource usage
- Less native feel

#### Approach 2: QGridLayout with Custom Widgets
**Pros:**
- Native Qt performance
- Full control over rendering
- Lightweight
- Better integration with app

**Cons:**
- More complex responsive logic
- Manual size calculations
- Less flexible for complex layouts

#### Approach 3: QGraphicsView Framework
**Pros:**
- Powerful scene management
- Smooth animations
- Good for complex interactions
- Efficient for many items

**Cons:**
- Steeper learning curve
- Overkill for simple layouts
- More memory overhead

### Recommended Approach
Based on project requirements, I recommend **QGridLayout with custom sizing logic**:
- Best performance for health data updates
- Native Qt integration
- Predictable behavior
- Easy to implement WSJ grid system

### WSJ-Style Layout Principles

Based on the WSJ chart examples:

1. **Information Density**
   - Multiple related metrics in single view
   - Efficient use of space without crowding
   - Clear visual hierarchy

2. **Grid System**
   ```python
   class WSJGridSystem:
       # Based on 12-column grid like WSJ
       GRID_COLUMNS = 12
       GUTTER_WIDTH = 16  # pixels
       MARGIN = 24  # pixels
       
       # Responsive breakpoints
       BREAKPOINTS = {
           'mobile': 768,
           'tablet': 1024,
           'desktop': 1440,
           'wide': 1920
       }
   ```

3. **Chart Sizing Rules**
   - Primary chart: 8-12 columns
   - Secondary charts: 4-6 columns
   - Supporting metrics: 2-4 columns
   - Maintain golden ratio (1.618) when possible

### Implementation Approaches - Pros and Cons

#### Approach 1: CSS Grid with Qt WebEngine
**Pros:**
- Modern, flexible layout system
- Easy responsive design
- Familiar to web developers
- Natural for Plotly integration

**Cons:**
- Requires QWebEngineView
- Heavier resource usage
- Less native feel

#### Approach 2: QGridLayout with Custom Widgets
**Pros:**
- Native Qt performance
- Full control over rendering
- Lightweight
- Better integration with app

**Cons:**
- More complex responsive logic
- Manual size calculations
- Less flexible for complex layouts

#### Approach 3: QGraphicsView Framework
**Pros:**
- Powerful scene management
- Smooth animations
- Good for complex interactions
- Efficient for many items

**Cons:**
- Steeper learning curve
- Overkill for simple layouts
- More memory overhead

### Recommended Approach
Based on project requirements, I recommend **QGridLayout with custom sizing logic**:
- Best performance for health data updates
- Native Qt integration
- Predictable behavior
- Easy to implement WSJ grid system

## Dependencies
- G058: Visualization Component Architecture

## Parallel Work
- Can be developed in parallel with G060 (Interactive controls)
- Works together with G062 (Health insights)

## Implementation Notes

### Practical Dashboard Implementation

```python
# src/ui/visualizations/dashboards/wsj_dashboard_layout.py
from PyQt6.QtWidgets import QWidget, QGridLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from typing import List, Dict, Tuple
import math

class WSJDashboardLayout(QWidget):
    """WSJ-styled responsive dashboard layout"""
    
    # Signals
    layout_changed = pyqtSignal(str)  # layout_name
    chart_focused = pyqtSignal(str)  # chart_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts: Dict[str, ChartWidget] = {}
        self.current_layout = 'default'
        self.grid_layout = QGridLayout(self)
        self._setup_wsj_styling()
        
    def _setup_wsj_styling(self):
        """Apply WSJ styling to dashboard"""
        self.setStyleSheet(f"""
            WSJDashboardLayout {{
                background-color: #F5E6D3;
                border: 1px solid #D4B5A0;
            }}
        """)
        
        # Grid spacing matching WSJ
        self.grid_layout.setSpacing(16)  # Gutter
        self.grid_layout.setContentsMargins(24, 24, 24, 24)  # Margins
        
    def add_chart(self, chart_id: str, chart: ChartWidget, 
                  grid_spec: GridSpec) -> None:
        """Add chart to dashboard with grid specification"""
        
        self.charts[chart_id] = chart
        
        # Apply WSJ chart frame
        chart.setFrameStyle(QFrame.Shape.Box)
        chart.setStyleSheet("""
            ChartWidget {
                background-color: white;
                border: 1px solid #E8D4BC;
                border-radius: 4px;
            }
        """)
        
        # Add to grid
        self.grid_layout.addWidget(
            chart,
            grid_spec.row,
            grid_spec.col,
            grid_spec.row_span,
            grid_spec.col_span
        )
        
        # Set size policy for responsive behavior
        chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
    def apply_layout_template(self, template: DashboardTemplate) -> None:
        """Apply predefined dashboard template"""
        
        # Clear existing layout
        self._clear_layout()
        
        # Apply new template
        for chart_config in template.chart_configs:
            chart = self._create_chart_for_metric(chart_config.metric_type)
            self.add_chart(
                chart_config.chart_id,
                chart,
                chart_config.grid_spec
            )
            
        self.current_layout = template.name
        self.layout_changed.emit(template.name)
        
    def optimize_for_size(self, width: int, height: int) -> None:
        """Optimize layout for current window size"""
        
        if width < 768:  # Mobile
            self._apply_mobile_layout()
        elif width < 1024:  # Tablet
            self._apply_tablet_layout()
        elif width < 1440:  # Desktop
            self._apply_desktop_layout()
        else:  # Wide
            self._apply_wide_layout()
            
    def _apply_mobile_layout(self):
        """Stack all charts vertically for mobile"""
        
        row = 0
        for chart_id, chart in self.charts.items():
            self.grid_layout.removeWidget(chart)
            self.grid_layout.addWidget(chart, row, 0, 1, 12)
            row += 1
            
    def _apply_desktop_layout(self):
        """Apply standard desktop grid layout"""
        
        # Primary chart takes 8 columns
        if 'primary' in self.charts:
            self.grid_layout.addWidget(
                self.charts['primary'], 0, 0, 2, 8
            )
            
        # Secondary charts in 4-column sidebar
        row = 0
        for chart_id, chart in self.charts.items():
            if chart_id != 'primary':
                self.grid_layout.addWidget(
                    chart, row, 8, 1, 4
                )
                row += 1

# src/ui/visualizations/dashboards/health_dashboard_templates.py                
class HealthDashboardTemplates:
    """Predefined dashboard templates for health data"""
    
    @staticmethod
    def daily_overview() -> DashboardTemplate:
        """Daily health overview template"""
        
        return DashboardTemplate(
            name='daily_overview',
            title='Daily Health Overview',
            chart_configs=[
                ChartConfig(
                    chart_id='heart_rate_trend',
                    metric_type='heart_rate',
                    chart_type='time_series',
                    grid_spec=GridSpec(0, 0, 2, 6),  # Top left, half width
                    config={
                        'title': 'Heart Rate',
                        'subtitle': '24-hour trend',
                        'show_zones': True
                    }
                ),
                ChartConfig(
                    chart_id='steps_progress',
                    metric_type='steps',
                    chart_type='progress_bar',
                    grid_spec=GridSpec(0, 6, 1, 6),  # Top right
                    config={
                        'title': 'Daily Steps',
                        'subtitle': 'vs. goal',
                        'goal': 10000
                    }
                ),
                ChartConfig(
                    chart_id='activity_rings',
                    metric_type='activity',
                    chart_type='ring_chart',
                    grid_spec=GridSpec(1, 6, 1, 6),  # Middle right
                    config={
                        'title': 'Activity',
                        'metrics': ['move', 'exercise', 'stand']
                    }
                ),
                ChartConfig(
                    chart_id='sleep_timeline',
                    metric_type='sleep',
                    chart_type='timeline',
                    grid_spec=GridSpec(2, 0, 1, 12),  # Bottom full width
                    config={
                        'title': 'Sleep Analysis',
                        'show_stages': True,
                        'show_quality_score': True
                    }
                )
            ]
        )
        
    @staticmethod
    def weekly_trends() -> DashboardTemplate:
        """Weekly trend analysis template"""
        
        return DashboardTemplate(
            name='weekly_trends',
            title='Weekly Health Trends',
            chart_configs=[
                ChartConfig(
                    chart_id='multi_metric_trend',
                    metric_type='multiple',
                    chart_type='multi_line',
                    grid_spec=GridSpec(0, 0, 2, 8),  # Large left chart
                    config={
                        'title': 'Weekly Trends',
                        'metrics': ['steps', 'active_calories', 'exercise_minutes'],
                        'normalize': True
                    }
                ),
                ChartConfig(
                    chart_id='week_comparison',
                    metric_type='comparison',
                    chart_type='bar_comparison',
                    grid_spec=GridSpec(0, 8, 1, 4),  # Top right
                    config={
                        'title': 'This Week vs Last',
                        'metrics': ['steps', 'calories', 'distance']
                    }
                ),
                ChartConfig(
                    chart_id='day_patterns',
                    metric_type='patterns',
                    chart_type='heatmap',
                    grid_spec=GridSpec(1, 8, 1, 4),  # Bottom right
                    config={
                        'title': 'Day of Week Patterns',
                        'metric': 'activity_level'
                    }
                )
            ]
        )

# src/ui/visualizations/dashboards/responsive_grid_manager.py
class ResponsiveGridManager:
    """Manages responsive grid behavior for dashboards"""
    
    def __init__(self, dashboard: WSJDashboardLayout):
        self.dashboard = dashboard
        self.current_breakpoint = 'desktop'
        
    def calculate_optimal_layout(self, container_size: QSize, 
                               chart_count: int) -> GridConfiguration:
        """Calculate optimal grid configuration"""
        
        width = container_size.width()
        height = container_size.height()
        
        # Determine breakpoint
        breakpoint = self._get_breakpoint(width)
        
        # Calculate grid dimensions
        if breakpoint == 'mobile':
            return self._mobile_grid(chart_count)
        elif breakpoint == 'tablet':
            return self._tablet_grid(chart_count, height)
        else:
            return self._desktop_grid(chart_count, width, height)
            
    def _get_breakpoint(self, width: int) -> str:
        """Determine current responsive breakpoint"""
        
        if width < 768:
            return 'mobile'
        elif width < 1024:
            return 'tablet'
        elif width < 1440:
            return 'desktop'
        else:
            return 'wide'
            
    def _desktop_grid(self, chart_count: int, width: int, height: int) -> GridConfiguration:
        """Calculate desktop grid configuration"""
        
        # Use golden ratio for primary chart
        primary_width = int(width * 0.618)
        primary_height = int(primary_width / 1.618)
        
        # Calculate secondary chart dimensions
        secondary_width = width - primary_width - 16  # minus gutter
        secondary_height = (height - 48) // (chart_count - 1)  # minus margins
        
        return GridConfiguration(
            primary_size=(primary_width, primary_height),
            secondary_size=(secondary_width, secondary_height),
            layout='sidebar'
        )
```

### Practical Dashboard Implementation

```python
# src/ui/visualizations/dashboards/wsj_dashboard_layout.py
from PyQt6.QtWidgets import QWidget, QGridLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from typing import List, Dict, Tuple
import math

class WSJDashboardLayout(QWidget):
    """WSJ-styled responsive dashboard layout"""
    
    # Signals
    layout_changed = pyqtSignal(str)  # layout_name
    chart_focused = pyqtSignal(str)  # chart_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts: Dict[str, ChartWidget] = {}
        self.current_layout = 'default'
        self.grid_layout = QGridLayout(self)
        self._setup_wsj_styling()
        
    def _setup_wsj_styling(self):
        """Apply WSJ styling to dashboard"""
        self.setStyleSheet(f"""
            WSJDashboardLayout {{
                background-color: #F5E6D3;
                border: 1px solid #D4B5A0;
            }}
        """)
        
        # Grid spacing matching WSJ
        self.grid_layout.setSpacing(16)  # Gutter
        self.grid_layout.setContentsMargins(24, 24, 24, 24)  # Margins
        
    def add_chart(self, chart_id: str, chart: ChartWidget, 
                  grid_spec: GridSpec) -> None:
        """Add chart to dashboard with grid specification"""
        
        self.charts[chart_id] = chart
        
        # Apply WSJ chart frame
        chart.setFrameStyle(QFrame.Shape.Box)
        chart.setStyleSheet("""
            ChartWidget {
                background-color: white;
                border: 1px solid #E8D4BC;
                border-radius: 4px;
            }
        """)
        
        # Add to grid
        self.grid_layout.addWidget(
            chart,
            grid_spec.row,
            grid_spec.col,
            grid_spec.row_span,
            grid_spec.col_span
        )
        
        # Set size policy for responsive behavior
        chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
    def apply_layout_template(self, template: DashboardTemplate) -> None:
        """Apply predefined dashboard template"""
        
        # Clear existing layout
        self._clear_layout()
        
        # Apply new template
        for chart_config in template.chart_configs:
            chart = self._create_chart_for_metric(chart_config.metric_type)
            self.add_chart(
                chart_config.chart_id,
                chart,
                chart_config.grid_spec
            )
            
        self.current_layout = template.name
        self.layout_changed.emit(template.name)
        
    def optimize_for_size(self, width: int, height: int) -> None:
        """Optimize layout for current window size"""
        
        if width < 768:  # Mobile
            self._apply_mobile_layout()
        elif width < 1024:  # Tablet
            self._apply_tablet_layout()
        elif width < 1440:  # Desktop
            self._apply_desktop_layout()
        else:  # Wide
            self._apply_wide_layout()
            
    def _apply_mobile_layout(self):
        """Stack all charts vertically for mobile"""
        
        row = 0
        for chart_id, chart in self.charts.items():
            self.grid_layout.removeWidget(chart)
            self.grid_layout.addWidget(chart, row, 0, 1, 12)
            row += 1
            
    def _apply_desktop_layout(self):
        """Apply standard desktop grid layout"""
        
        # Primary chart takes 8 columns
        if 'primary' in self.charts:
            self.grid_layout.addWidget(
                self.charts['primary'], 0, 0, 2, 8
            )
            
        # Secondary charts in 4-column sidebar
        row = 0
        for chart_id, chart in self.charts.items():
            if chart_id != 'primary':
                self.grid_layout.addWidget(
                    chart, row, 8, 1, 4
                )
                row += 1

# src/ui/visualizations/dashboards/health_dashboard_templates.py                
class HealthDashboardTemplates:
    """Predefined dashboard templates for health data"""
    
    @staticmethod
    def daily_overview() -> DashboardTemplate:
        """Daily health overview template"""
        
        return DashboardTemplate(
            name='daily_overview',
            title='Daily Health Overview',
            chart_configs=[
                ChartConfig(
                    chart_id='heart_rate_trend',
                    metric_type='heart_rate',
                    chart_type='time_series',
                    grid_spec=GridSpec(0, 0, 2, 6),  # Top left, half width
                    config={
                        'title': 'Heart Rate',
                        'subtitle': '24-hour trend',
                        'show_zones': True
                    }
                ),
                ChartConfig(
                    chart_id='steps_progress',
                    metric_type='steps',
                    chart_type='progress_bar',
                    grid_spec=GridSpec(0, 6, 1, 6),  # Top right
                    config={
                        'title': 'Daily Steps',
                        'subtitle': 'vs. goal',
                        'goal': 10000
                    }
                ),
                ChartConfig(
                    chart_id='activity_rings',
                    metric_type='activity',
                    chart_type='ring_chart',
                    grid_spec=GridSpec(1, 6, 1, 6),  # Middle right
                    config={
                        'title': 'Activity',
                        'metrics': ['move', 'exercise', 'stand']
                    }
                ),
                ChartConfig(
                    chart_id='sleep_timeline',
                    metric_type='sleep',
                    chart_type='timeline',
                    grid_spec=GridSpec(2, 0, 1, 12),  # Bottom full width
                    config={
                        'title': 'Sleep Analysis',
                        'show_stages': True,
                        'show_quality_score': True
                    }
                )
            ]
        )
        
    @staticmethod
    def weekly_trends() -> DashboardTemplate:
        """Weekly trend analysis template"""
        
        return DashboardTemplate(
            name='weekly_trends',
            title='Weekly Health Trends',
            chart_configs=[
                ChartConfig(
                    chart_id='multi_metric_trend',
                    metric_type='multiple',
                    chart_type='multi_line',
                    grid_spec=GridSpec(0, 0, 2, 8),  # Large left chart
                    config={
                        'title': 'Weekly Trends',
                        'metrics': ['steps', 'active_calories', 'exercise_minutes'],
                        'normalize': True
                    }
                ),
                ChartConfig(
                    chart_id='week_comparison',
                    metric_type='comparison',
                    chart_type='bar_comparison',
                    grid_spec=GridSpec(0, 8, 1, 4),  # Top right
                    config={
                        'title': 'This Week vs Last',
                        'metrics': ['steps', 'calories', 'distance']
                    }
                ),
                ChartConfig(
                    chart_id='day_patterns',
                    metric_type='patterns',
                    chart_type='heatmap',
                    grid_spec=GridSpec(1, 8, 1, 4),  # Bottom right
                    config={
                        'title': 'Day of Week Patterns',
                        'metric': 'activity_level'
                    }
                )
            ]
        )

# src/ui/visualizations/dashboards/responsive_grid_manager.py
class ResponsiveGridManager:
    """Manages responsive grid behavior for dashboards"""
    
    def __init__(self, dashboard: WSJDashboardLayout):
        self.dashboard = dashboard
        self.current_breakpoint = 'desktop'
        
    def calculate_optimal_layout(self, container_size: QSize, 
                               chart_count: int) -> GridConfiguration:
        """Calculate optimal grid configuration"""
        
        width = container_size.width()
        height = container_size.height()
        
        # Determine breakpoint
        breakpoint = self._get_breakpoint(width)
        
        # Calculate grid dimensions
        if breakpoint == 'mobile':
            return self._mobile_grid(chart_count)
        elif breakpoint == 'tablet':
            return self._tablet_grid(chart_count, height)
        else:
            return self._desktop_grid(chart_count, width, height)
            
    def _get_breakpoint(self, width: int) -> str:
        """Determine current responsive breakpoint"""
        
        if width < 768:
            return 'mobile'
        elif width < 1024:
            return 'tablet'
        elif width < 1440:
            return 'desktop'
        else:
            return 'wide'
            
    def _desktop_grid(self, chart_count: int, width: int, height: int) -> GridConfiguration:
        """Calculate desktop grid configuration"""
        
        # Use golden ratio for primary chart
        primary_width = int(width * 0.618)
        primary_height = int(primary_width / 1.618)
        
        # Calculate secondary chart dimensions
        secondary_width = width - primary_width - 16  # minus gutter
        secondary_height = (height - 48) // (chart_count - 1)  # minus margins
        
        return GridConfiguration(
            primary_size=(primary_width, primary_height),
            secondary_size=(secondary_width, secondary_height),
            layout='sidebar'
        )
```