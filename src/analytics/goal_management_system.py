"""
Goal Management System for Apple Health Monitor Dashboard.
Manages goal creation, tracking, suggestions, and adaptive adjustments.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, date, timedelta
import logging
import json
import pandas as pd
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

from ..database import DatabaseManager
from ..health_database import HealthDatabase
from .goal_models import (
    Goal, GoalType, GoalStatus, GoalTimeframe,
    TargetGoal, ConsistencyGoal, ImprovementGoal, HabitGoal,
    GoalSuggestion, GoalProgress, GoalAdjustment, GoalRelationship
)
from .daily_metrics_calculator import DailyMetricsCalculator
from .weekly_metrics_calculator import WeeklyMetricsCalculator
from .monthly_metrics_calculator import MonthlyMetricsCalculator
from .personal_records_tracker import PersonalRecordsTracker
from .notification_manager import NotificationManager
from .goal_notification_integration import GoalNotificationBridge

logger = logging.getLogger(__name__)


class GoalManagementSystem:
    """Main system for managing health goals."""
    
    def __init__(self, health_database: HealthDatabase, notification_manager: Optional[NotificationManager] = None):
        """Initialize the goal management system."""
        self.health_db = health_database
        self.db_manager = DatabaseManager()
        self.daily_calc = DailyMetricsCalculator()
        self.weekly_calc = WeeklyMetricsCalculator()
        self.monthly_calc = MonthlyMetricsCalculator()
        self.records_tracker = PersonalRecordsTracker(health_database)
        
        # Initialize database tables
        self._initialize_database()
        
        # Initialize components
        self.goal_store = GoalStore(self.db_manager)
        self.suggestion_engine = GoalSuggestionEngine(
            self.health_db, 
            self.daily_calc,
            self.weekly_calc,
            self.monthly_calc
        )
        self.progress_tracker = ProgressTracker(self.db_manager, self.health_db, self)
        self.adaptive_manager = AdaptiveGoalManager()
        self.correlation_analyzer = GoalCorrelationAnalyzer(self)
        self.motivation_system = MotivationSystem()
        
        # Initialize notification integration if available
        if notification_manager:
            self.notification_bridge = GoalNotificationBridge(notification_manager)
        else:
            self.notification_bridge = None
            logger.info("Goal system initialized without notification integration")
    
    def _initialize_database(self):
        """Initialize goal-related database tables."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Goals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_type VARCHAR(20) NOT NULL,
                    metric VARCHAR(50) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    user_id INTEGER,
                    config TEXT NOT NULL
                )
            """)
            
            # Goal progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    value REAL NOT NULL,
                    progress_percentage REAL NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    UNIQUE(goal_id, date)
                )
            """)
            
            # Goal relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal1_id INTEGER NOT NULL,
                    goal2_id INTEGER NOT NULL,
                    relationship_type VARCHAR(20) NOT NULL,
                    strength REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (goal1_id) REFERENCES goals(id),
                    FOREIGN KEY (goal2_id) REFERENCES goals(id),
                    UNIQUE(goal1_id, goal2_id)
                )
            """)
            
            # Goal achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goal_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id INTEGER NOT NULL,
                    achievement_date DATE NOT NULL,
                    final_value REAL,
                    final_progress REAL,
                    celebration_shown BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_metric ON goals(metric)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_progress_date ON goal_progress(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_progress_goal ON goal_progress(goal_id)")
            
            conn.commit()
    
    def create_goal(self, goal_type: str, config: Dict[str, Any]) -> Goal:
        """Create a new goal."""
        # Validate goal configuration
        validator = GoalValidator(goal_type)
        if not validator.validate(config):
            raise ValueError(f"Invalid goal configuration: {validator.errors}")
        
        # Create appropriate goal instance
        if goal_type == 'target':
            goal = TargetGoal(**config)
        elif goal_type == 'consistency':
            goal = ConsistencyGoal(**config)
        elif goal_type == 'improvement':
            goal = ImprovementGoal(**config)
        elif goal_type == 'habit':
            goal = HabitGoal(**config)
        else:
            raise ValueError(f"Unknown goal type: {goal_type}")
        
        # Apply smart defaults
        goal = self.apply_smart_defaults(goal)
        
        # Store goal
        goal_id = self.goal_store.add_goal(goal)
        goal.id = goal_id
        
        # Track initial progress
        self.progress_tracker.update_progress(goal)
        
        # Schedule notifications if available
        if self.notification_bridge:
            self.notification_bridge.schedule_goal_notifications(goal)
        
        logger.info(f"Created new {goal_type} goal: {goal.name}")
        return goal
    
    def apply_smart_defaults(self, goal: Goal) -> Goal:
        """Apply intelligent defaults based on user history."""
        if not goal.end_date:
            # Default duration based on goal type
            if isinstance(goal, HabitGoal):
                goal.end_date = goal.start_date + timedelta(days=goal.target_days)
            elif isinstance(goal, TargetGoal) and goal.duration:
                if goal.timeframe == GoalTimeframe.DAILY:
                    goal.end_date = goal.start_date + timedelta(days=goal.duration)
                elif goal.timeframe == GoalTimeframe.WEEKLY:
                    goal.end_date = goal.start_date + timedelta(weeks=goal.duration)
                elif goal.timeframe == GoalTimeframe.MONTHLY:
                    goal.end_date = goal.start_date + timedelta(days=goal.duration * 30)
            else:
                # Default to 30 days
                goal.end_date = goal.start_date + timedelta(days=30)
        
        # Set baseline for improvement goals
        if isinstance(goal, ImprovementGoal) and not goal.baseline_value:
            baseline = self._calculate_baseline(goal.metric, goal.baseline_period)
            if baseline:
                goal.baseline_value = baseline
        
        return goal
    
    def _calculate_baseline(self, metric: str, period_days: int) -> Optional[float]:
        """Calculate baseline value for a metric."""
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=period_days)
        
        df = self.health_db.query_health_data(
            start_date=start_date,
            end_date=end_date,
            health_types=[metric]
        )
        
        if df.empty:
            return None
        
        # Calculate average daily value
        daily_values = df.groupby(df['startDate'].dt.date)['value'].sum()
        return daily_values.mean()
    
    def suggest_goals(self, metric: str, user_profile: Optional[Dict] = None) -> List[GoalSuggestion]:
        """Generate personalized goal suggestions."""
        return self.suggestion_engine.suggest_goals(metric, user_profile)
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        return self.goal_store.get_active_goals()
    
    def get_goal_by_id(self, goal_id: int) -> Optional[Goal]:
        """Get a specific goal by ID."""
        return self.goal_store.get_goal_by_id(goal_id)
    
    def update_goal_status(self, goal_id: int, status: GoalStatus):
        """Update the status of a goal."""
        self.goal_store.update_goal_status(goal_id, status)
    
    def check_goal_progress(self, goal_id: int) -> Dict[str, Any]:
        """Check current progress of a goal."""
        goal = self.get_goal_by_id(goal_id)
        if not goal:
            return {}
        
        progress = self.progress_tracker.get_current_progress(goal)
        
        # Check if goal needs adjustment
        adjustment = None
        if goal.is_active():
            progress_history = self.progress_tracker.get_progress_history(goal_id, days=7)
            adjustment = self.adaptive_manager.evaluate_goal_progress(
                goal, 
                [p.progress_percentage for p in progress_history]
            )
        
        return {
            'goal': goal,
            'current_progress': progress,
            'needs_adjustment': adjustment is not None,
            'adjustment': adjustment,
            'message': self.motivation_system.generate_message(goal, progress)
        }
    
    def analyze_goal_relationships(self) -> Dict[str, Any]:
        """Analyze relationships between active goals."""
        active_goals = self.get_active_goals()
        if len(active_goals) < 2:
            return {'relationships': [], 'recommendations': []}
        
        relationships = self.correlation_analyzer.analyze_goal_relationships(active_goals)
        
        return {
            'relationships': relationships,
            'recommendations': self.correlation_analyzer.generate_recommendations(relationships)
        }
    
    def complete_goal(self, goal_id: int):
        """Mark a goal as completed."""
        goal = self.get_goal_by_id(goal_id)
        if not goal:
            return
        
        # Get final progress
        progress = self.progress_tracker.get_current_progress(goal)
        
        # Record achievement
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO goal_achievements (goal_id, achievement_date, final_value, final_progress)
                VALUES (?, ?, ?, ?)
            """, (goal_id, date.today(), progress.value, progress.progress_percentage))
            conn.commit()
        
        # Update goal status
        self.update_goal_status(goal_id, GoalStatus.COMPLETED)
        
        logger.info(f"Goal completed: {goal.name} with {progress.progress_percentage:.1f}% progress")


