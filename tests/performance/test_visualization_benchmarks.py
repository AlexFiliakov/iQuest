"""
Performance benchmarks for visualization components.

This module provides comprehensive performance testing for all chart types
and rendering strategies to ensure optimal performance across different 
data sizes and use cases.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json
from pathlib import Path

from tests.performance.benchmark_base import PerformanceBenchmark
from tests.fixtures.health_fixtures import HealthDataFixtures
from src.ui.charts import LineChart, EnhancedLineChart
from src.ui.charts.waterfall_chart import WaterfallChartWidget as WaterfallChart
from src.ui.charts.calendar_heatmap import CalendarHeatmapComponent as CalendarHeatmap
from src.ui.charts.chart_performance_optimizer import ChartPerformanceOptimizer
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QSize

# Ensure Qt Application exists
if not QApplication.instance():
    app = QApplication([])


class VisualizationBenchmark(PerformanceBenchmark):
    """Extended benchmark class for visualization-specific metrics."""
    
    def setup_method(self):
        super().setup_method()
        self.frame_times = []
        self.render_calls = 0
        
    def measure_fps(self, duration: float = 1.0) -> float:
        """Measure frames per second over given duration."""
        if not self.frame_times or duration == 0:
            return 0.0
        
        frames_in_duration = len([t for t in self.frame_times if t < duration])
        return frames_in_duration / duration
    
    def record_frame(self, frame_time: float):
        """Record a single frame render time."""
        self.frame_times.append(frame_time)
        self.render_calls += 1


class TestVisualizationPerformance:
    """Comprehensive performance tests for visualization components."""
    
    @pytest.fixture
    def viz_benchmark(self):
        """Provide visualization benchmark instance."""
        bench = VisualizationBenchmark()
        bench.setup_method()
        return bench
    
    @pytest.fixture
    def test_widget(self):
        """Provide a test widget for rendering."""
        widget = QWidget()
        widget.resize(QSize(800, 600))
        return widget
    
    @pytest.fixture
    def data_generator(self):
        """Provide health data generator."""
        return HealthDataFixtures()
    
    def generate_time_series_data(self, points: int) -> pd.DataFrame:
        """Generate time series data with specified number of points."""
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
    
    @pytest.mark.parametrize("data_size", [100, 1000, 10000, 50000, 100000])
    def test_line_chart_performance(self, benchmark, viz_benchmark, test_widget, data_size):
        """Test line chart rendering performance across data sizes."""
        data = self.generate_time_series_data(data_size)
        
        with viz_benchmark.measure_performance(f"line_chart_{data_size}_points"):
            chart = LineChart()
            chart.update_chart(data[['heart_rate']], "Heart Rate", test_widget)
        
        # Assert performance requirements
        if data_size <= 10000:
            viz_benchmark.assert_performance(
                f"line_chart_{data_size}_points",
                max_duration=0.2,  # 200ms
                max_memory_mb=100
            )
        elif data_size <= 100000:
            viz_benchmark.assert_performance(
                f"line_chart_{data_size}_points",
                max_duration=0.5,  # 500ms
                max_memory_mb=200
            )
    
    @pytest.mark.parametrize("renderer", ["matplotlib", "pyqtgraph", "canvas"])
    def test_renderer_comparison(self, benchmark, viz_benchmark, test_widget, renderer):
        """Compare performance across different rendering backends."""
        data = self.generate_time_series_data(10000)
        
        with viz_benchmark.measure_performance(f"renderer_{renderer}_10k"):
            if renderer == "matplotlib":
                from src.ui.charts.matplotlib_chart_factory import MatplotlibChartFactory
                factory = MatplotlibChartFactory()
                chart = factory.create_line_chart()
            elif renderer == "pyqtgraph":
                from src.ui.charts.pyqtgraph_chart_factory import PyQtGraphChartFactory
                factory = PyQtGraphChartFactory()
                chart = factory.create_line_chart()
            else:  # canvas
                # Canvas renderer would be implemented here
                chart = EnhancedLineChart()
            
            chart.update_chart(data[['heart_rate']], "Heart Rate", test_widget)
    
    def test_data_optimization_impact(self, benchmark, viz_benchmark, test_widget):
        """Test impact of data optimization strategies."""
        original_data = self.generate_time_series_data(50000)
        optimizer = ChartPerformanceOptimizer()
        
        # Test without optimization
        with viz_benchmark.measure_performance("no_optimization_50k"):
            chart = LineChart()
            chart.update_chart(original_data[['heart_rate']], "No Optimization", test_widget)
        
        # Test with optimization
        with viz_benchmark.measure_performance("with_optimization_50k"):
            optimized_data = optimizer.optimize_data(
                original_data,
                target_points=5000,
                algorithm='lttb'
            )
            chart = LineChart()
            chart.update_chart(optimized_data[['heart_rate']], "Optimized", test_widget)
        
        # Compare results
        no_opt = viz_benchmark.get_result("no_optimization_50k")
        with_opt = viz_benchmark.get_result("with_optimization_50k")
        
        # Optimization should provide significant speedup
        assert with_opt['duration'] < no_opt['duration'] * 0.3  # At least 70% faster
        assert with_opt['memory_delta'] < no_opt['memory_delta'] * 0.5  # Less memory
    
    def test_animation_performance(self, benchmark, viz_benchmark, test_widget):
        """Test animation performance for real-time updates."""
        data_stream = self.generate_time_series_data(1000)
        chart = EnhancedLineChart()
        
        # Initial render
        chart.update_chart(data_stream[:100], "Animation Test", test_widget)
        
        # Simulate real-time updates
        frame_times = []
        
        with viz_benchmark.measure_performance("animation_fps"):
            for i in range(100, 200):  # 100 frame updates
                frame_start = time.perf_counter()
                
                # Update with new data point
                new_data = data_stream[:i+1]
                chart.update_chart(new_data, "Animation Test", test_widget)
                
                frame_time = time.perf_counter() - frame_start
                frame_times.append(frame_time)
                viz_benchmark.record_frame(frame_time)
        
        # Calculate FPS
        fps = viz_benchmark.measure_fps()
        avg_frame_time = np.mean(frame_times) * 1000  # Convert to ms
        
        # Assert smooth animation (60 FPS = 16.67ms per frame)
        assert avg_frame_time < 16.67, f"Average frame time {avg_frame_time:.2f}ms exceeds 60 FPS target"
        assert fps >= 60, f"FPS {fps:.1f} below 60 FPS target"
    
    def test_memory_efficiency(self, benchmark, viz_benchmark, test_widget):
        """Test memory efficiency with large datasets."""
        # Test memory growth with increasing data
        memory_usage = []
        
        for size in [1000, 10000, 50000, 100000]:
            data = self.generate_time_series_data(size)
            
            with viz_benchmark.measure_performance(f"memory_test_{size}"):
                chart = LineChart()
                chart.update_chart(data[['heart_rate']], f"Memory Test {size}", test_widget)
            
            result = viz_benchmark.get_result(f"memory_test_{size}")
            memory_usage.append((size, result['peak_memory']))
        
        # Check memory scales sub-linearly
        # Memory per point should decrease as dataset grows
        memory_per_point = [(mem / size) for size, mem in memory_usage]
        
        # Assert memory efficiency improves with scale
        for i in range(1, len(memory_per_point)):
            assert memory_per_point[i] <= memory_per_point[i-1], \
                "Memory per point should decrease with larger datasets"
    
    def test_zoom_pan_performance(self, benchmark, viz_benchmark, test_widget):
        """Test performance of zoom and pan operations."""
        data = self.generate_time_series_data(100000)
        chart = EnhancedLineChart()
        
        # Initial render
        chart.update_chart(data, "Zoom/Pan Test", test_widget)
        
        # Test zoom operations
        zoom_levels = [1.0, 2.0, 5.0, 10.0, 0.5, 0.1]
        
        for zoom in zoom_levels:
            with viz_benchmark.measure_performance(f"zoom_{zoom}x"):
                chart.zoom(zoom)
                chart.update_chart(data, "Zoom Test", test_widget)
        
        # All zoom operations should be fast
        for zoom in zoom_levels:
            viz_benchmark.assert_performance(
                f"zoom_{zoom}x",
                max_duration=0.05,  # 50ms for zoom
                max_memory_growth_mb=10
            )
    
    def test_chart_type_performance(self, benchmark, viz_benchmark, test_widget):
        """Test performance across different chart types."""
        data = self.generate_time_series_data(5000)
        
        chart_types = [
            ("line", LineChart),
            ("enhanced", EnhancedLineChart),
        ]
        
        for chart_name, chart_class in chart_types:
            with viz_benchmark.measure_performance(f"{chart_name}_chart_5k"):
                chart = chart_class()
                
                # Update chart with data
                chart.update_chart(data[['heart_rate']], f"{chart_name} Test", test_widget)
            
            # All chart types should render within reasonable time
            viz_benchmark.assert_performance(
                f"{chart_name}_chart_5k",
                max_duration=0.3,  # 300ms
                max_memory_mb=150
            )
    
    def test_progressive_rendering(self, benchmark, viz_benchmark, test_widget):
        """Test progressive rendering performance."""
        large_data = self.generate_time_series_data(100000)
        
        # Create chart with progressive rendering
        chart = EnhancedLineChart()
        chart.enable_progressive_rendering(
            initial_points=1000,
            chunk_size=10000,
            delay_ms=50
        )
        
        # Measure time to first paint
        with viz_benchmark.measure_performance("progressive_first_paint"):
            chart.initial_render(large_data, "Progressive Test", test_widget)
        
        # First paint should be very fast
        viz_benchmark.assert_performance(
            "progressive_first_paint",
            max_duration=0.05  # 50ms
        )
        
        # Measure full render time
        with viz_benchmark.measure_performance("progressive_full_render"):
            chart.complete_render()
        
        # Full render can take longer but should still be reasonable
        viz_benchmark.assert_performance(
            "progressive_full_render",
            max_duration=1.0  # 1 second
        )
    
    def test_concurrent_charts(self, benchmark, viz_benchmark, test_widget):
        """Test performance with multiple charts rendering concurrently."""
        data_sets = [self.generate_time_series_data(10000) for _ in range(4)]
        
        with viz_benchmark.measure_performance("concurrent_4_charts"):
            charts = []
            for i, data in enumerate(data_sets):
                chart = LineChart()
                chart.update_chart(data[['heart_rate']], f"Chart {i+1}", test_widget)
                charts.append(chart)
        
        # Concurrent rendering should still be performant
        viz_benchmark.assert_performance(
            "concurrent_4_charts",
            max_duration=1.0,  # 1 second for 4 charts
            max_memory_mb=400  # 100MB per chart
        )
    
    @pytest.mark.integration
    def test_real_world_scenario(self, benchmark, viz_benchmark, test_widget, data_generator):
        """Test performance with real-world usage patterns."""
        # Generate a year of health data
        health_data = data_generator.create_health_dataframe(
            start_date=datetime.now() - timedelta(days=365),
            days=365,
            metrics=['heart_rate', 'steps', 'calories', 'distance']
        )
        
        # Simulate typical user interaction
        with viz_benchmark.measure_performance("real_world_year_data"):
            # Create dashboard with multiple charts
            charts = {
                'heart_rate': EnhancedLineChart(),
                'steps': LineChart(),
                'calories': WaterfallChart(),
                'monthly': CalendarHeatmap()
            }
            
            # Render each chart
            for metric, chart in charts.items():
                if metric == 'monthly':
                    monthly_data = health_data.resample('M').sum()
                    chart.update_chart(monthly_data, "Monthly Summary", test_widget)
                else:
                    chart.update_chart(health_data[[metric]], metric.title(), test_widget)
        
        # Real-world scenario should complete reasonably fast
        viz_benchmark.assert_performance(
            "real_world_year_data",
            max_duration=2.0,  # 2 seconds for full dashboard
            max_memory_mb=500
        )
    
    def test_performance_regression(self, viz_benchmark):
        """Test for performance regression against baseline."""
        baseline_path = Path("tests/performance/baseline_metrics.json")
        baseline = PerformanceBenchmark.load_baseline(baseline_path)
        
        # Run standard benchmark
        data = self.generate_time_series_data(10000)
        test_widget = QWidget()
        
        with viz_benchmark.measure_performance("standard_benchmark"):
            chart = LineChart()
            chart.update_chart(data[['heart_rate']], "Regression Test", test_widget)
        
        # Compare to baseline
        if baseline:
            regression_detected = not viz_benchmark.compare_to_baseline(
                "standard_benchmark",
                baseline.get("standard_benchmark", {}),
                tolerance=1.2  # Allow 20% degradation
            )
            
            if regression_detected:
                current = viz_benchmark.get_result("standard_benchmark")
                base = baseline.get("standard_benchmark", {})
                pytest.fail(
                    f"Performance regression detected:\n"
                    f"Current: {current['duration']:.3f}s, "
                    f"Baseline: {base.get('duration', 0):.3f}s"
                )
    
    @pytest.mark.benchmark
    def test_save_benchmark_results(self, viz_benchmark, tmp_path):
        """Save benchmark results for future comparison."""
        # Run a few benchmarks
        for size in [1000, 10000]:
            data = self.generate_time_series_data(size)
            test_widget = QWidget()
            
            with viz_benchmark.measure_performance(f"benchmark_{size}"):
                chart = LineChart()
                chart.update_chart(data[['heart_rate']], f"Test {size}", test_widget)
        
        # Save results
        results_path = tmp_path / "benchmark_results.json"
        viz_benchmark.save_results(results_path)
        
        # Verify saved
        assert results_path.exists()
        
        # Print summary
        print("\n" + viz_benchmark.summary())


if __name__ == "__main__":
    # Run benchmarks and save baseline
    pytest.main([__file__, "-v", "-m", "benchmark"])