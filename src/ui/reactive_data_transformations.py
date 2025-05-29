"""
Data Transformation Pipelines for Reactive Data Binding

This module provides flexible data transformation capabilities for the
reactive data binding system, allowing data to be transformed before
being applied to visualizations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class DataTransformation(ABC):
    """Base class for data transformations"""
    
    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply transformation to data"""
        pass
        
    @abstractmethod
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if this transformation can be applied to the data"""
        pass
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class AggregationTransformation(DataTransformation):
    """Aggregate data over time periods"""
    
    def __init__(self, period: str, aggregation_func: Union[str, Callable] = 'mean'):
        self.period = period
        self.aggregation_func = aggregation_func
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate data by the specified period"""
        if data.empty:
            return data
            
        # Ensure we have a datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                data = data.set_index('timestamp')
            else:
                logger.warning("No timestamp column found for aggregation")
                return data
                
        # Resample and aggregate
        try:
            if isinstance(self.aggregation_func, str):
                result = data.resample(self.period).agg(self.aggregation_func)
            else:
                result = data.resample(self.period).apply(self.aggregation_func)
                
            # Remove any rows with all NaN values
            result = result.dropna(how='all')
            return result
            
        except Exception as e:
            logger.error(f"Error in aggregation: {e}")
            return data
            
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if data has datetime index or timestamp column"""
        return (isinstance(data.index, pd.DatetimeIndex) or 
                'timestamp' in data.columns)


class SlidingWindowTransformation(DataTransformation):
    """Apply sliding window calculations"""
    
    def __init__(self, window_size: int, calculation: str = 'mean'):
        self.window_size = window_size
        self.calculation = calculation
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply sliding window calculation"""
        if data.empty or len(data) < self.window_size:
            return data
            
        try:
            if self.calculation == 'mean':
                return data.rolling(window=self.window_size).mean()
            elif self.calculation == 'sum':
                return data.rolling(window=self.window_size).sum()
            elif self.calculation == 'std':
                return data.rolling(window=self.window_size).std()
            elif self.calculation == 'min':
                return data.rolling(window=self.window_size).min()
            elif self.calculation == 'max':
                return data.rolling(window=self.window_size).max()
            else:
                logger.warning(f"Unknown calculation: {self.calculation}")
                return data
                
        except Exception as e:
            logger.error(f"Error in sliding window: {e}")
            return data
            
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if data has enough rows for window"""
        return len(data) >= self.window_size


class NormalizationTransformation(DataTransformation):
    """Normalize data to a specific range"""
    
    def __init__(self, method: str = 'minmax', range_min: float = 0, range_max: float = 1):
        self.method = method
        self.range_min = range_min
        self.range_max = range_max
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize numeric columns"""
        if data.empty:
            return data
            
        result = data.copy()
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if self.method == 'minmax':
                min_val = data[col].min()
                max_val = data[col].max()
                if max_val > min_val:
                    result[col] = (data[col] - min_val) / (max_val - min_val)
                    result[col] = result[col] * (self.range_max - self.range_min) + self.range_min
                    
            elif self.method == 'zscore':
                mean_val = data[col].mean()
                std_val = data[col].std()
                if std_val > 0:
                    result[col] = (data[col] - mean_val) / std_val
                    
        return result
        
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if data has numeric columns"""
        return len(data.select_dtypes(include=[np.number]).columns) > 0


class FilterTransformation(DataTransformation):
    """Filter data based on conditions"""
    
    def __init__(self, conditions: Dict[str, Any]):
        self.conditions = conditions
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply filtering conditions"""
        if data.empty:
            return data
            
        result = data
        
        for column, condition in self.conditions.items():
            if column not in data.columns:
                continue
                
            if isinstance(condition, dict):
                # Range condition
                if 'min' in condition:
                    result = result[result[column] >= condition['min']]
                if 'max' in condition:
                    result = result[result[column] <= condition['max']]
                if 'values' in condition:
                    result = result[result[column].isin(condition['values'])]
            else:
                # Equality condition
                result = result[result[column] == condition]
                
        return result
        
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if any filter columns exist in data"""
        return any(col in data.columns for col in self.conditions.keys())


class HealthMetricTransformation(DataTransformation):
    """Specialized transformations for health metrics"""
    
    def __init__(self, metric_type: str):
        self.metric_type = metric_type
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply health-specific transformations"""
        if data.empty:
            return data
            
        if self.metric_type == 'heart_rate_zones':
            return self._calculate_heart_rate_zones(data)
        elif self.metric_type == 'activity_intensity':
            return self._calculate_activity_intensity(data)
        elif self.metric_type == 'sleep_quality':
            return self._calculate_sleep_quality(data)
        else:
            return data
            
    def _calculate_heart_rate_zones(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate heart rate zones"""
        if 'heart_rate' not in data.columns:
            return data
            
        result = data.copy()
        
        # Define zones (assuming age 30 for example)
        max_hr = 190  # 220 - age
        zones = {
            'rest': (0, 0.5 * max_hr),
            'light': (0.5 * max_hr, 0.6 * max_hr),
            'moderate': (0.6 * max_hr, 0.7 * max_hr),
            'hard': (0.7 * max_hr, 0.85 * max_hr),
            'maximum': (0.85 * max_hr, max_hr)
        }
        
        # Calculate zone for each heart rate value
        def get_zone(hr):
            for zone_name, (min_hr, max_hr) in zones.items():
                if min_hr <= hr < max_hr:
                    return zone_name
            return 'maximum'
            
        result['heart_rate_zone'] = result['heart_rate'].apply(get_zone)
        return result
        
    def _calculate_activity_intensity(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate activity intensity from steps"""
        if 'steps' not in data.columns:
            return data
            
        result = data.copy()
        
        # Define intensity levels based on steps per hour
        def get_intensity(steps_per_hour):
            if steps_per_hour < 1000:
                return 'sedentary'
            elif steps_per_hour < 3000:
                return 'light'
            elif steps_per_hour < 6000:
                return 'moderate'
            else:
                return 'vigorous'
                
        # Assuming data is hourly
        result['activity_intensity'] = result['steps'].apply(get_intensity)
        return result
        
    def _calculate_sleep_quality(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate sleep quality score"""
        if 'sleep_duration' not in data.columns:
            return data
            
        result = data.copy()
        
        # Simple sleep quality based on duration
        def get_quality(duration_hours):
            if 7 <= duration_hours <= 9:
                return 'excellent'
            elif 6 <= duration_hours < 7 or 9 < duration_hours <= 10:
                return 'good'
            elif 5 <= duration_hours < 6 or 10 < duration_hours <= 11:
                return 'fair'
            else:
                return 'poor'
                
        result['sleep_quality'] = result['sleep_duration'].apply(get_quality)
        return result
        
    def can_transform(self, data: pd.DataFrame) -> bool:
        """Check if relevant columns exist"""
        if self.metric_type == 'heart_rate_zones':
            return 'heart_rate' in data.columns
        elif self.metric_type == 'activity_intensity':
            return 'steps' in data.columns
        elif self.metric_type == 'sleep_quality':
            return 'sleep_duration' in data.columns
        return False


class TransformationPipeline:
    """Compose multiple transformations into a pipeline"""
    
    def __init__(self, transformations: List[DataTransformation]):
        self.transformations = transformations
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply all transformations in sequence"""
        result = data
        
        for transformation in self.transformations:
            if transformation.can_transform(result):
                result = transformation.transform(result)
            else:
                logger.warning(f"Skipping {transformation} - cannot transform data")
                
        return result
        
    def add_transformation(self, transformation: DataTransformation) -> None:
        """Add a transformation to the pipeline"""
        self.transformations.append(transformation)
        
    def remove_transformation(self, index: int) -> None:
        """Remove a transformation by index"""
        if 0 <= index < len(self.transformations):
            self.transformations.pop(index)
            
    def __repr__(self) -> str:
        return f"TransformationPipeline({len(self.transformations)} transformations)"


# Predefined pipelines for common use cases

def create_daily_summary_pipeline() -> TransformationPipeline:
    """Create pipeline for daily health summaries"""
    return TransformationPipeline([
        AggregationTransformation('D', 'mean'),
        NormalizationTransformation('minmax', 0, 100)
    ])


def create_weekly_trend_pipeline() -> TransformationPipeline:
    """Create pipeline for weekly trend analysis"""
    return TransformationPipeline([
        AggregationTransformation('W', 'mean'),
        SlidingWindowTransformation(4, 'mean'),  # 4-week moving average
        NormalizationTransformation('zscore')
    ])


def create_activity_analysis_pipeline() -> TransformationPipeline:
    """Create pipeline for activity analysis"""
    return TransformationPipeline([
        HealthMetricTransformation('activity_intensity'),
        AggregationTransformation('H', 'sum'),  # Hourly totals
        FilterTransformation({'activity_intensity': {'values': ['moderate', 'vigorous']}})
    ])


def create_heart_rate_analysis_pipeline() -> TransformationPipeline:
    """Create pipeline for heart rate analysis"""
    return TransformationPipeline([
        HealthMetricTransformation('heart_rate_zones'),
        SlidingWindowTransformation(10, 'mean'),  # 10-minute average
        FilterTransformation({'heart_rate': {'min': 40, 'max': 200}})  # Valid range
    ])