class GoalStore:
    """Storage and retrieval of goals."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_goal(self, goal: Goal) -> int:
        """Add a new goal to the database."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert goal-specific attributes to JSON config
            config = goal.to_dict()
            
            cursor.execute("""
                INSERT INTO goals (goal_type, metric, name, description, status, 
                                 start_date, end_date, user_id, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.goal_type.value,
                goal.metric,
                goal.name,
                goal.description,
                goal.status.value,
                goal.start_date,
                goal.end_date,
                goal.user_id,
                json.dumps(config)
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_goal_by_id(self, goal_id: int) -> Optional[Goal]:
        """Retrieve a goal by ID."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._goal_from_row(row)
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM goals 
                WHERE status = 'active' 
                AND (end_date IS NULL OR end_date >= date('now'))
                ORDER BY created_at DESC
            """)
            
            goals = []
            for row in cursor.fetchall():
                goal = self._goal_from_row(row)
                if goal:
                    goals.append(goal)
            
            return goals
    
    def update_goal_status(self, goal_id: int, status: GoalStatus):
        """Update the status of a goal."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE goals 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status.value, goal_id))
            conn.commit()
    
    def _goal_from_row(self, row: sqlite3.Row) -> Optional[Goal]:
        """Create a Goal object from a database row."""
        try:
            config = json.loads(row['config'])
            goal_type = row['goal_type']
            
            # Create appropriate goal instance
            if goal_type == 'target':
                goal = TargetGoal(
                    metric=row['metric'],
                    name=row['name'],
                    description=row['description'],
                    target_value=config.get('target_value', 0),
                    timeframe=GoalTimeframe(config.get('timeframe', 'daily')),
                    duration=config.get('duration')
                )
            elif goal_type == 'consistency':
                goal = ConsistencyGoal(
                    metric=row['metric'],
                    name=row['name'],
                    description=row['description'],
                    frequency=config.get('frequency', 0),
                    period=GoalTimeframe(config.get('period', 'weekly')),
                    threshold=config.get('threshold'),
                    allow_partial=config.get('allow_partial', True)
                )
            elif goal_type == 'improvement':
                goal = ImprovementGoal(
                    metric=row['metric'],
                    name=row['name'],
                    description=row['description'],
                    improvement_target=config.get('improvement_target', 0),
                    improvement_type=config.get('improvement_type', 'percentage'),
                    baseline_value=config.get('baseline_value'),
                    baseline_period=config.get('baseline_period', 30)
                )
            elif goal_type == 'habit':
                goal = HabitGoal(
                    metric=row['metric'],
                    name=row['name'],
                    description=row['description'],
                    target_days=config.get('target_days', 21),
                    current_streak=config.get('current_streak', 0),
                    best_streak=config.get('best_streak', 0),
                    required_daily_value=config.get('required_daily_value'),
                    allow_skip_days=config.get('allow_skip_days', 0),
                    skips_used=config.get('skips_used', 0)
                )
            else:
                return None
            
            # Set common attributes
            goal.id = row['id']
            goal.status = GoalStatus(row['status'])
            goal.created_at = datetime.fromisoformat(row['created_at'])
            goal.updated_at = datetime.fromisoformat(row['updated_at'])
            goal.start_date = date.fromisoformat(row['start_date'])
            goal.end_date = date.fromisoformat(row['end_date']) if row['end_date'] else None
            goal.user_id = row['user_id']
            
            return goal
            
        except Exception as e:
            logger.error(f"Error creating goal from row: {e}")
            return None


class GoalSuggestionEngine:
    """Engine for generating personalized goal suggestions."""
    
    def __init__(self, health_db: HealthDatabase, 
                 daily_calc: DailyMetricsCalculator,
                 weekly_calc: WeeklyMetricsCalculator,
                 monthly_calc: MonthlyMetricsCalculator):
        self.health_db = health_db
        self.daily_calc = daily_calc
        self.weekly_calc = weekly_calc
        self.monthly_calc = monthly_calc
    
    def suggest_goals(self, metric: str, user_profile: Optional[Dict] = None) -> List[GoalSuggestion]:
        """Generate personalized goal suggestions."""
        suggestions = []
        
        # Get historical data
        history_df = self._get_metric_history(metric, days=90)
        if history_df.empty:
            return self._get_starter_suggestions(metric)
        
        # Calculate statistics
        stats = self._calculate_statistics(history_df)
        
        # Generate different goal types
        suggestions.extend(self._suggest_target_goals(metric, stats))
        suggestions.extend(self._suggest_consistency_goals(metric, stats))
        suggestions.extend(self._suggest_improvement_goals(metric, stats))
        suggestions.extend(self._suggest_habit_goals(metric, stats))
        
        # Score and rank suggestions
        for suggestion in suggestions:
            suggestion.achievability_score = self._calculate_achievability(
                suggestion, stats, user_profile
            )
            suggestion.impact_score = self._calculate_impact(suggestion, stats)
        
        # Sort by combined score
        suggestions.sort(
            key=lambda s: s.achievability_score * s.impact_score, 
            reverse=True
        )
        
        return suggestions[:5]  # Top 5 suggestions
    
    def _get_metric_history(self, metric: str, days: int) -> pd.DataFrame:
        """Get historical data for a metric."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return self.health_db.query_health_data(
            start_date=start_date,
            end_date=end_date,
            health_types=[metric]
        )
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive statistics from historical data."""
        # Daily aggregation
        daily_values = df.groupby(df['startDate'].dt.date)['value'].sum()
        
        # Basic stats
        stats = {
            'mean': daily_values.mean(),
            'median': daily_values.median(),
            'std': daily_values.std(),
            'min': daily_values.min(),
            'max': daily_values.max(),
            'count': len(daily_values),
            'active_days': (daily_values > 0).sum()
        }
        
        # Percentiles
        stats['p25'] = daily_values.quantile(0.25)
        stats['p75'] = daily_values.quantile(0.75)
        stats['p90'] = daily_values.quantile(0.90)
        
        # Trends
        if len(daily_values) >= 7:
            recent_week = daily_values.tail(7).mean()
            previous_week = daily_values.tail(14).head(7).mean()
            stats['weekly_trend'] = (recent_week - previous_week) / previous_week if previous_week > 0 else 0
        
        # Consistency
        stats['consistency_score'] = stats['active_days'] / stats['count']
        
        return stats
    
    def _suggest_target_goals(self, metric: str, stats: Dict) -> List[GoalSuggestion]:
        """Generate target-based goal suggestions."""
        suggestions = []
        
        # Daily target based on 75th percentile
        if stats['p75'] > stats['median']:
            suggestions.append(GoalSuggestion(
                goal_type=GoalType.TARGET,
                metric=metric,
                suggested_value=stats['p75'],
                timeframe=GoalTimeframe.DAILY,
                reasoning="Achieve your better days more consistently",
                based_on="Your 75th percentile performance"
            ))
        
        # Weekly target based on recent performance
        weekly_target = stats['mean'] * 7 * 1.1  # 10% improvement
        suggestions.append(GoalSuggestion(
            goal_type=GoalType.TARGET,
            metric=metric,
            suggested_value=weekly_target,
            timeframe=GoalTimeframe.WEEKLY,
            reasoning="Gradual improvement from current weekly average",
            based_on="Your average weekly performance + 10%"
        ))
        
        return suggestions
    
    def _suggest_consistency_goals(self, metric: str, stats: Dict) -> List[GoalSuggestion]:
        """Generate consistency-based goal suggestions."""
        suggestions = []
        
        # Frequency goal
        current_frequency = stats['active_days'] / stats['count'] * 7
        if current_frequency < 7:
            target_frequency = min(int(current_frequency + 1), 7)
            suggestions.append(GoalSuggestion(
                goal_type=GoalType.CONSISTENCY,
                metric=metric,
                suggested_value=target_frequency,
                timeframe=GoalTimeframe.WEEKLY,
                reasoning=f"Increase from {current_frequency:.1f} to {target_frequency} days per week",
                based_on="Your current weekly frequency"
            ))
        
        return suggestions
    
    def _suggest_improvement_goals(self, metric: str, stats: Dict) -> List[GoalSuggestion]:
        """Generate improvement-based goal suggestions."""
        suggestions = []
        
        # Percentage improvement
        if stats.get('weekly_trend', 0) > 0:
            # Already improving, suggest maintaining momentum
            improvement = 15.0
        else:
            # Not improving, suggest modest goal
            improvement = 10.0
        
        suggestions.append(GoalSuggestion(
            goal_type=GoalType.IMPROVEMENT,
            metric=metric,
            suggested_value=improvement,
            timeframe=GoalTimeframe.MONTHLY,
            reasoning=f"Improve by {improvement}% over the next month",
            based_on="Your recent performance trend"
        ))
        
        return suggestions
    
    def _suggest_habit_goals(self, metric: str, stats: Dict) -> List[GoalSuggestion]:
        """Generate habit formation goal suggestions."""
        suggestions = []
        
        # 21-day challenge
        threshold = stats['median'] * 0.8  # 80% of median
        suggestions.append(GoalSuggestion(
            goal_type=GoalType.HABIT,
            metric=metric,
            suggested_value=threshold,
            timeframe=GoalTimeframe.DAILY,
            reasoning=f"Build a habit with 21 consecutive days above {threshold:.0f}",
            based_on="80% of your median daily value"
        ))
        
        return suggestions
    
    def _calculate_achievability(self, suggestion: GoalSuggestion, 
                                stats: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate how achievable a goal is (0-1)."""
        score = 0.5  # Base score
        
        # Adjust based on goal type and historical performance
        if suggestion.goal_type == GoalType.TARGET:
            # Check how often they've hit this target before
            if 'daily_values' in stats:
                hit_rate = (stats['daily_values'] >= suggestion.suggested_value).mean()
                score = 0.3 + (hit_rate * 0.7)
        
        elif suggestion.goal_type == GoalType.CONSISTENCY:
            # Check current consistency
            current_consistency = stats.get('consistency_score', 0)
            target_consistency = suggestion.suggested_value / 7  # Convert to ratio
            if target_consistency <= current_consistency * 1.2:  # 20% improvement
                score = 0.8
            else:
                score = 0.5
        
        elif suggestion.goal_type == GoalType.IMPROVEMENT:
            # Check recent trend
            if stats.get('weekly_trend', 0) > 0:
                score = 0.7  # Already improving
            else:
                score = 0.5  # Needs to reverse trend
        
        elif suggestion.goal_type == GoalType.HABIT:
            # Check longest streak
            score = 0.6  # Habits are moderately challenging
        
        # Adjust based on user profile if available
        if user_profile:
            if user_profile.get('experience_level') == 'beginner':
                score *= 1.2  # Make easier goals for beginners
            elif user_profile.get('experience_level') == 'advanced':
                score *= 0.8  # More challenging for advanced users
        
        return min(1.0, max(0.1, score))
    
    def _calculate_impact(self, suggestion: GoalSuggestion, stats: Dict) -> float:
        """Calculate the potential impact of achieving this goal (0-1)."""
        impact = 0.5  # Base impact
        
        # Calculate improvement from current state
        if suggestion.goal_type == GoalType.TARGET:
            improvement_ratio = suggestion.suggested_value / stats['mean'] if stats['mean'] > 0 else 1
            impact = min(1.0, improvement_ratio - 1)  # How much above average
        
        elif suggestion.goal_type == GoalType.CONSISTENCY:
            current_days = stats['active_days'] / stats['count'] * 7
            improvement = suggestion.suggested_value - current_days
            impact = min(1.0, improvement / 7)  # Normalized improvement
        
        elif suggestion.goal_type == GoalType.IMPROVEMENT:
            impact = min(1.0, suggestion.suggested_value / 100)  # Percentage as impact
        
        elif suggestion.goal_type == GoalType.HABIT:
            impact = 0.8  # Habits have high long-term impact
        
        return max(0.1, impact)
    
    def _get_starter_suggestions(self, metric: str) -> List[GoalSuggestion]:
        """Get starter suggestions when no historical data is available."""
        # Return generic starter goals
        return [
            GoalSuggestion(
                goal_type=GoalType.HABIT,
                metric=metric,
                suggested_value=1,
                timeframe=GoalTimeframe.DAILY,
                achievability_score=0.8,
                impact_score=0.7,
                reasoning="Start with a simple daily habit",
                based_on="Recommended starter goal"
            ),
            GoalSuggestion(
                goal_type=GoalType.CONSISTENCY,
                metric=metric,
                suggested_value=3,
                timeframe=GoalTimeframe.WEEKLY,
                achievability_score=0.7,
                impact_score=0.6,
                reasoning="Build consistency with 3 days per week",
                based_on="Recommended starter frequency"
            )
        ]


class ProgressTracker:
    """Tracks progress towards goals."""
    
    def __init__(self, db_manager: DatabaseManager, health_db: HealthDatabase, 
                 goal_system: Optional['GoalManagementSystem'] = None):
        self.db_manager = db_manager
        self.health_db = health_db
        self.goal_system = goal_system
    
    def update_progress(self, goal: Goal):
        """Update progress for a goal."""
        current_value = self._get_current_value(goal)
        if current_value is None:
            return
        
        progress_percentage = goal.calculate_progress(current_value)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO goal_progress (goal_id, date, value, progress_percentage)
                VALUES (?, ?, ?, ?)
            """, (goal.id, date.today(), current_value, progress_percentage))
            conn.commit()
        
        # Check if goal is achieved
        if goal.is_achieved(current_value) and goal.status == GoalStatus.ACTIVE:
            self._handle_goal_achievement(goal)
    
    def get_current_progress(self, goal: Goal) -> GoalProgress:
        """Get current progress for a goal."""
        current_value = self._get_current_value(goal)
        if current_value is None:
            current_value = 0
        
        progress_percentage = goal.calculate_progress(current_value)
        
        return GoalProgress(
            goal_id=goal.id,
            date=date.today(),
            value=current_value,
            progress_percentage=progress_percentage
        )
    
    def get_progress_history(self, goal_id: int, days: int = 30) -> List[GoalProgress]:
        """Get progress history for a goal."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM goal_progress
                WHERE goal_id = ? AND date >= date('now', '-' || ? || ' days')
                ORDER BY date DESC
            """, (goal_id, days))
            
            progress_list = []
            for row in cursor.fetchall():
                progress_list.append(GoalProgress(
                    goal_id=row['goal_id'],
                    date=date.fromisoformat(row['date']),
                    value=row['value'],
                    progress_percentage=row['progress_percentage'],
                    notes=row['notes']
                ))
            
            return progress_list
    
    def _get_current_value(self, goal: Goal) -> Optional[Union[float, List[float]]]:
        """Get current value for goal calculation."""
        if isinstance(goal, TargetGoal):
            return self._get_target_value(goal)
        elif isinstance(goal, ConsistencyGoal):
            return self._get_consistency_values(goal)
        elif isinstance(goal, ImprovementGoal):
            return self._get_improvement_value(goal)
        elif isinstance(goal, HabitGoal):
            return self._get_habit_streak(goal)
        return None
    
    def _get_target_value(self, goal: TargetGoal) -> Optional[float]:
        """Get current value for a target goal."""
        if goal.timeframe == GoalTimeframe.DAILY:
            end_date = date.today()
            start_date = end_date
        elif goal.timeframe == GoalTimeframe.WEEKLY:
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
        else:  # Monthly
            end_date = date.today()
            start_date = end_date - timedelta(days=29)
        
        df = self.health_db.query_health_data(
            start_date=start_date,
            end_date=end_date,
            health_types=[goal.metric]
        )
        
        if df.empty:
            return 0
        
        return df['value'].sum()
    
    def _get_consistency_values(self, goal: ConsistencyGoal) -> List[float]:
        """Get values for consistency goal calculation."""
        if goal.period == GoalTimeframe.WEEKLY:
            days = 7
        else:  # Monthly
            days = 30
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        df = self.health_db.query_health_data(
            start_date=start_date,
            end_date=end_date,
            health_types=[goal.metric]
        )
        
        # Group by day and sum
        if not df.empty:
            daily_values = df.groupby(df['startDate'].dt.date)['value'].sum()
            
            # Fill missing days with 0
            date_range = pd.date_range(start_date, end_date, freq='D')
            all_values = []
            for d in date_range:
                if d.date() in daily_values.index:
                    all_values.append(daily_values[d.date()])
                else:
                    all_values.append(0)
            
            return all_values
        
        return [0] * days
    
    def _get_improvement_value(self, goal: ImprovementGoal) -> Optional[float]:
        """Get current value for improvement goal."""
        # Get recent average
        end_date = date.today()
        start_date = end_date - timedelta(days=6)  # Last 7 days
        
        df = self.health_db.query_health_data(
            start_date=start_date,
            end_date=end_date,
            health_types=[goal.metric]
        )
        
        if df.empty:
            return 0
        
        daily_avg = df.groupby(df['startDate'].dt.date)['value'].sum().mean()
        return daily_avg
    
    def _get_habit_streak(self, goal: HabitGoal) -> int:
        """Get current streak for habit goal."""
        # Check consecutive days meeting the requirement
        current_streak = 0
        check_date = date.today()
        
        while True:
            df = self.health_db.query_health_data(
                start_date=check_date,
                end_date=check_date,
                health_types=[goal.metric]
            )
            
            if df.empty:
                daily_value = 0
            else:
                daily_value = df['value'].sum()
            
            if goal.required_daily_value:
                met_requirement = daily_value >= goal.required_daily_value
            else:
                met_requirement = daily_value > 0
            
            if met_requirement:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return current_streak
    
    def _handle_goal_achievement(self, goal: Goal):
        """Handle when a goal is achieved."""
        # Send notification if available
        if self.goal_system and hasattr(self.goal_system, 'notification_bridge') and self.goal_system.notification_bridge:
            progress = self.get_current_progress(goal)
            self.goal_system.notification_bridge.notify_goal_achieved(goal, progress)
        
        # Update goal status
        if self.goal_system:
            self.goal_system.update_goal_status(goal.id, GoalStatus.COMPLETED)


