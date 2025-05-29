"""
Visualization performance optimization system.

This module provides comprehensive performance optimizations for health data
visualizations including virtualization, progressive rendering, LOD systems,
and adaptive rendering strategies.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass
from collections import deque
from abc import ABC, abstractmethod
import threading
import queue
import time
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
import logging

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QRect, QSize, QPointF
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


@dataclass
class DataProfile:
    """Profile of dataset characteristics."""
    point_count: int
    time_range: pd.Timedelta
    density: float  # points per time unit
    has_gaps: bool
    is_regular: bool
    memory_size: int
    value_range: Tuple[float, float]
    is_time_series: bool
    has_integer_values: bool
    has_float_values: bool
    benefits_from_aggregation: bool


@dataclass
class ViewportConfig:
    """Configuration for viewport-based rendering."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    width_pixels: int
    height_pixels: int
    zoom_level: float = 1.0
    
    @property
    def max_renderable_points(self) -> int:
        """Maximum points that should be rendered in viewport."""
        # 2-3 points per pixel is optimal for line charts
        return self.width_pixels * 3
    
    @property
    def primary_dimension(self) -> str:
        """Primary dimension for sorting (usually time)."""
        return 'index'


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    render_time: float
    memory_usage: int
    fps: float
    frame_drops: int
    data_points_rendered: int
    optimization_level: str


