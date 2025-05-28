"""
Unit tests for SmartDefaultSelector
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, timedelta

from src.ui.smart_default_selector import SmartDefaultSelector, SelectionContext, SelectionFactors
from src.ui.preference_tracker import PreferenceTracker
from src.data_availability_service import (DataAvailabilityService, TimeRange, 
                                          RangeAvailability, AvailabilityLevel)


class TestSmartDefaultSelector:
    """Test cases for SmartDefaultSelector."""
    
    @pytest.fixture
    def mock_availability_service(self):
        """Create mock availability service."""
        service = Mock(spec=DataAvailabilityService)
        return service
        
    @pytest.fixture
    def mock_preference_tracker(self):
        """Create mock preference tracker."""
        tracker = Mock(spec=PreferenceTracker)
        tracker.get_preference_score.return_value = 0.5
        tracker.record_selection = Mock()
        tracker.update_preferences = Mock()
        return tracker
        
    @pytest.fixture
    def sample_range_availabilities(self):
        """Create sample range availability data."""
        return [
            RangeAvailability(
                range_type=TimeRange.TODAY,
                available=True,
                level=AvailabilityLevel.FULL,
                reason="",
                data_points=24,
                coverage_percent=100.0
            ),
            RangeAvailability(
                range_type=TimeRange.WEEK,
                available=True,
                level=AvailabilityLevel.PARTIAL,
                reason="",
                data_points=120,
                coverage_percent=75.0
            ),
            RangeAvailability(
                range_type=TimeRange.MONTH,
                available=True,
                level=AvailabilityLevel.SPARSE,
                reason="",
                data_points=200,
                coverage_percent=45.0
            )
        ]
        
    @pytest.fixture
    def smart_selector(self, mock_availability_service, mock_preference_tracker):
        """Create SmartDefaultSelector instance."""
        selector = SmartDefaultSelector(
            availability_service=mock_availability_service,
            preference_tracker=mock_preference_tracker
        )
        return selector
        
    def test_initialization(self, mock_availability_service):
        """Test SmartDefaultSelector initialization."""
        selector = SmartDefaultSelector(mock_availability_service)
        
        assert selector.availability == mock_availability_service
        assert selector.preference_tracker is not None
        assert isinstance(selector.selection_weights, dict)
        assert len(selector.fallback_order) > 0
        
    def test_initialization_with_preference_tracker(self, mock_availability_service, mock_preference_tracker):
        """Test initialization with custom preference tracker."""
        selector = SmartDefaultSelector(
            mock_availability_service, 
            mock_preference_tracker
        )
        
        assert selector.preference_tracker == mock_preference_tracker
        
    def test_select_default_range_success(self, smart_selector, sample_range_availabilities):
        """Test successful default range selection."""
        metric_type = "HeartRate"
        
        # Setup mock
        smart_selector.availability.get_available_ranges.return_value = sample_range_availabilities
        smart_selector.preference_tracker.get_preference_score.return_value = 0.7
        
        # Execute
        result = smart_selector.select_default_range(metric_type, SelectionContext.STARTUP)
        
        # Verify
        assert result is not None
        assert isinstance(result, TimeRange)
        smart_selector.preference_tracker.record_selection.assert_called_once()
        
    def test_select_default_range_no_data(self, smart_selector):
        """Test default range selection with no available data."""
        metric_type = "HeartRate"
        
        # Setup mock to return no available ranges
        smart_selector.availability.get_available_ranges.return_value = []
        
        # Execute
        result = smart_selector.select_default_range(metric_type)
        
        # Verify
        assert result is None
        smart_selector.preference_tracker.record_selection.assert_not_called()
        
    def test_calculate_range_score_components(self, smart_selector):
        """Test range score calculation components."""
        metric_type = "HeartRate"
        range_availability = RangeAvailability(
            range_type=TimeRange.WEEK,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=100,
            coverage_percent=90.0
        )
        
        # Execute
        factors = smart_selector._calculate_range_score(
            metric_type, range_availability, SelectionContext.STARTUP
        )
        
        # Verify
        assert isinstance(factors, SelectionFactors)
        assert 0.0 <= factors.data_density_score <= 1.0
        assert 0.0 <= factors.recency_score <= 1.0
        assert 0.0 <= factors.user_preference_score <= 1.0
        assert 0.0 <= factors.data_interest_score <= 1.0
        assert 0.0 <= factors.pattern_score <= 1.0
        assert 0.0 <= factors.final_score <= 1.0
        
    def test_calculate_density_score(self, smart_selector):
        """Test density score calculation."""
        # Test full coverage
        range_avail = RangeAvailability(
            range_type=TimeRange.WEEK,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=100,
            coverage_percent=100.0
        )
        
        score = smart_selector._calculate_density_score(range_avail)
        assert score >= 0.9  # Should be high for full coverage
        
        # Test sparse coverage
        range_avail.level = AvailabilityLevel.SPARSE
        range_avail.coverage_percent = 30.0
        
        score = smart_selector._calculate_density_score(range_avail)
        assert score < 0.7  # Should be lower for sparse coverage
        
    def test_calculate_recency_score(self, smart_selector):
        """Test recency score calculation."""
        # Today should have highest recency score
        today_avail = RangeAvailability(
            range_type=TimeRange.TODAY,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=24,
            coverage_percent=100.0
        )
        
        today_score = smart_selector._calculate_recency_score(today_avail)
        
        # Year should have lower recency score
        year_avail = RangeAvailability(
            range_type=TimeRange.YEAR,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=365,
            coverage_percent=100.0
        )
        
        year_score = smart_selector._calculate_recency_score(year_avail)
        
        assert today_score > year_score
        
    def test_calculate_interest_score(self, smart_selector):
        """Test interest score calculation."""
        metric_type = "HeartRate"
        
        # Test with many data points
        range_avail = RangeAvailability(
            range_type=TimeRange.MONTH,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=500,
            coverage_percent=100.0
        )
        
        high_score = smart_selector._calculate_interest_score(metric_type, range_avail)
        
        # Test with few data points
        range_avail.data_points = 2
        low_score = smart_selector._calculate_interest_score(metric_type, range_avail)
        
        assert high_score > low_score
        
    def test_calculate_pattern_score_contexts(self, smart_selector):
        """Test pattern score calculation for different contexts."""
        metric_type = "HeartRate"
        range_avail = RangeAvailability(
            range_type=TimeRange.WEEK,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=100,
            coverage_percent=100.0
        )
        
        # Test different contexts
        startup_score = smart_selector._calculate_pattern_score(
            metric_type, range_avail, SelectionContext.STARTUP
        )
        
        metric_change_score = smart_selector._calculate_pattern_score(
            metric_type, range_avail, SelectionContext.METRIC_CHANGE
        )
        
        user_initiated_score = smart_selector._calculate_pattern_score(
            metric_type, range_avail, SelectionContext.USER_INITIATED
        )
        
        # All scores should be reasonable
        assert 0.0 <= startup_score <= 1.0
        assert 0.0 <= metric_change_score <= 1.0
        assert 0.0 <= user_initiated_score <= 1.0
        
    def test_fallback_selection(self, smart_selector):
        """Test fallback selection mechanism."""
        metric_type = "HeartRate"
        
        # Mock available ranges to include week but not others
        available_ranges = [
            RangeAvailability(
                range_type=TimeRange.WEEK,
                available=True,
                level=AvailabilityLevel.FULL,
                reason="",
                data_points=100,
                coverage_percent=100.0
            )
        ]
        
        smart_selector.availability.get_available_ranges.return_value = available_ranges
        
        # Execute
        result = smart_selector._fallback_selection(metric_type)
        
        # Verify
        assert result == TimeRange.WEEK
        
    def test_fallback_selection_no_data(self, smart_selector):
        """Test fallback selection with no available data."""
        metric_type = "HeartRate"
        
        # Mock no available ranges
        smart_selector.availability.get_available_ranges.return_value = []
        
        # Execute
        result = smart_selector._fallback_selection(metric_type)
        
        # Verify
        assert result is None
        
    def test_learn_from_behavior(self, smart_selector):
        """Test learning from user behavior."""
        metric_type = "HeartRate"
        selected_range = TimeRange.WEEK
        interaction_data = {
            'view_duration': 120.0,
            'actions_taken': 5,
            'manually_selected': True,
            'context': 'view_session'
        }
        
        # Execute
        smart_selector.learn_from_behavior(metric_type, selected_range, interaction_data)
        
        # Verify
        smart_selector.preference_tracker.update_preferences.assert_called_once_with(
            metric=metric_type,
            range_type=selected_range,
            duration=120.0,
            actions=5,
            explicit=True,
            context='view_session'
        )
        
    def test_get_selection_weights(self, smart_selector):
        """Test getting selection weights."""
        weights = smart_selector.get_selection_weights()
        
        assert isinstance(weights, dict)
        assert 'data_density' in weights
        assert 'recency' in weights
        assert 'user_preference' in weights
        assert 'data_interest' in weights
        assert 'pattern_analysis' in weights
        
        # Check weights sum approximately to 1.0
        total_weight = sum(weights.values())
        assert 0.95 <= total_weight <= 1.05
        
    def test_update_selection_weights(self, smart_selector):
        """Test updating selection weights."""
        new_weights = {
            'data_density': 0.3,
            'recency': 0.2,
            'user_preference': 0.3,
            'data_interest': 0.1,
            'pattern_analysis': 0.1
        }
        
        # Execute
        smart_selector.update_selection_weights(new_weights)
        
        # Verify
        updated_weights = smart_selector.get_selection_weights()
        for key, value in new_weights.items():
            assert updated_weights[key] == value
            
    def test_selection_with_error_handling(self, smart_selector):
        """Test error handling in selection process."""
        metric_type = "HeartRate"
        
        # Setup mock to raise exception
        smart_selector.availability.get_available_ranges.side_effect = Exception("Test error")
        
        # Execute
        result = smart_selector.select_default_range(metric_type)
        
        # Should fallback gracefully
        assert result is None or isinstance(result, TimeRange)
        
    def test_export_import_preferences(self, smart_selector):
        """Test preference export and import."""
        # Test export
        exported = smart_selector.export_preferences()
        assert isinstance(exported, dict)
        
        # Test import
        test_preferences = {"test": "data"}
        smart_selector.import_preferences(test_preferences)
        smart_selector.preference_tracker.import_preferences.assert_called_once_with(test_preferences)
        
    def test_get_selection_statistics(self, smart_selector):
        """Test getting selection statistics."""
        smart_selector.preference_tracker.get_statistics.return_value = {
            'total_selections': 100,
            'explicit_selections': 25
        }
        
        stats = smart_selector.get_selection_statistics()
        
        assert isinstance(stats, dict)
        smart_selector.preference_tracker.get_statistics.assert_called_once()


class TestSelectionFactors:
    """Test cases for SelectionFactors dataclass."""
    
    def test_selection_factors_creation(self):
        """Test SelectionFactors creation."""
        factors = SelectionFactors(
            data_density_score=0.8,
            recency_score=0.9,
            user_preference_score=0.7,
            data_interest_score=0.6,
            pattern_score=0.8,
            final_score=0.76
        )
        
        assert factors.data_density_score == 0.8
        assert factors.recency_score == 0.9
        assert factors.user_preference_score == 0.7
        assert factors.data_interest_score == 0.6
        assert factors.pattern_score == 0.8
        assert factors.final_score == 0.76


class TestSelectionContext:
    """Test cases for SelectionContext enum."""
    
    def test_selection_context_values(self):
        """Test SelectionContext enum values."""
        assert SelectionContext.STARTUP.value == "startup"
        assert SelectionContext.METRIC_CHANGE.value == "metric_change"
        assert SelectionContext.USER_INITIATED.value == "user_initiated"
        assert SelectionContext.AUTO_REFRESH.value == "auto_refresh"
        
    def test_selection_context_membership(self):
        """Test SelectionContext membership."""
        contexts = list(SelectionContext)
        assert len(contexts) == 4
        assert SelectionContext.STARTUP in contexts
        assert SelectionContext.METRIC_CHANGE in contexts
        assert SelectionContext.USER_INITIATED in contexts
        assert SelectionContext.AUTO_REFRESH in contexts