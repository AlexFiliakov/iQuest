"""Personalization engine for health score adjustments."""

from typing import Dict, Optional, List
from .health_score_models import UserProfile, HealthCondition


class PersonalizationEngine:
    """Engine for personalizing health scores based on user profile."""
    
    def __init__(self, user_profile: UserProfile):
        """Initialize with user profile."""
        self.user_profile = user_profile
        self.conditions = self._load_health_conditions()
    
    def adjust_for_age(self, component: str, base_score: float) -> float:
        """Adjust score based on age-appropriate expectations."""
        age = self.user_profile.age
        
        age_factors = {
            'activity': self._get_activity_age_factor(age),
            'sleep': self._get_sleep_age_factor(age),
            'heart': self._get_heart_age_factor(age),
            'other': 1.0  # No age adjustment for other metrics
        }
        
        factor = age_factors.get(component, 1.0)
        return base_score * factor
    
    def adjust_for_conditions(self, component: str, base_score: float) -> float:
        """Adjust score based on health conditions."""
        if not self.user_profile.health_conditions:
            return base_score
        
        factor = 1.0
        for condition_name in self.user_profile.health_conditions:
            condition = self.conditions.get(condition_name)
            if condition:
                component_factor = condition.component_factors.get(component, 1.0)
                factor *= component_factor
        
        return base_score * factor
    
    def adjust_for_fitness_level(self, component: str, base_score: float) -> float:
        """Adjust score based on fitness level."""
        if not self.user_profile.fitness_level:
            return base_score
        
        fitness_adjustments = {
            'sedentary': {
                'activity': 1.1,  # More credit for activity
                'sleep': 1.0,
                'heart': 0.9,  # Expectations adjusted
                'other': 1.0
            },
            'lightly_active': {
                'activity': 1.05,
                'sleep': 1.0,
                'heart': 0.95,
                'other': 1.0
            },
            'moderately_active': {
                'activity': 1.0,
                'sleep': 1.0,
                'heart': 1.0,
                'other': 1.0
            },
            'very_active': {
                'activity': 0.95,  # Higher expectations
                'sleep': 1.05,  # More credit for recovery
                'heart': 1.05,  # Higher expectations
                'other': 1.0
            }
        }
        
        level_factors = fitness_adjustments.get(self.user_profile.fitness_level, {})
        factor = level_factors.get(component, 1.0)
        
        return base_score * factor
    
    def get_personalized_weights(self, default_weights: Dict[str, float]) -> Dict[str, float]:
        """Get personalized component weights based on user goals and conditions."""
        weights = default_weights.copy()
        
        # Adjust weights based on health conditions
        if 'diabetes' in self.user_profile.health_conditions:
            weights['activity'] *= 1.2
            weights['other'] *= 1.1  # Nutrition more important
        
        if 'hypertension' in self.user_profile.health_conditions:
            weights['heart'] *= 1.3
            weights['activity'] *= 1.1
        
        if 'insomnia' in self.user_profile.health_conditions:
            weights['sleep'] *= 1.3
        
        # Adjust based on goals
        if 'weight_loss' in self.user_profile.goals:
            weights['activity'] *= 1.2
            weights['other'] *= 1.1  # Nutrition
        
        if 'stress_reduction' in self.user_profile.goals:
            weights['sleep'] *= 1.1
            weights['heart'] *= 1.1  # HRV
            weights['other'] *= 1.1  # Mindfulness
        
        if 'athletic_performance' in self.user_profile.goals:
            weights['activity'] *= 1.1
            weights['heart'] *= 1.2
            weights['sleep'] *= 1.1  # Recovery
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    
    def _get_activity_age_factor(self, age: int) -> float:
        """Get age adjustment factor for activity."""
        if age < 18:
            return 1.1  # Higher expectations for youth
        elif age < 30:
            return 1.05
        elif age < 50:
            return 1.0
        elif age < 65:
            return 0.95
        elif age < 80:
            return 0.85
        else:
            return 0.75  # Significantly adjusted for elderly
    
    def _get_sleep_age_factor(self, age: int) -> float:
        """Get age adjustment factor for sleep."""
        if age < 18:
            return 0.95  # Teens often have irregular sleep
        elif age < 65:
            return 1.0
        else:
            return 0.95  # Seniors may need less sleep
    
    def _get_heart_age_factor(self, age: int) -> float:
        """Get age adjustment factor for heart health."""
        if age < 30:
            return 1.05  # Young adults should have excellent heart health
        elif age < 50:
            return 1.0
        elif age < 65:
            return 0.95
        else:
            return 0.90  # Age-related changes expected
    
    def _load_health_conditions(self) -> Dict[str, HealthCondition]:
        """Load health condition definitions."""
        return {
            'diabetes': HealthCondition(
                name='diabetes',
                component_factors={
                    'activity': 1.1,  # Extra important
                    'sleep': 1.05,
                    'heart': 1.1,
                    'other': 1.15  # Nutrition critical
                },
                description='Diabetes requires consistent activity and nutrition management'
            ),
            'hypertension': HealthCondition(
                name='hypertension',
                component_factors={
                    'activity': 1.1,
                    'sleep': 1.0,
                    'heart': 1.2,  # Critical
                    'other': 1.05
                },
                description='High blood pressure requires heart health focus'
            ),
            'arthritis': HealthCondition(
                name='arthritis',
                component_factors={
                    'activity': 0.8,  # Adjusted expectations
                    'sleep': 1.05,  # May affect sleep
                    'heart': 1.0,
                    'other': 1.0
                },
                description='Joint conditions may limit certain activities'
            ),
            'copd': HealthCondition(
                name='copd',
                component_factors={
                    'activity': 0.7,  # Significantly adjusted
                    'sleep': 1.1,  # Often affects sleep
                    'heart': 1.1,
                    'other': 1.0
                },
                description='Respiratory conditions affect activity capacity'
            ),
            'insomnia': HealthCondition(
                name='insomnia',
                component_factors={
                    'activity': 1.0,
                    'sleep': 0.8,  # Adjusted expectations
                    'heart': 0.95,  # May affect HRV
                    'other': 1.05  # Stress management important
                },
                description='Sleep disorders require adjusted sleep scoring'
            ),
            'depression': HealthCondition(
                name='depression',
                component_factors={
                    'activity': 0.9,  # May affect motivation
                    'sleep': 0.9,  # Often disrupted
                    'heart': 0.95,
                    'other': 1.1  # Mental health tracking important
                },
                description='Mental health conditions affect multiple components'
            ),
            'obesity': HealthCondition(
                name='obesity',
                component_factors={
                    'activity': 0.85,  # Adjusted for capacity
                    'sleep': 0.95,  # May affect sleep quality
                    'heart': 0.9,  # Higher risk factors
                    'other': 1.1  # Nutrition important
                },
                description='Weight management requires balanced approach'
            )
        }
    
    def get_personalized_recommendations(self, component_scores: Dict[str, float]) -> List[str]:
        """Generate personalized recommendations based on scores and profile."""
        recommendations = []
        
        # Age-specific recommendations
        age = self.user_profile.age
        if age >= 65:
            if component_scores.get('activity', 0) < 70:
                recommendations.append("Consider low-impact activities like walking or swimming")
            if component_scores.get('heart', 0) < 70:
                recommendations.append("Regular blood pressure monitoring is important at your age")
        elif age < 30:
            if component_scores.get('sleep', 0) < 70:
                recommendations.append("Establish a consistent sleep schedule for better health")
        
        # Condition-specific recommendations
        if 'diabetes' in self.user_profile.health_conditions:
            if component_scores.get('activity', 0) < 80:
                recommendations.append("Regular physical activity helps manage blood sugar")
            recommendations.append("Track nutrition data for better diabetes management")
        
        if 'hypertension' in self.user_profile.health_conditions:
            if component_scores.get('heart', 0) < 80:
                recommendations.append("Focus on stress reduction and regular cardio exercise")
        
        # Goal-specific recommendations
        if 'weight_loss' in self.user_profile.goals:
            if component_scores.get('activity', 0) < 80:
                recommendations.append("Increase daily activity to support weight loss goals")
        
        if 'athletic_performance' in self.user_profile.goals:
            if component_scores.get('sleep', 0) < 85:
                recommendations.append("Prioritize sleep for optimal athletic recovery")
        
        return recommendations