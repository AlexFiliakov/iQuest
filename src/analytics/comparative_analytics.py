"""
Comparative Analytics Engine for Apple Health Monitor.

This module provides privacy-first comparative analytics including:
- Personal historical comparisons
- Demographic comparisons (opt-in)
- Seasonal/weather norm comparisons
- Peer group comparisons (anonymous)

All comparisons are designed with privacy and encouragement in mind.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
import secrets
from functools import lru_cache
import re

from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator

logger = logging.getLogger(__name__)

# Constants
MIN_COHORT_SIZE = 50  # K-anonymity threshold
DEFAULT_PRIVACY_EPSILON = 1.0  # Differential privacy
TREND_IMPROVEMENT_THRESHOLD = 1.05
TREND_DECLINE_THRESHOLD = 0.95
CACHE_SIZE = 128  # LRU cache size
VALID_METRICS = {'steps', 'distance', 'calories', 'heart_rate', 'sleep_hours'}
MAX_AGE = 120
MIN_AGE = 13




class ComparisonType(Enum):
    """Types of comparisons available."""
    PERSONAL_HISTORICAL = "personal_historical"
    DEMOGRAPHIC = "demographic"
    SEASONAL = "seasonal"
    PEER_GROUP = "peer_group"


class PrivacyLevel(Enum):
    """Privacy levels for data sharing."""
    LOCAL_ONLY = "local_only"
    ANONYMOUS_AGGREGATE = "anonymous_aggregate"
    PEER_GROUP = "peer_group"
    PUBLIC = "public"


@dataclass
class ComparisonResult:
    """Result of a comparison analysis."""
    comparison_type: ComparisonType
    current_value: float
    comparison_value: float
    percentile: Optional[float] = None
    context: Optional[str] = None
    insights: List[str] = None
    visualization_data: Optional[Dict] = None
    privacy_level: PrivacyLevel = PrivacyLevel.LOCAL_ONLY
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


@dataclass
class HistoricalComparison:
    """Historical comparison data."""
    rolling_7_day: Optional[MetricStatistics] = None
    rolling_30_day: Optional[MetricStatistics] = None
    rolling_90_day: Optional[MetricStatistics] = None
    rolling_365_day: Optional[MetricStatistics] = None
    same_period_last_year: Optional[MetricStatistics] = None
    personal_best: Optional[Tuple[datetime, float]] = None
    personal_average: Optional[float] = None
    trend_direction: Optional[str] = None  # "improving", "stable", "declining"


@dataclass
class DemographicCohort:
    """Demographic cohort information."""
    age_range: Tuple[int, int]
    gender: Optional[str]
    activity_level: Optional[str]
    cohort_size: int
    stats: MetricStatistics
    last_updated: datetime
    
    @property
    def is_valid_for_comparison(self) -> bool:
        """Check if cohort has enough members for privacy."""
        return self.cohort_size >= 50  # K-anonymity threshold


@dataclass
class SeasonalNorm:
    """Seasonal norm data."""
    month: int
    average: float
    std_dev: float
    percentile_25: float
    percentile_75: float
    typical_range: Tuple[float, float]
    weather_adjusted: Optional[float] = None


@dataclass
class PeerGroupStats:
    """Anonymous peer group statistics."""
    group_id: str
    member_count: int
    group_average: float
    group_median: float
    percentile_25: float
    percentile_75: float
    anonymous_ranking: Optional[str] = None  # "top quarter", "middle half", etc.


class PrivacyManager:
    """Manages privacy settings and permissions."""
    
    def __init__(self):
        self.permissions = {}
        self.minimum_cohort_size = MIN_COHORT_SIZE
        self.differential_privacy_epsilon = DEFAULT_PRIVACY_EPSILON
        
    def has_permission(self, permission_type: str) -> bool:
        """Check if user has granted specific permission."""
        return self.permissions.get(permission_type, {}).get('granted', False)
        
    def request_permission(self, permission_type: str, explanation: str) -> bool:
        """Request permission from user (placeholder for UI integration)."""
        # In real implementation, this would show a dialog
        logger.info(f"Permission requested: {permission_type}")
        return False  # Default to no permission
        
    def anonymize_value(self, value: float, method: str = 'rounding') -> float:
        """Anonymize a value for privacy."""
        try:
            if method == 'rounding':
                # Round to reduce precision
                return round(value, -1)  # Round to nearest 10
            elif method == 'differential_privacy':
                # Add Laplace noise using cryptographically secure randomness
                sensitivity = 1.0
                scale = sensitivity / self.differential_privacy_epsilon
                # Use secrets module for cryptographically secure random values
                random_bytes = secrets.randbits(64)
                u = (random_bytes / (1 << 64)) - 0.5  # Uniform random in [-0.5, 0.5]
                noise = -scale * np.sign(u) * np.log(1 - 2 * abs(u))
                return value + noise
            return value
        except Exception as e:
            logger.error(f"Error in anonymize_value: {e}")
            return value


class ComparativeAnalyticsEngine:
    """Main engine for comparative analytics."""
    
    def __init__(self, 
                 daily_calculator: DailyMetricsCalculator,
                 weekly_calculator: WeeklyMetricsCalculator,
                 monthly_calculator: MonthlyMetricsCalculator,
                 privacy_manager: Optional[PrivacyManager] = None,
                 background_processor=None):
        self.daily_calc = daily_calculator
        self.weekly_calc = weekly_calculator
        self.monthly_calc = monthly_calculator
        self.privacy_manager = privacy_manager or PrivacyManager()
        self.insights_generator = InsightsGenerator()
        self.background_processor = background_processor
        
    def get_trend_analysis(self, metric: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get trend analysis for a metric, using cache if available.
        
        Args:
            metric: The metric to analyze
            use_cache: Whether to use cached results
            
        Returns:
            Trend analysis results or None
        """
        if not self.background_processor:
            # Fall back to synchronous calculation
            logger.warning("No background processor available, performing synchronous trend calculation")
            return None
            
        if use_cache:
            # Try to get from cache first
            trend_result = self.background_processor.get_trend(metric, wait=False)
            if trend_result:
                return trend_result
                
        # Queue for background calculation
        self.background_processor.queue_trend_calculation(metric, priority=5)
        
        # Return None to indicate processing
        return None
        
    def _validate_metric_name(self, metric: str) -> bool:
        """Validate metric name for security and correctness."""
        if not metric or not isinstance(metric, str):
            return False
        # Check against valid metrics or use pattern matching
        if metric in VALID_METRICS:
            return True
        # Allow custom metrics with safe pattern
        safe_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{0,49}$')
        return bool(safe_pattern.match(metric))
        
    def _validate_age(self, age: int) -> bool:
        """Validate age is within reasonable bounds."""
        return isinstance(age, int) and MIN_AGE <= age <= MAX_AGE
        
    @lru_cache(maxsize=CACHE_SIZE)
    def compare_to_historical(self, 
                            metric: str, 
                            current_date: datetime,
                            lookback_days: int = 365) -> HistoricalComparison:
        """Compare current metrics to personal historical data."""
        try:
            # Validate inputs
            if not self._validate_metric_name(metric):
                raise ValueError(f"Invalid metric name: {metric}")
            if lookback_days < 1 or lookback_days > 3650:
                raise ValueError(f"Lookback days must be between 1 and 3650, got {lookback_days}")
            
            logger.info(f"Generating historical comparison for {metric}")
        
            # Get current value
            current_stats = self.daily_calc.calculate_statistics(
                metric, 
                current_date - timedelta(days=1), 
                current_date
            )
            
            if not current_stats or current_stats.count == 0:
                logger.warning(f"No current data for {metric}")
                return HistoricalComparison()
                
            current_value = current_stats.mean
        
            # Calculate rolling averages
            historical = HistoricalComparison()
            
            # 7-day rolling
            historical.rolling_7_day = self.daily_calc.calculate_statistics(
                metric,
                current_date - timedelta(days=7),
                current_date
            )
            
            # 30-day rolling
            historical.rolling_30_day = self.daily_calc.calculate_statistics(
                metric,
                current_date - timedelta(days=30),
                current_date
            )
            
            # 90-day rolling
            historical.rolling_90_day = self.daily_calc.calculate_statistics(
                metric,
                current_date - timedelta(days=90),
                current_date
            )
            
            # 365-day rolling
            historical.rolling_365_day = self.daily_calc.calculate_statistics(
                metric,
                current_date - timedelta(days=365),
                current_date
            )
            
            # Same period last year
            last_year_start = current_date - timedelta(days=365)
            last_year_end = last_year_start + timedelta(days=30)
            historical.same_period_last_year = self.daily_calc.calculate_statistics(
                metric,
                last_year_start,
                last_year_end
            )
            
            # Personal best (simplified - would need full data scan)
            if historical.rolling_365_day:
                historical.personal_best = (current_date, historical.rolling_365_day.max)
                historical.personal_average = historical.rolling_365_day.mean
                
            # Determine trend
            if historical.rolling_30_day and historical.rolling_90_day:
                if historical.rolling_30_day.mean > historical.rolling_90_day.mean * TREND_IMPROVEMENT_THRESHOLD:
                    historical.trend_direction = "improving"
                elif historical.rolling_30_day.mean < historical.rolling_90_day.mean * TREND_DECLINE_THRESHOLD:
                    historical.trend_direction = "declining"
                else:
                    historical.trend_direction = "stable"
                    
            return historical
        except Exception as e:
            logger.error(f"Error in compare_to_historical: {e}")
            return HistoricalComparison()
        
    def compare_to_demographic(self,
                             metric: str,
                             age: int,
                             gender: Optional[str] = None,
                             activity_level: Optional[str] = None) -> Optional[ComparisonResult]:
        """Compare to demographic cohort if permitted."""
        try:
            # Validate inputs
            if not self._validate_metric_name(metric):
                raise ValueError(f"Invalid metric name: {metric}")
            if not self._validate_age(age):
                raise ValueError(f"Invalid age: {age}")
            if gender and gender not in ['male', 'female', 'other', None]:
                raise ValueError(f"Invalid gender: {gender}")
            if activity_level and activity_level not in ['sedentary', 'lightly_active', 'moderately_active', 'very_active', None]:
                raise ValueError(f"Invalid activity level: {activity_level}")
                
            if not self.privacy_manager.has_permission('demographic_comparison'):
                logger.info("No permission for demographic comparison")
                return None
                
            # In real implementation, this would query a demographic database
            # For now, return a mock result
            cohort = self._get_demographic_cohort(metric, age, gender, activity_level)
            
            if not cohort.is_valid_for_comparison:
                return ComparisonResult(
                    comparison_type=ComparisonType.DEMOGRAPHIC,
                    current_value=0,
                    comparison_value=0,
                    context="Insufficient data for comparison",
                    privacy_level=PrivacyLevel.LOCAL_ONLY
                )
                
            # Calculate percentile (mock)
            percentile = self._calculate_percentile_in_cohort(metric, cohort)
            
            return ComparisonResult(
                comparison_type=ComparisonType.DEMOGRAPHIC,
                current_value=0,  # Would get from current data
                comparison_value=cohort.stats.mean,
                percentile=percentile,
                context=f"Compared to {cohort.cohort_size} similar individuals",
                insights=self.insights_generator.generate_demographic_insights(percentile),
                privacy_level=PrivacyLevel.ANONYMOUS_AGGREGATE
            )
        except Exception as e:
            logger.error(f"Error in compare_to_demographic: {e}")
            return None
        
    def compare_to_seasonal(self,
                          metric: str,
                          current_date: datetime,
                          location: Optional[str] = None) -> Optional[ComparisonResult]:
        """Compare to seasonal norms."""
        try:
            # Validate inputs
            if not self._validate_metric_name(metric):
                raise ValueError(f"Invalid metric name: {metric}")
            if not isinstance(current_date, datetime):
                raise ValueError("current_date must be a datetime object")
                
            month = current_date.month
            
            # Get seasonal baseline (mock for now)
            seasonal_norm = self._get_seasonal_norm(metric, month, location)
            
            if not seasonal_norm:
                return None
                
            # Get current value
            current_stats = self.daily_calc.calculate_statistics(
                metric,
                current_date - timedelta(days=30),
                current_date
            )
            
            if not current_stats:
                return None
                
            return ComparisonResult(
                comparison_type=ComparisonType.SEASONAL,
                current_value=current_stats.mean,
                comparison_value=seasonal_norm.average,
                context=f"Typical for {current_date.strftime('%B')}",
                insights=self.insights_generator.generate_seasonal_insights(
                    current_stats.mean, seasonal_norm
                ),
                privacy_level=PrivacyLevel.LOCAL_ONLY
            )
        except Exception as e:
            logger.error(f"Error in compare_to_seasonal: {e}")
            return None
        
    def _get_demographic_cohort(self, metric: str, age: int, gender: Optional[str], 
                               activity_level: Optional[str]) -> DemographicCohort:
        """Get demographic cohort (mock implementation)."""
        age_range = ((age // 5) * 5, (age // 5) * 5 + 4)
        
        # Mock statistics
        mock_stats = MetricStatistics(
            metric_name=metric,  # Add required metric_name parameter
            count=100,
            mean=8000,  # Mock average steps
            median=7500,
            std=2000,
            min=3000,
            max=15000,
            percentile_25=6000,
            percentile_75=10000,
            percentile_95=12000,  # Add percentile_95
            missing_data_count=0,
            outlier_count=5
        )
        
        return DemographicCohort(
            age_range=age_range,
            gender=gender,
            activity_level=activity_level,
            cohort_size=150,
            stats=mock_stats,
            last_updated=datetime.now()
        )
        
    def _calculate_percentile_in_cohort(self, metric: str, 
                                       cohort: DemographicCohort) -> float:
        """Calculate percentile within cohort (mock)."""
        # In real implementation, would calculate based on actual distribution
        # Use secrets module for secure random generation
        return 25 + (secrets.randbits(16) / 65536) * 50  # Mock percentile between 25-75
        
    def _get_seasonal_norm(self, metric: str, month: int, 
                          location: Optional[str]) -> Optional[SeasonalNorm]:
        """Get seasonal norm (mock implementation)."""
        # Mock seasonal variations
        seasonal_factors = {
            1: 0.85,  # January - New Year's resolutions
            2: 0.80,  # February - Winter
            3: 0.90,  # March - Spring begins
            4: 1.00,  # April - Spring
            5: 1.10,  # May - Nice weather
            6: 1.15,  # June - Summer begins
            7: 1.20,  # July - Peak summer
            8: 1.15,  # August - Late summer
            9: 1.05,  # September - Fall begins
            10: 1.00, # October - Fall
            11: 0.90, # November - Holiday season begins
            12: 0.85  # December - Winter holidays
        }
        
        base_value = 8000  # Base steps
        factor = seasonal_factors.get(month, 1.0)
        
        return SeasonalNorm(
            month=month,
            average=base_value * factor,
            std_dev=2000,
            percentile_25=(base_value * factor) - 2000,
            percentile_75=(base_value * factor) + 2000,
            typical_range=((base_value * factor) - 3000, (base_value * factor) + 3000)
        )
    
    def _validate_metric_name(self, metric: str) -> bool:
        """Validate metric name for security."""
        if not metric or not isinstance(metric, str):
            return False
        # Allow alphanumeric, underscores, and common health metric separators
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', metric):
            return False
        if len(metric) > 100:  # Reasonable length limit
            return False
        return True
    
    def _validate_age(self, age: int) -> bool:
        """Validate age input."""
        if not isinstance(age, int):
            return False
        if age < 0 or age > 150:
            return False
        return True
    
    def _validate_date_range(self, start_date: datetime, end_date: datetime) -> bool:
        """Validate date range."""
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            return False
        if start_date > end_date:
            return False
        # Don't allow unreasonably large date ranges
        if (end_date - start_date).days > 3650:  # 10 years
            return False
        return True


class InsightsGenerator:
    """Generates constructive insights from comparisons."""
    
    def generate_demographic_insights(self, percentile: float) -> List[str]:
        """Generate encouraging demographic insights."""
        insights = []
        
        if percentile >= 75:
            insights.append("You're inspiring others with your activity! 🌟")
            insights.append("Your consistency puts you in the top quarter.")
        elif percentile >= 50:
            insights.append("You're on a great path! 💪")
            insights.append("You're right on track with your peers.")
        elif percentile >= 25:
            insights.append("Every step counts! 🚶")
            insights.append("You're building healthy habits.")
        else:
            insights.append("Your journey is unique! 🌱")
            insights.append("Small improvements lead to big changes.")
            
        return insights
        
    def generate_seasonal_insights(self, current: float, 
                                 seasonal: SeasonalNorm) -> List[str]:
        """Generate seasonal insights."""
        insights = []
        
        if current > seasonal.average:
            insights.append(f"You're above the typical {seasonal.month} average!")
        else:
            insights.append(f"Seasonal patterns affect everyone - you're doing great!")
            
        if seasonal.weather_adjusted:
            insights.append("Weather conditions have been factored into your comparison.")
            
        return insights
        
    def generate_historical_insights(self, historical: HistoricalComparison) -> List[str]:
        """Generate personal historical insights."""
        insights = []
        
        if historical.trend_direction == "improving":
            insights.append("Your recent trend shows improvement! 📈")
        elif historical.trend_direction == "stable":
            insights.append("You're maintaining consistency - that's great! 📊")
        else:
            insights.append("Every journey has ups and downs - keep going! 💪")
            
        if historical.personal_best:
            insights.append(f"Personal best: {historical.personal_best[1]:,.0f}")
            
        return insights