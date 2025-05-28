# Test Data Generation Guide

This guide explains how to use the test data generation system for Apple Health Monitor tests.

## Overview

The test data generation system provides a modular approach to creating realistic health data for testing. It consists of:

- **Base generators** - Abstract base classes for all generators
- **Health metric generators** - Generate realistic health metric values
- **Time series generators** - Create time-based data with patterns
- **Edge case generators** - Generate boundary and error conditions
- **Fixture factories** - Create ready-to-use test data fixtures

## Quick Start

### Using Pytest Fixtures

The easiest way to get test data is through the pytest fixtures:

```python
def test_analytics_with_sample_data(sample_health_data):
    """Test analytics with generated sample data."""
    # sample_health_data is a DataFrame with 30 days of data
    assert len(sample_health_data) == 30
    assert 'steps' in sample_health_data.columns
```

### Available Fixtures

- `health_data_generator` - Session-scoped generator instance
- `sample_health_data` - Function-scoped DataFrame with 30 days of data
- `user_profiles` - Dictionary of user profiles (sedentary, athlete, elderly)
- `dataset_size` - Parameterized fixture for small/medium/large datasets
- `time_series_generator` - Time series generator instance
- `edge_case_generator` - Edge case generator instance
- `edge_case_datasets` - Collection of pre-generated edge cases

## Generator Classes

### HealthMetricGenerator

Generates realistic health metric values with patterns:

```python
from tests.generators import HealthMetricGenerator

generator = HealthMetricGenerator(seed=42)

# Generate single metric value
steps = generator.generate('steps', datetime.now())

# Generate with user profile
athlete_profile = {'activity_multiplier': 1.6}
athlete_steps = generator.generate('steps', datetime.now(), athlete_profile)
```

Supported metrics:
- `steps` - Daily step count with weekly/seasonal patterns
- `heart_rate` - Heart rate with activity correlation
- `distance` - Distance in km, correlates with steps
- `calories` - Calorie burn, correlates with steps/distance
- `sleep_hours` - Sleep duration with weekly patterns
- `exercise_minutes` - Exercise time with weekly patterns

### TimeSeriesGenerator

Creates time series data with realistic correlations:

```python
from tests.generators import TimeSeriesGenerator

generator = TimeSeriesGenerator(seed=42)

# Generate basic time series
df = generator.generate_series(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    metrics=['steps', 'heart_rate', 'calories']
)

# Generate with gaps (missing data)
df_with_gaps = generator.generate_series(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    metrics=['steps', 'heart_rate'],
    include_gaps=True
)

# Generate with specific trends
trending_data = generator.generate_with_trends(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    metric='steps',
    trend_type='seasonal',  # linear, exponential, seasonal, cyclic
    trend_strength=0.2
)
```

### EdgeCaseGenerator

Creates edge case datasets for testing error handling:

```python
from tests.generators import EdgeCaseGenerator

generator = EdgeCaseGenerator(seed=42)

# Get all edge case datasets
edge_cases = generator.generate_edge_case_datasets()

# Available edge cases:
# - all_zeros: All metrics are zero
# - all_nulls: All metrics are null/None
# - single_point: Only one data point
# - extreme_values: Very large/negative values
# - missing_dates: Gaps in date sequence
# - duplicate_dates: Multiple entries for same date
# - perfect_correlation: Metrics perfectly correlated
# - no_correlation: Random uncorrelated data
# - monotonic_increase: Steadily increasing values
# - cyclic_pattern: Repeating patterns

# Add outliers to existing data
df_with_outliers = generator.generate_outliers(df, 'steps')

# Add empty periods
df_with_gaps = generator.generate_empty_periods(df)
```

### HealthDataFixtures

Factory class for creating complete test datasets:

