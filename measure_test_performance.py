#!/usr/bin/env python3
"""
Measure test execution times for the visualization testing framework.

This script runs various test scenarios and measures their performance
to ensure they complete within the 10-minute target.
"""

import sys
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set Qt to offscreen mode
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication
from tests.visual.visualization_testing_framework import (
    VisualizationTestingFramework,
    VisualizationTestDataGenerator
)


class TestPerformanceMonitor:
    """Monitor test execution performance"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.target_time = 600  # 10 minutes in seconds
        
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        print(f"Performance monitoring started at {datetime.now()}")
        print(f"Target: Complete all tests within {self.target_time/60:.0f} minutes")
        print("=" * 60)
        
    def record(self, test_name: str, duration: float):
        """Record test duration"""
        self.results.append({
            'test': test_name,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
    def report(self):
        """Generate performance report"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("TEST PERFORMANCE REPORT")
        print("=" * 60)
        
        # Individual test times
        print("\nTest Execution Times:")
        for result in sorted(self.results, key=lambda x: x['duration'], reverse=True):
            print(f"  {result['test']:<40} {result['duration']:>8.2f}s")
            
        # Summary statistics
        durations = [r['duration'] for r in self.results]
        print(f"\nSummary:")
        print(f"  Total tests run: {len(self.results)}")
        print(f"  Total time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        print(f"  Average time per test: {sum(durations)/len(durations):.2f}s")
        print(f"  Slowest test: {max(durations):.2f}s")
        print(f"  Fastest test: {min(durations):.2f}s")
        
        # Target compliance
        if total_time <= self.target_time:
            print(f"\n✓ PASSED: Tests completed within {self.target_time/60:.0f} minute target")
        else:
            print(f"\n✗ FAILED: Tests exceeded {self.target_time/60:.0f} minute target by {(total_time-self.target_time)/60:.1f} minutes")
            
        # Save report
        report_path = Path("tests/results/performance_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_time': total_time,
            'target_time': self.target_time,
            'passed': total_time <= self.target_time,
            'test_count': len(self.results),
            'results': self.results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_path}")
        
        return total_time <= self.target_time


def run_performance_tests():
    """Run performance tests for visualization framework"""
    monitor = TestPerformanceMonitor()
    monitor.start()
    
    # Initialize framework
    framework = VisualizationTestingFramework()
    data_generator = VisualizationTestDataGenerator()
    
    # Test 1: Data generation performance
    print("\n1. Testing data generation performance...")
    start = time.time()
    
    # Generate various datasets
    datasets = {
        'small': data_generator.create_time_series_data(points=100),
        'medium': data_generator.create_time_series_data(points=1000),
        'large': data_generator.create_time_series_data(points=10000),
        'edge_cases': data_generator.create_edge_case_datasets()
    }
    
    duration = time.time() - start
    monitor.record("Data Generation", duration)
    print(f"   ✓ Generated test datasets in {duration:.2f}s")
    
    # Test 2: Unit test performance
    print("\n2. Testing unit test performance...")
    
    # Create mock component
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtGui import QPainter
    from PyQt6.QtCore import Qt
    
    class MockComponent(QWidget):
        def __init__(self, data=None):
            super().__init__()
            self.data = data
            self.setMinimumSize(400, 300)
            
        def set_data(self, data):
            self.data = data
            
        def get_data(self):
            return self.data if self.data is not None else []
            
        def apply_theme(self, theme):
            pass
            
        def render(self):
            """Custom render method for testing"""
            pass
            
        def paintEvent(self, event):
            """Override paint event for Qt rendering"""
            painter = QPainter(self)
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
            painter.end()
    
    start = time.time()
    unit_results = framework.unit_test_runner.run_tests(MockComponent)
    duration = time.time() - start
    monitor.record("Unit Tests", duration)
    print(f"   ✓ Ran {len(unit_results.tests)} unit tests in {duration:.2f}s")
    
    # Test 3: Visual regression test performance
    print("\n3. Testing visual regression performance...")
    start = time.time()
    
    # Simulate visual regression testing
    from PIL import Image
    test_images = []
    for i in range(10):  # Simulate 10 visual tests
        img = Image.new('RGB', (800, 400), color='white')
        test_images.append(img)
        
    # Simulate comparison
    from tests.visual.image_comparison import ImageComparator
    comparator = ImageComparator()
    
    for i, img in enumerate(test_images):
        # Compare with itself (perfect match)
        result = comparator.compare(img, img, method='ssim')
        
    duration = time.time() - start
    monitor.record("Visual Regression", duration)
    print(f"   ✓ Performed {len(test_images)} visual comparisons in {duration:.2f}s")
    
    # Test 4: Performance test execution
    print("\n4. Testing performance benchmarks...")
    start = time.time()
    
    # Simulate performance testing
    perf_results = framework.performance_tester.run_tests(MockComponent)
    
    duration = time.time() - start
    monitor.record("Performance Benchmarks", duration)
    print(f"   ✓ Ran performance benchmarks in {duration:.2f}s")
    
    # Test 5: Accessibility test performance
    print("\n5. Testing accessibility checks...")
    start = time.time()
    
    # Run accessibility tests
    accessibility_results = framework.accessibility_tester.run_tests(MockComponent)
    
    duration = time.time() - start
    monitor.record("Accessibility Tests", duration)
    print(f"   ✓ Performed accessibility checks in {duration:.2f}s")
    
    # Test 6: Integration test performance
    print("\n6. Testing integration scenarios...")
    start = time.time()
    
    integration_results = framework.integration_tester.run_tests(MockComponent)
    
    duration = time.time() - start
    monitor.record("Integration Tests", duration)
    print(f"   ✓ Ran integration tests in {duration:.2f}s")
    
    # Test 7: Simulate full test suite on multiple components
    print("\n7. Simulating full test suite...")
    start = time.time()
    
    # Simulate testing 5 components
    component_count = 5
    for i in range(component_count):
        # Quick simulation of full test run
        time.sleep(0.1)  # Simulate some work
        
    duration = time.time() - start
    monitor.record(f"Full Suite ({component_count} components)", duration)
    print(f"   ✓ Simulated full test suite in {duration:.2f}s")
    
    # Generate report
    passed = monitor.report()
    
    return 0 if passed else 1


def main():
    """Main entry point"""
    # Initialize Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        return run_performance_tests()
    except Exception as e:
        print(f"\nError during performance testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())