class AdaptiveGoalManager:
    """Manages adaptive goal adjustments."""
    
    def evaluate_goal_progress(self, goal: Goal, progress_history: List[float]) -> Optional[GoalAdjustment]:
        """Evaluate if goal needs adjustment."""
        if len(progress_history) < 3:
            return None
        
        # Check if goal is too easy
        if self._is_goal_too_easy(progress_history):
            return GoalAdjustment(
                adjustment_type='increase_difficulty',
                reason='Consistently exceeding target',
                new_target=self._calculate_stretch_target(goal, progress_history),
                confidence=0.8
            )
        
        # Check if goal is too hard
        if self._is_goal_too_hard(progress_history):
            return GoalAdjustment(
                adjustment_type='decrease_difficulty',
                reason='Struggling to make progress',
                new_target=self._calculate_achievable_target(goal, progress_history),
                confidence=0.7
            )
        
        # Check for plateau
        if self._detect_plateau(progress_history):
            return GoalAdjustment(
                adjustment_type='modify_approach',
                reason='Progress has plateaued',
                suggestion=self._suggest_new_approach(goal),
                confidence=0.6
            )
        
        return None
    
    def _is_goal_too_easy(self, progress_history: List[float]) -> bool:
        """Check if goal is consistently exceeded."""
        if len(progress_history) < 7:
            return False
        
        # Goal achieved every day for a week
        return all(p >= 100 for p in progress_history[-7:])
    
    def _is_goal_too_hard(self, progress_history: List[float]) -> bool:
        """Check if goal is too difficult."""
        if len(progress_history) < 7:
            return False
        
        # Less than 20% progress for a week
        return all(p < 20 for p in progress_history[-7:])
    
    def _detect_plateau(self, progress_history: List[float]) -> bool:
        """Detect if progress has plateaued."""
        if len(progress_history) < 14:
            return False
        
        # Compare last week to previous week
        recent_week = np.mean(progress_history[-7:])
        previous_week = np.mean(progress_history[-14:-7])
        
        # Plateau if less than 5% change
        return abs(recent_week - previous_week) < 5
    
    def _calculate_stretch_target(self, goal: Goal, progress_history: List[float]) -> float:
        """Calculate a stretch target based on performance."""
        if isinstance(goal, TargetGoal):
            # Average achievement above 100%
            avg_achievement = np.mean([p for p in progress_history if p > 100])
            increase_factor = 1.1 + (avg_achievement - 100) / 1000
            return goal.target_value * increase_factor
        
        return None
    
    def _calculate_achievable_target(self, goal: Goal, progress_history: List[float]) -> float:
        """Calculate a more achievable target."""
        if isinstance(goal, TargetGoal):
            # Set to 90th percentile of actual achievement
            actual_values = [p * goal.target_value / 100 for p in progress_history]
            return np.percentile(actual_values, 90)
        
        return None
    
    def _suggest_new_approach(self, goal: Goal) -> str:
        """Suggest a new approach for plateaued progress."""
        suggestions = [
            "Try breaking down your goal into smaller daily tasks",
            "Consider adding variety to your routine",
            "Focus on consistency rather than intensity",
            "Track additional metrics that contribute to this goal",
            "Review and adjust the time of day you work on this goal"
        ]
        
        # Return a relevant suggestion based on goal type
        if isinstance(goal, ConsistencyGoal):
            return suggestions[2]
        elif isinstance(goal, HabitGoal):
            return suggestions[0]
        else:
            return suggestions[1]


