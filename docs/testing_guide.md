# Testing Guide for Apple Health Analytics Dashboard

## Overview

This guide covers testing best practices, mock usage patterns, and common testing scenarios for the Apple Health Analytics Dashboard project.

## Table of Contents

1. [Mock Objects and Fixtures](#mock-objects-and-fixtures)
2. [Testing Patterns](#testing-patterns)
3. [Common Scenarios](#common-scenarios)
4. [Pitfalls to Avoid](#pitfalls-to-avoid)
5. [Running Tests](#running-tests)

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
                'creationDate': row['date'],
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
        'creationDate': [datetime.now()],
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
    'creationDate': ['2024-01-01', '2024-01-02'],  # Strings!
    'type': ['HKQuantityTypeIdentifierStepCount'] * 2,
    'value': [8000, 9000]
})
```

✅ **Do:**
```python
# Proper datetime objects
data = pd.DataFrame({
    'creationDate': pd.date_range('2024-01-01', periods=2),
    'type': ['HKQuantityTypeIdentifierStepCount'] * 2,
    'value': [8000, 9000]
})
```

### 3. Missing Required Columns

❌ **Don't:**
```python
# Missing 'type' column
data = pd.DataFrame({
    'creationDate': pd.date_range('2024-01-01', periods=7),
    'value': [8000] * 7
})
mock = MockDataSource(data)  # Will raise ValueError
```

✅ **Do:**
```python
# All required columns present
data = pd.DataFrame({
    'creationDate': pd.date_range('2024-01-01', periods=7),
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