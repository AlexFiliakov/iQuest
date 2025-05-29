"""
Data Availability Service for adaptive display logic.

Detects available data ranges and provides intelligent UI adaptation
based on actual data availability.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum
import logging

from .health_database import HealthDatabase


logger = logging.getLogger(__name__)


class AvailabilityLevel(Enum):
    """Data availability levels for different time ranges.
    
    Attributes:
        FULL: Complete data for the time range with minimal gaps.
        PARTIAL: Some gaps but still usable for analysis.
        SPARSE: Limited data points, may not be reliable for analysis.
        NONE: No data available for the time range.
    """
    FULL = "full"       # Complete data for range
    PARTIAL = "partial" # Some gaps but usable  
    SPARSE = "sparse"   # Limited data points
    NONE = "none"       # No data available


class TimeRange(Enum):
    """Available time range options.
    
    Attributes:
        TODAY: Single day view.
        WEEK: Last 7 days view.
        MONTH: Last 30 days view.
        YEAR: Last 365 days view.
        CUSTOM: User-defined date range.
    """
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    CUSTOM = "custom"


@dataclass
class DataRange:
    """Data range information for a metric.
    
    Contains comprehensive information about data availability,
    density, and gaps for a specific health metric type.
    
    Attributes:
        start_date: First date with available data.
        end_date: Last date with available data.
        total_points: Total number of data points.
        density: Average data points per day.
        gaps: List of date ranges with missing data.
        level: Overall availability level assessment.
    """
    start_date: Optional[date]
    end_date: Optional[date]
    total_points: int
    density: float  # Points per day
    gaps: List[Tuple[date, date]]  # List of gap ranges
    level: AvailabilityLevel


@dataclass
class RangeAvailability:
    """Availability information for a specific time range.
    
    Contains analysis results for whether a specific time range
    (today, week, month, year) has sufficient data for visualization.
    
    Attributes:
        range_type: The time range being analyzed.
        available: Whether the range has sufficient data.
        level: Data availability level for this range.
        reason: Human-readable explanation if not available.
        data_points: Number of data points in this range.
        coverage_percent: Percentage of days with data.
    """
    range_type: TimeRange
    available: bool
    level: AvailabilityLevel
    reason: str
    data_points: int
    coverage_percent: float


class DataAvailabilityService:
    """Service to detect data availability and provide UI adaptation logic.
    
    This service analyzes health data to determine what time ranges have
    sufficient data for meaningful visualization. It provides caching,
    callback notifications, and intelligent recommendations for default
    time ranges based on actual data availability.
    
    Attributes:
        db (HealthDatabase): Database interface for health data queries.
        availability_cache (Dict[str, DataRange]): Cached availability data.
        update_callbacks (List[Callable]): Registered update callbacks.
        cache_expiry (timedelta): Cache validity duration.
        last_scan (Optional[datetime]): Timestamp of last availability scan.
    """
    
    def __init__(self, database: HealthDatabase):
        """Initialize the DataAvailabilityService.
        
        Args:
            database (HealthDatabase): The database interface for health data queries.
        """
        self.db = database
        self.availability_cache: Dict[str, DataRange] = {}
        self.update_callbacks: List[Callable] = []
        self.cache_expiry = timedelta(minutes=5)  # Cache for 5 minutes
        self.last_scan = None
        
    def register_callback(self, callback: Callable) -> None:
        """Register callback for availability updates.
        
        Args:
            callback (Callable): Function to call when availability data updates.
        """
        self.update_callbacks.append(callback)
        
    def unregister_callback(self, callback: Callable) -> None:
        """Unregister callback.
        
        Args:
            callback (Callable): The callback function to remove.
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            
    def notify_updates(self) -> None:
        """Notify all registered callbacks of availability updates.
        
        Calls all registered callback functions to inform them that
        availability data has been updated. Logs errors if callbacks fail.
        """
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in availability callback: {e}")
                
    def _is_cache_valid(self) -> bool:
        """Check if availability cache is still valid.
        
        Returns:
            bool: True if cache is within expiry time, False otherwise.
        """
        if self.last_scan is None:
            return False
        return datetime.now() - self.last_scan < self.cache_expiry
        
    def scan_availability(self) -> Dict[str, DataRange]:
        """Scan all metrics for data availability.
        
        Performs a comprehensive scan of all available health metric types
        to determine their data availability, gaps, and density. Updates
        the internal cache and notifies registered callbacks.
        
        Returns:
            Dict[str, DataRange]: Dictionary mapping metric types to their
                                 availability information. Empty dict on error.
        """
        logger.info("Scanning data availability for all metrics")
        
        availability = {}
        
        try:
            # Get all available metric types
            types = self.db.get_available_types()
            
            for metric_type in types:
                availability[metric_type] = self._scan_metric_availability(metric_type)
                
        except Exception as e:
            logger.error(f"Error scanning availability: {e}")
            # Return empty cache on error
            availability = {}
            
        self.availability_cache = availability
        self.last_scan = datetime.now()
        self.notify_updates()
        return availability
        
    def _scan_metric_availability(self, metric_type: str) -> DataRange:
        """Scan availability for a specific metric type.
        
        Args:
            metric_type (str): The health metric type to analyze.
            
        Returns:
            DataRange: Comprehensive availability information for the metric.
                      Returns DataRange with NONE level on error.
        """
        try:
            # Get basic range info
            date_range = self.db.get_date_range_for_type(metric_type)
            if not date_range or not date_range[0] or not date_range[1]:
                return DataRange(
                    start_date=None,
                    end_date=None,
                    total_points=0,
                    density=0.0,
                    gaps=[],
                    level=AvailabilityLevel.NONE
                )
                
            start_date, end_date = date_range
            total_points = self.db.get_record_count_for_type(metric_type)
            
            # Calculate density and gaps
            total_days = (end_date - start_date).days + 1
            density = total_points / total_days if total_days > 0 else 0.0
            gaps = self._detect_gaps(metric_type, start_date, end_date)
            
            # Determine availability level
            level = self._determine_availability_level(density, gaps, total_days)
            
            return DataRange(
                start_date=start_date,
                end_date=end_date,
                total_points=total_points,
                density=density,
                gaps=gaps,
                level=level
            )
            
        except Exception as e:
            logger.error(f"Error scanning metric {metric_type}: {e}")
            return DataRange(
                start_date=None,
                end_date=None,
                total_points=0,
                density=0.0,
                gaps=[],
                level=AvailabilityLevel.NONE
            )
            
    def _detect_gaps(self, metric_type: str, start_date: date, end_date: date) -> List[Tuple[date, date]]:
        """Detect gaps in data for a metric type."""
        gaps = []
        
        try:
            # Get dates with data
            dates_with_data = self.db.get_dates_with_data(metric_type, start_date, end_date)
            if not dates_with_data:
                return [(start_date, end_date)]
                
            # Convert to sorted list
            dates_with_data = sorted(set(dates_with_data))
            
            # Find gaps between consecutive dates
            gap_start = None
            current_date = start_date
            
            for data_date in dates_with_data:
                if current_date < data_date:
                    # Found a gap
                    gap_end = data_date - timedelta(days=1)
                    gaps.append((current_date, gap_end))
                current_date = data_date + timedelta(days=1)
                
            # Check for gap at the end
            if current_date <= end_date:
                gaps.append((current_date, end_date))
                
        except Exception as e:
            logger.error(f"Error detecting gaps for {metric_type}: {e}")
            
        return gaps
        
    def _determine_availability_level(self, density: float, gaps: List[Tuple[date, date]], total_days: int) -> AvailabilityLevel:
        """Determine availability level based on density and gaps."""
        if density == 0:
            return AvailabilityLevel.NONE
            
        # Calculate coverage percentage
        gap_days = sum((gap[1] - gap[0]).days + 1 for gap in gaps)
        coverage = (total_days - gap_days) / total_days if total_days > 0 else 0
        
        if coverage >= 0.9 and density >= 0.8:
            return AvailabilityLevel.FULL
        elif coverage >= 0.6 and density >= 0.3:
            return AvailabilityLevel.PARTIAL
        elif coverage >= 0.2 or density >= 0.1:
            return AvailabilityLevel.SPARSE
        else:
            return AvailabilityLevel.NONE
            
    def get_availability(self, metric_type: str) -> Optional[DataRange]:
        """Get availability information for a metric type."""
        if not self._is_cache_valid():
            self.scan_availability()
            
        return self.availability_cache.get(metric_type)
        
    def get_available_ranges(self, metric_type: str) -> List[RangeAvailability]:
        """Get list of available time ranges for a metric type."""
        data_range = self.get_availability(metric_type)
        if not data_range or data_range.level == AvailabilityLevel.NONE:
            return []
            
        available_ranges = []
        today = date.today()
        
        # Check Today
        today_availability = self._check_today_availability(data_range, today)
        available_ranges.append(today_availability)
        
        # Check Week (last 7 days)
        week_availability = self._check_week_availability(data_range, today)
        available_ranges.append(week_availability)
        
        # Check Month (last 30 days)
        month_availability = self._check_month_availability(data_range, today)
        available_ranges.append(month_availability)
        
        # Check Year (last 365 days)
        year_availability = self._check_year_availability(data_range, today)
        available_ranges.append(year_availability)
        
        return available_ranges
        
    def _check_today_availability(self, data_range: DataRange, today: date) -> RangeAvailability:
        """Check if today's data is available."""
        if not data_range.end_date or today > data_range.end_date:
            return RangeAvailability(
                range_type=TimeRange.TODAY,
                available=False,
                level=AvailabilityLevel.NONE,
                reason="No data for today",
                data_points=0,
                coverage_percent=0.0
            )
            
        # Check if today has data
        has_today_data = self._has_data_for_date_range(data_range, today, today)
        
        return RangeAvailability(
            range_type=TimeRange.TODAY,
            available=has_today_data,
            level=AvailabilityLevel.FULL if has_today_data else AvailabilityLevel.NONE,
            reason="" if has_today_data else "No data for today",
            data_points=1 if has_today_data else 0,
            coverage_percent=100.0 if has_today_data else 0.0
        )
        
    def _check_week_availability(self, data_range: DataRange, today: date) -> RangeAvailability:
        """Check if last 7 days have sufficient data."""
        week_start = today - timedelta(days=6)
        return self._check_range_availability(
            data_range, TimeRange.WEEK, week_start, today,
            min_days=3, min_coverage=0.4
        )
        
    def _check_month_availability(self, data_range: DataRange, today: date) -> RangeAvailability:
        """Check if last 30 days have sufficient data."""
        month_start = today - timedelta(days=29)
        return self._check_range_availability(
            data_range, TimeRange.MONTH, month_start, today,
            min_days=10, min_coverage=0.3
        )
        
    def _check_year_availability(self, data_range: DataRange, today: date) -> RangeAvailability:
        """Check if last year has sufficient data."""
        year_start = today - timedelta(days=364)
        return self._check_range_availability(
            data_range, TimeRange.YEAR, year_start, today,
            min_days=90, min_coverage=0.25
        )
        
    def _check_range_availability(self, data_range: DataRange, range_type: TimeRange, 
                                start_date: date, end_date: date,
                                min_days: int, min_coverage: float) -> RangeAvailability:
        """Check availability for a specific date range."""
        # Check if range overlaps with available data
        if not data_range.start_date or not data_range.end_date:
            return RangeAvailability(
                range_type=range_type,
                available=False,
                level=AvailabilityLevel.NONE,
                reason="No data available",
                data_points=0,
                coverage_percent=0.0
            )
            
        # Calculate overlap
        overlap_start = max(start_date, data_range.start_date)
        overlap_end = min(end_date, data_range.end_date)
        
        if overlap_start > overlap_end:
            return RangeAvailability(
                range_type=range_type,
                available=False,
                level=AvailabilityLevel.NONE,
                reason="No data in this time range",
                data_points=0,
                coverage_percent=0.0
            )
            
        # Calculate coverage in the overlap period
        total_days = (end_date - start_date).days + 1
        overlap_days = (overlap_end - overlap_start).days + 1
        
        # Count days with data (excluding gaps)
        days_with_data = overlap_days
        for gap_start, gap_end in data_range.gaps:
            gap_overlap_start = max(overlap_start, gap_start)
            gap_overlap_end = min(overlap_end, gap_end)
            if gap_overlap_start <= gap_overlap_end:
                days_with_data -= (gap_overlap_end - gap_overlap_start).days + 1
                
        coverage_percent = (days_with_data / total_days) * 100
        
        # Determine availability
        available = days_with_data >= min_days and (days_with_data / total_days) >= min_coverage
        
        if not available:
            if days_with_data < min_days:
                reason = f"Only {days_with_data} days available (need {min_days})"
            else:
                reason = f"Only {coverage_percent:.1f}% coverage (need {min_coverage*100:.1f}%)"
        else:
            reason = ""
            
        # Determine level
        if coverage_percent >= 90:
            level = AvailabilityLevel.FULL
        elif coverage_percent >= 60:
            level = AvailabilityLevel.PARTIAL
        elif coverage_percent >= 20:
            level = AvailabilityLevel.SPARSE
        else:
            level = AvailabilityLevel.NONE
            
        return RangeAvailability(
            range_type=range_type,
            available=available,
            level=level,
            reason=reason,
            data_points=days_with_data,
            coverage_percent=coverage_percent
        )
        
    def _has_data_for_date_range(self, data_range: DataRange, start_date: date, end_date: date) -> bool:
        """Check if there's any data in the specified date range."""
        if not data_range.start_date or not data_range.end_date:
            return False
            
        # Check if ranges overlap
        if start_date > data_range.end_date or end_date < data_range.start_date:
            return False
            
        # Check if the entire range is in a gap
        for gap_start, gap_end in data_range.gaps:
            if start_date >= gap_start and end_date <= gap_end:
                return False
                
        return True
        
    def suggest_default_range(self, metric_type: str) -> Optional[TimeRange]:
        """Suggest the best default time range for a metric."""
        available_ranges = self.get_available_ranges(metric_type)
        available_ranges = [r for r in available_ranges if r.available]
        
        if not available_ranges:
            return None
            
        # Prefer week view if available with good coverage
        week_ranges = [r for r in available_ranges if r.range_type == TimeRange.WEEK]
        if week_ranges and week_ranges[0].coverage_percent >= 60:
            return TimeRange.WEEK
            
        # Otherwise prefer the range with best coverage
        best_range = max(available_ranges, key=lambda r: r.coverage_percent)
        return best_range.range_type
        
    def invalidate_cache(self) -> None:
        """Invalidate the availability cache."""
        self.availability_cache.clear()
        self.last_scan = None
        logger.info("Data availability cache invalidated")
        self.notify_updates()
        
    def get_cache_stats(self) -> Dict[str, any]:
        """Get statistics about the availability cache."""
        return {
            "cached_metrics": len(self.availability_cache),
            "last_scan": self.last_scan,
            "cache_valid": self._is_cache_valid(),
            "callbacks_registered": len(self.update_callbacks)
        }