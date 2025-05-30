"""Unit tests for adaptive display logic components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
from typing import List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.data_availability_service import (
    DataAvailabilityService, AvailabilityLevel, TimeRange, 
    DataRange, RangeAvailability
)
from src.health_database import HealthDatabase


class TestDataAvailabilityService:
    """Test cases for DataAvailabilityService."""
    
    @pytest.fixture
    def mock_database(self):
        """Create a mock HealthDatabase."""
        db = Mock(spec=HealthDatabase)
        return db
        
    @pytest.fixture
    def availability_service(self, mock_database):
        """Create DataAvailabilityService with mock database."""
        return DataAvailabilityService(mock_database)
        
    def test_initialization(self, availability_service):
        """Test service initialization."""
        assert availability_service.db is not None
        assert availability_service.availability_cache == {}
        assert availability_service.update_callbacks == []
        assert availability_service.last_scan is None
        
    def test_callback_registration(self, availability_service):
        """Test callback registration and deregistration."""
        callback = Mock()
        
        # Register callback
        availability_service.register_callback(callback)
        assert callback in availability_service.update_callbacks
        
        # Unregister callback
        availability_service.unregister_callback(callback)
        assert callback not in availability_service.update_callbacks
        
    def test_cache_invalidation(self, availability_service):
        """Test cache invalidation."""
        # Add some data to cache
        availability_service.availability_cache['test'] = Mock()
        availability_service.last_scan = date.today()
        
        # Invalidate cache
        availability_service.invalidate_cache()
        
        assert availability_service.availability_cache == {}
        assert availability_service.last_scan is None
        
    def test_scan_availability_empty_database(self, availability_service, mock_database):
        """Test availability scanning with empty database."""
        mock_database.get_available_types.return_value = []
        
        result = availability_service.scan_availability()
        
        assert result == {}
        assert availability_service.availability_cache == {}
        
    def test_scan_availability_with_data(self, availability_service, mock_database):
        """Test availability scanning with data."""
        # Setup mock data
        mock_database.get_available_types.return_value = ['StepCount', 'HeartRate']
        
        # Mock StepCount data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        mock_database.get_date_range_for_type.side_effect = [
            (start_date, end_date),  # StepCount
            (start_date, end_date)   # HeartRate
        ]
        mock_database.get_record_count_for_type.side_effect = [1000, 500]
        mock_database.get_dates_with_data.side_effect = [
            [start_date + timedelta(days=i) for i in range(31)],  # All days for StepCount
            [start_date + timedelta(days=i) for i in range(0, 31, 2)]  # Every other day for HeartRate
        ]
        
        result = availability_service.scan_availability()
        
        assert len(result) == 2
        assert 'StepCount' in result
        assert 'HeartRate' in result
        
        # Check StepCount (should be FULL)
        step_data = result['StepCount']
        assert step_data.level == AvailabilityLevel.FULL
        assert step_data.total_points == 1000
        
        # Check HeartRate (should be PARTIAL due to gaps)
        heart_data = result['HeartRate']
        assert heart_data.level in [AvailabilityLevel.PARTIAL, AvailabilityLevel.SPARSE]
        assert heart_data.total_points == 500
        
    def test_availability_level_determination(self, availability_service):
        """Test availability level determination logic."""
        # Test FULL availability (90%+ coverage, 80%+ density)
        level = availability_service._determine_availability_level(1.0, [], 30)
        assert level == AvailabilityLevel.FULL
        
        # Test PARTIAL availability (60%+ coverage, 30%+ density)
        level = availability_service._determine_availability_level(0.5, [(date(2024, 1, 1), date(2024, 1, 10))], 30)
        assert level == AvailabilityLevel.PARTIAL
        
        # Test SPARSE availability (20%+ coverage or 10%+ density)
        level = availability_service._determine_availability_level(0.15, [(date(2024, 1, 1), date(2024, 1, 25))], 30)
        assert level == AvailabilityLevel.SPARSE
        
        # Test NONE availability
        level = availability_service._determine_availability_level(0.0, [], 30)
        assert level == AvailabilityLevel.NONE
        
    def test_get_available_ranges_no_data(self, availability_service, mock_database):
        """Test getting available ranges with no data."""
        mock_database.get_available_types.return_value = []
        availability_service.scan_availability()
        
        ranges = availability_service.get_available_ranges('NonExistentMetric')
        assert ranges == []
        
    def test_get_available_ranges_with_data(self, availability_service, mock_database):
        """Test getting available ranges with good data."""
        # Setup mock for metric with good recent data
        today = date.today()
        start_date = today - timedelta(days=30)
        
        mock_database.get_available_types.return_value = ['StepCount']
        mock_database.get_date_range_for_type.return_value = (start_date, today)
        mock_database.get_record_count_for_type.return_value = 1000
        mock_database.get_dates_with_data.return_value = [
            start_date + timedelta(days=i) for i in range(31)
        ]
        
        availability_service.scan_availability()
        ranges = availability_service.get_available_ranges('StepCount')
        
        # Should have multiple available ranges
        assert len(ranges) > 0
        
        # Check that ranges have proper structure
        for range_availability in ranges:
            assert isinstance(range_availability, RangeAvailability)
            assert hasattr(range_availability, 'range_type')
            assert hasattr(range_availability, 'available')
            assert hasattr(range_availability, 'level')
            
    def test_suggest_default_range(self, availability_service, mock_database):
        """Test default range suggestion."""
        # Setup mock data with week availability
        today = date.today()
        start_date = today - timedelta(days=10)
        
        mock_database.get_available_types.return_value = ['StepCount']
        mock_database.get_date_range_for_type.return_value = (start_date, today)
        mock_database.get_record_count_for_type.return_value = 100
        mock_database.get_dates_with_data.return_value = [
            start_date + timedelta(days=i) for i in range(11)
        ]
        
        availability_service.scan_availability()
        suggested = availability_service.suggest_default_range('StepCount')
        
        # Should suggest a valid time range or None
        assert suggested is None or isinstance(suggested, TimeRange)
        
    def test_edge_case_future_dates(self, availability_service, mock_database):
        """Test handling of future dates."""
        # Setup mock data that ends in the past
        past_date = date.today() - timedelta(days=10)
        start_date = past_date - timedelta(days=30)
        
        mock_database.get_available_types.return_value = ['StepCount']
        mock_database.get_date_range_for_type.return_value = (start_date, past_date)
        mock_database.get_record_count_for_type.return_value = 100
        mock_database.get_dates_with_data.return_value = [
            start_date + timedelta(days=i) for i in range(31)
        ]
        
        availability_service.scan_availability()
        ranges = availability_service.get_available_ranges('StepCount')
        
        # Today range should not be available
        today_ranges = [r for r in ranges if r.range_type == TimeRange.TODAY]
        if today_ranges:
            assert not today_ranges[0].available
            
    def test_gap_detection(self, availability_service):
        """Test gap detection logic."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 10)
        
        # Mock database with gaps
        mock_db = Mock()
        mock_db.get_dates_with_data.return_value = [
            date(2024, 1, 1),
            date(2024, 1, 2),
            # Gap: 1/3 - 1/7
            date(2024, 1, 8),
            date(2024, 1, 9),
            date(2024, 1, 10)
        ]
        
        availability_service.db = mock_db
        gaps = availability_service._detect_gaps('TestMetric', start_date, end_date)
        
        # Should detect gap in the middle
        assert len(gaps) > 0
        
    def test_cache_validity(self, availability_service):
        """Test cache validity checking."""
        # Initially invalid (no scan)
        assert not availability_service._is_cache_valid()
        
        # After scan, should be valid
        from datetime import datetime
        availability_service.last_scan = datetime.now()
        assert availability_service._is_cache_valid()
        
        # After expiry time, should be invalid
        old_time = datetime.now() - availability_service.cache_expiry - timedelta(minutes=1)
        availability_service.last_scan = old_time
        assert not availability_service._is_cache_valid()


