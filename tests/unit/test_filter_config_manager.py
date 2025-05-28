"""Unit tests for FilterConfigManager."""

import pytest
import tempfile
import os
import json
from datetime import date, datetime
from unittest.mock import Mock, patch

from src.filter_config_manager import FilterConfigManager, FilterConfig
from src.data_filter_engine import FilterCriteria


class TestFilterConfig:
    """Test FilterConfig class."""
    
    def test_filter_config_creation(self):
        """Test basic FilterConfig creation."""
        config = FilterConfig(
            preset_name="test_preset",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_names=["iPhone", "Apple Watch"],
            health_types=["StepCount", "HeartRate"]
        )
        
        assert config.preset_name == "test_preset"
        assert config.start_date == date(2024, 1, 1)
        assert config.end_date == date(2024, 12, 31)
        assert config.source_names == ["iPhone", "Apple Watch"]
        assert config.health_types == ["StepCount", "HeartRate"]
        assert config.is_default is False
        assert config.is_last_used is False
    
    def test_to_filter_criteria(self):
        """Test conversion to FilterCriteria."""
        config = FilterConfig(
            preset_name="test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_names=["iPhone"],
            health_types=["StepCount"]
        )
        
        criteria = config.to_filter_criteria()
        
        assert isinstance(criteria, FilterCriteria)
        assert criteria.start_date == date(2024, 1, 1)
        assert criteria.end_date == date(2024, 12, 31)
        assert criteria.source_names == ["iPhone"]
        assert criteria.health_types == ["StepCount"]
    
    def test_from_filter_criteria(self):
        """Test creation from FilterCriteria."""
        criteria = FilterCriteria(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_names=["iPhone"],
            health_types=["StepCount"]
        )
        
        config = FilterConfig.from_filter_criteria(criteria, "test_preset")
        
        assert config.preset_name == "test_preset"
        assert config.start_date == date(2024, 1, 1)
        assert config.end_date == date(2024, 12, 31)
        assert config.source_names == ["iPhone"]
        assert config.health_types == ["StepCount"]
    
    def test_to_dict(self):
        """Test dictionary conversion with date serialization."""
        config = FilterConfig(
            preset_name="test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_names=["iPhone"],
            health_types=["StepCount"]
        )
        
        result = config.to_dict()
        
        assert result['preset_name'] == "test"
        assert result['start_date'] == "2024-01-01"
        assert result['end_date'] == "2024-12-31"
        assert result['source_names'] == ["iPhone"]
        assert result['health_types'] == ["StepCount"]


