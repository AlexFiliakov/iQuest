"""
Unit tests for PreferenceTracker
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from datetime import datetime, timedelta

from PyQt6.QtCore import QSettings

from src.ui.preference_tracker import PreferenceTracker
from src.ui.settings_manager import SettingsManager
from src.data_availability_service import TimeRange


class TestPreferenceTracker:
    """Test cases for PreferenceTracker."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock QSettings."""
        settings = Mock(spec=QSettings)
        settings.allKeys.return_value = []
        settings.value.return_value = None
        settings.setValue = Mock()
        settings.clear = Mock()
        settings.sync = Mock()
        settings.beginGroup = Mock()
        settings.endGroup = Mock()
        return settings
        
    @pytest.fixture
    def mock_settings_manager(self, mock_settings):
        """Create mock SettingsManager."""
        manager = Mock(spec=SettingsManager)
        manager.settings = mock_settings
        return manager
        
    @pytest.fixture
    def preference_tracker(self, mock_settings_manager):
        """Create PreferenceTracker instance."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_qsettings.return_value = mock_settings_manager.settings
            tracker = PreferenceTracker(mock_settings_manager)
            return tracker
            
    @pytest.fixture
    def sample_preferences(self):
        """Create sample preference data."""
        return {
            'HeartRate_week': {
                'score': 0.8,
                'count': 10,
                'last_used': datetime.now().isoformat(),
                'total_duration': 1200.0,
                'total_actions': 25,
                'explicit_selections': 7,
                'selection_types': {'manual': 7, 'auto': 3},
                'contexts': {'startup': 5, 'metric_change': 5}
            },
            'Steps_month': {
                'score': 0.6,
                'count': 5,
                'last_used': (datetime.now() - timedelta(days=7)).isoformat(),
                'total_duration': 600.0,
                'total_actions': 10,
                'explicit_selections': 3,
                'selection_types': {'manual': 3, 'auto': 2},
                'contexts': {'startup': 2, 'user_initiated': 3}
            }
        }
        
    def test_initialization(self, mock_settings_manager):
        """Test PreferenceTracker initialization."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_qsettings.return_value = mock_settings_manager.settings
            tracker = PreferenceTracker(mock_settings_manager)
            
            assert tracker.settings == mock_settings_manager.settings
            assert isinstance(tracker.preferences, dict)
            assert isinstance(tracker.session_data, dict)
            assert tracker.weekly_decay_factor == 0.95
            assert tracker.max_preference_age_days == 90
            
    def test_initialization_without_settings_manager(self):
        """Test initialization without settings manager."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_settings = Mock(spec=QSettings)
            mock_settings.allKeys.return_value = []
            mock_settings.beginGroup = Mock()
            mock_settings.endGroup = Mock()
            mock_qsettings.return_value = mock_settings
            
            tracker = PreferenceTracker()
            
            assert tracker.settings == mock_settings
            mock_qsettings.assert_called_once()
            
    def test_get_preference_score_existing(self, preference_tracker, sample_preferences):
        """Test getting preference score for existing preference."""
        preference_tracker.preferences = sample_preferences
        
        score = preference_tracker.get_preference_score("HeartRate", TimeRange.WEEK)
        
        # Score should be affected by time decay
        assert 0.0 <= score <= 1.0
        # Since it's recent, should be close to original score
        assert score >= 0.7
        
    def test_get_preference_score_nonexistent(self, preference_tracker):
        """Test getting preference score for non-existent preference."""
        score = preference_tracker.get_preference_score("NonExistent", TimeRange.WEEK)
        
        # Should return neutral score
        assert score == 0.5
        
    def test_get_preference_score_with_decay(self, preference_tracker):
        """Test preference score with time decay."""
        # Create old preference
        old_preference = {
            'HeartRate_week': {
                'score': 0.9,
                'count': 10,
                'last_used': (datetime.now() - timedelta(days=30)).isoformat()
            }
        }
        preference_tracker.preferences = old_preference
        
        score = preference_tracker.get_preference_score("HeartRate", TimeRange.WEEK)
        
        # Score should be decayed
        assert score < 0.9
        assert score > 0.0
        
    def test_record_selection(self, preference_tracker):
        """Test recording a selection."""
        metric = "HeartRate"
        range_type = TimeRange.WEEK
        selection_type = "manual"
        context = "startup"
        
        # Execute
        preference_tracker.record_selection(metric, range_type, selection_type, context)
        
        # Verify preference was created/updated
        key = f"{metric}_{range_type.value}"
        assert key in preference_tracker.preferences
        
        preference = preference_tracker.preferences[key]
        assert preference['count'] == 1
        assert selection_type in preference['selection_types']
        assert context in preference['contexts']
        assert preference['selection_types'][selection_type] == 1
        assert preference['contexts'][context] == 1
        
    def test_record_selection_existing_preference(self, preference_tracker, sample_preferences):
        """Test recording selection for existing preference."""
        preference_tracker.preferences = sample_preferences.copy()
        
        original_count = sample_preferences['HeartRate_week']['count']
        
        # Execute
        preference_tracker.record_selection("HeartRate", TimeRange.WEEK, "auto", "refresh")
        
        # Verify count increased
        key = "HeartRate_week"
        assert preference_tracker.preferences[key]['count'] == original_count + 1
        
    def test_update_preferences_explicit_selection(self, preference_tracker):
        """Test updating preferences with explicit selection."""
        metric = "HeartRate"
        range_type = TimeRange.WEEK
        
        # Execute
        preference_tracker.update_preferences(
            metric=metric,
            range_type=range_type,
            duration=120.0,
            actions=5,
            explicit=True,
            context="user_action"
        )
        
        # Verify preference was updated
        key = f"{metric}_{range_type.value}"
        preference = preference_tracker.preferences[key]
        
        assert preference['count'] == 1
        assert preference['total_duration'] == 120.0
        assert preference['total_actions'] == 5
        assert preference['explicit_selections'] == 1
        # Score should be boosted for explicit selection
        assert preference['score'] > 0.5
        
    def test_update_preferences_long_duration(self, preference_tracker):
        """Test updating preferences with long view duration."""
        metric = "Steps"
        range_type = TimeRange.MONTH
        
        # Execute with long duration
        preference_tracker.update_preferences(
            metric=metric,
            range_type=range_type,
            duration=180.0,  # 3 minutes
            actions=3,
            explicit=False
        )
        
        # Verify score boost for long duration
        key = f"{metric}_{range_type.value}"
        preference = preference_tracker.preferences[key]
        
        # Should get bonuses for >30s and >120s duration
        assert preference['score'] > 0.55  # Base 0.5 + bonuses
        
    def test_update_preferences_many_actions(self, preference_tracker):
        """Test updating preferences with many actions."""
        metric = "HeartRate"
        range_type = TimeRange.TODAY
        
        # Execute with many actions
        preference_tracker.update_preferences(
            metric=metric,
            range_type=range_type,
            duration=60.0,
            actions=10,  # Heavy interaction
            explicit=False
        )
        
        # Verify score boost for actions
        key = f"{metric}_{range_type.value}"
        preference = preference_tracker.preferences[key]
        
        # Should get bonuses for actions
        assert preference['score'] > 0.55
        
    def test_update_preferences_short_duration_penalty(self, preference_tracker):
        """Test updating preferences with short duration penalty."""
        metric = "Steps"
        range_type = TimeRange.YEAR
        
        # Execute with very short duration, non-explicit
        preference_tracker.update_preferences(
            metric=metric,
            range_type=range_type,
            duration=3.0,  # Very short
            actions=0,
            explicit=False
        )
        
        # Verify score penalty for short non-explicit view
        key = f"{metric}_{range_type.value}"
        preference = preference_tracker.preferences[key]
        
        # Should be penalized below neutral
        assert preference['score'] < 0.5
        
    def test_get_top_preferences(self, preference_tracker, sample_preferences):
        """Test getting top preferences for a metric."""
        preference_tracker.preferences = sample_preferences
        
        # Execute
        top_prefs = preference_tracker.get_top_preferences("HeartRate", limit=2)
        
        # Verify
        assert isinstance(top_prefs, list)
        assert len(top_prefs) <= 2
        
        if top_prefs:
            # Should be sorted by score (highest first)
            for i in range(len(top_prefs) - 1):
                assert top_prefs[i]['score'] >= top_prefs[i + 1]['score']
                
            # Check structure
            pref = top_prefs[0]
            assert 'range_type' in pref
            assert 'score' in pref
            assert 'count' in pref
            assert 'last_used' in pref
            assert 'avg_duration' in pref
            assert 'explicit_selections' in pref
            
    def test_get_statistics(self, preference_tracker, sample_preferences):
        """Test getting preference statistics."""
        preference_tracker.preferences = sample_preferences
        
        # Execute
        stats = preference_tracker.get_statistics()
        
        # Verify
        assert isinstance(stats, dict)
        assert 'total_preferences' in stats
        assert 'active_preferences' in stats
        assert 'total_selections' in stats
        assert 'explicit_selections' in stats
        assert 'explicit_percentage' in stats
        assert 'total_view_time_hours' in stats
        assert 'avg_view_time_seconds' in stats
        assert 'range_type_popularity' in stats
        assert 'metric_usage' in stats
        
        # Check calculations
        assert stats['total_preferences'] == len(sample_preferences)
        assert stats['explicit_percentage'] >= 0.0
        assert stats['explicit_percentage'] <= 100.0
        
    def test_export_preferences(self, preference_tracker, sample_preferences):
        """Test exporting preferences."""
        preference_tracker.preferences = sample_preferences
        
        # Execute
        exported = preference_tracker.export_preferences()
        
        # Verify
        assert isinstance(exported, dict)
        assert 'preferences' in exported
        assert 'export_time' in exported
        assert 'statistics' in exported
        assert exported['preferences'] == sample_preferences
        
    def test_import_preferences(self, preference_tracker):
        """Test importing preferences."""
        import_data = {
            'preferences': {
                'TestMetric_week': {
                    'score': 0.7,
                    'count': 5,
                    'last_used': datetime.now().isoformat()
                }
            },
            'export_time': datetime.now().isoformat()
        }
        
        # Execute
        preference_tracker.import_preferences(import_data)
        
        # Verify
        assert 'TestMetric_week' in preference_tracker.preferences
        assert preference_tracker.preferences['TestMetric_week']['score'] == 0.7
        
    def test_import_preferences_merge_newer(self, preference_tracker):
        """Test importing preferences merges newer data."""
        # Set up existing preference
        old_time = datetime.now() - timedelta(days=1)
        preference_tracker.preferences = {
            'TestMetric_week': {
                'score': 0.5,
                'count': 3,
                'last_used': old_time.isoformat()
            }
        }
        
        # Import newer preference
        new_time = datetime.now()
        import_data = {
            'preferences': {
                'TestMetric_week': {
                    'score': 0.8,
                    'count': 7,
                    'last_used': new_time.isoformat()
                }
            }
        }
        
        # Execute
        preference_tracker.import_preferences(import_data)
        
        # Verify newer data was used
        assert preference_tracker.preferences['TestMetric_week']['score'] == 0.8
        assert preference_tracker.preferences['TestMetric_week']['count'] == 7
        
    def test_reset_preferences(self, preference_tracker, sample_preferences):
        """Test resetting all preferences."""
        preference_tracker.preferences = sample_preferences.copy()
        
        # Execute
        preference_tracker.reset_preferences()
        
        # Verify
        assert len(preference_tracker.preferences) == 0
        
    def test_get_preference_details(self, preference_tracker, sample_preferences):
        """Test getting detailed preference information."""
        preference_tracker.preferences = sample_preferences
        
        # Execute
        details = preference_tracker.get_preference_details("HeartRate", TimeRange.WEEK)
        
        # Verify
        assert details is not None
        assert isinstance(details, dict)
        assert 'current_score' in details
        assert 'avg_duration' in details
        assert details['count'] == sample_preferences['HeartRate_week']['count']
        
    def test_get_preference_details_nonexistent(self, preference_tracker):
        """Test getting details for non-existent preference."""
        details = preference_tracker.get_preference_details("NonExistent", TimeRange.WEEK)
        
        assert details is None
        
    def test_cleanup_old_preferences(self, preference_tracker):
        """Test cleanup of old preferences."""
        # Create preferences with old dates
        old_date = datetime.now() - timedelta(days=100)
        recent_date = datetime.now() - timedelta(days=10)
        
        preference_tracker.preferences = {
            'Old_week': {
                'score': 0.7,
                'count': 5,
                'last_used': old_date.isoformat()
            },
            'Recent_week': {
                'score': 0.8,
                'count': 3,
                'last_used': recent_date.isoformat()
            }
        }
        
        # Execute cleanup
        preference_tracker._cleanup_old_preferences()
        
        # Verify old preference was removed, recent kept
        assert 'Old_week' not in preference_tracker.preferences
        assert 'Recent_week' in preference_tracker.preferences
        
    def test_save_and_load_preferences_integration(self, mock_settings_manager):
        """Test preference save and load integration."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_qsettings.return_value = mock_settings_manager.settings
            
            # Setup mock to return saved data
            test_pref = {
                'score': 0.8,
                'count': 5,
                'last_used': datetime.now().isoformat()
            }
            
            mock_settings_manager.settings.allKeys.return_value = ['HeartRate_week']
            mock_settings_manager.settings.value.return_value = json.dumps(test_pref)
            
            # Create new tracker (should load preferences)
            tracker = PreferenceTracker(mock_settings_manager)
            
            # Verify preferences were loaded
            assert 'HeartRate_week' in tracker.preferences
            assert tracker.preferences['HeartRate_week']['score'] == 0.8
            
    def test_error_handling_in_load_preferences(self, mock_settings_manager):
        """Test error handling during preference loading."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_qsettings.return_value = mock_settings_manager.settings
            
            # Setup mock to return invalid JSON
            mock_settings_manager.settings.allKeys.return_value = ['Invalid_pref']
            mock_settings_manager.settings.value.return_value = "invalid_json"
            
            # Should not raise exception
            tracker = PreferenceTracker(mock_settings_manager)
            
            # Should have empty preferences due to parsing error
            assert len(tracker.preferences) == 0
            
    def test_error_handling_in_methods(self, preference_tracker):
        """Test error handling in various methods."""
        # Test with invalid preference data
        preference_tracker.preferences = {
            'Invalid_pref': {
                'last_used': 'invalid_date_string'
            }
        }
        
        # These should not raise exceptions
        score = preference_tracker.get_preference_score("Invalid", TimeRange.WEEK)
        assert score == 0.5  # Should return neutral score
        
        stats = preference_tracker.get_statistics()
        assert isinstance(stats, dict)  # Should return some stats
        
        exported = preference_tracker.export_preferences()
        assert isinstance(exported, dict)  # Should return some data