class TestAvailabilityLevels:
    """Test availability level classifications."""
    
    def test_availability_level_enum(self):
        """Test AvailabilityLevel enum values."""
        assert AvailabilityLevel.FULL.value == "full"
        assert AvailabilityLevel.PARTIAL.value == "partial"
        assert AvailabilityLevel.SPARSE.value == "sparse"
        assert AvailabilityLevel.NONE.value == "none"
        
    def test_time_range_enum(self):
        """Test TimeRange enum values."""
        assert TimeRange.TODAY.value == "today"
        assert TimeRange.WEEK.value == "week"
        assert TimeRange.MONTH.value == "month"
        assert TimeRange.YEAR.value == "year"
        assert TimeRange.CUSTOM.value == "custom"


class TestDataRange:
    """Test DataRange data class."""
    
    def test_data_range_creation(self):
        """Test DataRange creation and attributes."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        gaps = [(date(2024, 1, 10), date(2024, 1, 15))]
        
        data_range = DataRange(
            start_date=start_date,
            end_date=end_date,
            total_points=1000,
            density=0.8,
            gaps=gaps,
            level=AvailabilityLevel.PARTIAL
        )
        
        assert data_range.start_date == start_date
        assert data_range.end_date == end_date
        assert data_range.total_points == 1000
        assert data_range.density == 0.8
        assert data_range.gaps == gaps
        assert data_range.level == AvailabilityLevel.PARTIAL


class TestRangeAvailability:
    """Test RangeAvailability data class."""
    
    def test_range_availability_creation(self):
        """Test RangeAvailability creation and attributes."""
        range_availability = RangeAvailability(
            range_type=TimeRange.WEEK,
            available=True,
            level=AvailabilityLevel.FULL,
            reason="",
            data_points=7,
            coverage_percent=100.0
        )
        
        assert range_availability.range_type == TimeRange.WEEK
        assert range_availability.available is True
        assert range_availability.level == AvailabilityLevel.FULL
        assert range_availability.reason == ""
        assert range_availability.data_points == 7
        assert range_availability.coverage_percent == 100.0


if __name__ == '__main__':
    pytest.main([__file__])