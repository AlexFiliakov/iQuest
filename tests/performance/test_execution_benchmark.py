"""
Comprehensive test execution performance measurement tool.

This module provides tools to measure and benchmark test execution performance
across all test categories, including collection time, execution time, and
resource usage to validate the 35% performance improvement target.
"""

import time
import psutil
import pytest
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Import will be handled differently since we're creating a standalone tool


@dataclass
class ExecutionMetrics:
    """Comprehensive metrics for test execution."""
    category: str
    test_count: int
    collection_time: float
    execution_time: float
    total_time: float
    memory_peak_mb: float
    memory_delta_mb: float
    cpu_avg_percent: float
    passed: int
    failed: int
    skipped: int
    errors: int
    timestamp: str


class SuitePerformanceBenchmark:
    """Comprehensive test suite performance measurement tool."""
    
    def __init__(self, baseline_file: str = "tests/performance/baseline_metrics.json"):
        """
        Initialize the benchmark tool.
        
        Args:
            baseline_file: Path to store/load baseline performance metrics
        """
        self.baseline_file = Path(baseline_file)
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.results = {}
        self.process = psutil.Process()
        
    def benchmark_test_category(
        self, 
        category: str, 
        test_path: str,
        pytest_args: List[str] = None
    ) -> ExecutionMetrics:
        """
        Benchmark execution of a specific test category.
        
        Args:
            category: Name of the test category (e.g., 'unit', 'integration', 'ui')
            test_path: Path to the test directory/file
            pytest_args: Additional pytest arguments
            
        Returns:
            ExecutionMetrics: Comprehensive metrics for the test execution
        """
        if pytest_args is None:
            pytest_args = []
            
        # Base pytest command
        cmd = [
            sys.executable, "-m", "pytest", test_path,
            "--tb=short",
            "--collect-only", "--quiet"
        ] + pytest_args
        
        # Measure collection time
        start_collection = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        
        # First run: collect tests to count them
        try:
            collection_result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            collection_time = time.perf_counter() - start_collection
            
            # Count tests from collection output
            test_count = len([
                line for line in collection_result.stdout.split('\n') 
                if '::' in line and 'PASSED' not in line
            ])
            
        except subprocess.TimeoutExpired:
            collection_time = 60.0
            test_count = 0
            
        # Second run: execute tests with timing
        exec_cmd = [
            sys.executable, "-m", "pytest", test_path,
            "--tb=short",
            "-v",
            "--durations=0"
        ] + pytest_args
        
        start_execution = time.perf_counter()
        start_cpu = self.process.cpu_percent(interval=0.1)
        peak_memory = start_memory
        
        # Monitor memory during execution
        memory_samples = []
        
        try:
            # Run tests and capture output
            execution_result = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.perf_counter() - start_execution
            
            # Parse test results from output
            output_lines = execution_result.stdout.split('\n')
            passed = failed = skipped = errors = 0
            
            for line in output_lines:
                if 'passed' in line and 'failed' in line:
                    # Parse summary line like "5 passed, 2 failed, 1 skipped"
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if 'passed' in part:
                            passed = int(part.split()[0])
                        elif 'failed' in part:
                            failed = int(part.split()[0])
                        elif 'skipped' in part:
                            skipped = int(part.split()[0])
                        elif 'error' in part:
                            errors = int(part.split()[0])
                            
        except subprocess.TimeoutExpired:
            execution_time = 300.0
            passed = failed = skipped = errors = 0
            
        # Final measurements
        end_memory = self.process.memory_info().rss / 1024 / 1024
        end_cpu = self.process.cpu_percent(interval=0.1)
        
        # Create metrics object
        metrics = ExecutionMetrics(
            category=category,
            test_count=test_count,
            collection_time=collection_time,
            execution_time=execution_time,
            total_time=collection_time + execution_time,
            memory_peak_mb=max(start_memory, end_memory),
            memory_delta_mb=end_memory - start_memory,
            cpu_avg_percent=(start_cpu + end_cpu) / 2,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            timestamp=datetime.now().isoformat()
        )
        
        self.results[category] = metrics
        return metrics
    
    def benchmark_full_suite(self) -> Dict[str, ExecutionMetrics]:
        """
        Benchmark the entire test suite across all categories.
        
        Returns:
            Dict mapping category names to their metrics
        """
        categories = {
            'unit': 'tests/unit',
            'integration': 'tests/integration', 
            'ui': 'tests/ui',
            'performance': 'tests/performance',
            'visual': 'tests/visual'
        }
        
        print("🚀 Starting comprehensive test suite benchmark...")
        
        for category, path in categories.items():
            test_path = Path(path)
            if test_path.exists():
                print(f"📊 Benchmarking {category} tests...")
                metrics = self.benchmark_test_category(category, str(test_path))
                print(f"✅ {category}: {metrics.test_count} tests in {metrics.total_time:.2f}s")
            else:
                print(f"⚠️  Skipping {category} - path not found")
                
        return self.results
    
    def save_baseline(self):
        """Save current results as baseline for future comparisons."""
        baseline_data = {
            category: asdict(metrics) 
            for category, metrics in self.results.items()
        }
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
            
        print(f"💾 Baseline saved to {self.baseline_file}")
    
    def load_baseline(self) -> Dict[str, ExecutionMetrics]:
        """Load baseline metrics from file."""
        if not self.baseline_file.exists():
            return {}
            
        with open(self.baseline_file, 'r') as f:
            baseline_data = json.load(f)
            
        return {
            category: ExecutionMetrics(**data)
            for category, data in baseline_data.items()
        }
    
    def compare_to_baseline(self) -> Dict[str, Dict[str, float]]:
        """
        Compare current results to baseline.
        
        Returns:
            Dict with performance deltas for each category
        """
        baseline = self.load_baseline()
        if not baseline:
            print("⚠️  No baseline found. Run save_baseline() first.")
            return {}
            
        comparisons = {}
        
        for category, current in self.results.items():
            if category not in baseline:
                continue
                
            baseline_metrics = baseline[category]
            
            # Calculate percentage changes
            time_delta = (
                (current.total_time - baseline_metrics.total_time) 
                / baseline_metrics.total_time * 100
            )
            
            memory_delta = (
                (current.memory_peak_mb - baseline_metrics.memory_peak_mb) 
                / baseline_metrics.memory_peak_mb * 100
            ) if baseline_metrics.memory_peak_mb > 0 else 0
            
            comparisons[category] = {
                'time_change_percent': time_delta,
                'memory_change_percent': memory_delta,
                'test_count_change': current.test_count - baseline_metrics.test_count,
                'meets_target': time_delta <= -35.0  # 35% improvement target
            }
            
        return comparisons
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        lines = [
            "# Test Suite Performance Benchmark Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Current Performance Metrics",
            ""
        ]
        
        total_tests = sum(m.test_count for m in self.results.values())
        total_time = sum(m.total_time for m in self.results.values())
        
        lines.append(f"**Total Tests:** {total_tests}")
        lines.append(f"**Total Execution Time:** {total_time:.2f}s")
        lines.append("")
        
        # Category breakdown
        lines.append("### By Category")
        lines.append("")
        lines.append("| Category | Tests | Collection (s) | Execution (s) | Total (s) | Memory (MB) |")
        lines.append("|----------|-------|----------------|---------------|-----------|-------------|")
        
        for category, metrics in self.results.items():
            lines.append(
                f"| {category.title()} | {metrics.test_count} | "
                f"{metrics.collection_time:.2f} | {metrics.execution_time:.2f} | "
                f"{metrics.total_time:.2f} | {metrics.memory_peak_mb:.1f} |"
            )
        
        # Baseline comparison if available
        comparisons = self.compare_to_baseline()
        if comparisons:
            lines.extend([
                "",
                "## Performance vs Baseline",
                "",
                "| Category | Time Change | Memory Change | Target Met |",
                "|----------|-------------|---------------|------------|"
            ])
            
            for category, comp in comparisons.items():
                time_change = comp['time_change_percent']
                memory_change = comp['memory_change_percent']
                target_met = "✅" if comp['meets_target'] else "❌"
                
                lines.append(
                    f"| {category.title()} | {time_change:+.1f}% | "
                    f"{memory_change:+.1f}% | {target_met} |"
                )
        
        return "\n".join(lines)


