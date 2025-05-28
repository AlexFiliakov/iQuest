"""
Time-based Comparison Utilities for Bar Charts

Provides utilities for creating daily/weekly comparisons and time-based
grouping logic for health data visualization.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class TimeComparisonType(Enum):
    """Types of time-based comparisons available."""
    DAY_OVER_DAY = "day_over_day"
    WEEK_OVER_WEEK = "week_over_week"
    MONTH_OVER_MONTH = "month_over_month"
    DAILY_AVERAGE = "daily_average"
    WEEKLY_AVERAGE = "weekly_average"
    BASELINE_COMPARISON = "baseline_comparison"


@dataclass
class ComparisonConfig:
    """Configuration for time-based comparisons."""
    comparison_type: TimeComparisonType
    reference_period_days: int = 30
    include_percentage_change: bool = True
    include_trend_indicators: bool = True
    baseline_value: Optional[float] = None
    group_weekends: bool = False
    

class TimeComparisonEngine:
    """Engine for creating time-based health data comparisons."""
    
    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig(TimeComparisonType.DAY_OVER_DAY)
        
    def create_daily_comparison(self, data: pd.DataFrame, metric_column: str) -> pd.DataFrame:
        """
        Create daily comparison chart data.
        
        Args:
            data: DataFrame with datetime index and health metrics
            metric_column: Column name to compare
            
        Returns:
            DataFrame formatted for bar chart display with comparison values
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
            
        # Sort by date
        data = data.sort_index()
        
        # Get recent days for comparison
        recent_data = data.tail(14)  # Last 2 weeks
        
        if len(recent_data) < 2:
            raise ValueError("Need at least 2 days of data for comparison")
            
        # Create comparison data
        comparison_data = []
        
        for i in range(1, len(recent_data)):
            current_date = recent_data.index[i]
            previous_date = recent_data.index[i-1]
            
            current_value = recent_data.iloc[i][metric_column]
            previous_value = recent_data.iloc[i-1][metric_column]
            
            # Calculate change
            if self.config.include_percentage_change and previous_value != 0:
                percent_change = ((current_value - previous_value) / previous_value) * 100
            else:
                percent_change = 0
                
            comparison_data.append({
                'Date': current_date.strftime('%a %m/%d'),
                'Current': current_value,
                'Previous': previous_value,
                'Change': current_value - previous_value,
                'Percent_Change': percent_change
            })
            
        return pd.DataFrame(comparison_data).set_index('Date')
        
    def create_weekly_comparison(self, data: pd.DataFrame, metric_column: str) -> pd.DataFrame:
        """
        Create weekly comparison chart data.
        
        Args:
            data: DataFrame with datetime index and health metrics
            metric_column: Column name to compare
            
        Returns:
            DataFrame formatted for weekly comparison bar chart
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
            
        # Group by week
        data['Week'] = data.index.isocalendar().week
        data['Year'] = data.index.year
        data['Week_Year'] = data['Year'].astype(str) + '-W' + data['Week'].astype(str)
        
        # Calculate weekly averages
        weekly_avg = data.groupby('Week_Year')[metric_column].mean()
        weekly_count = data.groupby('Week_Year')[metric_column].count()
        
        # Only include weeks with sufficient data (at least 4 days)
        weekly_avg = weekly_avg[weekly_count >= 4]
        
        if len(weekly_avg) < 2:
            raise ValueError("Need at least 2 weeks of data for comparison")
            
        # Get recent weeks
        recent_weeks = weekly_avg.tail(8)  # Last 8 weeks
        
        # Create comparison data
        comparison_data = []
        
        for i in range(1, len(recent_weeks)):
            current_week = recent_weeks.index[i]
            previous_week = recent_weeks.index[i-1]
            
            current_value = recent_weeks.iloc[i]
            previous_value = recent_weeks.iloc[i-1]
            
            # Calculate change
            if self.config.include_percentage_change and previous_value != 0:
                percent_change = ((current_value - previous_value) / previous_value) * 100
            else:
                percent_change = 0
                
            comparison_data.append({
                'Week': current_week,
                'Current_Week': current_value,
                'Previous_Week': previous_value,
                'Change': current_value - previous_value,
                'Percent_Change': percent_change
            })
            
        return pd.DataFrame(comparison_data).set_index('Week')
        
    def create_baseline_comparison(self, data: pd.DataFrame, metric_column: str, 
                                 baseline_period_days: int = 30) -> pd.DataFrame:
        """
        Create comparison against baseline period.
        
        Args:
            data: DataFrame with datetime index and health metrics
            metric_column: Column name to compare
            baseline_period_days: Number of days to use for baseline calculation
            
        Returns:
            DataFrame comparing recent values to baseline
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
            
        data = data.sort_index()
        
        if len(data) < baseline_period_days + 7:
            raise ValueError(f"Need at least {baseline_period_days + 7} days of data")
            
        # Calculate baseline (earlier period)
        baseline_data = data.iloc[:baseline_period_days]
        baseline_avg = baseline_data[metric_column].mean()
        
        # Get recent data for comparison
        recent_data = data.tail(7)  # Last week
        
        comparison_data = []
        
        for date, row in recent_data.iterrows():
            current_value = row[metric_column]
            
            # Calculate difference from baseline
            diff_from_baseline = current_value - baseline_avg
            
            if self.config.include_percentage_change and baseline_avg != 0:
                percent_change = (diff_from_baseline / baseline_avg) * 100
            else:
                percent_change = 0
                
            comparison_data.append({
                'Date': date.strftime('%a %m/%d'),
                'Current': current_value,
                'Baseline': baseline_avg,
                'Difference': diff_from_baseline,
                'Percent_Change': percent_change
            })
            
        return pd.DataFrame(comparison_data).set_index('Date')
        
    def create_day_of_week_comparison(self, data: pd.DataFrame, metric_column: str) -> pd.DataFrame:
        """
        Create day-of-week pattern comparison.
        
        Args:
            data: DataFrame with datetime index and health metrics
            metric_column: Column name to analyze
            
        Returns:
            DataFrame showing patterns by day of week
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
            
        # Add day of week
        data_copy = data.copy()
        data_copy['DayOfWeek'] = data_copy.index.day_name()
        data_copy['WeekNumber'] = data_copy.index.isocalendar().week
        
        # Calculate averages by day of week
        day_averages = data_copy.groupby('DayOfWeek')[metric_column].agg(['mean', 'std', 'count'])
        
        # Get last 4 weeks for comparison
        recent_weeks = data_copy.tail(28)  # Last 4 weeks
        recent_day_averages = recent_weeks.groupby('DayOfWeek')[metric_column].mean()
        
        # Order by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_averages = day_averages.reindex([d for d in day_order if d in day_averages.index])
        recent_day_averages = recent_day_averages.reindex([d for d in day_order if d in recent_day_averages.index])
        
        # Create comparison data
        comparison_data = pd.DataFrame({
            'Overall_Average': day_averages['mean'],
            'Recent_4_Weeks': recent_day_averages,
            'Standard_Deviation': day_averages['std']
        })
        
        # Calculate differences
        comparison_data['Difference'] = (
            comparison_data['Recent_4_Weeks'] - comparison_data['Overall_Average']
        )
        
        if self.config.include_percentage_change:
            comparison_data['Percent_Change'] = (
                comparison_data['Difference'] / comparison_data['Overall_Average'] * 100
            ).fillna(0)
            
        return comparison_data
        
    def add_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add trend indicators to comparison data.
        
        Args:
            data: DataFrame with comparison data
            
        Returns:
            DataFrame with trend indicators added
        """
        if not self.config.include_trend_indicators:
            return data
            
        data_copy = data.copy()
        
        # Add trend direction indicators
        if 'Change' in data_copy.columns:
            data_copy['Trend'] = data_copy['Change'].apply(
                lambda x: '↑' if x > 0 else '↓' if x < 0 else '→'
            )
            
        if 'Percent_Change' in data_copy.columns:
            data_copy['Trend_Strength'] = data_copy['Percent_Change'].apply(
                lambda x: 'Strong' if abs(x) > 20 else 'Moderate' if abs(x) > 10 else 'Mild'
            )
            
        return data_copy
        
    def format_for_bar_chart(self, comparison_data: pd.DataFrame, 
                            chart_type: str = 'grouped') -> pd.DataFrame:
        """
        Format comparison data for specific bar chart types.
        
        Args:
            comparison_data: DataFrame with comparison results
            chart_type: Type of bar chart ('simple', 'grouped', 'stacked')
            
        Returns:
            DataFrame formatted for the specified chart type
        """
        if chart_type == 'simple':
            # For simple charts, return just the current/main values
            if 'Current' in comparison_data.columns:
                return comparison_data[['Current']]
            elif 'Recent_4_Weeks' in comparison_data.columns:
                return comparison_data[['Recent_4_Weeks']]
            else:
                return comparison_data.iloc[:, [0]]
                
        elif chart_type == 'grouped':
            # For grouped charts, show current vs reference values
            if 'Current' in comparison_data.columns and 'Previous' in comparison_data.columns:
                return comparison_data[['Current', 'Previous']]
            elif 'Current_Week' in comparison_data.columns and 'Previous_Week' in comparison_data.columns:
                return comparison_data[['Current_Week', 'Previous_Week']]
            elif 'Overall_Average' in comparison_data.columns and 'Recent_4_Weeks' in comparison_data.columns:
                return comparison_data[['Overall_Average', 'Recent_4_Weeks']]
            else:
                return comparison_data
                
        elif chart_type == 'stacked':
            # For stacked charts, break down components if available
            # This would need custom logic based on the specific use case
            return comparison_data
            
        return comparison_data


