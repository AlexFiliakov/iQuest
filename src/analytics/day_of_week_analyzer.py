"""Day of week pattern analysis for health metrics."""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternResult:
    """Result of pattern detection."""
    pattern_type: str
    confidence: float
    description: str
    details: Dict[str, Any]


@dataclass
class ChiSquareResult:
    """Result of chi-square test for independence."""
    statistic: float
    p_value: float
    degrees_of_freedom: int
    is_significant: bool
    interpretation: str


@dataclass
class DayMetrics:
    """Metrics for a specific day of week."""
    day_name: str
    day_number: int
    mean: float
    std: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    consistency_score: float


class DayOfWeekAnalyzer:
    """Analyze health metrics by day of week to identify patterns."""
    
    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize analyzer with health data.
        
        Args:
            data: DataFrame with columns ['date', 'metric_type', 'value', 'unit']
        """
        self.data = data.copy()
        self._prepare_data()
        self.patterns = {}
        self.day_metrics = {}
        
    def _prepare_data(self):
        """Add day of week information to data."""
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
            self.data['day_of_week'] = self.data['date'].dt.dayofweek
            self.data['day_name'] = self.data['date'].dt.day_name()
            self.data['hour'] = self.data['date'].dt.hour
    
    def _ensure_prepared(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensure data has day_of_week and other required columns."""
        if 'day_of_week' not in data.columns and 'date' in data.columns:
            data = data.copy()
            data['date'] = pd.to_datetime(data['date'])
            data['day_of_week'] = data['date'].dt.dayofweek
            data['day_name'] = data['date'].dt.day_name()
            data['hour'] = data['date'].dt.hour
        return data
        
    def analyze_metric(self, metric_type: str) -> Dict[str, Any]:
        """
        Perform complete analysis for a specific metric.
        
        Args:
            metric_type: Type of metric to analyze
            
        Returns:
            Dictionary containing all analysis results
        """
        metric_data = self.data[self.data['metric_type'] == metric_type]
        
        if metric_data.empty:
            logger.warning(f"No data found for metric type: {metric_type}")
            return {}
        
        results = {
            'metric_type': metric_type,
            'day_metrics': self.calculate_day_metrics(metric_data),
            'patterns': self.detect_all_patterns(metric_data),
            'chi_square': self.perform_chi_square_test(metric_data),
            'consistency_scores': self.calculate_consistency_scores(metric_data),
            'habit_strength': self.calculate_habit_strength(metric_data)
        }
        
        return results
    
    def calculate_day_metrics(self, data: pd.DataFrame) -> Dict[int, DayMetrics]:
        """Calculate metrics for each day of week."""
        data = self._ensure_prepared(data)
        day_metrics = {}
        
        for day in range(7):
            day_data = data[data['day_of_week'] == day]['value']
            
            if len(day_data) < 2:
                continue
                
            mean = day_data.mean()
            std = day_data.std()
            sem = stats.sem(day_data)
            ci = stats.t.interval(0.95, len(day_data)-1, loc=mean, scale=sem)
            
            consistency = 1 - (std / mean) if mean > 0 else 0
            
            day_metrics[day] = DayMetrics(
                day_name=self.DAY_NAMES[day],
                day_number=day,
                mean=mean,
                std=std,
                confidence_interval=ci,
                sample_size=len(day_data),
                consistency_score=max(0, min(1, consistency))
            )
        
        return day_metrics
    
    def detect_all_patterns(self, data: pd.DataFrame) -> List[PatternResult]:
        """Detect all patterns in the data."""
        patterns = []
        
        weekend_warrior = self.detect_weekend_warrior(data)
        if weekend_warrior:
            patterns.append(weekend_warrior)
            
        monday_blues = self.detect_monday_blues(data)
        if monday_blues:
            patterns.append(monday_blues)
            
        workday_warrior = self.detect_workday_warrior(data)
        if workday_warrior:
            patterns.append(workday_warrior)
            
        return patterns
    
    def detect_weekend_warrior(self, data: pd.DataFrame) -> Optional[PatternResult]:
        """Detect weekend warrior pattern."""
        data = self._ensure_prepared(data)
        weekday_data = data[data['day_of_week'].isin([0, 1, 2, 3, 4])]['value']
        weekend_data = data[data['day_of_week'].isin([5, 6])]['value']
        
        if weekday_data.empty or weekend_data.empty:
            return None
            
        weekday_avg = weekday_data.mean()
        weekend_avg = weekend_data.mean()
        
        if weekday_avg <= 0:
            return None
            
        ratio = weekend_avg / weekday_avg
        
        if ratio > 1.5:
            # Statistical test
            t_stat, p_value = stats.ttest_ind(weekend_data, weekday_data)
            
            confidence = min(0.99, 1 - p_value) if p_value < 0.05 else 0.0
            
            return PatternResult(
                pattern_type='weekend_warrior',
                confidence=confidence,
                description=f"Weekend activity is {ratio:.1f}x higher than weekdays",
                details={
                    'weekday_average': weekday_avg,
                    'weekend_average': weekend_avg,
                    'ratio': ratio,
                    'p_value': p_value
                }
            )
        
        return None
    
    def detect_monday_blues(self, data: pd.DataFrame) -> Optional[PatternResult]:
        """Detect Monday blues pattern."""
        data = self._ensure_prepared(data)
        monday_data = data[data['day_of_week'] == 0]['value']
        other_days_data = data[data['day_of_week'] != 0]['value']
        
        if monday_data.empty or other_days_data.empty:
            return None
            
        monday_avg = monday_data.mean()
        other_avg = other_days_data.mean()
        
        if other_avg <= 0:
            return None
            
        ratio = monday_avg / other_avg
        
        if ratio < 0.8:
            # Statistical test
            t_stat, p_value = stats.ttest_ind(monday_data, other_days_data)
            
            confidence = min(0.99, 1 - p_value) if p_value < 0.05 else 0.0
            
            # Check for gradual improvement through week
            weekly_trend = []
            for day in range(5):  # Monday to Friday
                day_avg = data[data['day_of_week'] == day]['value'].mean()
                weekly_trend.append(day_avg)
            
            is_improving = all(weekly_trend[i] <= weekly_trend[i+1] 
                              for i in range(len(weekly_trend)-1))
            
            return PatternResult(
                pattern_type='monday_blues',
                confidence=confidence,
                description=f"Monday activity is {(1-ratio)*100:.0f}% lower than other days",
                details={
                    'monday_average': monday_avg,
                    'other_days_average': other_avg,
                    'ratio': ratio,
                    'p_value': p_value,
                    'gradual_improvement': is_improving
                }
            )
        
        return None
    
    def detect_workday_warrior(self, data: pd.DataFrame) -> Optional[PatternResult]:
        """Detect workday warrior pattern (opposite of weekend warrior)."""
        data = self._ensure_prepared(data)
        weekday_data = data[data['day_of_week'].isin([0, 1, 2, 3, 4])]['value']
        weekend_data = data[data['day_of_week'].isin([5, 6])]['value']
        
        if weekday_data.empty or weekend_data.empty:
            return None
            
        weekday_avg = weekday_data.mean()
        weekend_avg = weekend_data.mean()
        
        if weekend_avg <= 0:
            return None
            
        ratio = weekday_avg / weekend_avg
        
        if ratio > 1.3:
            # Statistical test
            t_stat, p_value = stats.ttest_ind(weekday_data, weekend_data)
            
            confidence = min(0.99, 1 - p_value) if p_value < 0.05 else 0.0
            
            return PatternResult(
                pattern_type='workday_warrior',
                confidence=confidence,
                description=f"Weekday activity is {ratio:.1f}x higher than weekends",
                details={
                    'weekday_average': weekday_avg,
                    'weekend_average': weekend_avg,
                    'ratio': ratio,
                    'p_value': p_value
                }
            )
        
        return None
    
    def calculate_consistency_scores(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate consistency score for each day."""
        data = self._ensure_prepared(data)
        scores = {}
        
        for day in range(7):
            day_data = data[data['day_of_week'] == day]['value']
            
            if len(day_data) < 2:
                scores[self.DAY_NAMES[day]] = 0.0
                continue
                
            mean = day_data.mean()
            std = day_data.std()
            cv = std / mean if mean > 0 else float('inf')
            
            # Convert coefficient of variation to consistency score (0-1)
            consistency = max(0, min(1, 1 - cv))
            scores[self.DAY_NAMES[day]] = consistency
        
        return scores
    
    def calculate_habit_strength(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate habit strength indicators."""
        data = self._ensure_prepared(data)
        habit_metrics = {
            'regularity_score': self._calculate_regularity(data),
            'time_consistency': self._calculate_time_consistency(data),
            'completion_rate': self._calculate_completion_rate(data),
            'overall_strength': 0.0
        }
        
        # Calculate overall strength as weighted average
        weights = {'regularity_score': 0.4, 'time_consistency': 0.3, 'completion_rate': 0.3}
        habit_metrics['overall_strength'] = sum(
            habit_metrics[k] * weights[k] 
            for k in weights.keys()
        )
        
        return habit_metrics
    
    def _calculate_regularity(self, data: pd.DataFrame) -> float:
        """Calculate regularity score (0-100)."""
        # Ensure data is prepared
        data = self._ensure_prepared(data)
        
        # Check how many days per week have data
        weekly_coverage = data.groupby([
            pd.Grouper(key='date', freq='W'),
            'day_of_week'
        ]).size().groupby(level=0).count()
        
        if weekly_coverage.empty:
            return 0.0
            
        avg_days_per_week = weekly_coverage.mean()
        return min(100, (avg_days_per_week / 7) * 100)
    
    def _calculate_time_consistency(self, data: pd.DataFrame) -> float:
        """Calculate time of day consistency."""
        data = self._ensure_prepared(data)
        
        if 'hour' not in data.columns:
            return 0.0
            
        # Calculate standard deviation of activity hours
        hour_std = data.groupby('day_of_week')['hour'].std().mean()
        
        # Convert to consistency score (lower std = higher consistency)
        max_std = 12  # Maximum possible std for 24 hours
        consistency = max(0, min(100, (1 - hour_std / max_std) * 100))
        
        return consistency
    
    def _calculate_completion_rate(self, data: pd.DataFrame) -> float:
        """Calculate activity completion rate."""
        data = self._ensure_prepared(data)
        
        # Count days with any activity
        active_days = data['date'].dt.date.nunique()
        
        # Calculate total days in date range
        date_range = (data['date'].max() - data['date'].min()).days + 1
        
        if date_range <= 0:
            return 0.0
            
        return min(100, (active_days / date_range) * 100)
    
    def perform_chi_square_test(self, data: pd.DataFrame) -> ChiSquareResult:
        """Test if activity depends on day of week."""
        data = self._ensure_prepared(data)
        # Create contingency table
        day_counts = data.groupby('day_of_week').size()
        
        # Ensure all days are represented
        all_days = pd.Series(0, index=range(7))
        all_days.update(day_counts)
        
        # Expected frequencies (uniform distribution)
        total = all_days.sum()
        expected = total / 7
        
        # Chi-square test
        chi2, p_value = stats.chisquare(all_days, f_exp=[expected] * 7)
        
        is_significant = bool(p_value < 0.05)
        
        if is_significant:
            interpretation = "Activity levels significantly depend on day of week"
        else:
            interpretation = "Activity levels are independent of day of week"
        
        return ChiSquareResult(
            statistic=chi2,
            p_value=p_value,
            degrees_of_freedom=6,
            is_significant=is_significant,
            interpretation=interpretation
        )
    
    def create_radar_chart(self, metric_type: str, ax: Optional[plt.Axes] = None, 
                          animate: bool = False) -> Figure:
        """Create spider/radar chart for weekly pattern."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        else:
            fig = ax.figure
        
        # Get day metrics
        metric_data = self.data[self.data['metric_type'] == metric_type]
        metric_data = self._ensure_prepared(metric_data)
        day_metrics = self.calculate_day_metrics(metric_data)
        
        # Prepare data
        angles = np.linspace(0, 2 * np.pi, 7, endpoint=False).tolist()
        values = [day_metrics.get(i, DayMetrics('', i, 0, 0, (0, 0), 0, 0)).mean 
                 for i in range(7)]
        
        # Normalize values for better visualization
        max_val = max(values) if max(values) > 0 else 1
        norm_values = [v / max_val for v in values]
        
        # Close the polygon
        angles += angles[:1]
        norm_values += norm_values[:1]
        
        # Plot with optional animation
        if animate:
            # Simple animation effect - start from center and grow
            import matplotlib.animation as animation
            
            def animate_frame(frame):
                ax.clear()
                progress = frame / 30  # 30 frames
                current_values = [v * progress for v in norm_values]
                current_values += current_values[:1]  # Close polygon
                
                ax.plot(angles, current_values, 'o-', linewidth=2, color='#FF8C42')
                ax.fill(angles, current_values, alpha=0.25, color='#FFD166')
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(self.DAY_NAMES)
                ax.set_ylim(0, 1.1)
                ax.set_title(f'{metric_type} - Weekly Pattern', fontsize=14, pad=20)
                ax.grid(True, alpha=0.3)
                
                return ax.patches + ax.lines
            
            # Create animation
            anim = animation.FuncAnimation(fig, animate_frame, frames=31, 
                                         interval=50, blit=False, repeat=False)
        else:
            # Static plot
            ax.plot(angles, norm_values, 'o-', linewidth=2, color='#FF8C42')
            ax.fill(angles, norm_values, alpha=0.25, color='#FFD166')
        
        # Customize
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.DAY_NAMES)
        ax.set_ylim(0, 1.1)
        ax.set_title(f'{metric_type} - Weekly Pattern', fontsize=14, pad=20)
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for angle, value, norm_val in zip(angles[:-1], values, norm_values[:-1]):
            ax.text(angle, norm_val + 0.05, f'{value:.1f}', 
                   ha='center', va='center', fontsize=10)
        
        return fig
    
    def create_heatmap(self, metric_type: str, ax: Optional[plt.Axes] = None) -> Figure:
        """Create heatmap with time-of-day breakdown."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        else:
            fig = ax.figure
        
        # Prepare data
        metric_data = self.data[self.data['metric_type'] == metric_type]
        metric_data = self._ensure_prepared(metric_data)
        
        # Create pivot table
        heatmap_data = metric_data.pivot_table(
            values='value',
            index='hour',
            columns='day_of_week',
            aggfunc='mean'
        )
        
        # Ensure all days and hours are represented
        full_index = range(24)
        full_columns = range(7)
        heatmap_data = heatmap_data.reindex(index=full_index, columns=full_columns)
        
        # Create custom colormap (Yellow-Orange-Red)
        cmap = LinearSegmentedColormap.from_list('YlOrRd', ['#FFFFCC', '#FFD166', '#FF8C42', '#D84315'])
        
        # Create heatmap using imshow
        im = ax.imshow(heatmap_data.values, cmap=cmap, aspect='auto')
        
        # Add colorbar
        if hasattr(fig, 'colorbar'):
            cbar = fig.colorbar(im, ax=ax)
        else:
            cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Average Value', rotation=270, labelpad=20)
        
        # Set ticks and labels
        ax.set_xticks(range(7))
        ax.set_xticklabels(self.DAY_NAMES)
        ax.set_yticks(range(24))
        ax.set_yticklabels([f'{h:02d}:00' for h in range(24)])
        
        ax.set_title(f'{metric_type} - Activity by Day and Hour', fontsize=14, pad=10)
        ax.set_xlabel('Day of Week', fontsize=12)
        ax.set_ylabel('Hour of Day', fontsize=12)
        
        # Add grid
        ax.set_xticks(np.arange(-.5, 7, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 24, 1), minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=0.5)
        
        return fig
    
    def create_pattern_summary_chart(self, patterns: List[PatternResult], 
                                   ax: Optional[plt.Axes] = None) -> Figure:
        """Create a summary chart of detected patterns."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        if not patterns:
            ax.text(0.5, 0.5, 'No patterns detected', ha='center', va='center', 
                   fontsize=14, transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        # Prepare data
        pattern_names = [p.pattern_type.replace('_', ' ').title() for p in patterns]
        confidences = [p.confidence * 100 for p in patterns]
        
        # Create horizontal bar chart
        y_pos = np.arange(len(pattern_names))
        bars = ax.barh(y_pos, confidences, color='#FF8C42', alpha=0.8)
        
        # Customize
        ax.set_yticks(y_pos)
        ax.set_yticklabels(pattern_names)
        ax.set_xlabel('Confidence (%)', fontsize=12)
        ax.set_title('Detected Patterns', fontsize=14, pad=10)
        ax.set_xlim(0, 100)
        
        # Add value labels
        for i, (bar, conf) in enumerate(zip(bars, confidences)):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'{conf:.0f}%', va='center', fontsize=10)
        
        # Add descriptions
        for i, pattern in enumerate(patterns):
            ax.text(5, i - 0.3, pattern.description, fontsize=9, 
                   style='italic', color='gray')
        
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        
        return fig
    
    def detect_weekday_anomalies(self, data: pd.DataFrame, metric_type: str, 
                                z_threshold: float = 2.0) -> Dict[int, List[Dict]]:
        """Detect anomalies per weekday using z-score."""
        data = self._ensure_prepared(data)
        metric_data = data[data['metric_type'] == metric_type]
        
        anomalies_by_day = {}
        
        for day in range(7):
            day_data = metric_data[metric_data['day_of_week'] == day].copy()
            
            if len(day_data) < 3:  # Need minimum data for anomaly detection
                anomalies_by_day[day] = []
                continue
            
            # Calculate z-scores for this day
            mean_val = day_data['value'].mean()
            std_val = day_data['value'].std()
            
            if std_val == 0:  # No variation
                anomalies_by_day[day] = []
                continue
            
            day_data['z_score'] = (day_data['value'] - mean_val) / std_val
            
            # Find anomalies
            anomalies = day_data[abs(day_data['z_score']) > z_threshold]
            
            anomaly_list = []
            for _, row in anomalies.iterrows():
                anomaly_list.append({
                    'date': row['date'],
                    'value': row['value'],
                    'z_score': row['z_score'],
                    'is_high': row['z_score'] > 0,
                    'day_name': self.DAY_NAMES[day]
                })
            
            anomalies_by_day[day] = anomaly_list
        
        return anomalies_by_day
    
    def add_custom_pattern(self, pattern_name: str, pattern_function):
        """Add a user-configurable pattern definition."""
        if not hasattr(self, '_custom_patterns'):
            self._custom_patterns = {}
        
        self._custom_patterns[pattern_name] = pattern_function
    
    def detect_custom_patterns(self, data: pd.DataFrame) -> List[PatternResult]:
        """Detect user-defined custom patterns."""
        if not hasattr(self, '_custom_patterns'):
            return []
        
        data = self._ensure_prepared(data)
        custom_results = []
        
        for pattern_name, pattern_func in self._custom_patterns.items():
            try:
                result = pattern_func(data)
                if result and isinstance(result, PatternResult):
                    custom_results.append(result)
            except Exception as e:
                logger.warning(f"Custom pattern '{pattern_name}' failed: {e}")
        
        return custom_results
    
    def get_pattern_config_template(self) -> Dict[str, Any]:
        """Get template for configuring custom patterns."""
        return {
            'weekend_warrior_threshold': 1.5,
            'monday_blues_threshold': 0.8,
            'workday_warrior_threshold': 1.3,
            'significance_level': 0.05,
            'min_data_points': 10,
            'custom_patterns': {
                'example_pattern': {
                    'description': 'Template for custom pattern',
                    'threshold': 1.0,
                    'days_to_check': [0, 1, 2, 3, 4, 5, 6],
                    'comparison_type': 'ratio'  # 'ratio', 'difference', 'percentile'
                }
            }
        }