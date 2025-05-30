#!/usr/bin/env python3
"""
Run performance benchmarks and establish baselines.

This script runs a subset of performance benchmarks to establish
baseline metrics for visualization performance.
"""

import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.charts import LineChart, EnhancedLineChart
from src.ui.charts.chart_performance_optimizer import ChartPerformanceOptimizer
from src.ui.charts.adaptive_chart_renderer import AdaptiveChartRenderer
from src.ui.charts.optimized_line_chart import OptimizedLineChart
from src.ui.charts.visualization_performance_optimizer import VisualizationPerformanceOptimizer

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QSize

# Set offscreen platform for headless operation
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Ensure Qt Application exists
app = QApplication.instance() or QApplication(sys.argv)


def generate_test_data(points: int) -> pd.DataFrame:
    """Generate test time series data."""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=points//24),
        periods=points,
        freq='h'
    )
    
    # Generate realistic health metric data
    base_value = 70  # Base heart rate
    noise = np.random.normal(0, 5, points)
    trend = np.sin(np.linspace(0, 10*np.pi, points)) * 10
    values = base_value + trend + noise
    
    return pd.DataFrame({
        'timestamp': dates,
        'heart_rate': values,
        'steps': np.random.poisson(100, points),
        'calories': np.random.normal(100, 20, points)
    }).set_index('timestamp')


def benchmark_chart(chart_class, data: pd.DataFrame, name: str) -> dict:
    """Benchmark a single chart rendering."""
    widget = QWidget()
    widget.resize(QSize(800, 600))
    
    # Measure render time
    start_time = time.perf_counter()
    start_memory = 0  # Would need psutil for real memory tracking
    
    try:
        chart = chart_class()
        chart.update_chart(data[['heart_rate']], f"{name} Test", widget)
        
        render_time = (time.perf_counter() - start_time) * 1000  # ms
        
        return {
            'success': True,
            'render_time': render_time,
            'data_points': len(data),
            'chart_type': name
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data_points': len(data),
            'chart_type': name
        }


def run_benchmarks():
    """Run performance benchmarks."""
    results = []
    
    # Test different data sizes
    data_sizes = [100, 1000, 5000, 10000, 50000, 100000]
    
    print("Running Performance Benchmarks")
    print("=" * 50)
    
    for size in data_sizes:
        print(f"\nTesting with {size} data points:")
        data = generate_test_data(size)
        
        # Test standard LineChart
        result = benchmark_chart(LineChart, data, "LineChart")
        if result['success']:
            print(f"  LineChart: {result['render_time']:.1f}ms")
        else:
            print(f"  LineChart: FAILED - {result['error']}")
        results.append(result)
        
        # Test EnhancedLineChart
        result = benchmark_chart(EnhancedLineChart, data, "EnhancedLineChart")
        if result['success']:
            print(f"  EnhancedLineChart: {result['render_time']:.1f}ms")
        else:
            print(f"  EnhancedLineChart: FAILED - {result['error']}")
        results.append(result)
        
        # Test OptimizedLineChart
        result = benchmark_chart(OptimizedLineChart, data, "OptimizedLineChart")
        if result['success']:
            print(f"  OptimizedLineChart: {result['render_time']:.1f}ms")
        else:
            print(f"  OptimizedLineChart: FAILED - {result['error']}")
        results.append(result)
    
    # Test optimization impact
    print("\n\nTesting Optimization Impact:")
    print("-" * 50)
    
    large_data = generate_test_data(50000)
    optimizer = ChartPerformanceOptimizer()
    
    # Without optimization
    start = time.perf_counter()
    chart = LineChart()
    widget = QWidget()
    widget.resize(QSize(800, 600))
    try:
        chart.update_chart(large_data[['heart_rate']], "No Optimization", widget)
        no_opt_time = (time.perf_counter() - start) * 1000
        print(f"Without optimization (50k points): {no_opt_time:.1f}ms")
    except Exception as e:
        print(f"Without optimization: FAILED - {e}")
        no_opt_time = None
    
    # With optimization
    start = time.perf_counter()
    optimized_data = optimizer.optimize_data(large_data, target_points=5000, algorithm='lttb')
    chart2 = LineChart()
    widget2 = QWidget()
    widget2.resize(QSize(800, 600))
    try:
        chart2.update_chart(optimized_data[['heart_rate']], "Optimized", widget2)
        opt_time = (time.perf_counter() - start) * 1000
        print(f"With LTTB optimization (5k points): {opt_time:.1f}ms")
        
        if no_opt_time:
            speedup = no_opt_time / opt_time
            print(f"Speedup: {speedup:.1f}x")
    except Exception as e:
        print(f"With optimization: FAILED - {e}")
    
    # Test adaptive renderer
    print("\n\nTesting Adaptive Renderer:")
    print("-" * 50)
    
    adaptive = AdaptiveChartRenderer()
    for size in [1000, 10000, 100000]:
        data = generate_test_data(size)
        widget = QWidget()
        widget.resize(QSize(800, 600))
        
        start = time.perf_counter()
        try:
            adaptive.render(data, 'line', widget)
            render_time = (time.perf_counter() - start) * 1000
            print(f"{size} points: {render_time:.1f}ms using {adaptive.current_renderer.value if adaptive.current_renderer else 'None'}")
        except Exception as e:
            print(f"{size} points: FAILED - {e}")
    
    # Save baseline metrics
    baseline_path = Path("tests/performance/baseline_metrics.json")
    baseline_path.parent.mkdir(exist_ok=True)
    
    baseline = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': results,
        'system_info': {
            'python_version': sys.version,
            'qt_version': 'PyQt6'
        }
    }
    
    with open(baseline_path, 'w') as f:
        json.dump(baseline, f, indent=2)
    
    print(f"\n\nBaseline metrics saved to: {baseline_path}")
    
    # Summary
    print("\n\nPerformance Summary:")
    print("=" * 50)
    print("Data Points | LineChart | Enhanced | Optimized")
    print("-" * 50)
    
    for size in data_sizes:
        line_results = [r for r in results if r['data_points'] == size and r['chart_type'] == 'LineChart']
        enhanced_results = [r for r in results if r['data_points'] == size and r['chart_type'] == 'EnhancedLineChart']
        optimized_results = [r for r in results if r['data_points'] == size and r['chart_type'] == 'OptimizedLineChart']
        
        line_time = line_results[0]['render_time'] if line_results and line_results[0]['success'] else 'N/A'
        enhanced_time = enhanced_results[0]['render_time'] if enhanced_results and enhanced_results[0]['success'] else 'N/A'
        optimized_time = optimized_results[0]['render_time'] if optimized_results and optimized_results[0]['success'] else 'N/A'
        
        if isinstance(line_time, float):
            line_str = f"{line_time:.1f}ms"
        else:
            line_str = line_time
            
        if isinstance(enhanced_time, float):
            enhanced_str = f"{enhanced_time:.1f}ms"
        else:
            enhanced_str = enhanced_time
            
        if isinstance(optimized_time, float):
            optimized_str = f"{optimized_time:.1f}ms"
        else:
            optimized_str = optimized_time
        
        print(f"{size:10} | {line_str:9} | {enhanced_str:8} | {optimized_str}")


if __name__ == "__main__":
    run_benchmarks()
    app.quit()