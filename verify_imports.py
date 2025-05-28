#!/usr/bin/env python3
"""Verify that all imports are working correctly."""

import sys
import traceback

def test_imports():
    """Test all the problematic imports."""
    errors = []
    
    print("Testing imports...")
    print("=" * 80)
    
    # Test 1: Import ChartConfig from chart_config
    try:
        from src.ui.charts.chart_config import ChartConfig
        print("✅ ChartConfig import from chart_config.py works")
    except Exception as e:
        errors.append(f"ChartConfig import failed: {e}")
        print(f"❌ ChartConfig import failed: {e}")
    
    # Test 2: Import EnhancedLineChart
    try:
        from src.ui.charts.enhanced_line_chart import EnhancedLineChart
        print("✅ EnhancedLineChart import works")
    except Exception as e:
        errors.append(f"EnhancedLineChart import failed: {e}")
        print(f"❌ EnhancedLineChart import failed: {e}")
    
    # Test 3: Import from charts module
    try:
        from src.ui.charts import EnhancedLineChart, ChartConfig, LineChartConfig
        print("✅ Imports from charts module work")
    except Exception as e:
        errors.append(f"Charts module imports failed: {e}")
        print(f"❌ Charts module imports failed: {e}")
        traceback.print_exc()
    
    # Test 4: Import component_factory
    try:
        from src.ui.component_factory import ComponentFactory
        print("✅ ComponentFactory import works")
    except Exception as e:
        errors.append(f"ComponentFactory import failed: {e}")
        print(f"❌ ComponentFactory import failed: {e}")
        traceback.print_exc()
    
    # Test 5: Import week_over_week_widget
    try:
        from src.ui.week_over_week_widget import WeekOverWeekWidget
        print("✅ WeekOverWeekWidget import works")
    except Exception as e:
        errors.append(f"WeekOverWeekWidget import failed: {e}")
        print(f"❌ WeekOverWeekWidget import failed: {e}")
        traceback.print_exc()
    
    print("=" * 80)
    
    if errors:
        print(f"\n❌ {len(errors)} import errors found")
        return False
    else:
        print("\n✅ All imports working correctly!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)