"""
Enhanced Health Insights & Recommendations Engine.

This module implements the intelligent insights engine that analyzes health patterns,
identifies opportunities for improvement, and generates personalized, actionable 
recommendations based on evidence-based health guidelines.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats

from .health_insights_models import (
    HealthInsight, InsightCategory, InsightType, EvidenceLevel,
    Priority, ImpactPotential, Achievability, Timeframe,
    PersonalizedGoal, InsightBatch, InsightEvidence
)
from .evidence_database import EvidenceDatabase
from ..ui.charts.wsj_style_manager import WSJStyleManager
from .medical_evidence_validator import MedicalEvidenceValidator


class StatisticalPatternAnalyzer:
    """Analyzes patterns in health data using statistical methods."""
    
    def calculate_consistency_score(self, data: pd.Series, 
                                  target_variance: float = 0.5) -> float:
        """Calculate consistency score (0-1) for a time series."""
        if len(data) < 3:
            return 0.0
        
        # Calculate coefficient of variation
        mean_val = data.mean()
        std_val = data.std()
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / mean_val
        
        # Convert to 0-1 score (lower CV = higher consistency)
        consistency = max(0, 1 - (cv / target_variance))
        return min(1.0, consistency)
    
    def detect_trend(self, data: pd.Series, 
                    min_points: int = 7) -> Dict[str, Any]:
        """Detect trend in time series data."""
        if len(data) < min_points:
            return {'trend': 'insufficient_data', 'confidence': 0}
        
        # Prepare data for linear regression
        x = np.arange(len(data))
        y = data.values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < min_points:
            return {'trend': 'insufficient_data', 'confidence': 0}
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend direction and strength
        if p_value > 0.05:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        # Calculate confidence based on R-squared and p-value
        confidence = (r_value ** 2) * 100 * (1 - p_value)
        
        return {
            'trend': trend,
            'slope': slope,
            'confidence': min(100, max(0, confidence)),
            'p_value': p_value,
            'r_squared': r_value ** 2
        }
    
    def find_weekly_patterns(self, data: pd.DataFrame,
                           date_column: str,
                           value_column: str) -> Dict[str, Any]:
        """Find day-of-week patterns in data."""
        if len(data) < 14:  # Need at least 2 weeks
            return {'pattern_found': False}
        
        # Add day of week
        data['day_of_week'] = pd.to_datetime(data[date_column]).dt.dayofweek
        
        # Group by day of week
        daily_stats = data.groupby('day_of_week')[value_column].agg(['mean', 'std', 'count'])
        
        # Check if there's significant variation between days
        if daily_stats['count'].min() < 2:
            return {'pattern_found': False}
        
        # Perform ANOVA to test if days are significantly different
        groups = []
        for day in range(7):
            day_data = data[data['day_of_week'] == day][value_column].dropna()
            if len(day_data) >= 2:
                groups.append(day_data.values)
        
        if len(groups) < 2:
            return {'pattern_found': False}
        
        f_stat, p_value = stats.f_oneway(*groups)
        
        pattern_found = p_value < 0.05
        
        return {
            'pattern_found': pattern_found,
            'daily_averages': daily_stats['mean'].to_dict(),
            'best_days': daily_stats.nlargest(2, 'mean').index.tolist(),
            'worst_days': daily_stats.nsmallest(2, 'mean').index.tolist(),
            'p_value': p_value,
            'variation_coefficient': daily_stats['mean'].std() / daily_stats['mean'].mean()
        }


class CorrelationInsightGenerator:
    """Generates insights based on correlations between metrics."""
    
    def find_significant_correlations(self, data: Dict[str, pd.DataFrame],
                                    min_correlation: float = 0.3,
                                    min_points: int = 30) -> List[Dict[str, Any]]:
        """Find significant correlations between different metrics."""
        correlations = []
        
        # Get all metric pairs
        metrics = list(data.keys())
        
        for i, metric1 in enumerate(metrics):
            for metric2 in metrics[i+1:]:
                df1 = data[metric1]
                df2 = data[metric2]
                
                # Merge on date
                if 'date' in df1.columns and 'date' in df2.columns:
                    merged = pd.merge(df1, df2, on='date', suffixes=('_1', '_2'))
                    
                    if len(merged) >= min_points:
                        # Get value columns
                        val_cols_1 = [c for c in merged.columns if c.endswith('_1') and c != 'date']
                        val_cols_2 = [c for c in merged.columns if c.endswith('_2') and c != 'date']
                        
                        if val_cols_1 and val_cols_2:
                            val1 = merged[val_cols_1[0]].dropna()
                            val2 = merged[val_cols_2[0]].dropna()
                            
                            if len(val1) >= min_points and len(val2) >= min_points:
                                # Calculate correlation
                                corr, p_value = stats.pearsonr(val1, val2)
                                
                                if abs(corr) >= min_correlation and p_value < 0.05:
                                    correlations.append({
                                        'metric1': metric1,
                                        'metric2': metric2,
                                        'correlation': corr,
                                        'p_value': p_value,
                                        'strength': 'strong' if abs(corr) > 0.7 else 'moderate',
                                        'direction': 'positive' if corr > 0 else 'negative',
                                        'sample_size': len(val1)
                                    })
        
        return sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)


class TrendInsightGenerator:
    """Generates insights based on trend analysis."""
    
    def __init__(self, pattern_analyzer: StatisticalPatternAnalyzer):
        self.pattern_analyzer = pattern_analyzer
    
    def analyze_metric_trends(self, data: pd.DataFrame,
                            metric_name: str,
                            value_column: str,
                            date_column: str = 'date',
                            lookback_days: int = 30) -> Optional[Dict[str, Any]]:
        """Analyze trends for a specific metric."""
        if len(data) < 7:
            return None
        
        # Filter to recent data
        data = data.copy()
        data[date_column] = pd.to_datetime(data[date_column])
        cutoff_date = data[date_column].max() - timedelta(days=lookback_days)
        recent_data = data[data[date_column] >= cutoff_date]
        
        if len(recent_data) < 7:
            return None
        
        # Analyze trend
        trend_info = self.pattern_analyzer.detect_trend(recent_data[value_column])
        
        if trend_info['confidence'] < 60:
            return None
        
        # Calculate change magnitude
        start_val = recent_data[value_column].iloc[:3].mean()
        end_val = recent_data[value_column].iloc[-3:].mean()
        
        if start_val == 0:
            percent_change = 0
        else:
            percent_change = ((end_val - start_val) / start_val) * 100
        
        return {
            'metric': metric_name,
            'trend': trend_info['trend'],
            'confidence': trend_info['confidence'],
            'percent_change': percent_change,
            'start_value': start_val,
            'end_value': end_val,
            'days_analyzed': len(recent_data),
            'statistical_significance': trend_info.get('p_value', 1.0) < 0.05
        }


class EvidenceBasedGoalGenerator:
    """Generates personalized goals based on evidence and current performance."""
    
    def __init__(self, evidence_db: EvidenceDatabase):
        self.evidence_db = evidence_db
    
    def generate_goal(self, metric_type: str,
                     current_value: float,
                     category: InsightCategory,
                     user_demographics: Optional[Dict[str, Any]] = None) -> Optional[PersonalizedGoal]:
        """Generate a personalized goal for a specific metric."""
        # Get evidence-based recommendation
        recommendation = self.evidence_db.get_recommendation_value(
            category, metric_type, user_demographics
        )
        
        if not recommendation:
            return None
        
        # Determine target based on recommendation and current value
        if 'optimal' in recommendation:
            target = recommendation['optimal']
        elif 'min' in recommendation and 'max' in recommendation:
            # If current is below min, target min
            # If current is above max, target max
            # Otherwise, aim for middle
            if current_value < recommendation['min']:
                target = recommendation['min']
            elif current_value > recommendation['max']:
                target = recommendation['max']
            else:
                target = (recommendation['min'] + recommendation['max']) / 2
        else:
            return None
        
        # Calculate timeline based on gap
        gap = abs(target - current_value)
        gap_percent = (gap / current_value * 100) if current_value > 0 else 100
        
        if gap_percent < 10:
            timeline = "2-4 weeks"
        elif gap_percent < 25:
            timeline = "1-2 months"
        else:
            timeline = "2-3 months"
        
        # Create milestones
        milestones = []
        if gap > 0:
            milestone_count = min(4, max(2, int(gap_percent / 10)))
            for i in range(1, milestone_count + 1):
                milestone_value = current_value + (gap * i / milestone_count)
                milestones.append({
                    'week': i * 2,
                    'target': milestone_value,
                    'description': f"Reach {milestone_value:.1f}"
                })
        
        # Get evidence
        evidence = self.evidence_db.get_evidence_for_insight(category, metric_type)
        
        return PersonalizedGoal(
            goal_type=metric_type,
            current_baseline=current_value,
            recommended_target=target,
            rationale=f"Based on {evidence.source_name if evidence else 'health guidelines'}",
            timeline=timeline,
            milestones=milestones,
            evidence_basis=evidence,
            confidence_score=85.0,
            personalization_factors={'current_performance': current_value}
        )


class EnhancedHealthInsightsEngine:
    """Evidence-based insights engine following WSJ analytics principles."""
    
    def __init__(self, data_manager=None, 
                 evidence_db: Optional[EvidenceDatabase] = None,
                 style_manager: Optional[WSJStyleManager] = None):
        """Initialize the insights engine."""
        self.data_manager = data_manager
        self.evidence_db = evidence_db or EvidenceDatabase()
        self.style_manager = style_manager or WSJStyleManager()
        
        # Rule-based insight generators with evidence integration
        self.pattern_analyzer = StatisticalPatternAnalyzer()
        self.correlation_analyzer = CorrelationInsightGenerator()
        self.trend_analyzer = TrendInsightGenerator(self.pattern_analyzer)
        self.goal_optimizer = EvidenceBasedGoalGenerator(self.evidence_db)
        
        # Evidence validation
        self.evidence_validator = MedicalEvidenceValidator()
        
        # Insight cache
        self._insight_cache = {}
    
    def generate_prioritized_insights(self, user_data: Dict[str, pd.DataFrame],
                                    time_period: str = "monthly",
                                    max_insights: int = 5) -> List[HealthInsight]:
        """Generate evidence-based insights with WSJ presentation."""
        all_insights = []
        
        # Pattern-based insights
        pattern_insights = self._analyze_behavioral_patterns(user_data)
        all_insights.extend(pattern_insights)
        
        # Correlation insights
        correlation_insights = self._analyze_correlation_patterns(user_data)
        all_insights.extend(correlation_insights)
        
        # Trend insights
        trend_insights = self._analyze_trend_patterns(user_data)
        all_insights.extend(trend_insights)
        
        # Goal opportunity insights
        goal_insights = self._identify_goal_opportunities(user_data)
        all_insights.extend(goal_insights)
        
        # Validate evidence and add medical disclaimers
        validated_insights = []
        for insight in all_insights:
            validated_insight = self._validate_and_enhance_insight(insight)
            if validated_insight:
                validated_insights.append(validated_insight)
        
        # Prioritize insights
        prioritized = self._prioritize_insights(validated_insights)
        
        # Apply WSJ-style formatting
        for insight in prioritized[:max_insights]:
            insight = self._apply_wsj_presentation(insight)
        
        return prioritized[:max_insights]
    
    def _analyze_behavioral_patterns(self, user_data: Dict[str, pd.DataFrame]) -> List[HealthInsight]:
        """Analyze behavioral patterns with statistical rigor."""
        insights = []
        
        # Sleep consistency analysis
        if 'sleep_duration' in user_data:
            sleep_insight = self._analyze_sleep_consistency(user_data['sleep_duration'])
            if sleep_insight:
                insights.append(sleep_insight)
        
        # Activity pattern analysis
        if 'daily_steps' in user_data:
            activity_insight = self._analyze_activity_patterns(user_data['daily_steps'])
            if activity_insight:
                insights.append(activity_insight)
        
        # Recovery pattern analysis
        if 'resting_heart_rate' in user_data:
            recovery_insight = self._analyze_recovery_patterns(user_data['resting_heart_rate'])
            if recovery_insight:
                insights.append(recovery_insight)
        
        return insights
    
    def _analyze_sleep_consistency(self, sleep_data: pd.DataFrame) -> Optional[HealthInsight]:
        """Analyze sleep consistency patterns."""
        if len(sleep_data) < 7:
            return None
        
        # Calculate bedtime and wake time consistency
        if 'bedtime' in sleep_data.columns and 'wake_time' in sleep_data.columns:
            # Convert times to minutes from midnight for consistency calculation
            sleep_data = sleep_data.copy()
            sleep_data['bedtime_minutes'] = pd.to_datetime(sleep_data['bedtime']).dt.hour * 60 + pd.to_datetime(sleep_data['bedtime']).dt.minute
            sleep_data['wake_minutes'] = pd.to_datetime(sleep_data['wake_time']).dt.hour * 60 + pd.to_datetime(sleep_data['wake_time']).dt.minute
            
            bedtime_consistency = self.pattern_analyzer.calculate_consistency_score(
                sleep_data['bedtime_minutes'].dropna()
            )
            wake_consistency = self.pattern_analyzer.calculate_consistency_score(
                sleep_data['wake_minutes'].dropna()
            )
            
            overall_consistency = (bedtime_consistency + wake_consistency) / 2
        else:
            # Use duration consistency as fallback
            overall_consistency = self.pattern_analyzer.calculate_consistency_score(
                sleep_data['duration'].dropna() if 'duration' in sleep_data.columns else sleep_data.iloc[:, 0].dropna()
            )
        
        if overall_consistency < 0.7:  # Evidence threshold for concern
            evidence = self.evidence_db.get_evidence_for_insight(
                InsightCategory.SLEEP, 'sleep_consistency'
            )
            
            # Calculate variability statistics
            sleep_values = sleep_data['duration'] if 'duration' in sleep_data.columns else sleep_data.iloc[:, 0]
            variability_minutes = sleep_values.std() * 60  # Convert hours to minutes
            
            insight = HealthInsight(
                category=InsightCategory.SLEEP,
                insight_type=InsightType.PATTERN,
                title='Your Sleep Schedule Varies Significantly',
                summary=f'Your sleep times vary by about {variability_minutes:.0f} minutes, which may affect sleep quality.',
                description=f'Analysis of your sleep patterns over the past {len(sleep_data)} days shows significant variability. Consistent sleep-wake times help regulate your circadian rhythm, leading to better sleep quality and daytime alertness.',
                recommendation='Try going to bed and waking up within 30 minutes of the same time daily, even on weekends.',
                evidence_level=evidence.evidence_quality if evidence else EvidenceLevel.PATTERN_BASED,
                evidence_sources=[evidence.source_name] if evidence else ['Personal Pattern Analysis'],
                confidence=85.0,
                priority=Priority.HIGH,
                impact_potential=ImpactPotential.HIGH,
                achievability=Achievability.MODERATE,
                timeframe=Timeframe.SHORT_TERM,
                supporting_data={
                    'consistency_score': overall_consistency,
                    'variability_minutes': variability_minutes,
                    'days_analyzed': len(sleep_data)
                },
                medical_disclaimer='',
                evidence_details=[evidence] if evidence else []
            )
            
            return insight
        
        return None
    
    def _analyze_activity_patterns(self, activity_data: pd.DataFrame) -> Optional[HealthInsight]:
        """Analyze activity patterns and compare to guidelines."""
        if len(activity_data) < 7:
            return None
        
        # Get daily steps or activity minutes
        if 'steps' in activity_data.columns:
            metric_column = 'steps'
            metric_name = 'daily_steps'
        elif 'active_minutes' in activity_data.columns:
            metric_column = 'active_minutes'
            metric_name = 'activity_minutes'
        else:
            metric_column = activity_data.columns[0]
            metric_name = 'activity'
        
        # Calculate average
        avg_value = activity_data[metric_column].mean()
        
        # Get recommendation
        recommendation = self.evidence_db.get_recommendation_value(
            InsightCategory.ACTIVITY, metric_name
        )
        
        if recommendation and 'general' in recommendation:
            target = recommendation['general'].get('steps', recommendation['general'].get('minutes', 8000))
            
            if avg_value < target * 0.8:  # More than 20% below target
                evidence = self.evidence_db.get_evidence_for_insight(
                    InsightCategory.ACTIVITY, metric_name
                )
                
                gap = target - avg_value
                gap_percent = (gap / target) * 100
                
                insight = HealthInsight(
                    category=InsightCategory.ACTIVITY,
                    insight_type=InsightType.OPPORTUNITY,
                    title=f'Opportunity to Increase Your Daily {metric_name.replace("_", " ").title()}',
                    summary=f'You\'re averaging {avg_value:.0f} {metric_name.replace("_", " ")}, which is {gap_percent:.0f}% below recommended levels.',
                    description=f'Your average of {avg_value:.0f} {metric_name.replace("_", " ")} over the past {len(activity_data)} days is below the recommended {target:.0f}. Increasing activity can improve cardiovascular health, mood, and energy levels.',
                    recommendation=f'Try adding a 15-minute walk after lunch to increase your daily total by about {gap/3:.0f} {metric_name.replace("_", " ")}.',
                    evidence_level=evidence.evidence_quality if evidence else EvidenceLevel.MODERATE,
                    evidence_sources=[evidence.source_name] if evidence else ['WHO Physical Activity Guidelines'],
                    confidence=90.0,
                    priority=Priority.HIGH if gap_percent > 30 else Priority.MEDIUM,
                    impact_potential=ImpactPotential.HIGH,
                    achievability=Achievability.MODERATE,
                    timeframe=Timeframe.SHORT_TERM,
                    supporting_data={
                        'current_average': avg_value,
                        'recommended_target': target,
                        'gap': gap,
                        'gap_percent': gap_percent
                    },
                    medical_disclaimer='',
                    evidence_details=[evidence] if evidence else []
                )
                
                return insight
        
        return None
    
    def _analyze_recovery_patterns(self, hr_data: pd.DataFrame) -> Optional[HealthInsight]:
        """Analyze recovery patterns from heart rate data."""
        if len(hr_data) < 14:
            return None
        
        # Analyze resting heart rate trend
        if 'resting_hr' in hr_data.columns:
            metric_column = 'resting_hr'
        else:
            metric_column = hr_data.columns[0]
        
        trend_info = self.pattern_analyzer.detect_trend(hr_data[metric_column].dropna())
        
        if trend_info['trend'] == 'increasing' and trend_info['confidence'] > 70:
            # Increasing RHR might indicate overtraining or stress
            current_avg = hr_data[metric_column].iloc[-7:].mean()
            previous_avg = hr_data[metric_column].iloc[-14:-7].mean()
            increase = current_avg - previous_avg
            
            insight = HealthInsight(
                category=InsightCategory.RECOVERY,
                insight_type=InsightType.CONCERN,
                title='Your Resting Heart Rate is Trending Upward',
                summary=f'Your resting heart rate has increased by {increase:.0f} bpm over the past two weeks.',
                description='An increasing resting heart rate can indicate accumulated fatigue, stress, or overtraining. Your body may need more recovery time.',
                recommendation='Consider adding an extra rest day this week and focus on stress management techniques.',
                evidence_level=EvidenceLevel.MODERATE,
                evidence_sources=['Sports Science Recovery Guidelines'],
                confidence=trend_info['confidence'],
                priority=Priority.MEDIUM,
                impact_potential=ImpactPotential.MEDIUM,
                achievability=Achievability.EASY,
                timeframe=Timeframe.IMMEDIATE,
                supporting_data={
                    'trend': trend_info['trend'],
                    'current_avg_rhr': current_avg,
                    'previous_avg_rhr': previous_avg,
                    'increase_bpm': increase
                },
                medical_disclaimer=''
            )
            
            return insight
        
        return None
    
    def _analyze_correlation_patterns(self, user_data: Dict[str, pd.DataFrame]) -> List[HealthInsight]:
        """Analyze correlations between different health metrics."""
        insights = []
        
        # Find significant correlations
        correlations = self.correlation_analyzer.find_significant_correlations(user_data)
        
        # Create insights for top correlations
        for corr in correlations[:3]:  # Top 3 correlations
            insight = self._create_correlation_insight(corr, user_data)
            if insight:
                insights.append(insight)
        
        return insights
    
    def _create_correlation_insight(self, correlation: Dict[str, Any],
                                  user_data: Dict[str, pd.DataFrame]) -> Optional[HealthInsight]:
        """Create insight from correlation finding."""
        metric1 = correlation['metric1']
        metric2 = correlation['metric2']
        corr_value = correlation['correlation']
        direction = correlation['direction']
        
        # Create meaningful description based on metrics
        if direction == 'positive':
            relationship = "increases with"
        else:
            relationship = "decreases as"
        
        title = f'Your {metric1.replace("_", " ").title()} {relationship.title()} Your {metric2.replace("_", " ").title()}'
        
        # Calculate impact of relationship
        impact_description = self._describe_correlation_impact(metric1, metric2, corr_value)
        
        insight = HealthInsight(
            category=InsightCategory.ACTIVITY,  # Default, would be smarter in real implementation
            insight_type=InsightType.CORRELATION,
            title=title,
            summary=f'Strong {direction} correlation ({abs(corr_value):.1%}) found between these metrics.',
            description=f'Analysis of {correlation["sample_size"]} data points shows that your {metric1} {relationship} your {metric2}. {impact_description}',
            recommendation=f'Use this relationship to your advantage by optimizing your {metric1} to positively influence your {metric2}.',
            evidence_level=EvidenceLevel.PATTERN_BASED,
            evidence_sources=['Statistical Analysis of Personal Data'],
            confidence=min(100, abs(corr_value) * 100),
            priority=Priority.MEDIUM if abs(corr_value) > 0.5 else Priority.LOW,
            impact_potential=ImpactPotential.MEDIUM,
            achievability=Achievability.MODERATE,
            timeframe=Timeframe.SHORT_TERM,
            supporting_data={
                'correlation_coefficient': corr_value,
                'p_value': correlation['p_value'],
                'sample_size': correlation['sample_size']
            },
            medical_disclaimer=''
        )
        
        return insight
    
    def _describe_correlation_impact(self, metric1: str, metric2: str, 
                                   correlation: float) -> str:
        """Generate impact description for correlation."""
        strength = abs(correlation)
        
        if strength > 0.7:
            impact = "This strong relationship suggests that changes in one directly affect the other."
        elif strength > 0.5:
            impact = "This moderate relationship indicates these metrics influence each other."
        else:
            impact = "While statistically significant, this relationship is relatively weak."
        
        return impact
    
    def _analyze_trend_patterns(self, user_data: Dict[str, pd.DataFrame]) -> List[HealthInsight]:
        """Analyze trends in health metrics."""
        insights = []
        
        for metric_name, data in user_data.items():
            if len(data) < 7:
                continue
            
            # Determine value column
            value_cols = [c for c in data.columns if c != 'date']
            if not value_cols:
                continue
            
            trend_result = self.trend_analyzer.analyze_metric_trends(
                data, metric_name, value_cols[0]
            )
            
            if trend_result and trend_result['statistical_significance']:
                insight = self._create_trend_insight(metric_name, trend_result)
                if insight:
                    insights.append(insight)
        
        return insights
    
    def _create_trend_insight(self, metric_name: str, 
                            trend_info: Dict[str, Any]) -> Optional[HealthInsight]:
        """Create insight from trend analysis."""
        trend = trend_info['trend']
        percent_change = trend_info['percent_change']
        
        if trend == 'stable':
            return None
        
        # Determine if trend is positive or concerning
        positive_metrics = ['steps', 'active_minutes', 'exercise_minutes', 'standing_hours']
        negative_metrics = ['weight', 'resting_hr', 'blood_pressure']
        
        is_positive = (
            (trend == 'increasing' and metric_name in positive_metrics) or
            (trend == 'decreasing' and metric_name in negative_metrics)
        )
        
        if is_positive:
            insight_type = InsightType.ACHIEVEMENT
            priority = Priority.LOW
            title = f'Great Progress: Your {metric_name.replace("_", " ").title()} is Improving'
        else:
            insight_type = InsightType.CONCERN
            priority = Priority.HIGH
            title = f'Attention Needed: Your {metric_name.replace("_", " ").title()} is {trend.title()}'
        
        insight = HealthInsight(
            category=self._determine_category(metric_name),
            insight_type=insight_type,
            title=title,
            summary=f'{abs(percent_change):.0f}% change over the past {trend_info["days_analyzed"]} days.',
            description=f'Your {metric_name} has {trend} from {trend_info["start_value"]:.1f} to {trend_info["end_value"]:.1f}.',
            recommendation=self._generate_trend_recommendation(metric_name, trend, is_positive),
            evidence_level=EvidenceLevel.PATTERN_BASED,
            evidence_sources=['Trend Analysis'],
            confidence=trend_info['confidence'],
            priority=priority,
            impact_potential=ImpactPotential.HIGH if abs(percent_change) > 20 else ImpactPotential.MEDIUM,
            achievability=Achievability.MODERATE,
            timeframe=Timeframe.SHORT_TERM,
            supporting_data=trend_info,
            medical_disclaimer=''
        )
        
        return insight
    
    def _determine_category(self, metric_name: str) -> InsightCategory:
        """Determine category based on metric name."""
        category_map = {
            'sleep': InsightCategory.SLEEP,
            'steps': InsightCategory.ACTIVITY,
            'active': InsightCategory.ACTIVITY,
            'exercise': InsightCategory.ACTIVITY,
            'heart': InsightCategory.HEART_HEALTH,
            'hr': InsightCategory.HEART_HEALTH,
            'weight': InsightCategory.BODY_METRICS,
            'bmi': InsightCategory.BODY_METRICS
        }
        
        metric_lower = metric_name.lower()
        for key, category in category_map.items():
            if key in metric_lower:
                return category
        
        return InsightCategory.ACTIVITY  # Default
    
    def _generate_trend_recommendation(self, metric_name: str, 
                                     trend: str, is_positive: bool) -> str:
        """Generate recommendation based on trend."""
        if is_positive:
            return f"Keep up the great work! Continue your current routine to maintain this positive trend."
        else:
            if 'sleep' in metric_name:
                return "Try establishing a consistent bedtime routine and limiting screen time before bed."
            elif 'steps' in metric_name or 'active' in metric_name:
                return "Consider setting hourly movement reminders and taking short walks throughout the day."
            elif 'weight' in metric_name:
                return "Review your recent dietary and activity patterns. Small, consistent changes can reverse this trend."
            else:
                return "Monitor this trend and consider consulting with healthcare providers if it continues."
    
    def _identify_goal_opportunities(self, user_data: Dict[str, pd.DataFrame]) -> List[HealthInsight]:
        """Identify opportunities for setting and achieving health goals."""
        insights = []
        
        # Analyze each metric for goal opportunities
        for metric_name, data in user_data.items():
            if len(data) < 7:
                continue
            
            # Get current baseline
            value_cols = [c for c in data.columns if c != 'date']
            if not value_cols:
                continue
            
            current_value = data[value_cols[0]].iloc[-7:].mean()
            
            # Generate goal
            category = self._determine_category(metric_name)
            goal = self.goal_optimizer.generate_goal(
                metric_name, current_value, category
            )
            
            if goal and abs(goal.recommended_target - current_value) > current_value * 0.1:
                # Create insight for significant goal opportunity
                insight = self._create_goal_insight(metric_name, goal, category)
                insights.append(insight)
        
        return insights
    
    def _create_goal_insight(self, metric_name: str, 
                           goal: PersonalizedGoal,
                           category: InsightCategory) -> HealthInsight:
        """Create insight from goal opportunity."""
        gap = goal.recommended_target - goal.current_baseline
        gap_percent = abs(gap / goal.current_baseline * 100) if goal.current_baseline > 0 else 100
        
        if gap > 0:
            direction = "increase"
        else:
            direction = "decrease"
        
        insight = HealthInsight(
            category=category,
            insight_type=InsightType.OPPORTUNITY,
            title=f'Goal Opportunity: {direction.title()} Your {metric_name.replace("_", " ").title()}',
            summary=f'You could {direction} from {goal.current_baseline:.1f} to {goal.recommended_target:.1f} based on health guidelines.',
            description=f'{goal.rationale} Achieving this goal could significantly improve your health outcomes.',
            recommendation=f'Start with small changes: {goal.milestones[0]["description"] if goal.milestones else "gradual improvement"}.',
            evidence_level=goal.evidence_basis.evidence_quality if goal.evidence_basis else EvidenceLevel.MODERATE,
            evidence_sources=[goal.evidence_basis.source_name] if goal.evidence_basis else ['Health Guidelines'],
            confidence=goal.confidence_score,
            priority=Priority.MEDIUM,
            impact_potential=ImpactPotential.HIGH if gap_percent > 25 else ImpactPotential.MEDIUM,
            achievability=Achievability.MODERATE,
            timeframe=Timeframe.LONG_TERM if gap_percent > 30 else Timeframe.SHORT_TERM,
            supporting_data={
                'current_baseline': goal.current_baseline,
                'recommended_target': goal.recommended_target,
                'gap': gap,
                'gap_percent': gap_percent,
                'timeline': goal.timeline,
                'milestones': goal.milestones
            },
            medical_disclaimer='',
            evidence_details=[goal.evidence_basis] if goal.evidence_basis else []
        )
        
        return insight
    
    def _validate_and_enhance_insight(self, insight: HealthInsight) -> Optional[HealthInsight]:
        """Validate insight against evidence database and enhance with medical context."""
        # Use medical evidence validator
        validated_insight = self.evidence_validator.ensure_medical_safety(insight)
        
        # Additional validation
        if validated_insight.confidence < 50:
            return None  # Skip low confidence insights
        
        return validated_insight
    
    def _prioritize_insights(self, insights: List[HealthInsight]) -> List[HealthInsight]:
        """Prioritize insights based on multiple factors."""
        # Calculate priority scores
        for insight in insights:
            score = 0
            
            # Priority weight (0-30)
            if insight.priority == Priority.HIGH:
                score += 30
            elif insight.priority == Priority.MEDIUM:
                score += 20
            else:
                score += 10
            
            # Evidence weight (0-20)
            if insight.evidence_level == EvidenceLevel.STRONG:
                score += 20
            elif insight.evidence_level == EvidenceLevel.MODERATE:
                score += 15
            elif insight.evidence_level == EvidenceLevel.WEAK:
                score += 10
            else:
                score += 5
            
            # Impact weight (0-20)
            if insight.impact_potential == ImpactPotential.HIGH:
                score += 20
            elif insight.impact_potential == ImpactPotential.MEDIUM:
                score += 10
            else:
                score += 5
            
            # Achievability weight (0-20)
            if insight.achievability == Achievability.EASY:
                score += 20
            elif insight.achievability == Achievability.MODERATE:
                score += 15
            else:
                score += 10
            
            # Confidence weight (0-10)
            score += insight.confidence / 10
            
            # Store score
            insight.supporting_data['priority_score'] = score
        
        # Sort by priority score
        return sorted(insights, 
                     key=lambda i: i.supporting_data.get('priority_score', 0),
                     reverse=True)
    
    def _apply_wsj_presentation(self, insight: HealthInsight) -> HealthInsight:
        """Apply WSJ design principles to insight presentation."""
        return self.style_manager.apply_wsj_styling(insight)
    
    def generate_weekly_summary(self, insights: List[HealthInsight]) -> str:
        """Generate WSJ-style weekly health summary."""
        if not insights:
            return "No significant health patterns detected this week."
        
        # Group by priority and category
        high_priority = [i for i in insights if i.priority == Priority.HIGH]
        
        summary = "**Your Health This Week**\n\n"
        
        if high_priority:
            summary += f"**Key Finding**: {high_priority[0].title}\n"
            summary += f"{high_priority[0].summary}\n\n"
            
            if len(high_priority) > 1:
                summary += "**Other Important Patterns:**\n"
                for insight in high_priority[1:3]:  # Top 3 total
                    summary += f"• {insight.title}\n"
                summary += "\n"
        
        # Add evidence transparency
        evidence_counts = self._count_evidence_levels(insights)
        summary += f"*Based on {evidence_counts['strong']} evidence-based insights "
        summary += f"and {evidence_counts['pattern_based']} personal patterns.*\n\n"
        
        # Medical disclaimer
        summary += "*This analysis is for informational purposes only and does not constitute medical advice.*"
        
        return summary
    
    def _count_evidence_levels(self, insights: List[HealthInsight]) -> Dict[str, int]:
        """Count insights by evidence level."""
        counts = {
            'strong': 0,
            'moderate': 0,
            'weak': 0,
            'pattern_based': 0
        }
        
        for insight in insights:
            if insight.evidence_level == EvidenceLevel.STRONG:
                counts['strong'] += 1
            elif insight.evidence_level == EvidenceLevel.MODERATE:
                counts['moderate'] += 1
            elif insight.evidence_level == EvidenceLevel.WEAK:
                counts['weak'] += 1
            else:
                counts['pattern_based'] += 1
        
        return counts
    
    def generate_insight_batch(self, user_data: Dict[str, pd.DataFrame],
                             start_date: datetime,
                             end_date: datetime,
                             time_period: str = "weekly") -> InsightBatch:
        """Generate a batch of insights for a specific time period."""
        insights = self.generate_prioritized_insights(user_data, time_period)
        
        batch = InsightBatch(
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            insights=insights
        )
        
        # Generate summary
        batch.summary = self.generate_weekly_summary(insights)
        
        return batch