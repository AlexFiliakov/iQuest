# G070: Consolidate and Prune Duplicate/Redundant Tests

## Status: ACTIVE
Priority: MEDIUM
Type: REFACTOR
Parallel: No (should be done after other fixes to avoid conflicts)

## Problem Summary
Test suite has grown with many duplicate and redundant tests:
- `test_comprehensive_unit_coverage.py` has 43 failing instances
- Multiple test files testing same functionality
- Overlapping integration and unit tests
- Redundant test cases within same files

## Analysis of Duplicates
1. **Comprehensive unit coverage overlaps**
   - Duplicates functionality-specific unit tests
   - Should be consolidated or removed

2. **Multiple widget test files**
   - `test_week_over_week_widget.py` (23 failures)
   - `test_comparison_overlay_widget.py` (24 failures)
   - Similar test patterns repeated

3. **Redundant calculator tests**
   - Same calculations tested in multiple places
   - Integration tests duplicating unit test coverage

## Implementation Options Analysis

### Option A: Aggressive Consolidation
**Pros:**
- Maximum reduction in test count
- Fastest test execution
- Minimal maintenance

**Cons:**
- Risk of losing edge cases
- Harder to identify failures
- Less granular coverage reports

### Option B: Moderate Refactoring (Recommended)
**Pros:**
- Balance between coverage and speed
- Maintains test clarity
- Easier to debug failures
- Preserves important edge cases

**Cons:**
- Still some duplication
- More files than minimum

### Option C: Minimal Changes
**Pros:**
- Low risk of breaking tests
- Preserves all current coverage
- Easy to implement

**Cons:**
- Minimal performance gain
- Duplication remains
- Maintenance burden continues

## Detailed Implementation Plan

### Phase 1: Test Coverage Analysis
1. **Create comprehensive test matrix**
   ```python
   # tools/analyze_test_coverage.py
   import ast
   import os
   from collections import defaultdict
   from pathlib import Path
   
   class TestAnalyzer:
       def __init__(self):
           self.test_map = defaultdict(list)
           self.duplicate_tests = []
           self.coverage_map = {}
       
       def analyze_test_file(self, filepath: Path):
           """Analyze single test file for coverage."""
           with open(filepath, 'r') as f:
               tree = ast.parse(f.read())
           
           for node in ast.walk(tree):
               if isinstance(node, ast.FunctionDef):
                   if node.name.startswith('test_'):
                       test_info = {
                           'file': filepath.name,
                           'class': self._get_class_name(node),
                           'method': node.name,
                           'imports': self._extract_imports(tree),
                           'fixtures': self._extract_fixtures(node)
                       }
                       
                       # Categorize by what it tests
                       category = self._categorize_test(test_info)
                       self.test_map[category].append(test_info)
       
       def find_duplicates(self):
           """Identify duplicate tests across files."""
           seen_tests = {}
           
           for category, tests in self.test_map.items():
               for test in tests:
                   key = self._create_test_signature(test)
                   if key in seen_tests:
                       self.duplicate_tests.append({
                           'original': seen_tests[key],
                           'duplicate': test,
                           'similarity': self._calculate_similarity(
                               seen_tests[key], test
                           )
                       })
                   else:
                       seen_tests[key] = test
       
       def generate_report(self):
           """Generate consolidation recommendations."""
           report = {
               'total_tests': sum(len(tests) for tests in self.test_map.values()),
               'categories': len(self.test_map),
               'duplicates': len(self.duplicate_tests),
               'recommendations': self._generate_recommendations()
           }
           return report
   ```

2. **Identify consolidation opportunities**
   - [ ] Run analyzer on entire test suite
   - [ ] Review duplicate detection results
   - [ ] Categorize tests by component
   - [ ] Identify overlapping integration tests

### Phase 2: Test Reorganization Strategy
1. **New test structure**
   ```
   tests/
   ├── unit/                    # Pure unit tests
   │   ├── analytics/          # Analytics components
   │   │   ├── test_daily_calculator.py
   │   │   ├── test_weekly_calculator.py
   │   │   └── test_statistics.py
   │   ├── ui/                 # UI components
   │   │   ├── test_charts.py  # All chart tests
   │   │   ├── test_widgets.py # All widget tests
   │   │   └── test_cards.py   # All card tests
   │   └── data/               # Data processing
   │       ├── test_loaders.py
   │       └── test_validators.py
   ├── integration/            # Integration tests
   │   ├── test_analytics_flow.py
   │   ├── test_ui_integration.py
   │   └── test_data_pipeline.py
   ├── performance/            # Performance tests
   └── visual/                 # Visual regression tests
   ```

2. **Consolidation rules**
   - Merge tests testing identical functionality
   - Combine similar widget tests into parametrized tests
   - Extract common test patterns into base classes
   - Move integration tests out of unit test files

