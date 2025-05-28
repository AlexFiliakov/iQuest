---
task_id: G021
status: open
created: 2025-01-27
complexity: high
sprint_ref: S03
---

# Task G021: Implement Monthly Metrics Calculator

## Description
Create `MonthlyMetricsCalculator` class with advanced calculations including running 30-day windows vs calendar months, year-over-year comparisons, compound monthly growth rates, and distribution analysis (skewness, kurtosis).

## Goals
- [ ] Create `MonthlyMetricsCalculator` class
- [ ] Support both 30-day rolling and calendar month calculations
- [ ] Implement year-over-year comparison logic
- [ ] Calculate compound monthly growth rates
- [ ] Add distribution analysis (skewness, kurtosis)
- [ ] Optimize for multi-year datasets with chunked processing
- [ ] Implement lazy evaluation for on-demand metrics

## Acceptance Criteria
- [ ] Calculator supports both rolling and calendar month modes
- [ ] Handles February variations (28/29 days) correctly
- [ ] Manages partial months at data boundaries
- [ ] Handles month transitions across timezones
- [ ] Accounts for leap seconds and DST transitions
- [ ] Uses chunked processing for multi-year data
- [ ] Implements lazy evaluation for memory efficiency
- [ ] Memory-mapped files for huge datasets
- [ ] Comprehensive unit tests with edge cases

## Technical Details

### Advanced Calculations
- **Dual Mode**: Support 30-day rolling windows AND calendar months
- **YoY Comparisons**: Same month comparison across years
- **Growth Rates**: Compound monthly growth rate calculations
- **Distribution Analysis**: 
  - Skewness (asymmetry of distribution)
  - Kurtosis (tail heaviness)
  - Normality tests

### Performance Features
- **Chunked Processing**: Process multi-year data in chunks
- **Lazy Evaluation**: Calculate metrics on-demand
- **Memory-Mapped Files**: Handle datasets larger than RAM
- **Caching**: Smart caching of expensive calculations

### Edge Cases
- **February**: Handle 28/29 day variations
- **Partial Months**: Beginning/end of dataset
- **Timezone Transitions**: Month boundaries across zones
- **Leap Seconds**: Rare but must be handled
- **DST Changes**: Affect month boundary calculations

## Dependencies
- G019 (Daily Metrics Calculator)
- G020 (Weekly Metrics Calculator)
- NumPy for numerical operations
- SciPy for distribution analysis
- Memory mapping libraries

## Implementation Notes
```python
# Example structure
class MonthlyMetricsCalculator:
    def __init__(self, mode: str = 'calendar'):  # 'calendar' or 'rolling'
        self.mode = mode
        self.cache = LRUCache(maxsize=100)
        
    def calculate_monthly_stats(self, metric: str, year: int, month: int) -> Dict:
        """Calculate statistics for a specific month"""
        pass
        
    def compare_year_over_year(self, metric: str, month: int) -> pd.DataFrame:
        """Compare same month across multiple years"""
        pass
        
    def calculate_growth_rate(self, metric: str, periods: int) -> float:
        """Calculate compound monthly growth rate"""
        pass
        
    def analyze_distribution(self, metric: str, year: int, month: int) -> DistributionStats:
        """Analyze distribution characteristics"""
        pass
        
    @lazy_property
    def monthly_aggregates(self) -> Dict:
        """Lazy-loaded monthly aggregates"""
        pass
```

## Performance Requirements
- Process 5 years of data in < 5 seconds
- Memory usage < 1GB for 10 years of data
- Support datasets up to 100GB with memory mapping
- Cache hit rate > 70% for repeated queries

## Testing Requirements
- Edge case tests for all month variations
- Timezone handling tests
- Large dataset performance tests
- Memory usage profiling
- Distribution analysis validation
- Growth rate calculation accuracy

## Notes
- Coordinate with daily/weekly calculators for consistency
- Consider providing both exact and approximate algorithms
- Document assumptions about month boundaries
- Provide clear configuration for business rules
- Consider future requirements for quarterly/yearly analysis