"""Trend analysis for health scores over time."""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from scipy import stats
from collections import defaultdict

from .health_score_models import HealthScore, TrendAnalysis, TrendDirection


class HealthScoreTrendAnalyzer:
    """Analyze trends in health scores over time."""
    
    def analyze_trend(self, score_history: List[HealthScore]) -> TrendAnalysis:
        """Analyze health score trends from history."""
        if len(score_history) < 2:
            return TrendAnalysis(
                direction=TrendDirection.INSUFFICIENT_DATA,
                long_term_direction=TrendDirection.INSUFFICIENT_DATA,
                rate_of_change=0.0,
                inflection_points=[],
                component_trends={}
            )
        
        # Sort by timestamp
        score_history = sorted(score_history, key=lambda s: s.timestamp)
        
        # Extract overall scores and timestamps
        scores = [s.overall for s in score_history]
        timestamps = [s.timestamp for s in score_history]
        dates = [s.timestamp.date() for s in score_history]
        
        # Calculate trend directions
        recent_trend = self.calculate_recent_trend(scores[-7:] if len(scores) >= 7 else scores)
        long_trend = self.calculate_long_trend(scores)
        
        # Calculate rate of change
        rate_of_change = self.calculate_rate_of_change(scores, dates)
        
        # Find inflection points
        inflection_points = self.find_inflection_points(scores, dates)
        
        # Analyze component trends
        component_trends = self.analyze_component_trends(score_history)
        
        # Generate forecast
        forecast, confidence_interval = self.forecast_score(scores, dates)
        
        # Find significant changes
        significant_changes = self.find_significant_changes(score_history)
        
        return TrendAnalysis(
            direction=recent_trend,
            long_term_direction=long_trend,
            rate_of_change=rate_of_change,
            inflection_points=inflection_points,
            component_trends=component_trends,
            forecast=forecast,
            confidence_interval=confidence_interval,
            significant_changes=significant_changes
        )
    
    def calculate_recent_trend(self, recent_scores: List[float]) -> TrendDirection:
        """Calculate trend direction for recent scores."""
        if len(recent_scores) < 2:
            return TrendDirection.INSUFFICIENT_DATA
        
        # Calculate linear regression
        x = np.arange(len(recent_scores))
        slope, _, r_value, _, _ = stats.linregress(x, recent_scores)
        
        # Determine trend based on slope and correlation
        if abs(r_value) < 0.3:  # Low correlation, no clear trend
            return TrendDirection.STABLE
        elif slope > 0.5:  # Positive slope
            return TrendDirection.IMPROVING
        elif slope < -0.5:  # Negative slope
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def calculate_long_trend(self, scores: List[float]) -> TrendDirection:
        """Calculate long-term trend direction."""
        if len(scores) < 10:
            return self.calculate_recent_trend(scores)
        
        # Compare first third to last third
        first_third = scores[:len(scores)//3]
        last_third = scores[-len(scores)//3:]
        
        avg_first = np.mean(first_third)
        avg_last = np.mean(last_third)
        
        change = avg_last - avg_first
        
        if change > 5:
            return TrendDirection.IMPROVING
        elif change < -5:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def calculate_rate_of_change(self, scores: List[float], dates: List[date]) -> float:
        """Calculate rate of change in percentage per day."""
        if len(scores) < 2:
            return 0.0
        
        # Calculate days between first and last
        days = (dates[-1] - dates[0]).days
        if days == 0:
            return 0.0
        
        # Calculate total change
        change = scores[-1] - scores[0]
        
        # Return percentage change per day
        return (change / scores[0] * 100) / days if scores[0] != 0 else 0.0
    
    def find_inflection_points(self, scores: List[float], dates: List[date]) -> List[Tuple[date, float]]:
        """Find points where trend direction changes significantly."""
        if len(scores) < 5:
            return []
        
        inflection_points = []
        
        # Use rolling window to detect changes
        window_size = min(5, len(scores) // 3)
        
        for i in range(window_size, len(scores) - window_size):
            # Calculate slopes before and after
            before = scores[i-window_size:i]
            after = scores[i:i+window_size]
            
            slope_before = np.polyfit(range(len(before)), before, 1)[0]
            slope_after = np.polyfit(range(len(after)), after, 1)[0]
            
            # Check if sign changes or significant change in magnitude
            if (slope_before * slope_after < 0 or 
                abs(slope_after - slope_before) > 2):
                inflection_points.append((dates[i], scores[i]))
        
        return inflection_points
    
    def analyze_component_trends(self, score_history: List[HealthScore]) -> Dict[str, TrendDirection]:
        """Analyze trends for each component."""
        component_trends = {}
        
        # Group scores by component
        component_scores = defaultdict(list)
        
        for score in score_history:
            for component, comp_score in score.components.items():
                component_scores[component].append(comp_score.score)
        
        # Calculate trend for each component
        for component, scores in component_scores.items():
            if len(scores) >= 2:
                trend = self.calculate_recent_trend(scores[-7:] if len(scores) >= 7 else scores)
                component_trends[component] = trend
            else:
                component_trends[component] = TrendDirection.INSUFFICIENT_DATA
        
        return component_trends
    
    def forecast_score(self, scores: List[float], dates: List[date]) -> Tuple[Optional[float], Optional[Tuple[float, float]]]:
        """Forecast score 30 days in the future with confidence interval."""
        if len(scores) < 7:
            return None, None
        
        # Use exponential smoothing for forecast
        alpha = 0.3  # Smoothing parameter
        
        # Calculate exponentially weighted moving average
        ewma = [scores[0]]
        for i in range(1, len(scores)):
            ewma.append(alpha * scores[i] + (1 - alpha) * ewma[-1])
        
        # Calculate trend
        recent_trend = ewma[-1] - ewma[-7] if len(ewma) >= 7 else 0
        daily_trend = recent_trend / 7
        
        # Project 30 days
        forecast = ewma[-1] + daily_trend * 30
        
        # Ensure forecast is within valid range
        forecast = max(0, min(100, forecast))
        
        # Calculate confidence interval based on recent variance
        recent_scores = scores[-14:] if len(scores) >= 14 else scores
        std_dev = np.std(recent_scores)
        
        # 95% confidence interval
        margin = 1.96 * std_dev
        confidence_interval = (
            max(0, forecast - margin),
            min(100, forecast + margin)
        )
        
        return forecast, confidence_interval
    
    def find_significant_changes(self, score_history: List[HealthScore]) -> List[Tuple[date, str, float]]:
        """Find significant changes in component scores."""
        if len(score_history) < 2:
            return []
        
        significant_changes = []
        
        # Compare consecutive scores
        for i in range(1, len(score_history)):
            prev_score = score_history[i-1]
            curr_score = score_history[i]
            
            # Check each component for significant changes
            for component in curr_score.components:
                if component in prev_score.components:
                    prev_value = prev_score.components[component].score
                    curr_value = curr_score.components[component].score
                    
                    change = curr_value - prev_value
                    
                    # Consider >10 point change as significant
                    if abs(change) > 10:
                        significant_changes.append((
                            curr_score.timestamp.date(),
                            component,
                            change
                        ))
        
        return significant_changes
    
    def get_trend_insights(self, analysis: TrendAnalysis) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []
        
        # Overall trend insights
        if analysis.direction == TrendDirection.IMPROVING:
            insights.append("Your health score is trending upward - keep up the good work!")
        elif analysis.direction == TrendDirection.DECLINING:
            insights.append("Your health score has been declining - consider focusing on weak areas")
        
        # Long-term vs short-term
        if (analysis.long_term_direction == TrendDirection.IMPROVING and 
            analysis.direction == TrendDirection.DECLINING):
            insights.append("Recent decline despite long-term improvement - stay focused")
        
        # Component-specific insights
        declining_components = [
            comp for comp, trend in analysis.component_trends.items()
            if trend == TrendDirection.DECLINING
        ]
        
        if declining_components:
            insights.append(f"Focus on improving: {', '.join(declining_components)}")
        
        # Forecast insights
        if analysis.forecast is not None:
            if analysis.forecast > 80:
                insights.append(f"On track to reach excellent health score of {analysis.forecast:.0f}")
            elif analysis.forecast < 60:
                insights.append("Current trends suggest intervention needed to improve score")
        
        return insights