# Apple Health Monitor Testing Guide

This comprehensive guide documents the testing infrastructure, patterns, and best practices for the Apple Health Monitor project.

## Table of Contents

1. [Test Suite Overview](#test-suite-overview)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Test Fixtures](#test-fixtures)
5. [Mock Objects](#mock-objects)
6. [Testing Patterns](#testing-patterns)
7. [Writing New Tests](#writing-new-tests)
8. [Common Scenarios](#common-scenarios)
9. [Troubleshooting](#troubleshooting)

## Test Suite Overview

The Apple Health Monitor uses pytest as its testing framework with comprehensive coverage across:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing component interactions
- **UI Tests**: Testing PyQt6 widgets and user interfaces
- **Performance Tests**: Benchmarking critical operations
- **Visual Tests**: Screenshot comparison tests (when enabled)

### Key Statistics

- **Total Test Files**: 57
- **Test Coverage Goal**: 80%
- **Framework**: pytest 8.3.5
- **UI Testing**: pytest-qt 4.2.0
- **Parallel Testing**: pytest-xdist

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Global test configuration and fixtures
├── base_test_classes.py     # Base classes for test inheritance
├── fixtures/                # Test fixtures and data generators
│   ├── __init__.py
│   ├── database.py         # Database fixtures
│   ├── factories.py        # Data factories
│   └── health_fixtures.py  # Health data fixtures
├── generators/             # Test data generators
│   ├── base.py
│   ├── edge_cases.py
│   ├── health_data.py
│   └── time_series.py
├── helpers/                # Test utilities
│   ├── time_helpers.py
│   └── transaction_helpers.py
├── mocks/                 # Mock implementations
│   └── data_sources.py
├── integration/           # Integration tests
├── performance/          # Performance benchmarks
├── ui/                  # UI component tests
├── unit/               # Unit tests
└── visual/            # Visual regression tests
```

### Test Categories

#### Unit Tests (`tests/unit/`)
- **Analytics**: `test_analytics_optimized.py` - correlation, anomaly detection, causality
- **Calculators**: `test_*_metrics_calculator.py` - daily, weekly, monthly calculations
- **Data Processing**: `test_data_loader.py`, `test_database.py`
- **UI Components**: `test_preference_tracker.py`, `test_smart_default_selector.py`
- **Utilities**: `test_error_handler.py`, `test_logging.py`

#### Integration Tests (`tests/integration/`)
- **Database**: `test_database_integration.py`
- **Analytics**: `test_comparative_analytics_integration.py`
- **UI**: `test_smart_selection_integration.py`
- **XML Processing**: `test_xml_streaming_integration.py`

#### UI Tests (`tests/ui/`)
- **Components**: `test_component_factory.py`, `test_bar_chart_component.py`
- **Widgets**: `test_consolidated_widgets.py`, `test_summary_cards.py`

#### Performance Tests (`tests/performance/`)
- **Benchmarks**: `test_calculator_benchmarks.py`, `test_database_benchmarks.py`
- **Memory**: `test_memory_benchmarks.py`
- **Execution**: `test_execution_benchmark.py`

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_statistics_calculator.py

# Run specific test class
pytest tests/unit/test_analytics_optimized.py::TestCorrelationAnalysis

# Run specific test method
pytest tests/unit/test_analytics_optimized.py::TestCorrelationAnalysis::test_correlation_methods

# Run tests matching pattern
pytest -k "test_correlation"

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run with specific markers
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m ui            # UI tests only
pytest -m "not slow"    # Skip slow tests
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html

# Terminal coverage summary
pytest --cov=src --cov-report=term-missing

# XML coverage for CI
pytest --cov=src --cov-report=xml
```

## Test Fixtures

### Core Fixtures (conftest.py)

```python
# Qt Application
@pytest.fixture(scope='session')
def qapp():
    """QApplication instance for Qt tests."""
    
# Health Data
@pytest.fixture
def sample_health_data():
    """30 days of sample health data."""
    
# Database
@pytest.fixture
def memory_db():
    """In-memory SQLite database."""
    
# Calculators
@pytest.fixture
def daily_calculator(mock_data_source):
    """DailyMetricsCalculator with mock data."""
    
# UI Testing
@pytest.fixture
def qtbot():
    """PyQt6 test bot (from pytest-qt)."""
```

### Custom Fixtures

```python
# Visual Testing
@pytest.fixture
def visual_tester():
    """Visual regression testing helper."""
    
# Performance Testing
@pytest.fixture
def performance_benchmark():
    """Performance benchmark helper."""
    
# Chart Rendering
@pytest.fixture
def chart_renderer():
    """Chart rendering helper for visual tests."""
```

## Mock Objects and Fixtures

### Available Mock Data Sources

The project provides several mock data source implementations in `tests/mocks/data_sources.py`:

#### MockDataSource
Full implementation of `DataSourceProtocol` with realistic data handling.

```python
from tests.mocks import MockDataSource
from tests.fixtures.factories import FixtureFactory

# Create mock with generated data
data = FixtureFactory.create_health_data(days=30)
mock = MockDataSource(data)

# Use with calculators
calculator = DailyMetricsCalculator(mock)
```

#### EmptyDataSource
For testing edge cases with no data.

```python
from tests.mocks import EmptyDataSource

mock = EmptyDataSource()
# Returns empty DataFrame, empty metrics list, None date range
```

#### LargeDataSource
For performance testing with large datasets.

```python
from tests.mocks import LargeDataSource

# Creates 365 days of data for 4 metrics
mock = LargeDataSource(days=365)
```

#### CorruptDataSource
For testing error handling with invalid data.

```python
from tests.mocks import CorruptDataSource

mock = CorruptDataSource()
# Contains invalid dates, missing values, wrong types
```

### Fixture Factory

The `FixtureFactory` provides consistent test data generation:

```python
from tests.fixtures.factories import FixtureFactory

# Create health data
data = FixtureFactory.create_health_data(
    days=30,
    metrics=['HKQuantityTypeIdentifierStepCount'],
    include_gaps=True,
    include_anomalies=True
)

# Create pre-configured data source
mock = FixtureFactory.create_data_source(days=30)

# Specialized datasets
weekly_data = FixtureFactory.create_weekly_data()
monthly_data = FixtureFactory.create_monthly_data()
yearly_data = FixtureFactory.create_year_data()
```

### Pytest Fixtures

Available fixtures in `conftest.py`:

```python
def test_with_fixtures(
    health_data,          # 30 days of health data
    mock_data_source,     # MockDataSource with health_data
    daily_calculator,     # DailyMetricsCalculator with mock
    weekly_calculator,    # WeeklyMetricsCalculator
    monthly_calculator    # MonthlyMetricsCalculator
):
    # Test implementation
    pass
```

## Testing Patterns

### Pattern 1: Calculator Chain Testing

```python
def test_calculator_chain():
    # Create data source
    mock = LargeDataSource(days=60)
    
    # Build calculator chain
    daily = DailyMetricsCalculator(mock)
    weekly = WeeklyMetricsCalculator(daily)
    monthly = MonthlyMetricsCalculator(daily)
    
    # Test calculations
    stats = daily.calculate_statistics('HKQuantityTypeIdentifierStepCount')
    assert stats.mean > 0
```

### Pattern 2: Data Transformation Testing

```python
def test_data_transformation():
    # Original format (from CSV/XML)
    raw_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=7),
        'steps': [8000, 9000, 7500, 8500, 9500, 6000, 7000],
        'distance': [5.0, 5.5, 4.8, 5.2, 5.8, 4.0, 4.5]
    })
    
    # Transform to expected format
    transformed = []
    for _, row in raw_data.iterrows():
        for metric, value in [('steps', row['steps']), ('distance', row['distance'])]:
            transformed.append({
                'startDate': row['date'],
                'type': f'HKQuantityTypeIdentifier{metric.title()}',
                'value': value
            })
    
    data_df = pd.DataFrame(transformed)
    mock = MockDataSource(data_df)
    
    # Verify transformation
    assert len(mock.get_available_metrics()) == 2
```

### Pattern 3: Edge Case Testing

```python
def test_edge_cases():
    # Empty data
    empty = EmptyDataSource()
    calc = DailyMetricsCalculator(empty)
    stats = calc.calculate_statistics('AnyMetric')
    assert stats.insufficient_data
    
    # Single data point
    single_point = pd.DataFrame({
        'startDate': [datetime.now()],
        'type': ['HKQuantityTypeIdentifierStepCount'],
        'value': [5000]
    })
    mock = MockDataSource(single_point)
    calc = DailyMetricsCalculator(mock)
    stats = calc.calculate_statistics('HKQuantityTypeIdentifierStepCount')
    assert stats.count == 1
    assert stats.mean == 5000
    assert stats.std is None  # Not enough data
```

## Common Scenarios

### Scenario 1: Testing Date Range Filtering

```python
def test_date_range_filtering():
    mock = LargeDataSource(days=365)
    calc = DailyMetricsCalculator(mock)
    
    # Test specific month
    start_date = date(2024, 3, 1)
    end_date = date(2024, 3, 31)
    
    stats = calc.calculate_statistics(
        'HKQuantityTypeIdentifierStepCount',
        start_date=start_date,
        end_date=end_date
    )
    
    assert stats.count <= 31  # At most 31 days in March
```

### Scenario 2: Testing Multiple Metrics

```python
def test_multiple_metrics():
    metrics = [
        'HKQuantityTypeIdentifierStepCount',
        'HKQuantityTypeIdentifierDistanceWalkingRunning',
        'HKQuantityTypeIdentifierActiveEnergyBurned'
    ]
    
    mock = FixtureFactory.create_data_source(days=30, metrics=metrics)
    calc = DailyMetricsCalculator(mock)
    
    summary = calc.get_metrics_summary(metrics)
    
    assert len(summary) == 3
    for metric in metrics:
        assert metric in summary
        assert summary[metric].count > 0
```

### Scenario 3: Testing Data Consistency

```python
def test_data_consistency():
    # Create known data
    data = FixtureFactory.create_health_data(days=7)
    mock = MockDataSource(data)
    
    # Multiple calls should return consistent data
    df1 = mock.get_dataframe()
    df2 = mock.get_dataframe()
    
    # Verify immutability
    df1.loc[0, 'value'] = -999
    df2_check = mock.get_dataframe()
    assert df2_check.loc[0, 'value'] != -999
```

## Pitfalls to Avoid

### 1. Direct DataFrame Modification

❌ **Don't:**
```python
mock = MockDataSource(data)
df = mock.get_dataframe()
df['value'] = df['value'] * 2  # Modifies the returned copy, not the source
```

✅ **Do:**
```python
mock = MockDataSource(data)
df = mock.get_dataframe()
df = df.copy()  # Explicit copy if modifications needed
df['value'] = df['value'] * 2
```

### 2. Incorrect Date Handling

❌ **Don't:**
```python
# String dates without proper conversion
data = pd.DataFrame({
    'startDate': ['2024-01-01', '2024-01-02'],  # Strings!
    'type': ['HKQuantityTypeIdentifierStepCount'] * 2,
    'value': [8000, 9000]
})
```

✅ **Do:**
```python
# Proper datetime objects
data = pd.DataFrame({
    'startDate': pd.date_range('2024-01-01', periods=2),
    'type': ['HKQuantityTypeIdentifierStepCount'] * 2,
    'value': [8000, 9000]
})
```

### 3. Missing Required Columns

❌ **Don't:**
```python
# Missing 'type' column
data = pd.DataFrame({
    'startDate': pd.date_range('2024-01-01', periods=7),
    'value': [8000] * 7
})
mock = MockDataSource(data)  # Will raise ValueError
```

✅ **Do:**
```python
# All required columns present
data = pd.DataFrame({
    'startDate': pd.date_range('2024-01-01', periods=7),
    'type': ['HKQuantityTypeIdentifierStepCount'] * 7,
    'value': [8000] * 7
})
mock = MockDataSource(data)
```

## Running Tests

### Running All Tests
```bash
pytest
```

### Running Specific Test Files
```bash
# Run mock compliance tests
pytest tests/test_mock_compliance.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Running with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Running Specific Test Classes or Methods
```bash
# Run specific test class
pytest tests/test_mock_compliance.py::TestMockCompliance -v

# Run specific test method
pytest tests/test_mock_compliance.py::TestMockCompliance::test_mock_implements_protocol -v
```

### Common Test Flags
- `-v`: Verbose output
- `-s`: Show print statements
- `-x`: Stop on first failure
- `--lf`: Run last failed tests
- `-k "pattern"`: Run tests matching pattern

## Best Practices

1. **Use Type Hints**: Always type hint test parameters and return values
2. **Test Isolation**: Each test should be independent
3. **Descriptive Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Mock at Boundaries**: Mock external dependencies, not internal components
6. **Test One Thing**: Each test should verify one behavior
7. **Use Fixtures**: Leverage pytest fixtures for common setup

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
1. Ensure virtual environment is activated
2. Install all dependencies: `pip install -r requirements.txt`
3. Check PYTHONPATH includes src directory

### Mock Data Issues
If mocks aren't behaving as expected:
1. Verify required columns are present
2. Check data types match expectations
3. Ensure dates are datetime objects, not strings
4. Use `mock.get_available_metrics()` to debug

### Calculator Chain Issues
If calculators fail in chain:
1. Verify data source implements DataSourceProtocol
2. Check data has required columns
3. Ensure proper date handling
4. Test each calculator in isolation first