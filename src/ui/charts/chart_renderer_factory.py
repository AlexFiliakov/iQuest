"""Chart renderer factory for supporting multiple rendering backends."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, Callable
import pandas as pd
from PyQt6.QtWidgets import QWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .base_chart import BaseChart, ChartConfig, ChartTheme
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class ChartRenderer(ABC):
    """Abstract base class for chart renderers."""
    
    @abstractmethod
    def render(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme) -> QWidget:
        """Render chart data and return a Qt widget."""
        pass
    
    @abstractmethod
    def export(self, widget: QWidget, format: str, path: str, dpi: int = 300) -> bool:
        """Export chart to file."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """Get renderer capabilities."""
        pass
    
    @abstractmethod
    def supports_animation(self) -> bool:
        """Check if renderer supports animation."""
        pass
    
    @abstractmethod
    def supports_interactivity(self) -> bool:
        """Check if renderer supports interactivity."""
        pass


class MatplotlibRenderer(ChartRenderer):
    """Matplotlib-based chart renderer for static, publication-quality charts."""
    
    def __init__(self):
        """Initialize matplotlib renderer."""
        self._figure: Optional[Figure] = None
        self._canvas: Optional[FigureCanvasQTAgg] = None
    
    def render(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme) -> QWidget:
        """Render chart using matplotlib."""
        logger.debug(f"Rendering chart with matplotlib: {config.title}")
        
        # Create figure with theme background
        self._figure = Figure(facecolor=theme.background_color)
        self._canvas = FigureCanvasQTAgg(self._figure)
        
        # Apply theme settings
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(theme.background_color)
        
        # Configure grid
        if config.show_grid:
            ax.grid(True, color=theme.grid_color, alpha=0.3, linestyle=':')
        
        # Set labels
        if config.title:
            ax.set_title(config.title, color=theme.text_color, 
                        fontsize=theme.title_font_size, 
                        fontfamily=theme.font_family, pad=20)
        
        if config.subtitle:
            ax.text(0.5, 1.02, config.subtitle, transform=ax.transAxes,
                   ha='center', va='bottom', color=theme.text_color,
                   fontsize=theme.subtitle_font_size, alpha=0.8)
        
        if config.x_label:
            ax.set_xlabel(config.x_label, color=theme.text_color,
                         fontsize=theme.label_font_size)
        
        if config.y_label:
            ax.set_ylabel(config.y_label, color=theme.text_color,
                         fontsize=theme.label_font_size)
        
        # Remove spines for WSJ style
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Configure ticks
        ax.tick_params(colors=theme.text_color, labelsize=theme.label_font_size)
        
        return self._canvas
    
    def export(self, widget: QWidget, format: str, path: str, dpi: int = 300) -> bool:
        """Export matplotlib chart."""
        try:
            if self._figure:
                self._figure.savefig(path, format=format, dpi=dpi, 
                                   bbox_inches='tight', facecolor=self._figure.get_facecolor())
                logger.info(f"Exported chart to {path}")
                return True
        except Exception as e:
            logger.error(f"Failed to export chart: {e}")
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get matplotlib renderer capabilities."""
        return {
            'static_charts': True,
            'animations': False,
            'real_time': False,
            '3d_charts': True,
            'statistical_plots': True,
            'export_vector': True,
            'export_raster': True
        }
    
    def supports_animation(self) -> bool:
        """Matplotlib has limited animation support."""
        return False
    
    def supports_interactivity(self) -> bool:
        """Matplotlib has basic interactivity."""
        return True


