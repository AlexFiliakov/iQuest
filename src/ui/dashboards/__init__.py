"""Advanced dashboard layout system for multi-metric health data visualization.

This module provides sophisticated dashboard management capabilities that enable users
to create, customize, and interact with comprehensive health monitoring interfaces.
The dashboard system combines multiple visualizations into cohesive, responsive
layouts that adapt to different screen sizes and user preferences.

The dashboard system includes:

- **WSJ-Inspired Layouts**: Professional grid-based layouts with Wall Street Journal styling
- **Responsive Design**: Automatic adaptation to different screen sizes and orientations
- **Template System**: Pre-configured dashboard templates for common health monitoring scenarios
- **Interactive Coordination**: Synchronized interactions across multiple charts and visualizations
- **Customization Engine**: User-configurable layouts with drag-and-drop functionality
- **Performance Optimization**: Efficient rendering and updates for complex multi-chart dashboards

Key Features:
- **Flexible Grid System**: CSS-Grid inspired layout with automatic sizing and spacing
- **Chart Coordination**: Linked brushing, zooming, and filtering across multiple visualizations
- **Template Library**: Pre-built dashboards for fitness tracking, health monitoring, and clinical analysis
- **Responsive Breakpoints**: Optimized layouts for desktop, tablet, and mobile viewing
- **Accessibility Integration**: Full keyboard navigation and screen reader support
- **Export Capabilities**: Dashboard-wide export to PDF, HTML, and image formats

The dashboard system follows responsive design principles and provides both
predefined templates and complete customization flexibility for power users.

Example:
    Creating a comprehensive health dashboard:
    
    >>> from ui.dashboards import WSJDashboardLayout, HealthDashboardTemplates
    >>> layout = WSJDashboardLayout()
    >>> template = HealthDashboardTemplates.FITNESS_OVERVIEW
    >>> dashboard = layout.create_dashboard(template)
    >>> dashboard.add_chart('steps', chart_config)
    >>> dashboard.add_chart('heart_rate', chart_config)
    
    Setting up responsive grid management:
    
    >>> from ui.dashboards import ResponsiveGridManager
    >>> grid_manager = ResponsiveGridManager()
    >>> grid_manager.configure_breakpoints({'mobile': 480, 'tablet': 768, 'desktop': 1024})
    >>> grid_manager.apply_responsive_layout(dashboard)

Note:
    All dashboard layouts maintain visual consistency with the WSJ design language
    and provide smooth animations and transitions between different configurations.
"""

from .wsj_dashboard_layout import WSJDashboardLayout
from .health_dashboard_templates import HealthDashboardTemplates
from .responsive_grid_manager import ResponsiveGridManager
from .dashboard_models import (
    GridSpec,
    ChartConfig,
    DashboardTemplate,
    GridConfiguration
)
from .dashboard_interaction_coordinator import DashboardInteractionCoordinator

__all__ = [
    'WSJDashboardLayout',
    'HealthDashboardTemplates',
    'ResponsiveGridManager',
    'GridSpec',
    'ChartConfig',
    'DashboardTemplate',
    'GridConfiguration',
    'DashboardInteractionCoordinator'
]