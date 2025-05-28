"""
Memory usage profiler for test execution.

This module provides tools to measure and track memory usage during test execution
to identify memory-intensive tests and potential memory leaks.
"""

import psutil
import gc
import tracemalloc
import pytest
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import json
from pathlib import Path


@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""
    rss_mb: float
    vms_mb: float
    tracemalloc_mb: float
    num_objects: int
    timestamp: float


class MemoryProfiler:
    """Memory usage profiler for test execution."""
    
    def __init__(self):
        """Initialize memory profiler."""
        self.process = psutil.Process()
        self.snapshots = {}
        self.test_memory_usage = {}
        self.tracemalloc_started = False
        
    def start_tracing(self):
        """Start memory tracing."""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True
    
    def stop_tracing(self):
        """Stop memory tracing."""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False
    
    def take_snapshot(self, label: str) -> MemorySnapshot:
        """Take a memory usage snapshot."""
        # Force garbage collection for accurate measurement
        gc.collect()
        
        # Get process memory info
        memory_info = self.process.memory_info()
        rss_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024
        
        # Get tracemalloc info if available
        tracemalloc_mb = 0
        if self.tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_mb = current / 1024 / 1024
        
        # Count objects
        num_objects = len(gc.get_objects())
        
        snapshot = MemorySnapshot(
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            tracemalloc_mb=tracemalloc_mb,
            num_objects=num_objects,
            timestamp=psutil.time.time()
        )
        
        self.snapshots[label] = snapshot
        return snapshot
    
    @contextmanager
    def measure_test_memory(self, test_name: str):
        """Context manager to measure memory usage of a test."""
        self.start_tracing()
        
        # Take before snapshot
        before = self.take_snapshot(f"{test_name}_before")
        
        try:
            yield self
        finally:
            # Take after snapshot
            after = self.take_snapshot(f"{test_name}_after")
            
            # Calculate memory delta
            memory_delta = {
                'rss_delta_mb': after.rss_mb - before.rss_mb,
                'vms_delta_mb': after.vms_mb - before.vms_mb,
                'tracemalloc_delta_mb': after.tracemalloc_mb - before.tracemalloc_mb,
                'objects_delta': after.num_objects - before.num_objects,
                'peak_rss_mb': after.rss_mb,
                'duration': after.timestamp - before.timestamp
            }
            
            self.test_memory_usage[test_name] = memory_delta
    
    def get_memory_heavy_tests(self, threshold_mb: float = 10.0) -> List[Tuple[str, Dict]]:
        """Get tests that use more than threshold MB of memory."""
        heavy_tests = []
        
        for test_name, usage in self.test_memory_usage.items():
            if usage['rss_delta_mb'] > threshold_mb:
                heavy_tests.append((test_name, usage))
        
        # Sort by memory usage descending
        heavy_tests.sort(key=lambda x: x[1]['rss_delta_mb'], reverse=True)
        return heavy_tests
    
    def get_object_leak_candidates(self, threshold_objects: int = 1000) -> List[Tuple[str, Dict]]:
        """Get tests that create many objects without cleaning up."""
        leak_candidates = []
        
        for test_name, usage in self.test_memory_usage.items():
            if usage['objects_delta'] > threshold_objects:
                leak_candidates.append((test_name, usage))
        
        # Sort by object count descending
        leak_candidates.sort(key=lambda x: x[1]['objects_delta'], reverse=True)
        return leak_candidates
    
    def generate_memory_report(self) -> str:
        """Generate a memory usage report."""
        lines = [
            "# Memory Usage Report",
            f"Generated: {psutil.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"Total tests measured: {len(self.test_memory_usage)}",
            ""
        ]
        
        if self.test_memory_usage:
            total_memory = sum(usage['rss_delta_mb'] for usage in self.test_memory_usage.values())
            avg_memory = total_memory / len(self.test_memory_usage)
            max_memory = max(usage['rss_delta_mb'] for usage in self.test_memory_usage.values())
            
            lines.extend([
                f"Total memory used: {total_memory:.1f} MB",
                f"Average per test: {avg_memory:.1f} MB", 
                f"Maximum per test: {max_memory:.1f} MB",
                ""
            ])
        
        # Memory heavy tests
        heavy_tests = self.get_memory_heavy_tests(5.0)  # 5MB threshold
        if heavy_tests:
            lines.extend([
                "## Memory Heavy Tests (>5MB)",
                "",
                "| Test | Memory (MB) | Objects | Duration (s) |",
                "|------|-------------|---------|--------------|"
            ])
            
            for test_name, usage in heavy_tests:
                lines.append(
                    f"| {test_name} | {usage['rss_delta_mb']:.1f} | "
                    f"{usage['objects_delta']} | {usage['duration']:.2f} |"
                )
            lines.append("")
        
        # Potential memory leaks
        leak_candidates = self.get_object_leak_candidates(500)  # 500 objects threshold
        if leak_candidates:
            lines.extend([
                "## Potential Memory Leaks (>500 objects)",
                "",
                "| Test | Objects Created | Memory (MB) | Duration (s) |",
                "|------|-----------------|-------------|--------------|"
            ])
            
            for test_name, usage in leak_candidates:
                lines.append(
                    f"| {test_name} | {usage['objects_delta']} | "
                    f"{usage['rss_delta_mb']:.1f} | {usage['duration']:.2f} |"
                )
        
        return "\n".join(lines)
    
    def save_results(self, filepath: str):
        """Save memory profiling results to JSON."""
        results = {
            'snapshots': {
                label: {
                    'rss_mb': snapshot.rss_mb,
                    'vms_mb': snapshot.vms_mb,
                    'tracemalloc_mb': snapshot.tracemalloc_mb,
                    'num_objects': snapshot.num_objects,
                    'timestamp': snapshot.timestamp
                }
                for label, snapshot in self.snapshots.items()
            },
            'test_memory_usage': self.test_memory_usage
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)


# Pytest plugin integration
@pytest.fixture(scope="function")
def memory_profiler():
    """Pytest fixture for memory profiling."""
    profiler = MemoryProfiler()
    yield profiler
    profiler.stop_tracing()


def pytest_runtest_protocol(item, nextitem):
    """Hook to measure memory for each test."""
    if hasattr(item.config, '_memory_profiler'):
        profiler = item.config._memory_profiler
        test_name = f"{item.parent.name}::{item.name}"
        
        with profiler.measure_test_memory(test_name):
            return pytest_runtest_protocol.original(item, nextitem)
    
    return None


def pytest_configure(config):
    """Configure memory profiling."""
    if config.getoption("--memory-profile", default=False):
        config._memory_profiler = MemoryProfiler()
        
        # Store original function
        import pytest
        pytest_runtest_protocol.original = pytest.hookimpl(pytest_runtest_protocol)


def pytest_addoption(parser):
    """Add memory profiling command line option."""
    parser.addoption(
        "--memory-profile",
        action="store_true",
        default=False,
        help="Enable memory profiling for tests"
    )


def pytest_unconfigure(config):
    """Generate memory report when tests complete."""
    if hasattr(config, '_memory_profiler'):
        profiler = config._memory_profiler
        
        # Generate report
        report = profiler.generate_memory_report()
        print("\n" + report)
        
        # Save detailed results
        profiler.save_results("tests/performance/memory_profile_results.json")
        
        with open("tests/performance/memory_report.md", 'w') as f:
            f.write(report)