"""PyQtGraph chart factory for interactive health visualizations."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None

from ...utils.logging_config import get_logger
from .wsj_style_manager import WSJStyleManager

logger = get_logger(__name__)


class InteractiveChartWidget(QWidget):
    """Base widget for interactive charts with PyQtGraph."""
    
    # Signals
    dataPointClicked = pyqtSignal(dict)  # Emitted when a data point is clicked
    rangeChanged = pyqtSignal(tuple)     # Emitted when zoom/pan changes
    
    def __init__(self, style_manager: WSJStyleManager, parent=None):
        super().__init__(parent)
        self.style_manager = style_manager
        self.plot_widget = None
        self.data = None
        self.config = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the basic UI structure."""
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # Apply WSJ background color
        self.setStyleSheet(f"background-color: {self.style_manager.WARM_PALETTE['surface']};")
    
    def update_data(self, data: Any, config: Dict[str, Any] = None):
        """Update chart data and configuration."""
        self.data = data
        if config:
            self.config.update(config)
        self._render_chart()
    
    def _render_chart(self):
        """Render the chart - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _render_chart")
    
    def export_image(self, filename: str, width: int = 1200, height: int = 800):
        """Export chart as image."""
        if self.plot_widget:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.parameters()['width'] = width
            exporter.parameters()['height'] = height
            exporter.export(filename)


class PyQtGraphChartFactory:
    """Factory for creating interactive charts using PyQtGraph."""
    
    def __init__(self, style_manager: WSJStyleManager):
        """Initialize the chart factory."""
        self.style_manager = style_manager
        
        if not PYQTGRAPH_AVAILABLE:
            logger.warning("PyQtGraph not available. Interactive charts will be limited.")
            return
        
        # Configure PyQtGraph global settings
        pg.setConfigOptions(
            antialias=True,
            background=style_manager.WARM_PALETTE['surface'],
            foreground=style_manager.WARM_PALETTE['text_primary']
        )
    
    def create_chart(self, chart_type: str, data: Any, config: Dict[str, Any]) -> QWidget:
        """Create an interactive chart of the specified type."""
        if not PYQTGRAPH_AVAILABLE:
            return self._create_fallback_widget(chart_type, config)
        
        chart_creators = {
            'multi_metric_line': self._create_multi_metric_line,
            'correlation_heatmap': self._create_correlation_heatmap,
            'sparkline': self._create_sparkline,
            'timeline': self._create_timeline_chart,
            'polar': self._create_polar_chart,
            'scatter': self._create_scatter_chart,
            'box_plot': self._create_box_plot
        }
        
        creator = chart_creators.get(chart_type)
        if creator:
            return creator(data, config)
        else:
            logger.warning(f"Unknown chart type: {chart_type}")
            return self._create_fallback_widget(chart_type, config)
    
    def _create_fallback_widget(self, chart_type: str, config: Dict[str, Any]) -> QWidget:
        """Create a fallback widget when PyQtGraph is not available."""
        widget = QWidget()  # Remove self as parent
        layout = QVBoxLayout(widget)
        
        label = QLabel(f"Interactive {chart_type} chart\n(PyQtGraph not available)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            color: {self.style_manager.WARM_PALETTE['text_secondary']};
            font-size: 14px;
            padding: 20px;
        """)
        
        layout.addWidget(label)
        return widget
    
    def _create_multi_metric_line(self, data: Dict[str, pd.DataFrame], 
                                 config: Dict[str, Any]) -> QWidget:
        """Create multi-metric line chart with independent y-axes."""
        widget = MultiMetricLineChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_correlation_heatmap(self, data: Dict[str, pd.DataFrame],
                                   config: Dict[str, Any]) -> QWidget:
        """Create interactive correlation heatmap."""
        widget = CorrelationHeatmapChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_sparkline(self, data: pd.Series, config: Dict[str, Any]) -> QWidget:
        """Create compact sparkline visualization."""
        widget = SparklineChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_timeline_chart(self, data: Dict[str, Any], config: Dict[str, Any]) -> QWidget:
        """Create timeline chart with events."""
        widget = TimelineChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_polar_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create polar chart for cyclical patterns."""
        widget = PolarPatternChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_scatter_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create scatter plot with trend line."""
        widget = ScatterChart(self.style_manager)
        widget.update_data(data, config)
        return widget
    
    def _create_box_plot(self, data: pd.DataFrame, config: Dict[str, Any]) -> QWidget:
        """Create box plot for distribution comparison."""
        widget = BoxPlotChart(self.style_manager)
        widget.update_data(data, config)
        return widget


