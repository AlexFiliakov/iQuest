"""
Optimized line chart with performance enhancements.

This module extends the enhanced line chart with advanced performance
optimizations including virtualization, progressive rendering, and
adaptive quality adjustments.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import time
import pandas as pd
import numpy as np
import logging

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor

from .enhanced_line_chart import EnhancedLineChart, DataSeries
from .chart_config import LineChartConfig
from .visualization_performance_optimizer import (
    VisualizationPerformanceOptimizer,
    ViewportConfig,
    ChartVirtualizationEngine,
    ProgressiveRenderer,
    RealTimePerformanceMonitor
)
from .chart_performance_optimizer import ChartPerformanceOptimizer
from .optimized_data_structures import TypedTimeSeriesArray, SpatialTimeSeriesIndex

logger = logging.getLogger(__name__)


class OptimizedLineChart(EnhancedLineChart):
    """
    High-performance line chart with advanced optimizations.
    
    Features all capabilities of EnhancedLineChart plus:
    - Automatic data virtualization for large datasets
    - Progressive rendering with visual feedback
    - Adaptive quality based on performance
    - Efficient memory management
    - GPU acceleration when available
    """
    
    # Additional signals
    performanceWarning = pyqtSignal(str)
    renderProgress = pyqtSignal(float)  # 0-1 progress
    
    def __init__(self, config: Optional[LineChartConfig] = None, parent=None):
        """Initialize optimized line chart."""
        super().__init__(config, parent)
        
        # Performance optimization components
        self.perf_optimizer = VisualizationPerformanceOptimizer()
        self.chart_optimizer = ChartPerformanceOptimizer()
        self.virtualization_engine = ChartVirtualizationEngine()
        self.progressive_renderer = ProgressiveRenderer()
        self.performance_monitor = RealTimePerformanceMonitor()
        
        # Optimization settings
        self.virtualization_enabled = True
        self.progressive_enabled = True
        self.adaptive_quality = True
        self.target_fps = 60
        self.max_render_time = 16.67  # ms for 60 FPS
        
        # Optimized data storage
        self.optimized_series: Dict[str, TypedTimeSeriesArray] = {}
        self.spatial_indices: Dict[str, SpatialTimeSeriesIndex] = {}
        self.virtual_sources = {}
        
        # Performance state
        self.is_virtualized = False
        self.current_quality = 'high'
        self.last_render_time = 0
        self.frame_times = []
        
        # Progressive rendering state
        self.render_stage = 0
        self.progressive_timer = QTimer()
        self.progressive_timer.timeout.connect(self._progressive_render_step)
        
        # Connect performance monitoring
        self.performance_monitor.performance_warning.connect(self.performanceWarning.emit)
        self.performance_monitor.quality_changed.connect(self._on_quality_changed)
        self.progressive_renderer.render_progress.connect(self.renderProgress.emit)
        
    def addSeries(self, name: str, data: Union[pd.DataFrame, List[Dict[str, Any]]], 
                  color: Optional[str] = None, style: str = 'solid'):
        """Add data series with optimization."""
        # Convert to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
            
        # Profile data
        profile = self.perf_optimizer._profile_data(df)
        
        # Store original data
        series = DataSeries(name, data, color, style)
        self.series[name] = series
        
        # Create optimized structures
        if profile.point_count > 10000:
            # Use typed arrays for large datasets
            typed_array = TypedTimeSeriesArray.from_dataframe(df)
            self.optimized_series[name] = typed_array
            
            # Build spatial index
            index = SpatialTimeSeriesIndex()
            index.build(typed_array.timestamps)
            self.spatial_indices[name] = index
            
            # Setup virtualization if needed
            if profile.point_count > 100000:
                self._setup_virtualization(name, df)
                
        # Update ranges
        self._updateDataRanges()
        
        # Request optimized render
        self.update()
        
    def _setup_virtualization(self, series_name: str, data: pd.DataFrame):
        """Setup virtualization for large dataset."""
        logger.info(f"Setting up virtualization for {series_name} ({len(data)} points)")
        
        # Create virtual data source
        virtual_source = self.virtualization_engine.setup_virtualization(data)
        self.virtual_sources[series_name] = virtual_source
        self.is_virtualized = True
        
    def paintEvent(self, event):
        """Optimized paint event with performance monitoring."""
        if not self.series:
            super().paintEvent(event)
            return
            
        # Start performance measurement
        start_time = time.perf_counter()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, 
                            self.current_quality != 'low')
        
        # Clear background
        painter.fillRect(self.rect(), QColor(self.config.background_color))
        
        # Calculate viewport
        viewport = self._calculate_viewport()
        
        # Progressive rendering check
        if self.progressive_enabled and self._should_use_progressive():
            self._start_progressive_render(painter, viewport)
        else:
            # Standard optimized rendering
            self._render_optimized(painter, viewport)
            
        # Record performance
        render_time = (time.perf_counter() - start_time) * 1000
        self._record_render_performance(render_time)
        
    def _calculate_viewport(self) -> ViewportConfig:
        """Calculate current viewport configuration."""
        chart_rect = self._getChartRect()
        
        # Use view ranges if zoomed, otherwise full ranges
        x_range = self.view_x_range or self.x_range
        y_range = self.view_y_range or self.y_range
        
        return ViewportConfig(
            x_min=x_range[0],
            x_max=x_range[1],
            y_min=y_range[0],
            y_max=y_range[1],
            width_pixels=chart_rect.width(),
            height_pixels=chart_rect.height(),
            zoom_level=self._calculate_zoom_level()
        )
        
    def _should_use_progressive(self) -> bool:
        """Determine if progressive rendering should be used."""
        # Use progressive for large datasets or slow renders
        total_points = sum(len(s.data) for s in self.series.values())
        return total_points > 50000 or self.last_render_time > 50
        
    def _start_progressive_render(self, painter: QPainter, viewport: ViewportConfig):
        """Start progressive rendering process."""
        self.render_stage = 0
        self.renderProgress.emit(0.0)
        
        # Render first stage immediately
        self._progressive_render_step()
        
        # Start timer for subsequent stages
        self.progressive_timer.start(16)  # 60 FPS
        
    def _progressive_render_step(self):
        """Render one stage of progressive rendering."""
        if self.render_stage >= 4:
            self.progressive_timer.stop()
            self.renderProgress.emit(1.0)
            return
            
        # Calculate what to render in this stage
        if self.render_stage == 0:
            # Stage 1: Render axes and grid
            self._drawAxesAndGrid(QPainter(self))
        elif self.render_stage == 1:
            # Stage 2: Render low-res preview (every 10th point)
            self._render_preview(QPainter(self))
        elif self.render_stage == 2:
            # Stage 3: Render medium resolution
            self._render_medium_quality(QPainter(self))
        else:
            # Stage 4: Full quality render
            self._render_full_quality(QPainter(self))
            
        self.render_stage += 1
        self.renderProgress.emit(self.render_stage / 4.0)
        
    def _render_optimized(self, painter: QPainter, viewport: ViewportConfig):
        """Render chart with optimizations."""
        # Draw base elements
        self._drawAxesAndGrid(painter)
        
        # Get visible data for each series
        chart_rect = self._getChartRect()
        
        for name, series in self.series.items():
            if not series.visible:
                continue
                
            # Get optimized data for viewport
            if self.is_virtualized and name in self.virtual_sources:
                # Use virtualized data
                visible_data = self.virtualization_engine.get_viewport_data(
                    self.virtual_sources[name], viewport
                )
            elif name in self.optimized_series:
                # Use optimized typed arrays
                visible_data = self._get_viewport_data_typed(name, viewport)
            else:
                # Small dataset - use original data
                visible_data = pd.DataFrame(series.data)
                
            # Apply additional optimization if needed
            if len(visible_data) > viewport.max_renderable_points:
                visible_data = self.chart_optimizer.optimize_data(
                    visible_data,
                    target_points=viewport.max_renderable_points,
                    algorithm='lttb'
                )
                
            # Render the series
            self._render_series_optimized(painter, name, visible_data, chart_rect)
            
        # Draw decorations
        self._drawTitle(painter)
        self._drawLegend(painter)
        
    def _get_viewport_data_typed(self, series_name: str, 
                                viewport: ViewportConfig) -> pd.DataFrame:
        """Get viewport data from typed arrays."""
        typed_array = self.optimized_series[series_name]
        index = self.spatial_indices[series_name]
        
        # Query spatial index
        indices = index.query_range(int(viewport.x_min), int(viewport.x_max))
        
        if len(indices) == 0:
            return pd.DataFrame()
            
        # Extract visible data
        timestamps, values = typed_array[indices]
        
        # Convert back to DataFrame
        return pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps, unit='s'),
            'value': values
        }).set_index('timestamp')
        
    def _render_series_optimized(self, painter: QPainter, series_name: str,
                                data: pd.DataFrame, chart_rect: QRectF):
        """Render series with optimizations."""
        if data.empty:
            return
            
        series = self.series[series_name]
        
        # Set pen
        color = QColor(series.color or self.config.get_color(
            list(self.series.keys()).index(series_name)
        ))
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        # Convert to screen coordinates
        points = []
        x_scale = chart_rect.width() / (self.x_range[1] - self.x_range[0])
        y_scale = chart_rect.height() / (self.y_range[1] - self.y_range[0])
        
        for idx, value in data.iterrows():
            # Convert timestamp to numeric if needed
            if hasattr(idx, 'timestamp'):
                x = idx.timestamp()
            else:
                x = float(idx)
                
            y = float(value.iloc[0])
            
            # Transform to screen coordinates
            screen_x = chart_rect.left() + (x - self.x_range[0]) * x_scale
            screen_y = chart_rect.bottom() - (y - self.y_range[0]) * y_scale
            
            points.append(QPointF(screen_x, screen_y))
            
        # Draw line
        if points:
            painter.drawPolyline(points)
            
    def _record_render_performance(self, render_time: float):
        """Record and analyze render performance."""
        self.last_render_time = render_time
        self.frame_times.append(render_time)
        
        # Keep only recent history
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
            
        # Update performance monitor
        data_points = sum(len(s.data) for s in self.series.values())
        self.performance_monitor.record_frame(render_time, 0, data_points)
        
        # Check if we need to adapt quality
        if self.adaptive_quality:
            self._check_quality_adaptation()
            
    def _check_quality_adaptation(self):
        """Check if rendering quality should be adjusted."""
        if len(self.frame_times) < 10:
            return
            
        avg_frame_time = np.mean(self.frame_times[-10:])
        
        if avg_frame_time > self.max_render_time * 1.5 and self.current_quality != 'low':
            # Reduce quality
            self._set_quality('medium' if self.current_quality == 'high' else 'low')
        elif avg_frame_time < self.max_render_time * 0.5 and self.current_quality != 'high':
            # Increase quality
            self._set_quality('medium' if self.current_quality == 'low' else 'high')
            
    def _set_quality(self, quality: str):
        """Set rendering quality level."""
        self.current_quality = quality
        logger.info(f"Adjusted rendering quality to: {quality}")
        
        # Adjust settings based on quality
        if quality == 'low':
            self.setUpdatesEnabled(False)  # Batch updates
            self.config.enable_animations = False
        elif quality == 'medium':
            self.setUpdatesEnabled(True)
            self.config.enable_animations = False
        else:  # high
            self.setUpdatesEnabled(True)
            self.config.enable_animations = True
            
        self.update()
        
    def _on_quality_changed(self, quality: str):
        """Handle quality change from performance monitor."""
        self._set_quality(quality)
        
    def _calculate_zoom_level(self) -> float:
        """Calculate current zoom level."""
        if not self.view_x_range:
            return 1.0
            
        full_range = self.x_range[1] - self.x_range[0]
        view_range = self.view_x_range[1] - self.view_x_range[0]
        
        return full_range / view_range if view_range > 0 else 1.0
        
    def setVisualizationEnabled(self, enabled: bool):
        """Enable or disable virtualization."""
        self.virtualization_enabled = enabled
        if not enabled:
            self.is_virtualized = False
            self.virtual_sources.clear()
            
    def setProgressiveRenderingEnabled(self, enabled: bool):
        """Enable or disable progressive rendering."""
        self.progressive_enabled = enabled
        
    def setAdaptiveQualityEnabled(self, enabled: bool):
        """Enable or disable adaptive quality adjustments."""
        self.adaptive_quality = enabled
        if not enabled:
            self._set_quality('high')
            
    def getPerformanceStats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'avg_frame_time': np.mean(self.frame_times) if self.frame_times else 0,
            'current_fps': 1000 / self.last_render_time if self.last_render_time > 0 else 0,
            'current_quality': self.current_quality,
            'is_virtualized': self.is_virtualized,
            'total_points': sum(len(s.data) for s in self.series.values()),
            'memory_usage': self._estimate_memory_usage()
        }
        
    def _estimate_memory_usage(self) -> int:
        """Estimate current memory usage in bytes."""
        total = 0
        
        # Original series data
        for series in self.series.values():
            total += len(series.data) * 100  # Rough estimate per point
            
        # Optimized structures
        for typed_array in self.optimized_series.values():
            total += typed_array.memory_usage()
            
        return total
        
    def enable_progressive_rendering(self, initial_points: int = 1000,
                                   chunk_size: int = 10000,
                                   delay_ms: int = 50):
        """Configure progressive rendering parameters."""
        self.progressive_enabled = True
        self.progressive_initial_points = initial_points
        self.progressive_chunk_size = chunk_size
        self.progressive_delay = delay_ms
        
    def initial_render(self, data: pd.DataFrame, title: str, widget: QWidget):
        """Initial fast render for progressive loading."""
        # Store full data but render subset
        self.full_data = data
        
        # Render initial subset
        initial_data = data.iloc[:self.progressive_initial_points]
        self.update_chart(initial_data, title, widget)
        
        # Schedule progressive updates
        self.progressive_timer.start(self.progressive_delay)
        
    def complete_render(self):
        """Complete full resolution render."""
        if hasattr(self, 'full_data'):
            self.update_chart(self.full_data, self.title, self)
            self.progressive_timer.stop()