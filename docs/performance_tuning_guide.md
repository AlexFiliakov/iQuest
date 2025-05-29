# Visualization Performance Tuning Guide

This guide provides comprehensive information on optimizing visualization performance in the Apple Health Monitor application, particularly when working with large health datasets.

## Table of Contents

1. [Overview](#overview)
2. [Performance Features](#performance-features)
3. [Configuration Options](#configuration-options)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Tuning](#advanced-tuning)

## Overview

The Apple Health Monitor includes sophisticated performance optimization features designed to handle datasets ranging from thousands to millions of data points while maintaining smooth, responsive visualizations.

### Key Performance Metrics

- **Target Render Time**: < 200ms for datasets up to 100K points
- **Memory Usage**: < 200MB for large visualizations
- **Frame Rate**: 60 FPS for animations and interactions
- **Progressive Loading**: First paint within 50ms

## Performance Features

### 1. Automatic Optimization

The application automatically optimizes performance based on dataset size:

- **Small datasets (< 10K points)**: Full resolution rendering
- **Medium datasets (10K - 100K points)**: Adaptive downsampling with LTTB algorithm
- **Large datasets (> 100K points)**: Viewport-based virtualization

### 2. Adaptive Renderer Selection

The system intelligently selects the optimal rendering backend:

```python
# The ComponentFactory automatically chooses the best renderer
factory = ComponentFactory()
chart = factory.create_adaptive_chart(data, chart_type='line')
```

Available renderers:
- **Matplotlib**: High-quality static charts (< 50K points)
- **PyQtGraph**: Real-time interactive charts (< 1M points) 
- **Canvas**: Custom high-performance rendering (< 500K points)
- **WebGL**: GPU-accelerated for massive datasets (> 1M points)

### 3. Data Optimization Algorithms

#### LTTB (Largest Triangle Three Buckets)
Best for time series data, preserves visual shape while reducing points:

```python
from src.ui.component_factory import ComponentFactory

factory = ComponentFactory()
optimized_data = factory.optimize_chart_data(
    data, 
    target_points=5000,
    algorithm='lttb'
)
```

#### Aggregation-based Downsampling
For heavily compressed views:

```python
optimized_data = factory.optimize_chart_data(
    data,
    target_points=1000, 
    algorithm='aggregation'
)
```

### 4. Progressive Rendering

For large datasets, charts render progressively:

1. **Stage 1**: Axes and grid (instant)
2. **Stage 2**: Low-resolution preview (< 50ms)
3. **Stage 3**: Medium resolution (< 200ms)
4. **Stage 4**: Full resolution (background)

### 5. Viewport-based Virtualization

For datasets over 100K points, only visible data is rendered:

- Automatic chunking and spatial indexing
- Predictive prefetching for smooth scrolling
- Memory-mapped storage for huge datasets

## Configuration Options

### Global Settings

Enable/disable optimization features:

```python
from src.ui.component_factory import ComponentFactory

factory = ComponentFactory()

# Enable/disable automatic optimization
factory.set_optimization_enabled(True)

# Check current performance stats
stats = factory.get_performance_stats()
print(f"Current renderer: {stats['current_renderer']}")
print(f"Average render time: {stats['avg_render_time']}ms")
```

### Chart-specific Settings

When creating charts, specify expected data size for optimal setup:

```python
# Create optimized chart for large dataset
chart = factory.create_line_chart(
    config=chart_config,
    data_size=150000  # Triggers OptimizedLineChart
)

# Enable specific features
if hasattr(chart, 'setVisualizationEnabled'):
    chart.setVisualizationEnabled(True)
    chart.setProgressiveRenderingEnabled(True)
    chart.setAdaptiveQualityEnabled(True)
```

## Best Practices

### 1. Data Preparation

- **Pre-filter data**: Only load necessary date ranges and metrics
- **Use appropriate data types**: Int8/Int16 for counts, Float32 for most metrics
- **Index by time**: Ensure time-based data has datetime index

### 2. Chart Selection

Choose the right chart type for your data:

- **Line charts**: Best for continuous time series
- **Bar charts**: Good for categorical comparisons
- **Scatter plots**: Efficient for correlation analysis
- **Heatmaps**: Ideal for patterns across two dimensions

### 3. Memory Management

- **Clear unused charts**: Explicitly clear charts when switching views
- **Limit concurrent charts**: Avoid rendering more than 4-6 charts simultaneously
- **Use data windows**: For real-time data, maintain rolling windows

### 4. Interaction Optimization

- **Debounce updates**: Limit update frequency during interactions
- **Disable animations**: For slower systems, disable smooth transitions
- **Use viewport hints**: Provide expected zoom/pan ranges

## Troubleshooting

### Slow Rendering

1. **Check data size**: 
   ```python
   print(f"Data points: {len(data)}")
   ```

2. **Monitor performance**:
   ```python
   stats = chart.getPerformanceStats() if hasattr(chart, 'getPerformanceStats') else {}
   print(f"FPS: {stats.get('current_fps', 'N/A')}")
   ```

3. **Force optimization**:
   ```python
   optimized = factory.optimize_chart_data(data, target_points=5000)
   ```

### High Memory Usage

1. **Enable memory monitoring**:
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

2. **Clear cache**:
   ```python
   factory.performance_optimizer.clear_cache()
   ```

3. **Use typed arrays**: Convert DataFrames to optimized structures

### Visual Artifacts

1. **Adjust quality settings**: Increase target points for optimization
2. **Disable LOD transitions**: Set fixed detail level
3. **Check renderer compatibility**: Some systems may need fallback renderers

## Advanced Tuning

### Custom Optimization Strategies

Create custom optimization for specific use cases:

```python
from src.ui.charts.chart_performance_optimizer import ChartPerformanceOptimizer

class CustomOptimizer(ChartPerformanceOptimizer):
    def optimize_data(self, data, target_points=None, **kwargs):
        # Custom optimization logic
        if 'heart_rate' in data.columns:
            # Special handling for heart rate data
            return self._optimize_heart_rate(data, target_points)
        return super().optimize_data(data, target_points, **kwargs)
```

### Performance Profiling

Enable detailed profiling:

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Render charts
chart = factory.create_adaptive_chart(large_data, 'line')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 time consumers
```

### Memory Optimization

For extremely large datasets:

```python
from src.ui.charts.optimized_data_structures import ChunkedDataStore

# Use chunked storage
store = ChunkedDataStore(chunk_size=100000)
store.add_data(timestamps, values)

# Query only needed range
visible_data = store.query_range(start_time, end_time)
```

### GPU Acceleration

Enable GPU acceleration when available:

```python
import os
os.environ['PYQTGRAPH_USE_OPENGL'] = '1'

# Charts will automatically use GPU when beneficial
```

## Performance Benchmarks

Expected performance for different data sizes:

| Data Points | Render Time | Memory Usage | Recommended Approach |
|-------------|-------------|--------------|---------------------|
| < 1K        | < 16ms      | < 10MB       | Direct rendering    |
| 1K - 10K    | < 50ms      | < 50MB       | Minimal optimization|
| 10K - 100K  | < 200ms     | < 100MB      | LTTB downsampling   |
| 100K - 1M   | < 500ms     | < 200MB      | Virtualization      |
| > 1M        | < 1000ms    | < 500MB      | GPU + Virtualization|

## Summary

The visualization performance optimization system provides:

1. **Automatic optimization** based on data characteristics
2. **Multiple rendering backends** for different use cases
3. **Progressive rendering** for immediate feedback
4. **Memory-efficient structures** for large datasets
5. **Real-time adaptation** based on system performance

By following these guidelines and leveraging the built-in optimization features, you can maintain smooth, responsive visualizations even with very large health datasets.