class MultiMetricLineChart(InteractiveChartWidget):
    """Multi-metric line chart with independent y-axes."""
    
    def _render_chart(self):
        """Render the multi-metric line chart."""
        if not self.data or not pg:
            return
        
        # Clear existing content
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        
        # Create header with title and subtitle
        header = self._create_header()
        self.layout().addWidget(header)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.layout().addWidget(self.plot_widget)
        
        # Apply WSJ styling
        self._apply_wsj_style()
        
        # Plot each metric
        self._plot_metrics()
        
        # Add legend
        self._add_legend()
        
        # Set up interactivity
        self._setup_interactivity()
    
    def _create_header(self) -> QWidget:
        """Create header with title and subtitle."""
        header = QWidget(self)
        header.setLayout(QVBoxLayout())
        header.layout().setContentsMargins(20, 20, 20, 10)
        
        # Title
        if 'title' in self.config:
            title = QLabel(self.config['title'])
            title.setFont(QFont(
                self.style_manager.TYPOGRAPHY['title']['family'],
                self.style_manager.TYPOGRAPHY['title']['size'],
                self.style_manager.TYPOGRAPHY['title']['weight']
            ))
            title.setStyleSheet(f"color: {self.style_manager.TYPOGRAPHY['title']['color']};")
            header.layout().addWidget(title)
        
        # Subtitle
        if 'subtitle' in self.config:
            subtitle = QLabel(self.config['subtitle'])
            subtitle.setFont(QFont(
                self.style_manager.TYPOGRAPHY['subtitle']['family'],
                self.style_manager.TYPOGRAPHY['subtitle']['size']
            ))
            subtitle.setStyleSheet(f"color: {self.style_manager.TYPOGRAPHY['subtitle']['color']};")
            header.layout().addWidget(subtitle)
        
        return header
    
    def _apply_wsj_style(self):
        """Apply WSJ styling to the plot widget."""
        plot_item = self.plot_widget.getPlotItem()
        
        # Set background colors
        self.plot_widget.setBackground(self.style_manager.WARM_PALETTE['surface'])
        
        # Configure axes
        styles = self.style_manager.get_pyqtgraph_style()
        
        # Bottom axis (time)
        bottom_axis = plot_item.getAxis('bottom')
        bottom_axis.setPen(pg.mkPen(color=styles['axis']['color'], width=0.5))
        bottom_axis.setTextPen(pg.mkPen(color=styles['axis']['color']))
        
        # Hide top and right axes by default
        plot_item.showAxis('top', False)
        plot_item.showAxis('right', False)
        
        # Grid
        if self.config.get('grid_style', 'subtle') != 'none':
            plot_item.showGrid(x=True, y=True, alpha=0.3)
    
    def _plot_metrics(self):
        """Plot each metric with its own y-axis."""
        plot_item = self.plot_widget.getPlotItem()
        
        # Get y-axis configuration
        y_axes_config = self.config.get('y_axes', {})
        colors = self.config.get('colors', {})
        
        self.curves = {}
        self.y_axes = {}
        
        for i, (metric_name, metric_data) in enumerate(self.data.items()):
            # Prepare data
            if isinstance(metric_data, pd.DataFrame):
                # Convert index to numpy array of timestamps
                x_data = np.array(metric_data.index.astype(np.int64) // 10**9)  # Convert to timestamp
                y_data = metric_data.iloc[:, 0].values
            else:
                x_data = np.arange(len(metric_data))
                y_data = np.array(metric_data.values) if hasattr(metric_data, 'values') else np.array(metric_data)
            
            # Get metric configuration
            metric_config = y_axes_config.get(metric_name, {})
            color = colors.get(metric_name, self.style_manager.get_metric_color(metric_name, i))
            
            # Create y-axis for metrics after the first
            if i == 0:
                # Use the default left axis
                axis = plot_item.getAxis('left')
                curve = plot_item.plot(x_data, y_data, pen=pg.mkPen(color=color, width=2))
            else:
                # Create new y-axis
                axis = pg.AxisItem('right' if metric_config.get('position', 'right') == 'right' else 'left')
                
                # Position the axis
                if i > 1:
                    axis.setWidth(60)
                
                # Add to plot
                plot_item.layout.addItem(axis, 2, 3 if metric_config.get('position', 'right') == 'right' else 1)
                
                # Create ViewBox for this metric
                vb = pg.ViewBox()
                plot_item.scene().addItem(vb)
                
                # Link x-axis
                vb.setXLink(plot_item.vb)
                
                # Plot data
                curve = pg.PlotCurveItem(x_data, y_data, pen=pg.mkPen(color=color, width=2))
                vb.addItem(curve)
                
                # Connect axis to ViewBox
                axis.linkToView(vb)
                axis.setZValue(-10000)
                
                # Update view when main plot changes
                def updateViews():
                    vb.setGeometry(plot_item.vb.sceneBoundingRect())
                    vb.linkedViewChanged(plot_item.vb, vb.XAxis)
                
                updateViews()
                plot_item.vb.sigResized.connect(updateViews)
            
            # Style the axis
            axis.setPen(pg.mkPen(color=color, width=1))
            axis.setTextPen(pg.mkPen(color=color))
            axis.setLabel(metric_name, color=color, 
                         font=QFont(self.style_manager.TYPOGRAPHY['axis_label']['family'],
                                   self.style_manager.TYPOGRAPHY['axis_label']['size']))
            
            self.curves[metric_name] = curve
            self.y_axes[metric_name] = axis
    
    def _add_legend(self):
        """Add legend to the chart."""
        if self.config.get('legend_position', 'top') == 'none':
            return
        
        legend = pg.LegendItem(offset=(20, 20))
        legend.setParentItem(self.plot_widget.getPlotItem())
        
        for metric_name, curve in self.curves.items():
            legend.addItem(curve, metric_name)
        
        # Style the legend
        legend.setLabelTextColor(self.style_manager.WARM_PALETTE['text_primary'])
    
    def _setup_interactivity(self):
        """Set up interactive features."""
        # Crosshair for hover
        self.vline = pg.InfiniteLine(angle=90, movable=False, 
                                    pen=pg.mkPen(self.style_manager.WARM_PALETTE['text_secondary'], 
                                               width=1, style=Qt.PenStyle.DashLine))
        self.hline = pg.InfiniteLine(angle=0, movable=False,
                                    pen=pg.mkPen(self.style_manager.WARM_PALETTE['text_secondary'],
                                               width=1, style=Qt.PenStyle.DashLine))
        
        self.plot_widget.addItem(self.vline, ignoreBounds=True)
        self.plot_widget.addItem(self.hline, ignoreBounds=True)
        
        # Tooltip
        self.tooltip = pg.TextItem(anchor=(0.5, 1.2))
        self.plot_widget.addItem(self.tooltip)
        
        # Mouse tracking
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)
        
        # Range changes
        self.plot_widget.getPlotItem().vb.sigRangeChanged.connect(self._on_range_changed)
    
    def _on_mouse_move(self, pos):
        """Handle mouse movement for crosshair and tooltip."""
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
            
            self.vline.setPos(mouse_point.x())
            self.hline.setPos(mouse_point.y())
            
            # Update tooltip with nearest data point info
            # This is a simplified version - in production, find nearest point
            self.tooltip.setText(f"Time: {mouse_point.x():.0f}\nValue: {mouse_point.y():.1f}")
            self.tooltip.setPos(mouse_point.x(), mouse_point.y())
    
    def _on_range_changed(self):
        """Handle zoom/pan range changes."""
        view_range = self.plot_widget.getPlotItem().vb.viewRange()
        self.rangeChanged.emit((view_range[0], view_range[1]))