class TestFilterConfigManager:
    """Test FilterConfigManager class."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        with patch('src.filter_config_manager.DatabaseManager') as mock_db:
            mock_instance = Mock()
            mock_db.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def filter_manager(self, mock_db_manager):
        """Create FilterConfigManager with mocked database."""
        return FilterConfigManager()
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample FilterConfig for testing."""
        return FilterConfig(
            preset_name="test_preset",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_names=["iPhone", "Apple Watch"],
            health_types=["StepCount", "HeartRate"]
        )
    
    def test_save_new_config(self, filter_manager, mock_db_manager, sample_config):
        """Test saving a new configuration."""
        mock_db_manager.execute_command.return_value = 123
        
        config_id = filter_manager.save_config(sample_config)
        
        assert config_id == 123
        assert mock_db_manager.execute_command.call_count == 1
        
        # Verify the SQL call
        call_args = mock_db_manager.execute_command.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO filter_configs" in query
        assert params[0] == "test_preset"  # preset_name
        assert params[1] == "2024-01-01"   # start_date
        assert params[2] == "2024-12-31"   # end_date
        assert '"iPhone"' in params[3]     # source_names JSON
        assert '"StepCount"' in params[4]  # health_types JSON
    
    def test_save_existing_config(self, filter_manager, mock_db_manager, sample_config):
        """Test updating an existing configuration."""
        sample_config.id = 123
        mock_db_manager.execute_command.return_value = 123
        
        config_id = filter_manager.save_config(sample_config)
        
        assert config_id == 123
        
        # Verify UPDATE query was used
        call_args = mock_db_manager.execute_command.call_args
        query = call_args[0][0]
        assert "UPDATE filter_configs" in query
    
    def test_save_as_default_clears_other_defaults(self, filter_manager, mock_db_manager, sample_config):
        """Test that setting a config as default clears other defaults."""
        sample_config.is_default = True
        mock_db_manager.execute_command.return_value = 123
        
        filter_manager.save_config(sample_config)
        
        # Should have called execute_command twice: clear defaults, then insert
        assert mock_db_manager.execute_command.call_count == 2
        
        # First call should clear defaults
        first_call = mock_db_manager.execute_command.call_args_list[0]
        assert "is_default = FALSE" in first_call[0][0]
    
    def test_save_as_last_used_clears_other_last_used(self, filter_manager, mock_db_manager, sample_config):
        """Test that setting a config as last used clears other last used flags."""
        sample_config.is_last_used = True
        mock_db_manager.execute_command.return_value = 123
        
        filter_manager.save_config(sample_config)
        
        # Should have called execute_command twice: clear last_used, then insert
        assert mock_db_manager.execute_command.call_count == 2
        
        # First call should clear last_used
        first_call = mock_db_manager.execute_command.call_args_list[0]
        assert "is_last_used = FALSE" in first_call[0][0]
    
    def test_load_config_found(self, filter_manager, mock_db_manager):
        """Test loading an existing configuration."""
        # Mock database response
        mock_row = {
            'id': 123,
            'preset_name': 'test_preset',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'source_names': '["iPhone", "Apple Watch"]',
            'health_types': '["StepCount", "HeartRate"]',
            'is_default': False,
            'is_last_used': False,
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        }
        mock_db_manager.execute_query.return_value = [mock_row]
        
        config = filter_manager.load_config("test_preset")
        
        assert config is not None
        assert config.preset_name == "test_preset"
        assert config.start_date == date(2024, 1, 1)
        assert config.end_date == date(2024, 12, 31)
        assert config.source_names == ["iPhone", "Apple Watch"]
        assert config.health_types == ["StepCount", "HeartRate"]
        assert config.id == 123
    
    def test_load_config_not_found(self, filter_manager, mock_db_manager):
        """Test loading a non-existent configuration."""
        mock_db_manager.execute_query.return_value = []
        
        config = filter_manager.load_config("non_existent")
        
        assert config is None
    
    def test_get_default_config(self, filter_manager, mock_db_manager):
        """Test getting the default configuration."""
        mock_row = {
            'id': 123,
            'preset_name': 'default_preset',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'source_names': '["iPhone"]',
            'health_types': '["StepCount"]',
            'is_default': True,
            'is_last_used': False,
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        }
        mock_db_manager.execute_query.return_value = [mock_row]
        
        config = filter_manager.get_default_config()
        
        assert config is not None
        assert config.is_default is True
        assert config.preset_name == "default_preset"
        
        # Verify correct query
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        assert "is_default = TRUE" in query
    
    def test_get_last_used_config(self, filter_manager, mock_db_manager):
        """Test getting the last used configuration."""
        mock_row = {
            'id': 123,
            'preset_name': '__last_used__',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'source_names': '["iPhone"]',
            'health_types': '["StepCount"]',
            'is_default': False,
            'is_last_used': True,
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        }
        mock_db_manager.execute_query.return_value = [mock_row]
        
        config = filter_manager.get_last_used_config()
        
        assert config is not None
        assert config.is_last_used is True
        assert config.preset_name == "__last_used__"
        
        # Verify correct query
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        assert "is_last_used = TRUE" in query
    
    def test_list_configs(self, filter_manager, mock_db_manager):
        """Test listing all configurations."""
        mock_rows = [
            {
                'id': 1,
                'preset_name': 'preset1',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'source_names': '["iPhone"]',
                'health_types': '["StepCount"]',
                'is_default': False,
                'is_last_used': False,
                'created_at': '2024-01-01T10:00:00',
                'updated_at': '2024-01-01T10:00:00'
            },
            {
                'id': 2,
                'preset_name': 'preset2',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'source_names': '["Apple Watch"]',
                'health_types': '["HeartRate"]',
                'is_default': False,
                'is_last_used': False,
                'created_at': '2024-01-01T10:00:00',
                'updated_at': '2024-01-01T10:00:00'
            }
        ]
        mock_db_manager.execute_query.return_value = mock_rows
        
        configs = filter_manager.list_configs()
        
        assert len(configs) == 2
        assert configs[0].preset_name == "preset1"
        assert configs[1].preset_name == "preset2"
        
        # Verify query includes ORDER BY
        call_args = mock_db_manager.execute_query.call_args
        query = call_args[0][0]
        assert "ORDER BY preset_name" in query
    
    def test_delete_config(self, filter_manager, mock_db_manager):
        """Test deleting a configuration."""
        mock_db_manager.execute_command.return_value = 1  # Simulate successful deletion
        
        result = filter_manager.delete_config("test_preset")
        
        assert result is True
        
        # Verify DELETE query
        call_args = mock_db_manager.execute_command.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        assert "DELETE FROM filter_configs" in query
        assert params == ("test_preset",)
    
    def test_delete_config_not_found(self, filter_manager, mock_db_manager):
        """Test deleting a non-existent configuration."""
        mock_db_manager.execute_command.return_value = 0  # No rows affected
        
        result = filter_manager.delete_config("non_existent")
        
        assert result is False
    
    def test_set_as_default(self, filter_manager, mock_db_manager):
        """Test setting a configuration as default."""
        mock_db_manager.execute_command.return_value = 1
        
        result = filter_manager.set_as_default("test_preset")
        
        assert result is True
        assert mock_db_manager.execute_command.call_count == 2  # Clear + Set
        
        # Verify queries
        calls = mock_db_manager.execute_command.call_args_list
        clear_call = calls[0][0][0]
        set_call = calls[1][0][0]
        
        assert "is_default = FALSE" in clear_call
        assert "is_default = TRUE" in set_call
    
    def test_save_as_last_used(self, filter_manager, mock_db_manager, sample_config):
        """Test saving configuration as last used."""
        mock_db_manager.execute_command.return_value = 1
        
        result = filter_manager.save_as_last_used(sample_config)
        
        assert result is True
        assert sample_config.preset_name == "__last_used__"
        assert sample_config.is_last_used is True
        
        # Should have multiple calls: clear last_used, delete existing, insert new
        assert mock_db_manager.execute_command.call_count >= 2
    
    def test_migrate_from_json(self, filter_manager, mock_db_manager):
        """Test migrating presets from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json_data = {
                "workout_preset": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "devices": ["iPhone", "Apple Watch"],
                    "metrics": ["StepCount", "WorkoutType"]
                },
                "heart_preset": {
                    "start_date": "2024-06-01",
                    "end_date": "2024-12-31",
                    "devices": ["Apple Watch"],
                    "metrics": ["HeartRate"]
                }
            }
            json.dump(json_data, f)
            temp_path = f.name
        
        try:
            mock_db_manager.execute_command.return_value = 1
            
            migrated_count = filter_manager.migrate_from_json(temp_path)
            
            assert migrated_count == 2
            # Should have been called twice for two presets
            assert mock_db_manager.execute_command.call_count == 2
            
        finally:
            os.unlink(temp_path)
    
    def test_migrate_from_json_file_not_found(self, filter_manager):
        """Test migration when JSON file doesn't exist."""
        migrated_count = filter_manager.migrate_from_json("/non/existent/path.json")
        assert migrated_count == 0
    
    def test_row_to_config_with_nulls(self, filter_manager):
        """Test converting database row with null values."""
        mock_row = {
            'id': 123,
            'preset_name': 'minimal_preset',
            'start_date': None,
            'end_date': None,
            'source_names': None,
            'health_types': None,
            'is_default': False,
            'is_last_used': False,
            'created_at': None,
            'updated_at': None
        }
        
        config = filter_manager._row_to_config(mock_row)
        
        assert config.preset_name == "minimal_preset"
        assert config.start_date is None
        assert config.end_date is None
        assert config.source_names is None
        assert config.health_types is None
        assert config.created_at is None
        assert config.updated_at is None