class ChartVirtualizationEngine:
    """Engine for virtualizing chart data rendering."""
    
    def __init__(self):
        self.chunk_size = 10000
        self.viewport_buffer = 2.0  # Render 2x viewport
        self.chunks_cache = weakref.WeakValueDictionary()
        self.spatial_index = None
        self.prefetch_executor = ThreadPoolExecutor(max_workers=2)
        
    def setup_virtualization(self, data: pd.DataFrame) -> 'VirtualDataSource':
        """Setup virtualization for large dataset."""
        # Create chunks
        chunks = self._create_chunks(data)
        
        # Build spatial index
        self.spatial_index = self._build_spatial_index(chunks)
        
        # Create virtual data source
        return VirtualDataSource(
            chunks=chunks,
            spatial_index=self.spatial_index,
            cache=self.chunks_cache
        )
    
    def _create_chunks(self, data: pd.DataFrame) -> List['DataChunk']:
        """Split data into manageable chunks."""
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(data), self.chunk_size):
            chunk_data = data.iloc[i:i + self.chunk_size]
            chunk = DataChunk(
                id=chunk_id,
                data=chunk_data,
                start_idx=i,
                end_idx=min(i + self.chunk_size, len(data)),
                bounds=self._calculate_bounds(chunk_data)
            )
            chunks.append(chunk)
            chunk_id += 1
            
        return chunks
    
    def _build_spatial_index(self, chunks: List['DataChunk']) -> 'SpatialIndex':
        """Build spatial index for fast viewport queries."""
        index = SpatialIndex()
        
        for chunk in chunks:
            index.insert(chunk.id, chunk.bounds)
            
        return index
    
    def _calculate_bounds(self, data: pd.DataFrame) -> Tuple[float, float, float, float]:
        """Calculate bounding box for data."""
        if data.empty:
            return (0, 0, 0, 0)
            
        x_min = data.index.min()
        x_max = data.index.max()
        
        # Handle multiple columns
        if len(data.columns) > 1:
            y_min = data.min().min()
            y_max = data.max().max()
        else:
            y_min = data.iloc[:, 0].min()
            y_max = data.iloc[:, 0].max()
            
        # Convert timestamps to numeric if needed
        if hasattr(x_min, 'timestamp'):
            x_min = x_min.timestamp()
            x_max = x_max.timestamp()
            
        return (x_min, y_min, x_max, y_max)
    
    def get_viewport_data(self, 
                         source: 'VirtualDataSource',
                         viewport: ViewportConfig) -> pd.DataFrame:
        """Get only data visible in viewport."""
        # Query spatial index
        chunk_ids = source.spatial_index.query(
            viewport.x_min, viewport.y_min,
            viewport.x_max, viewport.y_max
        )
        
        # Load and combine chunks
        chunks_data = []
        for chunk_id in chunk_ids:
            chunk = source.get_chunk(chunk_id)
            if chunk:
                # Filter to viewport
                filtered = self._filter_chunk_to_viewport(chunk.data, viewport)
                if not filtered.empty:
                    chunks_data.append(filtered)
        
        # Prefetch adjacent chunks
        self._prefetch_adjacent_chunks(source, chunk_ids)
        
        if chunks_data:
            combined = pd.concat(chunks_data)
            # Apply viewport-specific optimizations
            return self._optimize_viewport_data(combined, viewport)
        
        return pd.DataFrame()
    
    def _filter_chunk_to_viewport(self, 
                                 data: pd.DataFrame,
                                 viewport: ViewportConfig) -> pd.DataFrame:
        """Filter chunk data to viewport bounds."""
        # Convert viewport bounds to appropriate format
        if hasattr(data.index[0], 'timestamp'):
            x_min = pd.Timestamp(viewport.x_min, unit='s')
            x_max = pd.Timestamp(viewport.x_max, unit='s')
        else:
            x_min = viewport.x_min
            x_max = viewport.x_max
            
        # Filter by x-axis (usually time)
        mask = (data.index >= x_min) & (data.index <= x_max)
        filtered = data[mask]
        
        # Additional y-axis filtering if needed
        if not filtered.empty and len(filtered.columns) == 1:
            y_mask = (filtered.iloc[:, 0] >= viewport.y_min) & \
                     (filtered.iloc[:, 0] <= viewport.y_max)
            filtered = filtered[y_mask]
            
        return filtered
    
    def _optimize_viewport_data(self,
                               data: pd.DataFrame,
                               viewport: ViewportConfig) -> pd.DataFrame:
        """Optimize data specifically for viewport rendering."""
        if len(data) <= viewport.max_renderable_points:
            return data
            
        # Apply adaptive downsampling
        return self._adaptive_downsample(data, viewport.max_renderable_points)
    
    def _adaptive_downsample(self, 
                            data: pd.DataFrame,
                            target_points: int) -> pd.DataFrame:
        """Adaptively downsample data while preserving features."""
        if len(data) <= target_points:
            return data
            
        # Use LTTB (Largest Triangle Three Buckets) algorithm
        return self._lttb_downsample(data, target_points)
    
    def _lttb_downsample(self, data: pd.DataFrame, target_points: int) -> pd.DataFrame:
        """LTTB downsampling algorithm implementation."""
        if len(data) <= target_points:
            return data
            
        # Convert to numpy for performance
        x = np.arange(len(data))
        y = data.iloc[:, 0].values
        
        # Bucket size
        every = (len(data) - 2) / (target_points - 2)
        
        # Always include first and last
        sampled_indices = [0]
        
        # Bucket processing
        a = 0  # Previous selected point
        
        for i in range(target_points - 2):
            # Calculate bucket range
            avg_range_start = int((i + 1) * every) + 1
            avg_range_end = int((i + 2) * every) + 1
            
            if avg_range_end >= len(data):
                avg_range_end = len(data)
                
            # Calculate average point in next bucket
            avg_x = np.mean(x[avg_range_start:avg_range_end])
            avg_y = np.mean(y[avg_range_start:avg_range_end])
            
            # Find point in current bucket with largest triangle area
            range_start = int(i * every) + 1
            range_end = int((i + 1) * every) + 1
            
            if range_end >= len(data):
                range_end = len(data)
                
            max_area = -1
            max_area_idx = range_start
            
            for j in range(range_start, range_end):
                # Calculate triangle area
                area = abs((x[a] - avg_x) * (y[j] - y[a]) - 
                          (x[a] - x[j]) * (avg_y - y[a])) * 0.5
                
                if area > max_area:
                    max_area = area
                    max_area_idx = j
                    
            sampled_indices.append(max_area_idx)
            a = max_area_idx
            
        # Always include last point
        sampled_indices.append(len(data) - 1)
        
        return data.iloc[sampled_indices]
    
    def _prefetch_adjacent_chunks(self,
                                 source: 'VirtualDataSource',
                                 current_chunks: List[int]):
        """Prefetch adjacent chunks in background."""
        # Determine adjacent chunks
        adjacent = set()
        for chunk_id in current_chunks:
            adjacent.add(chunk_id - 1)
            adjacent.add(chunk_id + 1)
            
        # Remove invalid and already loaded
        adjacent = {c for c in adjacent 
                   if 0 <= c < len(source.chunks) and c not in current_chunks}
        
        # Prefetch in background
        for chunk_id in adjacent:
            self.prefetch_executor.submit(source.get_chunk, chunk_id)


class DataChunk:
    """A chunk of data with metadata."""
    
    def __init__(self, id: int, data: pd.DataFrame, 
                 start_idx: int, end_idx: int,
                 bounds: Tuple[float, float, float, float]):
        self.id = id
        self.data = data
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.bounds = bounds


