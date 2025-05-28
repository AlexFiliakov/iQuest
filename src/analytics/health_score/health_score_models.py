"""Data models for health score calculations."""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ScoringMethod(Enum):
    """Available scoring methods."""
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    TREND = "trend"
    PERCENTILE = "percentile"
    HYBRID = "hybrid"


class TrendDirection(Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class UserProfile:
    """User profile for personalization."""
    age: int
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    health_conditions: List[str] = field(default_factory=list)
    fitness_level: Optional[str] = None  # sedentary, lightly_active, moderately_active, very_active
    goals: List[str] = field(default_factory=list)


@dataclass
class HealthCondition:
    """Health condition with impact factors."""
    name: str
    component_factors: Dict[str, float]  # component -> adjustment factor
    description: Optional[str] = None


@dataclass
class ComponentScore:
    """Individual component score with breakdown."""
    component: str
    score: float  # 0-100
    weight: float  # 0-1
    breakdown: Dict[str, float] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0-1, based on data availability


@dataclass
class ScoreInsight:
    """Insight about a health score."""
    category: str  # component name or "overall"
    message: str
    severity: str  # info, warning, success
    recommendation: Optional[str] = None
    related_metrics: List[str] = field(default_factory=list)


@dataclass
class HealthScore:
    """Complete health score with components and insights."""
    overall: float  # 0-100
    components: Dict[str, ComponentScore]
    weights: Dict[str, float]
    insights: List[ScoreInsight]
    trend: TrendDirection
    timestamp: datetime
    date_range: Tuple[date, date]
    scoring_method: ScoringMethod = ScoringMethod.HYBRID
    confidence: float = 1.0  # 0-1, overall confidence
    
    def get_category(self) -> str:
        """Get score category."""
        if self.overall >= 90:
            return "Excellent"
        elif self.overall >= 80:
            return "Very Good"
        elif self.overall >= 70:
            return "Good"
        elif self.overall >= 60:
            return "Fair"
        else:
            return "Needs Attention"
    
    def get_color(self) -> str:
        """Get color for visualization."""
        if self.overall >= 80:
            return "#4CAF50"  # Green
        elif self.overall >= 60:
            return "#FFC107"  # Amber
        else:
            return "#F44336"  # Red


@dataclass
class TrendAnalysis:
    """Analysis of health score trends."""
    direction: TrendDirection
    long_term_direction: TrendDirection
    rate_of_change: float  # percentage per day
    inflection_points: List[Tuple[date, float]]  # (date, score)
    component_trends: Dict[str, TrendDirection]
    forecast: Optional[float] = None  # predicted score in 30 days
    confidence_interval: Optional[Tuple[float, float]] = None
    significant_changes: List[Tuple[date, str, float]] = field(default_factory=list)  # (date, component, change)


@dataclass
class HealthData:
    """Container for health data used in calculations."""
    data: Dict[str, any]  # Raw data dictionary
    user_profile: UserProfile
    
    def has_data(self, date: date) -> bool:
        """Check if data exists for date."""
        return date.isoformat() in self.data.get('daily_data', {})
    
    def get_steps(self, date: date) -> Optional[int]:
        """Get step count for date."""
        daily = self.data.get('daily_data', {}).get(date.isoformat(), {})
        return daily.get('steps')
    
    def get_step_goal(self, date: date) -> int:
        """Get step goal for date."""
        return self.data.get('goals', {}).get('daily_steps', 10000)
    
    def get_sleep_duration(self, date: date) -> Optional[float]:
        """Get sleep duration in hours."""
        daily = self.data.get('daily_data', {}).get(date.isoformat(), {})
        return daily.get('sleep_hours')
    
    def get_heart_rate_resting(self, date: date) -> Optional[float]:
        """Get resting heart rate."""
        daily = self.data.get('daily_data', {}).get(date.isoformat(), {})
        return daily.get('resting_heart_rate')
    
    def get_exercise_minutes(self, date: date) -> Optional[int]:
        """Get exercise minutes."""
        daily = self.data.get('daily_data', {}).get(date.isoformat(), {})
        return daily.get('exercise_minutes')
    
    def get_hrv(self, date: date) -> Optional[float]:
        """Get heart rate variability."""
        daily = self.data.get('daily_data', {}).get(date.isoformat(), {})
        return daily.get('hrv')


@dataclass
class ScoringParameters:
    """Parameters for score calculation."""
    method: ScoringMethod = ScoringMethod.HYBRID
    weights: Dict[str, float] = field(default_factory=dict)
    age_adjustments: bool = True
    condition_adjustments: bool = True
    trend_weight: float = 0.3  # How much to weight trends vs absolute
    percentile_data: Optional[Dict[str, any]] = None  # Population comparison data