class QPainterRenderer(ChartRenderer):
    """Custom QPainter-based renderer for real-time, high-performance charts."""
    
    def render(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme) -> QWidget:
        """Render chart using QPainter."""
        logger.debug(f"Rendering chart with QPainter: {config.title}")
        
        # Create custom widget that will handle painting
        from .qpainter_chart_widget import QPainterChartWidget
        widget = QPainterChartWidget(data, config, theme)
        
        return widget
    
    def export(self, widget: QWidget, format: str, path: str, dpi: int = 300) -> bool:
        """Export QPainter chart."""
        try:
            from PyQt6.QtCore import QSize
            from PyQt6.QtGui import QPixmap, QPainter
            
            # Calculate size based on DPI
            size = QSize(int(widget.width() * dpi / 96), 
                        int(widget.height() * dpi / 96))
            
            pixmap = QPixmap(size)
            pixmap.fill(widget.palette().window().color())
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Scale to match DPI
            scale = dpi / 96.0
            painter.scale(scale, scale)
            
            # Render widget
            widget.render(painter)
            painter.end()
            
            # Save based on format
            if format.lower() in ['png', 'jpg', 'jpeg']:
                pixmap.save(path, format.upper())
                logger.info(f"Exported chart to {path}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to export chart: {e}")
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get QPainter renderer capabilities."""
        return {
            'static_charts': True,
            'animations': True,
            'real_time': True,
            '3d_charts': False,
            'statistical_plots': False,
            'export_vector': False,
            'export_raster': True
        }
    
    def supports_animation(self) -> bool:
        """QPainter has excellent animation support."""
        return True
    
    def supports_interactivity(self) -> bool:
        """QPainter supports full interactivity."""
        return True


class PyQtGraphRenderer(ChartRenderer):
    """PyQtGraph-based renderer for scientific, real-time visualizations."""
    
    def render(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme) -> QWidget:
        """Render chart using PyQtGraph."""
        logger.debug(f"Rendering chart with PyQtGraph: {config.title}")
        
        try:
            import pyqtgraph as pg
            
            # Configure pyqtgraph
            pg.setConfigOptions(antialias=True)
            pg.setConfigOption('background', theme.background_color)
            pg.setConfigOption('foreground', theme.text_color)
            
            # Create plot widget
            plot_widget = pg.PlotWidget(title=config.title)
            
            # Style the plot
            plot_widget.setLabel('left', config.y_label, color=theme.text_color)
            plot_widget.setLabel('bottom', config.x_label, color=theme.text_color)
            
            # Configure grid
            if config.show_grid:
                plot_widget.showGrid(x=True, y=True, alpha=0.3)
            
            return plot_widget
            
        except ImportError:
            logger.warning("PyQtGraph not available, falling back to matplotlib")
            return MatplotlibRenderer().render(data, config, theme)
    
    def export(self, widget: QWidget, format: str, path: str, dpi: int = 300) -> bool:
        """Export PyQtGraph chart."""
        try:
            import pyqtgraph as pg
            from pyqtgraph.exporters import ImageExporter
            
            if hasattr(widget, 'plotItem'):
                exporter = ImageExporter(widget.plotItem)
                exporter.parameters()['width'] = int(widget.width() * dpi / 96)
                exporter.export(path)
                logger.info(f"Exported chart to {path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to export chart: {e}")
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get PyQtGraph renderer capabilities."""
        return {
            'static_charts': True,
            'animations': True,
            'real_time': True,
            '3d_charts': True,
            'statistical_plots': True,
            'export_vector': True,
            'export_raster': True
        }
    
    def supports_animation(self) -> bool:
        """PyQtGraph has excellent animation support."""
        return True
    
    def supports_interactivity(self) -> bool:
        """PyQtGraph supports full interactivity."""
        return True


