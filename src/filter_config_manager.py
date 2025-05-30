"""Filter Configuration Manager for Apple Health Monitor.

This module handles persistence of filter configurations to the SQLite database,
replacing the JSON-based preset system with database-backed storage.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dataclasses import dataclass, asdict

from .database import DatabaseManager
from .data_filter_engine import FilterCriteria
from .utils.error_handler import DataImportError

logger = logging.getLogger(__name__)


@dataclass
class FilterConfig:
    """Data class representing a filter configuration."""
    preset_name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    source_names: Optional[List[str]] = None
    health_types: Optional[List[str]] = None
    is_default: bool = False
    is_last_used: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_filter_criteria(self) -> FilterCriteria:
        """Convert to FilterCriteria object for use with DataFilterEngine."""
        return FilterCriteria(
            start_date=self.start_date,
            end_date=self.end_date,
            source_names=self.source_names,
            health_types=self.health_types
        )

    @classmethod
    def from_filter_criteria(cls, criteria: FilterCriteria, preset_name: str) -> 'FilterConfig':
        """Create FilterConfig from FilterCriteria."""
        return cls(
            preset_name=preset_name,
            start_date=criteria.start_date,
            end_date=criteria.end_date,
            source_names=criteria.source_names,
            health_types=criteria.health_types
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with date serialization."""
        result = asdict(self)
        
        # Convert dates to ISO format strings for storage
        if self.start_date:
            result['start_date'] = self.start_date.isoformat()
        if self.end_date:
            result['end_date'] = self.end_date.isoformat()
        
        # Convert datetime objects to ISO strings
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
            
        return result


