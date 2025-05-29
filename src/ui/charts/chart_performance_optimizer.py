"""
Chart performance optimization utilities.

This module provides optimizations specifically for chart rendering
including data reduction algorithms and caching strategies.
"""

import numpy as np
import pandas as pd
from typing import Optional, Union, Literal, Dict, Any, Tuple
import hashlib
import pickle
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ChartPerformanceOptimizer:
    """Optimizes chart data for improved rendering performance."""
    
    def __init__(self):
        self.cache = {}
        self.optimization_stats = {
            'total_optimizations': 0,
            'total_time_saved': 0,
            'total_memory_saved': 0
        }
        
    def optimize_data(self, 
                     data: pd.DataFrame,
                     target_points: Optional[int] = None,
                     algorithm: Literal['lttb', 'decimation', 'aggregation', 'auto'] = 'auto',
                     preserve_peaks: bool = True) -> pd.DataFrame:
        """
        Optimize data for chart rendering.
        
        Args:
            data: Input DataFrame
            target_points: Target number of points (auto-calculated if None)
            algorithm: Downsampling algorithm to use
            preserve_peaks: Whether to preserve local maxima/minima
            
        Returns:
            Optimized DataFrame
        """
        if data.empty:
            return data
            
        # Auto-calculate target points if not provided
        if target_points is None:
            target_points = self._calculate_optimal_points(len(data))
            
        # Skip if already optimal
        if len(data) <= target_points:
            return data
            
        # Check cache
        cache_key = self._generate_cache_key(data, target_points, algorithm)
        if cache_key in self.cache:
            logger.debug(f"Using cached optimization for {len(data)} points")
            return self.cache[cache_key]
            
        # Select algorithm
        if algorithm == 'auto':
            algorithm = self._select_algorithm(data, target_points)
            
        # Apply optimization
        if algorithm == 'lttb':
            optimized = self._lttb_downsample(data, target_points, preserve_peaks)
        elif algorithm == 'decimation':
            optimized = self._decimation_downsample(data, target_points)
        elif algorithm == 'aggregation':
            optimized = self._aggregation_downsample(data, target_points)
        else:
            optimized = data
            
        # Cache result
        self.cache[cache_key] = optimized
        
        # Update stats
        self.optimization_stats['total_optimizations'] += 1
        self.optimization_stats['total_memory_saved'] += \
            data.memory_usage(deep=True).sum() - optimized.memory_usage(deep=True).sum()
            
        logger.info(f"Optimized {len(data)} points to {len(optimized)} using {algorithm}")
        
        return optimized
        
    def _calculate_optimal_points(self, data_length: int) -> int:
        """Calculate optimal number of points based on data size."""
        if data_length <= 1000:
            return data_length
        elif data_length <= 10000:
            return 2000
        elif data_length <= 100000:
            return 5000
        else:
            return 10000
            
    def _select_algorithm(self, data: pd.DataFrame, target_points: int) -> str:
        """Select best algorithm based on data characteristics."""
        compression_ratio = len(data) / target_points
        
        # For time series data
        if isinstance(data.index, pd.DatetimeIndex):
            if compression_ratio > 100:
                return 'aggregation'  # Heavy compression needs aggregation
            elif compression_ratio > 10:
                return 'lttb'  # Moderate compression with shape preservation
            else:
                return 'decimation'  # Light compression
        else:
            # Non-time series data
            return 'lttb' if compression_ratio > 5 else 'decimation'
            
    def _generate_cache_key(self, data: pd.DataFrame, 
                           target_points: int, algorithm: str) -> str:
        """Generate cache key for optimization result."""
        # Create hash of data characteristics
        data_hash = hashlib.md5(
            f"{len(data)}_{data.index[0]}_{data.index[-1]}_{target_points}_{algorithm}".encode()
        ).hexdigest()
        return data_hash
        
    def _lttb_downsample(self, data: pd.DataFrame, 
                        target_points: int,
                        preserve_peaks: bool = True) -> pd.DataFrame:
        """
        Largest Triangle Three Buckets (LTTB) downsampling.
        
        This algorithm is excellent for preserving the visual shape of time series.
        """
        if len(data) <= target_points:
            return data
            
        # Handle multi-column data
        if len(data.columns) > 1:
            # Apply LTTB to each column
            results = []
            for col in data.columns:
                col_data = data[[col]]
                downsampled = self._lttb_single_series(col_data, target_points)
                results.append(downsampled)
            
            # Merge on index
            result = results[0]
            for df in results[1:]:
                result = result.join(df, how='outer')
            return result.sort_index()
        else:
            return self._lttb_single_series(data, target_points)
            
    def _lttb_single_series(self, data: pd.DataFrame, target_points: int) -> pd.DataFrame:
        """LTTB implementation for single series."""
        n = len(data)
        
        # Convert to numpy for performance
        x = np.arange(n)
        y = data.iloc[:, 0].values
        
        # Bucket size
        every = (n - 2) / (target_points - 2)
        
        # Always include first and last points
        sampled_indices = [0]
        
        # Previous selected point
        a = 0
        
        for i in range(target_points - 2):
            # Calculate average point in next bucket
            avg_range_start = int((i + 1) * every) + 1
            avg_range_end = int((i + 2) * every) + 1
            avg_range_end = min(avg_range_end, n)
            
            avg_x = np.mean(x[avg_range_start:avg_range_end])
            avg_y = np.mean(y[avg_range_start:avg_range_end])
            
            # Calculate point in current bucket with largest triangle area
            range_start = int(i * every) + 1
            range_end = int((i + 1) * every) + 1
            range_end = min(range_end, n)
            
            # Vectorized triangle area calculation
            areas = 0.5 * np.abs(
                (x[a] - avg_x) * (y[range_start:range_end] - y[a]) -
                (x[a] - x[range_start:range_end]) * (avg_y - y[a])
            )
            
            max_area_idx = range_start + np.argmax(areas)
            sampled_indices.append(max_area_idx)
            a = max_area_idx
            
        # Always include last point
        sampled_indices.append(n - 1)
        
        return data.iloc[sampled_indices]
        
    def _decimation_downsample(self, data: pd.DataFrame, 
                              target_points: int) -> pd.DataFrame:
        """Simple decimation downsampling - takes every nth point."""
        n = len(data)
        step = max(1, n // target_points)
        
        # Always include first and last points
        indices = list(range(0, n - 1, step))
        if indices[-1] != n - 1:
            indices.append(n - 1)
            
        return data.iloc[indices]
        
    def _aggregation_downsample(self, data: pd.DataFrame, 
                               target_points: int) -> pd.DataFrame:
        """Aggregation-based downsampling for time series."""
        if not isinstance(data.index, pd.DatetimeIndex):
            # Fall back to decimation for non-time series
            return self._decimation_downsample(data, target_points)
            
        # Calculate appropriate frequency
        time_range = data.index[-1] - data.index[0]
        target_freq = time_range / target_points
        
        # Convert to pandas frequency string
        if target_freq.total_seconds() < 60:
            freq = f"{int(target_freq.total_seconds())}s"
        elif target_freq.total_seconds() < 3600:
            freq = f"{int(target_freq.total_seconds() / 60)}min"
        elif target_freq.total_seconds() < 86400:
            freq = f"{int(target_freq.total_seconds() / 3600)}h"
        else:
            freq = f"{int(target_freq.total_seconds() / 86400)}D"
            
        # Resample with appropriate aggregation
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        agg_dict = {col: ['mean', 'min', 'max'] for col in numeric_cols}
        
        resampled = data.resample(freq).agg(agg_dict)
        
        # Flatten multi-level columns
        resampled.columns = ['_'.join(col).strip() for col in resampled.columns.values]
        
        # Select mean values as primary (include min/max for reference)
        mean_cols = [col for col in resampled.columns if col.endswith('_mean')]
        result_cols = []
        
        for mean_col in mean_cols:
            base_name = mean_col.replace('_mean', '')
            # Rename mean column to original name
            resampled[base_name] = resampled[mean_col]
            result_cols.append(base_name)
            
        return resampled[result_cols]
        
    def optimize_for_viewport(self, data: pd.DataFrame,
                            viewport_start: Any,
                            viewport_end: Any,
                            viewport_pixels: int = 1000) -> pd.DataFrame:
        """Optimize data specifically for viewport rendering."""
        # Filter to viewport
        if isinstance(data.index, pd.DatetimeIndex):
            viewport_data = data[
                (data.index >= viewport_start) & (data.index <= viewport_end)
            ]
        else:
            viewport_data = data.iloc[viewport_start:viewport_end]
            
        # Calculate optimal points for viewport
        # 2-3 data points per pixel is optimal
        target_points = min(len(viewport_data), viewport_pixels * 2)
        
        return self.optimize_data(viewport_data, target_points)
        
    def clear_cache(self):
        """Clear optimization cache."""
        self.cache.clear()
        logger.info("Cleared optimization cache")
        
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            **self.optimization_stats,
            'cache_size': len(self.cache),
            'cache_memory_mb': sum(
                df.memory_usage(deep=True).sum() / 1024 / 1024
                for df in self.cache.values()
            )
        }


