---
task_id: G066
status: open
created: 2025-05-28
complexity: medium
sprint_ref: S05_M01_Visualization
dependencies: [G058]
parallel_group: quality
---

# Task G066: Visualization Testing Framework

## Description
Build comprehensive testing framework for health visualizations including unit tests, integration tests, visual regression testing, performance testing, and accessibility testing. Ensure reliable visualization behavior across all scenarios.

## Goals
- [ ] Create unit testing framework for visualization components
- [ ] Implement visual regression testing with image comparison
- [ ] Build performance testing and benchmarking suite
- [ ] Add integration testing for data binding and interactions
- [ ] Create accessibility testing automation
- [ ] Implement cross-browser compatibility testing

## Acceptance Criteria
- [ ] 90%+ code coverage for visualization components
- [ ] Visual regression tests catch styling and layout changes
- [ ] Performance tests validate render time and memory targets
- [ ] Integration tests cover all user interaction scenarios
- [ ] Accessibility tests run automatically in CI/CD
- [ ] Tests run successfully across Chrome, Firefox, Safari, Edge
- [ ] Test suite completes within 10 minutes for full run

## Technical Details

### Testing Architecture
```python
class VisualizationTestingFramework:
    """Comprehensive testing framework for health visualizations"""
    
    def __init__(self):
        self.unit_test_runner = VisualizationUnitTestRunner()
        self.visual_regression_tester = VisualRegressionTester()
        self.performance_tester = VisualizationPerformanceTester()
        self.integration_tester = VisualizationIntegrationTester()
        self.accessibility_tester = AccessibilityTestRunner()
        
    def run_full_test_suite(self, components: List[VisualizationComponent]) -> TestReport:
        """Run comprehensive test suite on visualization components"""
        pass
        
    def run_visual_regression_tests(self, baseline_dir: str, 
                                   output_dir: str) -> VisualRegressionReport:
        """Run visual regression testing"""
        pass
```

### Test Categories
1. **Unit Tests**: Component functionality, data processing, rendering logic
2. **Visual Regression**: Screenshot comparison, layout validation
3. **Performance Tests**: Render time, memory usage, animation smoothness
4. **Integration Tests**: Data binding, user interactions, cross-component behavior
5. **Accessibility Tests**: WCAG compliance, screen reader compatibility
6. **Cross-browser Tests**: Compatibility across different browsers and versions

### Test Data Management
- **Synthetic Data**: Generated test datasets with known characteristics
- **Real Data Samples**: Sanitized real health data for realistic testing
- **Edge Cases**: Boundary conditions, empty datasets, extreme values
- **Performance Data**: Large datasets for stress testing

### WSJ Testing Standards

Based on publication-quality requirements:

1. **Visual Quality Tests**
   - Pixel-perfect rendering
   - Correct WSJ styling
   - Typography consistency
   - Color accuracy

2. **Data Accuracy Tests**
   ```python
   class WSJDataAccuracyTests:
       TOLERANCE = {
           'position': 1.0,      # 1 pixel tolerance
           'color': 0.02,        # 2% color variance
           'value': 0.001,       # 0.1% data accuracy
           'timing': 16.67       # 1 frame (60fps)
       }
   ```

3. **Interaction Tests**
   - Responsive to all inputs
   - Smooth animations
   - Correct state transitions
   - Accessibility compliance

### Testing Approaches - Pros and Cons

#### Approach 1: PyTest with Qt Test
**Pros:**
- Native Qt testing support
- Good async handling
- Familiar pytest ecosystem
- Easy CI/CD integration

**Cons:**
- Limited visual testing
- Complex UI interactions
- No built-in screenshots

#### Approach 2: Selenium-based Testing
**Pros:**
- Real browser testing
- Visual regression tools
- Cross-platform testing
- Record/playback

**Cons:**
- Slower execution
- Complex setup
- Browser dependencies

#### Approach 3: Custom Testing Framework
**Pros:**
- Tailored to health data
- Optimized performance
- Deep integration
- Custom assertions

**Cons:**
- Development overhead
- Maintenance burden
- Learning curve

### Recommended Testing Strategy

