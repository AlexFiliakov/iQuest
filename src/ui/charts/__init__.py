"""Chart components for Apple Health Monitor.

This module provides comprehensive visualization components for health data with
Wall Street Journal-inspired styling and professional data visualization capabilities.

The charts package includes:

- **Base Components**: Core chart infrastructure and configuration
- **Chart Types**: Line charts, enhanced charts with advanced features
- **Styling**: WSJ-inspired visual design and theming
- **Chart Factories**: PyQtGraph and Matplotlib backend support
- **Visualization Suite**: Complete health data visualization system
- **Interactive Features**: Drill-down, sharing, and progressive loading
- **Accessibility**: WCAG 2.1 AA compliant chart components
- **Export System**: High-quality export to multiple formats

The visualization system is designed for both interactive exploration and
publication-ready static exports, with comprehensive accessibility support
for screen readers and keyboard navigation.

Example:
    Basic chart creation:
    
    >>> from ui.charts import LineChart, ChartConfig
    >>> config = ChartConfig(title="Daily Steps", y_label="Steps")
    >>> chart = LineChart(config)
    >>> chart.set_data(dates, values)
    
    WSJ-styled visualization suite:
    
    >>> from ui.charts import WSJHealthVisualizationSuite
    >>> suite = WSJHealthVisualizationSuite()
    >>> chart = suite.create_trend_chart(data, metric_type="steps")
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