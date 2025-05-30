#!/usr/bin/env python3
"""
Run comprehensive visualization tests for health dashboard components.

This script executes the visualization testing framework against all available
components and generates reports.
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.visual.visualization_testing_framework import VisualizationTestingFramework


def discover_visualization_components():
    """Discover all visualization components to test"""
    components = []
    
    # Import chart components
    try:
        from src.ui.charts.line_chart import LineChart
        components.append(('LineChart', LineChart))
    except ImportError as e:
        print(f"Could not import LineChart: {e}")
        
    try:
        from src.ui.charts.enhanced_line_chart import EnhancedLineChart
        components.append(('EnhancedLineChart', EnhancedLineChart))
    except ImportError as e:
        print(f"Could not import EnhancedLineChart: {e}")
        
    try:
        from src.ui.bar_chart_component import BarChartComponent
        components.append(('BarChartComponent', BarChartComponent))
    except ImportError as e:
        print(f"Could not import BarChartComponent: {e}")
        
    try:
        from src.ui.charts.calendar_heatmap import CalendarHeatmap
        components.append(('CalendarHeatmap', CalendarHeatmap))
    except ImportError as e:
        print(f"Could not import CalendarHeatmap: {e}")
        
    try:
        from src.ui.charts.waterfall_chart import WaterfallChart
        components.append(('WaterfallChart', WaterfallChart))
    except ImportError as e:
        print(f"Could not import WaterfallChart: {e}")
        
    # Import visualization widgets
    try:
        from src.ui.health_score_visualizations import HealthScoreGauge
        components.append(('HealthScoreGauge', HealthScoreGauge))
    except ImportError as e:
        print(f"Could not import HealthScoreGauge: {e}")
        
    try:
        from src.ui.week_over_week_widget import WeekOverWeekWidget
        components.append(('WeekOverWeekWidget', WeekOverWeekWidget))
    except ImportError as e:
        print(f"Could not import WeekOverWeekWidget: {e}")
        
    try:
        from src.ui.correlation_matrix_widget import CorrelationMatrixWidget
        components.append(('CorrelationMatrixWidget', CorrelationMatrixWidget))
    except ImportError as e:
        print(f"Could not import CorrelationMatrixWidget: {e}")
        
    return components


def run_tests():
    """Run visualization tests and generate reports"""
    print("=" * 80)
    print("Health Dashboard Visualization Testing")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print()
    
    # Create test directories
    Path("tests/results").mkdir(parents=True, exist_ok=True)
    Path("tests/visual_baselines").mkdir(parents=True, exist_ok=True)
    
    # Discover components
    print("Discovering visualization components...")
    components = discover_visualization_components()
    print(f"Found {len(components)} components to test")
    
    if not components:
        print("No components found to test!")
        return 1
    
    # Initialize testing framework
    print("\nInitializing testing framework...")
    framework = VisualizationTestingFramework()
    
    # Run tests on discovered components
    print("\nRunning tests...")
    test_classes = [comp[1] for comp in components]
    reports = framework.run_full_test_suite(test_classes)
    
    # Generate summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    
    for report in reports:
        print(f"\n{report.component_name}:")
        print(f"  Total Tests: {report.total_tests}")
        print(f"  Passed: {report.passed_tests}")
        print(f"  Failed: {report.total_tests - report.passed_tests}")
        print(f"  Pass Rate: {(report.passed_tests/report.total_tests*100):.1f}%")
        
        total_tests += report.total_tests
        total_passed += report.passed_tests
        
        # Show category breakdown
        for category in report.categories:
            print(f"    {category.category_name}: {len(category.tests)} tests, " +
                  f"{sum(1 for t in category.tests if t.passed)} passed")
    
    # Overall summary
    print("\n" + "-" * 80)
    print("OVERALL SUMMARY:")
    print(f"  Total Components Tested: {len(reports)}")
    print(f"  Total Tests Run: {total_tests}")
    print(f"  Total Tests Passed: {total_passed}")
    print(f"  Total Tests Failed: {total_tests - total_passed}")
    print(f"  Overall Pass Rate: {(total_passed/total_tests*100):.1f}%")
    
    # Save summary report
    summary_file = Path("tests/results/test_summary.json")
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'components_tested': len(reports),
        'total_tests': total_tests,
        'tests_passed': total_passed,
        'tests_failed': total_tests - total_passed,
        'pass_rate': total_passed / total_tests if total_tests > 0 else 0,
        'components': [
            {
                'name': report.component_name,
                'passed': report.passed,
                'total_tests': report.total_tests,
                'passed_tests': report.passed_tests
            }
            for report in reports
        ]
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {summary_file}")
    
    # Return exit code based on results
    if total_passed < total_tests:
        return 1
    return 0


if __name__ == '__main__':
    # Set up Qt application if needed
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Run tests
    exit_code = run_tests()
    sys.exit(exit_code)