1. **Unit Tests**: PyTest for logic
2. **Integration Tests**: Qt Test for UI
3. **Visual Tests**: Custom screenshot comparison
4. **Performance Tests**: Custom profiling
5. **Accessibility Tests**: axe-core integration

## Dependencies
- G058: Visualization Component Architecture

## Parallel Work
- Can be developed in parallel with G065 (Accessibility compliance)
- Works with all visualization components

## Implementation Notes
```python
class HealthVisualizationTestSuite:
    """Comprehensive test suite for health visualization components."""
    
    def __init__(self):
        self.test_data_generator = HealthTestDataGenerator()
        self.visual_comparator = VisualRegressionComparator()
        self.performance_profiler = VisualizationPerformanceProfiler()
        
    def test_time_series_chart(self, chart_class: Type[TimeSeriesChart]) -> TestResult:
        """Test time series chart with comprehensive scenarios."""
        
        test_result = TestResult(f"TimeSeriesChart_{chart_class.__name__}")
        
        # Unit tests
        test_result.add_category_results(
            self._run_time_series_unit_tests(chart_class)
        )
        
        # Visual regression tests
        test_result.add_category_results(
            self._run_time_series_visual_tests(chart_class)
        )
        
        # Performance tests
        test_result.add_category_results(
            self._run_time_series_performance_tests(chart_class)
        )
        
        # Integration tests
        test_result.add_category_results(
            self._run_time_series_integration_tests(chart_class)
        )
        
        return test_result
        
    def _run_time_series_unit_tests(self, chart_class: Type[TimeSeriesChart]) -> CategoryTestResult:
        """Run unit tests for time series chart."""
        
        category_result = CategoryTestResult("Unit Tests")
        
        # Test data processing
        test_data = self.test_data_generator.create_time_series_data(
            points=1000,
            date_range=('2023-01-01', '2023-12-31'),
            metrics=['heart_rate']
        )
        
        chart = chart_class(data=test_data)
        
        # Test 1: Data loading
        category_result.add_test(
            name="data_loading",
            assertion=lambda: len(chart.get_data()) == 1000,
            description="Chart loads correct number of data points"
        )
        
        # Test 2: Date range calculation
        category_result.add_test(
            name="date_range_calculation",
            assertion=lambda: chart.get_date_range() == ('2023-01-01', '2023-12-31'),
            description="Chart calculates correct date range"
        )
        
        # Test 3: Data filtering
        filtered_chart = chart.filter_by_date_range('2023-06-01', '2023-06-30')
        category_result.add_test(
            name="data_filtering",
            assertion=lambda: len(filtered_chart.get_data()) < 1000,
            description="Data filtering reduces dataset size"
        )
        
        # Test 4: Statistical calculations
        stats = chart.calculate_statistics()
        category_result.add_test(
            name="statistical_calculations",
            assertion=lambda: all(key in stats for key in ['mean', 'min', 'max', 'std']),
            description="Chart calculates basic statistics"
        )
        
        # Test 5: Empty data handling
        empty_chart = chart_class(data=pd.DataFrame())
        category_result.add_test(
            name="empty_data_handling",
            assertion=lambda: empty_chart.get_data().empty,
            description="Chart handles empty data gracefully"
        )
        
        # Test 6: Invalid data handling
        invalid_data = self.test_data_generator.create_invalid_time_series_data()
        try:
            invalid_chart = chart_class(data=invalid_data)
            category_result.add_test(
                name="invalid_data_handling",
                assertion=lambda: False,  # Should have raised exception
                description="Chart rejects invalid data"
            )
        except ValueError:
            category_result.add_test(
                name="invalid_data_handling",
                assertion=lambda: True,
                description="Chart rejects invalid data"
            )
            
        return category_result
        
    def _run_time_series_visual_tests(self, chart_class: Type[TimeSeriesChart]) -> CategoryTestResult:
        """Run visual regression tests for time series chart."""
        
        category_result = CategoryTestResult("Visual Regression Tests")
        
        # Standard rendering test
        standard_data = self.test_data_generator.create_standard_time_series_data()
        chart = chart_class(data=standard_data)
        
        # Render chart
        rendered_image = chart.render_to_image(width=800, height=400, dpi=300)
        
        # Compare with baseline
        baseline_path = f"test_baselines/{chart_class.__name__}_standard.png"
        comparison_result = self.visual_comparator.compare_images(
            baseline_path=baseline_path,
            test_image=rendered_image,
            threshold=0.95  # 95% similarity required
        )
        
        category_result.add_test(
            name="standard_rendering",
            assertion=lambda: comparison_result.similarity >= 0.95,
            description="Standard chart rendering matches baseline",
            details=comparison_result.get_details()
        )
        
        # Theme variations
        for theme_name in ['light', 'dark', 'high_contrast']:
            chart.apply_theme(theme_name)
            themed_image = chart.render_to_image(width=800, height=400, dpi=300)
            
            theme_baseline = f"test_baselines/{chart_class.__name__}_{theme_name}.png"
            theme_comparison = self.visual_comparator.compare_images(
                baseline_path=theme_baseline,
                test_image=themed_image,
                threshold=0.95
            )
            
            category_result.add_test(
                name=f"theme_{theme_name}_rendering",
                assertion=lambda: theme_comparison.similarity >= 0.95,
                description=f"Chart rendering with {theme_name} theme matches baseline"
            )
            
        # Responsive size variations
        for width, height in [(400, 200), (1200, 600), (1920, 1080)]:
            responsive_image = chart.render_to_image(width=width, height=height, dpi=300)
            
            size_baseline = f"test_baselines/{chart_class.__name__}_{width}x{height}.png"
            size_comparison = self.visual_comparator.compare_images(
                baseline_path=size_baseline,
                test_image=responsive_image,
                threshold=0.90  # Slightly lower threshold for responsive tests
            )
            
            category_result.add_test(
                name=f"responsive_{width}x{height}",
                assertion=lambda: size_comparison.similarity >= 0.90,
                description=f"Chart rendering at {width}x{height} matches baseline"
            )
            
        return category_result
        
    def _run_time_series_performance_tests(self, chart_class: Type[TimeSeriesChart]) -> CategoryTestResult:
        """Run performance tests for time series chart."""
        
        category_result = CategoryTestResult("Performance Tests")
        
        # Test with different data sizes
        data_sizes = [100, 1000, 10000, 100000]
        
        for size in data_sizes:
            test_data = self.test_data_generator.create_time_series_data(points=size)
            
            # Measure rendering performance
            performance_result = self.performance_profiler.profile_chart_rendering(
                chart_class=chart_class,
                data=test_data,
                render_config=RenderConfig(width=800, height=400)
            )
            
            # Render time test
            target_render_time = min(200, size * 0.002)  # 2ms per 1000 points, max 200ms
            category_result.add_test(
                name=f"render_time_{size}_points",
                assertion=lambda: performance_result.render_time <= target_render_time,
                description=f"Render time for {size} points under {target_render_time}ms",
                details=f"Actual: {performance_result.render_time}ms"
            )
            
            # Memory usage test
            target_memory = min(100_000_000, size * 1000)  # 1KB per point, max 100MB
            category_result.add_test(
                name=f"memory_usage_{size}_points",
                assertion=lambda: performance_result.peak_memory <= target_memory,
                description=f"Memory usage for {size} points under {target_memory / 1_000_000}MB",
                details=f"Actual: {performance_result.peak_memory / 1_000_000}MB"
            )
            
        # Animation performance test
        animation_data = self.test_data_generator.create_time_series_data(points=5000)
        chart = chart_class(data=animation_data)
        
        animation_performance = self.performance_profiler.profile_animation(
            chart=chart,
            animation_type='zoom',
            duration=1000  # 1 second
        )
        
        category_result.add_test(
            name="animation_smoothness",
            assertion=lambda: animation_performance.average_frame_time <= 16.67,  # 60fps
            description="Animation maintains 60fps",
            details=f"Average frame time: {animation_performance.average_frame_time}ms"
        )
        
        return category_result
        
    def _run_time_series_integration_tests(self, chart_class: Type[TimeSeriesChart]) -> CategoryTestResult:
        """Run integration tests for time series chart."""
        
        category_result = CategoryTestResult("Integration Tests")
        
        # Data binding integration
        reactive_data_source = ReactiveDataSource()
        chart = chart_class(data_source=reactive_data_source)
        
        # Test data updates
        initial_data = self.test_data_generator.create_time_series_data(points=100)
        reactive_data_source.set_data(initial_data)
        
        category_result.add_test(
            name="reactive_data_binding",
            assertion=lambda: len(chart.get_data()) == 100,
            description="Chart updates when data source changes"
        )
        
        # Test interactive features
        if hasattr(chart, 'enable_zoom'):
            chart.enable_zoom()
            zoom_result = chart.zoom_to_range('2023-06-01', '2023-06-30')
            
            category_result.add_test(
                name="zoom_interaction",
                assertion=lambda: zoom_result.success,
                description="Chart zoom interaction works correctly"
            )
            
        if hasattr(chart, 'enable_brush_selection'):
            chart.enable_brush_selection()
            selection_result = chart.select_range('2023-07-01', '2023-07-31')
            
            category_result.add_test(
                name="brush_selection",
                assertion=lambda: selection_result.selected_points > 0,
                description="Chart brush selection works correctly"
            )
            
        # Test multi-chart coordination
        second_chart = chart_class(data_source=reactive_data_source)
        coordinator = ChartInteractionCoordinator([chart, second_chart])
        
        # Zoom first chart
        chart.zoom_to_range('2023-08-01', '2023-08-31')
        
        category_result.add_test(
            name="chart_coordination",
            assertion=lambda: second_chart.get_zoom_range() == chart.get_zoom_range(),
            description="Charts coordinate interactions correctly"
        )
        
        return category_result
        
class HealthTestDataGenerator:
    """Generate test data for health visualization testing."""
    
    def __init__(self):
        self.random_seed = 42
        
    def create_time_series_data(self, points: int = 1000, 
                              date_range: Tuple[str, str] = ('2023-01-01', '2023-12-31'),
                              metrics: List[str] = ['heart_rate']) -> pd.DataFrame:
        """Create realistic time series health data for testing."""
        
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
                
        return pd.DataFrame(data)
        
    def create_invalid_time_series_data(self) -> pd.DataFrame:
        """Create invalid data for error handling tests."""
        
        return pd.DataFrame({
            'invalid_timestamp': ['not_a_date', '2023-13-45', None],
            'invalid_values': ['text', np.inf, -np.inf],
            'missing_data': [np.nan, np.nan, np.nan]
        })
        
    def create_edge_case_datasets(self) -> Dict[str, pd.DataFrame]:
        """Create various edge case datasets for comprehensive testing."""
        
        return {
            'empty': pd.DataFrame(),
            'single_point': self.create_time_series_data(points=1),
            'very_large': self.create_time_series_data(points=1_000_000),
            'duplicate_timestamps': self._create_duplicate_timestamp_data(),
            'extreme_values': self._create_extreme_value_data(),
            'gaps_in_data': self._create_gapped_data()
        }
```

