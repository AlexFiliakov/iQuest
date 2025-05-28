"""
Smart Default Selection for Time Ranges

Implements intelligent time range selection based on data density, user preferences,
and data patterns with fallback logic for sparse data scenarios.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from ..data_availability_service import (DataAvailabilityService, TimeRange, 
                                        RangeAvailability, AvailabilityLevel)
from .preference_tracker import PreferenceTracker

logger = logging.getLogger(__name__)


class SelectionContext(Enum):
    """Context for selection - different contexts may have different preferences."""
    STARTUP = "startup"
    METRIC_CHANGE = "metric_change"
    USER_INITIATED = "user_initiated"
    AUTO_REFRESH = "auto_refresh"


@dataclass
class SelectionFactors:
    """Factors that influence time range selection."""
    data_density_score: float
    recency_score: float
    user_preference_score: float
    data_interest_score: float
    pattern_score: float
    final_score: float


class SmartDefaultSelector:
    """Intelligent time range selector that learns from user behavior."""
    
    def __init__(self, availability_service: DataAvailabilityService, 
                 preference_tracker: Optional[PreferenceTracker] = None):
        """Initialize smart default selector.
        
        Args:
            availability_service: Service to check data availability
            preference_tracker: Service to track user preferences
        """
        self.availability = availability_service
        self.preference_tracker = preference_tracker or PreferenceTracker()
        
        # Selection weights - can be tuned based on user feedback
        self.selection_weights = {
            'data_density': 0.25,
            'recency': 0.20,
            'user_preference': 0.30,
            'data_interest': 0.15,
            'pattern_analysis': 0.10
        }
        
        # Fallback strategy order
        self.fallback_order = [
            TimeRange.WEEK,    # Most common preference
            TimeRange.MONTH,   # Broader context
            TimeRange.TODAY,   # If very recent data
            TimeRange.YEAR     # Last resort for historical view
        ]
        
        logger.info("SmartDefaultSelector initialized")
        
    def select_default_range(self, metric_type: str, 
                           context: SelectionContext = SelectionContext.STARTUP) -> Optional[TimeRange]:
        """Select optimal default time range for a metric.
        
        Args:
            metric_type: The metric to select a range for
            context: Context of the selection (startup, metric change, etc.)
            
        Returns:
            Best time range or None if no data available
        """
        logger.debug(f"Selecting default range for {metric_type} in {context.value} context")
        
        try:
            # Get available ranges
            available_ranges = self.availability.get_available_ranges(metric_type)
            available_ranges = [r for r in available_ranges if r.available]
            
            if not available_ranges:
                logger.warning(f"No available ranges for {metric_type}")
                return None
                
            # Score each available range
            range_scores = {}
            for range_availability in available_ranges:
                score_factors = self._calculate_range_score(
                    metric_type, range_availability, context
                )
                range_scores[range_availability.range_type] = score_factors
                
            if not range_scores:
                return None
                
            # Select highest scoring range
            best_range = max(range_scores, key=lambda r: range_scores[r].final_score)
            best_factors = range_scores[best_range]
            
            # Log the selection decision
            logger.info(f"Selected {best_range.value} for {metric_type} "
                       f"(score: {best_factors.final_score:.3f})")
            logger.debug(f"Score breakdown - Density: {best_factors.data_density_score:.3f}, "
                        f"Recency: {best_factors.recency_score:.3f}, "
                        f"Preference: {best_factors.user_preference_score:.3f}, "
                        f"Interest: {best_factors.data_interest_score:.3f}, "
                        f"Pattern: {best_factors.pattern_score:.3f}")
            
            # Track the automatic selection for learning
            self.preference_tracker.record_selection(
                metric_type, best_range, 'auto', context.value
            )
            
            return best_range
            
        except Exception as e:
            logger.error(f"Error selecting default range for {metric_type}: {e}")
            return self._fallback_selection(metric_type)
            
    def _calculate_range_score(self, metric_type: str, 
                              range_availability: RangeAvailability,
                              context: SelectionContext) -> SelectionFactors:
        """Calculate suitability score for a time range.
        
        Args:
            metric_type: The metric being scored
            range_availability: Availability info for the range
            context: Selection context
            
        Returns:
            SelectionFactors with detailed scoring breakdown
        """
        try:
            # Data density score (0-1)
            density_score = self._calculate_density_score(range_availability)
            
            # Recency score (0-1) - prefer recent data
            recency_score = self._calculate_recency_score(range_availability)
            
            # User preference score (0-1)
            preference_score = self.preference_tracker.get_preference_score(
                metric_type, range_availability.range_type
            )
            
            # Data interest score (0-1) - based on variance and patterns
            interest_score = self._calculate_interest_score(
                metric_type, range_availability
            )
            
            # Pattern analysis score (0-1) - based on typical usage patterns
            pattern_score = self._calculate_pattern_score(
                metric_type, range_availability, context
            )
            
            # Calculate weighted final score
            final_score = (
                density_score * self.selection_weights['data_density'] +
                recency_score * self.selection_weights['recency'] +
                preference_score * self.selection_weights['user_preference'] +
                interest_score * self.selection_weights['data_interest'] +
                pattern_score * self.selection_weights['pattern_analysis']
            )
            
            return SelectionFactors(
                data_density_score=density_score,
                recency_score=recency_score,
                user_preference_score=preference_score,
                data_interest_score=interest_score,
                pattern_score=pattern_score,
                final_score=final_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating score for {range_availability.range_type}: {e}")
            # Return neutral scores on error
            return SelectionFactors(
                data_density_score=0.5,
                recency_score=0.5,
                user_preference_score=0.5,
                data_interest_score=0.5,
                pattern_score=0.5,
                final_score=0.5
            )
            
    def _calculate_density_score(self, range_availability: RangeAvailability) -> float:
        """Calculate score based on data density."""
        # Convert coverage percentage to score
        coverage_score = range_availability.coverage_percent / 100.0
        
        # Bonus for availability level
        level_bonus = {
            AvailabilityLevel.FULL: 1.0,
            AvailabilityLevel.PARTIAL: 0.8,
            AvailabilityLevel.SPARSE: 0.6,
            AvailabilityLevel.NONE: 0.0
        }.get(range_availability.level, 0.5)
        
        # Combine coverage and level with weighted average
        return (coverage_score * 0.7) + (level_bonus * 0.3)
        
    def _calculate_recency_score(self, range_availability: RangeAvailability) -> float:
        """Calculate score based on data recency."""
        # Prefer ranges that include more recent data
        range_recency = {
            TimeRange.TODAY: 1.0,
            TimeRange.WEEK: 0.9,
            TimeRange.MONTH: 0.7,
            TimeRange.YEAR: 0.5
        }.get(range_availability.range_type, 0.5)
        
        return range_recency
        
    def _calculate_interest_score(self, metric_type: str, 
                                 range_availability: RangeAvailability) -> float:
        """Calculate score based on data interest (variance, trends)."""
        # This is a placeholder - in a real implementation, this would
        # analyze actual data variance and trends
        
        # For now, prefer ranges with more data points as they're likely more interesting
        if range_availability.data_points == 0:
            return 0.0
        elif range_availability.data_points < 5:
            return 0.3
        elif range_availability.data_points < 20:
            return 0.6
        else:
            return 0.8
            
    def _calculate_pattern_score(self, metric_type: str, 
                                range_availability: RangeAvailability,
                                context: SelectionContext) -> float:
        """Calculate score based on usage patterns and context."""
        # Context-based preferences
        context_preferences = {
            SelectionContext.STARTUP: {
                TimeRange.WEEK: 0.9,
                TimeRange.MONTH: 0.8,
                TimeRange.TODAY: 0.6,
                TimeRange.YEAR: 0.4
            },
            SelectionContext.METRIC_CHANGE: {
                TimeRange.WEEK: 0.8,
                TimeRange.MONTH: 0.9,
                TimeRange.TODAY: 0.5,
                TimeRange.YEAR: 0.6
            },
            SelectionContext.USER_INITIATED: {
                # Respect user patterns more in this context
                TimeRange.WEEK: 0.7,
                TimeRange.MONTH: 0.7,
                TimeRange.TODAY: 0.7,
                TimeRange.YEAR: 0.7
            }
        }
        
        default_pattern = {
            TimeRange.WEEK: 0.8,
            TimeRange.MONTH: 0.7,
            TimeRange.TODAY: 0.6,
            TimeRange.YEAR: 0.5
        }
        
        patterns = context_preferences.get(context, default_pattern)
        return patterns.get(range_availability.range_type, 0.5)
        
    def _fallback_selection(self, metric_type: str) -> Optional[TimeRange]:
        """Fallback selection when scoring fails."""
        logger.info(f"Using fallback selection for {metric_type}")
        
        try:
            available_ranges = self.availability.get_available_ranges(metric_type)
            available_ranges = [r.range_type for r in available_ranges if r.available]
            
            # Try fallback order
            for range_type in self.fallback_order:
                if range_type in available_ranges:
                    logger.info(f"Fallback selected {range_type.value} for {metric_type}")
                    return range_type
                    
            # If nothing from fallback order works, try any available range
            if available_ranges:
                selected = available_ranges[0]
                logger.info(f"Last resort: selected {selected.value} for {metric_type}")
                return selected
                
        except Exception as e:
            logger.error(f"Error in fallback selection: {e}")
            
        return None
        
    def learn_from_behavior(self, metric_type: str, selected_range: TimeRange, 
                           interaction_data: Dict):
        """Update preference model based on user behavior.
        
        Args:
            metric_type: The metric that was viewed
            selected_range: The time range that was selected
            interaction_data: Data about user interaction (duration, actions, etc.)
        """
        try:
            self.preference_tracker.update_preferences(
                metric=metric_type,
                range_type=selected_range,
                duration=interaction_data.get('view_duration', 0),
                actions=interaction_data.get('actions_taken', 0),
                explicit=interaction_data.get('manually_selected', False),
                context=interaction_data.get('context', 'unknown')
            )
            
            logger.debug(f"Learned from behavior: {metric_type}, {selected_range.value}, "
                        f"duration={interaction_data.get('view_duration', 0)}s")
                        
        except Exception as e:
            logger.error(f"Error learning from behavior: {e}")
            
    def get_selection_weights(self) -> Dict[str, float]:
        """Get current selection weights."""
        return self.selection_weights.copy()
        
    def update_selection_weights(self, new_weights: Dict[str, float]):
        """Update selection weights for tuning.
        
        Args:
            new_weights: New weights dictionary (values should sum to 1.0)
        """
        # Validate weights
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Selection weights sum to {total_weight}, not 1.0")
            
        self.selection_weights.update(new_weights)
        logger.info(f"Updated selection weights: {self.selection_weights}")
        
    def get_selection_statistics(self) -> Dict[str, any]:
        """Get statistics about selections made."""
        return self.preference_tracker.get_statistics()
        
    def export_preferences(self) -> Dict[str, any]:
        """Export user preferences for backup/analysis."""
        return self.preference_tracker.export_preferences()
        
    def import_preferences(self, preferences: Dict[str, any]):
        """Import user preferences from backup."""
        self.preference_tracker.import_preferences(preferences)