class PlotlyRenderer(ChartRenderer):
    """Plotly-based renderer for interactive, web-based visualizations."""
    
    def render(self, data: pd.DataFrame, config: ChartConfig, theme: ChartTheme) -> QWidget:
        """Render chart using Plotly in a QWebEngineView."""
        logger.debug(f"Rendering chart with Plotly: {config.title}")
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            import plotly.graph_objects as go
            import plotly.io as pio
            
            # Create Plotly figure
            fig = go.Figure()
            
            # Apply theme
            layout = dict(
                title=config.title,
                xaxis_title=config.x_label,
                yaxis_title=config.y_label,
                plot_bgcolor=theme.background_color,
                paper_bgcolor=theme.background_color,
                font=dict(
                    family=theme.font_family,
                    size=theme.label_font_size,
                    color=theme.text_color
                ),
                showlegend=config.show_legend,
                hovermode='x unified'
            )
            
            fig.update_layout(layout)
            
            # Convert to HTML
            html = pio.to_html(fig, include_plotlyjs='cdn')
            
            # Create web view
            web_view = QWebEngineView()
            web_view.setHtml(html)
            
            return web_view
            
        except ImportError:
            logger.warning("Plotly/QWebEngine not available, falling back to matplotlib")
            return MatplotlibRenderer().render(data, config, theme)
    
    def export(self, widget: QWidget, format: str, path: str, dpi: int = 300) -> bool:
        """Export Plotly chart."""
        try:
            # Plotly export would require saving the figure object
            # For now, use screenshot approach
            from PyQt6.QtCore import QSize
            from PyQt6.QtGui import QPixmap
            
            pixmap = widget.grab()
            pixmap.save(path, format.upper())
            logger.info(f"Exported chart to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export chart: {e}")
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get Plotly renderer capabilities."""
        return {
            'static_charts': True,
            'animations': True,
            'real_time': False,
            '3d_charts': True,
            'statistical_plots': True,
            'export_vector': True,
            'export_raster': True
        }
    
    def supports_animation(self) -> bool:
        """Plotly has excellent animation support."""
        return True
    
    def supports_interactivity(self) -> bool:
        """Plotly is built for interactivity."""
        return True


class ChartRendererFactory:
    """Factory for creating chart renderers based on requirements."""
    
    # Renderer registry
    _renderers: Dict[str, Type[ChartRenderer]] = {
        'matplotlib': MatplotlibRenderer,
        'qpainter': QPainterRenderer,
        'pyqtgraph': PyQtGraphRenderer,
        'plotly': PlotlyRenderer
    }
    
    # Selection criteria
    _criteria_map = {
        'static': 'matplotlib',
        'real_time': 'pyqtgraph',
        'interactive': 'plotly',
        'performance': 'qpainter',
        'publication': 'matplotlib'
    }
    
    @classmethod
    def create_renderer(cls, renderer_type: str) -> ChartRenderer:
        """Create a specific renderer by type."""
        renderer_class = cls._renderers.get(renderer_type, MatplotlibRenderer)
        return renderer_class()
    
    @classmethod
    def get_optimal_renderer(cls, requirements: Dict[str, bool]) -> ChartRenderer:
        """Select optimal renderer based on requirements."""
        # Priority order for requirements
        if requirements.get('real_time', False):
            if requirements.get('scientific', False):
                return cls.create_renderer('pyqtgraph')
            else:
                return cls.create_renderer('qpainter')
        
        elif requirements.get('interactive', False):
            if requirements.get('web_export', False):
                return cls.create_renderer('plotly')
            else:
                return cls.create_renderer('pyqtgraph')
        
        elif requirements.get('publication_quality', False):
            return cls.create_renderer('matplotlib')
        
        elif requirements.get('performance', False):
            return cls.create_renderer('qpainter')
        
        # Default to matplotlib
        return cls.create_renderer('matplotlib')
    
    @classmethod
    def register_renderer(cls, name: str, renderer_class: Type[ChartRenderer]):
        """Register a custom renderer."""
        cls._renderers[name] = renderer_class
        logger.info(f"Registered custom renderer: {name}")
    
    @classmethod
    def get_available_renderers(cls) -> list:
        """Get list of available renderers."""
        return list(cls._renderers.keys())
    
    @classmethod
    def get_renderer_capabilities(cls, renderer_type: str) -> Dict[str, bool]:
        """Get capabilities of a specific renderer."""
        renderer = cls.create_renderer(renderer_type)
        return renderer.get_capabilities()