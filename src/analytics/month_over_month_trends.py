"""
Month-over-month trends analysis with Wall Street Journal style visualizations.

This module provides comprehensive month-over-month analysis including:
- Waterfall charts for cumulative changes
- Bump charts for ranking changes  
- Stream graphs for composition over time
- Small multiples for metric comparison
- Seasonal decomposition and change point detection
- Insight generation with milestone detection
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
import logging
from collections import defaultdict
from enum import Enum
import warnings

from .monthly_metrics_calculator import MonthlyMetricsCalculator, MonthlyMetrics
from .daily_metrics_calculator import DailyMetricsCalculator, MetricStatistics

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction indicators."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class ChangePoint:
    """Detected change point in time series."""
    date: datetime
    confidence: float
    change_magnitude: float
    before_avg: float
    after_avg: float
    significance: str  # 'low', 'medium', 'high'


@dataclass
class SeasonalDecomposition:
    """Results from seasonal decomposition analysis."""
    trend: List[float]
    seasonal: List[float]
    residual: List[float]
    dates: List[datetime]
    seasonal_strength: float
    trend_strength: float


@dataclass
class MomentumScore:
    """Momentum scoring for trend strength."""
    score: float  # -1.0 to 1.0
    strength: str  # 'weak', 'moderate', 'strong'
    direction: TrendDirection
    acceleration: float
    consistency: float


@dataclass
class ForecastInterval:
    """Forecast with confidence intervals."""
    dates: List[datetime]
    point_forecast: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    confidence_level: float
    method: str


@dataclass
class Milestone:
    """Significant milestone or achievement."""
    date: datetime
    type: str  # 'record', 'goal', 'streak', 'improvement'
    description: str
    value: float
    context: Dict[str, Any]


@dataclass
class TrendInsight:
    """Generated narrative insight."""
    category: str  # 'trend', 'milestone', 'comparison', 'recommendation'
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]


@dataclass
class WaterfallData:
    """Data structure for waterfall chart."""
    categories: List[str]
    values: List[float]
    cumulative: List[float]
    colors: List[str]
    labels: List[str]


@dataclass
class BumpChartData:
    """Data structure for bump chart rankings."""
    metrics: List[str]
    dates: List[datetime]
    rankings: Dict[str, List[int]]
    values: Dict[str, List[float]]


@dataclass
class StreamGraphData:
    """Data structure for stream graph."""
    categories: List[str]
    dates: List[datetime]
    values: Dict[str, List[float]]
    baseline: List[float]


@dataclass
class TrendAnalysis:
    """Comprehensive month-over-month trend analysis results."""
    metric_name: str
    analysis_period: Tuple[datetime, datetime]
    
    # Core data
    monthly_data: List[MonthlyMetrics]
    raw_values: List[float]
    dates: List[datetime]
    
    # Visualization data
    waterfall_data: Optional[WaterfallData] = None
    bump_data: Optional[BumpChartData] = None
    stream_data: Optional[StreamGraphData] = None
    
    # Statistical analysis
    decomposition: Optional[SeasonalDecomposition] = None
    change_points: List[ChangePoint] = field(default_factory=list)
    momentum: Optional[MomentumScore] = None
    forecast: Optional[ForecastInterval] = None
    
    # Insights and milestones
    milestones: List[Milestone] = field(default_factory=list)
    insights: List[TrendInsight] = field(default_factory=list)
    
    # Population comparison (when available)
    percentile_rank: Optional[float] = None
    age_adjusted_rank: Optional[float] = None


class SeasonalDecomposer:
    """Seasonal decomposition using STL (Seasonal and Trend decomposition using Loess)."""
    
    def __init__(self, seasonal_period: int = 12):
        self.seasonal_period = seasonal_period
    
    def decompose(self, values: List[float], dates: List[datetime]) -> SeasonalDecomposition:
        """Perform seasonal decomposition on time series data."""
        if len(values) < self.seasonal_period * 2:
            logger.warning("Insufficient data for seasonal decomposition")
            return self._simple_decomposition(values, dates)
        
        try:
            from statsmodels.tsa.seasonal import STL
            
            # Create pandas series
            ts = pd.Series(values, index=pd.to_datetime(dates))
            ts = ts.resample('M').mean()  # Ensure monthly frequency
            
            # Apply STL decomposition
            stl = STL(ts, seasonal=self.seasonal_period, trend=None, robust=True)
            result = stl.fit()
            
            # Calculate strength metrics
            seasonal_strength = np.var(result.seasonal) / (np.var(result.seasonal) + np.var(result.resid))
            trend_strength = np.var(result.trend) / (np.var(result.trend) + np.var(result.resid))
            
            return SeasonalDecomposition(
                trend=result.trend.values.tolist(),
                seasonal=result.seasonal.values.tolist(),
                residual=result.resid.values.tolist(),
                dates=result.trend.index.to_list(),
                seasonal_strength=float(seasonal_strength),
                trend_strength=float(trend_strength)
            )
            
        except ImportError:
            logger.warning("statsmodels not available, using simple decomposition")
            return self._simple_decomposition(values, dates)
        except Exception as e:
            logger.error(f"Seasonal decomposition failed: {e}")
            return self._simple_decomposition(values, dates)
    
    def _simple_decomposition(self, values: List[float], dates: List[datetime]) -> SeasonalDecomposition:
        """Simple trend extraction using moving average."""
        trend = []
        seasonal = []
        residual = []
        
        window = min(self.seasonal_period, len(values) // 2)
        
        for i in range(len(values)):
            start = max(0, i - window // 2)
            end = min(len(values), i + window // 2 + 1)
            trend_val = np.mean(values[start:end])
            trend.append(trend_val)
            
            # Simple seasonal: remainder after removing trend
            seasonal_val = 0.0  # Simplified - no seasonal component
            seasonal.append(seasonal_val)
            
            residual_val = values[i] - trend_val - seasonal_val
            residual.append(residual_val)
        
        return SeasonalDecomposition(
            trend=trend,
            seasonal=seasonal,
            residual=residual,
            dates=dates,
            seasonal_strength=0.0,
            trend_strength=np.var(trend) / (np.var(trend) + np.var(residual)) if np.var(residual) > 0 else 1.0
        )


class ChangePointDetector:
    """Detect significant change points in time series data."""
    
    def __init__(self, min_segment_length: int = 3, penalty: float = 1.0):
        self.min_segment_length = min_segment_length
        self.penalty = penalty
    
    def detect(self, values: List[float], dates: List[datetime]) -> List[ChangePoint]:
        """Detect change points using PELT (Pruned Exact Linear Time) algorithm."""
        if len(values) < self.min_segment_length * 2:
            return []
        
        try:
            # Simple implementation using variance change detection
            change_points = self._variance_change_detection(values, dates)
            return change_points
            
        except Exception as e:
            logger.error(f"Change point detection failed: {e}")
            return []
    
    def _variance_change_detection(self, values: List[float], dates: List[datetime]) -> List[ChangePoint]:
        """Detect change points based on variance changes."""
        change_points = []
        n = len(values)
        
        # Calculate rolling variance
        window = max(self.min_segment_length, n // 10)
        
        for i in range(window, n - window):
            before_segment = values[i-window:i]
            after_segment = values[i:i+window]
            
            before_var = np.var(before_segment)
            after_var = np.var(after_segment)
            before_mean = np.mean(before_segment)
            after_mean = np.mean(after_segment)
            
            # Statistical test for change in mean
            if len(before_segment) > 1 and len(after_segment) > 1:
                try:
                    t_stat, p_value = stats.ttest_ind(before_segment, after_segment)
                    
                    if p_value < 0.05:  # Significant change
                        change_magnitude = abs(after_mean - before_mean)
                        confidence = 1.0 - p_value
                        
                        # Determine significance level
                        if p_value < 0.001:
                            significance = 'high'
                        elif p_value < 0.01:
                            significance = 'medium'
                        else:
                            significance = 'low'
                        
                        change_points.append(ChangePoint(
                            date=dates[i],
                            confidence=confidence,
                            change_magnitude=change_magnitude,
                            before_avg=before_mean,
                            after_avg=after_mean,
                            significance=significance
                        ))
                except:
                    continue
        
        # Remove nearby change points (within window)
        filtered_points = []
        for cp in change_points:
            if not any(abs((cp.date - existing.date).days) < window * 30 for existing in filtered_points):
                filtered_points.append(cp)
        
        return filtered_points


class InsightNarrator:
    """Generate natural language insights from trend analysis."""
    
    def __init__(self):
        self.templates = self._load_insight_templates()
    
    def generate_insights(self, analysis: TrendAnalysis) -> List[TrendInsight]:
        """Generate narrative insights from trend analysis."""
        insights = []
        
        # Trend direction insights
        insights.extend(self._generate_trend_insights(analysis))
        
        # Milestone insights
        insights.extend(self._generate_milestone_insights(analysis))
        
        # Change point insights
        insights.extend(self._generate_change_point_insights(analysis))
        
        # Forecast insights
        insights.extend(self._generate_forecast_insights(analysis))
        
        # Sort by confidence
        insights.sort(key=lambda x: x.confidence, reverse=True)
        
        return insights[:10]  # Top 10 insights
    
    def _generate_trend_insights(self, analysis: TrendAnalysis) -> List[TrendInsight]:
        """Generate insights about overall trends."""
        insights = []
        
        if not analysis.momentum:
            return insights
        
        momentum = analysis.momentum
        
        if momentum.strength == 'strong':
            if momentum.direction == TrendDirection.INCREASING:
                insights.append(TrendInsight(
                    category='trend',
                    title='Strong Upward Trend',
                    description=f"{analysis.metric_name} shows strong improvement with consistent growth over recent months.",
                    confidence=0.9,
                    supporting_data={'momentum_score': momentum.score, 'direction': momentum.direction.value}
                ))
            elif momentum.direction == TrendDirection.DECREASING:
                insights.append(TrendInsight(
                    category='trend',
                    title='Declining Trend Detected',
                    description=f"{analysis.metric_name} has been declining consistently. Consider reviewing related health habits.",
                    confidence=0.9,
                    supporting_data={'momentum_score': momentum.score, 'direction': momentum.direction.value}
                ))
        
        return insights
    
    def _generate_milestone_insights(self, analysis: TrendAnalysis) -> List[TrendInsight]:
        """Generate insights about milestones."""
        insights = []
        
        recent_milestones = [m for m in analysis.milestones 
                           if (datetime.now() - m.date).days <= 90]
        
        if recent_milestones:
            milestone = recent_milestones[0]
            insights.append(TrendInsight(
                category='milestone',
                title=f"Recent {milestone.type.title()}",
                description=milestone.description,
                confidence=0.8,
                supporting_data={'milestone_type': milestone.type, 'value': milestone.value}
            ))
        
        return insights
    
    def _generate_change_point_insights(self, analysis: TrendAnalysis) -> List[TrendInsight]:
        """Generate insights about significant changes."""
        insights = []
        
        high_confidence_changes = [cp for cp in analysis.change_points 
                                 if cp.significance == 'high']
        
        if high_confidence_changes:
            change = high_confidence_changes[0]
            direction = "improvement" if change.after_avg > change.before_avg else "decline"
            insights.append(TrendInsight(
                category='trend',
                title=f"Significant Change Detected",
                description=f"Notable {direction} in {analysis.metric_name} detected around {change.date.strftime('%B %Y')}.",
                confidence=change.confidence,
                supporting_data={'change_date': change.date, 'magnitude': change.change_magnitude}
            ))
        
        return insights
    
    def _generate_forecast_insights(self, analysis: TrendAnalysis) -> List[TrendInsight]:
        """Generate insights about forecasts."""
        insights = []
        
        if analysis.forecast and len(analysis.forecast.point_forecast) > 0:
            current_avg = np.mean(analysis.raw_values[-3:]) if len(analysis.raw_values) >= 3 else analysis.raw_values[-1]
            forecast_avg = np.mean(analysis.forecast.point_forecast[:3])
            
            change_pct = ((forecast_avg - current_avg) / current_avg) * 100
            
            if abs(change_pct) > 5:  # Significant forecast change
                direction = "increase" if change_pct > 0 else "decrease"
                insights.append(TrendInsight(
                    category='recommendation',
                    title=f"Projected {direction.title()}",
                    description=f"Based on current trends, {analysis.metric_name} is projected to {direction} by approximately {abs(change_pct):.1f}% in the coming months.",
                    confidence=0.7,
                    supporting_data={'forecast_change': change_pct, 'confidence_level': analysis.forecast.confidence_level}
                ))
        
        return insights
    
    def _load_insight_templates(self) -> Dict[str, List[str]]:
        """Load insight generation templates."""
        return {
            'improvement': [
                "{metric} shows consistent improvement over the past {period}",
                "Positive trend detected in {metric} with {change}% increase",
                "Strong momentum in {metric} suggests continued progress"
            ],
            'decline': [
                "{metric} has declined by {change}% over {period}",
                "Downward trend in {metric} warrants attention",
                "Consider strategies to improve {metric} performance"
            ],
            'milestone': [
                "New personal record achieved in {metric}",
                "{streak_length} day improvement streak in {metric}",
                "Reached {goal_type} goal for {metric}"
            ],
            'seasonal': [
                "{metric} typically {pattern} during {season}",
                "Seasonal pattern detected: {metric} peaks in {peak_month}",
                "Your {metric} follows a {confidence}% predictable seasonal cycle"
            ]
        }


class MonthOverMonthTrends:
    """
    Comprehensive month-over-month trends analysis with Wall Street Journal style visualizations.
    
    Provides:
    - Statistical analysis (seasonal decomposition, change points, momentum)
    - Multiple visualization formats (waterfall, bump, stream, small multiples)
    - Natural language insights and milestone detection
    - Population comparisons and forecasting
    """
    
    def __init__(self, monthly_calculator: MonthlyMetricsCalculator):
        self.calculator = monthly_calculator
        self.decomposer = SeasonalDecomposer()
        self.change_detector = ChangePointDetector()
        self.narrator = InsightNarrator()
    
    def analyze_trends(self, 
                      metric: str, 
                      months: int = 12,
                      include_forecast: bool = True,
                      include_population_comparison: bool = False) -> TrendAnalysis:
        """
        Comprehensive month-over-month analysis.
        
        Args:
            metric: The health metric to analyze
            months: Number of months to analyze
            include_forecast: Whether to generate forecasts
            include_population_comparison: Whether to include population benchmarks
            
        Returns:
            TrendAnalysis object with complete analysis results
        """
        logger.info(f"Starting month-over-month analysis for {metric} over {months} months")
        
        try:
            # Get monthly data
            monthly_data = self.calculator.get_monthly_metrics(metric, months)
            
            if not monthly_data:
                raise ValueError(f"No data available for metric {metric}")
            
            # Extract values and dates
            values = [m.avg for m in monthly_data]
            dates = [m.month_start for m in monthly_data]
            
            # Create base analysis
            analysis = TrendAnalysis(
                metric_name=metric,
                analysis_period=(dates[0], dates[-1]),
                monthly_data=monthly_data,
                raw_values=values,
                dates=dates
            )
            
            # Prepare visualization data
            analysis.waterfall_data = self.prepare_waterfall_data(values, dates)
            analysis.bump_data = self.prepare_bump_chart_data({metric: values}, dates)
            analysis.stream_data = self.prepare_stream_graph_data({metric: values}, dates)
            
            # Statistical analysis
            if len(values) >= 6:  # Need sufficient data
                analysis.decomposition = self.decomposer.decompose(values, dates)
                analysis.change_points = self.change_detector.detect(values, dates)
                analysis.momentum = self.calculate_momentum_score(values)
                
                if include_forecast:
                    analysis.forecast = self.generate_forecast(values, dates)
            
            # Detect milestones
            analysis.milestones = self.detect_milestones(values, dates, metric)
            
            # Generate insights
            analysis.insights = self.narrator.generate_insights(analysis)
            
            # Population comparison (placeholder - would require external data)
            if include_population_comparison:
                analysis.percentile_rank = self._estimate_percentile_rank(np.mean(values))
            
            logger.info(f"Completed month-over-month analysis for {metric}")
            return analysis
            
        except Exception as e:
            logger.error(f"Month-over-month analysis failed for {metric}: {e}")
            raise
    
    def prepare_waterfall_data(self, values: List[float], dates: List[datetime]) -> WaterfallData:
        """Prepare data for waterfall chart visualization."""
        if len(values) < 2:
            return WaterfallData([], [], [], [], [])
        
        categories = []
        chart_values = []
        cumulative = []
        colors = []
        labels = []
        
        # Start with initial value
        categories.append(dates[0].strftime('%b %Y'))
        chart_values.append(values[0])
        cumulative.append(values[0])
        colors.append('#4A90E2')  # Blue for starting value
        labels.append(f'{values[0]:.1f}')
        
        # Add month-to-month changes
        running_total = values[0]
        for i in range(1, len(values)):
            change = values[i] - values[i-1]
            categories.append(f'{dates[i].strftime("%b %Y")} Change')
            chart_values.append(change)
            running_total += change
            cumulative.append(running_total)
            
            # Color coding
            if change > 0:
                colors.append('#50E3C2')  # Green for positive
            else:
                colors.append('#F5A623')  # Orange for negative
            
            labels.append(f'{change:+.1f}')
        
        # End with final value
        categories.append(f'Final ({dates[-1].strftime("%b %Y")})')
        chart_values.append(values[-1])
        cumulative.append(values[-1])
        colors.append('#4A90E2')  # Blue for ending value
        labels.append(f'{values[-1]:.1f}')
        
        return WaterfallData(
            categories=categories,
            values=chart_values,
            cumulative=cumulative,
            colors=colors,
            labels=labels
        )
    
    def prepare_bump_chart_data(self, 
                               metrics_data: Dict[str, List[float]], 
                               dates: List[datetime]) -> BumpChartData:
        """Prepare data for bump chart (ranking over time)."""
        if not metrics_data or len(dates) == 0:
            return BumpChartData([], [], {}, {})
        
        metrics = list(metrics_data.keys())
        rankings = {}
        
        # Calculate rankings for each time period
        for i in range(len(dates)):
            period_values = {}
            for metric in metrics:
                if i < len(metrics_data[metric]):
                    period_values[metric] = metrics_data[metric][i]
            
            # Sort by value (highest gets rank 1)
            sorted_metrics = sorted(period_values.items(), key=lambda x: x[1], reverse=True)
            
            for rank, (metric, value) in enumerate(sorted_metrics, 1):
                if metric not in rankings:
                    rankings[metric] = []
                rankings[metric].append(rank)
        
        return BumpChartData(
            metrics=metrics,
            dates=dates,
            rankings=rankings,
            values=metrics_data
        )
    
    def prepare_stream_graph_data(self, 
                                 metrics_data: Dict[str, List[float]], 
                                 dates: List[datetime]) -> StreamGraphData:
        """Prepare data for stream graph visualization."""
        categories = list(metrics_data.keys())
        
        # Normalize values to show composition
        normalized_values = {}
        baseline = []
        
        for i in range(len(dates)):
            period_total = sum(metrics_data[metric][i] if i < len(metrics_data[metric]) else 0 
                             for metric in categories)
            
            if period_total > 0:
                baseline.append(0)
                for metric in categories:
                    if metric not in normalized_values:
                        normalized_values[metric] = []
                    
                    value = metrics_data[metric][i] if i < len(metrics_data[metric]) else 0
                    normalized_pct = (value / period_total) * 100
                    normalized_values[metric].append(normalized_pct)
            else:
                baseline.append(0)
                for metric in categories:
                    if metric not in normalized_values:
                        normalized_values[metric] = []
                    normalized_values[metric].append(0)
        
        return StreamGraphData(
            categories=categories,
            dates=dates,
            values=normalized_values,
            baseline=baseline
        )
    
    def calculate_momentum_score(self, values: List[float]) -> MomentumScore:
        """Calculate momentum score for trend strength and direction."""
        if len(values) < 3:
            return MomentumScore(0.0, 'weak', TrendDirection.STABLE, 0.0, 0.0)
        
        # Calculate linear trend
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Normalize slope to get score (-1 to 1)
        value_range = max(values) - min(values)
        if value_range > 0:
            normalized_slope = slope * len(values) / value_range
            score = np.tanh(normalized_slope)  # Bounded between -1 and 1
        else:
            score = 0.0
        
        # Determine direction
        if abs(score) < 0.1:
            direction = TrendDirection.STABLE
        elif abs(slope) / np.std(values) < 0.5:  # High volatility relative to trend
            direction = TrendDirection.VOLATILE
        elif score > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Determine strength
        abs_score = abs(score)
        if abs_score < 0.3:
            strength = 'weak'
        elif abs_score < 0.7:
            strength = 'moderate'
        else:
            strength = 'strong'
        
        # Calculate acceleration (second derivative)
        if len(values) >= 4:
            acceleration = np.mean(np.diff(np.diff(values)))
        else:
            acceleration = 0.0
        
        # Calculate consistency (inverse of coefficient of variation of residuals)
        residuals = np.array(values) - (slope * x + intercept)
        consistency = 1.0 / (1.0 + np.std(residuals) / np.mean(np.abs(residuals))) if np.mean(np.abs(residuals)) > 0 else 1.0
        
        return MomentumScore(
            score=float(score),
            strength=strength,
            direction=direction,
            acceleration=float(acceleration),
            consistency=float(consistency)
        )
    
    def generate_forecast(self, 
                         values: List[float], 
                         dates: List[datetime],
                         periods: int = 6,
                         confidence_level: float = 0.95) -> ForecastInterval:
        """Generate forecast with confidence intervals."""
        if len(values) < 4:
            logger.warning("Insufficient data for forecasting")
            return None
        
        try:
            # Simple linear regression forecast
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Generate future dates
            last_date = dates[-1]
            future_dates = []
            for i in range(1, periods + 1):
                future_date = last_date + timedelta(days=30 * i)  # Approximate month
                future_dates.append(future_date)
            
            # Generate point forecasts
            future_x = np.arange(len(values), len(values) + periods)
            point_forecast = slope * future_x + intercept
            
            # Calculate prediction intervals
            residuals = np.array(values) - (slope * x + intercept)
            mse = np.mean(residuals ** 2)
            
            # Standard error for prediction
            se_pred = np.sqrt(mse * (1 + 1/len(values) + (future_x - np.mean(x))**2 / np.sum((x - np.mean(x))**2)))
            
            # T-distribution critical value
            alpha = 1 - confidence_level
            df = len(values) - 2
            t_crit = stats.t.ppf(1 - alpha/2, df)
            
            # Confidence intervals
            margin_error = t_crit * se_pred
            lower_bound = point_forecast - margin_error
            upper_bound = point_forecast + margin_error
            
            return ForecastInterval(
                dates=future_dates,
                point_forecast=point_forecast.tolist(),
                lower_bound=lower_bound.tolist(),
                upper_bound=upper_bound.tolist(),
                confidence_level=confidence_level,
                method='linear_regression'
            )
            
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return None
    
    def detect_milestones(self, 
                         values: List[float], 
                         dates: List[datetime], 
                         metric: str) -> List[Milestone]:
        """Detect significant milestones and achievements."""
        milestones = []
        
        if len(values) < 2:
            return milestones
        
        # Personal records
        max_value = max(values)
        max_idx = values.index(max_value)
        milestones.append(Milestone(
            date=dates[max_idx],
            type='record',
            description=f"Personal record of {max_value:.1f} achieved in {metric}",
            value=max_value,
            context={'record_type': 'maximum', 'previous_best': max(values[:max_idx]) if max_idx > 0 else 0}
        ))
        
        # Improvement streaks (3+ consecutive increases)
        streak_start = None
        streak_length = 0
        
        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                if streak_start is None:
                    streak_start = i-1
                streak_length += 1
            else:
                if streak_length >= 3:
                    milestones.append(Milestone(
                        date=dates[streak_start + streak_length],
                        type='streak',
                        description=f"{streak_length}-month improvement streak in {metric}",
                        value=values[streak_start + streak_length],
                        context={'streak_length': streak_length, 'start_value': values[streak_start]}
                    ))
                streak_start = None
                streak_length = 0
        
        # Check final streak
        if streak_length >= 3:
            milestones.append(Milestone(
                date=dates[-1],
                type='streak',
                description=f"{streak_length}-month improvement streak in {metric}",
                value=values[-1],
                context={'streak_length': streak_length, 'start_value': values[-streak_length]}
            ))
        
        # Significant improvements (>20% increase from previous low)
        for i in range(2, len(values)):
            window_min = min(values[max(0, i-6):i])  # 6-month lookback
            if values[i] > window_min * 1.2:  # 20% improvement
                milestones.append(Milestone(
                    date=dates[i],
                    type='improvement',
                    description=f"Significant improvement: {values[i]:.1f} (+{((values[i]/window_min - 1) * 100):.0f}%) in {metric}",
                    value=values[i],
                    context={'improvement_pct': (values[i]/window_min - 1) * 100, 'from_value': window_min}
                ))
        
        # Sort by date and limit to most significant
        milestones.sort(key=lambda x: x.date)
        return milestones[-10:]  # Keep most recent 10
    
    def _estimate_percentile_rank(self, value: float) -> float:
        """Estimate percentile rank compared to population (placeholder implementation)."""
        # This would typically query a population database
        # For now, return a simulated percentile based on value
        
        # Simulate normal distribution ranking
        # This is a placeholder - real implementation would use actual population data
        normalized_value = (value - 50) / 20  # Assume mean=50, std=20
        percentile = stats.norm.cdf(normalized_value) * 100
        
        return max(0, min(100, percentile))


class TrendVisualizationSuite:
    """Complete visualization suite for month-over-month trends."""
    
    def __init__(self):
        self.charts = {
            'waterfall': self._create_waterfall_chart,
            'bump': self._create_bump_chart,
            'stream': self._create_stream_graph,
            'multiples': self._create_small_multiples
        }
    
    def render_suite(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Render complete visualization suite."""
        rendered_charts = {}
        
        for chart_type, renderer in self.charts.items():
            try:
                rendered_charts[chart_type] = renderer(analysis)
            except Exception as e:
                logger.error(f"Failed to render {chart_type} chart: {e}")
                rendered_charts[chart_type] = None
        
        return rendered_charts
    
    def _create_waterfall_chart(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Create waterfall chart configuration."""
        if not analysis.waterfall_data:
            return None
        
        return {
            'type': 'waterfall',
            'title': f'{analysis.metric_name} - Month-over-Month Changes',
            'categories': analysis.waterfall_data.categories,
            'values': analysis.waterfall_data.values,
            'cumulative': analysis.waterfall_data.cumulative,
            'colors': analysis.waterfall_data.colors,
            'labels': analysis.waterfall_data.labels,
            'style': 'wsj_minimal'
        }
    
    def _create_bump_chart(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Create bump chart configuration."""
        if not analysis.bump_data:
            return None
        
        return {
            'type': 'bump',
            'title': f'{analysis.metric_name} - Ranking Over Time',
            'metrics': analysis.bump_data.metrics,
            'dates': [d.strftime('%b %Y') for d in analysis.bump_data.dates],
            'rankings': analysis.bump_data.rankings,
            'values': analysis.bump_data.values,
            'style': 'wsj_lines'
        }
    
    def _create_stream_graph(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Create stream graph configuration."""
        if not analysis.stream_data:
            return None
        
        return {
            'type': 'stream',
            'title': f'{analysis.metric_name} - Composition Over Time',
            'categories': analysis.stream_data.categories,
            'dates': [d.strftime('%b %Y') for d in analysis.stream_data.dates],
            'values': analysis.stream_data.values,
            'baseline': analysis.stream_data.baseline,
            'style': 'wsj_areas'
        }
    
    def _create_small_multiples(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Create small multiples configuration."""
        return {
            'type': 'small_multiples',
            'title': f'{analysis.metric_name} - Multiple Views',
            'charts': [
                {
                    'title': 'Raw Values',
                    'type': 'line',
                    'x': [d.strftime('%b %Y') for d in analysis.dates],
                    'y': analysis.raw_values
                },
                {
                    'title': 'Trend Component',
                    'type': 'line',
                    'x': [d.strftime('%b %Y') for d in analysis.decomposition.dates] if analysis.decomposition else [],
                    'y': analysis.decomposition.trend if analysis.decomposition else []
                },
                {
                    'title': 'Monthly Changes',
                    'type': 'bar',
                    'x': [d.strftime('%b %Y') for d in analysis.dates[1:]],
                    'y': [analysis.raw_values[i] - analysis.raw_values[i-1] for i in range(1, len(analysis.raw_values))]
                }
            ],
            'style': 'wsj_grid'
        }