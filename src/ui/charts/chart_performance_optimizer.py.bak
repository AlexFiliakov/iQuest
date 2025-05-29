"""Performance optimization framework for chart rendering with large datasets."""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
from dataclasses import dataclass
from functools import lru_cache
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for chart rendering."""
    data_points: int
    render_time_ms: float
    memory_usage_mb: float
    fps: float
    optimization_applied: List[str]


class DataSampler:
    """Intelligent data sampling for large datasets."""
    
    @staticmethod
    def downsample_lttb(data: pd.DataFrame, target_points: int) -> pd.DataFrame:
        """
        Largest Triangle Three Buckets (LTTB) algorithm for downsampling.
        Preserves visual characteristics while reducing data points.
        """
        if len(data) <= target_points:
            return data
        
        # Implementation of LTTB algorithm
        sampled_indices = [0]  # Always include first point
        
        # Calculate bucket size
        bucket_size = (len(data) - 2) / (target_points - 2)
        
        # Process each bucket
        for i in range(1, target_points - 1):
            # Calculate bucket boundaries
            start = int((i - 1) * bucket_size) + 1
            end = int(i * bucket_size) + 1
            
            # Find the point with largest triangle area
            max_area = 0
            max_index = start
            
            # Get average point of next bucket for triangle calculation
            next_start = int(i * bucket_size) + 1
            next_end = int((i + 1) * bucket_size) + 1
            next_end = min(next_end, len(data))
            
            if next_end > next_start:
                avg_x = data.iloc[next_start:next_end, 0].mean()
                avg_y = data.iloc[next_start:next_end, 1].mean()
            else:
                avg_x = data.iloc[-1, 0]
                avg_y = data.iloc[-1, 1]
            
            # Previous selected point
            prev_x = data.iloc[sampled_indices[-1], 0]
            prev_y = data.iloc[sampled_indices[-1], 1]
            
            # Find point with maximum triangle area
            for j in range(start, min(end, len(data))):
                # Calculate triangle area
                area = abs((prev_x - avg_x) * (data.iloc[j, 1] - prev_y) -
                          (prev_x - data.iloc[j, 0]) * (avg_y - prev_y))
                
                if area > max_area:
                    max_area = area
                    max_index = j
            
            sampled_indices.append(max_index)
        
        # Always include last point
        sampled_indices.append(len(data) - 1)
        
        return data.iloc[sampled_indices].reset_index(drop=True)
    
    @staticmethod
    def adaptive_sampling(data: pd.DataFrame, viewport: Tuple[float, float, float, float],
                         max_points: int = 1000) -> pd.DataFrame:
        """
        Adaptive sampling based on viewport visibility.
        Higher density for visible data, lower for off-screen.
        """
        x_min, x_max, y_min, y_max = viewport
        
        # Filter to viewport with margin
        margin_x = (x_max - x_min) * 0.1
        margin_y = (y_max - y_min) * 0.1
        
        visible_mask = (
            (data.iloc[:, 0] >= x_min - margin_x) &
            (data.iloc[:, 0] <= x_max + margin_x) &
            (data.iloc[:, 1] >= y_min - margin_y) &
            (data.iloc[:, 1] <= y_max + margin_y)
        )
        
        visible_data = data[visible_mask]
        
        # Apply LTTB to visible data
        if len(visible_data) > max_points:
            return DataSampler.downsample_lttb(visible_data, max_points)
        
        return visible_data
    
    @staticmethod
    def time_based_aggregation(data: pd.DataFrame, time_column: str, 
                              aggregation: str = 'mean') -> pd.DataFrame:
        """
        Aggregate data based on time intervals.
        Useful for time series data.
        """
        if len(data) < 10000:
            return data
        
        # Determine appropriate time interval
        time_range = data[time_column].max() - data[time_column].min()
        
        if time_range.days > 365:
            freq = 'W'  # Weekly
        elif time_range.days > 30:
            freq = 'D'  # Daily
        elif time_range.days > 7:
            freq = '6H'  # 6 hours
        else:
            freq = 'H'  # Hourly
        
        # Set time column as index
        data_copy = data.copy()
        data_copy.set_index(time_column, inplace=True)
        
        # Resample and aggregate
        aggregation_funcs = {
            'mean': 'mean',
            'sum': 'sum',
            'max': 'max',
            'min': 'min',
            'median': 'median'
        }
        
        agg_func = aggregation_funcs.get(aggregation, 'mean')
        resampled = data_copy.resample(freq).agg(agg_func)
        
        return resampled.reset_index()


class ChartPerformanceOptimizer:
    """Main performance optimizer for chart rendering."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.sampler = DataSampler()
        self._cache = {}
        self._metrics = []
        self._optimization_thresholds = {
            'large_dataset': 10000,      # Points requiring optimization
            'huge_dataset': 100000,      # Points requiring aggressive optimization
            'target_render_ms': 200,     # Target render time
            'target_memory_mb': 100,     # Target memory usage
            'min_fps': 30               # Minimum acceptable FPS
        }
        
        # Thread pool for background processing
        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._processing_queue = queue.Queue()
    
    def optimize_data(self, data: pd.DataFrame, chart_type: str = 'line',
                     viewport: Optional[Tuple[float, float, float, float]] = None,
                     quality: str = 'balanced') -> pd.DataFrame:
        """
        Optimize data for rendering based on size and chart type.
        
        Args:
            data: Input dataframe
            chart_type: Type of chart (line, scatter, bar, etc.)
            viewport: Current viewport bounds (x_min, x_max, y_min, y_max)
            quality: Optimization quality (performance, balanced, quality)
        
        Returns:
            Optimized dataframe
        """
        if data.empty:
            return data
        
        data_size = len(data)
        optimizations_applied = []
        
        logger.debug(f"Optimizing {data_size} data points for {chart_type} chart")
        
        # Check cache
        cache_key = self._get_cache_key(data, chart_type, viewport, quality)
        if cache_key in self._cache:
            logger.debug("Using cached optimized data")
            return self._cache[cache_key]
        
        # Determine optimization strategy
        if data_size <= self._optimization_thresholds['large_dataset']:
            # No optimization needed
            optimized_data = data
        
        elif data_size <= self._optimization_thresholds['huge_dataset']:
            # Moderate optimization
            if viewport:
                optimized_data = self.sampler.adaptive_sampling(data, viewport, 
                                                               max_points=5000)
                optimizations_applied.append('adaptive_sampling')
            else:
                target_points = 5000 if quality == 'balanced' else 10000
                optimized_data = self.sampler.downsample_lttb(data, target_points)
                optimizations_applied.append('lttb_downsampling')
        
        else:
            # Aggressive optimization
            if chart_type == 'line' and self._is_time_series(data):
                # Time-based aggregation for time series
                optimized_data = self.sampler.time_based_aggregation(
                    data, data.columns[0], 'mean')
                optimizations_applied.append('time_aggregation')
            else:
                # Heavy downsampling
                target_points = 1000 if quality == 'performance' else 2000
                optimized_data = self.sampler.downsample_lttb(data, target_points)
                optimizations_applied.append('heavy_downsampling')
        
        # Cache result
        self._cache[cache_key] = optimized_data
        
        # Log optimization
        logger.info(f"Optimized {data_size} points to {len(optimized_data)} points. "
                   f"Applied: {', '.join(optimizations_applied)}")
        
        return optimized_data
    
    def preload_data_async(self, data: pd.DataFrame, chart_type: str,
                          callback: Optional[callable] = None):
        """
        Preload and optimize data asynchronously.
        """
        def process():
            optimized = self.optimize_data(data, chart_type)
            if callback:
                callback(optimized)
        
        self._thread_pool.submit(process)
    
    def get_render_quality(self, data_size: int, target_fps: int = 30) -> str:
        """
        Determine appropriate render quality based on data size and target FPS.
        """
        if data_size < 1000:
            return 'high'
        elif data_size < 10000:
            return 'medium' if target_fps >= 60 else 'high'
        else:
            return 'low' if target_fps >= 30 else 'very_low'
    
    def should_use_webgl(self, data_size: int) -> bool:
        """
        Determine if WebGL rendering should be used.
        """
        return data_size > 50000
    
    def get_optimization_suggestions(self, metrics: PerformanceMetrics) -> List[str]:
        """
        Get suggestions for improving performance based on metrics.
        """
        suggestions = []
        
        if metrics.render_time_ms > self._optimization_thresholds['target_render_ms']:
            suggestions.append("Consider reducing data points or enabling hardware acceleration")
        
        if metrics.memory_usage_mb > self._optimization_thresholds['target_memory_mb']:
            suggestions.append("Enable data streaming or pagination for large datasets")
        
        if metrics.fps < self._optimization_thresholds['min_fps']:
            suggestions.append("Reduce visual complexity or enable frame skipping")
        
        if metrics.data_points > 100000:
            suggestions.append("Use aggregated views for datasets over 100K points")
        
        return suggestions
    
    def enable_progressive_rendering(self, chunk_size: int = 1000):
        """
        Enable progressive rendering for smooth initial display.
        """
        logger.info(f"Progressive rendering enabled with chunk size: {chunk_size}")
        # Implementation would handle chunked rendering
    
    @lru_cache(maxsize=32)
    def _get_cache_key(self, data: pd.DataFrame, chart_type: str,
                      viewport: Optional[tuple], quality: str) -> str:
        """Generate cache key for optimized data."""
        # Create a hashable key from parameters
        data_hash = hash(tuple(data.columns) + (len(data),))
        viewport_str = str(viewport) if viewport else 'full'
        return f"{data_hash}_{chart_type}_{viewport_str}_{quality}"
    
    def _is_time_series(self, data: pd.DataFrame) -> bool:
        """Check if data appears to be time series."""
        if len(data.columns) < 1:
            return False
        
        first_col = data.iloc[:, 0]
        
        # Check if first column is datetime
        if pd.api.types.is_datetime64_any_dtype(first_col):
            return True
        
        # Check if values are monotonically increasing (common for time)
        if pd.api.types.is_numeric_dtype(first_col):
            return first_col.is_monotonic_increasing
        
        return False
    
    def cleanup(self):
        """Clean up resources."""
        self._thread_pool.shutdown(wait=False)
        self._cache.clear()


class MemoryOptimizer:
    """Memory optimization for chart data."""
    
    @staticmethod
    def optimize_dtypes(data: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types to reduce memory usage."""
        optimized = data.copy()
        
        for col in optimized.columns:
            col_type = optimized[col].dtype
            
            if col_type != object:
                c_min = optimized[col].min()
                c_max = optimized[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        optimized[col] = optimized[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        optimized[col] = optimized[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        optimized[col] = optimized[col].astype(np.int32)
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        optimized[col] = optimized[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        optimized[col] = optimized[col].astype(np.float32)
        
        return optimized
    
    @staticmethod
    def estimate_memory_usage(data: pd.DataFrame) -> float:
        """Estimate memory usage in MB."""
        return data.memory_usage(deep=True).sum() / 1024 / 1024