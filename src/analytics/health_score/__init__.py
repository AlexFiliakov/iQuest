"""Health Score Calculator package for composite health scoring.

This package provides a comprehensive health scoring system that analyzes multiple
health metrics to generate personalized health scores and insights. The system
uses evidence-based algorithms to evaluate activity, sleep, heart health, and
other key health indicators.

The package includes:

- **Core Calculator**: Main health score computation engine
- **Data Models**: Health score, component scores, and trend analysis models
- **Component Calculators**: Specialized calculators for different health domains
- **Personalization Engine**: User-specific score adjustments and recommendations
- **Trend Analysis**: Historical trend analysis and prediction

The health scoring system is designed to provide actionable insights while
maintaining clinical accuracy and personalization for individual user profiles.

Example:
    Basic health score calculation:
    
    >>> from analytics.health_score import HealthScoreCalculator
    >>> calculator = HealthScoreCalculator(database)
    >>> score = calculator.calculate_score(user_id, start_date, end_date)
    >>> print(f"Health Score: {score.overall_score}")
    
    Component-specific analysis:
    
    >>> from analytics.health_score import ActivityConsistencyCalculator
    >>> activity_calc = ActivityConsistencyCalculator()
    >>> activity_score = activity_calc.calculate(activity_data)
"""

from .health_score_calculator import HealthScoreCalculator
from .health_score_models import (
    HealthScore,
    ComponentScore,
    ScoreInsight,
    ScoringMethod,
    TrendAnalysis,
    TrendDirection,
    UserProfile,
    HealthCondition
)
from .component_calculators import (
    ActivityConsistencyCalculator,
    SleepQualityCalculator,
    HeartHealthCalculator,
    OtherMetricsCalculator
)
from .personalization_engine import PersonalizationEngine
from .trend_analyzer import HealthScoreTrendAnalyzer

__all__ = [
    'HealthScoreCalculator',
    'HealthScore',
    'ComponentScore',
    'ScoreInsight',
    'ScoringMethod',
    'TrendAnalysis',
    'TrendDirection',
    'UserProfile',
    'HealthCondition',
    'ActivityConsistencyCalculator',
    'SleepQualityCalculator',
    'HeartHealthCalculator',
    'OtherMetricsCalculator',
    'PersonalizationEngine',
    'HealthScoreTrendAnalyzer'
]