```python
from tests.fixtures import HealthDataFixtures

# Create basic health DataFrame
df = HealthDataFixtures.create_health_dataframe(
    days=90,  # 3 months of data
    metrics=['steps', 'distance', 'calories', 'heart_rate'],
    include_anomalies=True
)

# Create user profiles
profiles = {
    'sedentary': HealthDataFixtures.create_user_profile(
        age=45, fitness_level='sedentary'
    ),
    'athlete': HealthDataFixtures.create_user_profile(
        age=25, fitness_level='athlete'
    )
}

# Get sample datasets for different scenarios
datasets = HealthDataFixtures.create_sample_datasets()
# Returns: small, medium, large, with_anomalies, athlete, sedentary
```

## Testing Patterns

### Performance Testing

```python
@pytest.mark.parametrize('dataset_size', ['small', 'medium', 'large'], indirect=True)
def test_analytics_performance(dataset_size, time_series_generator):
    """Test analytics performance with different data sizes."""
    df = time_series_generator.generate_series(
        start_date=datetime.now() - timedelta(days=dataset_size),
        end_date=datetime.now(),
        metrics=['steps', 'heart_rate', 'calories']
    )
    
    # Test your analytics with various data sizes
    start_time = time.time()
    results = analyze_data(df)
    duration = time.time() - start_time
    
    assert duration < expected_duration[dataset_size]
```

### Edge Case Testing

```python
def test_analytics_edge_cases(edge_case_datasets):
    """Test analytics with various edge cases."""
    for case_name, df in edge_case_datasets.items():
        try:
            result = analyze_data(df)
            # Verify graceful handling
            assert result is not None
        except Exception as e:
            # Some edge cases should raise specific exceptions
            if case_name == 'all_nulls':
                assert isinstance(e, DataError)
```

### Visual Regression Testing

```python
def test_chart_generation(sample_health_data):
    """Test chart generation with consistent data."""
    # Using seeded data ensures consistent visual output
    chart = generate_health_chart(sample_health_data)
    
    # Compare with baseline image
    assert_images_equal(chart, 'baseline_chart.png')
```

## Migration from Old System

If you have tests using the old `TestDataGenerator`:

1. Run the migration tool:
   ```bash
   python tools/migrate_test_data.py
   ```

2. Update any custom usage:
   ```python
   # Old
   from tests.test_data_generator import TestDataGenerator
   generator = TestDataGenerator()
   data = generator.generate_synthetic_data(365)
   
   # New
   from tests.fixtures import HealthDataFixtures
   data = HealthDataFixtures.create_health_dataframe(days=365)
   ```

3. Update method calls:
   - `generate_test_data()` → `generate()`
   - `create_test_dataframe()` → `create_health_dataframe()`
   - `generate_synthetic_data()` → `generate_series()`

## Best Practices

1. **Always use seeds for reproducibility**:
   ```python
   generator = HealthMetricGenerator(seed=42)
   ```

2. **Use appropriate data sizes**:
   - Unit tests: 7-30 days
   - Integration tests: 30-90 days
   - Performance tests: 365+ days

3. **Test with realistic patterns**:
   - Include weekly patterns (weekday vs weekend)
   - Add seasonal variations
   - Include data gaps and anomalies

4. **Use fixtures for common scenarios**:
   - Leverage pytest fixtures for standard test data
   - Create custom fixtures for specific test needs

5. **Document expected data characteristics**:
   ```python
   def test_with_athlete_data(user_profiles):
       """Test with high-activity user data.
       
       Expects:
       - Steps: 12,000-15,000 daily average
       - Heart rate: 55-65 resting average
       - Exercise: 60-90 minutes daily
       """
       data = generate_for_profile(user_profiles['athlete'])
   ```

## Troubleshooting

### Import Errors

If you get import errors:
```python
# Add to your test file
import sys
sys.path.insert(0, '.')
```

### Circular Imports

The migration tool may create circular imports. Fix by removing duplicate imports:
```python
# Remove duplicate line like:
from tests.fixtures import HealthDataFixtures  # Remove if already imported
```

### Data Validation

Always validate generated data:
```python
df = generator.generate_series(...)
assert not df.empty
assert df.index.is_unique
assert not df.isna().all().any()  # No columns are all NaN
```