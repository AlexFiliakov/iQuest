"""
Adaptive chart rendering system.

This module provides an intelligent rendering system that automatically
selects the optimal rendering backend based on data characteristics,
performance metrics, and system capabilities.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import weakref

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import QWidget

from src.ui.charts.chart_performance_optimizer import ChartPerformanceOptimizer
from src.ui.charts.visualization_performance_optimizer import (
    DataProfile, RealTimePerformanceMonitor, PerformanceMetrics
)

logger = logging.getLogger(__name__)


class RendererType(Enum):
    """Available renderer types."""
    MATPLOTLIB = "matplotlib"
    PYQTGRAPH = "pyqtgraph"
    CANVAS = "canvas"
    WEBGL = "webgl"
    SVG = "svg"


@dataclass
class RendererCapabilities:
    """Capabilities of a specific renderer."""
    max_points: int
    supports_animation: bool
    supports_interactivity: bool
    supports_3d: bool
    memory_efficient: bool
    gpu_accelerated: bool
    quality_level: str  # 'low', 'medium', 'high'
    render_speed: str  # 'slow', 'medium', 'fast'


class BaseRenderer:
    """Base class for all renderers."""
    
    def __init__(self):
        self.capabilities = self._define_capabilities()
        
    def _define_capabilities(self) -> RendererCapabilities:
        """Define renderer capabilities."""
        raise NotImplementedError
        
    def render(self, data: pd.DataFrame, chart_type: str, 
               container: QWidget, **kwargs) -> Any:
        """Render chart with this backend."""
        raise NotImplementedError
        
    def update(self, data: pd.DataFrame, **kwargs):
        """Update existing chart."""
        raise NotImplementedError
        
    def clear(self):
        """Clear rendered content."""
        raise NotImplementedError
        
    def supports_chart_type(self, chart_type: str) -> bool:
        """Check if renderer supports specific chart type."""
        return True  # Override in subclasses


class MatplotlibRenderer(BaseRenderer):
    """Matplotlib-based renderer for high-quality static charts."""
    
    def _define_capabilities(self) -> RendererCapabilities:
        return RendererCapabilities(
            max_points=50000,
            supports_animation=False,
            supports_interactivity=True,
            supports_3d=True,
            memory_efficient=False,
            gpu_accelerated=False,
            quality_level='high',
            render_speed='slow'
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """Render using matplotlib."""
        try:
            from src.ui.charts.matplotlib_chart_factory import MatplotlibChartFactory
            
            factory = MatplotlibChartFactory()
            
            # Select appropriate chart type
            if chart_type == 'line':
                chart = factory.create_line_chart()
            elif chart_type == 'bar':
                chart = factory.create_bar_chart()
            elif chart_type == 'scatter':
                chart = factory.create_scatter_chart()
            else:
                chart = factory.create_line_chart()  # Default
                
            # Render chart
            chart.update_chart(data, kwargs.get('title', ''), container)
            return chart
            
        except ImportError:
            logger.error("Matplotlib not available")
            return None


class PyQtGraphRenderer(BaseRenderer):
    """PyQtGraph renderer for real-time interactive charts."""
    
    def _define_capabilities(self) -> RendererCapabilities:
        return RendererCapabilities(
            max_points=1000000,
            supports_animation=True,
            supports_interactivity=True,
            supports_3d=True,
            memory_efficient=True,
            gpu_accelerated=True,
            quality_level='medium',
            render_speed='fast'
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """Render using PyQtGraph."""
        try:
            from src.ui.charts.pyqtgraph_chart_factory import PyQtGraphChartFactory
            
            factory = PyQtGraphChartFactory()
            
            if chart_type == 'line':
                chart = factory.create_line_chart()
            elif chart_type == 'scatter':
                chart = factory.create_scatter_chart()
            elif chart_type == 'heatmap':
                chart = factory.create_heatmap()
            else:
                chart = factory.create_line_chart()
                
            chart.update_chart(data, kwargs.get('title', ''), container)
            return chart
            
        except ImportError:
            logger.error("PyQtGraph not available")
            return None
            
    def supports_chart_type(self, chart_type: str) -> bool:
        """PyQtGraph best for line, scatter, and heatmap."""
        return chart_type in ['line', 'scatter', 'heatmap', 'candlestick']


class CanvasRenderer(BaseRenderer):
    """Canvas-based renderer for custom high-performance rendering."""
    
    def _define_capabilities(self) -> RendererCapabilities:
        return RendererCapabilities(
            max_points=500000,
            supports_animation=True,
            supports_interactivity=True,
            supports_3d=False,
            memory_efficient=True,
            gpu_accelerated=False,
            quality_level='medium',
            render_speed='fast'
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """Render using custom canvas implementation."""
        # This would use a custom QPainter-based implementation
        logger.info("Canvas renderer not yet implemented, falling back")
        return None


class WebGLRenderer(BaseRenderer):
    """WebGL renderer for massive datasets."""
    
    def _define_capabilities(self) -> RendererCapabilities:
        return RendererCapabilities(
            max_points=10000000,
            supports_animation=True,
            supports_interactivity=True,
            supports_3d=True,
            memory_efficient=True,
            gpu_accelerated=True,
            quality_level='medium',
            render_speed='fast'
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """Render using WebGL."""
        # This would use a QWebEngineView with WebGL
        logger.info("WebGL renderer not yet implemented, falling back")
        return None


class SVGRenderer(BaseRenderer):
    """SVG renderer for scalable vector graphics."""
    
    def _define_capabilities(self) -> RendererCapabilities:
        return RendererCapabilities(
            max_points=5000,
            supports_animation=True,
            supports_interactivity=True,
            supports_3d=False,
            memory_efficient=False,
            gpu_accelerated=False,
            quality_level='high',
            render_speed='medium'
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """Render as SVG."""
        # This would generate SVG and display in QSvgWidget
        logger.info("SVG renderer not yet implemented, falling back")
        return None


class AdaptiveChartRenderer(QObject):
    """
    Intelligent renderer that selects optimal backend.
    
    Monitors performance and automatically switches renderers
    to maintain optimal performance.
    """
    
    renderer_changed = pyqtSignal(str)  # Emitted when renderer changes
    performance_warning = pyqtSignal(str)  # Performance issues
    
    def __init__(self):
        super().__init__()
        
        # Initialize renderers
        self.renderers = {
            RendererType.MATPLOTLIB: MatplotlibRenderer(),
            RendererType.PYQTGRAPH: PyQtGraphRenderer(),
            RendererType.CANVAS: CanvasRenderer(),
            RendererType.WEBGL: WebGLRenderer(),
            RendererType.SVG: SVGRenderer()
        }
        
        # State
        self.current_renderer: Optional[RendererType] = None
        self.current_chart = None
        self.performance_monitor = RealTimePerformanceMonitor()
        self.optimizer = ChartPerformanceOptimizer()
        
        # Performance history
        self.renderer_performance: Dict[RendererType, List[float]] = {
            r: [] for r in RendererType
        }
        
        # Connect performance monitor
        self.performance_monitor.performance_warning.connect(
            self.performance_warning.emit
        )
        
    def render(self, data: pd.DataFrame, chart_type: str,
               container: QWidget, **kwargs) -> Any:
        """
        Render chart with automatic backend selection.
        
        Args:
            data: Chart data
            chart_type: Type of chart to render
            container: Widget container for chart
            **kwargs: Additional options
            
        Returns:
            Rendered chart object
        """
        start_time = time.perf_counter()
        
        # Profile data
        profile = self._profile_data(data)
        
        # Select optimal renderer
        selected_renderer = self._select_renderer(
            profile, chart_type, container.size(), **kwargs
        )
        
        # Switch renderer if needed
        if selected_renderer != self.current_renderer:
            self._switch_renderer(selected_renderer)
            
        # Optimize data if needed
        optimized_data = self._optimize_data(data, profile, **kwargs)
        
        # Render with selected backend
        renderer = self.renderers[selected_renderer]
        
        try:
            result = renderer.render(
                optimized_data, chart_type, container, **kwargs
            )
            
            # Record performance
            render_time = (time.perf_counter() - start_time) * 1000
            self._record_performance(selected_renderer, render_time, len(data))
            
            # Adapt if needed
            self._check_adaptation()
            
            self.current_chart = result
            return result
            
        except Exception as e:
            logger.error(f"Renderer {selected_renderer} failed: {e}")
            # Try fallback renderer
            return self._render_with_fallback(
                data, chart_type, container, selected_renderer, **kwargs
            )
            
    def _profile_data(self, data: pd.DataFrame) -> DataProfile:
        """Profile dataset characteristics."""
        # Use the profiling from visualization_performance_optimizer
        from src.ui.charts.visualization_performance_optimizer import (
            VisualizationPerformanceOptimizer
        )
        
        optimizer = VisualizationPerformanceOptimizer()
        return optimizer._profile_data(data)
        
    def _select_renderer(self, profile: DataProfile, chart_type: str,
                        container_size: QSize, **kwargs) -> RendererType:
        """Select optimal renderer based on context."""
        candidates = []
        
        # Filter by chart type support
        for renderer_type, renderer in self.renderers.items():
            if renderer.supports_chart_type(chart_type):
                candidates.append(renderer_type)
                
        if not candidates:
            return RendererType.MATPLOTLIB  # Default fallback
            
        # Score each candidate
        scores = {}
        for renderer_type in candidates:
            score = self._score_renderer(
                renderer_type, profile, chart_type, container_size, **kwargs
            )
            scores[renderer_type] = score
            
        # Select highest scoring renderer
        best_renderer = max(scores.items(), key=lambda x: x[1])[0]
        
        logger.debug(f"Selected {best_renderer} for {profile.point_count} points")
        return best_renderer
        
    def _score_renderer(self, renderer_type: RendererType,
                       profile: DataProfile, chart_type: str,
                       container_size: QSize, **kwargs) -> float:
        """Score renderer for given context."""
        renderer = self.renderers[renderer_type]
        capabilities = renderer.capabilities
        score = 100.0
        
        # Data size compatibility
        if profile.point_count > capabilities.max_points:
            score *= 0.1  # Heavily penalize if over capacity
        else:
            # Prefer renderers that can handle the data comfortably
            utilization = profile.point_count / capabilities.max_points
            score *= (1.0 - utilization * 0.3)  # Up to 30% penalty
            
        # Performance requirements
        if kwargs.get('realtime', False) and capabilities.render_speed == 'slow':
            score *= 0.5
            
        # Animation requirements
        if kwargs.get('animated', False) and not capabilities.supports_animation:
            score *= 0.3
            
        # Quality preferences
        quality_pref = kwargs.get('quality', 'medium')
        if quality_pref == 'high' and capabilities.quality_level != 'high':
            score *= 0.7
        elif quality_pref == 'low' and capabilities.quality_level == 'high':
            score *= 0.8  # Slight penalty for overkill
            
        # GPU acceleration bonus for large datasets
        if profile.point_count > 100000 and capabilities.gpu_accelerated:
            score *= 1.5
            
        # Historical performance
        if renderer_type in self.renderer_performance:
            perf_history = self.renderer_performance[renderer_type]
            if perf_history:
                avg_time = np.mean(perf_history[-10:])  # Last 10 renders
                if avg_time < 50:  # Very fast
                    score *= 1.2
                elif avg_time > 200:  # Slow
                    score *= 0.8
                    
        return score
        
    def _switch_renderer(self, new_renderer: RendererType):
        """Switch to new renderer."""
        if self.current_renderer == new_renderer:
            return
            
        # Clear old renderer
        if self.current_renderer and self.current_chart:
            try:
                self.renderers[self.current_renderer].clear()
            except:
                pass
                
        self.current_renderer = new_renderer
        self.renderer_changed.emit(new_renderer.value)
        
        logger.info(f"Switched to {new_renderer.value} renderer")
        
    def _optimize_data(self, data: pd.DataFrame, profile: DataProfile,
                      **kwargs) -> pd.DataFrame:
        """Optimize data based on renderer capabilities."""
        if not kwargs.get('optimize', True):
            return data
            
        renderer = self.renderers[self.current_renderer]
        capabilities = renderer.capabilities
        
        # Check if optimization needed
        if profile.point_count <= capabilities.max_points * 0.5:
            return data  # No optimization needed
            
        # Calculate target points
        target_points = int(capabilities.max_points * 0.8)  # 80% of capacity
        
        # Use appropriate algorithm
        if profile.is_time_series:
            algorithm = 'lttb'  # Best for time series
        else:
            algorithm = 'decimation'
            
        return self.optimizer.optimize_data(
            data,
            target_points=target_points,
            algorithm=algorithm
        )
        
    def _record_performance(self, renderer_type: RendererType,
                           render_time: float, data_points: int):
        """Record rendering performance."""
        self.renderer_performance[renderer_type].append(render_time)
        
        # Keep only recent history
        if len(self.renderer_performance[renderer_type]) > 100:
            self.renderer_performance[renderer_type].pop(0)
            
        # Update performance monitor
        self.performance_monitor.record_frame(
            render_time,
            0,  # Memory delta not measured here
            data_points
        )
        
    def _check_adaptation(self):
        """Check if renderer switch is needed based on performance."""
        if not self.current_renderer:
            return
            
        perf_history = self.renderer_performance[self.current_renderer]
        if len(perf_history) < 5:
            return
            
        # Check recent performance
        recent_avg = np.mean(perf_history[-5:])
        
        # Switch if consistently slow
        if recent_avg > 300:  # >300ms is too slow
            logger.warning(
                f"{self.current_renderer.value} averaging {recent_avg:.0f}ms, "
                "considering switch"
            )
            # Don't auto-switch for now, just warn
            self.performance_warning.emit(
                f"Slow rendering detected ({recent_avg:.0f}ms average)"
            )
            
    def _render_with_fallback(self, data: pd.DataFrame, chart_type: str,
                             container: QWidget, failed_renderer: RendererType,
                             **kwargs) -> Any:
        """Try rendering with fallback renderer."""
        # Find alternative renderer
        for renderer_type in [RendererType.PYQTGRAPH, RendererType.MATPLOTLIB]:
            if renderer_type != failed_renderer:
                try:
                    logger.info(f"Trying fallback renderer: {renderer_type.value}")
                    self._switch_renderer(renderer_type)
                    
                    renderer = self.renderers[renderer_type]
                    return renderer.render(data, chart_type, container, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback renderer {renderer_type} also failed: {e}")
                    
        return None
        
    def update_chart(self, data: pd.DataFrame, **kwargs):
        """Update existing chart with new data."""
        if not self.current_renderer or not self.current_chart:
            return
            
        renderer = self.renderers[self.current_renderer]
        renderer.update(data, **kwargs)
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            'current_renderer': self.current_renderer.value if self.current_renderer else None,
            'renderer_stats': {}
        }
        
        for renderer_type, history in self.renderer_performance.items():
            if history:
                stats['renderer_stats'][renderer_type.value] = {
                    'render_count': len(history),
                    'avg_time': np.mean(history),
                    'min_time': np.min(history),
                    'max_time': np.max(history)
                }
                
        return stats