"""
Comparison Overlay Calculator for Daily Analytics

Implements multiple overlay types for daily analytics including weekly average,
monthly average, personal best overlay, and historical comparisons.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class OverlayData:
    """Data structure for overlay information"""
    overlay_type: str
    values: pd.Series
    metadata: Dict
    confidence_upper: Optional[pd.Series] = None
    confidence_lower: Optional[pd.Series] = None
    significance: Optional[pd.Series] = None


@dataclass
class ComparisonResult:
    """Result of comparison analysis"""
    current_value: float
    comparison_value: float
    difference: float
    percentage_change: float
    is_significant: bool
    context_message: str


class ComparisonOverlayCalculator:
    """
    Calculates comparison overlays for daily analytics charts.
    
    Provides weekly averages, monthly averages, personal bests,
    and historical comparisons with statistical significance testing.
    """
    
    def __init__(self):
        self.confidence_level = 1.96  # 95% confidence interval
        self.min_data_points = 7  # Minimum points for statistical validity
        
    def calculate_weekly_average(
        self, 
        data: pd.Series, 
        current_date: datetime,
        exclude_current: bool = True
    ) -> OverlayData:
        """
        Calculate rolling 7-day average overlay.
        
        Args:
            data: Time series data indexed by date
            current_date: Current date for calculation
            exclude_current: Whether to exclude current day from calculation
            
        Returns:
            OverlayData with weekly average and confidence bands
        """
        try:
            # Get 7-day window before current date
            end_date = current_date - timedelta(days=1) if exclude_current else current_date
            start_date = end_date - timedelta(days=6)
            
            # Filter data for window
            window_data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            if len(window_data) < 3:  # Need minimum data
                logger.warning(f"Insufficient data for weekly average: {len(window_data)} points")
                return OverlayData(
                    overlay_type="weekly_average",
                    values=pd.Series(dtype=float),
                    metadata={"error": "insufficient_data", "data_points": len(window_data)}
                )
            
            # Calculate rolling statistics
            rolling_mean = data.rolling(window=7, min_periods=3).mean()
            rolling_std = data.rolling(window=7, min_periods=3).std()
            
            # Calculate confidence bands
            confidence_upper = rolling_mean + (self.confidence_level * rolling_std / np.sqrt(7))
            confidence_lower = rolling_mean - (self.confidence_level * rolling_std / np.sqrt(7))
            
            # Calculate trend direction
            if len(window_data) >= 2:
                trend_direction = "up" if window_data.iloc[-1] > window_data.iloc[0] else "down"
            else:
                trend_direction = "neutral"
            
            metadata = {
                "window_size": 7,
                "data_points": len(window_data),
                "mean": float(window_data.mean()) if len(window_data) > 0 else None,
                "std": float(window_data.std()) if len(window_data) > 1 else None,
                "trend_direction": trend_direction,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
            
            return OverlayData(
                overlay_type="weekly_average",
                values=rolling_mean,
                metadata=metadata,
                confidence_upper=confidence_upper,
                confidence_lower=confidence_lower
            )
            
        except Exception as e:
            logger.error(f"Error calculating weekly average: {e}")
            return OverlayData(
                overlay_type="weekly_average",
                values=pd.Series(dtype=float),
                metadata={"error": str(e)}
            )
    
    def calculate_monthly_average(
        self, 
        data: pd.Series, 
        current_date: datetime,
        seasonal_adjustment: bool = False
    ) -> OverlayData:
        """
        Calculate rolling 30-day average overlay.
        
        Args:
            data: Time series data indexed by date
            current_date: Current date for calculation
            seasonal_adjustment: Whether to apply seasonal adjustment
            
        Returns:
            OverlayData with monthly average and confidence bands
        """
        try:
            # Get 30-day window
            end_date = current_date - timedelta(days=1)
            start_date = end_date - timedelta(days=29)
            
            window_data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            if len(window_data) < 7:  # Need minimum week of data
                logger.warning(f"Insufficient data for monthly average: {len(window_data)} points")
                return OverlayData(
                    overlay_type="monthly_average",
                    values=pd.Series(dtype=float),
                    metadata={"error": "insufficient_data", "data_points": len(window_data)}
                )
            
            # Calculate rolling statistics
            rolling_mean = data.rolling(window=30, min_periods=7).mean()
            rolling_std = data.rolling(window=30, min_periods=7).std()
            
            # Apply seasonal adjustment if requested
            if seasonal_adjustment and len(data) > 365:
                seasonal_component = self._calculate_seasonal_component(data)
                rolling_mean = rolling_mean - seasonal_component
            
            # Calculate confidence bands
            confidence_upper = rolling_mean + (self.confidence_level * rolling_std / np.sqrt(30))
            confidence_lower = rolling_mean - (self.confidence_level * rolling_std / np.sqrt(30))
            
            metadata = {
                "window_size": 30,
                "data_points": len(window_data),
                "mean": float(window_data.mean()) if len(window_data) > 0 else None,
                "std": float(window_data.std()) if len(window_data) > 1 else None,
                "seasonal_adjustment": seasonal_adjustment,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
            
            return OverlayData(
                overlay_type="monthly_average",
                values=rolling_mean,
                metadata=metadata,
                confidence_upper=confidence_upper,
                confidence_lower=confidence_lower
            )
            
        except Exception as e:
            logger.error(f"Error calculating monthly average: {e}")
            return OverlayData(
                overlay_type="monthly_average",
                values=pd.Series(dtype=float),
                metadata={"error": str(e)}
            )
    
    def calculate_personal_best(
        self, 
        data: pd.Series, 
        metric_type: str,
        higher_is_better: bool = True
    ) -> OverlayData:
        """
        Calculate personal best overlay.
        
        Args:
            data: Time series data indexed by date
            metric_type: Type of metric for context
            higher_is_better: Whether higher values are better
            
        Returns:
            OverlayData with personal best line
        """
        try:
            if len(data) == 0:
                return OverlayData(
                    overlay_type="personal_best",
                    values=pd.Series(dtype=float),
                    metadata={"error": "no_data"}
                )
            
            # Find personal best
            if higher_is_better:
                best_value = data.max()
                best_date = data.idxmax()
            else:
                best_value = data.min()
                best_date = data.idxmin()
            
            # Create horizontal line at best value
            best_line = pd.Series(
                [best_value] * len(data),
                index=data.index,
                name=f"personal_best_{metric_type}"
            )
            
            # Calculate percentage comparison for each point
            if higher_is_better:
                percentage_of_best = (data / best_value * 100).round(1)
            else:
                percentage_of_best = (best_value / data * 100).round(1)
            
            metadata = {
                "best_value": float(best_value),
                "best_date": best_date.strftime('%Y-%m-%d'),
                "metric_type": metric_type,
                "higher_is_better": higher_is_better,
                "days_since_best": (data.index[-1] - best_date).days if len(data) > 0 else 0,
                "percentage_comparisons": percentage_of_best.to_dict()
            }
            
            return OverlayData(
                overlay_type="personal_best",
                values=best_line,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error calculating personal best: {e}")
            return OverlayData(
                overlay_type="personal_best",
                values=pd.Series(dtype=float),
                metadata={"error": str(e)}
            )
    
    def calculate_historical_comparison(
        self, 
        data: pd.Series, 
        current_date: datetime,
        comparison_periods: List[str] = None
    ) -> Dict[str, OverlayData]:
        """
        Calculate historical comparison overlays.
        
        Args:
            data: Time series data indexed by date
            current_date: Current date for comparison
            comparison_periods: List of periods ('week', 'month', 'year')
            
        Returns:
            Dictionary of OverlayData for each comparison period
        """
        if comparison_periods is None:
            comparison_periods = ['week', 'month', 'year']
        
        results = {}
        
        for period in comparison_periods:
            try:
                if period == 'week':
                    comparison_date = current_date - timedelta(weeks=1)
                elif period == 'month':
                    comparison_date = current_date - timedelta(days=30)
                elif period == 'year':
                    comparison_date = current_date - timedelta(days=365)
                else:
                    logger.warning(f"Unknown comparison period: {period}")
                    continue
                
                # Find closest available data point
                available_dates = data.index
                if len(available_dates) == 0:
                    continue
                    
                closest_date = min(available_dates, key=lambda x: abs((x - comparison_date).days))
                
                # Check if the closest date is within reasonable range (±3 days)
                if abs((closest_date - comparison_date).days) > 3:
                    logger.warning(f"No data near {comparison_date} for {period} comparison")
                    continue
                
                comparison_value = data.loc[closest_date]
                
                # Create horizontal line at comparison value
                comparison_line = pd.Series(
                    [comparison_value] * len(data),
                    index=data.index,
                    name=f"comparison_{period}"
                )
                
                metadata = {
                    "comparison_period": period,
                    "comparison_date": closest_date.strftime('%Y-%m-%d'),
                    "comparison_value": float(comparison_value),
                    "target_date": comparison_date.strftime('%Y-%m-%d'),
                    "days_difference": (closest_date - comparison_date).days
                }
                
                results[f"last_{period}"] = OverlayData(
                    overlay_type=f"historical_{period}",
                    values=comparison_line,
                    metadata=metadata
                )
                
            except Exception as e:
                logger.error(f"Error calculating {period} comparison: {e}")
                continue
        
        return results
    
    def check_statistical_significance(
        self, 
        current_value: float, 
        comparison_values: List[float], 
        alpha: float = 0.05
    ) -> bool:
        """
        Check if current value is statistically significantly different.
        
        Args:
            current_value: Current metric value
            comparison_values: Historical values for comparison
            alpha: Significance level (default 0.05 for 95% confidence)
            
        Returns:
            True if difference is statistically significant
        """
        try:
            if len(comparison_values) < 3:
                return False
            
            comparison_array = np.array(comparison_values)
            mean_comparison = np.mean(comparison_array)
            std_comparison = np.std(comparison_array, ddof=1)
            
            if std_comparison == 0:
                return current_value != mean_comparison
            
            # Calculate z-score
            z_score = abs(current_value - mean_comparison) / (std_comparison / np.sqrt(len(comparison_values)))
            
            # Check significance (two-tailed test)
            critical_value = stats.norm.ppf(1 - alpha/2)
            return z_score > critical_value
            
        except Exception as e:
            logger.error(f"Error in significance test: {e}")
            return False
    
    def generate_context_message(
        self, 
        metric: str, 
        current_value: float,
        comparisons: Dict[str, float]
    ) -> str:
        """
        Generate contextual insight message based on comparisons.
        
        Args:
            metric: Name of the metric
            current_value: Current value
            comparisons: Dictionary of comparison values
            
        Returns:
            Contextual message string
        """
        try:
            messages = []
            
            # Weekly comparison
            if 'weekly_avg' in comparisons:
                weekly_diff = ((current_value - comparisons['weekly_avg']) / comparisons['weekly_avg']) * 100
                if abs(weekly_diff) > 10:  # Significant change
                    direction = "above" if weekly_diff > 0 else "below"
                    messages.append(f"{abs(weekly_diff):.1f}% {direction} weekly average")
            
            # Monthly comparison
            if 'monthly_avg' in comparisons:
                monthly_diff = ((current_value - comparisons['monthly_avg']) / comparisons['monthly_avg']) * 100
                if abs(monthly_diff) > 15:  # Significant change
                    direction = "above" if monthly_diff > 0 else "below"
                    messages.append(f"{abs(monthly_diff):.1f}% {direction} monthly average")
            
            # Personal best comparison
            if 'personal_best' in comparisons:
                best_diff = ((current_value - comparisons['personal_best']) / comparisons['personal_best']) * 100
                if best_diff > -5:  # Close to or exceeding personal best
                    if best_diff >= 0:
                        messages.append("New personal best! 🎉")
                    else:
                        messages.append(f"{abs(best_diff):.1f}% from personal best")
            
            # Historical comparisons
            if 'last_week' in comparisons:
                week_diff = ((current_value - comparisons['last_week']) / comparisons['last_week']) * 100
                if abs(week_diff) > 20:
                    direction = "higher" if week_diff > 0 else "lower"
                    messages.append(f"{abs(week_diff):.1f}% {direction} than last week")
            
            # Generate summary message
            if not messages:
                return f"Today's {metric}: {current_value:.1f}"
            elif len(messages) == 1:
                return f"Today's {metric}: {messages[0]}"
            else:
                return f"Today's {metric}: {messages[0]}; {messages[1]}"
                
        except Exception as e:
            logger.error(f"Error generating context message: {e}")
            return f"Today's {metric}: {current_value:.1f}"
    
    def _calculate_seasonal_component(self, data: pd.Series) -> pd.Series:
        """Calculate seasonal component for adjustment."""
        try:
            # Simple seasonal decomposition using day of year
            data_with_dayofyear = data.copy()
            data_with_dayofyear.index = pd.to_datetime(data_with_dayofyear.index)
            
            # Group by day of year and calculate average
            seasonal_means = data_with_dayofyear.groupby(data_with_dayofyear.index.dayofyear).mean()
            overall_mean = data_with_dayofyear.mean()
            
            # Calculate seasonal component (deviation from overall mean)
            seasonal_component = pd.Series(index=data.index, dtype=float)
            for idx in data.index:
                day_of_year = pd.to_datetime(idx).dayofyear
                if day_of_year in seasonal_means.index:
                    seasonal_component.loc[idx] = seasonal_means.loc[day_of_year] - overall_mean
                else:
                    seasonal_component.loc[idx] = 0
            
            return seasonal_component
            
        except Exception as e:
            logger.error(f"Error calculating seasonal component: {e}")
            return pd.Series([0] * len(data), index=data.index)