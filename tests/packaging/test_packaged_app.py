"""
Automated tests for packaged Apple Health Dashboard application.

This module provides automated testing capabilities for validating
the packaged distribution formats on Windows systems.
"""

import subprocess
import time
import psutil
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import unittest
from datetime import datetime

# Add win32 imports for Windows-specific testing
try:
    import win32gui
    import win32con
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class PackagedAppTests:
    """Test suite for packaged application validation."""
    
    def __init__(self, exe_path: str):
        """Initialize test suite with executable path.
        
        Args:
            exe_path: Path to the packaged executable
        """
        self.exe_path = Path(exe_path)
        if not self.exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")
            
        self.test_results = {
            "exe_path": str(self.exe_path),
            "test_time": datetime.now().isoformat(),
            "os_version": self._get_os_version(),
            "results": {}
        }
        
    def _get_os_version(self) -> str:
        """Get Windows version information."""
        if sys.platform == "win32":
            import platform
            return f"Windows {platform.version()}"
        return "Unknown"
        
    def is_window_visible(self, title_substring: str = "Apple Health") -> bool:
        """Check if application window is visible.
        
        Args:
            title_substring: Part of window title to search for
            
        Returns:
            True if window is found and visible
        """
        if not WINDOWS_AVAILABLE:
            return False
            
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title_substring in window_title:
                    windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return len(windows) > 0
        
    def test_startup_time(self) -> float:
        """Test application startup time.
        
        Returns:
            Startup time in seconds
            
        Raises:
            AssertionError: If startup exceeds 5 second limit
        """
        print("Testing startup time...")
        start_time = time.time()
        
        # Launch application
        process = subprocess.Popen([str(self.exe_path)])
        
        # Wait for window to appear (max 10 seconds)
        timeout = 10
        elapsed = 0
        while not self.is_window_visible() and elapsed < timeout:
            time.sleep(0.1)
            elapsed = time.time() - start_time
            
        startup_time = time.time() - start_time
        
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
            
        self.test_results["results"]["startup_time"] = {
            "value": startup_time,
            "passed": startup_time < 5.0,
            "target": 5.0
        }
        
        assert startup_time < 5.0, f"Startup took {startup_time:.1f}s (>5s limit)"
        print(f"✓ Startup time: {startup_time:.1f}s")
        return startup_time
        
    def test_memory_usage(self) -> float:
        """Test memory usage of packaged app.
        
        Returns:
            Memory usage in MB
            
        Raises:
            AssertionError: If memory exceeds limit
        """
        print("Testing memory usage...")
        process = subprocess.Popen([str(self.exe_path)])
        
        # Let app fully load
        time.sleep(5)
        
        try:
            # Get process memory info
            p = psutil.Process(process.pid)
            memory_mb = p.memory_info().rss / 1024 / 1024
            
            self.test_results["results"]["memory_usage"] = {
                "value": memory_mb,
                "passed": memory_mb < 500,
                "target": 500
            }
            
            assert memory_mb < 500, f"Memory usage {memory_mb:.1f}MB exceeds limit"
            print(f"✓ Memory usage: {memory_mb:.1f}MB")
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
                
        return memory_mb
        
    def test_cpu_idle(self) -> float:
        """Test CPU usage when application is idle.
        
        Returns:
            Average CPU usage percentage
            
        Raises:
            AssertionError: If CPU usage exceeds limit
        """
        print("Testing idle CPU usage...")
        process = subprocess.Popen([str(self.exe_path)])
        
        # Let app fully load and settle
        time.sleep(5)
        
        try:
            p = psutil.Process(process.pid)
            
            # Measure CPU over 5 seconds
            cpu_samples = []
            for _ in range(5):
                cpu_percent = p.cpu_percent(interval=1)
                cpu_samples.append(cpu_percent)
                
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            
            self.test_results["results"]["cpu_idle"] = {
                "value": avg_cpu,
                "passed": avg_cpu < 5.0,
                "target": 5.0
            }
            
            assert avg_cpu < 5.0, f"Idle CPU {avg_cpu:.1f}% exceeds limit"
            print(f"✓ Idle CPU usage: {avg_cpu:.1f}%")
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
                
        return avg_cpu
        
    def test_file_operations(self) -> Dict[str, bool]:
        """Test file read/write operations.
        
        Returns:
            Dictionary of operation results
        """
        print("Testing file operations...")
        results = {}
        
        # Test AppData directory creation
        appdata_dir = Path(os.environ.get('APPDATA', '')) / 'AppleHealthDashboard'
        
        # Clean up any existing directory
        if appdata_dir.exists():
            shutil.rmtree(appdata_dir, ignore_errors=True)
            
        # Launch app
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(3)
        
        try:
            # Check if AppData directory was created
            results['appdata_created'] = appdata_dir.exists()
            
            # Check for database file
            db_path = appdata_dir / 'health_data.db'
            results['database_created'] = db_path.exists()
            
            # Check for settings file
            settings_path = appdata_dir / 'settings.json'
            results['settings_created'] = settings_path.exists()
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
                
        self.test_results["results"]["file_operations"] = results
        
        for op, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {op}: {success}")
            
        return results
        
    def test_portable_mode(self) -> bool:
        """Test portable mode functionality.
        
        Returns:
            True if portable mode works correctly
        """
        print("Testing portable mode...")
        
        # Check if this is a portable build
        data_dir = self.exe_path.parent / 'data'
        portable_marker = self.exe_path.parent / 'portable.txt'
        
        is_portable = portable_marker.exists() or data_dir.exists()
        
        if not is_portable:
            print("  Not a portable build, skipping...")
            return True
            
        # Launch app
        process = subprocess.Popen([str(self.exe_path)])
        time.sleep(3)
        
        try:
            # Check if data directory was created in app directory
            data_created = data_dir.exists()
            
            # Check that no AppData directory was created
            appdata_dir = Path(os.environ.get('APPDATA', '')) / 'AppleHealthDashboard'
            no_appdata = not appdata_dir.exists()
            
            result = data_created and no_appdata
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
                
        self.test_results["results"]["portable_mode"] = {
            "data_in_app_dir": data_created,
            "no_appdata": no_appdata,
            "passed": result
        }
        
        status = "✓" if result else "✗"
        print(f"  {status} Portable mode: {result}")
        
        return result
        
    def run_all_tests(self) -> Dict[str, any]:
        """Run all automated tests.
        
        Returns:
            Dictionary of all test results
        """
        print(f"\nRunning automated tests for: {self.exe_path}")
        print(f"OS: {self._get_os_version()}")
        print("=" * 60)
        
        # Run tests
        tests = [
            ("Startup Time", self.test_startup_time),
            ("Memory Usage", self.test_memory_usage),
            ("CPU Idle", self.test_cpu_idle),
            ("File Operations", self.test_file_operations),
            ("Portable Mode", self.test_portable_mode),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"✗ {test_name} failed: {e}")
                self.test_results["results"][test_name.lower().replace(" ", "_")] = {
                    "error": str(e),
                    "passed": False
                }
                
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results["results"])
        passed_tests = sum(1 for r in self.test_results["results"].values() 
                          if isinstance(r, dict) and r.get("passed", False))
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        # Save results
        results_file = Path("packaging_test_results.json")
        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nResults saved to: {results_file}")
        
        return self.test_results