class GoalCorrelationAnalyzer:
    """Analyzes relationships between goals."""
    
    def __init__(self, goal_manager):
        self.goal_manager = goal_manager
    
    def analyze_goal_relationships(self, goals: List[Goal]) -> List[GoalRelationship]:
        """Analyze relationships between active goals."""
        relationships = []
        
        for i, goal1 in enumerate(goals):
            for goal2 in goals[i+1:]:
                relationship = self._analyze_pair(goal1, goal2)
                if relationship and relationship.strength > 0.3:
                    relationships.append(relationship)
        
        return relationships
    
    def _analyze_pair(self, goal1: Goal, goal2: Goal) -> Optional[GoalRelationship]:
        """Analyze relationship between two goals."""
        # Get progress history for both goals
        progress1 = self.goal_manager.progress_tracker.get_progress_history(goal1.id, days=30)
        progress2 = self.goal_manager.progress_tracker.get_progress_history(goal2.id, days=30)
        
        if len(progress1) < 7 or len(progress2) < 7:
            return None
        
        # Align dates and calculate correlation
        dates1 = {p.date: p.progress_percentage for p in progress1}
        dates2 = {p.date: p.progress_percentage for p in progress2}
        
        common_dates = sorted(set(dates1.keys()) & set(dates2.keys()))
        if len(common_dates) < 7:
            return None
        
        values1 = [dates1[d] for d in common_dates]
        values2 = [dates2[d] for d in common_dates]
        
        correlation = np.corrcoef(values1, values2)[0, 1]
        
        # Determine relationship type
        if correlation > 0.5:
            rel_type = 'synergistic'
            description = f"{goal1.metric} and {goal2.metric} tend to improve together"
        elif correlation < -0.3:
            rel_type = 'conflicting'
            description = f"{goal1.metric} and {goal2.metric} may compete for time or energy"
        else:
            rel_type = 'independent'
            description = f"{goal1.metric} and {goal2.metric} appear to be independent"
        
        return GoalRelationship(
            goal1_id=goal1.id,
            goal2_id=goal2.id,
            relationship_type=rel_type,
            strength=abs(correlation),
            description=description
        )
    
    def generate_recommendations(self, relationships: List[GoalRelationship]) -> List[str]:
        """Generate recommendations based on goal relationships."""
        recommendations = []
        
        # Find synergistic goals
        synergistic = [r for r in relationships if r.relationship_type == 'synergistic']
        if synergistic:
            recommendations.append(
                "Consider scheduling synergistic goals together to maximize efficiency"
            )
        
        # Find conflicting goals
        conflicting = [r for r in relationships if r.relationship_type == 'conflicting']
        if conflicting:
            recommendations.append(
                "Schedule conflicting goals at different times to avoid competition"
            )
        
        return recommendations


