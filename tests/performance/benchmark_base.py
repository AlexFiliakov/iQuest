"""
Base benchmark utilities for performance testing.

This module provides infrastructure for measuring performance, memory usage,
and other metrics in a consistent way across all benchmark tests.
"""

import time
import psutil
import pytest
import gc
from memory_profiler import memory_usage
from contextlib import contextmanager
from typing import Callable, Dict, Any, Optional, List
import json
from pathlib import Path


class PerformanceBenchmark:
    """Base class for performance benchmarks with comprehensive measurement capabilities."""
    
    def __init__(self):
        """Initialize benchmark with process monitoring."""
        self.process = psutil.Process()
        self.baseline_memory = None
        self.results = {}
        self._start_metrics = {}
        
    @contextmanager
    def measure_performance(self, name: str, warmup: bool = True):
        """
        Context manager to measure performance metrics.
        
        Args:
            name: Name of the benchmark
            warmup: Whether to perform warmup runs
            
        Yields:
            self: The benchmark instance for access within context
        """
        # Warmup phase
        if warmup:
            gc.collect()
            gc.disable()  # Disable during measurement
        
        # Initial measurements
        cpu_before = self.process.cpu_percent(interval=0.1)
        start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Store start metrics
        self._start_metrics[name] = {
            'time': start_time,
            'memory': start_memory,
            'cpu': cpu_before
        }
        
        try:
            yield self
        finally:
            # Final measurements
            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss / 1024 / 1024
            cpu_after = self.process.cpu_percent(interval=0.1)
            
            # Calculate peak memory during execution
            peak_memory = max(memory_usage(
                (lambda: None,), interval=0.1, timeout=0.1
            )) if end_time - start_time > 0.1 else end_memory
            
            # Store results
            self.results[name] = {
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'peak_memory': peak_memory,
                'cpu_average': (cpu_before + cpu_after) / 2,
                'start_memory': start_memory,
                'end_memory': end_memory
            }
            
            # Re-enable garbage collection
            if warmup:
                gc.enable()
                gc.collect()
    
    def assert_performance(
        self, 
        name: str, 
        max_duration: Optional[float] = None,
        max_memory_mb: Optional[float] = None,
        max_memory_growth_mb: Optional[float] = None
    ):
        """
        Assert performance meets requirements.
        
        Args:
            name: Name of the benchmark
            max_duration: Maximum allowed duration in seconds
            max_memory_mb: Maximum allowed peak memory in MB
            max_memory_growth_mb: Maximum allowed memory growth in MB
        """
        result = self.results.get(name)
        if not result:
            raise ValueError(f"No results found for benchmark '{name}'")
        
        # Check duration
        if max_duration and result['duration'] > max_duration:
            pytest.fail(
                f"Performance: {name} took {result['duration']:.3f}s "
                f"(max allowed: {max_duration}s)"
            )
        
        # Check peak memory
        if max_memory_mb and result['peak_memory'] > max_memory_mb:
            pytest.fail(
                f"Memory: {name} peaked at {result['peak_memory']:.1f}MB "
                f"(max allowed: {max_memory_mb}MB)"
            )
            
        # Check memory growth
        if max_memory_growth_mb and result['memory_delta'] > max_memory_growth_mb:
            pytest.fail(
                f"Memory Growth: {name} grew by {result['memory_delta']:.1f}MB "
                f"(max allowed: {max_memory_growth_mb}MB)"
            )
    
    def get_result(self, name: str) -> Dict[str, float]:
        """Get benchmark results for a specific test."""
        return self.results.get(name, {})
    
    def summary(self) -> str:
        """Generate a summary of all benchmark results."""
        if not self.results:
            return "No benchmark results available"
        
        lines = ["Performance Benchmark Summary", "=" * 40]
        
        for name, result in self.results.items():
            lines.extend([
                f"\n{name}:",
                f"  Duration: {result['duration']:.3f}s",
                f"  Memory Growth: {result['memory_delta']:.1f}MB",
                f"  Peak Memory: {result['peak_memory']:.1f}MB",
                f"  CPU Average: {result['cpu_average']:.1f}%"
            ])
        
        return "\n".join(lines)
    
    def save_results(self, filepath: Path):
        """Save benchmark results to JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    @classmethod
    def load_baseline(cls, filepath: Path) -> Dict[str, Dict[str, float]]:
        """Load baseline results from JSON file."""
        filepath = Path(filepath)
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def compare_to_baseline(
        self, 
        name: str, 
        baseline: Dict[str, float],
        tolerance: float = 1.2
    ) -> bool:
        """
        Compare current results to baseline.
        
        Args:
            name: Name of the benchmark
            baseline: Baseline metrics to compare against
            tolerance: Acceptable performance degradation factor (1.2 = 20% slower)
            
        Returns:
            True if performance is within tolerance
        """
        result = self.results.get(name)
        if not result or not baseline:
            return True  # No comparison possible
        
        # Check each metric
        duration_ok = result['duration'] <= baseline.get('duration', float('inf')) * tolerance
        memory_ok = result['peak_memory'] <= baseline.get('peak_memory', float('inf')) * tolerance
        
        return duration_ok and memory_ok


class BenchmarkFixture:
    """Pytest fixture for benchmark tests."""
    
    def __init__(self):
        self.benchmark = PerformanceBenchmark()
        
    def __call__(self, func: Callable, *args, **kwargs):
        """Run a function and benchmark it."""
        name = func.__name__
        
        with self.benchmark.measure_performance(name):
            result = func(*args, **kwargs)
            
        return result
    
    def pedantic(
        self, 
        func: Callable, 
        args: tuple = (),
        kwargs: dict = None,
        rounds: int = 10,
        warmup_rounds: int = 3,
        iterations: int = 1
    ) -> Dict[str, Any]:
        """
        Run function multiple times with statistics.
        
        Args:
            func: Function to benchmark
            args: Arguments to pass to function
            kwargs: Keyword arguments to pass to function
            rounds: Number of rounds to run
            warmup_rounds: Number of warmup rounds
            iterations: Number of iterations per round
            
        Returns:
            Statistics about the benchmark runs
        """
        if kwargs is None:
            kwargs = {}
            
        times = []
        name = func.__name__
        
        # Warmup rounds
        for _ in range(warmup_rounds):
            func(*args, **kwargs)
            
        # Actual benchmark rounds
        for _ in range(rounds):
            start = time.perf_counter()
            for _ in range(iterations):
                func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) / iterations)
        
        # Calculate statistics
        times_array = np.array(times)
        stats = {
            'mean': float(np.mean(times_array)),
            'stddev': float(np.std(times_array)),
            'min': float(np.min(times_array)),
            'max': float(np.max(times_array)),
            'median': float(np.median(times_array)),
            'rounds': rounds,
            'iterations': iterations
        }
        
        # Store in results
        self.benchmark.results[name] = {
            'duration': stats['mean'],
            'memory_delta': 0,  # Not measured in pedantic mode
            'peak_memory': 0,
            'cpu_average': 0,
            'stats': stats
        }
        
        return stats


# Import numpy for statistics if available
try:
    import numpy as np
except ImportError:
    # Fallback implementation without numpy
    class np:
        @staticmethod
        def mean(arr): return sum(arr) / len(arr)
        @staticmethod
        def std(arr): 
            m = sum(arr) / len(arr)
            return (sum((x - m) ** 2 for x in arr) / len(arr)) ** 0.5
        @staticmethod
        def min(arr): return min(arr)
        @staticmethod
        def max(arr): return max(arr)
        @staticmethod
        def median(arr): 
            s = sorted(arr)
            n = len(s)
            return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2