class VirtualDataSource:
    """Virtual data source for large datasets."""
    
    def __init__(self, chunks: List[DataChunk], 
                 spatial_index: 'SpatialIndex',
                 cache: dict):
        self.chunks = chunks
        self.spatial_index = spatial_index
        self.cache = cache
        
    def get_chunk(self, chunk_id: int) -> Optional[DataChunk]:
        """Get chunk by ID with caching."""
        if chunk_id in self.cache:
            return self.cache[chunk_id]
            
        if 0 <= chunk_id < len(self.chunks):
            chunk = self.chunks[chunk_id]
            self.cache[chunk_id] = chunk
            return chunk
            
        return None


class SpatialIndex:
    """Simple spatial index for viewport queries."""
    
    def __init__(self):
        self.items = {}
        
    def insert(self, item_id: int, bounds: Tuple[float, float, float, float]):
        """Insert item with bounds into index."""
        self.items[item_id] = bounds
        
    def query(self, x_min: float, y_min: float, 
              x_max: float, y_max: float) -> List[int]:
        """Query items intersecting with given bounds."""
        results = []
        
        for item_id, (bx_min, by_min, bx_max, by_max) in self.items.items():
            # Check intersection
            if not (x_max < bx_min or x_min > bx_max or 
                    y_max < by_min or y_min > by_max):
                results.append(item_id)
                
        return results


class LevelOfDetailManager:
    """Manages level-of-detail rendering for charts."""
    
    def __init__(self):
        self.lod_levels = {}
        self.current_level = None
        
    def generate_lod_levels(self, data: pd.DataFrame, 
                           zoom_thresholds: List[float]) -> Dict[float, pd.DataFrame]:
        """Generate LOD levels for different zoom levels."""
        levels = {}
        
        # Full resolution
        levels[max(zoom_thresholds)] = data
        
        # Generate downsampled levels
        for threshold in sorted(zoom_thresholds, reverse=True):
            if threshold < max(zoom_thresholds):
                # Calculate target points based on zoom
                target_points = int(len(data) / (max(zoom_thresholds) / threshold))
                target_points = max(100, min(target_points, len(data)))
                
                # Downsample
                optimizer = ChartPerformanceOptimizer()
                levels[threshold] = optimizer.optimize_data(
                    data, target_points=target_points
                )
                
        self.lod_levels = levels
        return levels
    
    def select_lod_level(self, zoom: float) -> pd.DataFrame:
        """Select appropriate LOD level for zoom."""
        # Find appropriate level
        for threshold in sorted(self.lod_levels.keys(), reverse=True):
            if zoom >= threshold:
                return self.lod_levels[threshold]
                
        # Return lowest detail level
        return self.lod_levels[min(self.lod_levels.keys())]


class ProgressiveRenderer(QObject):
    """Progressive rendering system for large visualizations."""
    
    render_progress = pyqtSignal(float)  # Progress 0-1
    render_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.render_queue = queue.Queue()
        self.is_rendering = False
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._process_render_queue)
        self.render_timer.setInterval(16)  # 60 FPS
        
    def render_progressive(self, data: pd.DataFrame, 
                          render_func: Callable,
                          stages: int = 4):
        """Render data progressively in stages."""
        if self.is_rendering:
            return
            
        self.is_rendering = True
        self.render_queue.queue.clear()
        
        # Create render stages
        data_len = len(data)
        stage_size = data_len // stages
        
        for i in range(stages):
            start = i * stage_size
            end = (i + 1) * stage_size if i < stages - 1 else data_len
            
            stage_data = data.iloc[start:end]
            priority = stages - i  # Higher priority for earlier stages
            
            self.render_queue.put((priority, stage_data, render_func))
            
        # Start rendering
        self.render_timer.start()
        
    def _process_render_queue(self):
        """Process one item from render queue."""
        if self.render_queue.empty():
            self.render_timer.stop()
            self.is_rendering = False
            self.render_complete.emit()
            return
            
        try:
            priority, data, render_func = self.render_queue.get_nowait()
            
            # Render this stage
            render_func(data)
            
            # Update progress
            progress = 1.0 - (self.render_queue.qsize() / 4.0)
            self.render_progress.emit(progress)
            
        except queue.Empty:
            pass


