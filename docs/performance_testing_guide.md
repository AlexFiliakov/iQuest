# Performance Testing Guide

This guide covers performance testing practices for the Apple Health Analytics project.

## Table of Contents

1. [Overview](#overview)
2. [Running Benchmarks](#running-benchmarks)
3. [Writing Performance Tests](#writing-performance-tests)
4. [Understanding Results](#understanding-results)
5. [CI/CD Integration](#cicd-integration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Overview

Performance testing ensures our analytics components maintain acceptable speed and memory usage as data scales. We use:

- **pytest-benchmark**: For timing and statistical analysis
- **memory-profiler**: For memory usage tracking
- **psutil**: For system resource monitoring
- **Adaptive thresholds**: To account for different environments

## Running Benchmarks

### Basic Commands

```bash
# Run all performance tests
pytest -m performance

# Run specific benchmark groups
pytest -m benchmark --benchmark-only

# Run with detailed output
pytest -m performance -v --benchmark-verbose

# Generate HTML report
pytest -m performance --benchmark-histogram

# Run memory profiling tests
pytest tests/performance/test_memory_benchmarks.py

# Profile specific test with line-by-line memory
python -m memory_profiler tests/performance/test_memory_benchmarks.py::test_name
```

### Benchmark Options

```bash
# Control benchmark execution
--benchmark-min-rounds=5      # Minimum rounds to run
--benchmark-max-time=1.0      # Max time per benchmark
--benchmark-warmup=yes        # Enable warmup rounds
--benchmark-disable-gc        # Disable GC during benchmarks

# Save results
--benchmark-json=results.json # Save to JSON
--benchmark-autosave         # Auto-save to .benchmarks/

# Compare results
--benchmark-compare=HEAD     # Compare to git revision
--benchmark-compare-fail=5%  # Fail if 5% slower
```

## Writing Performance Tests

### Basic Performance Test

```python
from tests.performance import PerformanceBenchmark, AdaptiveThresholds

@pytest.mark.performance
class TestMyComponentPerformance(PerformanceBenchmark):
    
    def setup_method(self):
        """Set up test environment."""
        super().__init__()
        self.thresholds = AdaptiveThresholds()
    
    def test_operation_speed(self, benchmark):
        """Test operation performance."""
        data = generate_test_data()
        
        # Use pytest-benchmark
        result = benchmark.pedantic(
            my_operation,
            args=(data,),
            rounds=10,
            warmup_rounds=3
        )
        
        # Check against adaptive threshold
        threshold = self.thresholds.get_threshold(
            'my_operation',
            'duration'
        )
        assert result['mean'] < threshold
```

### Memory Usage Test

```python
def test_memory_efficiency(self):
    """Test memory usage stays within bounds."""
    with self.measure_performance('memory_test'):
        # Perform memory-intensive operation
        result = process_large_dataset()
    
    # Assert memory usage
    self.assert_performance(
        'memory_test',
        max_memory_growth_mb=100,
        max_peak_memory_mb=500
    )
```

### Scaling Test

```python
@pytest.mark.parametrize('size,max_time', [
    (1000, 0.1),     # Small: 100ms
    (10000, 0.5),    # Medium: 500ms  
    (100000, 3.0),   # Large: 3s
])
def test_linear_scaling(self, benchmark, size, max_time):
    """Test that performance scales linearly."""
    data = generate_data(size)
    
    result = benchmark(process_data, data)
    
    # Adjust threshold for environment
    threshold = self.thresholds.get_threshold(
        f'scaling_{size}',
        'duration',
        environment_adjust=True
    )
    
    assert result.stats['mean'] < min(max_time, threshold)
```

## Understanding Results

### Benchmark Output

```
-------------------------------- benchmark: 5 tests --------------------------------
Name (time in ms)          Min       Max      Mean    StdDev    Median      IQR
------------------------------------------------------------------------------------
test_small_dataset      15.234    18.567   16.123     1.234    15.987    0.567
test_medium_dataset    125.456   145.234  132.456     8.123   130.234    5.234
test_large_dataset     987.234  1234.567 1045.234    89.234  1023.456   45.234
------------------------------------------------------------------------------------
```

### Key Metrics

- **Min/Max**: Best and worst case times
- **Mean**: Average execution time
- **StdDev**: Consistency measure (lower is better)
- **Median**: Middle value (less affected by outliers)
- **IQR**: Interquartile range (variability measure)

### Memory Profile Output

```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    45     50.2 MiB     50.2 MiB           1   @profile
    46                                         def process_data():
    47     50.2 MiB      0.0 MiB           1       data = load_data()
    48    150.5 MiB    100.3 MiB           1       result = transform(data)
    49    125.3 MiB    -25.2 MiB           1       return aggregate(result)
```

## CI/CD Integration

### GitHub Actions

Performance benchmarks run automatically on:
- Pull requests (comparing to base branch)
- Daily schedule (tracking trends)
- Manual workflow dispatch

### Regression Detection

The CI pipeline:
1. Runs benchmarks on multiple platforms
2. Compares results to baseline
3. Comments on PRs with results
4. Alerts on performance regressions (>20% slower)

### Viewing Results

- **PR Comments**: Automatic table of benchmark results
- **Actions Tab**: Detailed logs and artifacts
- **Benchmark History**: Stored in `dev/bench` branch

## Best Practices

### 1. Write Realistic Tests

```python
# Good: Tests with realistic data
def test_daily_calculator_real_world(self, benchmark):
    # One year of realistic health data
    data = generate_realistic_health_data(days=365)
    calculator = DailyMetricsCalculator(data)
    benchmark(calculator.calculate_all_metrics)

# Bad: Oversimplified test
def test_calculator(self, benchmark):
    data = [1, 2, 3, 4, 5]
    benchmark(calculate, data)
```

### 2. Use Appropriate Fixtures

```python
@pytest.fixture(scope="session")
def large_dataset():
    """Generate once, reuse across tests."""
    return generate_large_dataset()

@pytest.fixture
def calculator(large_dataset):
    """Create calculator with data."""
    return Calculator(large_dataset)
```

### 3. Test Multiple Scenarios

```python
class TestPerformanceScenarios:
    
    def test_best_case(self, benchmark):
        """Sorted data, no edge cases."""
        data = generate_ideal_data()
        benchmark(process, data)
    
    def test_worst_case(self, benchmark):
        """Unsorted, many edge cases."""
        data = generate_pathological_data()
        benchmark(process, data)
    
    def test_typical_case(self, benchmark):
        """Real-world data distribution."""
        data = generate_realistic_data()
        benchmark(process, data)
```

### 4. Consider Environment

```python
def test_with_environment_awareness(self):
    """Adjust expectations based on environment."""
    thresholds = AdaptiveThresholds()
    
    # CI environments are typically slower
    if thresholds.is_ci_environment():
        margin = 2.0  # 100% slower acceptable
    else:
        margin = 1.2  # 20% slower acceptable
    
    max_time = thresholds.get_threshold(
        'test_name',
        'duration',
        margin=margin
    )
```

### 5. Document Performance Requirements

```python
def test_sla_compliance(self, benchmark):
    """
    SLA: Process 1 million records in < 5 seconds.
    
    This test ensures we meet our performance SLA for
    production workloads.
    """
    data = generate_records(1_000_000)
    result = benchmark(bulk_process, data)
    
    assert result.stats['mean'] < 5.0, "SLA violation"
```

## Troubleshooting

### Common Issues

1. **Flaky Tests**
   ```python
   # Increase rounds and warmup
   benchmark.pedantic(
       func,
       rounds=20,
       warmup_rounds=5
   )
   ```

2. **Environment Differences**
   ```python
   # Use adaptive thresholds
   threshold = self.thresholds.get_threshold(
       'test_name',
       'duration',
       environment_adjust=True
   )
   ```

3. **Memory Profiler Overhead**
   ```python
   # Disable for accurate timing
   @pytest.mark.skipif(
       PROFILING_ENABLED,
       reason="Memory profiling affects timing"
   )
   ```

4. **GC Interference**
   ```python
   # Disable GC during critical measurements
   import gc
   gc.disable()
   try:
       result = benchmark(func)
   finally:
       gc.enable()
   ```

### Debug Commands

```bash
# Verbose benchmark output
pytest -m performance -v --benchmark-verbose

# Save detailed results
pytest -m performance --benchmark-json=debug.json --benchmark-save=debug

# Profile specific test
python -m cProfile -o profile.stats test_file.py::test_name

# Analyze profile
python -m pstats profile.stats
```

### Performance Regression Checklist

When a performance regression is detected:

1. **Verify the regression**
   - Run locally with same Python version
   - Check multiple runs for consistency
   - Compare environments (local vs CI)

2. **Identify the cause**
   - Use git bisect to find the commit
   - Profile the specific operation
   - Check for algorithm changes

3. **Fix or accept**
   - Optimize if possible
   - Update thresholds if justified
   - Document why regression is acceptable

## Additional Resources

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [memory-profiler documentation](https://pypi.org/project/memory-profiler/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed)
- Project-specific benchmarks: `tests/performance/`