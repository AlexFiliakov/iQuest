"""Advanced chart interaction components for health data visualization.

This module provides sophisticated interactive controls that transform static health
visualizations into dynamic, explorable interfaces. The interaction system enables
users to deeply engage with their health data through intuitive gestures, keyboard
shortcuts, and contextual navigation.

The interaction components include:

- **Zoom and Pan Controls**: Smooth, multi-scale navigation with momentum and boundaries
- **Brush Selection**: Precise date range selection with visual feedback and snapping
- **Rich Tooltips**: Contextual health insights with WSJ-inspired styling and formatting
- **Drill-Down Navigation**: Progressive disclosure from overview to detailed metrics
- **Crossfilter Interactions**: Linked charts with coordinated filtering and highlighting
- **Keyboard Navigation**: Complete accessibility support with logical tab ordering
- **Performance Monitoring**: Real-time interaction performance tracking and optimization

All interaction components are designed to:
- **Enhance Understanding**: Reveal insights through exploration and comparison
- **Maintain Performance**: Smooth 60fps interactions even with large datasets
- **Support Accessibility**: Full keyboard and assistive technology compatibility
- **Follow Standards**: Consistent interaction patterns across all chart types

The interaction system follows principles from Edward Tufte's information design
and Ben Shneiderman's information seeking mantra: "Overview first, zoom and filter,
then details on demand."

Example:
    Setting up comprehensive chart interactions:
    
    >>> from ui.charts.interactions import ChartInteractionManager
    >>> interaction_manager = ChartInteractionManager(chart_widget)
    >>> interaction_manager.enable_zoom_pan()
    >>> interaction_manager.enable_brush_selection()
    >>> interaction_manager.enable_tooltips()
    
    Configuring drill-down navigation:
    
    >>> from ui.charts.interactions import DrillDownNavigator
    >>> navigator = DrillDownNavigator()
    >>> navigator.configure_levels(['yearly', 'monthly', 'daily', 'hourly'])
    >>> navigator.attach_to_chart(chart_widget)

Note:
    All interactions preserve data integrity and maintain visual consistency
    with the overall WSJ-inspired design language of the application.
"""

from .chart_interaction_manager import ChartInteractionManager
from .zoom_controller import SmoothZoomController
from .brush_selector import BrushRangeSelector
from .wsj_tooltip import WSJTooltip
from .keyboard_navigation import KeyboardNavigationHandler
from .crossfilter_manager import CrossfilterManager
from .drill_down_navigator import DrillDownNavigator
from .performance_monitor import InteractionPerformanceMonitor

__all__ = [
    'ChartInteractionManager',
    'SmoothZoomController',
    'BrushRangeSelector',
    'WSJTooltip',
    'KeyboardNavigationHandler',
    'CrossfilterManager',
    'DrillDownNavigator',
    'InteractionPerformanceMonitor'
]