### Phase 3: Test Consolidation Implementation
1. **Create base test classes**
   ```python
   # tests/base_test_classes.py
   class BaseCalculatorTest:
       """Base class for calculator tests."""
       
       def assert_calculation(self, calculator, input_data, expected):
           """Common assertion pattern."""
           result = calculator.calculate(input_data)
           assert result == pytest.approx(expected, rel=1e-5)
       
       def test_empty_data_handling(self, calculator_class):
           """Common empty data test."""
           calc = calculator_class(pd.DataFrame())
           assert calc.calculate() == {}
       
       def test_null_handling(self, calculator_class):
           """Common null handling test."""
           data = pd.DataFrame({'value': [1, None, 3]})
           calc = calculator_class(data)
           result = calc.calculate()
           assert not pd.isna(result).any()
   
   class BaseWidgetTest:
       """Base class for widget tests."""
       
       @pytest.fixture
       def qt_app(self):
           """Common Qt application fixture."""
           app = QApplication.instance() or QApplication([])
           yield app
           app.quit()
       
       def test_initialization(self, widget_class):
           """Common initialization test."""
           widget = widget_class()
           assert widget.isVisible() is False
           assert widget.layout() is not None
   ```

2. **Merge duplicate test files**
   ```python
   # Example: Consolidate widget tests
   # Before: test_week_over_week_widget.py, test_comparison_overlay_widget.py
   # After: test_analytics_widgets.py
   
   @pytest.mark.parametrize('widget_class,config', [
       (WeekOverWeekWidget, {'type': 'weekly'}),
       (ComparisonOverlayWidget, {'type': 'overlay'}),
       (MonthlyContextWidget, {'type': 'monthly'})
   ])
   class TestAnalyticsWidgets(BaseWidgetTest):
       """Consolidated analytics widget tests."""
       
       def test_widget_creation(self, qt_app, widget_class, config):
           """Test all widgets can be created."""
           widget = widget_class(**config)
           assert isinstance(widget, QWidget)
       
       def test_data_update(self, qt_app, widget_class, config, sample_data):
           """Test all widgets handle data updates."""
           widget = widget_class(**config)
           widget.update_data(sample_data)
           assert widget.has_data() is True
   ```

### Phase 4: Remove test_comprehensive_unit_coverage.py
1. **Distribute tests to appropriate files**
   - [ ] Map each test to its component
   - [ ] Move to component-specific test file
   - [ ] Ensure no loss of coverage
   - [ ] Delete the comprehensive file

2. **Update imports and references**
   ```python
   # tools/distribute_comprehensive_tests.py
   def distribute_tests(comprehensive_file, target_mapping):
       """Distribute tests from comprehensive file."""
       with open(comprehensive_file, 'r') as f:
           content = f.read()
       
       # Parse and categorize tests
       tree = ast.parse(content)
       tests_by_component = categorize_tests(tree)
       
       # Write to appropriate files
       for component, tests in tests_by_component.items():
           target_file = target_mapping[component]
           append_tests_to_file(target_file, tests)
   ```

### Phase 5: Optimize Test Execution
1. **Implement test markers**
   ```python
   # pytest.ini additions
   markers =
       unit: Unit tests (fast)
       integration: Integration tests (slower)
       slow: Slow tests
       ui: UI tests requiring Qt
       performance: Performance benchmarks
   ```

2. **Create test execution profiles**
   ```bash
   # Fast unit tests only
   pytest -m "unit and not slow"
   
   # UI tests only
   pytest -m ui
   
   # Everything except performance
   pytest -m "not performance"
   ```

### Phase 6: Verification and Documentation
1. **Coverage verification**
   ```bash
   # Before consolidation
   pytest --cov=src --cov-report=html
   mv htmlcov htmlcov_before
   
   # After consolidation
   pytest --cov=src --cov-report=html
   
   # Compare coverage
   diff_coverage.py htmlcov_before htmlcov
   ```

2. **Performance comparison**
   - [ ] Measure test execution time before
   - [ ] Measure after consolidation
   - [ ] Document performance gains
   - [ ] Create optimization report

## Affected Files (Detailed)
### Files to remove/consolidate:
- `test_comprehensive_unit_coverage.py` → Distribute to component tests
- `test_week_over_week_widget.py` → Merge into `test_analytics_widgets.py`
- `test_comparison_overlay_widget.py` → Merge into `test_analytics_widgets.py`

### Files to create:
- `tests/base_test_classes.py`
- `tests/unit/analytics/test_all_calculators.py`
- `tests/unit/ui/test_all_widgets.py`
- `tools/analyze_test_coverage.py`
- `tools/distribute_comprehensive_tests.py`

### Files to update:
- All remaining test files for new structure
- `pytest.ini` for markers
- `conftest.py` for shared fixtures

## Risk Mitigation
1. **Coverage protection**
   - Run coverage before any changes
   - Verify after each consolidation
   - Keep backup of original tests

2. **Gradual approach**
   - Consolidate one category at a time
   - Run full test suite after each change
   - Rollback if coverage drops

## Success Criteria
- [ ] Test count reduced by 40%+ (from ~400 to ~240)
- [ ] Test execution time reduced by 35%+
- [ ] Code coverage maintained at 90%+
- [ ] No duplicate test implementations
- [ ] Clear test organization structure
- [ ] All tests properly categorized with markers
- [ ] Documentation updated with new structure