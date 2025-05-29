"""Predefined dashboard templates for health data visualization."""

from typing import List, Dict, Any
from .dashboard_models import (
    DashboardTemplate, ChartConfig, GridSpec, LayoutType
)


class HealthDashboardTemplates:
    """Collection of predefined dashboard templates for health data."""
    
    @staticmethod
    def daily_overview() -> DashboardTemplate:
        """Daily health overview template with key metrics."""
        return DashboardTemplate(
            name='daily_overview',
            title='Daily Health Overview',
            description='Comprehensive view of today\'s health metrics',
            chart_configs=[
                ChartConfig(
                    chart_id='heart_rate_trend',
                    metric_type='heart_rate',
                    chart_type='time_series',
                    grid_spec=GridSpec(0, 0, 2, 6),  # Top left, half width
                    config={
                        'title': 'Heart Rate',
                        'subtitle': '24-hour trend with zones',
                        'show_zones': True,
                        'show_average': True,
                        'color': '#FF6B6B'  # Coral red for heart
                    }
                ),
                ChartConfig(
                    chart_id='steps_progress',
                    metric_type='steps',
                    chart_type='progress_ring',
                    grid_spec=GridSpec(0, 6, 1, 3),  # Top right
                    config={
                        'title': 'Daily Steps',
                        'subtitle': 'Progress to goal',
                        'goal': 10000,
                        'color': '#4ECDC4'  # Teal
                    }
                ),
                ChartConfig(
                    chart_id='active_calories',
                    metric_type='active_calories',
                    chart_type='progress_ring',
                    grid_spec=GridSpec(0, 9, 1, 3),  # Top right
                    config={
                        'title': 'Active Calories',
                        'subtitle': 'Calories burned',
                        'goal': 500,
                        'color': '#FFE66D'  # Yellow
                    }
                ),
                ChartConfig(
                    chart_id='activity_breakdown',
                    metric_type='activity',
                    chart_type='stacked_bar',
                    grid_spec=GridSpec(1, 6, 1, 6),  # Middle right
                    config={
                        'title': 'Activity Breakdown',
                        'metrics': ['move', 'exercise', 'stand'],
                        'show_goals': True
                    }
                ),
                ChartConfig(
                    chart_id='sleep_timeline',
                    metric_type='sleep',
                    chart_type='timeline',
                    grid_spec=GridSpec(2, 0, 1, 12),  # Bottom full width
                    config={
                        'title': 'Sleep Analysis',
                        'subtitle': 'Sleep stages and quality',
                        'show_stages': True,
                        'show_quality_score': True,
                        'height_ratio': 0.3  # Shorter height
                    }
                ),
                ChartConfig(
                    chart_id='hydration_intake',
                    metric_type='water',
                    chart_type='bar_progress',
                    grid_spec=GridSpec(3, 0, 1, 4),  # Bottom row
                    config={
                        'title': 'Hydration',
                        'subtitle': 'Water intake (oz)',
                        'goal': 64,
                        'color': '#45B7D1'  # Light blue
                    }
                ),
                ChartConfig(
                    chart_id='nutrition_summary',
                    metric_type='nutrition',
                    chart_type='macro_breakdown',
                    grid_spec=GridSpec(3, 4, 1, 4),  # Bottom row
                    config={
                        'title': 'Nutrition',
                        'subtitle': 'Macro breakdown',
                        'show_calories': True
                    }
                ),
                ChartConfig(
                    chart_id='wellness_score',
                    metric_type='wellness_score',
                    chart_type='radial_gauge',
                    grid_spec=GridSpec(3, 8, 1, 4),  # Bottom row
                    config={
                        'title': 'Wellness Score',
                        'subtitle': 'Overall health today',
                        'show_components': True
                    }
                )
            ],
            layout_type=LayoutType.GRID
        )
    
    @staticmethod
    def weekly_trends() -> DashboardTemplate:
        """Weekly trend analysis template."""
        return DashboardTemplate(
            name='weekly_trends',
            title='Weekly Health Trends',
            description='Track patterns and progress over the past week',
            chart_configs=[
                ChartConfig(
                    chart_id='multi_metric_trend',
                    metric_type='multiple',
                    chart_type='multi_line',
                    grid_spec=GridSpec(0, 0, 2, 8),  # Large left chart
                    config={
                        'title': 'Weekly Activity Trends',
                        'metrics': ['steps', 'active_calories', 'exercise_minutes'],
                        'normalize': True,
                        'show_moving_average': True,
                        'colors': ['#4ECDC4', '#FFE66D', '#FF6B6B']
                    }
                ),
                ChartConfig(
                    chart_id='week_comparison',
                    metric_type='comparison',
                    chart_type='grouped_bar',
                    grid_spec=GridSpec(0, 8, 1, 4),  # Top right
                    config={
                        'title': 'This Week vs Last',
                        'metrics': ['steps', 'calories', 'distance'],
                        'show_percentage_change': True
                    }
                ),
                ChartConfig(
                    chart_id='day_patterns',
                    metric_type='patterns',
                    chart_type='heatmap',
                    grid_spec=GridSpec(1, 8, 1, 4),  # Bottom right
                    config={
                        'title': 'Day of Week Patterns',
                        'metric': 'activity_level',
                        'color_scheme': 'warm'
                    }
                ),
                ChartConfig(
                    chart_id='sleep_consistency',
                    metric_type='sleep',
                    chart_type='range_chart',
                    grid_spec=GridSpec(2, 0, 1, 6),  # Bottom left
                    config={
                        'title': 'Sleep Consistency',
                        'show_bedtime': True,
                        'show_wake_time': True,
                        'show_duration': True
                    }
                ),
                ChartConfig(
                    chart_id='heart_variability',
                    metric_type='heart_rate_variability',
                    chart_type='box_plot',
                    grid_spec=GridSpec(2, 6, 1, 6),  # Bottom right
                    config={
                        'title': 'HRV Distribution',
                        'show_outliers': True,
                        'show_trend': True
                    }
                )
            ],
            layout_type=LayoutType.GRID
        )
    
    @staticmethod
    def monthly_analysis() -> DashboardTemplate:
        """Monthly analysis dashboard template."""
        return DashboardTemplate(
            name='monthly_analysis',
            title='Monthly Health Analysis',
            description='Long-term trends and monthly patterns',
            chart_configs=[
                ChartConfig(
                    chart_id='monthly_calendar',
                    metric_type='activity',
                    chart_type='calendar_heatmap',
                    grid_spec=GridSpec(0, 0, 2, 7),  # Left side
                    config={
                        'title': 'Activity Calendar',
                        'metric': 'steps',
                        'show_goals': True,
                        'color_scheme': 'sequential_warm'
                    }
                ),
                ChartConfig(
                    chart_id='monthly_trends',
                    metric_type='trends',
                    chart_type='area_chart',
                    grid_spec=GridSpec(0, 7, 1, 5),  # Top right
                    config={
                        'title': 'Monthly Trends',
                        'metrics': ['avg_steps', 'avg_sleep', 'avg_calories'],
                        'show_confidence_interval': True
                    }
                ),
                ChartConfig(
                    chart_id='goal_achievement',
                    metric_type='goals',
                    chart_type='bullet_chart',
                    grid_spec=GridSpec(1, 7, 1, 5),  # Bottom right
                    config={
                        'title': 'Goal Achievement',
                        'show_all_goals': True,
                        'show_progress': True
                    }
                ),
                ChartConfig(
                    chart_id='health_score_trend',
                    metric_type='health_score',
                    chart_type='sparkline_grid',
                    grid_spec=GridSpec(2, 0, 1, 12),  # Bottom full width
                    config={
                        'title': 'Health Score Components',
                        'show_all_components': True,
                        'show_total_score': True
                    }
                )
            ],
            layout_type=LayoutType.GRID
        )
    
    @staticmethod
    def workout_focus() -> DashboardTemplate:
        """Workout and fitness focused dashboard."""
        return DashboardTemplate(
            name='workout_focus',
            title='Workout & Fitness Dashboard',
            description='Detailed workout metrics and performance tracking',
            chart_configs=[
                ChartConfig(
                    chart_id='workout_calendar',
                    metric_type='workouts',
                    chart_type='workout_calendar',
                    grid_spec=GridSpec(0, 0, 2, 6),  # Left side
                    config={
                        'title': 'Workout History',
                        'show_types': True,
                        'show_duration': True,
                        'show_intensity': True
                    }
                ),
                ChartConfig(
                    chart_id='heart_rate_zones',
                    metric_type='heart_rate',
                    chart_type='zone_distribution',
                    grid_spec=GridSpec(0, 6, 1, 6),  # Top right
                    config={
                        'title': 'Heart Rate Zones',
                        'show_time_in_zone': True,
                        'show_zone_goals': True
                    }
                ),
                ChartConfig(
                    chart_id='performance_metrics',
                    metric_type='performance',
                    chart_type='radar_chart',
                    grid_spec=GridSpec(1, 6, 1, 6),  # Bottom right
                    config={
                        'title': 'Fitness Components',
                        'metrics': ['endurance', 'strength', 'flexibility', 'balance'],
                        'show_improvement': True
                    }
                ),
                ChartConfig(
                    chart_id='recovery_status',
                    metric_type='recovery',
                    chart_type='recovery_gauge',
                    grid_spec=GridSpec(2, 0, 1, 4),  # Bottom left
                    config={
                        'title': 'Recovery Status',
                        'show_hrv': True,
                        'show_sleep_quality': True
                    }
                ),
                ChartConfig(
                    chart_id='workout_volume',
                    metric_type='volume',
                    chart_type='cumulative_line',
                    grid_spec=GridSpec(2, 4, 1, 8),  # Bottom right
                    config={
                        'title': 'Training Volume',
                        'show_weekly_total': True,
                        'show_trend': True
                    }
                )
            ],
            layout_type=LayoutType.GRID
        )
    
    @staticmethod
    def health_monitoring() -> DashboardTemplate:
        """Health monitoring dashboard for medical metrics."""
        return DashboardTemplate(
            name='health_monitoring',
            title='Health Monitoring Dashboard',
            description='Track vital signs and medical metrics',
            chart_configs=[
                ChartConfig(
                    chart_id='blood_pressure',
                    metric_type='blood_pressure',
                    chart_type='bp_chart',
                    grid_spec=GridSpec(0, 0, 1, 6),  # Top left
                    config={
                        'title': 'Blood Pressure',
                        'show_systolic': True,
                        'show_diastolic': True,
                        'show_guidelines': True
                    }
                ),
                ChartConfig(
                    chart_id='resting_heart_rate',
                    metric_type='resting_hr',
                    chart_type='trend_line',
                    grid_spec=GridSpec(0, 6, 1, 6),  # Top right
                    config={
                        'title': 'Resting Heart Rate',
                        'show_normal_range': True,
                        'show_trend': True
                    }
                ),
                ChartConfig(
                    chart_id='body_measurements',
                    metric_type='body_measurements',
                    chart_type='multi_axis',
                    grid_spec=GridSpec(1, 0, 1, 8),  # Middle left
                    config={
                        'title': 'Body Measurements',
                        'metrics': ['weight', 'bmi', 'body_fat'],
                        'show_goals': True
                    }
                ),
                ChartConfig(
                    chart_id='vitals_summary',
                    metric_type='vitals',
                    chart_type='vital_cards',
                    grid_spec=GridSpec(1, 8, 1, 4),  # Middle right
                    config={
                        'title': 'Current Vitals',
                        'show_all_vitals': True,
                        'show_status': True
                    }
                ),
                ChartConfig(
                    chart_id='medication_adherence',
                    metric_type='medications',
                    chart_type='adherence_chart',
                    grid_spec=GridSpec(2, 0, 1, 12),  # Bottom full width
                    config={
                        'title': 'Medication Adherence',
                        'show_schedule': True,
                        'show_compliance_rate': True
                    }
                )
            ],
            layout_type=LayoutType.GRID
        )
    
    @staticmethod
    def get_all_templates() -> Dict[str, DashboardTemplate]:
        """Get all available dashboard templates."""
        return {
            'daily_overview': HealthDashboardTemplates.daily_overview(),
            'weekly_trends': HealthDashboardTemplates.weekly_trends(),
            'monthly_analysis': HealthDashboardTemplates.monthly_analysis(),
            'workout_focus': HealthDashboardTemplates.workout_focus(),
            'health_monitoring': HealthDashboardTemplates.health_monitoring()
        }
    
    @staticmethod
    def get_template_by_name(name: str) -> DashboardTemplate:
        """Get a specific template by name."""
        templates = HealthDashboardTemplates.get_all_templates()
        if name not in templates:
            raise ValueError(f"Template '{name}' not found")
        return templates[name]