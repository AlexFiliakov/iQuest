"""
Unit tests for the goal management system.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.analytics.goal_models import (
    Goal, GoalType, GoalStatus, GoalTimeframe,
    TargetGoal, ConsistencyGoal, ImprovementGoal, HabitGoal,
    GoalSuggestion, GoalProgress
)
from src.analytics.goal_management_system import (
    GoalManagementSystem, GoalStore, GoalSuggestionEngine,
    ProgressTracker, AdaptiveGoalManager, GoalValidator
)


class TestGoalModels:
    """Test goal model classes."""
    
    def test_target_goal_creation(self):
        """Test creating a target goal."""
        goal = TargetGoal(
            metric="steps",
            target_value=10000,
            timeframe=GoalTimeframe.DAILY
        )
        
        assert goal.goal_type == GoalType.TARGET
        assert goal.metric == "steps"
        assert goal.target_value == 10000
        assert goal.timeframe == GoalTimeframe.DAILY
        assert goal.name == "Reach 10000.0 steps daily"
    
    def test_target_goal_progress(self):
        """Test target goal progress calculation."""
        goal = TargetGoal(metric="steps", target_value=10000)
        
        assert goal.calculate_progress(5000) == 50.0
        assert goal.calculate_progress(10000) == 100.0
        assert goal.calculate_progress(15000) == 100.0  # Capped at 100%
        
        assert goal.is_achieved(9999) is False
        assert goal.is_achieved(10000) is True
        assert goal.is_achieved(10001) is True
    
    def test_consistency_goal_creation(self):
        """Test creating a consistency goal."""
        goal = ConsistencyGoal(
            metric="exercise",
            frequency=5,
            period=GoalTimeframe.WEEKLY,
            threshold=30.0
        )
        
        assert goal.goal_type == GoalType.CONSISTENCY
        assert goal.frequency == 5
        assert goal.threshold == 30.0
        assert "5 times per weekly" in goal.name
    
    def test_consistency_goal_progress(self):
        """Test consistency goal progress calculation."""
        goal = ConsistencyGoal(
            metric="exercise",
            frequency=5,
            threshold=30.0
        )
        
        # Test with daily values for a week
        week_data = [45, 0, 35, 40, 0, 50, 30]  # 5 days meet threshold
        assert goal.calculate_progress(week_data) == 100.0
        
        week_data = [45, 0, 35, 0, 0, 0, 30]  # 3 days meet threshold
        assert goal.calculate_progress(week_data) == 60.0
    
    def test_improvement_goal_creation(self):
        """Test creating an improvement goal."""
        goal = ImprovementGoal(
            metric="distance",
            improvement_target=10.0,
            improvement_type="percentage",
            baseline_value=100.0
        )
        
        assert goal.goal_type == GoalType.IMPROVEMENT
        assert goal.improvement_target == 10.0
        assert goal.baseline_value == 100.0
        assert "Improve distance by 10.0%" in goal.name
    
    def test_improvement_goal_progress(self):
        """Test improvement goal progress calculation."""
        goal = ImprovementGoal(
            metric="distance",
            improvement_target=10.0,
            improvement_type="percentage",
            baseline_value=100.0
        )
        
        # 5% improvement
        assert goal.calculate_progress(105) == 50.0
        
        # 10% improvement
        assert goal.calculate_progress(110) == 100.0
        
        # 15% improvement (capped)
        assert goal.calculate_progress(115) == 100.0
    
    def test_habit_goal_creation(self):
        """Test creating a habit goal."""
        goal = HabitGoal(
            metric="meditation",
            target_days=21,
            required_daily_value=10.0
        )
        
        assert goal.goal_type == GoalType.HABIT
        assert goal.target_days == 21
        assert goal.required_daily_value == 10.0
        assert "21-day meditation challenge" in goal.name
    
    def test_habit_goal_streak_tracking(self):
        """Test habit goal streak tracking."""
        goal = HabitGoal(
            metric="meditation",
            target_days=21,
            allow_skip_days=1
        )
        
        # Test streak updates
        goal.update_streak(True)
        assert goal.current_streak == 1
        
        goal.update_streak(True)
        assert goal.current_streak == 2
        
        # Skip with grace period
        goal.update_streak(False)
        assert goal.current_streak == 2
        assert goal.skips_used == 1
        
        # Skip without grace period
        goal.update_streak(False)
        assert goal.current_streak == 0
        assert goal.skips_used == 0


class TestGoalManagementSystem:
    """Test the main goal management system."""
    
    @pytest.fixture
    def mock_health_db(self):
        """Create a mock health database."""
        mock = Mock()
        mock.query_health_data.return_value = MagicMock()
        return mock
    
    @pytest.fixture
    def goal_system(self, mock_health_db):
        """Create a goal management system for testing."""
        with patch('src.analytics.goal_management_system.DatabaseManager'):
            system = GoalManagementSystem(mock_health_db)
            return system
    
    def test_create_target_goal(self, goal_system):
        """Test creating a target goal through the system."""
        config = {
            'metric': 'steps',
            'target_value': 10000,
            'timeframe': GoalTimeframe.DAILY
        }
        
        with patch.object(goal_system.goal_store, 'add_goal', return_value=1):
            goal = goal_system.create_goal('target', config)
            
            assert isinstance(goal, TargetGoal)
            assert goal.id == 1
            assert goal.metric == 'steps'
            assert goal.target_value == 10000
    
    def test_validate_goal_config(self):
        """Test goal configuration validation."""
        validator = GoalValidator('target')
        
        # Valid config
        assert validator.validate({
            'metric': 'steps',
            'target_value': 10000
        }) is True
        
        # Missing metric
        assert validator.validate({
            'target_value': 10000
        }) is False
        assert 'Metric is required' in validator.errors
        
        # Invalid target value
        validator = GoalValidator('target')
        assert validator.validate({
            'metric': 'steps',
            'target_value': -100
        }) is False
        assert 'Target value must be positive' in validator.errors
    
    def test_get_active_goals(self, goal_system):
        """Test retrieving active goals."""
        mock_goals = [
            TargetGoal(metric='steps', target_value=10000),
            ConsistencyGoal(metric='exercise', frequency=5)
        ]
        
        with patch.object(goal_system.goal_store, 'get_active_goals', return_value=mock_goals):
            goals = goal_system.get_active_goals()
            
            assert len(goals) == 2
            assert isinstance(goals[0], TargetGoal)
            assert isinstance(goals[1], ConsistencyGoal)


class TestGoalSuggestionEngine:
    """Test goal suggestion generation."""
    
    @pytest.fixture
    def suggestion_engine(self):
        """Create a suggestion engine for testing."""
        mock_health_db = Mock()
        mock_daily_calc = Mock()
        mock_weekly_calc = Mock()
        mock_monthly_calc = Mock()
        
        return GoalSuggestionEngine(
            mock_health_db,
            mock_daily_calc,
            mock_weekly_calc,
            mock_monthly_calc
        )
    
    def test_generate_suggestions_no_data(self, suggestion_engine):
        """Test generating suggestions with no historical data."""
        suggestion_engine._get_metric_history = Mock(return_value=MagicMock(empty=True))
        
        suggestions = suggestion_engine.suggest_goals('steps')
        
        assert len(suggestions) > 0
        assert all(isinstance(s, GoalSuggestion) for s in suggestions)
    
    def test_achievability_scoring(self, suggestion_engine):
        """Test achievability score calculation."""
        suggestion = GoalSuggestion(
            goal_type=GoalType.TARGET,
            metric='steps',
            suggested_value=10000,
            timeframe=GoalTimeframe.DAILY
        )
        
        stats = {
            'mean': 8000,
            'consistency_score': 0.8
        }
        
        score = suggestion_engine._calculate_achievability(suggestion, stats, None)
        
        assert 0 <= score <= 1
    
    def test_impact_scoring(self, suggestion_engine):
        """Test impact score calculation."""
        suggestion = GoalSuggestion(
            goal_type=GoalType.IMPROVEMENT,
            metric='distance',
            suggested_value=15.0,  # 15% improvement
            timeframe=GoalTimeframe.MONTHLY
        )
        
        stats = {'mean': 100}
        
        impact = suggestion_engine._calculate_impact(suggestion, stats)
        
        assert 0 <= impact <= 1
        assert impact == 0.15  # 15% improvement


class TestProgressTracker:
    """Test progress tracking functionality."""
    
    @pytest.fixture
    def progress_tracker(self):
        """Create a progress tracker for testing."""
        mock_db = Mock()
        mock_health_db = Mock()
        return ProgressTracker(mock_db, mock_health_db)
    
    def test_progress_history_retrieval(self, progress_tracker):
        """Test retrieving progress history."""
        mock_rows = [
            {
                'goal_id': 1,
                'date': '2024-01-01',
                'value': 8000,
                'progress_percentage': 80.0,
                'notes': None
            },
            {
                'goal_id': 1,
                'date': '2024-01-02',
                'value': 10000,
                'progress_percentage': 100.0,
                'notes': 'Goal achieved!'
            }
        ]
        
        with patch.object(progress_tracker.db_manager, 'get_connection') as mock_conn:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = mock_rows
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            
            history = progress_tracker.get_progress_history(1, days=7)
            
            assert len(history) == 2
            assert history[0].value == 8000
            assert history[1].progress_percentage == 100.0


class TestAdaptiveGoalManager:
    """Test adaptive goal management."""
    
    def test_detect_goal_too_easy(self):
        """Test detection of goals that are too easy."""
        manager = AdaptiveGoalManager()
        
        # All 100% for a week
        progress_history = [100] * 7
        assert manager._is_goal_too_easy(progress_history) is True
        
        # Mixed progress
        progress_history = [100, 90, 100, 85, 100, 95, 100]
        assert manager._is_goal_too_easy(progress_history) is False
    
    def test_detect_goal_too_hard(self):
        """Test detection of goals that are too difficult."""
        manager = AdaptiveGoalManager()
        
        # All below 20% for a week
        progress_history = [10, 15, 5, 18, 12, 8, 15]
        assert manager._is_goal_too_hard(progress_history) is True
        
        # Some progress
        progress_history = [10, 25, 30, 18, 40, 35, 45]
        assert manager._is_goal_too_hard(progress_history) is False
    
    def test_detect_plateau(self):
        """Test plateau detection."""
        manager = AdaptiveGoalManager()
        
        # Plateaued progress
        progress_history = [50, 51, 49, 50, 52, 51, 50,  # Week 1
                          52, 51, 50, 49, 51, 52, 51]     # Week 2
        assert manager._detect_plateau(progress_history) is True
        
        # Improving progress
        progress_history = [40, 42, 45, 48, 50, 52, 55,  # Week 1
                          58, 60, 62, 65, 68, 70, 72]     # Week 2
        assert manager._detect_plateau(progress_history) is False


if __name__ == "__main__":
    pytest.main([__file__])