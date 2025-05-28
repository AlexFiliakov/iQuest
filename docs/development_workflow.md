# Apple Health Monitor - Development Workflow

This document describes the centralized development workflow using the `run_dev.py` script.

## Overview

The `run_dev.py` script provides a unified entry point for all development activities, replacing the need to remember multiple script locations and commands.

## Quick Start

```bash
# Run the main application
python run_dev.py app

# Run all tests with coverage
python run_dev.py test all

# Run unit tests only
python run_dev.py test unit

# List available demos
python run_dev.py demos

# Run a specific demo
python run_dev.py demo bar_chart

# Check environment status
python run_dev.py status

# Fix environment issues
python run_dev.py fix
```

## Available Commands

### Application Commands

- `python run_dev.py app` - Run the main Apple Health Monitor dashboard
- `python run_dev.py status` - Show development environment status

### Testing Commands

- `python run_dev.py test unit` - Run unit tests with coverage
- `python run_dev.py test integration` - Run integration tests
- `python run_dev.py test performance` - Run performance benchmarks
- `python run_dev.py test visual` - Run visual regression tests
- `python run_dev.py test chaos` - Run chaos testing scenarios
- `python run_dev.py test all` - Run complete test suite
- `python run_dev.py test check` - Check test environment setup

#### Test Options

```bash
# Skip coverage reporting
python run_dev.py test unit --no-coverage

# Set coverage threshold
python run_dev.py test unit --coverage-threshold 85

# Save performance baseline
python run_dev.py test performance --save-baseline
```

### Demo Commands

- `python run_dev.py demos` - List all available demos
- `python run_dev.py demo <name>` - Run a specific demo

#### Available Demos

- `bar_chart` - Interactive bar chart component demo
- `line_chart` - Enhanced line chart with WSJ styling  
- `table` - Metric table component with pagination
- `journal` - General-purpose journaling system
- `month_over_month` - Month-over-month trends analysis

### Utility Commands

- `python run_dev.py fix` - Run environment fixes and dependency checks

## Development Scripts Integration

The following scripts are now integrated into the centralized workflow:

### Previously Standalone Scripts

1. **`src/main.py`** → `python run_dev.py app`
2. **`run_tests.py`** → `python run_dev.py test <type>`
3. **`fix_remaining_test_errors.py`** → `python run_dev.py fix`

### Demo Scripts

All demo scripts are accessible through the unified interface:

1. **`examples/bar_chart_demo.py`** → `python run_dev.py demo bar_chart`
2. **`src/examples/line_chart_demo.py`** → `python run_dev.py demo line_chart`
3. **`examples/table_usage_example.py`** → `python run_dev.py demo table`
4. **`examples/journal_example.py`** → `python run_dev.py demo journal`
5. **`src/ui/month_over_month_demo.py`** → `python run_dev.py demo month_over_month`

## Benefits of the Centralized Approach

1. **Consistency** - Single entry point for all development tasks
2. **Discoverability** - Easy to find and run demos/tests
3. **Maintainability** - Centralized path management and imports
4. **Documentation** - Self-documenting through help system

## Migration Notes

### For Developers

- Replace direct script execution with `run_dev.py` commands
- Use `python run_dev.py status` to verify environment setup
- Use `python run_dev.py demos` to discover available demos

### Script Path Resolution

All demo scripts now use robust path resolution:

```python
# Old approach (fragile)
sys.path.append('../src')

# New approach (robust)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))
```

This ensures scripts work correctly regardless of the current working directory.

## Adding New Development Scripts

To add a new development script to the centralized system:

1. Create your script in the appropriate location
2. Use robust path resolution for imports
3. Add an entry to the `DevRunner` class in `run_dev.py`
4. Update this documentation

### Example: Adding a New Demo

```python
# In run_dev.py, add to the demos dictionary:
'my_new_demo': {
    'path': 'examples/my_new_demo.py',
    'description': 'Description of what the demo does'
}
```

## Backward Compatibility

All existing scripts continue to work when run directly, but using the centralized approach is recommended for consistency and maintainability.