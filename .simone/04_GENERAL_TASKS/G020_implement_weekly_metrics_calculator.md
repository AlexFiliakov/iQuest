---
task_id: G020
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G020: Implement Weekly Metrics Calculator

## Description
Create `WeeklyMetricsCalculator` class to implement 7-day rolling statistics with configurable windows. Include advanced analytics like week-to-date comparisons, moving averages, trend detection, and volatility scores.

## Goals
- [ ] Create `WeeklyMetricsCalculator` class
- [ ] Implement 7-day rolling statistics with configurable windows
- [ ] Add week-to-date vs same period last week comparison
- [ ] Implement moving averages (7, 14, 28 days)
- [ ] Add trend detection using linear regression
- [ ] Calculate volatility/consistency scores
- [ ] Optimize performance with sliding window calculations

## Acceptance Criteria
- [ ] Calculator supports configurable rolling windows
- [ ] Correctly handles partial weeks at month boundaries
- [ ] Supports both ISO and US week numbering standards
- [ ] Handles 53-week years correctly
- [ ] Uses sliding window with deque for performance
- [ ] Supports incremental updates for real-time data
- [ ] Parallel processing for multiple metrics
- [ ] Unit tests cover various date ranges and edge cases

## Technical Details

### Advanced Analytics
- **Week-to-Date Comparisons**: Compare current week progress to same period last week
- **Moving Averages**: Support 7, 14, and 28-day windows
- **Trend Detection**: Use linear regression for trend analysis
- **Volatility Scores**: Calculate consistency/variability metrics

### Performance Optimizations
- Sliding window calculations using collections.deque
- Incremental updates for real-time data streams
- Parallel processing for multiple metrics using multiprocessing
- Efficient memory usage for large datasets

### Edge Cases
- **Partial Weeks**: Handle weeks at month/year boundaries
- **Week Numbering**: Support both ISO 8601 and US standards
- **53-Week Years**: Correctly handle years with 53 weeks
- **Missing Data**: Configurable handling (skip, interpolate, or fail)

## Dependencies
- G019 (Daily Metrics Calculator) for base calculations
- NumPy for numerical operations
- SciPy for linear regression
- Multiprocessing for parallel computation

## Implementation Notes
```python
# Example structure
class WeeklyMetricsCalculator:
    def __init__(self, daily_calculator: DailyMetricsCalculator):
        self.daily_calculator = daily_calculator
        self.window_cache = {}
        
    def calculate_rolling_stats(self, metric: str, window: int = 7) -> pd.DataFrame:
        """Calculate rolling statistics with configurable window"""
        pass
        
    def compare_week_to_date(self, metric: str, current_week: int, year: int) -> Dict:
        """Compare current week-to-date with previous week"""
        pass
        
    def detect_trend(self, metric: str, window: int = 7) -> TrendInfo:
        """Detect trend using linear regression"""
        pass
        
    def calculate_volatility(self, metric: str, window: int = 7) -> float:
        """Calculate volatility/consistency score"""
        pass
```

## Testing Requirements
- Unit tests for all calculation methods
- Edge case testing (partial weeks, year boundaries)
- Performance tests with large datasets
- Integration tests with daily calculator
- Parallel processing correctness tests

## Notes
- Coordinate with daily calculator for consistent interfaces
- Consider caching strategies for frequently accessed windows
- Document week numbering standard clearly
- Provide configuration options for business rules