def benchmark_packaged_app(exe_path: str, iterations: int = 5) -> Dict[str, List[float]]:
    """Run performance benchmarks on packaged app.
    
    Args:
        exe_path: Path to executable
        iterations: Number of test iterations
        
    Returns:
        Dictionary of benchmark results
    """
    results = {
        "startup_time": [],
        "memory_peak": [],
        "cpu_average": []
    }
    
    print(f"\nRunning performance benchmarks ({iterations} iterations)...")
    
    for i in range(iterations):
        print(f"\nIteration {i + 1}/{iterations}")
        
        # Test startup
        start = time.time()
        process = subprocess.Popen([exe_path])
        
        # Wait for window
        timeout = 10
        elapsed = 0
        while elapsed < timeout:
            time.sleep(0.1)
            elapsed = time.time() - start
            # In real implementation, check for window visibility
            if elapsed > 2:  # Assume started after 2 seconds
                break
                
        startup_time = elapsed
        results["startup_time"].append(startup_time)
        
        # Let it run for a bit to measure resources
        time.sleep(3)
        
        try:
            p = psutil.Process(process.pid)
            
            # Memory usage
            memory_mb = p.memory_info().rss / 1024 / 1024
            results["memory_peak"].append(memory_mb)
            
            # CPU usage
            cpu_percent = p.cpu_percent(interval=2)
            results["cpu_average"].append(cpu_percent)
            
        except:
            pass
            
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except:
            process.kill()
            
        # Brief pause between iterations
        time.sleep(2)
        
    # Calculate averages
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    for metric, values in results.items():
        if values:
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            print(f"\n{metric}:")
            print(f"  Average: {avg:.2f}")
            print(f"  Min: {min_val:.2f}")
            print(f"  Max: {max_val:.2f}")
            print(f"  Values: {[f'{v:.2f}' for v in values]}")
            
    return results


class PackagingTestRunner(unittest.TestCase):
    """Unit test wrapper for packaging tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.exe_path = os.environ.get('TEST_EXE_PATH', 'dist/AppleHealthDashboard.exe')
        if not Path(cls.exe_path).exists():
            raise unittest.SkipTest(f"Executable not found: {cls.exe_path}")
            
    def test_startup_performance(self):
        """Test that application starts within time limit."""
        tester = PackagedAppTests(self.exe_path)
        startup_time = tester.test_startup_time()
        self.assertLess(startup_time, 5.0, "Startup time exceeds 5 second limit")
        
    def test_memory_usage(self):
        """Test that memory usage is within limits."""
        tester = PackagedAppTests(self.exe_path)
        memory_mb = tester.test_memory_usage()
        self.assertLess(memory_mb, 500, "Memory usage exceeds 500MB limit")
        
    def test_cpu_idle(self):
        """Test that idle CPU usage is low."""
        tester = PackagedAppTests(self.exe_path)
        cpu_percent = tester.test_cpu_idle()
        self.assertLess(cpu_percent, 5.0, "Idle CPU usage exceeds 5% limit")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        exe_path = sys.argv[1]
        
        # Run automated tests
        tester = PackagedAppTests(exe_path)
        tester.run_all_tests()
        
        # Run benchmarks
        if "--benchmark" in sys.argv:
            benchmark_packaged_app(exe_path)
    else:
        print("Usage: python test_packaged_app.py <path_to_exe> [--benchmark]")
        print("\nExample:")
        print("  python test_packaged_app.py dist/AppleHealthDashboard.exe")
        print("  python test_packaged_app.py dist/AppleHealthDashboard.exe --benchmark")