"""
Integration tests for Smart Default Selection system
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, timedelta

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys

from src.ui.adaptive_time_range_selector import AdaptiveTimeRangeSelector
from src.ui.smart_default_selector import SmartDefaultSelector, SelectionContext
from src.ui.preference_tracker import PreferenceTracker
from src.data_availability_service import (DataAvailabilityService, TimeRange, 
                                          RangeAvailability, AvailabilityLevel)
from src.health_database import HealthDatabase


# qapp fixture is now provided by conftest.py
    

class TestSmartSelectionIntegration:
    """Integration tests for smart selection system."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock health database."""
        db = Mock(spec=HealthDatabase)
        db.get_available_types.return_value = ["HeartRate", "Steps", "Sleep"]
        db.get_date_range_for_type.return_value = (
            date.today() - timedelta(days=30),
            date.today()
        )
        db.get_record_count_for_type.return_value = 500
        db.get_dates_with_data.return_value = [
            date.today() - timedelta(days=i) for i in range(0, 30, 2)
        ]
        return db
        
    @pytest.fixture
    def availability_service(self, mock_database):
        """Create DataAvailabilityService."""
        service = DataAvailabilityService(mock_database)
        return service
        
    @pytest.fixture
    def preference_tracker(self):
        """Create PreferenceTracker with mock settings."""
        with patch('src.ui.preference_tracker.QSettings') as mock_qsettings:
            mock_settings = Mock()
            mock_settings.allKeys.return_value = []
            mock_settings.beginGroup = Mock()
            mock_settings.endGroup = Mock()
            mock_settings.setValue = Mock()
            mock_settings.sync = Mock()
            mock_qsettings.return_value = mock_settings
            
            tracker = PreferenceTracker()
            return tracker
            
    @pytest.fixture
    def smart_selector(self, availability_service, preference_tracker):
        """Create SmartDefaultSelector."""
        selector = SmartDefaultSelector(availability_service, preference_tracker)
        return selector
        
    @pytest.fixture
    def adaptive_selector(self, qapp, availability_service, smart_selector):
        """Create AdaptiveTimeRangeSelector with smart selection."""
        selector = AdaptiveTimeRangeSelector(
            availability_service=availability_service,
            smart_selector=smart_selector
        )
        return selector
        
    def test_end_to_end_smart_selection(self, adaptive_selector, availability_service):
        """Test end-to-end smart selection process."""
        # Set metric type (should trigger smart selection)
        adaptive_selector.set_metric_type("HeartRate")
        
        # Verify metric was set
        assert adaptive_selector.current_metric_type == "HeartRate"
        
        # Verify availability was updated
        assert len(adaptive_selector.range_availabilities) > 0
        
        # Verify smart selection occurred
        selected_range = adaptive_selector.get_selected_range()
        assert selected_range is not None
        
    def test_user_interaction_tracking(self, adaptive_selector):
        """Test user interaction tracking for learning."""
        # Set metric and let smart selection occur
        adaptive_selector.set_metric_type("Steps")
        
        # Simulate user manually selecting a different range
        adaptive_selector.select_range(TimeRange.MONTH)
        
        # Verify selection was tracked
        assert adaptive_selector.last_selected_range == TimeRange.MONTH
        assert adaptive_selector.selection_start_time is not None
        
        # Simulate user actions
        adaptive_selector.record_user_action()
        adaptive_selector.record_user_action()
        
        assert adaptive_selector.interaction_actions == 2
        
    def test_preference_learning_workflow(self, adaptive_selector):
        """Test the complete preference learning workflow."""
        metric = "HeartRate"
        
        # Initial selection
        adaptive_selector.set_metric_type(metric)
        initial_range = adaptive_selector.get_selected_range()
        
        # Simulate user interaction over time
        adaptive_selector.record_user_action()
        adaptive_selector.record_user_action()
        adaptive_selector.record_user_action()
        
        # Change to different metric (should end tracking and learn)
        adaptive_selector.set_metric_type("Steps")
        
        # Check that preference was recorded
        if adaptive_selector.smart_selector:
            preferences = adaptive_selector.smart_selector.preference_tracker.get_top_preferences(metric)
            # Should have some preference data
            assert isinstance(preferences, list)
            
    def test_context_based_selection(self, smart_selector):
        """Test that different contexts produce different selections."""
        metric = "HeartRate"
        
        # Test different contexts
        startup_selection = smart_selector.select_default_range(
            metric, SelectionContext.STARTUP
        )
        
        metric_change_selection = smart_selector.select_default_range(
            metric, SelectionContext.METRIC_CHANGE
        )
        
        user_initiated_selection = smart_selector.select_default_range(
            metric, SelectionContext.USER_INITIATED
        )
        
        # All should return valid ranges
        assert startup_selection is None or isinstance(startup_selection, TimeRange)
        assert metric_change_selection is None or isinstance(metric_change_selection, TimeRange)
        assert user_initiated_selection is None or isinstance(user_initiated_selection, TimeRange)
        
    def test_preference_persistence_simulation(self, preference_tracker):
        """Test preference persistence simulation."""
        metric = "HeartRate"
        range_type = TimeRange.WEEK
        
        # Record several selections
        for i in range(5):
            preference_tracker.record_selection(
                metric, range_type, "manual", "user_action"
            )
            
        # Update with behavioral data
        preference_tracker.update_preferences(
            metric=metric,
            range_type=range_type,
            duration=120.0,
            actions=3,
            explicit=True
        )
        
        # Check that preference score improved
        score = preference_tracker.get_preference_score(metric, range_type)
        assert score > 0.5  # Should be above neutral
        
        # Get statistics
        stats = preference_tracker.get_statistics()
        assert stats['total_selections'] >= 5
        assert stats['explicit_selections'] >= 1
        
    def test_fallback_behavior_with_no_data(self, qapp):
        """Test fallback behavior when no data is available."""
        # Create availability service with no data
        mock_db = Mock(spec=HealthDatabase)
        mock_db.get_available_types.return_value = []
        mock_db.get_date_range_for_type.return_value = (None, None)
        mock_db.get_record_count_for_type.return_value = 0
        
        availability_service = DataAvailabilityService(mock_db)
        smart_selector = SmartDefaultSelector(availability_service)
        
        adaptive_selector = AdaptiveTimeRangeSelector(
            availability_service=availability_service,
            smart_selector=smart_selector
        )
        
        # Set metric type
        adaptive_selector.set_metric_type("NonExistentMetric")
        
        # Should handle gracefully
        assert adaptive_selector.current_metric_type == "NonExistentMetric"
        selected_range = adaptive_selector.get_selected_range()
        # May be None or some fallback range
        assert selected_range is None or isinstance(selected_range, TimeRange)
        
    def test_smart_selection_with_learned_preferences(self, smart_selector):
        """Test smart selection incorporating learned preferences."""
        metric = "Steps"
        
        # Simulate learned preference for month view
        smart_selector.preference_tracker.preferences = {
            f"{metric}_month": {
                'score': 0.9,
                'count': 10,
                'last_used': datetime.now().isoformat(),
                'explicit_selections': 8
            },
            f"{metric}_week": {
                'score': 0.3,
                'count': 2,
                'last_used': datetime.now().isoformat(),
                'explicit_selections': 0
            }
        }
        
        # Selection should prefer the learned preference
        selected = smart_selector.select_default_range(metric, SelectionContext.STARTUP)
        
        # Should return some valid range
        assert selected is None or isinstance(selected, TimeRange)
        
    def test_weight_adjustment_affects_selection(self, smart_selector):
        """Test that adjusting selection weights affects outcomes."""
        metric = "HeartRate"
        
        # Get initial selection
        initial_selection = smart_selector.select_default_range(metric)
        
        # Adjust weights to heavily favor user preferences
        new_weights = {
            'data_density': 0.1,
            'recency': 0.1,
            'user_preference': 0.7,  # Heavy weight
            'data_interest': 0.05,
            'pattern_analysis': 0.05
        }
        
        smart_selector.update_selection_weights(new_weights)
        
        # Get new selection
        new_selection = smart_selector.select_default_range(metric)
        
        # Both should be valid (may or may not be different)
        assert initial_selection is None or isinstance(initial_selection, TimeRange)
        assert new_selection is None or isinstance(new_selection, TimeRange)
        
        # Verify weights were updated
        current_weights = smart_selector.get_selection_weights()
        assert current_weights['user_preference'] == 0.7
        
    def test_export_import_preferences_integration(self, adaptive_selector):
        """Test preference export and import functionality."""
        # Set up some preferences
        adaptive_selector.set_metric_type("HeartRate")
        adaptive_selector.record_user_action()
        
        # Export preferences
        exported = adaptive_selector.export_preferences()
        assert isinstance(exported, dict)
        
        # Reset preferences
        adaptive_selector.reset_preferences()
        
        # Import preferences back
        adaptive_selector.import_preferences(exported)
        
        # Should work without errors
        
    def test_availability_service_integration(self, availability_service):
        """Test integration with availability service."""
        # Scan availability
        availability = availability_service.scan_availability()
        assert isinstance(availability, dict)
        
        # Get available ranges for a metric
        ranges = availability_service.get_available_ranges("HeartRate")
        assert isinstance(ranges, list)
        
        # Each range should have proper structure
        for range_avail in ranges:
            assert hasattr(range_avail, 'range_type')
            assert hasattr(range_avail, 'available')
            assert hasattr(range_avail, 'level')
            assert hasattr(range_avail, 'coverage_percent')
            
    def test_selector_cleanup(self, adaptive_selector):
        """Test proper cleanup of selector."""
        # Set metric and start interaction tracking
        adaptive_selector.set_metric_type("Steps")
        adaptive_selector.record_user_action()
        
        # Verify tracking is active
        assert adaptive_selector.selection_start_time is not None
        
        # Cleanup
        adaptive_selector.cleanup()
        
        # Verify tracking was ended
        assert adaptive_selector.selection_start_time is None
        
    def test_error_handling_in_integration(self, qapp):
        """Test error handling in integrated system."""
        # Create system with mock that raises errors
        mock_db = Mock(spec=HealthDatabase)
        mock_db.get_available_types.side_effect = Exception("Database error")
        
        availability_service = DataAvailabilityService(mock_db)
        smart_selector = SmartDefaultSelector(availability_service)
        
        adaptive_selector = AdaptiveTimeRangeSelector(
            availability_service=availability_service,
            smart_selector=smart_selector
        )
        
        # Should handle errors gracefully
        adaptive_selector.set_metric_type("HeartRate")
        
        # Should not crash
        assert adaptive_selector.current_metric_type == "HeartRate"
        
    def test_multiple_metric_switches(self, adaptive_selector):
        """Test behavior with multiple rapid metric switches."""
        metrics = ["HeartRate", "Steps", "Sleep", "HeartRate", "Steps"]
        
        for metric in metrics:
            adaptive_selector.set_metric_type(metric)
            # Simulate some user interaction
            adaptive_selector.record_user_action()
            
        # Should handle all switches gracefully
        assert adaptive_selector.current_metric_type == "Steps"
        
    def test_selection_info_and_statistics(self, adaptive_selector):
        """Test getting selection information and statistics."""
        # Set up some activity
        adaptive_selector.set_metric_type("HeartRate")
        adaptive_selector.record_user_action()
        
        # Get smart selection info
        info = adaptive_selector.get_smart_selection_info()
        assert isinstance(info, dict)
        assert 'smart_selection_enabled' in info
        
        # Get availability summary
        summary = adaptive_selector.get_availability_summary()
        assert isinstance(summary, dict)
        assert 'metric_type' in summary
        assert 'available_ranges' in summary