class FilterConfigManager:
    """Manages filter configuration persistence in SQLite database."""
    
    def __init__(self):
        """Initialize the filter configuration manager."""
        self.db_manager = DatabaseManager()
        logger.info("FilterConfigManager initialized")
    
    def save_config(self, config: FilterConfig) -> int:
        """
        Save a filter configuration to the database.
        
        Args:
            config: FilterConfig object to save
            
        Returns:
            The ID of the saved configuration
            
        Raises:
            DataImportError: If saving fails
        """
        try:
            # If this is being set as last used, clear other last_used flags
            if config.is_last_used:
                self._clear_last_used_flags()
            
            # If this is being set as default, clear other default flags
            if config.is_default:
                self._clear_default_flags()
            
            # Convert lists to JSON strings for storage
            source_names_json = json.dumps(config.source_names) if config.source_names else None
            health_types_json = json.dumps(config.health_types) if config.health_types else None
            
            # Convert dates to ISO strings
            start_date_str = config.start_date.isoformat() if config.start_date else None
            end_date_str = config.end_date.isoformat() if config.end_date else None
            
            if config.id:
                # Update existing configuration
                query = """
                    UPDATE filter_configs 
                    SET preset_name = ?, start_date = ?, end_date = ?, 
                        source_names = ?, health_types = ?, is_default = ?, is_last_used = ?
                    WHERE id = ?
                """
                params = (
                    config.preset_name, start_date_str, end_date_str,
                    source_names_json, health_types_json, 
                    config.is_default, config.is_last_used, config.id
                )
                self.db_manager.execute_command(query, params)
                config_id = config.id
                logger.info(f"Updated filter config: {config.preset_name} (ID: {config_id})")
            else:
                # Insert new configuration
                query = """
                    INSERT INTO filter_configs 
                    (preset_name, start_date, end_date, source_names, health_types, is_default, is_last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    config.preset_name, start_date_str, end_date_str,
                    source_names_json, health_types_json, 
                    config.is_default, config.is_last_used
                )
                config_id = self.db_manager.execute_command(query, params)
                logger.info(f"Saved new filter config: {config.preset_name} (ID: {config_id})")
            
            return config_id
            
        except Exception as e:
            logger.error(f"Error saving filter config: {e}")
            raise DataImportError(f"Failed to save filter configuration: {str(e)}") from e
    
    def load_config(self, preset_name: str) -> Optional[FilterConfig]:
        """
        Load a filter configuration by name.
        
        Args:
            preset_name: Name of the preset to load
            
        Returns:
            FilterConfig object or None if not found
        """
        try:
            query = "SELECT * FROM filter_configs WHERE preset_name = ?"
            rows = self.db_manager.execute_query(query, (preset_name,))
            
            if rows:
                return self._row_to_config(rows[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading filter config '{preset_name}': {e}")
            return None
    
    def load_config_by_id(self, config_id: int) -> Optional[FilterConfig]:
        """
        Load a filter configuration by ID.
        
        Args:
            config_id: ID of the configuration to load
            
        Returns:
            FilterConfig object or None if not found
        """
        try:
            query = "SELECT * FROM filter_configs WHERE id = ?"
            rows = self.db_manager.execute_query(query, (config_id,))
            
            if rows:
                return self._row_to_config(rows[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading filter config ID {config_id}: {e}")
            return None
    
    def get_default_config(self) -> Optional[FilterConfig]:
        """
        Get the default filter configuration.
        
        Returns:
            Default FilterConfig or None if none set
        """
        try:
            query = "SELECT * FROM filter_configs WHERE is_default = TRUE LIMIT 1"
            rows = self.db_manager.execute_query(query)
            
            if rows:
                return self._row_to_config(rows[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading default config: {e}")
            return None
    
    def get_last_used_config(self) -> Optional[FilterConfig]:
        """
        Get the last used filter configuration.
        
        Returns:
            Last used FilterConfig or None if none set
        """
        try:
            query = "SELECT * FROM filter_configs WHERE is_last_used = TRUE LIMIT 1"
            rows = self.db_manager.execute_query(query)
            
            if rows:
                return self._row_to_config(rows[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading last used config: {e}")
            return None
    
    def list_configs(self) -> List[FilterConfig]:
        """
        List all filter configurations.
        
        Returns:
            List of FilterConfig objects ordered by name
        """
        try:
            query = "SELECT * FROM filter_configs ORDER BY preset_name"
            rows = self.db_manager.execute_query(query)
            
            return [self._row_to_config(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error listing filter configs: {e}")
            return []
    
    def delete_config(self, preset_name: str) -> bool:
        """
        Delete a filter configuration by name.
        
        Args:
            preset_name: Name of the preset to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            query = "DELETE FROM filter_configs WHERE preset_name = ?"
            result = self.db_manager.execute_command(query, (preset_name,))
            
            if result:
                logger.info(f"Deleted filter config: {preset_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting filter config '{preset_name}': {e}")
            return False
    
    def set_as_default(self, preset_name: str) -> bool:
        """
        Set a configuration as the default.
        
        Args:
            preset_name: Name of the preset to set as default
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing default
            self._clear_default_flags()
            
            # Set new default
            query = "UPDATE filter_configs SET is_default = TRUE WHERE preset_name = ?"
            result = self.db_manager.execute_command(query, (preset_name,))
            
            if result:
                logger.info(f"Set filter config as default: {preset_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting default config '{preset_name}': {e}")
            return False
    
    def save_as_last_used(self, config: FilterConfig) -> bool:
        """
        Save a configuration as the last used.
        
        Args:
            config: FilterConfig to save as last used
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing last_used flags
            self._clear_last_used_flags()
            
            # Set this config as last used
            config.is_last_used = True
            config.preset_name = "__last_used__"  # Special name for auto-save
            
            # Delete existing last_used entry if it exists
            self.db_manager.execute_command("DELETE FROM filter_configs WHERE preset_name = ?", ("__last_used__",))
            
            # Save the new last used config
            self.save_config(config)
            
            logger.info("Saved current filters as last used")
            return True
            
        except Exception as e:
            logger.error(f"Error saving last used config: {e}")
            return False
    
    def _clear_default_flags(self):
        """Clear all default flags."""
        query = "UPDATE filter_configs SET is_default = FALSE WHERE is_default = TRUE"
        self.db_manager.execute_command(query)
    
    def _clear_last_used_flags(self):
        """Clear all last_used flags."""
        query = "UPDATE filter_configs SET is_last_used = FALSE WHERE is_last_used = TRUE"
        self.db_manager.execute_command(query)
    
    def _row_to_config(self, row) -> FilterConfig:
        """Convert database row to FilterConfig object."""
        # Parse JSON fields
        source_names = json.loads(row['source_names']) if row['source_names'] else None
        health_types = json.loads(row['health_types']) if row['health_types'] else None
        
        # Parse date fields
        start_date = datetime.fromisoformat(row['start_date']).date() if row['start_date'] else None
        end_date = datetime.fromisoformat(row['end_date']).date() if row['end_date'] else None
        
        # Parse datetime fields
        created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        updated_at = datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        
        return FilterConfig(
            id=row['id'],
            preset_name=row['preset_name'],
            start_date=start_date,
            end_date=end_date,
            source_names=source_names,
            health_types=health_types,
            is_default=bool(row['is_default']),
            is_last_used=bool(row['is_last_used']),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def migrate_from_json(self, json_file_path: str) -> int:
        """
        Migrate existing JSON presets to database.
        
        Args:
            json_file_path: Path to the JSON presets file
            
        Returns:
            Number of presets migrated
        """
        try:
            import os
            if not os.path.exists(json_file_path):
                logger.info("No JSON presets file found to migrate")
                return 0
            
            with open(json_file_path, 'r') as f:
                presets = json.load(f)
            
            migrated_count = 0
            for preset_name, preset_data in presets.items():
                try:
                    # Convert JSON data to FilterConfig
                    start_date = datetime.fromisoformat(preset_data['start_date']).date() if preset_data.get('start_date') else None
                    end_date = datetime.fromisoformat(preset_data['end_date']).date() if preset_data.get('end_date') else None
                    
                    config = FilterConfig(
                        preset_name=preset_name,
                        start_date=start_date,
                        end_date=end_date,
                        source_names=preset_data.get('devices'),
                        health_types=preset_data.get('metrics')
                    )
                    
                    # Save to database
                    self.save_config(config)
                    migrated_count += 1
                    logger.info(f"Migrated preset: {preset_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to migrate preset '{preset_name}': {e}")
            
            logger.info(f"Migration completed: {migrated_count} presets migrated")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error during JSON migration: {e}")
            return 0
    
    def clear_all_presets(self) -> bool:
        """
        Clear all filter presets from the database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM filter_configs"
            result = self.db_manager.execute_command(query)
            
            if result:
                logger.info("Cleared all filter presets")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clearing all presets: {e}")
            return False