class AnimationOptimizer:
    """Optimizes animations for smooth performance."""
    
    def __init__(self):
        self.frame_budget = 16.67  # 60 FPS target
        self.animation_queue = deque()
        self.frame_skip_threshold = 33.34  # Skip frames if >30 FPS
        
    def optimize_animation(self, animation_func: Callable,
                          duration: float,
                          fps_target: int = 60) -> Callable:
        """Optimize animation for target FPS."""
        frame_time = 1000.0 / fps_target
        
        def optimized_animation(*args, **kwargs):
            start_time = time.perf_counter()
            
            # Execute animation
            result = animation_func(*args, **kwargs)
            
            # Measure frame time
            elapsed = (time.perf_counter() - start_time) * 1000
            
            # Skip frames if necessary
            if elapsed > self.frame_skip_threshold:
                logger.debug(f"Frame took {elapsed:.1f}ms, skipping next frame")
                return None
                
            return result
            
        return optimized_animation


class VisualizationMemoryManager:
    """Manages memory usage for visualizations."""
    
    def __init__(self, memory_limit_mb: int = 200):
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes
        self.cached_items = weakref.WeakValueDictionary()
        self.memory_usage = 0
        
    def should_reduce_quality(self) -> bool:
        """Check if quality should be reduced due to memory pressure."""
        import psutil
        
        # Get current memory usage
        process = psutil.Process()
        current_memory = process.memory_info().rss
        
        # Check if approaching limit
        return current_memory > self.memory_limit * 0.8
        
    def optimize_memory_usage(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        # Downcast numeric types
        for col in data.select_dtypes(include=['float']).columns:
            data[col] = pd.to_numeric(data[col], downcast='float')
            
        for col in data.select_dtypes(include=['int']).columns:
            data[col] = pd.to_numeric(data[col], downcast='integer')
            
        return data


class RealTimePerformanceMonitor(QObject):
    """Real-time performance monitoring and adaptation."""
    
    performance_warning = pyqtSignal(str)
    quality_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.metrics_window = deque(maxlen=100)
        self.quality_level = 'high'
        self.adaptation_enabled = True
        
    def record_frame(self, render_time: float, memory_delta: int,
                    data_points: int):
        """Record frame performance metrics."""
        metrics = PerformanceMetrics(
            render_time=render_time,
            memory_usage=memory_delta,
            fps=1000.0 / render_time if render_time > 0 else 0,
            frame_drops=0,
            data_points_rendered=data_points,
            optimization_level=self.quality_level
        )
        
        self.metrics_window.append(metrics)
        
        # Check if adaptation needed
        if self.adaptation_enabled:
            self._check_adaptation()
            
    def _check_adaptation(self):
        """Check if quality adaptation is needed."""
        if len(self.metrics_window) < 10:
            return
            
        # Calculate recent performance
        recent = list(self.metrics_window)[-10:]
        avg_render_time = np.mean([m.render_time for m in recent])
        avg_fps = np.mean([m.fps for m in recent])
        
        # Adapt quality based on performance
        if avg_fps < 30 and self.quality_level != 'low':
            self.quality_level = 'medium' if self.quality_level == 'high' else 'low'
            self.quality_changed.emit(self.quality_level)
            self.performance_warning.emit(
                f"Reducing quality to {self.quality_level} due to low FPS ({avg_fps:.1f})"
            )
        elif avg_fps > 120 and self.quality_level != 'high':
            self.quality_level = 'medium' if self.quality_level == 'low' else 'high'
            self.quality_changed.emit(self.quality_level)
            
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        if not self.metrics_window:
            return {}
            
        recent = list(self.metrics_window)[-10:]
        
        return {
            'avg_render_time': np.mean([m.render_time for m in recent]),
            'avg_fps': np.mean([m.fps for m in recent]),
            'avg_memory': np.mean([m.memory_usage for m in recent]),
            'quality_level': self.quality_level
        }


class VisualizationPerformanceOptimizer:
    """Main optimization orchestrator for visualizations."""
    
    def __init__(self):
        self.virtualization_engine = ChartVirtualizationEngine()
        self.lod_manager = LevelOfDetailManager()
        self.animation_optimizer = AnimationOptimizer()
        self.memory_manager = VisualizationMemoryManager()
        self.performance_monitor = RealTimePerformanceMonitor()
        self.progressive_renderer = ProgressiveRenderer()
        
    def optimize_chart_rendering(self, 
                               chart: Any,
                               data: pd.DataFrame,
                               viewport: Optional[ViewportConfig] = None) -> Any:
        """Apply comprehensive optimizations to chart rendering."""
        start_time = time.perf_counter()
        
        # Profile data
        profile = self._profile_data(data)
        
        # Choose optimization strategy
        if profile.point_count > 1_000_000:
            # Use full virtualization
            optimized_data = self._apply_virtualization(data, viewport)
        elif profile.point_count > 100_000:
            # Use LOD + progressive
            optimized_data = self._apply_lod_progressive(data, viewport)
        elif profile.point_count > 10_000:
            # Use adaptive downsampling
            optimized_data = self._apply_adaptive_optimization(data, viewport)
        else:
            # Minimal optimization
            optimized_data = self.memory_manager.optimize_memory_usage(data)
            
        # Record performance
        render_time = (time.perf_counter() - start_time) * 1000
        self.performance_monitor.record_frame(
            render_time, 0, len(optimized_data)
        )
        
        return optimized_data
        
    def _profile_data(self, data: pd.DataFrame) -> DataProfile:
        """Profile dataset characteristics."""
        if data.empty:
            return DataProfile(
                point_count=0, time_range=pd.Timedelta(0), density=0,
                has_gaps=False, is_regular=True, memory_size=0,
                value_range=(0, 0), is_time_series=False,
                has_integer_values=False, has_float_values=False,
                benefits_from_aggregation=False
            )
            
        # Analyze data
        is_time_series = isinstance(data.index, pd.DatetimeIndex)
        
        if is_time_series:
            time_range = data.index[-1] - data.index[0]
            density = len(data) / time_range.total_seconds()
            
            # Check for gaps
            diffs = data.index.to_series().diff()
            has_gaps = diffs.std() > diffs.mean() * 0.1
            is_regular = not has_gaps
        else:
            time_range = pd.Timedelta(0)
            density = len(data)
            has_gaps = False
            is_regular = True
            
        # Memory usage
        memory_size = data.memory_usage(deep=True).sum()
        
        # Value analysis
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            value_range = (
                numeric_data.min().min(),
                numeric_data.max().max()
            )
            has_integer_values = any(data[col].dtype.kind == 'i' 
                                    for col in numeric_data.columns)
            has_float_values = any(data[col].dtype.kind == 'f' 
                                  for col in numeric_data.columns)
        else:
            value_range = (0, 0)
            has_integer_values = False
            has_float_values = False
            
        # Aggregation benefit analysis
        benefits_from_aggregation = (
            is_time_series and 
            density > 1 and  # More than 1 point per second
            len(data) > 10000
        )
        
        return DataProfile(
            point_count=len(data),
            time_range=time_range,
            density=density,
            has_gaps=has_gaps,
            is_regular=is_regular,
            memory_size=memory_size,
            value_range=value_range,
            is_time_series=is_time_series,
            has_integer_values=has_integer_values,
            has_float_values=has_float_values,
            benefits_from_aggregation=benefits_from_aggregation
        )
        
    def _apply_virtualization(self, 
                             data: pd.DataFrame,
                             viewport: Optional[ViewportConfig]) -> pd.DataFrame:
        """Apply full virtualization for very large datasets."""
        # Setup virtual data source
        virtual_source = self.virtualization_engine.setup_virtualization(data)
        
        if viewport:
            # Get only viewport data
            return self.virtualization_engine.get_viewport_data(
                virtual_source, viewport
            )
        else:
            # Return heavily downsampled overview
            target_points = 1000
            return self.virtualization_engine._adaptive_downsample(
                data, target_points
            )
            
    def _apply_lod_progressive(self,
                              data: pd.DataFrame,
                              viewport: Optional[ViewportConfig]) -> pd.DataFrame:
        """Apply LOD with progressive rendering."""
        # Generate LOD levels
        zoom_thresholds = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        lod_levels = self.lod_manager.generate_lod_levels(data, zoom_thresholds)
        
        # Select appropriate level
        zoom = viewport.zoom_level if viewport else 1.0
        return self.lod_manager.select_lod_level(zoom)
        
    def _apply_adaptive_optimization(self,
                                   data: pd.DataFrame,
                                   viewport: Optional[ViewportConfig]) -> pd.DataFrame:
        """Apply adaptive optimization for medium datasets."""
        # Check memory pressure
        if self.memory_manager.should_reduce_quality():
            # Aggressive downsampling
            target_points = 1000
        else:
            # Moderate downsampling
            target_points = 5000 if viewport else 10000
            
        # Use LTTB algorithm
        return self.virtualization_engine._lttb_downsample(data, target_points)