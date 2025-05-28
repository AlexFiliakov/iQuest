# Test Failure Analysis Summary

## Overview
Total test failures: **272**

## Major Categories of Failures

### 1. Missing Fixtures (20 errors)
- **visual_tester**: 16 occurrences
- **sample_data**: 4 occurrences
These fixtures are not defined in conftest.py or the test setup.

### 2. Constructor/Initialization Errors (75 errors)
- **CorrelationAnalyzer.__init__()**: Missing 'data' argument (20 occurrences)
- **WeeklyMetricsCalculator.__init__()**: Missing 'daily_calculator' argument (18 occurrences)
- **DailyMetricsCalculator.__init__()**: Missing 'data' argument (13 occurrences)
- **SummaryCard.__init__()**: Unexpected keyword argument 'title' (11 occurrences)
- **MonthlyMetricsCalculator.__init__()**: Missing 'daily_calculator' argument (4 occurrences)
- **MetricStatistics.__init__()**: Unexpected keyword argument 'missing_count' (4 occurrences)
- **InteractiveLegend.__init__()**: Unexpected keyword argument 'items' (4 occurrences)
- **ComparisonOverlayWidget.__init__()**: Missing required positional arguments (4 occurrences)

### 3. PyQt6 API Issues (17 errors)
- **QFont.setFallbackFamilies**: Method doesn't exist in PyQt6 (17 occurrences)
- **QEasingCurve.Linear**: Attribute doesn't exist (1 occurrence)

### 4. Method Name Changes (23 errors)
- **detect_anomalies** → **detect_health_anomalies** (9 occurrences)
- **calculate_correlation_matrix** → **calculate_correlations** (9 occurrences)
- **find_strong_correlations**: Method doesn't exist (4 occurrences)
- **calculate_lagged_correlations** → **calculate_lag_correlation** (1 occurrence)

### 5. Missing Methods/Attributes (8 errors)
- **ChartConfig.get_wsj_style**: Static method doesn't exist (4 occurrences)
- **test_granger_causality**: Method doesn't exist (3 occurrences)
- **detect_multiple_metrics**: Method doesn't exist (3 occurrences)

### 6. Database Issues (3 errors)
- **DatabaseManager.__new__()**: Incorrect number of arguments (3 occurrences)

## Test Files with Most Failures
1. test_analytics_optimized.py: 53 failures
2. test_consolidated_widgets.py: 20 failures
3. test_monthly_context_provider.py: 18 failures
4. test_chaos_scenarios.py: 18 failures
5. test_activity_timeline_component.py: 17 failures
6. test_visual_regression.py: 16 failures
7. test_personal_records_tracker.py: 16 failures
8. test_weekly_metrics_calculator.py: 13 failures

## Key Issues to Fix

### Priority 1: Constructor Signatures
The following classes need their constructors updated to match test expectations:
- CorrelationAnalyzer: Should accept 'data' parameter
- WeeklyMetricsCalculator: Should accept 'daily_calculator' parameter
- DailyMetricsCalculator: Should accept 'data' parameter
- SummaryCard: Should accept 'title' as keyword argument
- MetricStatistics: Should accept 'missing_count' as keyword argument

### Priority 2: Missing Fixtures
Add the following fixtures to conftest.py:
- visual_tester
- sample_data

### Priority 3: Method Renames
Update tests to use new method names:
- detect_anomalies → detect_health_anomalies
- calculate_correlation_matrix → calculate_correlations
- calculate_lagged_correlations → calculate_lag_correlation

### Priority 4: PyQt6 Compatibility
- Remove usage of QFont.setFallbackFamilies (not available in PyQt6)
- Update QEasingCurve.Linear to correct PyQt6 syntax

### Priority 5: Missing Methods
Either implement or remove tests for:
- ChartConfig.get_wsj_style
- find_strong_correlations
- test_granger_causality
- detect_multiple_metrics

## Recommendations

1. **Update Class Constructors**: Many classes have changed their initialization signatures. Tests need to be updated to match the current implementation.

2. **Fix Fixture Definitions**: Add missing fixtures to the test configuration.

3. **PyQt6 Migration**: Complete the migration from PyQt5 to PyQt6 by updating incompatible API calls.

4. **Method Consistency**: Ensure all method names in tests match the actual implementation.

5. **Remove Obsolete Tests**: Some tests may be for features that no longer exist and should be removed.