class CorrelationHeatmapChart(InteractiveChartWidget):
    """Interactive correlation heatmap with progressive disclosure."""
    
    def _render_chart(self):
        """Render the correlation heatmap."""
        if not self.data or not pg:
            return
        
        # Clear existing content
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        
        # Create header
        header = self._create_header()
        self.layout().addWidget(header)
        
        # Create graphics layout
        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.layout().addWidget(self.graphics_layout)
        
        # Create heatmap
        self._create_heatmap()
        
        # Add color bar
        self._add_colorbar()
        
        # Set up interactivity
        self._setup_interactivity()
    
    def _create_header(self) -> QWidget:
        """Create header with title and subtitle."""
        header = QWidget(self)
        header.setLayout(QVBoxLayout())
        header.layout().setContentsMargins(20, 20, 20, 10)
        
        if 'title' in self.config:
            title = QLabel(self.config['title'])
            title.setFont(QFont(
                self.style_manager.TYPOGRAPHY['title']['family'],
                self.style_manager.TYPOGRAPHY['title']['size'],
                self.style_manager.TYPOGRAPHY['title']['weight']
            ))
            title.setStyleSheet(f"color: {self.style_manager.TYPOGRAPHY['title']['color']};")
            header.layout().addWidget(title)
        
        return header
    
    def _create_heatmap(self):
        """Create the heatmap visualization."""
        # Get correlation matrix
        corr_matrix = self.data.get('correlation', pd.DataFrame())
        
        # Create plot item
        self.plot_item = self.graphics_layout.addPlot()
        
        # Create image item for heatmap
        self.img = pg.ImageItem()
        self.plot_item.addItem(self.img)
        
        # Set data
        img_data = corr_matrix.values
        self.img.setImage(img_data.T, levels=[-1, 1])
        
        # Apply colormap
        cmap = self.style_manager.get_correlation_colormap()
        colors = [(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)) 
                 for c in cmap(np.linspace(0, 1, 256))]
        self.img.setLookupTable(colors)
        
        # Set axis labels
        axis_labels = list(corr_matrix.columns)
        
        # Configure axes
        left_axis = self.plot_item.getAxis('left')
        bottom_axis = self.plot_item.getAxis('bottom')
        
        left_axis.setTicks([[(i, label) for i, label in enumerate(axis_labels)]])
        bottom_axis.setTicks([[(i, label) for i, label in enumerate(axis_labels)]])
        
        # Rotate bottom labels - pyqtgraph doesn't support label rotation directly
        # We'll use tick spacing instead to avoid overlap
        bottom_axis.setStyle(tickLength=10)
        
        # Style axes
        for axis in [left_axis, bottom_axis]:
            axis.setPen(pg.mkPen(self.style_manager.WARM_PALETTE['text_secondary'], width=0.5))
            axis.setTextPen(pg.mkPen(self.style_manager.WARM_PALETTE['text_secondary']))
    
    def _add_colorbar(self):
        """Add a color bar to show correlation scale."""
        # Create colorbar plot
        self.colorbar = self.graphics_layout.addPlot()
        self.colorbar.hideAxis('left')
        self.colorbar.hideAxis('bottom')
        self.colorbar.setMaximumWidth(100)
        
        # Create gradient
        gradient = pg.GradientWidget(orientation='right')
        cmap = self.style_manager.get_correlation_colormap()
        
        # Set gradient colors
        gradient.setColorMap(pg.ColorMap(
            pos=np.linspace(0, 1, 3),
            color=[(229, 111, 81), (250, 248, 245), (149, 193, 123)]  # RGB values
        ))
        
        # Add labels
        self.colorbar.setLabel('right', 'Correlation', 
                              color=self.style_manager.WARM_PALETTE['text_primary'])
    
    def _setup_interactivity(self):
        """Set up interactive features."""
        # Hover text
        self.hover_text = pg.TextItem(anchor=(0.5, 1))
        self.plot_item.addItem(self.hover_text)
        
        # Mouse tracking for hover
        self.img.hoverEvent = self._on_hover
        
        # Click for details
        self.img.mouseClickEvent = self._on_click
    
    def _on_hover(self, event):
        """Handle hover events."""
        if event.isExit():
            self.hover_text.setText("")
            return
        
        # Get position
        pos = event.position().toPoint()
        i, j = int(pos.x()), int(pos.y())
        
        # Get correlation value
        corr_matrix = self.data.get('correlation', pd.DataFrame())
        if 0 <= i < len(corr_matrix.columns) and 0 <= j < len(corr_matrix.index):
            value = corr_matrix.iloc[j, i]
            var1 = corr_matrix.columns[i]
            var2 = corr_matrix.index[j]
            
            # Update hover text
            self.hover_text.setText(f"{var1} × {var2}\nCorrelation: {value:.3f}")
            self.hover_text.setPos(pos.x(), pos.y())
    
    def _on_click(self, event):
        """Handle click events."""
        pos = event.position().toPoint()
        i, j = int(pos.x()), int(pos.y())
        
        corr_matrix = self.data.get('correlation', pd.DataFrame())
        if 0 <= i < len(corr_matrix.columns) and 0 <= j < len(corr_matrix.index):
            value = corr_matrix.iloc[j, i]
            var1 = corr_matrix.columns[i]
            var2 = corr_matrix.index[j]
            
            # Emit signal with details
            self.dataPointClicked.emit({
                'variable1': var1,
                'variable2': var2,
                'correlation': value,
                'significance': self.data.get('significance', pd.DataFrame()).iloc[j, i]
                if 'significance' in self.data else None
            })