class MotivationSystem:
    """Generates motivational messages and celebrations."""
    
    def __init__(self):
        self.message_templates = self._load_message_templates()
    
    def generate_message(self, goal: Goal, progress: GoalProgress) -> str:
        """Generate contextual motivational message."""
        context = self._determine_context(goal, progress)
        
        if context == 'just_achieved':
            return self._get_celebration_message(goal, progress)
        elif context == 'close_to_goal':
            return self._get_encouragement_message(goal, progress)
        elif context == 'struggling':
            return self._get_support_message(goal, progress)
        elif context == 'streak_at_risk':
            return self._get_streak_reminder(goal, progress)
        else:
            return self._get_progress_update(goal, progress)
    
    def _determine_context(self, goal: Goal, progress: GoalProgress) -> str:
        """Determine the motivational context."""
        if progress.progress_percentage >= 100:
            return 'just_achieved'
        elif progress.progress_percentage >= 80:
            return 'close_to_goal'
        elif progress.progress_percentage < 30:
            return 'struggling'
        elif isinstance(goal, HabitGoal):
            return 'streak_at_risk'
        else:
            return 'progress_update'
    
    def _get_celebration_message(self, goal: Goal, progress: GoalProgress) -> str:
        """Get celebration message for achievement."""
        messages = [
            f"🎉 Congratulations! You've achieved your {goal.name} goal!",
            f"🌟 Amazing work! You crushed your {goal.metric} goal!",
            f"🏆 Goal achieved! You hit {progress.value:.0f} {goal.metric}!",
            f"✨ Fantastic! You've completed your {goal.name} challenge!"
        ]
        return messages[hash(str(goal.id)) % len(messages)]
    
    def _get_encouragement_message(self, goal: Goal, progress: GoalProgress) -> str:
        """Get encouragement for near completion."""
        remaining = 100 - progress.progress_percentage
        messages = [
            f"Almost there! Just {remaining:.0f}% to go on your {goal.name} goal!",
            f"You're so close! Keep pushing for your {goal.metric} goal!",
            f"Great progress! You're at {progress.progress_percentage:.0f}% of your goal!"
        ]
        return messages[hash(str(goal.id)) % len(messages)]
    
    def _get_support_message(self, goal: Goal, progress: GoalProgress) -> str:
        """Get supportive message for struggling."""
        messages = [
            f"Every step counts! You're making progress on {goal.name}.",
            f"Keep going! Small improvements add up over time.",
            f"Don't give up! You've got this - {goal.name} is within reach."
        ]
        return messages[hash(str(goal.id)) % len(messages)]
    
    def _get_streak_reminder(self, goal: Goal, progress: GoalProgress) -> str:
        """Get reminder for streak goals."""
        if isinstance(goal, HabitGoal):
            return f"Keep your streak alive! {goal.current_streak} days and counting!"
        return "Stay consistent to maintain your progress!"
    
    def _get_progress_update(self, goal: Goal, progress: GoalProgress) -> str:
        """Get general progress update."""
        return f"You're at {progress.progress_percentage:.0f}% of your {goal.name} goal. Keep it up!"
    
    def _load_message_templates(self) -> Dict[str, List[str]]:
        """Load message templates."""
        return {
            'celebration': [
                "🎉 Congratulations! You've achieved your {goal_name} goal!",
                "🌟 Amazing work! You crushed it!",
                "🏆 Goal achieved! Incredible effort!"
            ],
            'encouragement': [
                "Almost there! Just {remaining}% to go!",
                "You're so close! Keep pushing!",
                "Great progress! You're at {progress}%!"
            ],
            'support': [
                "Every step counts! Keep going!",
                "Small improvements add up!",
                "You've got this!"
            ]
        }


