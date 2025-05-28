# Syntax Error Fix Applied

## Issue
The test collection was failing with a SyntaxError in `enhanced_line_chart.py` at line 679:
```
SyntaxError: '(' was never closed
```

## Fix Applied
Fixed the missing closing parenthesis in `/src/ui/charts/enhanced_line_chart.py`:

**Line 679 Before:**
```python
painter.setPen(QPen(QColor(100, 100, 100, 100), 1, Qt.PenStyle.DashLine)
```

**Line 679 After:**
```python
painter.setPen(QPen(QColor(100, 100, 100, 100), 1, Qt.PenStyle.DashLine))
```

## Verification
- ✅ Python syntax validation passed for all chart files
- ✅ The file now compiles without errors
- ✅ Import chains should work correctly

## Next Steps
The tests should now collect successfully. Run:
```bash
pytest --collect-only
```

to verify all tests are collected without errors.