class SparklineChart(InteractiveChartWidget):
    """Compact sparkline visualization for trends."""
    
    def _render_chart(self):
        """Render the sparkline chart."""
        if self.data is None or not pg:
            return
        
        # Clear existing content
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().deleteLater()
        
        # Create horizontal layout for compact display
        container = QWidget(self)
        container.setLayout(QHBoxLayout())
        container.layout().setContentsMargins(5, 5, 5, 5)
        self.layout().addWidget(container)
        
        # Create small plot widget
        self.plot_widget = pg.PlotWidget()
        # self.plot_widget.setMaximumHeight(60)
        self.plot_widget.setMinimumHeight(40)
        container.layout().addWidget(self.plot_widget)
        
        # Hide axes for minimal look
        plot_item = self.plot_widget.getPlotItem()
        plot_item.hideAxis('left')
        plot_item.hideAxis('bottom')
        plot_item.setMouseEnabled(x=False, y=False)
        
        # Plot data
        if isinstance(self.data, pd.Series):
            y_data = self.data.values
        else:
            y_data = np.array(self.data)
        
        x_data = np.arange(len(y_data))
        
        # Determine color based on trend
        if len(y_data) > 1:
            trend = y_data[-1] - y_data[0]
            if trend > 0:
                color = self.style_manager.WARM_PALETTE['positive']
            elif trend < 0:
                color = self.style_manager.WARM_PALETTE['negative']
            else:
                color = self.style_manager.WARM_PALETTE['neutral']
        else:
            color = self.style_manager.WARM_PALETTE['primary']
        
        # Plot line
        self.plot_widget.plot(x_data, y_data, pen=pg.mkPen(color=color, width=2))
        
        # Add current value label
        if self.config.get('show_value', True):
            current_value = y_data[-1] if len(y_data) > 0 else 0
            label = QLabel(self.style_manager.format_number(current_value))
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet(f"""
                color: {color};
                font-size: {self.style_manager.TYPOGRAPHY['subtitle']['size']}px;
                font-weight: 600;
                padding: 0 10px;
            """)
            container.layout().addWidget(label)


class TimelineChart(InteractiveChartWidget):
    """Timeline visualization with events and background metrics."""
    
    def _render_chart(self):
        """Render the timeline chart."""
        # Implementation would follow similar pattern
        # This is a placeholder for the timeline chart
        pass


class PolarPatternChart(InteractiveChartWidget):
    """Polar chart for visualizing cyclical patterns."""
    
    def _render_chart(self):
        """Render the polar pattern chart."""
        # Implementation would follow similar pattern
        # This is a placeholder for the polar chart
        pass


class ScatterChart(InteractiveChartWidget):
    """Scatter plot with trend line and correlation."""
    
    def _render_chart(self):
        """Render the scatter chart."""
        # Implementation would follow similar pattern
        # This is a placeholder for the scatter chart
        pass


class BoxPlotChart(InteractiveChartWidget):
    """Box plot for distribution comparison."""
    
    def _render_chart(self):
        """Render the box plot chart."""
        # Implementation would follow similar pattern
        # This is a placeholder for the box plot
        pass