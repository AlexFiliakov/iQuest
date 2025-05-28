"""Main health score calculator implementation."""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta

from .health_score_models import (
    HealthScore, HealthData, UserProfile, ScoringMethod,
    ComponentScore, ScoreInsight, TrendDirection, ScoringParameters
)
from .component_calculators import (
    ActivityConsistencyCalculator,
    SleepQualityCalculator,
    HeartHealthCalculator,
    OtherMetricsCalculator
)
from .personalization_engine import PersonalizationEngine
from .trend_analyzer import HealthScoreTrendAnalyzer

logger = logging.getLogger(__name__)


class HealthScoreCalculator:
    """Main calculator for composite health scores."""
    
    def __init__(self, user_profile: UserProfile, 
                 scoring_params: Optional[ScoringParameters] = None):
        """Initialize calculator with user profile."""
        self.user_profile = user_profile
        self.scoring_params = scoring_params or ScoringParameters()
        self.personalization = PersonalizationEngine(user_profile)
        self.trend_analyzer = HealthScoreTrendAnalyzer()
        
        # Initialize component calculators
        self.component_calculators = {
            'activity': ActivityConsistencyCalculator(),
            'sleep': SleepQualityCalculator(),
            'heart': HeartHealthCalculator(),
            'other': OtherMetricsCalculator()
        }
        
        # Get personalized weights
        default_weights = self.get_default_weights()
        self.weights = self.personalization.get_personalized_weights(default_weights)
    
    def calculate_health_score(self, data: Dict[str, any], 
                             date_range: Tuple[date, date],
                             historical_scores: Optional[List[HealthScore]] = None) -> HealthScore:
        """Calculate composite health score for date range."""
        try:
            # Create health data container
            health_data = HealthData(data=data, user_profile=self.user_profile)
            
            # Calculate component scores
            component_scores = {}
            overall_confidence = 1.0
            
            for component, calculator in self.component_calculators.items():
                logger.info(f"Calculating {component} score...")
                
                # Calculate raw score
                component_score = calculator.calculate(health_data, date_range)
                
                # Apply personalization adjustments
                adjusted_score = self._apply_adjustments(component, component_score.score)
                component_score.score = adjusted_score
                
                # Update weight from personalized weights
                component_score.weight = self.weights[component]
                
                component_scores[component] = component_score
                overall_confidence *= component_score.confidence
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(component_scores)
            
            # Determine trend
            trend = self._determine_trend(overall_score, historical_scores)
            
            # Generate insights
            insights = self._generate_insights(component_scores, overall_score, trend)
            
            # Add personalized recommendations
            personalized_recs = self.personalization.get_personalized_recommendations(
                {comp: score.score for comp, score in component_scores.items()}
            )
            for rec in personalized_recs:
                insights.append(ScoreInsight(
                    category='personalized',
                    message=rec,
                    severity='info',
                    recommendation=rec
                ))
            
            # Create health score
            health_score = HealthScore(
                overall=overall_score,
                components=component_scores,
                weights=self.weights,
                insights=insights,
                trend=trend,
                timestamp=datetime.now(),
                date_range=date_range,
                scoring_method=self.scoring_params.method,
                confidence=overall_confidence ** (1/len(component_scores))  # Geometric mean
            )
            
            logger.info(f"Health score calculated: {overall_score:.1f}")
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            raise
    
    def get_default_weights(self) -> Dict[str, float]:
        """Get default component weights."""
        if self.scoring_params.weights:
            return self.scoring_params.weights
        
        return {
            'activity': 0.40,
            'sleep': 0.30,
            'heart': 0.20,
            'other': 0.10
        }
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update component weights."""
        # Validate weights sum to 1.0
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")
        
        self.weights = new_weights
        logger.info(f"Updated weights: {new_weights}")
    
    def _apply_adjustments(self, component: str, raw_score: float) -> float:
        """Apply all adjustments to raw score."""
        score = raw_score
        
        # Apply age adjustments
        if self.scoring_params.age_adjustments:
            score = self.personalization.adjust_for_age(component, score)
        
        # Apply condition adjustments
        if self.scoring_params.condition_adjustments:
            score = self.personalization.adjust_for_conditions(component, score)
        
        # Apply fitness level adjustments
        score = self.personalization.adjust_for_fitness_level(component, score)
        
        # Ensure score stays in valid range
        return min(100, max(0, score))
    
    def _calculate_overall_score(self, component_scores: Dict[str, ComponentScore]) -> float:
        """Calculate weighted overall score."""
        total_score = 0
        total_weight = 0
        
        for component, score in component_scores.items():
            if score.confidence > 0:  # Only include components with data
                total_score += score.score * score.weight
                total_weight += score.weight
        
        if total_weight == 0:
            return 0
        
        # Normalize by actual weights used
        return total_score / total_weight * 100
    
    def _determine_trend(self, current_score: float, 
                        historical_scores: Optional[List[HealthScore]]) -> TrendDirection:
        """Determine trend direction."""
        if not historical_scores:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Add current score to history for analysis
        all_scores = historical_scores + [
            HealthScore(
                overall=current_score,
                components={},
                weights=self.weights,
                insights=[],
                trend=TrendDirection.STABLE,
                timestamp=datetime.now(),
                date_range=(date.today(), date.today())
            )
        ]
        
        # Analyze trend
        trend_analysis = self.trend_analyzer.analyze_trend(all_scores)
        return trend_analysis.direction
    
    def _generate_insights(self, component_scores: Dict[str, ComponentScore], 
                          overall_score: float, trend: TrendDirection) -> List[ScoreInsight]:
        """Generate insights based on scores."""
        insights = []
        
        # Overall score insight
        category = self._get_score_category(overall_score)
        insights.append(ScoreInsight(
            category='overall',
            message=f"Your health score is {category}",
            severity='success' if overall_score >= 70 else 'warning'
        ))
        
        # Trend insight
        if trend == TrendDirection.IMPROVING:
            insights.append(ScoreInsight(
                category='overall',
                message="Your health is improving!",
                severity='success'
            ))
        elif trend == TrendDirection.DECLINING:
            insights.append(ScoreInsight(
                category='overall',
                message="Your health score is declining",
                severity='warning',
                recommendation="Focus on areas that need improvement"
            ))
        
        # Component insights
        for component, score in component_scores.items():
            # Add component-specific insights
            for insight_msg in score.insights:
                insights.append(ScoreInsight(
                    category=component,
                    message=insight_msg,
                    severity='info' if score.score >= 70 else 'warning'
                ))
            
            # Low score warnings
            if score.score < 60:
                insights.append(ScoreInsight(
                    category=component,
                    message=f"{component.title()} score needs attention",
                    severity='warning',
                    recommendation=f"Focus on improving your {component} habits"
                ))
            
            # Low confidence warnings
            if score.confidence < 0.5:
                insights.append(ScoreInsight(
                    category=component,
                    message=f"Limited {component} data available",
                    severity='info',
                    recommendation=f"Track more {component} data for accurate scoring"
                ))
        
        # Find strongest and weakest components
        sorted_components = sorted(
            component_scores.items(), 
            key=lambda x: x[1].score,
            reverse=True
        )
        
        if len(sorted_components) >= 2:
            strongest = sorted_components[0]
            weakest = sorted_components[-1]
            
            insights.append(ScoreInsight(
                category=strongest[0],
                message=f"{strongest[0].title()} is your strongest area",
                severity='success'
            ))
            
            if weakest[1].score < 70:
                insights.append(ScoreInsight(
                    category=weakest[0],
                    message=f"{weakest[0].title()} has the most room for improvement",
                    severity='info',
                    recommendation=f"Consider focusing on {weakest[0]} to boost overall health"
                ))
        
        return insights
    
    def _get_score_category(self, score: float) -> str:
        """Get category name for score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Attention"
    
    def calculate_score_history(self, data: Dict[str, any], 
                               periods: int = 30,
                               period_days: int = 1) -> List[HealthScore]:
        """Calculate historical scores for trend analysis."""
        scores = []
        end_date = date.today()
        
        for i in range(periods):
            period_end = end_date - timedelta(days=i * period_days)
            period_start = period_end - timedelta(days=period_days - 1)
            
            try:
                score = self.calculate_health_score(
                    data,
                    (period_start, period_end),
                    historical_scores=scores
                )
                scores.append(score)
            except Exception as e:
                logger.warning(f"Failed to calculate score for period {period_start}-{period_end}: {e}")
        
        # Reverse to get chronological order
        return list(reversed(scores))
    
    def get_score_breakdown(self, health_score: HealthScore) -> Dict[str, any]:
        """Get detailed breakdown of score calculation."""
        breakdown = {
            'overall_score': health_score.overall,
            'category': health_score.get_category(),
            'confidence': health_score.confidence,
            'components': {}
        }
        
        for component, score in health_score.components.items():
            breakdown['components'][component] = {
                'score': score.score,
                'weight': score.weight,
                'weighted_contribution': score.score * score.weight,
                'confidence': score.confidence,
                'breakdown': score.breakdown
            }
        
        return breakdown