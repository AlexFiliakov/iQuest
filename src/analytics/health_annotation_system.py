"""Health Insight Annotation System

Generates intelligent annotations for health visualizations by analyzing data patterns,
detecting anomalies, tracking achievements, and providing contextual insights.
"""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QPointF

from .annotation_models import (
    HealthAnnotation, AnomalyAnnotation, AchievementAnnotation,
    TrendAnnotation, InsightAnnotation, MilestoneAnnotation,
    ComparisonAnnotation, GoalAnnotation,
    AnnotationType, AnnotationPriority, TrendDirection
)
from .anomaly_detection_system import AnomalyDetectionSystem
from .personal_records_tracker import PersonalRecordsTracker
from .health_insights_engine import HealthInsightsEngine
from .goal_management_system import GoalManagementSystem
from ..analytics import AdvancedTrendEngine
from ..models import HealthMetric


class HealthAnnotationSystem(QObject):
    """Intelligent annotation system for health visualizations"""
    
    # Signals
    annotations_generated = pyqtSignal(list)  # List[HealthAnnotation]
    annotation_clicked = pyqtSignal(str)  # annotation_id
    annotation_hovered = pyqtSignal(str, bool)  # annotation_id, entered
    
    def __init__(self):
        super().__init__()
        
        # Initialize subsystems
        self.anomaly_detector = AnomalyDetectionSystem()
        self.records_tracker = PersonalRecordsTracker()
        self.insights_engine = HealthInsightsEngine()
        self.goal_system = GoalManagementSystem()
        self.trend_engine = AdvancedTrendEngine()
        
        # Configuration
        self.max_annotations_per_chart = 10
        self.min_annotation_spacing_days = 7
        self.priority_threshold = AnnotationPriority.MEDIUM
        
        # Cache for performance
        self._annotation_cache: Dict[str, List[HealthAnnotation]] = {}
    
    def generate_annotations(self, 
                           data: pd.DataFrame, 
                           metric_type: str,
                           date_range: Optional[Tuple[datetime, datetime]] = None,
                           annotation_types: Optional[List[AnnotationType]] = None) -> List[HealthAnnotation]:
        """Generate relevant annotations for health data
        
        Args:
            data: Health data DataFrame with 'date' and 'value' columns
            metric_type: Type of health metric
            date_range: Optional date range to focus on
            annotation_types: Optional list of annotation types to generate
            
        Returns:
            List of health annotations sorted by priority and date
        """
        if data.empty:
            return []
            
        # Check cache
        cache_key = self._generate_cache_key(data, metric_type, date_range)
        if cache_key in self._annotation_cache:
            return self._annotation_cache[cache_key]
        
        # Filter data by date range if provided
        if date_range:
            mask = (data['date'] >= date_range[0]) & (data['date'] <= date_range[1])
            data = data[mask].copy()
        
        # Determine which annotation types to generate
        if annotation_types is None:
            annotation_types = list(AnnotationType)
        
        annotations = []
        
        # Generate each type of annotation
        if AnnotationType.ANOMALY in annotation_types:
            annotations.extend(self._generate_anomaly_annotations(data, metric_type))
            
        if AnnotationType.ACHIEVEMENT in annotation_types:
            annotations.extend(self._generate_achievement_annotations(data, metric_type))
            
        if AnnotationType.TREND in annotation_types:
            annotations.extend(self._generate_trend_annotations(data, metric_type))
            
        if AnnotationType.INSIGHT in annotation_types:
            annotations.extend(self._generate_insight_annotations(data, metric_type))
            
        if AnnotationType.MILESTONE in annotation_types:
            annotations.extend(self._generate_milestone_annotations(data, metric_type))
            
        if AnnotationType.COMPARISON in annotation_types:
            annotations.extend(self._generate_comparison_annotations(data, metric_type))
            
        if AnnotationType.GOAL in annotation_types:
            annotations.extend(self._generate_goal_annotations(data, metric_type))
        
        # Post-process annotations
        annotations = self._prioritize_annotations(annotations)
        annotations = self._prevent_overlap(annotations)
        annotations = self._limit_annotations(annotations)
        
        # Cache results
        self._annotation_cache[cache_key] = annotations
        
        # Emit signal
        self.annotations_generated.emit(annotations)
        
        return annotations
    
    def _generate_anomaly_annotations(self, data: pd.DataFrame, metric_type: str) -> List[AnomalyAnnotation]:
        """Generate anomaly annotations using the anomaly detection system"""
        annotations = []
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(
            data=data,
            metric_type=metric_type,
            sensitivity=0.8
        )
        
        for anomaly in anomalies:
            if anomaly.severity >= 0.7:  # Only high severity anomalies
                annotation = AnomalyAnnotation(
                    id=f"anomaly_{anomaly.timestamp.timestamp()}",
                    data_point=anomaly.timestamp,
                    value=anomaly.value,
                    severity=anomaly.severity,
                    anomaly_type=anomaly.anomaly_type,
                    expected_range=(anomaly.lower_bound, anomaly.upper_bound),
                    deviation_percent=anomaly.deviation_score * 100,
                    priority=self._calculate_anomaly_priority(anomaly),
                    title=self._generate_anomaly_title(anomaly),
                    description=self._generate_anomaly_description(anomaly, metric_type)
                )
                annotations.append(annotation)
        
        return annotations
    
    def _generate_achievement_annotations(self, data: pd.DataFrame, metric_type: str) -> List[AchievementAnnotation]:
        """Generate achievement annotations for personal records and milestones"""
        annotations = []
        
        # Check for personal records
        records = self.records_tracker.find_records(
            data=data,
            metric_type=metric_type,
            lookback_days=365
        )
        
        for record in records:
            annotation = AchievementAnnotation(
                id=f"achievement_{record.date.timestamp()}",
                data_point=record.date,
                value=record.value,
                achievement_type=record.record_type,
                previous_best=record.previous_value,
                improvement_percent=record.improvement_percent,
                streak_days=record.streak_days,
                priority=AnnotationPriority.HIGH,
                title=self._generate_achievement_title(record),
                description=self._generate_achievement_description(record, metric_type)
            )
            annotations.append(annotation)
        
        return annotations
    
    def _generate_trend_annotations(self, data: pd.DataFrame, metric_type: str) -> List[TrendAnnotation]:
        """Generate trend annotations for significant patterns"""
        annotations = []
        
        # Analyze trends
        trends = self.trend_engine.analyze_trends(
            data=data,
            metric_type=metric_type,
            min_confidence=0.8
        )
        
        for trend in trends:
            if trend.is_significant:
                annotation = TrendAnnotation(
                    id=f"trend_{trend.start_date.timestamp()}",
                    data_point=trend.midpoint_date,
                    value=trend.midpoint_value,
                    trend_direction=self._map_trend_direction(trend.direction),
                    trend_start=trend.start_date,
                    trend_end=trend.end_date,
                    confidence=trend.confidence,
                    slope=trend.slope,
                    change_percent=trend.percent_change,
                    priority=self._calculate_trend_priority(trend),
                    title=self._generate_trend_title(trend),
                    description=self._generate_trend_description(trend, metric_type)
                )
                annotations.append(annotation)
        
        return annotations
    
    def _generate_insight_annotations(self, data: pd.DataFrame, metric_type: str) -> List[InsightAnnotation]:
        """Generate contextual insight annotations"""
        annotations = []
        
        # Generate insights
        insights = self.insights_engine.generate_insights(
            data=data,
            metric_type=metric_type,
            context='visualization'
        )
        
        # Limit to top insights
        for insight in insights[:3]:
            # Find the most relevant data point for the insight
            relevant_date = self._find_insight_focal_point(data, insight)
            
            annotation = InsightAnnotation(
                id=f"insight_{insight.id}",
                data_point=relevant_date,
                value=data.loc[data['date'] == relevant_date, 'value'].iloc[0],
                insight_category=insight.category,
                confidence=insight.confidence,
                related_metrics=insight.related_metrics,
                recommendation=insight.recommendation,
                priority=self._calculate_insight_priority(insight),
                title=insight.title,
                description=insight.description
            )
            annotations.append(annotation)
        
        return annotations
    
    def _generate_milestone_annotations(self, data: pd.DataFrame, metric_type: str) -> List[MilestoneAnnotation]:
        """Generate milestone annotations for significant achievements"""
        annotations = []
        
        # Define milestones based on metric type
        milestones = self._get_metric_milestones(metric_type)
        
        for milestone in milestones:
            # Check if milestone was achieved in this data
            achieved_dates = data[data['value'] >= milestone['target']]['date']
            
            if not achieved_dates.empty:
                first_achievement = achieved_dates.iloc[0]
                
                # Calculate days to achieve (from start of data)
                days_to_achieve = (first_achievement - data['date'].iloc[0]).days
                
                annotation = MilestoneAnnotation(
                    id=f"milestone_{milestone['name']}_{first_achievement.timestamp()}",
                    data_point=first_achievement,
                    value=data.loc[data['date'] == first_achievement, 'value'].iloc[0],
                    milestone_type=milestone['name'],
                    days_to_achieve=days_to_achieve,
                    target_value=milestone['target'],
                    priority=AnnotationPriority.HIGH,
                    title=f"{milestone['name']} Milestone!",
                    description=milestone['description']
                )
                annotations.append(annotation)
        
        return annotations
    
    def _generate_comparison_annotations(self, data: pd.DataFrame, metric_type: str) -> List[ComparisonAnnotation]:
        """Generate comparison annotations against averages and norms"""
        annotations = []
        
        # Calculate rolling averages and comparisons
        data['rolling_avg'] = data['value'].rolling(window=30, min_periods=7).mean()
        data['percentile'] = data['value'].rank(pct=True) * 100
        
        # Find exceptional days (top/bottom 5%)
        exceptional_high = data[data['percentile'] >= 95]
        exceptional_low = data[data['percentile'] <= 5]
        
        for _, row in exceptional_high.iterrows():
            annotation = ComparisonAnnotation(
                id=f"comparison_high_{row['date'].timestamp()}",
                data_point=row['date'],
                value=row['value'],
                comparison_type="personal_best",
                comparison_value=data['value'].mean(),
                difference_percent=((row['value'] - data['value'].mean()) / data['value'].mean()) * 100,
                better_than_percent=row['percentile'],
                priority=AnnotationPriority.MEDIUM,
                title="Exceptional Performance",
                description=f"Top {100 - row['percentile']:.0f}% of all recorded days"
            )
            annotations.append(annotation)
        
        return annotations
    
    def _generate_goal_annotations(self, data: pd.DataFrame, metric_type: str) -> List[GoalAnnotation]:
        """Generate goal-related annotations"""
        annotations = []
        
        # Get active goals for this metric
        goals = self.goal_system.get_active_goals(metric_type=metric_type)
        
        for goal in goals:
            # Find most recent data point
            latest_date = data['date'].max()
            latest_value = data.loc[data['date'] == latest_date, 'value'].iloc[0]
            
            # Calculate progress
            progress = self.goal_system.calculate_goal_progress(goal, latest_value)
            
            if progress.milestone_reached or progress.is_complete:
                annotation = GoalAnnotation(
                    id=f"goal_{goal.id}_{latest_date.timestamp()}",
                    data_point=latest_date,
                    value=latest_value,
                    goal_name=goal.name,
                    target_value=goal.target_value,
                    progress_percent=progress.percent_complete,
                    days_remaining=progress.days_remaining,
                    on_track=progress.on_track,
                    priority=AnnotationPriority.HIGH if progress.is_complete else AnnotationPriority.MEDIUM,
                    title=f"Goal {'Achieved' if progress.is_complete else 'Progress'}: {goal.name}",
                    description=progress.message
                )
                annotations.append(annotation)
        
        return annotations
    
    def _calculate_anomaly_priority(self, anomaly) -> AnnotationPriority:
        """Calculate priority for anomaly annotations"""
        if anomaly.severity >= 0.9:
            return AnnotationPriority.CRITICAL
        elif anomaly.severity >= 0.8:
            return AnnotationPriority.HIGH
        elif anomaly.severity >= 0.6:
            return AnnotationPriority.MEDIUM
        else:
            return AnnotationPriority.LOW
    
    def _calculate_trend_priority(self, trend) -> AnnotationPriority:
        """Calculate priority for trend annotations"""
        if abs(trend.percent_change) >= 20 and trend.confidence >= 0.9:
            return AnnotationPriority.HIGH
        elif abs(trend.percent_change) >= 10 and trend.confidence >= 0.8:
            return AnnotationPriority.MEDIUM
        else:
            return AnnotationPriority.LOW
    
    def _calculate_insight_priority(self, insight) -> AnnotationPriority:
        """Calculate priority for insight annotations"""
        if insight.actionability >= 0.8:
            return AnnotationPriority.HIGH
        elif insight.actionability >= 0.6:
            return AnnotationPriority.MEDIUM
        else:
            return AnnotationPriority.LOW
    
    def _generate_anomaly_title(self, anomaly) -> str:
        """Generate title for anomaly annotation"""
        if anomaly.anomaly_type == "spike":
            return "Unusual Spike Detected"
        elif anomaly.anomaly_type == "drop":
            return "Unusual Drop Detected"
        elif anomaly.anomaly_type == "pattern":
            return "Unusual Pattern"
        else:
            return "Anomaly Detected"
    
    def _generate_anomaly_description(self, anomaly, metric_type: str) -> str:
        """Generate description for anomaly annotation"""
        deviation_text = f"{abs(anomaly.deviation_score * 100):.0f}%"
        direction = "above" if anomaly.value > anomaly.upper_bound else "below"
        
        return (f"This {metric_type} reading is {deviation_text} {direction} "
                f"the expected range based on your historical patterns.")
    
    def _generate_achievement_title(self, record) -> str:
        """Generate title for achievement annotation"""
        if record.record_type == "all_time_best":
            return "🏆 New Personal Record!"
        elif record.record_type == "monthly_best":
            return "⭐ Best This Month!"
        elif record.record_type == "weekly_best":
            return "✨ Best This Week!"
        elif record.record_type == "streak":
            return f"🔥 {record.streak_days} Day Streak!"
        else:
            return "New Achievement!"
    
    def _generate_achievement_description(self, record, metric_type: str) -> str:
        """Generate description for achievement annotation"""
        if record.previous_value:
            improvement = f"{record.improvement_percent:.0f}% improvement"
            return f"You've set a new {record.record_type.replace('_', ' ')} for {metric_type}! {improvement} from your previous best."
        else:
            return f"Congratulations on setting a new {record.record_type.replace('_', ' ')} for {metric_type}!"
    
    def _generate_trend_title(self, trend) -> str:
        """Generate title for trend annotation"""
        direction = "Improving" if trend.direction > 0 else "Declining"
        return f"{direction} Trend"
    
    def _generate_trend_description(self, trend, metric_type: str) -> str:
        """Generate description for trend annotation"""
        days = (trend.end_date - trend.start_date).days
        change = f"{abs(trend.percent_change):.0f}%"
        direction = "improved" if trend.direction > 0 else "declined"
        
        return f"Your {metric_type} has {direction} by {change} over the past {days} days."
    
    def _map_trend_direction(self, direction: float) -> TrendDirection:
        """Map numeric trend direction to enum"""
        if direction > 0.1:
            return TrendDirection.IMPROVING
        elif direction < -0.1:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _find_insight_focal_point(self, data: pd.DataFrame, insight) -> datetime:
        """Find the most relevant date for an insight annotation"""
        # Default to most recent date
        if hasattr(insight, 'focal_date') and insight.focal_date:
            return insight.focal_date
        else:
            return data['date'].max()
    
    def _get_metric_milestones(self, metric_type: str) -> List[Dict[str, Any]]:
        """Get predefined milestones for a metric type"""
        # This would be configured based on metric type
        # Example milestones
        milestones = {
            'steps': [
                {'name': '10K Steps', 'target': 10000, 'description': 'You walked 10,000 steps in a day!'},
                {'name': '15K Steps', 'target': 15000, 'description': 'Amazing! 15,000 steps in a single day!'},
                {'name': '20K Steps', 'target': 20000, 'description': 'Incredible achievement - 20,000 steps!'},
            ],
            'heart_rate': [
                {'name': 'Resting HR < 60', 'target': 60, 'description': 'Excellent cardiovascular fitness!'},
                {'name': 'Resting HR < 55', 'target': 55, 'description': 'Athletic-level resting heart rate!'},
            ]
        }
        
        return milestones.get(metric_type, [])
    
    def _prioritize_annotations(self, annotations: List[HealthAnnotation]) -> List[HealthAnnotation]:
        """Sort annotations by priority and date"""
        return sorted(annotations, 
                     key=lambda a: (a.priority.value, a.data_point), 
                     reverse=True)
    
    def _prevent_overlap(self, annotations: List[HealthAnnotation]) -> List[HealthAnnotation]:
        """Filter annotations to prevent temporal overlap"""
        if not annotations:
            return annotations
        
        filtered = [annotations[0]]
        
        for annotation in annotations[1:]:
            # Check if too close to any existing annotation
            too_close = False
            for existing in filtered:
                days_apart = abs((annotation.data_point - existing.data_point).days)
                if days_apart < self.min_annotation_spacing_days:
                    # Keep the higher priority one
                    if annotation.priority.value > existing.priority.value:
                        filtered.remove(existing)
                        filtered.append(annotation)
                    too_close = True
                    break
            
            if not too_close:
                filtered.append(annotation)
        
        return filtered
    
    def _limit_annotations(self, annotations: List[HealthAnnotation]) -> List[HealthAnnotation]:
        """Limit the number of annotations per chart"""
        # Keep only annotations above threshold
        filtered = [a for a in annotations if a.priority.value >= self.priority_threshold.value]
        
        # Limit to max number
        return filtered[:self.max_annotations_per_chart]
    
    def _generate_cache_key(self, data: pd.DataFrame, metric_type: str, 
                           date_range: Optional[Tuple[datetime, datetime]]) -> str:
        """Generate cache key for annotation results"""
        data_hash = hash(tuple(data['value'].values))
        date_str = f"{date_range[0]}_{date_range[1]}" if date_range else "all"
        return f"{metric_type}_{data_hash}_{date_str}"
    
    def clear_cache(self):
        """Clear annotation cache"""
        self._annotation_cache.clear()
    
    def get_annotation_by_id(self, annotation_id: str) -> Optional[HealthAnnotation]:
        """Get a specific annotation by ID"""
        for annotations in self._annotation_cache.values():
            for annotation in annotations:
                if annotation.id == annotation_id:
                    return annotation
        return None