# Pytest plugin for automatic benchmarking
def pytest_configure(config):
    """Configure pytest with performance tracking."""
    config.addinivalue_line(
        "markers", "benchmark: mark test for performance benchmarking"
    )


def pytest_collection_modifyitems(config, items):
    """Add benchmark marker to performance tests."""
    for item in items:
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.benchmark)


# CLI interface for the benchmark tool
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Suite Performance Benchmark")
    parser.add_argument("--category", help="Specific category to benchmark")
    parser.add_argument("--save-baseline", action="store_true", help="Save results as baseline")
    parser.add_argument("--compare", action="store_true", help="Compare to baseline")
    parser.add_argument("--report", help="Generate report to file")
    
    args = parser.parse_args()
    
    benchmark = TestSuitePerformanceBenchmark()
    
    if args.category:
        metrics = benchmark.benchmark_test_category(args.category, f"tests/{args.category}")
        print(f"Category: {metrics.category}")
        print(f"Tests: {metrics.test_count}")
        print(f"Total time: {metrics.total_time:.2f}s")
    else:
        benchmark.benchmark_full_suite()
    
    if args.save_baseline:
        benchmark.save_baseline()
    
    if args.compare:
        comparisons = benchmark.compare_to_baseline()
        for category, comp in comparisons.items():
            print(f"{category}: {comp['time_change_percent']:+.1f}% time change")
    
    if args.report:
        report = benchmark.generate_performance_report()
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.report}")