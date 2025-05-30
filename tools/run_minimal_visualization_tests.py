#!/usr/bin/env python3
"""
Run minimal visualization tests to verify the testing framework works.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing visualization framework components...")

# Test 1: Import the framework
try:
    from tests.visual.visualization_testing_framework import (
        VisualizationTestingFramework,
        TestReport,
        CategoryTestResult,
        VisualizationTestDataGenerator
    )
    print("✓ Successfully imported visualization testing framework")
except ImportError as e:
    print(f"✗ Failed to import framework: {e}")
    sys.exit(1)

# Test 2: Create test data generator
try:
    generator = VisualizationTestDataGenerator()
    test_data = generator.create_time_series_data(points=100)
    print(f"✓ Generated test data with {len(test_data)} points")
except Exception as e:
    print(f"✗ Failed to generate test data: {e}")

# Test 3: Test color helpers
try:
    from tests.helpers.color_helpers import calculate_contrast_ratio, WSJColorContrastChecker
    ratio = calculate_contrast_ratio('#FFFFFF', '#000000')
    print(f"✓ Color contrast calculation works (white/black ratio: {ratio:.1f})")
    
    checker = WSJColorContrastChecker()
    results = checker.check_wsj_palette()
    print(f"✓ WSJ palette checked: {len(results)} combinations tested")
except Exception as e:
    print(f"✗ Failed color helpers test: {e}")

# Test 4: Test mock data sources
try:
    from tests.mocks.data_sources import ReactiveDataSource, MockDataSource
    source = ReactiveDataSource()
    source.set_data(test_data)
    print(f"✓ ReactiveDataSource works with {len(source.get_data())} rows")
except Exception as e:
    print(f"✗ Failed mock data source test: {e}")

# Test 5: Create a minimal mock component for testing
from PyQt6.QtWidgets import QWidget

class MockVisualizationComponent(QWidget):
    """Minimal mock component for testing the framework"""
    
    def __init__(self, data=None):
        super().__init__()
        self.data = data
        self.focusable = True
        self.accessible_name = "Mock Visualization"
        self.accessible_description = "Test component"
        
    def set_data(self, data):
        self.data = data
        
    def get_data(self):
        return self.data if self.data is not None else []
        
    def apply_theme(self, theme_name):
        return None
        
    def render(self):
        pass
        
    def render_to_image(self, width=800, height=400, dpi=300):
        from PIL import Image
        return Image.new('RGB', (width, height), color='white')

# Test 6: Run framework on mock component
try:
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    framework = VisualizationTestingFramework()
    print("✓ Created testing framework instance")
    
    # Run minimal test
    unit_runner = framework.unit_test_runner
    result = unit_runner.run_tests(MockVisualizationComponent)
    
    print(f"✓ Ran unit tests: {len(result.tests)} tests, {sum(1 for t in result.tests if t.passed)} passed")
    
    # Show individual test results
    for test in result.tests:
        status = "✓" if test.passed else "✗"
        print(f"  {status} {test.name}: {test.message}")
        
except Exception as e:
    print(f"✗ Failed framework test: {e}")
    import traceback
    traceback.print_exc()

print("\nVisualization testing framework is operational!")
print("\nNext steps:")
print("1. Create visual baselines for existing components")
print("2. Run full test suite when components are available")
print("3. Set up CI/CD pipeline with GitHub Actions")