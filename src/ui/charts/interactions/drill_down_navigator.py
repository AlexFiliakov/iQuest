"""
Drill-down navigation for hierarchical health data exploration.

Enables navigation between different levels of detail in health visualizations.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class DrillLevel(Enum):
    """Available drill-down levels"""
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    HOUR = "hour"
    DETAIL = "detail"


@dataclass
class NavigationContext:
    """Context for drill-down navigation"""
    current_level: DrillLevel
    current_range: Tuple[datetime, datetime]
    selected_item: Optional[Dict[str, Any]]
    breadcrumb: List[Tuple[DrillLevel, str]]
    filters: Dict[str, Any]


class DrillDownNavigator(QObject):
    """Manages drill-down navigation between chart levels"""
    
    # Signals
    navigation_requested = pyqtSignal(str, dict)  # target_view, context
    level_changed = pyqtSignal(DrillLevel, dict)  # new_level, context
    breadcrumb_updated = pyqtSignal(list)  # breadcrumb trail
    
    def __init__(self):
        super().__init__()
        
        # Navigation state
        self.current_level = DrillLevel.MONTH
        self.navigation_stack: List[NavigationContext] = []
        self.max_stack_size = 10
        
        # Level hierarchy
        self.level_hierarchy = [
            DrillLevel.YEAR,
            DrillLevel.MONTH,
            DrillLevel.WEEK,
            DrillLevel.DAY,
            DrillLevel.HOUR,
            DrillLevel.DETAIL
        ]
        
        # View mappings
        self.level_views = {
            DrillLevel.YEAR: "yearly_overview",
            DrillLevel.MONTH: "monthly_dashboard",
            DrillLevel.WEEK: "weekly_analysis",
            DrillLevel.DAY: "daily_details",
            DrillLevel.HOUR: "hourly_breakdown",
            DrillLevel.DETAIL: "detail_view"
        }
        
    def request_drill_down(self, data_point: Dict[str, Any]):
        """Request drill-down based on selected data point"""
        # Determine target level based on current level and data
        target_level = self._determine_target_level(data_point)
        
        if not target_level:
            return
            
        # Create navigation context
        context = self._create_navigation_context(data_point, target_level)
        
        # Push current state to stack
        self._push_navigation_state()
        
        # Update current level
        self.current_level = target_level
        
        # Emit navigation request
        target_view = self.level_views.get(target_level, "detail_view")
        self.navigation_requested.emit(target_view, context)
        
        # Update breadcrumb
        self._update_breadcrumb(target_level, data_point)
        
    def drill_up(self):
        """Navigate up one level"""
        if not self.can_drill_up():
            return
            
        # Pop previous state
        previous_context = self._pop_navigation_state()
        
        if previous_context:
            self.current_level = previous_context.current_level
            
            # Navigate to previous view
            target_view = self.level_views.get(self.current_level)
            self.navigation_requested.emit(target_view, {
                'range': previous_context.current_range,
                'filters': previous_context.filters
            })
            
            # Update breadcrumb
            self.breadcrumb_updated.emit(previous_context.breadcrumb)
            
    def navigate_to_level(self, level: DrillLevel, context: Optional[Dict[str, Any]] = None):
        """Navigate directly to a specific level"""
        if level == self.current_level:
            return
            
        # Push current state if moving to different level
        self._push_navigation_state()
        
        self.current_level = level
        target_view = self.level_views.get(level)
        
        # Use provided context or create default
        nav_context = context or self._create_default_context(level)
        
        self.navigation_requested.emit(target_view, nav_context)
        self.level_changed.emit(level, nav_context)
        
    def can_drill_down(self, data_point: Optional[Dict[str, Any]] = None) -> bool:
        """Check if drill-down is possible"""
        current_index = self.level_hierarchy.index(self.current_level)
        
        # Check if we're at the deepest level
        if current_index >= len(self.level_hierarchy) - 1:
            return False
            
        # Check if data point supports drill-down
        if data_point:
            return self._has_drill_down_data(data_point)
            
        return True
        
    def can_drill_up(self) -> bool:
        """Check if drill-up is possible"""
        return len(self.navigation_stack) > 0
        
    def get_available_levels(self) -> List[DrillLevel]:
        """Get list of available drill levels"""
        return self.level_hierarchy.copy()
        
    def get_breadcrumb(self) -> List[Tuple[DrillLevel, str]]:
        """Get current breadcrumb trail"""
        if self.navigation_stack:
            return self.navigation_stack[-1].breadcrumb.copy()
        return [(self.current_level, self._format_level_name(self.current_level))]
        
    def _determine_target_level(self, data_point: Dict[str, Any]) -> Optional[DrillLevel]:
        """Determine appropriate drill-down level based on data"""
        current_index = self.level_hierarchy.index(self.current_level)
        
        # Can't drill down from detail level
        if current_index >= len(self.level_hierarchy) - 1:
            return None
            
        # Get next level in hierarchy
        next_level = self.level_hierarchy[current_index + 1]
        
        # Check if data supports this level
        if self._supports_level(data_point, next_level):
            return next_level
            
        # Skip to appropriate level if needed
        for i in range(current_index + 2, len(self.level_hierarchy)):
            level = self.level_hierarchy[i]
            if self._supports_level(data_point, level):
                return level
                
        return None
        
    def _supports_level(self, data_point: Dict[str, Any], level: DrillLevel) -> bool:
        """Check if data point supports a specific drill level"""
        # Check based on data granularity
        if 'granularity' in data_point:
            data_gran = data_point['granularity']
            
            # Map granularity to supported levels
            if data_gran == 'yearly' and level in [DrillLevel.MONTH, DrillLevel.WEEK]:
                return True
            elif data_gran == 'monthly' and level in [DrillLevel.WEEK, DrillLevel.DAY]:
                return True
            elif data_gran == 'weekly' and level in [DrillLevel.DAY, DrillLevel.HOUR]:
                return True
            elif data_gran == 'daily' and level in [DrillLevel.HOUR, DrillLevel.DETAIL]:
                return True
                
        # Check for specific data availability
        if level == DrillLevel.DETAIL:
            return 'detailed_data' in data_point or 'id' in data_point
            
        return True
        
    def _has_drill_down_data(self, data_point: Dict[str, Any]) -> bool:
        """Check if data point has drill-down data available"""
        drill_indicators = ['has_details', 'child_count', 'can_expand', 'detailed_data']
        return any(indicator in data_point for indicator in drill_indicators)
        
    def _create_navigation_context(self, data_point: Dict[str, Any], 
                                 target_level: DrillLevel) -> Dict[str, Any]:
        """Create context for navigation"""
        context = {
            'source_level': self.current_level.value,
            'target_level': target_level.value,
            'selected_data': data_point,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add time range based on selection
        if 'timestamp' in data_point:
            context['focus_time'] = data_point['timestamp']
            context['range'] = self._calculate_time_range(data_point['timestamp'], target_level)
            
        # Add any active filters
        if 'filters' in data_point:
            context['filters'] = data_point['filters']
            
        # Add drill-down specific data
        if 'drill_data' in data_point:
            context['drill_data'] = data_point['drill_data']
            
        return context
        
    def _calculate_time_range(self, timestamp: Any, level: DrillLevel) -> Tuple[str, str]:
        """Calculate appropriate time range for drill level"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
            except:
                dt = datetime.now()
        else:
            dt = timestamp
            
        if level == DrillLevel.YEAR:
            start = dt.replace(month=1, day=1, hour=0, minute=0, second=0)
            end = start.replace(year=start.year + 1) - timedelta(seconds=1)
        elif level == DrillLevel.MONTH:
            start = dt.replace(day=1, hour=0, minute=0, second=0)
            # Get last day of month
            if dt.month == 12:
                end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(seconds=1)
            else:
                end = dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1)
        elif level == DrillLevel.WEEK:
            # Start on Monday
            days_since_monday = dt.weekday()
            start = dt.replace(hour=0, minute=0, second=0) - timedelta(days=days_since_monday)
            end = start + timedelta(days=7) - timedelta(seconds=1)
        elif level == DrillLevel.DAY:
            start = dt.replace(hour=0, minute=0, second=0)
            end = start + timedelta(days=1) - timedelta(seconds=1)
        elif level == DrillLevel.HOUR:
            start = dt.replace(minute=0, second=0)
            end = start + timedelta(hours=1) - timedelta(seconds=1)
        else:
            # Detail level - narrow range
            start = dt - timedelta(minutes=30)
            end = dt + timedelta(minutes=30)
            
        return (start.isoformat(), end.isoformat())
        
    def _create_default_context(self, level: DrillLevel) -> Dict[str, Any]:
        """Create default context for a level"""
        now = datetime.now()
        time_range = self._calculate_time_range(now, level)
        
        return {
            'level': level.value,
            'range': time_range,
            'timestamp': now.isoformat()
        }
        
    def _push_navigation_state(self):
        """Push current navigation state to stack"""
        # Get current context
        current_context = NavigationContext(
            current_level=self.current_level,
            current_range=(datetime.now(), datetime.now()),  # Would be actual range
            selected_item=None,
            breadcrumb=self.get_breadcrumb(),
            filters={}
        )
        
        self.navigation_stack.append(current_context)
        
        # Limit stack size
        if len(self.navigation_stack) > self.max_stack_size:
            self.navigation_stack.pop(0)
            
    def _pop_navigation_state(self) -> Optional[NavigationContext]:
        """Pop navigation state from stack"""
        if self.navigation_stack:
            return self.navigation_stack.pop()
        return None
        
    def _update_breadcrumb(self, level: DrillLevel, data_point: Dict[str, Any]):
        """Update breadcrumb trail"""
        breadcrumb = self.get_breadcrumb()
        
        # Add new level to breadcrumb
        label = self._create_breadcrumb_label(level, data_point)
        breadcrumb.append((level, label))
        
        self.breadcrumb_updated.emit(breadcrumb)
        
    def _create_breadcrumb_label(self, level: DrillLevel, data_point: Dict[str, Any]) -> str:
        """Create label for breadcrumb item"""
        if 'label' in data_point:
            return data_point['label']
        elif 'timestamp' in data_point:
            return self._format_timestamp_for_level(data_point['timestamp'], level)
        else:
            return self._format_level_name(level)
            
    def _format_level_name(self, level: DrillLevel) -> str:
        """Format level enum to readable name"""
        return level.value.capitalize()
        
    def _format_timestamp_for_level(self, timestamp: Any, level: DrillLevel) -> str:
        """Format timestamp based on drill level"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
            except:
                return timestamp
        else:
            dt = timestamp
            
        if level == DrillLevel.YEAR:
            return dt.strftime('%Y')
        elif level == DrillLevel.MONTH:
            return dt.strftime('%B %Y')
        elif level == DrillLevel.WEEK:
            return dt.strftime('Week of %b %d, %Y')
        elif level == DrillLevel.DAY:
            return dt.strftime('%b %d, %Y')
        elif level == DrillLevel.HOUR:
            return dt.strftime('%I:%M %p')
        else:
            return dt.strftime('%b %d, %Y %I:%M %p')