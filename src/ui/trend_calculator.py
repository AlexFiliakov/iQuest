"""Trend calculation utilities for daily metrics comparison."""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TrendCalculator:
    """Calculate trends and comparisons for daily metrics."""
    
    @staticmethod
    def calculate_daily_change(
        current_value: float,
        previous_value: Optional[float],
        handle_zero: bool = True
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate absolute and percentage change between two values.
        
        Args:
            current_value: Today's value
            previous_value: Yesterday's value (or last available)
            handle_zero: If True, returns None for percentage when previous is 0
            
        Returns:
            Tuple of (absolute_change, percentage_change)
        """
        if previous_value is None:
            return None, None
            
        absolute_change = current_value - previous_value
        
        # Handle zero values
        if previous_value == 0:
            if handle_zero:
                # Return absolute change only
                return absolute_change, None
            else:
                # Avoid division by zero
                percentage_change = 100.0 if current_value > 0 else 0.0
        else:
            percentage_change = (absolute_change / previous_value) * 100
            
        return absolute_change, percentage_change
        
    @staticmethod
    def get_previous_day_value(
        data: pd.DataFrame,
        current_date: datetime,
        metric_column: str,
        max_lookback_days: int = 7
    ) -> Optional[float]:
        """
        Get the previous day's value, looking back up to max_lookback_days if needed.
        
        Args:
            data: DataFrame with date index
            current_date: Current date
            metric_column: Column name containing the metric
            max_lookback_days: Maximum days to look back
            
        Returns:
            Previous value or None if not found
        """
        for i in range(1, max_lookback_days + 1):
            previous_date = current_date - timedelta(days=i)
            if previous_date in data.index:
                return data.loc[previous_date, metric_column]
                
        return None
        
    @staticmethod
    def get_trend_history(
        data: pd.DataFrame,
        end_date: datetime,
        metric_column: str,
        days: int = 7,
        fill_missing: bool = True
    ) -> List[float]:
        """
        Get historical values for trend visualization.
        
        Args:
            data: DataFrame with date index
            end_date: End date (inclusive)
            metric_column: Column name containing the metric
            days: Number of days to retrieve
            fill_missing: If True, interpolate missing values
            
        Returns:
            List of values (oldest to newest)
        """
        start_date = end_date - timedelta(days=days - 1)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        values = []
        for date in date_range:
            if date in data.index:
                values.append(data.loc[date, metric_column])
            else:
                if fill_missing and values:
                    # Use last known value
                    values.append(values[-1])
                else:
                    values.append(np.nan)
                    
        # Interpolate NaN values if requested
        if fill_missing:
            df_temp = pd.Series(values)
            df_temp = df_temp.interpolate(method='linear', limit_direction='both')
            values = df_temp.tolist()
            
        return values
        
    @staticmethod
    def classify_change_magnitude(percentage_change: Optional[float]) -> str:
        """
        Classify the magnitude of change for styling.
        
        Args:
            percentage_change: Percentage change value
            
        Returns:
            Classification string: 'significant_increase', 'moderate_increase',
            'minimal', 'moderate_decrease', 'significant_decrease', or 'neutral'
        """
        if percentage_change is None:
            return 'neutral'
            
        abs_change = abs(percentage_change)
        
        if abs_change < 0.1:
            return 'minimal'
        elif percentage_change > 0:
            if abs_change > 20:
                return 'significant_increase'
            elif abs_change > 10:
                return 'moderate_increase'
            else:
                return 'minor_increase'
        else:
            if abs_change > 20:
                return 'significant_decrease'
            elif abs_change > 10:
                return 'moderate_decrease'
            else:
                return 'minor_decrease'
                
    @staticmethod
    def get_trend_color(classification: str) -> str:
        """
        Get color for trend classification.
        
        Args:
            classification: Change classification
            
        Returns:
            Hex color code
        """
        color_map = {
            'significant_increase': '#2E7D32',  # Dark green
            'moderate_increase': '#95C17B',     # Medium green
            'minor_increase': '#FFD166',        # Yellow
            'minimal': '#8B7355',               # Neutral brown
            'minor_decrease': '#F4A261',        # Amber
            'moderate_decrease': '#E76F51',     # Medium red
            'significant_decrease': '#C62828',  # Dark red
            'neutral': '#8B7355'                # Neutral brown
        }
        return color_map.get(classification, '#8B7355')
        
    @staticmethod
    def calculate_trend_statistics(values: List[float]) -> Dict[str, float]:
        """
        Calculate trend statistics for a series of values.
        
        Args:
            values: List of values
            
        Returns:
            Dictionary with trend statistics
        """
        if not values or len(values) < 2:
            return {}
            
        clean_values = [v for v in values if not np.isnan(v)]
        if not clean_values:
            return {}
            
        # Calculate linear regression for trend
        x = np.arange(len(clean_values))
        y = np.array(clean_values)
        
        # Fit linear trend
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Calculate statistics
        stats = {
            'mean': np.mean(clean_values),
            'median': np.median(clean_values),
            'std': np.std(clean_values),
            'min': np.min(clean_values),
            'max': np.max(clean_values),
            'range': np.max(clean_values) - np.min(clean_values),
            'trend_slope': slope,
            'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
        }
        
        # Calculate volatility (coefficient of variation)
        if stats['mean'] != 0:
            stats['volatility'] = (stats['std'] / stats['mean']) * 100
        else:
            stats['volatility'] = 0
            
        return stats