class GoalValidator:
    """Validates goal configurations."""
    
    def __init__(self, goal_type: str):
        self.goal_type = goal_type
        self.errors = []
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate goal configuration."""
        self.errors = []
        
        # Common validations
        if 'metric' not in config or not config['metric']:
            self.errors.append("Metric is required")
        
        # Type-specific validations
        if self.goal_type == 'target':
            self._validate_target_goal(config)
        elif self.goal_type == 'consistency':
            self._validate_consistency_goal(config)
        elif self.goal_type == 'improvement':
            self._validate_improvement_goal(config)
        elif self.goal_type == 'habit':
            self._validate_habit_goal(config)
        
        return len(self.errors) == 0
    
    def _validate_target_goal(self, config: Dict):
        """Validate target goal configuration."""
        if 'target_value' not in config or config['target_value'] <= 0:
            self.errors.append("Target value must be positive")
        
        if 'timeframe' in config and config['timeframe'] not in ['daily', 'weekly', 'monthly']:
            self.errors.append("Invalid timeframe")
    
    def _validate_consistency_goal(self, config: Dict):
        """Validate consistency goal configuration."""
        if 'frequency' not in config or config['frequency'] <= 0:
            self.errors.append("Frequency must be positive")
        
        if 'period' in config and config['period'] not in ['weekly', 'monthly']:
            self.errors.append("Invalid period")
    
    def _validate_improvement_goal(self, config: Dict):
        """Validate improvement goal configuration."""
        if 'improvement_target' not in config or config['improvement_target'] <= 0:
            self.errors.append("Improvement target must be positive")
        
        if 'improvement_type' in config and config['improvement_type'] not in ['percentage', 'absolute']:
            self.errors.append("Invalid improvement type")
    
    def _validate_habit_goal(self, config: Dict):
        """Validate habit goal configuration."""
        if 'target_days' not in config or config['target_days'] <= 0:
            self.errors.append("Target days must be positive")