### Practical Testing Implementation

```python
# src/ui/visualizations/tests/wsj_visual_test_framework.py
import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
import numpy as np
from PIL import Image, ImageChops
import io
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class VisualTestResult:
    """Result of visual comparison test"""
    passed: bool
    similarity: float
    diff_image: Optional[Image.Image]
    message: str

class WSJVisualTestFramework:
    """Visual regression testing for WSJ-styled charts"""
    
    def __init__(self):
        self.baseline_dir = "tests/visual_baselines"
        self.output_dir = "tests/visual_output"
        self.diff_threshold = 0.95  # 95% similarity required
        
    def test_chart_rendering(self, chart: HealthVisualizationComponent,
                           test_name: str) -> VisualTestResult:
        """Test chart rendering against baseline"""
        
        # Render chart
        rendered_image = self._render_chart_to_image(chart)
        
        # Load baseline
        baseline_path = f"{self.baseline_dir}/{test_name}.png"
        try:
            baseline_image = Image.open(baseline_path)
        except FileNotFoundError:
            # Save as new baseline
            rendered_image.save(baseline_path)
            return VisualTestResult(
                passed=True,
                similarity=1.0,
                diff_image=None,
                message="New baseline created"
            )
            
        # Compare images
        return self._compare_images(rendered_image, baseline_image, test_name)
        
    def _render_chart_to_image(self, chart: HealthVisualizationComponent) -> Image.Image:
        """Render chart to PIL Image"""
        
        # Render to QPixmap
        pixmap = chart.grab()
        
        # Convert to PIL Image
        buffer = io.BytesIO()
        pixmap.save(buffer, 'PNG')
        buffer.seek(0)
        
        return Image.open(buffer)
        
    def _compare_images(self, actual: Image.Image, expected: Image.Image,
                       test_name: str) -> VisualTestResult:
        """Compare two images for visual regression"""
        
        # Ensure same size
        if actual.size != expected.size:
            return VisualTestResult(
                passed=False,
                similarity=0.0,
                diff_image=None,
                message=f"Size mismatch: {actual.size} vs {expected.size}"
            )
            
        # Calculate difference
        diff = ImageChops.difference(actual, expected)
        
        # Calculate similarity score
        pixels = list(diff.getdata())
        total_diff = sum(sum(pixel) for pixel in pixels)
        max_diff = 255 * 3 * len(pixels)  # RGB channels
        similarity = 1.0 - (total_diff / max_diff)
        
        # Save diff image if failed
        if similarity < self.diff_threshold:
            diff_path = f"{self.output_dir}/{test_name}_diff.png"
            self._create_diff_visualization(actual, expected, diff).save(diff_path)
            
        return VisualTestResult(
            passed=similarity >= self.diff_threshold,
            similarity=similarity,
            diff_image=diff if similarity < self.diff_threshold else None,
            message=f"Similarity: {similarity:.2%}"
        )
        
    def _create_diff_visualization(self, actual: Image.Image, 
                                  expected: Image.Image,
                                  diff: Image.Image) -> Image.Image:
        """Create side-by-side diff visualization"""
        
        # Create composite image
        width = actual.width * 3 + 20
        height = actual.height + 40
        
        composite = Image.new('RGB', (width, height), 'white')
        
        # Add images
        composite.paste(expected, (0, 20))
        composite.paste(actual, (actual.width + 10, 20))
        composite.paste(diff, (actual.width * 2 + 20, 20))
        
        # Add labels (requires PIL draw)
        # ... label code ...
        
        return composite

# src/ui/visualizations/tests/performance_test_suite.py
class ChartPerformanceTestSuite:
    """Performance testing for health visualizations"""
    
    def __init__(self):
        self.performance_targets = {
            'render_time': 200,      # ms
            'memory_usage': 200,     # MB
            'frame_rate': 60,        # fps
            'interaction_latency': 16 # ms
        }
        
    @pytest.mark.performance
    def test_large_dataset_rendering(self, qtbot):
        """Test rendering performance with large dataset"""
        
        # Create large dataset
        data = self._generate_large_dataset(100_000)
        
        # Create chart
        chart = TimeSeriesChart(data)
        qtbot.addWidget(chart)
        
        # Measure render time
        start_time = time.perf_counter()
        chart.show()
        qtbot.waitExposed(chart)
        render_time = (time.perf_counter() - start_time) * 1000
        
        # Assert performance
        assert render_time < self.performance_targets['render_time'], \
            f"Render time {render_time}ms exceeds target"
            
    @pytest.mark.performance
    def test_animation_smoothness(self, qtbot):
        """Test animation frame rate"""
        
        chart = AnimatedHealthChart()
        qtbot.addWidget(chart)
        chart.show()
        
        # Measure frame times
        frame_times = []
        
        def measure_frame():
            nonlocal last_time
            current_time = time.perf_counter()
            if last_time:
                frame_times.append((current_time - last_time) * 1000)
            last_time = current_time
            
        last_time = None
        chart.frame_rendered.connect(measure_frame)
        
        # Run animation
        chart.start_animation()
        qtbot.wait(1000)  # 1 second
        chart.stop_animation()
        
        # Calculate average frame rate
        avg_frame_time = np.mean(frame_times)
        fps = 1000 / avg_frame_time
        
        assert fps >= self.performance_targets['frame_rate'], \
            f"Frame rate {fps:.1f} below target"
            
    @pytest.mark.performance 
    def test_memory_usage(self, qtbot):
        """Test memory usage with multiple charts"""
        
        import psutil
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple charts
        charts = []
        for i in range(10):
            data = self._generate_large_dataset(10_000)
            chart = TimeSeriesChart(data)
            charts.append(chart)
            
        # Measure memory after creation
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_usage = peak_memory - baseline_memory
        
        assert memory_usage < self.performance_targets['memory_usage'], \
            f"Memory usage {memory_usage}MB exceeds target"

# src/ui/visualizations/tests/accessibility_test_suite.py            
class AccessibilityTestSuite:
    """Automated accessibility testing for charts"""
    
    def __init__(self):
        self.wcag_validator = WCAGValidator()
        
    def test_keyboard_navigation(self, qtbot):
        """Test complete keyboard navigation"""
        
        chart = AccessibleHealthChart()
        qtbot.addWidget(chart)
        chart.show()
        
        # Test tab navigation
        QTest.keyClick(chart, Qt.Key.Key_Tab)
        assert chart.hasFocus()
        
        # Test arrow navigation
        QTest.keyClick(chart, Qt.Key.Key_Right)
        assert chart.focused_index == 1
        
        # Test home/end
        QTest.keyClick(chart, Qt.Key.Key_End)
        assert chart.focused_index == chart.data_point_count - 1
        
    def test_screen_reader_announcements(self, qtbot):
        """Test screen reader compatibility"""
        
        chart = AccessibleHealthChart()
        announcements = []
        
        # Capture announcements
        chart.announcement.connect(announcements.append)
        
        # Navigate to data point
        chart.focus_data_point(0)
        
        # Verify announcement
        assert len(announcements) == 1
        assert "Heart rate: 72 bpm" in announcements[0]
        assert "January 1" in announcements[0]
        
    def test_color_contrast(self):
        """Test WSJ color palette for WCAG compliance"""
        
        checker = WSJColorContrastChecker()
        results = checker.check_wsj_palette()
        
        # Critical combinations must pass
        assert results['text_on_background'].passes_aa
        assert results['primary_on_background'].passes_aa
        
        # Log any failures
        failures = [k for k, v in results.items() if not v.passes_aa]
        if failures:
            pytest.warning(f"Color combinations failing WCAG AA: {failures}")

# src/ui/visualizations/tests/test_fixtures.py            
@pytest.fixture
def app(qtbot):
    """Create QApplication for testing"""
    return QApplication.instance() or QApplication([])

@pytest.fixture
def sample_health_data():
    """Generate sample health data for testing"""
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='H')
    
    return pd.DataFrame({
        'timestamp': dates,
        'heart_rate': np.random.normal(70, 10, len(dates)),
        'steps': np.random.poisson(100, len(dates)),
        'calories': np.random.normal(50, 10, len(dates))
    })

@pytest.fixture
def wsj_theme():
    """WSJ theme configuration for testing"""
    return WSJThemeManager()

@pytest.fixture
def mock_data_source(mocker):
    """Mock data source for testing"""
    source = mocker.Mock()
    source.get_data.return_value = pd.DataFrame({
        'value': [1, 2, 3, 4, 5],
        'timestamp': pd.date_range('2023-01-01', periods=5)
    })
    return source

# Parametrized test example
@pytest.mark.parametrize("chart_type,data_size,expected_renderer", [
    ('line', 100, 'svg'),
    ('line', 10000, 'canvas'), 
    ('line', 1000000, 'webgl'),
    ('bar', 50, 'svg'),
    ('scatter', 50000, 'canvas'),
])
def test_adaptive_rendering(chart_type, data_size, expected_renderer):
    """Test adaptive renderer selection"""
    
    renderer = AdaptiveChartRenderer()
    data = pd.DataFrame({
        'value': np.random.rand(data_size),
        'timestamp': pd.date_range('2023-01-01', periods=data_size, freq='min')
    })
    
    selected = renderer._select_renderer(data_size, chart_type, QSize(800, 600))
    assert selected == expected_renderer
```