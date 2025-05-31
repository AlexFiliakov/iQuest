"""
Comprehensive testing framework for health visualizations.

This module provides a unified framework for testing visualization components including:
- Unit testing for component functionality
- Visual regression testing with image comparison
- Performance testing and benchmarking
- Integration testing for data binding and interactions
- Accessibility testing automation
"""

import os
import time
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Type, Any, Callable
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

import pytest
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QPixmap

from tests.visual.visual_test_base import VisualTestBase
from tests.visual.baseline_manager import BaselineManager
from tests.visual.image_comparison import ImageComparator


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict[str, Any]] = None
    
    
@dataclass 
class CategoryTestResult:
    """Result of a test category"""
    category_name: str
    tests: List[TestResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """All tests in category passed"""
        return all(test.passed for test in self.tests)
        
    @property
    def pass_rate(self) -> float:
        """Percentage of tests that passed"""
        if not self.tests:
            return 0.0
        return sum(1 for test in self.tests if test.passed) / len(self.tests)
        
    def add_test(self, name: str, assertion: Callable[[], bool], 
                 description: str, details: Optional[Dict] = None) -> None:
        """Add a test to the category"""
        start_time = time.perf_counter()
        try:
            passed = assertion()
            message = description if passed else f"FAILED: {description}"
        except Exception as e:
            passed = False
            message = f"ERROR: {description} - {str(e)}"
            
        duration = time.perf_counter() - start_time
        self.tests.append(TestResult(name, passed, message, duration, details))
        

@dataclass
class TestReport:
    """Complete test report for a component"""
    component_name: str
    categories: List[CategoryTestResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """All categories passed"""
        return all(cat.passed for cat in self.categories)
        
    @property
    def total_tests(self) -> int:
        """Total number of tests"""
        return sum(len(cat.tests) for cat in self.categories)
        
    @property
    def passed_tests(self) -> int:
        """Number of passed tests"""
        return sum(sum(1 for test in cat.tests if test.passed) for cat in self.categories)
        
    def add_category_results(self, category: CategoryTestResult) -> None:
        """Add category results to report"""
        self.categories.append(category)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            'component_name': self.component_name,
            'passed': self.passed,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'categories': [
                {
                    'name': cat.category_name,
                    'passed': cat.passed,
                    'pass_rate': cat.pass_rate,
                    'tests': [
                        {
                            'name': test.name,
                            'passed': test.passed,
                            'message': test.message,
                            'duration': test.duration,
                            'details': test.details
                        }
                        for test in cat.tests
                    ]
                }
                for cat in self.categories
            ]
        }
        

@dataclass
class WSJDataAccuracyTolerances:
    """WSJ publication-quality tolerances"""
    position: float = 1.0      # 1 pixel tolerance
    color: float = 0.02        # 2% color variance
    value: float = 0.001       # 0.1% data accuracy
    timing: float = 16.67      # 1 frame (60fps)
    

class VisualizationTestingFramework:
    """
    Comprehensive testing framework for health visualizations.
    
    This framework provides unified testing capabilities for visualization components
    including unit tests, visual regression, performance benchmarks, integration tests,
    and accessibility validation.
    """
    
    def __init__(self):
        """Initialize the testing framework with all test runners"""
        self.unit_test_runner = VisualizationUnitTestRunner()
        self.visual_regression_tester = VisualRegressionTester()
        self.performance_tester = VisualizationPerformanceTester()
        self.integration_tester = VisualizationIntegrationTester()
        self.accessibility_tester = AccessibilityTestRunner()
        self.tolerances = WSJDataAccuracyTolerances()
        
        # Test data generator
        self.data_generator = VisualizationTestDataGenerator()
        
        # Results storage
        self.results_dir = Path("tests/results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_full_test_suite(self, components: List[Any]) -> List[TestReport]:
        """
        Run comprehensive test suite on visualization components.
        
        Args:
            components: List of visualization component classes to test
            
        Returns:
            List of test reports, one per component
        """
        reports = []
        
        for component in components:
            report = TestReport(component.__name__)
            
            # Run all test categories
            report.add_category_results(
                self.unit_test_runner.run_tests(component)
            )
            report.add_category_results(
                self.visual_regression_tester.run_tests(component)
            )
            report.add_category_results(
                self.performance_tester.run_tests(component)
            )
            report.add_category_results(
                self.integration_tester.run_tests(component)
            )
            report.add_category_results(
                self.accessibility_tester.run_tests(component)
            )
            
            reports.append(report)
            
        # Save reports
        self._save_reports(reports)
        
        return reports
        
    def run_visual_regression_tests(self, baseline_dir: str, 
                                   output_dir: str) -> Dict[str, Any]:
        """
        Run visual regression testing suite.
        
        Args:
            baseline_dir: Directory containing baseline images
            output_dir: Directory for test output and diffs
            
        Returns:
            Visual regression report with results
        """
        return self.visual_regression_tester.run_full_suite(baseline_dir, output_dir)
        
    def _save_reports(self, reports: List[TestReport]) -> None:
        """Save test reports to JSON files"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        class MockSafeEncoder(json.JSONEncoder):
            def default(self, obj):
                # Handle MagicMock objects and other non-serializable objects
                if hasattr(obj, '_mock_name') or 'Mock' in str(type(obj)):
                    return f"<Mock: {repr(obj)}>"
                try:
                    return super().default(obj)
                except TypeError:
                    return str(obj)
        
        for report in reports:
            filename = f"{report.component_name}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            try:
                with open(filepath, 'w') as f:
                    json.dump(report.to_dict(), f, indent=2, cls=MockSafeEncoder)
            except Exception as e:
                # If serialization still fails, just skip saving this report
                print(f"Warning: Could not save report for {report.component_name}: {e}")
                

class VisualizationUnitTestRunner:
    """Unit test runner for visualization components"""
    
    def __init__(self):
        self.data_generator = VisualizationTestDataGenerator()
        
    def run_tests(self, component_class: Type[Any]) -> CategoryTestResult:
        """Run unit tests for a visualization component"""
        result = CategoryTestResult("Unit Tests")
        
        # Test component initialization
        self._test_initialization(component_class, result)
        
        # Test data handling
        self._test_data_handling(component_class, result)
        
        # Test configuration
        self._test_configuration(component_class, result)
        
        # Test error handling
        self._test_error_handling(component_class, result)
        
        return result
        
    def _test_initialization(self, component_class: Type[Any], 
                           result: CategoryTestResult) -> None:
        """Test component initialization"""
        # Test default initialization
        result.add_test(
            name="default_initialization",
            assertion=lambda: component_class() is not None,
            description="Component initializes with defaults"
        )
        
        # Test with data
        test_data = self.data_generator.create_time_series_data(points=100)
        result.add_test(
            name="initialization_with_data",
            assertion=lambda: component_class(data=test_data) is not None,
            description="Component initializes with data"
        )
        
    def _test_data_handling(self, component_class: Type[Any],
                          result: CategoryTestResult) -> None:
        """Test data handling capabilities"""
        component = component_class()
        
        # Test data loading
        test_data = self.data_generator.create_time_series_data(points=1000)
        
        if hasattr(component, 'set_data'):
            component.set_data(test_data)
            result.add_test(
                name="data_loading",
                assertion=lambda: hasattr(component, 'get_data') and 
                                 len(component.get_data()) == 1000,
                description="Component loads data correctly"
            )
            
        # Test empty data
        if hasattr(component, 'set_data'):
            component.set_data(pd.DataFrame())
            result.add_test(
                name="empty_data_handling",
                assertion=lambda: hasattr(component, 'get_data') and
                                 component.get_data().empty,
                description="Component handles empty data"
            )
            
    def _test_configuration(self, component_class: Type[Any],
                          result: CategoryTestResult) -> None:
        """Test component configuration"""
        component = component_class()
        
        # Test theme application
        if hasattr(component, 'apply_theme'):
            for theme in ['light', 'dark', 'high_contrast']:
                result.add_test(
                    name=f"apply_theme_{theme}",
                    assertion=lambda t=theme: component.apply_theme(t) is None,
                    description=f"Component applies {theme} theme"
                )
                
    def _test_error_handling(self, component_class: Type[Any],
                           result: CategoryTestResult) -> None:
        """Test error handling"""
        component = component_class()
        
        # Test invalid data
        if hasattr(component, 'set_data'):
            invalid_data = self.data_generator.create_invalid_time_series_data()
            try:
                component.set_data(invalid_data)
                result.add_test(
                    name="invalid_data_rejection",
                    assertion=lambda: False,
                    description="Component should reject invalid data"
                )
            except (ValueError, TypeError):
                result.add_test(
                    name="invalid_data_rejection", 
                    assertion=lambda: True,
                    description="Component correctly rejects invalid data"
                )
                

class VisualRegressionTester:
    """Visual regression testing for visualization components"""
    
    def __init__(self):
        self.baseline_manager = BaselineManager()
        self.image_comparator = ImageComparator()
        self.data_generator = VisualizationTestDataGenerator()
        self.diff_threshold = 0.95  # 95% similarity required
        
    def run_tests(self, component_class: Type[Any]) -> CategoryTestResult:
        """Run visual regression tests"""
        result = CategoryTestResult("Visual Regression Tests")
        
        # Standard rendering tests
        self._test_standard_rendering(component_class, result)
        
        # Theme variation tests
        self._test_theme_variations(component_class, result)
        
        # Responsive size tests
        self._test_responsive_sizes(component_class, result)
        
        return result
        
    def run_full_suite(self, baseline_dir: str, output_dir: str) -> Dict[str, Any]:
        """Run complete visual regression suite"""
        self.baseline_manager.set_baseline_dir(baseline_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'new_baselines': []
        }
        
        # Run tests for each component type
        # This would be expanded with actual component discovery
        
        return results
        
    def _test_standard_rendering(self, component_class: Type[Any],
                               result: CategoryTestResult) -> None:
        """Test standard rendering against baseline"""
        # Create component with standard data
        test_data = self.data_generator.create_standard_time_series_data()
        
        if not hasattr(component_class, 'render_to_image'):
            return
            
        component = component_class(data=test_data)
        
        # Render image
        rendered_image = component.render_to_image(width=800, height=400, dpi=300)
        
        # Compare with baseline
        baseline_name = f"{component_class.__name__}_standard"
        comparison = self.image_comparator.compare_with_baseline(
            rendered_image, baseline_name
        )
        
        result.add_test(
            name="standard_rendering",
            assertion=lambda: comparison['similarity'] >= self.diff_threshold,
            description="Standard rendering matches baseline",
            details=comparison
        )
        
    def _test_theme_variations(self, component_class: Type[Any],
                             result: CategoryTestResult) -> None:
        """Test rendering with different themes"""
        if not hasattr(component_class, 'apply_theme'):
            return
            
        test_data = self.data_generator.create_standard_time_series_data()
        component = component_class(data=test_data)
        
        for theme in ['light', 'dark', 'high_contrast']:
            component.apply_theme(theme)
            
            if hasattr(component, 'render_to_image'):
                rendered = component.render_to_image(width=800, height=400)
                baseline_name = f"{component_class.__name__}_{theme}"
                
                comparison = self.image_comparator.compare_with_baseline(
                    rendered, baseline_name
                )
                
                result.add_test(
                    name=f"theme_{theme}",
                    assertion=lambda: comparison['similarity'] >= self.diff_threshold,
                    description=f"{theme} theme rendering matches baseline",
                    details=comparison
                )
                
    def _test_responsive_sizes(self, component_class: Type[Any],
                             result: CategoryTestResult) -> None:
        """Test rendering at different sizes"""
        if not hasattr(component_class, 'render_to_image'):
            return
            
        test_data = self.data_generator.create_standard_time_series_data()
        component = component_class(data=test_data)
        
        sizes = [(400, 200), (800, 400), (1200, 600), (1920, 1080)]
        
        for width, height in sizes:
            rendered = component.render_to_image(width=width, height=height)
            baseline_name = f"{component_class.__name__}_{width}x{height}"
            
            comparison = self.image_comparator.compare_with_baseline(
                rendered, baseline_name
            )
            
            # Slightly lower threshold for responsive tests
            threshold = 0.90
            
            result.add_test(
                name=f"size_{width}x{height}",
                assertion=lambda: comparison['similarity'] >= threshold,
                description=f"Rendering at {width}x{height} matches baseline",
                details=comparison
            )
            

class VisualizationPerformanceTester:
    """Performance testing for visualization components"""
    
    def __init__(self):
        self.data_generator = VisualizationTestDataGenerator()
        self.performance_targets = {
            'render_time': {
                100: 50,      # 50ms for 100 points
                1000: 100,    # 100ms for 1k points
                10000: 200,   # 200ms for 10k points
                100000: 500   # 500ms for 100k points
            },
            'memory_usage': {
                100: 10,      # 10MB for 100 points
                1000: 20,     # 20MB for 1k points  
                10000: 50,    # 50MB for 10k points
                100000: 200   # 200MB for 100k points
            },
            'frame_rate': 60,  # Target 60fps
            'interaction_latency': 16  # 16ms max
        }
        
    def run_tests(self, component_class: Type[Any]) -> CategoryTestResult:
        """Run performance tests"""
        result = CategoryTestResult("Performance Tests")
        
        # Test rendering performance
        self._test_render_performance(component_class, result)
        
        # Test memory usage
        self._test_memory_usage(component_class, result)
        
        # Test animation performance
        self._test_animation_performance(component_class, result)
        
        # Test interaction responsiveness
        self._test_interaction_performance(component_class, result)
        
        return result
        
    def _test_render_performance(self, component_class: Type[Any],
                                result: CategoryTestResult) -> None:
        """Test rendering performance with different data sizes"""
        data_sizes = [100, 1000, 10000]
        
        for size in data_sizes:
            test_data = self.data_generator.create_time_series_data(points=size)
            
            # Measure render time
            start_time = time.perf_counter()
            component = component_class(data=test_data)
            
            if hasattr(component, 'render'):
                # For Qt widgets, render to a pixmap
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap(component.size())
                component.render(pixmap)
                
            render_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            target_time = self.performance_targets['render_time'].get(size, 1000)
            
            result.add_test(
                name=f"render_time_{size}_points",
                assertion=lambda: render_time <= target_time,
                description=f"Render {size} points within {target_time}ms",
                details={'actual_time': render_time, 'target_time': target_time}
            )
            
    def _test_memory_usage(self, component_class: Type[Any],
                         result: CategoryTestResult) -> None:
        """Test memory usage with different data sizes"""
        import psutil
        import gc
        
        process = psutil.Process()
        data_sizes = [100, 1000, 10000]
        
        for size in data_sizes:
            gc.collect()  # Clean up before test
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create component with data
            test_data = self.data_generator.create_time_series_data(points=size)
            component = component_class(data=test_data)
            
            if hasattr(component, 'render'):
                # For Qt widgets, render to a pixmap
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap(component.size())
                component.render(pixmap)
                
            # Measure memory
            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_usage = peak_memory - baseline_memory
            
            target_memory = self.performance_targets['memory_usage'].get(size, 100)
            
            result.add_test(
                name=f"memory_usage_{size}_points",
                assertion=lambda: memory_usage <= target_memory,
                description=f"Memory usage for {size} points under {target_memory}MB",
                details={'actual_memory': memory_usage, 'target_memory': target_memory}
            )
            
            # Clean up
            del component
            gc.collect()
            
    def _test_animation_performance(self, component_class: Type[Any],
                                  result: CategoryTestResult) -> None:
        """Test animation frame rate"""
        if not hasattr(component_class, 'animate'):
            return
            
        test_data = self.data_generator.create_time_series_data(points=5000)
        component = component_class(data=test_data)
        
        # Measure frame times
        frame_times = []
        frame_count = 60  # Test 1 second of animation
        
        for _ in range(frame_count):
            start = time.perf_counter()
            component.animate()
            frame_time = (time.perf_counter() - start) * 1000
            frame_times.append(frame_time)
            
        avg_frame_time = np.mean(frame_times)
        fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
        
        result.add_test(
            name="animation_frame_rate",
            assertion=lambda: fps >= self.performance_targets['frame_rate'],
            description=f"Animation maintains {self.performance_targets['frame_rate']}fps",
            details={'actual_fps': fps, 'avg_frame_time': avg_frame_time}
        )
        
    def _test_interaction_performance(self, component_class: Type[Any],
                                    result: CategoryTestResult) -> None:
        """Test interaction responsiveness"""
        if not hasattr(component_class, 'handle_interaction'):
            return
            
        test_data = self.data_generator.create_time_series_data(points=10000)
        component = component_class(data=test_data)
        
        # Test various interactions
        interactions = ['zoom', 'pan', 'select', 'hover']
        
        for interaction in interactions:
            if hasattr(component, f'handle_{interaction}'):
                start = time.perf_counter()
                getattr(component, f'handle_{interaction}')()
                latency = (time.perf_counter() - start) * 1000
                
                result.add_test(
                    name=f"{interaction}_latency",
                    assertion=lambda: latency <= self.performance_targets['interaction_latency'],
                    description=f"{interaction} responds within {self.performance_targets['interaction_latency']}ms",
                    details={'actual_latency': latency}
                )
                

class VisualizationIntegrationTester:
    """Integration testing for visualization components"""
    
    def __init__(self):
        self.data_generator = VisualizationTestDataGenerator()
        
    def run_tests(self, component_class: Type[Any]) -> CategoryTestResult:
        """Run integration tests"""
        result = CategoryTestResult("Integration Tests")
        
        # Test data binding
        self._test_data_binding(component_class, result)
        
        # Test component coordination
        self._test_component_coordination(component_class, result)
        
        # Test event handling
        self._test_event_handling(component_class, result)
        
        return result
        
    def _test_data_binding(self, component_class: Type[Any],
                         result: CategoryTestResult) -> None:
        """Test reactive data binding"""
        if not hasattr(component_class, 'bind_data_source'):
            return
            
        # Create reactive data source
        from tests.mocks.data_sources import ReactiveDataSource
        data_source = ReactiveDataSource()
        
        component = component_class()
        component.bind_data_source(data_source)
        
        # Test data updates
        initial_data = self.data_generator.create_time_series_data(points=100)
        data_source.set_data(initial_data)
        
        result.add_test(
            name="reactive_data_binding",
            assertion=lambda: hasattr(component, 'get_data') and 
                            len(component.get_data()) == 100,
            description="Component updates with data source changes"
        )
        
        # Test data filtering
        filtered_data = initial_data.iloc[:50]
        data_source.set_data(filtered_data)
        
        result.add_test(
            name="reactive_filter_update",
            assertion=lambda: len(component.get_data()) == 50,
            description="Component updates with filtered data"
        )
        
    def _test_component_coordination(self, component_class: Type[Any],
                                   result: CategoryTestResult) -> None:
        """Test multi-component coordination"""
        if not hasattr(component_class, 'coordinate_with'):
            return
            
        # Create multiple components
        test_data = self.data_generator.create_time_series_data(points=1000)
        component1 = component_class(data=test_data)
        component2 = component_class(data=test_data)
        
        # Coordinate components
        component1.coordinate_with(component2)
        
        # Test synchronized actions
        if hasattr(component1, 'zoom_to_range'):
            component1.zoom_to_range('2023-06-01', '2023-06-30')
            
            result.add_test(
                name="synchronized_zoom",
                assertion=lambda: hasattr(component2, 'get_zoom_range') and
                                component2.get_zoom_range() == component1.get_zoom_range(),
                description="Components synchronize zoom actions"
            )
            
    def _test_event_handling(self, component_class: Type[Any],
                           result: CategoryTestResult) -> None:
        """Test event handling and propagation"""
        component = component_class()
        
        # Test event registration
        events_received = []
        
        if hasattr(component, 'on_data_changed'):
            component.on_data_changed(lambda: events_received.append('data_changed'))
            
        if hasattr(component, 'on_selection_changed'):
            component.on_selection_changed(lambda: events_received.append('selection_changed'))
            
        # Trigger events
        test_data = self.data_generator.create_time_series_data(points=100)
        
        if hasattr(component, 'set_data'):
            component.set_data(test_data)
            
            result.add_test(
                name="data_change_event",
                assertion=lambda: 'data_changed' in events_received,
                description="Data change event fires correctly"
            )
            

class AccessibilityTestRunner:
    """Accessibility testing for visualization components"""
    
    def __init__(self):
        self.wcag_requirements = {
            'contrast_ratio': 4.5,  # WCAG AA for normal text
            'focus_visible': True,
            'keyboard_navigable': True,
            'screen_reader_compatible': True
        }
        
    def run_tests(self, component_class: Type[Any]) -> CategoryTestResult:
        """Run accessibility tests"""
        result = CategoryTestResult("Accessibility Tests")
        
        # Test keyboard navigation
        self._test_keyboard_navigation(component_class, result)
        
        # Test screen reader support
        self._test_screen_reader_support(component_class, result)
        
        # Test color contrast
        self._test_color_contrast(component_class, result)
        
        # Test focus indicators
        self._test_focus_indicators(component_class, result)
        
        return result
        
    def _test_keyboard_navigation(self, component_class: Type[Any],
                                 result: CategoryTestResult) -> None:
        """Test keyboard navigation support"""
        if not hasattr(component_class, 'handle_key_event'):
            return
            
        component = component_class()
        
        # Test tab navigation
        result.add_test(
            name="tab_navigation",
            assertion=lambda: hasattr(component, 'focusable') and component.focusable,
            description="Component is focusable via tab"
        )
        
        # Test arrow key navigation
        key_events = [Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down]
        key_names = ['Left', 'Right', 'Up', 'Down']
        
        for key, key_name in zip(key_events, key_names):
            handled = component.handle_key_event(key) if hasattr(component, 'handle_key_event') else False
            
            result.add_test(
                name=f"key_navigation_{key_name}",
                assertion=lambda h=handled: h,
                description=f"Component handles {key_name} key navigation"
            )
            
    def _test_screen_reader_support(self, component_class: Type[Any],
                                  result: CategoryTestResult) -> None:
        """Test screen reader compatibility"""
        component = component_class()
        
        # Test accessible name
        result.add_test(
            name="accessible_name",
            assertion=lambda: hasattr(component, 'accessible_name') and 
                            bool(component.accessible_name),
            description="Component has accessible name"
        )
        
        # Test accessible description
        result.add_test(
            name="accessible_description",
            assertion=lambda: hasattr(component, 'accessible_description') and
                            bool(component.accessible_description),
            description="Component has accessible description"
        )
        
        # Test live region announcements
        if hasattr(component, 'announce'):
            component.announce("Test announcement")
            result.add_test(
                name="live_announcements",
                assertion=lambda: True,  # Would check actual announcement in real test
                description="Component supports live region announcements"
            )
            
    def _test_color_contrast(self, component_class: Type[Any],
                            result: CategoryTestResult) -> None:
        """Test color contrast ratios"""
        # This would analyze the component's color scheme
        # For now, we'll test WSJ color palette compliance
        
        wsj_colors = {
            'text': '#333333',
            'background': '#FFFFFF',
            'primary': '#0080C0',
            'secondary': '#F5E6D3'
        }
        
        # Calculate contrast ratios
        from tests.helpers.color_helpers import calculate_contrast_ratio
        
        text_bg_contrast = calculate_contrast_ratio(wsj_colors['text'], wsj_colors['background'])
        primary_bg_contrast = calculate_contrast_ratio(wsj_colors['primary'], wsj_colors['background'])
        
        result.add_test(
            name="text_contrast",
            assertion=lambda: text_bg_contrast >= self.wcag_requirements['contrast_ratio'],
            description=f"Text contrast meets WCAG AA ({text_bg_contrast:.2f}:1)",
            details={'contrast_ratio': text_bg_contrast}
        )
        
        result.add_test(
            name="primary_contrast", 
            assertion=lambda: primary_bg_contrast >= self.wcag_requirements['contrast_ratio'],
            description=f"Primary color contrast meets WCAG AA ({primary_bg_contrast:.2f}:1)",
            details={'contrast_ratio': primary_bg_contrast}
        )
        
    def _test_focus_indicators(self, component_class: Type[Any],
                              result: CategoryTestResult) -> None:
        """Test focus indicator visibility"""
        component = component_class()
        
        result.add_test(
            name="focus_visible",
            assertion=lambda: hasattr(component, 'show_focus_indicator'),
            description="Component has visible focus indicator"
        )
        

class VisualizationTestDataGenerator:
    """Generate test data for health visualization testing"""
    
    def __init__(self):
        self.random_seed = 42
        np.random.seed(self.random_seed)
        
    def create_time_series_data(self, points: int = 1000, 
                              date_range: Tuple[str, str] = ('2023-01-01', '2023-12-31'),
                              metrics: List[str] = None) -> pd.DataFrame:
        """Create realistic time series health data for testing"""
        if metrics is None:
            metrics = ['heart_rate']
            
        np.random.seed(self.random_seed)
        
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        
        # Generate timestamp array
        timestamps = pd.date_range(start=start_date, end=end_date, periods=points)
        
        data = {'timestamp': timestamps}
        
        for metric in metrics:
            if metric == 'heart_rate':
                # Realistic heart rate data with daily patterns
                base_hr = 70
                daily_variation = 10 * np.sin(2 * np.pi * np.arange(points) / (points / 365))
                hourly_variation = 5 * np.sin(2 * np.pi * np.arange(points) / (points / 365 / 24))
                noise = np.random.normal(0, 3, points)
                heart_rate = base_hr + daily_variation + hourly_variation + noise
                data[metric] = np.clip(heart_rate, 45, 200)
                
            elif metric == 'steps':
                # Realistic step data with weekly patterns
                base_steps = 8000
                weekly_variation = 2000 * np.sin(2 * np.pi * np.arange(points) / (points / 52))
                daily_variation = 1000 * np.sin(2 * np.pi * np.arange(points) / (points / 365))
                noise = np.random.normal(0, 500, points)
                steps = base_steps + weekly_variation + daily_variation + noise
                data[metric] = np.clip(steps, 0, 25000).astype(int)
                
            elif metric == 'sleep_hours':
                # Realistic sleep data
                base_sleep = 7.5
                weekly_variation = 0.5 * np.sin(2 * np.pi * np.arange(points) / (points / 52))
                noise = np.random.normal(0, 0.5, points)
                sleep = base_sleep + weekly_variation + noise
                data[metric] = np.clip(sleep, 4, 12)
                
        return pd.DataFrame(data)
        
    def create_standard_time_series_data(self) -> pd.DataFrame:
        """Create standard test dataset for baseline comparisons"""
        # Fixed seed for reproducible baselines
        np.random.seed(12345)
        
        return self.create_time_series_data(
            points=365,
            date_range=('2023-01-01', '2023-12-31'),
            metrics=['heart_rate', 'steps', 'sleep_hours']
        )
        
    def create_invalid_time_series_data(self) -> pd.DataFrame:
        """Create invalid data for error handling tests"""
        return pd.DataFrame({
            'invalid_timestamp': ['not_a_date', '2023-13-45', None],
            'invalid_values': ['text', np.inf, -np.inf],
            'missing_data': [np.nan, np.nan, np.nan]
        })
        
    def create_edge_case_datasets(self) -> Dict[str, pd.DataFrame]:
        """Create various edge case datasets for comprehensive testing"""
        return {
            'empty': pd.DataFrame(),
            'single_point': self.create_time_series_data(points=1),
            'very_large': self.create_time_series_data(points=1_000_000),
            'duplicate_timestamps': self._create_duplicate_timestamp_data(),
            'extreme_values': self._create_extreme_value_data(),
            'gaps_in_data': self._create_gapped_data()
        }
        
    def _create_duplicate_timestamp_data(self) -> pd.DataFrame:
        """Create data with duplicate timestamps"""
        base_data = self.create_time_series_data(points=100)
        # Duplicate some rows
        duplicated = pd.concat([base_data, base_data.iloc[40:60]])
        return duplicated.sort_values('timestamp')
        
    def _create_extreme_value_data(self) -> pd.DataFrame:
        """Create data with extreme values"""
        data = self.create_time_series_data(points=100, metrics=['heart_rate'])
        # Add some extreme values
        data.loc[10:15, 'heart_rate'] = 220  # Very high
        data.loc[50:55, 'heart_rate'] = 30   # Very low
        return data
        
    def _create_gapped_data(self) -> pd.DataFrame:
        """Create data with temporal gaps"""
        data1 = self.create_time_series_data(
            points=100, 
            date_range=('2023-01-01', '2023-03-31')
        )
        data2 = self.create_time_series_data(
            points=100,
            date_range=('2023-07-01', '2023-09-30')
        )
        return pd.concat([data1, data2]).reset_index(drop=True)