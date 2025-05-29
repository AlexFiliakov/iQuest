"""
Chart components for Apple Health Monitor.

This module provides visualization components for health data with WSJ-inspired styling.
"""

from .base_chart import BaseChart
from .line_chart import LineChart
from .chart_config import ChartConfig, LineChartConfig, LineChartBuilder
from .enhanced_line_chart import EnhancedLineChart
from .wsj_style_manager import WSJStyleManager
from .pyqtgraph_chart_factory import PyQtGraphChartFactory
from .matplotlib_chart_factory import MatplotlibChartFactory
from .wsj_health_visualization_suite import WSJHealthVisualizationSuite
from .progressive_drill_down import ProgressiveDrillDownWidget
from .shareable_dashboard import (ShareableDashboardManager, ShareDashboardDialog,
                                ShareLinkDisplay, SharedDashboardViewer)

# Import interaction components
from .interactions import (
    ChartInteractionManager,
    SmoothZoomController,
    BrushRangeSelector,
    WSJTooltip,
    KeyboardNavigationHandler,
    CrossfilterManager,
    DrillDownNavigator
)

# Import accessibility components
from ..accessibility import (
    VisualizationAccessibilityManager,
    AccessibleChart,
    WCAGValidator
)
from ..accessibility.accessible_chart_mixin import AccessibleChartMixin

# Import export components
from .export import (
    ExportFormat, WSJExportManager, VisualizationShareManager,
    PrintLayoutManager, HTMLExportBuilder
)

__all__ = [
    'BaseChart', 
    'LineChart',
    'ChartConfig',
    'LineChartConfig', 
    'LineChartBuilder',
    'EnhancedLineChart',
    'WSJStyleManager',
    'PyQtGraphChartFactory',
    'MatplotlibChartFactory',
    'WSJHealthVisualizationSuite',
    'ProgressiveDrillDownWidget',
    'ShareableDashboardManager',
    'ShareDashboardDialog',
    'ShareLinkDisplay',
    'SharedDashboardViewer',
    # Accessibility exports
    'VisualizationAccessibilityManager',
    'AccessibleChart',
    'WCAGValidator',
    'AccessibleChartMixin',
    # Interaction exports
    'ChartInteractionManager',
    'SmoothZoomController',
    'BrushRangeSelector',
    'WSJTooltip',
    'KeyboardNavigationHandler',
    'CrossfilterManager',
    'DrillDownNavigator',
    # Export system
    'ExportFormat',
    'WSJExportManager',
    'VisualizationShareManager',
    'PrintLayoutManager',
    'HTMLExportBuilder'
]