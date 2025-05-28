"""
Data Story Generator for creating narrative insights from health data.
Generates weekly recaps, monthly journeys, yearly reviews, and milestone celebrations.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import logging
from abc import ABC, abstractmethod

from .daily_metrics_calculator import DailyMetricsCalculator
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator
from .personal_records_tracker import PersonalRecordsTracker
from .correlation_analyzer import CorrelationAnalyzer
from .seasonal_pattern_analyzer import SeasonalPatternAnalyzer

logger = logging.getLogger(__name__)


class StoryType(Enum):
    """Types of stories that can be generated."""
    WEEKLY_RECAP = "weekly_recap"
    MONTHLY_JOURNEY = "monthly_journey"
    YEAR_IN_REVIEW = "year_in_review"
    MILESTONE_CELEBRATION = "milestone_celebration"


class ToneType(Enum):
    """Available tone options for story generation."""
    ENCOURAGING = "encouraging"
    NEUTRAL = "neutral"
    MOTIVATING = "motivating"
    CELEBRATORY = "celebratory"


@dataclass
class UserProfile:
    """User preferences and profile for story personalization."""
    name: Optional[str] = None
    preferred_tone: ToneType = ToneType.ENCOURAGING
    metric_priorities: List[str] = field(default_factory=list)
    communication_style: str = "casual"  # casual, formal
    name_usage: bool = True
    email_enabled: bool = False
    push_enabled: bool = False
    preferred_delivery_time: Optional[str] = None  # e.g., "09:00"


@dataclass
class Achievement:
    """Represents a health achievement."""
    type: str  # personal_record, streak, goal_met, improvement
    metric: str
    value: float
    context: str
    significance: float  # 0-1 score
    date: datetime


@dataclass
class Insight:
    """Represents a data-driven insight."""
    text: str
    category: str  # pattern, correlation, trend
    importance: float  # 0-1 score
    visual_hint: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None


@dataclass
class Recommendation:
    """Actionable recommendation based on data analysis."""
    action: str
    rationale: str
    category: str  # goal_support, goal_achievement, improvement
    difficulty: str  # easy, medium, hard
    success_probability: Optional[float] = None


@dataclass
class Story:
    """Complete generated story with metadata."""
    title: str
    text: str
    type: StoryType
    sections: Dict[str, str]
    insights: List[Insight]
    recommendations: List[Recommendation]
    metadata: Optional['StoryMetadata'] = None


@dataclass
class StoryMetadata:
    """Metadata about a generated story."""
    type: str
    generated_at: datetime
    data_period: Dict[str, Any]
    word_count: int
    tone: ToneType
    personalization_applied: bool = True


@dataclass
class WeekAnalysis:
    """Analysis results for a week of data."""
    achievements: List[Achievement]
    comparisons: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    challenges: List[Dict[str, Any]]
    highlights: List[Dict[str, Any]]
    progress: Dict[str, Any]
    summary_phrase: str
    top_achievement: Optional[Achievement] = None
    overall_improvement: float = 0.0
    is_exceptional_week: bool = False
    shows_improvement: bool = False
    shows_consistency: bool = False


class DataStoryGenerator:
    """Main class for generating data stories from health metrics."""
    
    def __init__(
        self,
        user_profile: UserProfile,
        daily_calculator: Optional[DailyMetricsCalculator] = None,
        weekly_calculator: Optional[WeeklyMetricsCalculator] = None,
        monthly_calculator: Optional[MonthlyMetricsCalculator] = None
    ):
        self.user_profile = user_profile
        self.template_engine = StoryTemplateEngine()
        self.insight_generator = InsightGenerator()
        self.tone_manager = ToneManager(user_profile.preferred_tone)
        self.preference_learner = PreferenceLearner()
        self.recommendation_engine = RecommendationEngine()
        
        # Calculator instances
        self.daily_calculator = daily_calculator
        self.weekly_calculator = weekly_calculator
        self.monthly_calculator = monthly_calculator
        
        # Additional analyzers
        self.records_tracker = PersonalRecordsTracker()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.pattern_analyzer = SeasonalPatternAnalyzer()
        
    def generate_weekly_recap(self, week_data: Dict[str, Any]) -> Story:
        """Generate weekly recap story."""
        try:
            # Analyze week data
            analysis = self.analyze_week(week_data)
            
            # Select narrative structure
            structure = self.select_weekly_structure(analysis)
            
            # Generate story sections
            sections = {
                'opening': self.generate_opening(analysis, 'weekly'),
                'achievements': self.generate_achievements_section(analysis),
                'comparison': self.generate_comparison_section(analysis),
                'insights': self.generate_insights_section(analysis),
                'recommendations': self.generate_recommendations_section(analysis),
                'closing': self.generate_closing(analysis, 'weekly')
            }
            
            # Apply tone
            sections = self.tone_manager.apply_tone(sections)
            
            # Extract insights and recommendations for structured data
            insights = self.insight_generator.generate_insights(week_data)
            recommendations = self.recommendation_engine.generate_recommendations(
                analysis, self.user_profile
            )
            
            # Assemble story
            story = self.assemble_story(sections, structure)
            
            # Add metadata
            story.metadata = StoryMetadata(
                type=StoryType.WEEKLY_RECAP.value,
                generated_at=datetime.now(),
                data_period=week_data.get('period', {}),
                word_count=len(story.text.split()),
                tone=self.user_profile.preferred_tone
            )
            
            story.insights = insights
            story.recommendations = recommendations
            
            return story
            
        except Exception as e:
            logger.error(f"Failed to generate weekly recap: {e}")
            raise
    
    def generate_monthly_journey(self, month_data: Dict[str, Any]) -> Story:
        """Generate monthly journey narrative."""
        try:
            # Analyze month data
            analysis = self.analyze_month(month_data)
            
            # Generate narrative arc
            narrative_arc = self.create_narrative_arc(analysis)
            
            # Generate story sections
            sections = {
                'opening': self.generate_opening(analysis, 'monthly'),
                'theme': self.generate_theme_section(analysis, narrative_arc),
                'progress': self.generate_progress_section(analysis),
                'habits': self.generate_habits_section(analysis),
                'challenges': self.generate_challenges_section(analysis),
                'growth': self.generate_growth_section(analysis),
                'closing': self.generate_closing(analysis, 'monthly')
            }
            
            # Apply tone
            sections = self.tone_manager.apply_tone(sections)
            
            # Extract insights and recommendations
            insights = self.insight_generator.generate_insights(month_data)
            recommendations = self.recommendation_engine.generate_recommendations(
                analysis, self.user_profile
            )
            
            # Assemble story
            story = self.assemble_story(sections, narrative_arc)
            
            # Add metadata
            story.metadata = StoryMetadata(
                type=StoryType.MONTHLY_JOURNEY.value,
                generated_at=datetime.now(),
                data_period=month_data.get('period', {}),
                word_count=len(story.text.split()),
                tone=self.user_profile.preferred_tone
            )
            
            story.insights = insights
            story.recommendations = recommendations
            
            return story
            
        except Exception as e:
            logger.error(f"Failed to generate monthly journey: {e}")
            raise
    
    def generate_year_in_review(self, year_data: Dict[str, Any]) -> Story:
        """Generate year in review summary."""
        try:
            # Comprehensive year analysis
            analysis = self.analyze_year(year_data)
            
            # Create transformation narrative
            transformation = self.create_transformation_story(analysis)
            
            # Generate story sections
            sections = {
                'opening': self.generate_opening(analysis, 'yearly'),
                'milestones': self.generate_milestones_section(analysis),
                'transformation': self.generate_transformation_section(transformation),
                'statistics': self.generate_statistics_section(analysis),
                'best_moments': self.generate_best_moments_section(analysis),
                'lessons': self.generate_lessons_section(analysis),
                'looking_forward': self.generate_looking_forward_section(analysis),
                'closing': self.generate_closing(analysis, 'yearly')
            }
            
            # Apply tone
            sections = self.tone_manager.apply_tone(sections)
            
            # Extract insights and recommendations
            insights = self.insight_generator.generate_insights(year_data)
            recommendations = self.recommendation_engine.generate_recommendations(
                analysis, self.user_profile
            )
            
            # Assemble story
            story = self.assemble_story(sections, transformation)
            
            # Add metadata
            story.metadata = StoryMetadata(
                type=StoryType.YEAR_IN_REVIEW.value,
                generated_at=datetime.now(),
                data_period=year_data.get('period', {}),
                word_count=len(story.text.split()),
                tone=self.user_profile.preferred_tone
            )
            
            story.insights = insights
            story.recommendations = recommendations
            
            return story
            
        except Exception as e:
            logger.error(f"Failed to generate year in review: {e}")
            raise
    
    def generate_milestone_celebration(self, milestone_data: Dict[str, Any]) -> Story:
        """Generate milestone celebration story."""
        try:
            # Analyze milestone context
            analysis = self.analyze_milestone(milestone_data)
            
            # Generate celebration narrative
            sections = {
                'opening': self.generate_celebration_opening(analysis),
                'context': self.generate_context_section(analysis),
                'journey': self.generate_journey_section(analysis),
                'significance': self.generate_significance_section(analysis),
                'next_challenges': self.generate_next_challenges_section(analysis),
                'closing': self.generate_celebration_closing(analysis)
            }
            
            # Apply celebratory tone
            tone_manager = ToneManager(ToneType.CELEBRATORY)
            sections = tone_manager.apply_tone(sections)
            
            # Create simple insights for the milestone
            insights = [
                Insight(
                    text=f"You've achieved {milestone_data['achievement']}!",
                    category="milestone",
                    importance=1.0
                )
            ]
            
            # Generate next step recommendations
            recommendations = self.recommendation_engine.generate_milestone_recommendations(
                analysis, self.user_profile
            )
            
            # Assemble story
            story = self.assemble_story(sections, "celebration")
            
            # Add metadata
            story.metadata = StoryMetadata(
                type=StoryType.MILESTONE_CELEBRATION.value,
                generated_at=datetime.now(),
                data_period={'milestone': milestone_data},
                word_count=len(story.text.split()),
                tone=ToneType.CELEBRATORY
            )
            
            story.insights = insights
            story.recommendations = recommendations
            
            return story
            
        except Exception as e:
            logger.error(f"Failed to generate milestone celebration: {e}")
            raise
    
    def analyze_week(self, week_data: Dict[str, Any]) -> WeekAnalysis:
        """Comprehensive week analysis for story generation."""
        # Extract basic metrics
        metrics = week_data.get('metrics', {})
        
        # Identify achievements
        achievements = self.identify_achievements(week_data)
        
        # Compare to previous weeks
        comparisons = self.compare_to_previous_weeks(week_data)
        
        # Find patterns
        patterns = self.identify_patterns(week_data)
        
        # Identify challenges
        challenges = self.identify_challenges(week_data)
        
        # Find standout moments
        highlights = self.find_standout_moments(week_data)
        
        # Assess goal progress
        progress = self.assess_goal_progress(week_data)
        
        # Create summary
        summary_phrase = self.create_week_summary_phrase(
            achievements, comparisons, patterns
        )
        
        # Determine week characteristics
        is_exceptional = len(achievements) >= 3 or any(
            a.significance > 0.8 for a in achievements
        )
        shows_improvement = comparisons.get('overall_trend', 0) > 0
        shows_consistency = self.check_consistency(patterns)
        
        return WeekAnalysis(
            achievements=achievements,
            comparisons=comparisons,
            patterns=patterns,
            challenges=challenges,
            highlights=highlights,
            progress=progress,
            summary_phrase=summary_phrase,
            top_achievement=achievements[0] if achievements else None,
            overall_improvement=comparisons.get('overall_improvement', 0),
            is_exceptional_week=is_exceptional,
            shows_improvement=shows_improvement,
            shows_consistency=shows_consistency
        )
    
    def identify_achievements(self, data: Dict[str, Any]) -> List[Achievement]:
        """Identify achievements from data."""
        achievements = []
        
        # Check for personal records
        if self.records_tracker:
            records = self.records_tracker.check_records(data)
            for record in records:
                achievements.append(Achievement(
                    type="personal_record",
                    metric=record['metric'],
                    value=record['value'],
                    context=record['context'],
                    significance=0.9,
                    date=record['date']
                ))
        
        # Check for streaks
        streaks = self.check_streaks(data)
        for streak in streaks:
            achievements.append(Achievement(
                type="streak",
                metric=streak['metric'],
                value=streak['days'],
                context=f"{streak['days']} day streak",
                significance=min(streak['days'] / 30, 1.0),
                date=datetime.now()
            ))
        
        # Check for goal achievements
        goals = self.check_goal_achievements(data)
        for goal in goals:
            achievements.append(Achievement(
                type="goal_met",
                metric=goal['metric'],
                value=goal['value'],
                context=goal['context'],
                significance=0.8,
                date=goal['date']
            ))
        
        # Sort by significance
        achievements.sort(key=lambda x: x.significance, reverse=True)
        
        return achievements
    
    def compare_to_previous_weeks(self, week_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current week to previous weeks."""
        comparisons = {
            'overall_trend': 0,
            'overall_improvement': 0,
            'metric_changes': {},
            'best_metrics': [],
            'worst_metrics': []
        }
        
        # Use weekly calculator if available
        if self.weekly_calculator and 'current_week' in week_data:
            try:
                current = week_data['current_week']
                previous = week_data.get('previous_week', {})
                
                if previous:
                    # Calculate changes for each metric
                    for metric in current.get('metrics', {}):
                        if metric in previous.get('metrics', {}):
                            current_val = current['metrics'][metric].get('mean', 0)
                            previous_val = previous['metrics'][metric].get('mean', 0)
                            
                            if previous_val > 0:
                                change = ((current_val - previous_val) / previous_val) * 100
                                comparisons['metric_changes'][metric] = change
                    
                    # Overall trend
                    if comparisons['metric_changes']:
                        comparisons['overall_trend'] = sum(
                            comparisons['metric_changes'].values()
                        ) / len(comparisons['metric_changes'])
                        
                        # Find best and worst
                        sorted_changes = sorted(
                            comparisons['metric_changes'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                        comparisons['best_metrics'] = sorted_changes[:3]
                        comparisons['worst_metrics'] = sorted_changes[-3:]
            
            except Exception as e:
                logger.warning(f"Failed to compare weeks: {e}")
        
        return comparisons
    
    def identify_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify patterns in the data."""
        patterns = []
        
        # Use pattern analyzer if available
        if self.pattern_analyzer:
            detected_patterns = self.pattern_analyzer.analyze_patterns(data)
            patterns.extend(detected_patterns)
        
        # Add basic pattern detection
        # Weekend warrior pattern
        if self.check_weekend_warrior_pattern(data):
            patterns.append({
                'type': 'weekend_warrior',
                'confidence': 0.8,
                'description': 'Higher activity on weekends'
            })
        
        # Morning person pattern
        if self.check_morning_person_pattern(data):
            patterns.append({
                'type': 'morning_person',
                'confidence': 0.7,
                'description': 'Most active in the morning hours'
            })
        
        return patterns
    
    def check_weekend_warrior_pattern(self, data: Dict[str, Any]) -> bool:
        """Check if user is more active on weekends."""
        # Simplified check - would need actual day-of-week analysis
        return False  # Placeholder
    
    def check_morning_person_pattern(self, data: Dict[str, Any]) -> bool:
        """Check if user is most active in mornings."""
        # Simplified check - would need actual hourly analysis
        return False  # Placeholder
    
    def identify_challenges(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify challenges or areas needing improvement."""
        challenges = []
        
        # Check for declining metrics
        comparisons = self.compare_to_previous_weeks(data)
        for metric, change in comparisons.get('metric_changes', {}).items():
            if change < -10:  # More than 10% decline
                challenges.append({
                    'type': 'declining_metric',
                    'metric': metric,
                    'change': change,
                    'severity': 'medium' if change > -20 else 'high'
                })
        
        # Check for missed goals
        goals = data.get('goals', {})
        for goal_name, goal_data in goals.items():
            if goal_data.get('progress', 100) < 50:
                challenges.append({
                    'type': 'missed_goal',
                    'goal': goal_name,
                    'progress': goal_data.get('progress', 0),
                    'severity': 'medium'
                })
        
        return challenges
    
    def find_standout_moments(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find standout moments in the data."""
        highlights = []
        
        # Check for exceptional days
        daily_data = data.get('daily_metrics', [])
        for day_data in daily_data:
            # Check if any metric was exceptional
            for metric, values in day_data.get('metrics', {}).items():
                if values.get('percentile', 0) > 95:
                    highlights.append({
                        'type': 'exceptional_day',
                        'date': day_data.get('date'),
                        'metric': metric,
                        'value': values.get('value'),
                        'percentile': values.get('percentile')
                    })
        
        return highlights
    
    def assess_goal_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess progress toward goals."""
        progress = {
            'active_goals': [],
            'completed_goals': [],
            'at_risk_goals': [],
            'overall_progress': 0
        }
        
        goals = data.get('goals', {})
        for goal_name, goal_data in goals.items():
            goal_progress = goal_data.get('progress', 0)
            
            goal_info = {
                'name': goal_name,
                'progress': goal_progress,
                'target': goal_data.get('target'),
                'current': goal_data.get('current')
            }
            
            if goal_progress >= 100:
                progress['completed_goals'].append(goal_info)
            elif goal_progress < 50:
                progress['at_risk_goals'].append(goal_info)
            else:
                progress['active_goals'].append(goal_info)
        
        # Calculate overall progress
        if goals:
            total_progress = sum(g.get('progress', 0) for g in goals.values())
            progress['overall_progress'] = total_progress / len(goals)
        
        return progress
    
    def check_streaks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for active streaks in the data."""
        streaks = []
        
        # Placeholder implementation
        # Would need to analyze consecutive days of activity
        
        return streaks
    
    def check_goal_achievements(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for achieved goals."""
        achievements = []
        
        goals = data.get('goals', {})
        for goal_name, goal_data in goals.items():
            if goal_data.get('progress', 0) >= 100:
                achievements.append({
                    'metric': goal_name,
                    'value': goal_data.get('current'),
                    'context': f"Achieved {goal_name} goal",
                    'date': datetime.now()
                })
        
        return achievements
    
    def create_week_summary_phrase(
        self,
        achievements: List[Achievement],
        comparisons: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """Create a summary phrase for the week."""
        if achievements and achievements[0].significance > 0.8:
            return "an exceptional week with major achievements"
        elif comparisons.get('overall_trend', 0) > 10:
            return "a week of significant improvement"
        elif len(patterns) > 2:
            return "a week revealing interesting patterns"
        elif comparisons.get('overall_trend', 0) > 0:
            return "a positive week with steady progress"
        else:
            return "a week of maintaining your routine"
    
    def check_consistency(self, patterns: List[Dict[str, Any]]) -> bool:
        """Check if patterns show consistency."""
        # Check for consistency patterns
        for pattern in patterns:
            if 'consistency' in pattern.get('type', '').lower():
                return True
        return False
    
    def analyze_month(self, month_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monthly data for story generation."""
        # Similar structure to analyze_week but for monthly data
        analysis = {
            'theme': self.identify_monthly_theme(month_data),
            'progress': self.assess_monthly_progress(month_data),
            'habits': self.analyze_habit_formation(month_data),
            'challenges_overcome': self.identify_overcome_challenges(month_data),
            'growth_areas': self.identify_growth_areas(month_data)
        }
        return analysis
    
    def analyze_year(self, year_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze yearly data for story generation."""
        analysis = {
            'major_milestones': self.identify_year_milestones(year_data),
            'transformation': self.analyze_year_transformation(year_data),
            'statistics': self.calculate_year_statistics(year_data),
            'best_moments': self.find_year_best_moments(year_data),
            'lessons_learned': self.extract_year_lessons(year_data)
        }
        return analysis
    
    def analyze_milestone(self, milestone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze milestone for celebration story."""
        analysis = {
            'achievement': milestone_data.get('achievement'),
            'context': milestone_data.get('context'),
            'journey': milestone_data.get('journey'),
            'significance': milestone_data.get('significance'),
            'next_challenges': milestone_data.get('next_challenges', [])
        }
        return analysis
    
    # Placeholder methods for additional analysis
    def identify_monthly_theme(self, data: Dict[str, Any]) -> str:
        """Identify the theme for the month."""
        return "Progress and Discovery"
    
    def assess_monthly_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess monthly progress."""
        return {}
    
    def analyze_habit_formation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze habit formation patterns."""
        return {}
    
    def identify_overcome_challenges(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify challenges that were overcome."""
        return []
    
    def identify_growth_areas(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify areas of growth."""
        return []
    
    def identify_year_milestones(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify major milestones for the year."""
        return []
    
    def analyze_year_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transformation over the year."""
        return {}
    
    def calculate_year_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate year-end statistics."""
        return {}
    
    def find_year_best_moments(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find the best moments of the year."""
        return []
    
    def extract_year_lessons(self, data: Dict[str, Any]) -> List[str]:
        """Extract lessons learned over the year."""
        return []
    
    def select_weekly_structure(self, analysis: WeekAnalysis) -> str:
        """Select the narrative structure for weekly recap."""
        if analysis.is_exceptional_week:
            return "achievement_focused"
        elif analysis.shows_improvement:
            return "progress_focused"
        elif analysis.shows_consistency:
            return "consistency_focused"
        else:
            return "balanced"
    
    def create_narrative_arc(self, analysis: Dict[str, Any]) -> str:
        """Create narrative arc for monthly journey."""
        return "transformation"  # Placeholder
    
    def create_transformation_story(self, analysis: Dict[str, Any]) -> str:
        """Create transformation narrative for year in review."""
        return "growth_journey"  # Placeholder
    
    def generate_opening(self, analysis: Union[WeekAnalysis, Dict[str, Any]], period: str) -> str:
        """Generate opening section."""
        return self.template_engine.generate_opening(analysis, period)
    
    def generate_achievements_section(self, analysis: WeekAnalysis) -> str:
        """Generate achievements section."""
        return self.template_engine.generate_achievements_section(analysis)
    
    def generate_comparison_section(self, analysis: WeekAnalysis) -> str:
        """Generate comparison section."""
        return self.template_engine.generate_comparison_section(analysis)
    
    def generate_insights_section(self, analysis: Union[WeekAnalysis, Dict[str, Any]]) -> str:
        """Generate insights section."""
        return self.template_engine.generate_insights_section(analysis)
    
    def generate_recommendations_section(self, analysis: Union[WeekAnalysis, Dict[str, Any]]) -> str:
        """Generate recommendations section."""
        return self.template_engine.generate_recommendations_section(analysis)
    
    def generate_closing(self, analysis: Union[WeekAnalysis, Dict[str, Any]], period: str) -> str:
        """Generate closing section."""
        return self.template_engine.generate_closing(analysis, period)
    
    # Additional section generators for different story types
    def generate_theme_section(self, analysis: Dict[str, Any], arc: str) -> str:
        """Generate theme section for monthly journey."""
        return ""  # Placeholder
    
    def generate_progress_section(self, analysis: Dict[str, Any]) -> str:
        """Generate progress section."""
        return ""  # Placeholder
    
    def generate_habits_section(self, analysis: Dict[str, Any]) -> str:
        """Generate habits section."""
        return ""  # Placeholder
    
    def generate_challenges_section(self, analysis: Dict[str, Any]) -> str:
        """Generate challenges section."""
        return ""  # Placeholder
    
    def generate_growth_section(self, analysis: Dict[str, Any]) -> str:
        """Generate growth section."""
        return ""  # Placeholder
    
    def generate_milestones_section(self, analysis: Dict[str, Any]) -> str:
        """Generate milestones section."""
        return ""  # Placeholder
    
    def generate_transformation_section(self, transformation: str) -> str:
        """Generate transformation section."""
        return ""  # Placeholder
    
    def generate_statistics_section(self, analysis: Dict[str, Any]) -> str:
        """Generate statistics section."""
        return ""  # Placeholder
    
    def generate_best_moments_section(self, analysis: Dict[str, Any]) -> str:
        """Generate best moments section."""
        return ""  # Placeholder
    
    def generate_lessons_section(self, analysis: Dict[str, Any]) -> str:
        """Generate lessons learned section."""
        return ""  # Placeholder
    
    def generate_looking_forward_section(self, analysis: Dict[str, Any]) -> str:
        """Generate looking forward section."""
        return ""  # Placeholder
    
    def generate_celebration_opening(self, analysis: Dict[str, Any]) -> str:
        """Generate celebration opening."""
        return ""  # Placeholder
    
    def generate_context_section(self, analysis: Dict[str, Any]) -> str:
        """Generate context section."""
        return ""  # Placeholder
    
    def generate_journey_section(self, analysis: Dict[str, Any]) -> str:
        """Generate journey section."""
        return ""  # Placeholder
    
    def generate_significance_section(self, analysis: Dict[str, Any]) -> str:
        """Generate significance section."""
        return ""  # Placeholder
    
    def generate_next_challenges_section(self, analysis: Dict[str, Any]) -> str:
        """Generate next challenges section."""
        return ""  # Placeholder
    
    def generate_celebration_closing(self, analysis: Dict[str, Any]) -> str:
        """Generate celebration closing."""
        return ""  # Placeholder
    
    def assemble_story(self, sections: Dict[str, str], structure: str) -> Story:
        """Assemble sections into complete story."""
        # Combine sections based on structure
        text_parts = []
        title = self.generate_title(sections, structure)
        
        # Order sections based on structure type
        if structure == "achievement_focused":
            section_order = ['opening', 'achievements', 'insights', 'comparison', 
                           'recommendations', 'closing']
        elif structure == "progress_focused":
            section_order = ['opening', 'comparison', 'achievements', 'insights',
                           'recommendations', 'closing']
        else:
            section_order = ['opening', 'achievements', 'comparison', 'insights',
                           'recommendations', 'closing']
        
        for section_name in section_order:
            if section_name in sections and sections[section_name]:
                text_parts.append(sections[section_name])
        
        return Story(
            title=title,
            text="\n\n".join(text_parts),
            type=StoryType.WEEKLY_RECAP,  # Will be set by caller
            sections=sections,
            insights=[],  # Will be populated by caller
            recommendations=[]  # Will be populated by caller
        )
    
    def generate_title(self, sections: Dict[str, str], structure: str) -> str:
        """Generate story title based on content."""
        # Simple title generation
        titles = {
            "achievement_focused": "Your Week of Achievements",
            "progress_focused": "Your Week of Progress",
            "consistency_focused": "Staying Strong This Week",
            "balanced": "Your Weekly Health Summary",
            "transformation": "Your Monthly Journey",
            "growth_journey": "Your Year of Growth",
            "celebration": "Milestone Achieved!"
        }
        return titles.get(structure, "Your Health Story")


class StoryTemplateEngine:
    """Template engine for generating story sections with variations."""
    
    def __init__(self):
        self.templates = self.load_templates()
        self.variations = self.load_variations()
    
    def load_templates(self) -> Dict[str, Any]:
        """Load story templates."""
        # In a real implementation, these would be loaded from files
        return {
            'weekly': {
                'openings': {
                    'exceptional': [
                        "What an incredible week, {name}! Your {key_metric} improved by {improvement_percent}%, making this {week_summary}.",
                        "{name}, this week stands out! With {week_summary}, you've shown remarkable progress in {key_metric}.",
                    ],
                    'improving': [
                        "Great progress this week, {name}! Your dedication is showing with {week_summary}.",
                        "{name}, you're building momentum! This was {week_summary} with consistent improvements.",
                    ],
                    'consistent': [
                        "Another solid week, {name}! Your consistency continues with {week_summary}.",
                        "Staying the course, {name}! This was {week_summary} with reliable patterns.",
                    ],
                    'standard': [
                        "Let's review your week, {name}. This was {week_summary}.",
                        "Here's your weekly summary, {name}. Overall, {week_summary}.",
                    ]
                }
            }
        }
    
    def load_variations(self) -> Dict[str, List[str]]:
        """Load template variations."""
        return {}
    
    def generate_opening(self, analysis: Union[WeekAnalysis, Dict[str, Any]], story_type: str) -> str:
        """Generate story opening with variations."""
        templates = self.templates.get(story_type, {}).get('openings', {})
        
        # Select template based on analysis
        if isinstance(analysis, WeekAnalysis):
            if analysis.is_exceptional_week:
                template_key = 'exceptional'
            elif analysis.shows_improvement:
                template_key = 'improving'
            elif analysis.shows_consistency:
                template_key = 'consistent'
            else:
                template_key = 'standard'
        else:
            template_key = 'standard'
        
        # Get template with variations
        template_options = templates.get(template_key, ["Welcome to your {story_type} summary."])
        selected = random.choice(template_options)
        
        # Fill template
        try:
            if isinstance(analysis, WeekAnalysis):
                return selected.format(
                    name="there",  # Default if no name in profile
                    week_summary=analysis.summary_phrase,
                    key_metric=analysis.top_achievement.metric if analysis.top_achievement else "health metrics",
                    improvement_percent=round(analysis.overall_improvement, 1),
                    story_type=story_type
                )
            else:
                return selected.format(
                    name="there",
                    story_type=story_type,
                    week_summary="your health journey",
                    key_metric="health metrics",
                    improvement_percent=0
                )
        except:
            return f"Welcome to your {story_type} summary."
    
    def generate_achievements_section(self, analysis: WeekAnalysis) -> str:
        """Generate achievements narrative."""
        achievements = analysis.achievements
        
        if not achievements:
            return self.get_no_achievements_message()
        
        # Group achievements by type
        grouped = self.group_achievements(achievements)
        
        sections = []
        for group_type, group_achievements in grouped.items():
            narrative = self.create_achievement_narrative(group_type, group_achievements)
            sections.append(narrative)
        
        return self.connect_sections(sections)
    
    def get_no_achievements_message(self) -> str:
        """Get message when no achievements."""
        messages = [
            "This week was about maintaining your routine and building consistency.",
            "While there weren't major milestones this week, every step counts toward your goals.",
            "This week focused on steady progress and routine maintenance."
        ]
        return random.choice(messages)
    
    def group_achievements(self, achievements: List[Achievement]) -> Dict[str, List[Achievement]]:
        """Group achievements by type."""
        grouped = {}
        for achievement in achievements:
            if achievement.type not in grouped:
                grouped[achievement.type] = []
            grouped[achievement.type].append(achievement)
        return grouped
    
    def create_achievement_narrative(self, achievement_type: str, achievements: List[Achievement]) -> str:
        """Create narrative for achievement group."""
        if achievement_type == 'personal_record':
            return self.create_record_narrative(achievements)
        elif achievement_type == 'streak':
            return self.create_streak_narrative(achievements)
        elif achievement_type == 'goal_met':
            return self.create_goal_narrative(achievements)
        else:
            return self.create_general_achievement_narrative(achievements)
    
    def create_record_narrative(self, achievements: List[Achievement]) -> str:
        """Create narrative for personal records."""
        if len(achievements) == 1:
            a = achievements[0]
            return f"You set a new personal record for {a.metric} at {a.value}! {a.context}"
        else:
            metrics = [a.metric for a in achievements[:3]]
            return f"Multiple personal records this week in {', '.join(metrics)}!"
    
    def create_streak_narrative(self, achievements: List[Achievement]) -> str:
        """Create narrative for streaks."""
        if len(achievements) == 1:
            a = achievements[0]
            return f"Your {a.metric} streak has reached {int(a.value)} days!"
        else:
            total_days = sum(a.value for a in achievements)
            return f"You're maintaining {len(achievements)} active streaks totaling {int(total_days)} days!"
    
    def create_goal_narrative(self, achievements: List[Achievement]) -> str:
        """Create narrative for goals met."""
        if len(achievements) == 1:
            a = achievements[0]
            return f"Goal achieved! {a.context}"
        else:
            return f"Fantastic progress - you've achieved {len(achievements)} goals this week!"
    
    def create_general_achievement_narrative(self, achievements: List[Achievement]) -> str:
        """Create general achievement narrative."""
        return f"You had {len(achievements)} notable achievements this week."
    
    def connect_sections(self, sections: List[str]) -> str:
        """Connect multiple sections smoothly."""
        return " ".join(sections)
    
    def generate_comparison_section(self, analysis: WeekAnalysis) -> str:
        """Generate comparison section."""
        comparisons = analysis.comparisons
        
        if not comparisons or not comparisons.get('metric_changes'):
            return "This week maintained similar patterns to previous weeks."
        
        # Build comparison narrative
        parts = []
        
        # Overall trend
        trend = comparisons.get('overall_trend', 0)
        if trend > 5:
            parts.append(f"Overall, your metrics improved by {round(trend, 1)}% compared to last week.")
        elif trend < -5:
            parts.append(f"This week saw a {round(abs(trend), 1)}% dip in overall metrics.")
        else:
            parts.append("Your metrics remained stable compared to last week.")
        
        # Best improvements
        best = comparisons.get('best_metrics', [])
        if best:
            metric, change = best[0]
            if change > 10:
                parts.append(f"{metric.replace('_', ' ').title()} showed excellent improvement at {round(change, 1)}% increase.")
        
        return " ".join(parts)
    
    def generate_insights_section(self, analysis: Union[WeekAnalysis, Dict[str, Any]]) -> str:
        """Generate insights section."""
        # This would integrate with InsightGenerator
        return "Your data reveals interesting patterns worth noting."
    
    def generate_recommendations_section(self, analysis: Union[WeekAnalysis, Dict[str, Any]]) -> str:
        """Generate recommendations section."""
        # This would integrate with RecommendationEngine
        return "Based on your progress, consider focusing on maintaining your positive momentum."
    
    def generate_closing(self, analysis: Union[WeekAnalysis, Dict[str, Any]], period: str) -> str:
        """Generate closing section."""
        closings = {
            'weekly': [
                "Keep up the great work!",
                "Every step forward counts!",
                "Looking forward to another great week!",
                "Your consistency is building lasting habits!"
            ],
            'monthly': [
                "Another month of progress in your health journey!",
                "You're building momentum month by month!",
                "Reflect on how far you've come this month!"
            ],
            'yearly': [
                "What an incredible year of growth and progress!",
                "You've transformed your health this year!",
                "Here's to another year of health and vitality!"
            ]
        }
        
        options = closings.get(period, closings['weekly'])
        return random.choice(options)


class ToneManager:
    """Manages tone adjustments for story content."""
    
    def __init__(self, preferred_tone: ToneType = ToneType.ENCOURAGING):
        self.tone = preferred_tone
        self.tone_adjusters = {
            ToneType.ENCOURAGING: EncouragingToneAdjuster(),
            ToneType.NEUTRAL: NeutralToneAdjuster(),
            ToneType.MOTIVATING: MotivatingToneAdjuster(),
            ToneType.CELEBRATORY: CelebratoryToneAdjuster()
        }
    
    def apply_tone(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Apply tone adjustments to story sections."""
        adjuster = self.tone_adjusters.get(self.tone, NeutralToneAdjuster())
        
        adjusted_sections = {}
        for section_name, content in sections.items():
            adjusted_sections[section_name] = adjuster.adjust(content, section_name)
        
        return adjusted_sections


class ToneAdjuster(ABC):
    """Base class for tone adjusters."""
    
    @abstractmethod
    def adjust(self, content: str, section_type: str) -> str:
        """Adjust content tone."""
        pass


class EncouragingToneAdjuster(ToneAdjuster):
    """Apply encouraging tone to content."""
    
    def adjust(self, content: str, section_type: str) -> str:
        """Apply encouraging tone to content."""
        if not content:
            return content
            
        # Replace neutral phrases with encouraging ones
        replacements = {
            "didn't meet": "came close to meeting",
            "failed to": "had opportunity to",
            "decreased": "had room for growth",
            "worse than": "different from",
            "below average": "building momentum",
            "no improvement": "maintaining baseline",
            "declined": "experienced variation"
        }
        
        adjusted = content
        for neutral, encouraging in replacements.items():
            adjusted = adjusted.replace(neutral, encouraging)
        
        # Add encouraging phrases to closing
        if section_type == 'closing' and not adjusted.endswith('!'):
            adjusted += " Keep up the great work - every step counts!"
        
        return adjusted


class NeutralToneAdjuster(ToneAdjuster):
    """Maintain neutral tone."""
    
    def adjust(self, content: str, section_type: str) -> str:
        """No adjustments for neutral tone."""
        return content


class MotivatingToneAdjuster(ToneAdjuster):
    """Apply motivating/challenging tone."""
    
    def adjust(self, content: str, section_type: str) -> str:
        """Apply motivating tone to content."""
        if not content:
            return content
            
        # Add challenge-oriented language
        if section_type == 'recommendations':
            content += " Push yourself to reach new heights!"
        elif section_type == 'closing':
            content += " You have the power to achieve even more!"
        
        return content


class CelebratoryToneAdjuster(ToneAdjuster):
    """Apply celebratory tone."""
    
    def adjust(self, content: str, section_type: str) -> str:
        """Apply celebratory tone to content."""
        if not content:
            return content
            
        # Add celebration elements
        replacements = {
            "achieved": "brilliantly achieved",
            "completed": "successfully completed",
            "reached": "triumphantly reached",
            "improved": "remarkably improved"
        }
        
        adjusted = content
        for neutral, celebratory in replacements.items():
            adjusted = adjusted.replace(neutral, celebratory)
        
        # Add celebration to opening/closing
        if section_type in ['opening', 'closing']:
            adjusted = "🎉 " + adjusted
        
        return adjusted


class InsightGenerator:
    """Generates insights from health data."""
    
    def __init__(self):
        self.pattern_templates = self.load_pattern_templates()
        self.correlation_templates = self.load_correlation_templates()
    
    def load_pattern_templates(self) -> Dict[str, str]:
        """Load pattern insight templates."""
        return {
            'weekend_warrior': "Your activity peaks on weekends - {detail}",
            'morning_person': "You're most active in the mornings, with {percent}% of activity before noon",
            'consistency_champion': "Your {metric} has been remarkably consistent, varying by only {variance}%",
            'improvement_streak': "You've improved your {metric} for {days} consecutive days!",
            'evening_person': "Your evening sessions show {percent}% higher intensity",
            'weekly_rhythm': "You follow a consistent weekly pattern with {detail}"
        }
    
    def load_correlation_templates(self) -> Dict[str, str]:
        """Load correlation insight templates."""
        return {
            'positive_correlation': "When your {metric1} increases, your {metric2} tends to improve by {percent}%",
            'negative_correlation': "Higher {metric1} is associated with lower {metric2}",
            'optimal_range': "Your {metric1} is optimal when {metric2} is between {min} and {max}"
        }
    
    def generate_insights(self, data: Dict[str, Any]) -> List[Insight]:
        """Generate personalized insights from data."""
        insights = []
        
        # Generate pattern insights
        patterns = data.get('patterns', [])
        for pattern in patterns[:2]:  # Limit to top 2 patterns
            insight = self.create_pattern_insight(pattern)
            if insight:
                insights.append(insight)
        
        # Generate trend insights
        trends = data.get('trends', {})
        if trends:
            trend_insight = self.create_trend_insight(trends)
            if trend_insight:
                insights.append(trend_insight)
        
        # Sort by importance
        insights.sort(key=lambda x: x.importance, reverse=True)
        
        return insights[:3]  # Return top 3 insights
    
    def create_pattern_insight(self, pattern: Dict[str, Any]) -> Optional[Insight]:
        """Create insight from detected pattern."""
        pattern_type = pattern.get('type', '')
        template = self.pattern_templates.get(pattern_type)
        
        if not template:
            return None
        
        try:
            text = template.format(**pattern.get('details', {}))
            return Insight(
                text=text,
                category='pattern',
                importance=pattern.get('confidence', 0.5),
                visual_hint=pattern.get('visual_hint')
            )
        except:
            return None
    
    def create_trend_insight(self, trends: Dict[str, Any]) -> Optional[Insight]:
        """Create insight from trends."""
        # Find most significant trend
        best_trend = None
        best_value = 0
        
        for metric, trend_data in trends.items():
            if abs(trend_data.get('change', 0)) > best_value:
                best_trend = metric
                best_value = abs(trend_data.get('change', 0))
        
        if best_trend and best_value > 5:
            change = trends[best_trend]['change']
            direction = "increased" if change > 0 else "decreased"
            
            return Insight(
                text=f"Your {best_trend.replace('_', ' ')} has {direction} by {round(abs(change), 1)}% this period",
                category='trend',
                importance=min(best_value / 50, 1.0)
            )
        
        return None


class RecommendationEngine:
    """Generates actionable recommendations."""
    
    def __init__(self):
        self.recommendation_db = self.load_recommendations()
    
    def load_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load recommendation templates."""
        return {
            'improvement_needed': [
                {
                    'action': "Try adding 10 minutes to your daily {metric} routine",
                    'rationale': "Small increments lead to sustainable progress",
                    'difficulty': 'easy'
                },
                {
                    'action': "Set a reminder to track your {metric} at the same time each day",
                    'rationale': "Consistency in tracking improves outcomes",
                    'difficulty': 'easy'
                }
            ],
            'maintain_streak': [
                {
                    'action': "Keep your {metric} streak alive - you're on day {days}!",
                    'rationale': "Streaks build lasting habits",
                    'difficulty': 'medium'
                }
            ],
            'push_further': [
                {
                    'action': "You're ready to increase your {metric} target by 10%",
                    'rationale': "You've consistently exceeded current targets",
                    'difficulty': 'medium'
                }
            ]
        }
    
    def generate_recommendations(
        self,
        analysis: Union[WeekAnalysis, Dict[str, Any]],
        user_profile: UserProfile
    ) -> List[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Goal-based recommendations
        if isinstance(analysis, WeekAnalysis):
            goal_recs = self.generate_goal_recommendations(analysis.progress)
            recommendations.extend(goal_recs)
        
        # Add generic recommendations based on patterns
        if len(recommendations) < 3:
            generic_rec = Recommendation(
                action="Continue tracking your health metrics daily",
                rationale="Consistent tracking leads to better insights",
                category="general",
                difficulty="easy",
                success_probability=0.8
            )
            recommendations.append(generic_rec)
        
        return recommendations[:3]
    
    def generate_goal_recommendations(self, goal_progress: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on goal progress."""
        recs = []
        
        # At-risk goals
        for goal in goal_progress.get('at_risk_goals', []):
            rec = Recommendation(
                action=f"Focus on your {goal['name']} goal this week",
                rationale=f"You're at {goal['progress']}% - small daily efforts will help",
                category='goal_support',
                difficulty='medium'
            )
            recs.append(rec)
        
        # Near completion goals
        for goal in goal_progress.get('active_goals', []):
            if goal['progress'] > 80:
                rec = Recommendation(
                    action=f"Final push for your {goal['name']} goal!",
                    rationale=f"You're {goal['progress']}% there",
                    category='goal_achievement',
                    difficulty='easy'
                )
                recs.append(rec)
        
        return recs
    
    def generate_milestone_recommendations(
        self,
        analysis: Dict[str, Any],
        user_profile: UserProfile
    ) -> List[Recommendation]:
        """Generate recommendations for milestone celebrations."""
        return [
            Recommendation(
                action="Set your next milestone target",
                rationale="Building on success maintains momentum",
                category="milestone",
                difficulty="medium"
            )
        ]


class PreferenceLearner:
    """Learns user preferences from interactions."""
    
    def __init__(self):
        self.interaction_history = []
        self.preference_model = {
            'optimal_length': 300,  # words
            'favorite_sections': [],
            'engagement_times': [],
            'dismissed_types': []
        }
    
    def learn_from_interaction(self, story: Story, interaction: Dict[str, Any]):
        """Learn user preferences from story interactions."""
        self.interaction_history.append({
            'story': story,
            'interaction': interaction,
            'timestamp': datetime.now()
        })
        
        # Update preference model
        interaction_type = interaction.get('type')
        
        if interaction_type == 'read_time':
            self.update_length_preference(story, interaction.get('duration'))
        elif interaction_type == 'section_expanded':
            self.update_section_preference(interaction.get('section'))
        elif interaction_type == 'shared':
            self.update_positive_preference(story)
        elif interaction_type == 'dismissed_quickly':
            self.update_negative_preference(story)
    
    def update_length_preference(self, story: Story, read_duration: float):
        """Update preferred story length based on read time."""
        word_count = story.metadata.word_count if story.metadata else 300
        words_per_minute = 200  # Average reading speed
        
        expected_duration = word_count / words_per_minute
        if read_duration > expected_duration * 0.8:
            # User read most of the story
            self.preference_model['optimal_length'] = int(
                0.9 * self.preference_model['optimal_length'] + 0.1 * word_count
            )
    
    def update_section_preference(self, section: str):
        """Update favorite sections based on expansions."""
        if section not in self.preference_model['favorite_sections']:
            self.preference_model['favorite_sections'].append(section)
    
    def update_positive_preference(self, story: Story):
        """Update preferences based on positive interaction."""
        # User liked this story type/style
        pass
    
    def update_negative_preference(self, story: Story):
        """Update preferences based on negative interaction."""
        # User didn't engage with this type
        story_type = story.metadata.type if story.metadata else None
        if story_type and story_type not in self.preference_model['dismissed_types']:
            self.preference_model['dismissed_types'].append(story_type)
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get current learned preferences."""
        return self.preference_model.copy()