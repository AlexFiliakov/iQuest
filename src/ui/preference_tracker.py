"""
Preference Tracker for Smart Default Selection

Tracks and learns from user behavior to improve time range selection.
Integrates with existing QSettings system for persistence.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import json
import logging

from PyQt6.QtCore import QSettings
from ..data_availability_service import TimeRange
from .settings_manager import SettingsManager
from ..config import ORGANIZATION_NAME, APP_NAME

logger = logging.getLogger(__name__)


class PreferenceTracker:
    """Tracks user preferences and behavior for smart default selection."""
    
    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        """Initialize preference tracker.
        
        Args:
            settings_manager: Optional settings manager. If None, creates its own.
        """
        # Use existing settings manager or create new one
        if settings_manager:
            self.settings = settings_manager.settings
        else:
            self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
            
        self.preferences: Dict[str, Dict] = {}
        self.session_data: Dict[str, Dict] = {}
        
        # Decay settings
        self.weekly_decay_factor = 0.95  # 5% decay per week
        self.max_preference_age_days = 90  # Remove very old preferences
        
        # Load existing preferences
        self._load_preferences()
        
        logger.info("PreferenceTracker initialized")
        
    def _load_preferences(self):
        """Load preferences from storage."""
        try:
            self.settings.beginGroup("TimeRangePreferences")
            
            # Get all preference keys
            preference_keys = self.settings.allKeys()
            
            for key in preference_keys:
                preference_data = self.settings.value(key)
                if preference_data:
                    # Parse JSON data
                    try:
                        if isinstance(preference_data, str):
                            self.preferences[key] = json.loads(preference_data)
                        else:
                            # Handle legacy or direct dict storage
                            self.preferences[key] = preference_data
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse preference {key}: {e}")
                        
            self.settings.endGroup()
            
            # Clean up old preferences
            self._cleanup_old_preferences()
            
            logger.info(f"Loaded {len(self.preferences)} preference entries")
            
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            self.preferences = {}
            
    def _save_preferences(self):
        """Save preferences to storage."""
        try:
            self.settings.beginGroup("TimeRangePreferences")
            
            # Clear existing preferences first
            self.settings.clear()
            
            # Save each preference as JSON
            for key, preference in self.preferences.items():
                preference_json = json.dumps(preference, default=str)
                self.settings.setValue(key, preference_json)
                
            self.settings.endGroup()
            self.settings.sync()
            
            logger.debug(f"Saved {len(self.preferences)} preference entries")
            
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            
    def _cleanup_old_preferences(self):
        """Remove preferences older than max_preference_age_days."""
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, preference in self.preferences.items():
            try:
                last_used_str = preference.get('last_used')
                if last_used_str:
                    if isinstance(last_used_str, str):
                        last_used = datetime.fromisoformat(last_used_str)
                    else:
                        last_used = last_used_str
                        
                    age_days = (current_time - last_used).days
                    if age_days > self.max_preference_age_days:
                        keys_to_remove.append(key)
                        
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid last_used date for preference {key}: {e}")
                keys_to_remove.append(key)
                
        # Remove old preferences
        for key in keys_to_remove:
            del self.preferences[key]
            logger.debug(f"Removed old preference: {key}")
            
        if keys_to_remove:
            self._save_preferences()
            
    def get_preference_score(self, metric: str, range_type: TimeRange) -> float:
        """Get learned preference score for a metric and range type.
        
        Args:
            metric: The metric name
            range_type: The time range type
            
        Returns:
            Preference score between 0.0 and 1.0
        """
        key = f"{metric}_{range_type.value}"
        
        if key not in self.preferences:
            return 0.5  # Neutral score for unknown preferences
            
        try:
            preference = self.preferences[key]
            
            # Apply time decay to score
            last_used_str = preference.get('last_used')
            if last_used_str:
                if isinstance(last_used_str, str):
                    last_used = datetime.fromisoformat(last_used_str)
                else:
                    last_used = last_used_str
                    
                weeks_since_used = (datetime.now() - last_used).days / 7.0
                decay_factor = self.weekly_decay_factor ** weeks_since_used
                
                base_score = preference.get('score', 0.5)
                decayed_score = base_score * decay_factor
                
                # Ensure score stays within bounds
                return max(0.0, min(1.0, decayed_score))
            else:
                return preference.get('score', 0.5)
                
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Error calculating preference score for {key}: {e}")
            return 0.5
            
    def record_selection(self, metric: str, range_type: TimeRange, 
                        selection_type: str, context: str = "unknown"):
        """Record a time range selection for learning.
        
        Args:
            metric: The metric that was selected
            range_type: The time range that was selected
            selection_type: Type of selection ('auto', 'manual', 'suggested')
            context: Context of the selection
        """
        try:
            key = f"{metric}_{range_type.value}"
            
            # Initialize preference if it doesn't exist
            if key not in self.preferences:
                self.preferences[key] = {
                    'score': 0.5,
                    'count': 0,
                    'last_used': datetime.now().isoformat(),
                    'selection_types': {},
                    'contexts': {}
                }
                
            preference = self.preferences[key]
            
            # Update last used time
            preference['last_used'] = datetime.now().isoformat()
            preference['count'] = preference.get('count', 0) + 1
            
            # Track selection types
            selection_types = preference.setdefault('selection_types', {})
            selection_types[selection_type] = selection_types.get(selection_type, 0) + 1
            
            # Track contexts
            contexts = preference.setdefault('contexts', {})
            contexts[context] = contexts.get(context, 0) + 1
            
            # Slightly boost score for any selection (shows this combination is used)
            if selection_type == 'auto':
                # Small boost for automatic selections
                preference['score'] = min(1.0, preference['score'] + 0.01)
            elif selection_type == 'manual':
                # Larger boost for manual selections (user explicitly chose this)
                preference['score'] = min(1.0, preference['score'] + 0.05)
                
            self._save_preferences()
            
            logger.debug(f"Recorded selection: {key}, type={selection_type}, context={context}")
            
        except Exception as e:
            logger.error(f"Error recording selection: {e}")
            
    def update_preferences(self, metric: str, range_type: TimeRange, 
                          duration: float = 0, actions: int = 0, 
                          explicit: bool = False, context: str = "unknown"):
        """Update preference scores based on user behavior.
        
        Args:
            metric: The metric that was viewed
            range_type: The time range that was viewed
            duration: How long the user viewed this range (seconds)
            actions: Number of actions taken while viewing
            explicit: Whether the user explicitly selected this range
            context: Context of the interaction
        """
        try:
            key = f"{metric}_{range_type.value}"
            
            # Initialize if needed
            if key not in self.preferences:
                self.preferences[key] = {
                    'score': 0.5,
                    'count': 0,
                    'last_used': datetime.now().isoformat(),
                    'total_duration': 0.0,
                    'total_actions': 0,
                    'explicit_selections': 0
                }
                
            preference = self.preferences[key]
            
            # Update usage statistics
            preference['last_used'] = datetime.now().isoformat()
            preference['count'] = preference.get('count', 0) + 1
            preference['total_duration'] = preference.get('total_duration', 0.0) + duration
            preference['total_actions'] = preference.get('total_actions', 0) + actions
            
            # Update score based on behavior signals
            score_delta = 0.0
            
            # Positive signals
            if explicit:
                score_delta += 0.1  # Strong signal - user explicitly chose this
                preference['explicit_selections'] = preference.get('explicit_selections', 0) + 1
                
            if duration > 30:  # Viewed for more than 30 seconds
                score_delta += 0.03
                
            if duration > 120:  # Viewed for more than 2 minutes
                score_delta += 0.02
                
            if actions > 0:  # User interacted (scrolled, exported, etc.)
                score_delta += 0.02
                
            if actions > 5:  # Heavy interaction
                score_delta += 0.03
                
            # Negative signals
            if not explicit and duration < 5:  # Very short view time
                score_delta -= 0.01
                
            # Apply score change with bounds checking
            current_score = preference.get('score', 0.5)
            new_score = max(0.0, min(1.0, current_score + score_delta))
            preference['score'] = new_score
            
            self._save_preferences()
            
            logger.debug(f"Updated preferences for {key}: score={new_score:.3f}, "
                        f"duration={duration}s, actions={actions}, explicit={explicit}")
                        
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            
    def get_top_preferences(self, metric: str, limit: int = 5) -> List[Dict]:
        """Get top preferences for a metric.
        
        Args:
            metric: The metric to get preferences for
            limit: Maximum number of results
            
        Returns:
            List of top preferences sorted by score
        """
        try:
            metric_preferences = []
            
            for key, preference in self.preferences.items():
                if key.startswith(f"{metric}_"):
                    range_type_str = key.split('_', 1)[1]
                    try:
                        range_type = TimeRange(range_type_str)
                        
                        # Get current score (with decay)
                        current_score = self.get_preference_score(metric, range_type)
                        
                        metric_preferences.append({
                            'range_type': range_type,
                            'score': current_score,
                            'count': preference.get('count', 0),
                            'last_used': preference.get('last_used'),
                            'avg_duration': (preference.get('total_duration', 0) / 
                                           max(1, preference.get('count', 1))),
                            'explicit_selections': preference.get('explicit_selections', 0)
                        })
                    except ValueError:
                        logger.warning(f"Invalid range type in preference key: {key}")
                        
            # Sort by score descending
            metric_preferences.sort(key=lambda x: x['score'], reverse=True)
            
            return metric_preferences[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top preferences for {metric}: {e}")
            return []
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about preference learning.
        
        Returns:
            Dictionary with preference statistics
        """
        try:
            total_preferences = len(self.preferences)
            active_preferences = 0
            total_selections = 0
            explicit_selections = 0
            total_duration = 0.0
            
            range_type_counts = {}
            metric_counts = {}
            
            for key, preference in self.preferences.items():
                count = preference.get('count', 0)
                total_selections += count
                explicit_selections += preference.get('explicit_selections', 0)
                total_duration += preference.get('total_duration', 0.0)
                
                if count > 0:
                    active_preferences += 1
                    
                # Parse key for statistics
                try:
                    metric, range_type_str = key.split('_', 1)
                    range_type_counts[range_type_str] = range_type_counts.get(range_type_str, 0) + count
                    metric_counts[metric] = metric_counts.get(metric, 0) + count
                except ValueError:
                    pass
                    
            return {
                'total_preferences': total_preferences,
                'active_preferences': active_preferences,
                'total_selections': total_selections,
                'explicit_selections': explicit_selections,
                'explicit_percentage': (explicit_selections / max(1, total_selections)) * 100,
                'total_view_time_hours': total_duration / 3600.0,
                'avg_view_time_seconds': total_duration / max(1, total_selections),
                'range_type_popularity': range_type_counts,
                'metric_usage': metric_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
            
    def export_preferences(self) -> Dict[str, Any]:
        """Export all preferences for backup or analysis.
        
        Returns:
            Dictionary containing all preference data
        """
        try:
            return {
                'preferences': self.preferences.copy(),
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }
        except Exception as e:
            logger.error(f"Error exporting preferences: {e}")
            return {}
            
    def import_preferences(self, preferences_data: Dict[str, Any]):
        """Import preferences from backup.
        
        Args:
            preferences_data: Dictionary containing preference data
        """
        try:
            if 'preferences' in preferences_data:
                # Merge with existing preferences
                imported_prefs = preferences_data['preferences']
                
                for key, preference in imported_prefs.items():
                    # Only import if newer or doesn't exist
                    if key not in self.preferences:
                        self.preferences[key] = preference
                    else:
                        existing_last_used = self.preferences[key].get('last_used')
                        imported_last_used = preference.get('last_used')
                        
                        if imported_last_used and (not existing_last_used or 
                                                 imported_last_used > existing_last_used):
                            self.preferences[key] = preference
                            
                self._save_preferences()
                logger.info(f"Imported {len(imported_prefs)} preferences")
                
        except Exception as e:
            logger.error(f"Error importing preferences: {e}")
            
    def reset_preferences(self):
        """Reset all preferences to default state."""
        try:
            self.preferences.clear()
            self._save_preferences()
            logger.info("All preferences reset")
        except Exception as e:
            logger.error(f"Error resetting preferences: {e}")
            
    def get_preference_details(self, metric: str, range_type: TimeRange) -> Optional[Dict]:
        """Get detailed information about a specific preference.
        
        Args:
            metric: The metric name
            range_type: The time range type
            
        Returns:
            Detailed preference information or None if not found
        """
        key = f"{metric}_{range_type.value}"
        preference = self.preferences.get(key)
        
        if preference:
            # Add calculated fields
            result = preference.copy()
            result['current_score'] = self.get_preference_score(metric, range_type)
            result['avg_duration'] = (preference.get('total_duration', 0) / 
                                    max(1, preference.get('count', 1)))
            return result
            
        return None