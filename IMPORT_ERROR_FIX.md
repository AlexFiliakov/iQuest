# Import Error Fix Applied

## Issue
The test collection was failing with ImportError:
```
ImportError: cannot import name 'ChartConfig' from 'src.ui.charts.enhanced_line_chart'
```

## Root Cause
- `ChartConfig` is defined in `src/ui/charts/chart_config.py`
- Files were incorrectly trying to import it from `enhanced_line_chart.py`
- `enhanced_line_chart.py` imports `LineChartConfig` from `chart_config.py` but doesn't re-export `ChartConfig`

## Fixes Applied

### 1. Fixed `/src/ui/component_factory.py`:
**Before:**
```python
from .charts.enhanced_line_chart import EnhancedLineChart, ChartConfig
```

**After:**
```python
from .charts.enhanced_line_chart import EnhancedLineChart
from .charts.chart_config import ChartConfig
```

### 2. Fixed `/src/ui/week_over_week_widget.py`:
**Before:**
```python
from .charts.enhanced_line_chart import EnhancedLineChart, ChartConfig
```

**After:**
```python
from .charts.enhanced_line_chart import EnhancedLineChart
from .charts.chart_config import ChartConfig
```

## Import Structure
The correct import structure is:
- `ChartConfig` and `LineChartConfig` are defined in `chart_config.py`
- `EnhancedLineChart` is defined in `enhanced_line_chart.py`
- The `charts/__init__.py` properly exports all these classes
- Import from the charts module when possible: `from src.ui.charts import ChartConfig, EnhancedLineChart`

## Verification
The import structure is now correct. The tests should collect successfully once PyQt6 is installed in your environment.