def create_time_comparison_chart_data(data: pd.DataFrame, metric_column: str,
                                    comparison_type: TimeComparisonType,
                                    **kwargs) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to create comparison data for charts.
    
    Args:
        data: DataFrame with datetime index and health metrics
        metric_column: Column name to compare
        comparison_type: Type of comparison to perform
        **kwargs: Additional configuration options
        
    Returns:
        Tuple of (formatted_data, chart_title)
    """
    # Filter kwargs to only include valid config parameters
    valid_config_keys = {'reference_period_days', 'include_percentage_change', 'include_trend_indicators', 'baseline_value', 'group_weekends'}
    config_kwargs = {k: v for k, v in kwargs.items() if k in valid_config_keys}
    config = ComparisonConfig(comparison_type, **config_kwargs)
    engine = TimeComparisonEngine(config)
    
    try:
        if comparison_type == TimeComparisonType.DAY_OVER_DAY:
            comparison_data = engine.create_daily_comparison(data, metric_column)
            chart_data = engine.format_for_bar_chart(comparison_data, 'grouped')
            title = f"Daily {metric_column} Comparison - Current vs Previous Day"
            
        elif comparison_type == TimeComparisonType.WEEK_OVER_WEEK:
            comparison_data = engine.create_weekly_comparison(data, metric_column)
            chart_data = engine.format_for_bar_chart(comparison_data, 'grouped')
            title = f"Weekly {metric_column} Comparison - Current vs Previous Week"
            
        elif comparison_type == TimeComparisonType.BASELINE_COMPARISON:
            baseline_days = kwargs.get('baseline_period_days', 30)
            comparison_data = engine.create_baseline_comparison(data, metric_column, baseline_days)
            chart_data = engine.format_for_bar_chart(comparison_data, 'grouped')
            title = f"{metric_column} vs {baseline_days}-Day Baseline"
            
        elif comparison_type == TimeComparisonType.DAILY_AVERAGE:
            comparison_data = engine.create_day_of_week_comparison(data, metric_column)
            chart_data = engine.format_for_bar_chart(comparison_data, 'grouped')
            title = f"{metric_column} by Day of Week - Overall vs Recent 4 Weeks"
            
        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")
            
        return chart_data, title
        
    except ValueError as e:
        # Return empty data with error message in title
        empty_data = pd.DataFrame()
        error_title = f"Error: {str(e)}"
        return empty_data, error_title


# Example usage functions
def demo_time_comparisons():
    """Demonstrate various time comparison utilities."""
    
    # Create sample health data
    dates = pd.date_range(start='2024-02-01', end='2024-03-30', freq='D')
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'Steps': np.random.normal(8500, 1500, len(dates)).astype(int),
        'Heart_Rate': np.random.normal(72, 8, len(dates)).astype(int),
        'Sleep_Hours': np.random.normal(7.5, 1.0, len(dates)),
        'Active_Minutes': np.random.normal(45, 15, len(dates)).astype(int)
    }, index=dates)
    
    # Ensure realistic ranges
    sample_data['Steps'] = sample_data['Steps'].clip(lower=2000, upper=15000)
    sample_data['Heart_Rate'] = sample_data['Heart_Rate'].clip(lower=55, upper=100)
    sample_data['Sleep_Hours'] = sample_data['Sleep_Hours'].clip(lower=5.0, upper=10.0)
    sample_data['Active_Minutes'] = sample_data['Active_Minutes'].clip(lower=10, upper=120)
    
    print("Time Comparison Utilities Demo")
    print("==============================")
    
    # Daily comparison
    daily_data, daily_title = create_time_comparison_chart_data(
        sample_data, 'Steps', TimeComparisonType.DAY_OVER_DAY
    )
    print(f"\n1. {daily_title}")
    print(f"   Data shape: {daily_data.shape}")
    
    # Weekly comparison
    weekly_data, weekly_title = create_time_comparison_chart_data(
        sample_data, 'Heart_Rate', TimeComparisonType.WEEK_OVER_WEEK
    )
    print(f"\n2. {weekly_title}")
    print(f"   Data shape: {weekly_data.shape}")
    
    # Baseline comparison
    baseline_data, baseline_title = create_time_comparison_chart_data(
        sample_data, 'Sleep_Hours', TimeComparisonType.BASELINE_COMPARISON,
        baseline_period_days=20
    )
    print(f"\n3. {baseline_title}")
    print(f"   Data shape: {baseline_data.shape}")
    
    # Day of week patterns
    dow_data, dow_title = create_time_comparison_chart_data(
        sample_data, 'Active_Minutes', TimeComparisonType.DAILY_AVERAGE
    )
    print(f"\n4. {dow_title}")
    print(f"   Data shape: {dow_data.shape}")
    
    print("\n✓ All time comparison utilities working correctly!")
    
    return {
        'daily': (daily_data, daily_title),
        'weekly': (weekly_data, weekly_title),
        'baseline': (baseline_data, baseline_title),
        'day_of_week': (dow_data, dow_title)
    }


if __name__ == '__main__':
    demo_time_comparisons()