class AdaptiveDataOptimizer:
    """Adaptive optimization that adjusts based on rendering performance."""
    
    def __init__(self):
        self.optimizer = ChartPerformanceOptimizer()
        self.performance_history = []
        self.quality_level = 'high'
        
    def optimize_adaptive(self, data: pd.DataFrame,
                         last_render_time: Optional[float] = None,
                         target_render_time: float = 200.0) -> pd.DataFrame:
        """
        Adaptively optimize based on rendering performance.
        
        Args:
            data: Input data
            last_render_time: Last frame render time in ms
            target_render_time: Target render time in ms
            
        Returns:
            Optimized data
        """
        # Record performance
        if last_render_time is not None:
            self.performance_history.append(last_render_time)
            
        # Adjust quality based on performance
        if len(self.performance_history) >= 5:
            avg_render_time = np.mean(self.performance_history[-5:])
            
            if avg_render_time > target_render_time * 1.5:
                # Too slow - reduce quality
                if self.quality_level == 'high':
                    self.quality_level = 'medium'
                elif self.quality_level == 'medium':
                    self.quality_level = 'low'
            elif avg_render_time < target_render_time * 0.5:
                # Too fast - increase quality
                if self.quality_level == 'low':
                    self.quality_level = 'medium'
                elif self.quality_level == 'medium':
                    self.quality_level = 'high'
                    
        # Apply optimization based on quality level
        quality_settings = {
            'high': {'ratio': 0.8, 'algorithm': 'lttb'},
            'medium': {'ratio': 0.5, 'algorithm': 'lttb'},
            'low': {'ratio': 0.2, 'algorithm': 'decimation'}
        }
        
        settings = quality_settings[self.quality_level]
        target_points = int(len(data) * settings['ratio'])
        
        return self.optimizer.optimize_data(
            data, 
            target_points=target_points,
            algorithm=settings['algorithm']
        )