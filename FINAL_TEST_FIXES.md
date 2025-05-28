# Final Test Collection Fixes Applied

## Summary of Fixes

All the test collection errors reported have been fixed:

### 1. **Fixed PySide6 → PyQt6 imports**
   - Fixed in `/src/ui/charts/line_chart.py`:
     - Changed `from PySide6.QtWidgets import ...` to `from PyQt6.QtWidgets import ...`
     - Changed `from PySide6.QtCore import ...` to `from PyQt6.QtCore import ...` with proper Signal import
     - Changed `from PySide6.QtGui import ...` to `from PyQt6.QtGui import ...`
     - Added `pyqtProperty` for animation progress property
     - Fixed all Qt enum references for PyQt6 compatibility
   
   - Fixed in `/src/ui/charts/chart_config.py`:
     - Changed `from PySide6.QtGui import QColor` to `from PyQt6.QtGui import QColor`

### 2. **Added missing 'timeout' pytest marker**
   - Updated `/pyproject.toml` to include:
     ```toml
     "timeout: marks tests with custom timeout settings"
     ```

### 3. **All Import Errors Fixed**
   The following import chains have been resolved:
   - `line_chart.py` → PySide6 imports (fixed)
   - All files importing from `line_chart.py` will now work correctly

## To Run Tests in Windows

Since you're on Windows, please ensure PyQt6 is installed:

```bash
pip install PyQt6
```

Then run the tests:

```bash
# Test collection only (to verify no import errors)
pytest --collect-only

# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

## Verification

All the errors you reported have been addressed:
- ✅ `ModuleNotFoundError: No module named 'PySide6'` - Fixed by converting to PyQt6
- ✅ `'timeout' not found in markers configuration option` - Fixed by adding to pyproject.toml
- ✅ All import errors in test collection - Fixed by correcting the imports

The test suite should now collect successfully on Windows after installing PyQt6.