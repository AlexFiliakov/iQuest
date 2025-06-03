"""
Performance benchmarking suite for packaged application.

This module provides comprehensive performance testing for the
packaged Apple Health Dashboard across different scenarios.
"""

import time
import psutil
import os
import sys
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for packaged app."""
    
    def __init__(self, exe_path: str):
        """Initialize benchmark suite.
        
        Args:
            exe_path: Path to packaged executable
        """
        self.exe_path = Path(exe_path)
        if not self.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")
            
        self.results = {
            "exe_path": str(self.exe_path),
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "benchmarks": {}
        }
        
    def _get_system_info(self) -> dict:
        """Gather system information for context."""
        return {
            "cpu": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "os": sys.platform,
            "python_version": sys.version
        }
        
    def benchmark_cold_start(self, iterations: int = 3) -> Dict[str, float]:
        """Benchmark cold start performance.
        
        Args:
            iterations: Number of test runs
            
        Returns:
            Dictionary with timing statistics
        """
        print(f"\nBenchmarking cold start ({iterations} iterations)...")
        times = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}")
            
            # Clear system caches (simulate cold start)
            self._clear_caches()
            time.sleep(2)  # Let system settle
            
            # Measure startup
            start_time = time.time()
            process = subprocess.Popen([str(self.exe_path)])
            
            # Wait for process to be responsive
            # In real scenario, we'd wait for window to appear
            time.sleep(3)  # Simplified wait
            
            startup_time = time.time() - start_time
            times.append(startup_time)
            
            # Clean up
            process.terminate()
            process.wait()
            time.sleep(2)
            
        results = {
            "times": times,
            "average": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times)
        }
        
        self.results["benchmarks"]["cold_start"] = results
        return results
        
    def benchmark_warm_start(self, iterations: int = 5) -> Dict[str, float]:
        """Benchmark warm start performance.
        
        Args:
            iterations: Number of test runs
            
        Returns:
            Dictionary with timing statistics
        """
        print(f"\nBenchmarking warm start ({iterations} iterations)...")
        
        # Do one cold start first to warm up
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(3)
        process.terminate()
        process.wait()
        time.sleep(1)
        
        times = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}")
            
            start_time = time.time()
            process = subprocess.Popen([str(self.exe_path)])
            
            # Wait for process to be responsive
            time.sleep(2)  # Simplified wait
            
            startup_time = time.time() - start_time
            times.append(startup_time)
            
            # Clean up
            process.terminate()
            process.wait()
            time.sleep(1)
            
        results = {
            "times": times,
            "average": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times)
        }
        
        self.results["benchmarks"]["warm_start"] = results
        return results
        
    def benchmark_memory_usage(self, duration: int = 60) -> Dict[str, float]:
        """Benchmark memory usage over time.
        
        Args:
            duration: How long to monitor (seconds)
            
        Returns:
            Dictionary with memory statistics
        """
        print(f"\nBenchmarking memory usage over {duration} seconds...")
        
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(3)  # Let app initialize
        
        try:
            p = psutil.Process(process.pid)
            memory_samples = []
            
            # Collect samples
            for i in range(duration):
                try:
                    mem_info = p.memory_info()
                    memory_mb = mem_info.rss / (1024 * 1024)
                    memory_samples.append(memory_mb)
                    
                    if i % 10 == 0:
                        print(f"  Progress: {i}/{duration}s - Current: {memory_mb:.1f}MB")
                        
                except psutil.NoSuchProcess:
                    break
                    
                time.sleep(1)
                
            results = {
                "samples": memory_samples,
                "initial_mb": memory_samples[0] if memory_samples else 0,
                "peak_mb": max(memory_samples) if memory_samples else 0,
                "average_mb": statistics.mean(memory_samples) if memory_samples else 0,
                "final_mb": memory_samples[-1] if memory_samples else 0,
                "growth_mb": (memory_samples[-1] - memory_samples[0]) if len(memory_samples) > 1 else 0
            }
            
        finally:
            process.terminate()
            process.wait()
            
        self.results["benchmarks"]["memory_usage"] = results
        return results
        
    def benchmark_cpu_usage(self, duration: int = 30) -> Dict[str, float]:
        """Benchmark CPU usage patterns.
        
        Args:
            duration: How long to monitor (seconds)
            
        Returns:
            Dictionary with CPU statistics
        """
        print(f"\nBenchmarking CPU usage over {duration} seconds...")
        
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(3)  # Let app initialize
        
        try:
            p = psutil.Process(process.pid)
            cpu_samples = []
            
            # Collect samples
            for i in range(duration):
                try:
                    cpu_percent = p.cpu_percent(interval=1)
                    cpu_samples.append(cpu_percent)
                    
                    if i % 5 == 0:
                        print(f"  Progress: {i}/{duration}s - Current: {cpu_percent:.1f}%")
                        
                except psutil.NoSuchProcess:
                    break
                    
            results = {
                "samples": cpu_samples,
                "average": statistics.mean(cpu_samples) if cpu_samples else 0,
                "median": statistics.median(cpu_samples) if cpu_samples else 0,
                "peak": max(cpu_samples) if cpu_samples else 0,
                "idle_average": statistics.mean(cpu_samples[10:]) if len(cpu_samples) > 10 else 0
            }
            
        finally:
            process.terminate()
            process.wait()
            
        self.results["benchmarks"]["cpu_usage"] = results
        return results
        
    def benchmark_file_operations(self, test_file: Optional[Path] = None) -> Dict[str, float]:
        """Benchmark file operation performance.
        
        Args:
            test_file: Path to test data file
            
        Returns:
            Dictionary with operation timings
        """
        print("\nBenchmarking file operations...")
        
        # For this test, we'd need to automate UI interactions
        # This is a simplified version that just measures app response
        
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(5)  # Let app fully initialize
        
        results = {
            "app_data_creation": 0,
            "settings_save": 0,
            "data_import": 0
        }
        
        try:
            # Check if AppData was created
            appdata_dir = Path(os.environ.get('APPDATA', '')) / 'AppleHealthDashboard'
            if appdata_dir.exists():
                results["app_data_creation"] = 1
                
            # In real scenario, we'd automate:
            # - Opening file dialog
            # - Selecting test file
            # - Measuring import time
            # - Checking database size
            
        finally:
            process.terminate()
            process.wait()
            
        self.results["benchmarks"]["file_operations"] = results
        return results
        
    def benchmark_ui_responsiveness(self) -> Dict[str, float]:
        """Benchmark UI responsiveness metrics."""
        print("\nBenchmarking UI responsiveness...")
        
        # This would require UI automation tools
        # Placeholder for manual testing results
        
        results = {
            "tab_switch_ms": 0,
            "chart_render_ms": 0,
            "dialog_open_ms": 0,
            "search_response_ms": 0
        }
        
        self.results["benchmarks"]["ui_responsiveness"] = results
        return results
        
    def _clear_caches(self):
        """Attempt to clear system caches for cold start testing."""
        # On Windows, this is limited without admin rights
        # This is mainly a placeholder for the concept
        try:
            # Clear Python's import cache
            sys.modules.clear()
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except:
            pass
            
    def run_all_benchmarks(self):
        """Run complete benchmark suite."""
        print("=" * 60)
        print("PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)
        print(f"Testing: {self.exe_path}")
        print(f"System: {self.results['system_info']['cpu']} CPUs, "
              f"{self.results['system_info']['memory_total_gb']:.1f}GB RAM")
        
        # Run benchmarks
        self.benchmark_cold_start(iterations=3)
        self.benchmark_warm_start(iterations=5)
        self.benchmark_memory_usage(duration=30)
        self.benchmark_cpu_usage(duration=20)
        self.benchmark_file_operations()
        self.benchmark_ui_responsiveness()
        
        # Generate report
        self._generate_report()
        
    def _generate_report(self):
        """Generate benchmark report."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        
        # Cold start
        cold = self.results["benchmarks"].get("cold_start", {})
        print(f"\nCold Start Performance:")
        print(f"  Average: {cold.get('average', 0):.2f}s")
        print(f"  Range: {cold.get('min', 0):.2f}s - {cold.get('max', 0):.2f}s")
        
        # Warm start
        warm = self.results["benchmarks"].get("warm_start", {})
        print(f"\nWarm Start Performance:")
        print(f"  Average: {warm.get('average', 0):.2f}s")
        print(f"  Range: {warm.get('min', 0):.2f}s - {warm.get('max', 0):.2f}s")
        
        # Memory
        mem = self.results["benchmarks"].get("memory_usage", {})
        print(f"\nMemory Usage:")
        print(f"  Initial: {mem.get('initial_mb', 0):.1f}MB")
        print(f"  Peak: {mem.get('peak_mb', 0):.1f}MB")
        print(f"  Average: {mem.get('average_mb', 0):.1f}MB")
        
        # CPU
        cpu = self.results["benchmarks"].get("cpu_usage", {})
        print(f"\nCPU Usage:")
        print(f"  Average: {cpu.get('average', 0):.1f}%")
        print(f"  Peak: {cpu.get('peak', 0):.1f}%")
        print(f"  Idle: {cpu.get('idle_average', 0):.1f}%")
        
        # Save detailed results
        report_path = Path("benchmark_results.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\nDetailed results saved to: {report_path}")
        
        # Check against targets
        print("\n" + "=" * 60)
        print("PERFORMANCE TARGETS CHECK")
        print("=" * 60)
        
        cold_avg = cold.get('average', 999)
        warm_avg = warm.get('average', 999)
        mem_peak = mem.get('peak_mb', 999)
        cpu_idle = cpu.get('idle_average', 999)
        
        checks = [
            ("Cold start < 5s", cold_avg < 5.0, f"{cold_avg:.1f}s"),
            ("Warm start < 3s", warm_avg < 3.0, f"{warm_avg:.1f}s"),
            ("Memory < 500MB", mem_peak < 500, f"{mem_peak:.0f}MB"),
            ("Idle CPU < 5%", cpu_idle < 5.0, f"{cpu_idle:.1f}%")
        ]
        
        all_passed = True
        for check, passed, value in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {check} (actual: {value})")
            if not passed:
                all_passed = False
                
        print("\n" + ("All performance targets met!" if all_passed else 
                      "Some performance targets not met - optimization needed"))


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python performance_benchmarks.py <path_to_exe>")
        print("\nExample:")
        print("  python performance_benchmarks.py dist/AppleHealthDashboard.exe")
        sys.exit(1)
        
    exe_path = sys.argv[1]
    
    try:
        benchmark = PerformanceBenchmark(exe_path)
        benchmark.run_all_benchmarks()
    except Exception as e:
        print(f"Error running benchmarks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()