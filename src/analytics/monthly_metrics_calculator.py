"""
Monthly metrics calculator for health data analysis.
Provides advanced monthly statistics with dual mode support (calendar/rolling),
year-over-year comparisons, compound growth rates, and distribution analysis.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from collections import defaultdict
import logging
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import calendar
from functools import lru_cache, cached_property
import warnings

from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics


logger = logging.getLogger(__name__)


class MonthMode:
    """Month calculation modes."""
    CALENDAR = "calendar"  # Calendar months (Jan 1-31, Feb 1-28/29, etc.)
    ROLLING = "rolling"    # 30-day rolling windows


@dataclass
class DistributionStats:
    """Container for distribution analysis results."""
    skewness: float
    kurtosis: float
    normality_p_value: float
    is_normal: bool
    jarque_bera_stat: float
    jarque_bera_p_value: float
    
    def __post_init__(self):
        """Validate distribution statistics."""
        self.is_normal = self.normality_p_value > 0.05  # 5% significance level


@dataclass 
class MonthlyComparison:
    """Container for year-over-year monthly comparison results."""
    current_month_avg: float
    previous_year_avg: float
    percent_change: float
    absolute_change: float
    current_month_days: int
    previous_year_days: int
    years_compared: int
    is_significant: bool


@dataclass
class GrowthRateInfo:
    """Container for compound growth rate analysis."""
    monthly_growth_rate: float
    annualized_growth_rate: float
    periods_analyzed: int
    confidence_interval: Tuple[float, float]
    r_squared: float
    is_significant: bool


@dataclass
class MonthlyMetrics:
    """Container for comprehensive monthly metrics."""
    month_start: datetime
    mode: str  # 'calendar' or 'rolling'
    avg: float
    median: float
    std: float
    min: float
    max: float
    count: int
    growth_rate: Optional[float] = None
    distribution_stats: Optional[DistributionStats] = None
    comparison_data: Optional[MonthlyComparison] = None


class MonthlyMetricsCalculator:
    """
    Calculator for monthly health metrics with advanced analytics.
    
    Supports both calendar and rolling 30-day calculations, year-over-year
    comparisons, compound growth rates, and distribution analysis with 
    performance optimizations for large datasets.
    """
    
    def __init__(self, 
                 daily_calculator: DailyMetricsCalculator,
                 mode: str = MonthMode.CALENDAR,
                 use_parallel: bool = True,
                 cache_size: int = 100):
        """
        Initialize the monthly calculator.
        
        Args:
            daily_calculator: Instance of DailyMetricsCalculator for base calculations
            mode: Calculation mode (calendar or rolling)
            use_parallel: Whether to use parallel processing for multiple metrics
            cache_size: Size of LRU cache for expensive calculations
        """
        self.daily_calculator = daily_calculator
        self.mode = mode
        self.use_parallel = use_parallel
        self._max_workers = multiprocessing.cpu_count() - 1
        self._cache_size = cache_size
        
        # Initialize caches
        self._monthly_cache = {}
        self._growth_cache = {}
        self._distribution_cache = {}
        
    @lru_cache(maxsize=100)
    def calculate_monthly_stats(self, 
                              metric: str, 
                              year: int, 
                              month: int) -> MonthlyMetrics:
        """
        Calculate comprehensive statistics for a specific month.
        
        Args:
            metric: The metric type to analyze
            year: Year of the month
            month: Month number (1-12)
            
        Returns:
            MonthlyMetrics object with calculated values
        """
        # Get month boundaries
        start_date, end_date = self._get_month_boundaries(year, month)
        
        # Get daily aggregates from daily calculator
        daily_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', start_date, end_date
        )
        
        if daily_data.empty:
            return MonthlyMetrics(
                month_start=datetime.combine(start_date, datetime.min.time()),
                mode=self.mode,
                avg=0.0,
                median=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                count=0
            )
        
        # Handle missing days for calendar mode
        if self.mode == MonthMode.CALENDAR:
            daily_data = self._fill_missing_days(daily_data, start_date, end_date)
        
        # Calculate basic statistics
        values = daily_data.values
        valid_values = values[~np.isnan(values)]
        
        if len(valid_values) == 0:
            return MonthlyMetrics(
                month_start=datetime.combine(start_date, datetime.min.time()),
                mode=self.mode,
                avg=0.0,
                median=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                count=0
            )
        
        # Calculate distribution statistics if enough data
        distribution_stats = None
        if len(valid_values) >= 8:  # Minimum for meaningful distribution analysis
            try:
                distribution_stats = self._calculate_distribution_stats(valid_values)
            except Exception as e:
                logger.warning(f"Could not calculate distribution stats for {metric} {year}-{month}: {e}")
        
        return MonthlyMetrics(
            month_start=datetime.combine(start_date, datetime.min.time()),
            mode=self.mode,
            avg=float(np.mean(valid_values)),
            median=float(np.median(valid_values)),
            std=float(np.std(valid_values, ddof=1)) if len(valid_values) > 1 else 0.0,
            min=float(np.min(valid_values)),
            max=float(np.max(valid_values)),
            count=len(valid_values),
            distribution_stats=distribution_stats
        )
    
    def compare_year_over_year(self, 
                             metric: str, 
                             month: int,
                             target_year: int,
                             years_back: int = 1) -> MonthlyComparison:
        """
        Compare same month across multiple years.
        
        Args:
            metric: The metric type to analyze
            month: Month number (1-12) to compare
            target_year: Target year for comparison
            years_back: Number of years to look back (default: 1)
            
        Returns:
            MonthlyComparison object with comparison results
        """
        # Get current year data
        current_metrics = self.calculate_monthly_stats(metric, target_year, month)
        
        # Collect data from previous years
        previous_years_data = []
        valid_years = 0
        
        for year_offset in range(1, years_back + 1):
            compare_year = target_year - year_offset
            try:
                prev_metrics = self.calculate_monthly_stats(metric, compare_year, month)
                if prev_metrics.count > 0:
                    previous_years_data.append(prev_metrics.avg)
                    valid_years += 1
            except Exception as e:
                logger.warning(f"Could not get data for {metric} {compare_year}-{month}: {e}")
        
        if not previous_years_data:
            return MonthlyComparison(
                current_month_avg=current_metrics.avg,
                previous_year_avg=0.0,
                percent_change=0.0,
                absolute_change=0.0,
                current_month_days=current_metrics.count,
                previous_year_days=0,
                years_compared=0,
                is_significant=False
            )
        
        # Calculate average of previous years
        prev_avg = float(np.mean(previous_years_data))
        
        # Calculate changes
        if prev_avg != 0:
            percent_change = ((current_metrics.avg - prev_avg) / prev_avg) * 100
        else:
            percent_change = 0 if current_metrics.avg == 0 else float('inf')
        
        absolute_change = current_metrics.avg - prev_avg
        
        # Statistical significance test (if we have enough data)
        is_significant = False
        if len(previous_years_data) >= 3 and current_metrics.count >= 7:
            try:
                # One-sample t-test against historical average
                t_stat, p_value = stats.ttest_1samp([current_metrics.avg], prev_avg)
                is_significant = p_value < 0.05
            except Exception:
                is_significant = False
        
        return MonthlyComparison(
            current_month_avg=current_metrics.avg,
            previous_year_avg=prev_avg,
            percent_change=float(percent_change),
            absolute_change=float(absolute_change),
            current_month_days=current_metrics.count,
            previous_year_days=int(np.mean([len(str(y)) for y in previous_years_data])),  # Placeholder
            years_compared=valid_years,
            is_significant=is_significant
        )
    
    def calculate_growth_rate(self, 
                            metric: str, 
                            periods: int,
                            end_year: int,
                            end_month: int) -> GrowthRateInfo:
        """
        Calculate compound monthly growth rate.
        
        Args:
            metric: The metric type to analyze
            periods: Number of months to analyze
            end_year: End year for analysis
            end_month: End month for analysis
            
        Returns:
            GrowthRateInfo object with growth analysis
        """
        # Generate list of (year, month) tuples going backwards
        month_periods = []
        current_year, current_month = end_year, end_month
        
        for _ in range(periods):
            month_periods.append((current_year, current_month))
            # Go back one month
            current_month -= 1
            if current_month == 0:
                current_month = 12
                current_year -= 1
        
        month_periods.reverse()  # Chronological order
        
        # Get monthly data
        monthly_values = []
        valid_periods = []
        
        for year, month in month_periods:
            try:
                metrics = self.calculate_monthly_stats(metric, year, month)
                if metrics.count > 0 and metrics.avg > 0:  # Only positive values for growth calc
                    monthly_values.append(metrics.avg)
                    valid_periods.append((year, month))
            except Exception as e:
                logger.warning(f"Could not get data for {metric} {year}-{month}: {e}")
        
        if len(monthly_values) < 2:
            return GrowthRateInfo(
                monthly_growth_rate=0.0,
                annualized_growth_rate=0.0,
                periods_analyzed=len(monthly_values),
                confidence_interval=(0.0, 0.0),
                r_squared=0.0,
                is_significant=False
            )
        
        # Calculate compound monthly growth rate
        # CMGR = (V_final / V_initial)^(1/n) - 1
        final_value = monthly_values[-1]
        initial_value = monthly_values[0]
        n_periods = len(monthly_values) - 1
        
        if initial_value <= 0:
            monthly_growth_rate = 0.0
        else:
            monthly_growth_rate = (final_value / initial_value) ** (1 / n_periods) - 1
        
        # Annualized growth rate
        annualized_growth_rate = (1 + monthly_growth_rate) ** 12 - 1
        
        # Regression analysis for confidence
        x_values = np.arange(len(monthly_values))
        log_values = np.log(monthly_values)  # Log-linear regression
        
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, log_values)
            
            # Calculate confidence interval (95%)
            alpha = 0.05
            t_val = stats.t.ppf(1 - alpha/2, len(monthly_values) - 2)
            margin_error = t_val * std_err
            
            lower_bound = slope - margin_error
            upper_bound = slope + margin_error
            
            # Convert back from log scale
            confidence_interval = (
                float(np.exp(lower_bound) - 1),
                float(np.exp(upper_bound) - 1)
            )
            
            r_squared = float(r_value ** 2)
            is_significant = p_value < 0.05
            
        except Exception as e:
            logger.warning(f"Could not calculate confidence interval: {e}")
            confidence_interval = (monthly_growth_rate, monthly_growth_rate)
            r_squared = 0.0
            is_significant = False
        
        return GrowthRateInfo(
            monthly_growth_rate=float(monthly_growth_rate),
            annualized_growth_rate=float(annualized_growth_rate),
            periods_analyzed=len(monthly_values),
            confidence_interval=confidence_interval,
            r_squared=r_squared,
            is_significant=is_significant
        )
    
    def analyze_distribution(self, 
                           metric: str, 
                           year: int, 
                           month: int) -> DistributionStats:
        """
        Analyze distribution characteristics for monthly data.
        
        Args:
            metric: The metric type to analyze
            year: Year of the month
            month: Month number (1-12)
            
        Returns:
            DistributionStats object with distribution analysis
        """
        # Use cached result if available
        cache_key = f"{metric}_{year}_{month}_dist"
        if cache_key in self._distribution_cache:
            return self._distribution_cache[cache_key]
        
        # Get monthly data
        monthly_metrics = self.calculate_monthly_stats(metric, year, month)
        
        if monthly_metrics.count < 8:  # Minimum sample size for meaningful analysis
            raise ValueError(f"Insufficient data for distribution analysis: {monthly_metrics.count} days")
        
        # Get raw daily values
        start_date, end_date = self._get_month_boundaries(year, month)
        daily_data = self.daily_calculator.calculate_daily_aggregates(
            metric, 'mean', start_date, end_date
        )
        
        if daily_data.empty:
            raise ValueError("No data available for distribution analysis")
        
        values = daily_data.values
        valid_values = values[~np.isnan(values)]
        
        # Calculate distribution statistics
        distribution_stats = self._calculate_distribution_stats(valid_values)
        
        # Cache result
        self._distribution_cache[cache_key] = distribution_stats
        
        return distribution_stats
    
    def _calculate_distribution_stats(self, values: np.ndarray) -> DistributionStats:
        """Calculate distribution statistics for a set of values."""
        # Calculate skewness and kurtosis
        skewness = float(stats.skew(values))
        kurtosis = float(stats.kurtosis(values))  # Excess kurtosis (normal = 0)
        
        # Normality tests
        try:
            # Shapiro-Wilk test (good for small samples)
            if len(values) <= 5000:
                _, normality_p_value = stats.shapiro(values)
            else:
                # Use Kolmogorov-Smirnov for larger samples
                _, normality_p_value = stats.kstest(values, 'norm',
                                                  args=(np.mean(values), np.std(values)))
        except Exception:
            normality_p_value = 0.0
        
        # Jarque-Bera test for normality
        try:
            jarque_bera_stat, jarque_bera_p_value = stats.jarque_bera(values)
        except Exception:
            jarque_bera_stat = 0.0
            jarque_bera_p_value = 0.0
        
        return DistributionStats(
            skewness=skewness,
            kurtosis=kurtosis,
            normality_p_value=float(normality_p_value),
            is_normal=normality_p_value > 0.05,
            jarque_bera_stat=float(jarque_bera_stat),
            jarque_bera_p_value=float(jarque_bera_p_value)
        )
    
    def _get_month_boundaries(self, year: int, month: int) -> Tuple[date, date]:
        """Get start and end dates for a month based on calculation mode."""
        if self.mode == MonthMode.CALENDAR:
            # Calendar month boundaries
            start_date = date(year, month, 1)
            # Get last day of month
            _, last_day = calendar.monthrange(year, month)
            end_date = date(year, month, last_day)
        else:
            # Rolling 30-day window ending on the 15th of specified month
            mid_month = date(year, month, 15)
            start_date = mid_month - timedelta(days=29)  # 30 days total
            end_date = mid_month
        
        return start_date, end_date
    
    def _fill_missing_days(self, 
                          daily_data: pd.Series, 
                          start_date: date, 
                          end_date: date) -> pd.Series:
        """Fill missing days in daily data series."""
        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Convert to date index if needed
        if isinstance(daily_data.index[0], date):
            complete_series = daily_data.reindex(date_range.date)
        else:
            complete_series = daily_data.reindex(date_range)
        
        # Fill missing values with NaN (will be handled in calculations)
        return complete_series
    
    @cached_property
    def monthly_aggregates(self) -> Dict[str, Any]:
        """Lazy-loaded monthly aggregates for all available data."""
        # This would be implemented for large dataset optimization
        # For now, return empty dict as placeholder
        return {}
    
    def calculate_multiple_months_parallel(self,
                                         metrics: List[str],
                                         year_month_pairs: List[Tuple[int, int]]) -> Dict[str, Dict[Tuple[int, int], MonthlyMetrics]]:
        """
        Calculate monthly statistics for multiple metrics and months in parallel.
        
        Args:
            metrics: List of metric types to analyze
            year_month_pairs: List of (year, month) tuples
            
        Returns:
            Dictionary mapping metric names to monthly results
        """
        if not self.use_parallel or len(metrics) * len(year_month_pairs) < 6:
            # Use sequential processing for small workloads
            results = {}
            for metric in metrics:
                results[metric] = {}
                for year, month in year_month_pairs:
                    try:
                        results[metric][(year, month)] = self.calculate_monthly_stats(
                            metric, year, month
                        )
                    except Exception as e:
                        logger.error(f"Error processing {metric} {year}-{month}: {e}")
                        results[metric][(year, month)] = MonthlyMetrics(
                            month_start=datetime(year, month, 1),
                            mode=self.mode,
                            avg=0.0,
                            median=0.0,
                            std=0.0,
                            min=0.0,
                            max=0.0,
                            count=0
                        )
            return results
        
        # Use parallel processing
        results = defaultdict(dict)
        
        # Create tasks for all combinations
        tasks = []
        for metric in metrics:
            for year, month in year_month_pairs:
                tasks.append((metric, year, month))
        
        with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit tasks
            future_to_task = {
                executor.submit(self.calculate_monthly_stats, metric, year, month): (metric, year, month)
                for metric, year, month in tasks
            }
            
            # Collect results
            for future in as_completed(future_to_task):
                metric, year, month = future_to_task[future]
                try:
                    results[metric][(year, month)] = future.result()
                except Exception as e:
                    logger.error(f"Error processing {metric} {year}-{month}: {e}")
                    results[metric][(year, month)] = MonthlyMetrics(
                        month_start=datetime(year, month, 1),
                        mode=self.mode,
                        avg=0.0,
                        median=0.0,
                        std=0.0,
                        min=0.0,
                        max=0.0,
                        count=0
                    )
        
        return dict(results)
    
    def get_monthly_summary(self,
                          metrics: List[str],
                          year: int,
                          month: int) -> Dict[str, Dict[str, Union[float, bool]]]:
        """
        Get comprehensive monthly summary for multiple metrics.
        
        Args:
            metrics: List of metric types
            year: Year
            month: Month number (1-12)
            
        Returns:
            Dictionary with summary statistics for each metric
        """
        results = {}
        
        for metric in metrics:
            try:
                # Get basic monthly statistics
                monthly_metrics = self.calculate_monthly_stats(metric, year, month)
                
                # Get year-over-year comparison
                yoy_comparison = self.compare_year_over_year(metric, month, year)
                
                # Get growth rate (6 months)
                try:
                    growth_info = self.calculate_growth_rate(metric, 6, year, month)
                    growth_rate = growth_info.monthly_growth_rate
                    growth_significant = growth_info.is_significant
                except Exception:
                    growth_rate = 0.0
                    growth_significant = False
                
                # Combine results
                results[metric] = {
                    'avg': monthly_metrics.avg,
                    'median': monthly_metrics.median,
                    'std': monthly_metrics.std,
                    'min': monthly_metrics.min,
                    'max': monthly_metrics.max,
                    'count': monthly_metrics.count,
                    'yoy_percent_change': yoy_comparison.percent_change,
                    'yoy_significant': yoy_comparison.is_significant,
                    'monthly_growth_rate': growth_rate,
                    'growth_significant': growth_significant,
                    'mode': self.mode
                }
                
                # Add distribution stats if available
                if monthly_metrics.distribution_stats:
                    results[metric].update({
                        'skewness': monthly_metrics.distribution_stats.skewness,
                        'kurtosis': monthly_metrics.distribution_stats.kurtosis,
                        'is_normal': monthly_metrics.distribution_stats.is_normal
                    })
                
            except Exception as e:
                logger.error(f"Error calculating monthly summary for {metric}: {e}")
                results[metric] = {}
        
        return results