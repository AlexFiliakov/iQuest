# Windows Test Fixes - Final Steps

## Issues Fixed in This Update

### 1. ✅ Fixed Import Path Issues
- **Fixed**: `src/ui/configuration_tab.py` - Changed to relative imports
- **Fixed**: `tests/test_chaos_scenarios.py` - Changed HealthDataLoader to DataLoader alias
- **Fixed**: `tests/test_performance_benchmarks.py` - Removed pytest_plugins declaration
- **Fixed**: `src/ui/charts/base_chart.py` - Removed ABC metaclass conflict

### 2. ✅ Remaining Windows-Specific Steps

To complete the test setup on Windows:

```bash
# 1. Activate your Python environment
# For conda:
conda activate myenv

# For venv:
.\venv\Scripts\activate

# 2. Install test requirements
pip install -r requirements-test.txt

# 3. Run the fix script (optional - for verification)
python fix_remaining_test_errors.py

# 4. Run tests
python -m pytest
```

## Test Categories You Can Run

### Core Analytics Tests (No PyQt6 Required)
```bash
# Test data generator
python -m pytest tests/test_data_generator_basic.py -v

# Unit tests for analytics
python -m pytest tests/unit/test_daily_metrics_calculator.py -v
python -m pytest tests/unit/test_weekly_metrics_calculator.py -v
python -m pytest tests/unit/test_monthly_metrics_calculator.py -v
python -m pytest tests/unit/test_statistics_calculator.py -v

# Performance benchmarks
python -m pytest tests/test_performance_benchmarks.py -v

# Chaos testing
python -m pytest tests/test_chaos_scenarios.py -v
```

### Full Test Suite (Requires PyQt6)
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific categories
python -m pytest -m "not visual"  # Skip visual regression tests
python -m pytest -m "not slow"    # Skip slow tests
```

## Troubleshooting

### If PyQt6 Installation Fails
```bash
# Try specific version
pip install PyQt6==6.5.0

# Or install with Qt dependencies
pip install PyQt6 PyQt6-Qt6 PyQt6-sip
```

### If pytest-benchmark Fails
```bash
# Reinstall
pip uninstall pytest-benchmark
pip install pytest-benchmark
```

### If You Get "No module named 'src'"
Make sure you're running pytest from the project root directory:
```bash
cd "C:\Users\alexf\OneDrive\Documents\Projects\Apple Health Exports"
python -m pytest
```

## Summary of All Fixes Applied

1. **Dependency Installation**: faker, memory-profiler, pytest-benchmark, networkx, etc.
2. **Import Path Corrections**: Fixed ~15 import issues across source and test files
3. **Class Name Fixes**: TestDataGenerator → HealthDataGenerator, various alias fixes
4. **Framework Issues**: PySide6 → PyQt6, metaclass conflicts resolved
5. **Test Configuration**: Updated pyproject.toml with test markers

## Expected Results

After applying all fixes:
- ✅ 560+ tests should be collected
- ✅ Core analytics tests should pass (no PyQt6 required)
- ✅ UI tests should pass (with PyQt6 installed)
- ⚠️ Some minor test failures possible (data type assertions, etc.)

The test suite is now ready for use in your Windows development environment!