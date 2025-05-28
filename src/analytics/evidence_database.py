"""
Evidence database for medical guidelines and research-based recommendations.

This module manages the storage and retrieval of evidence-based medical guidelines
from authoritative sources like CDC, WHO, NSF, and other medical organizations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from .health_insights_models import (
    MedicalGuideline, InsightCategory, EvidenceLevel, InsightEvidence
)


class EvidenceDatabase:
    """Database of medical guidelines and evidence-based recommendations."""
    
    def __init__(self):
        """Initialize the evidence database with built-in guidelines."""
        self.guidelines: Dict[str, List[MedicalGuideline]] = {}
        self._initialize_guidelines()
    
    def _initialize_guidelines(self):
        """Load built-in medical guidelines from authoritative sources."""
        # Sleep Guidelines (CDC, NSF)
        self.guidelines['sleep'] = [
            MedicalGuideline(
                category=InsightCategory.SLEEP,
                metric_type='sleep_duration',
                source='CDC',
                guideline_name='Recommended Sleep Duration by Age',
                recommendations={
                    'adult_18_60': {'min_hours': 7, 'max_hours': 9, 'optimal_hours': 8},
                    'adult_61_64': {'min_hours': 7, 'max_hours': 9, 'optimal_hours': 8},
                    'adult_65_plus': {'min_hours': 7, 'max_hours': 8, 'optimal_hours': 7.5},
                    'general': {'min_hours': 7, 'max_hours': 9, 'optimal_hours': 8}
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2022, 3, 2),
                url='https://www.cdc.gov/sleep/about_sleep/how_much_sleep.html',
                notes='Based on extensive epidemiological studies'
            ),
            MedicalGuideline(
                category=InsightCategory.SLEEP,
                metric_type='sleep_consistency',
                source='NSF',
                guideline_name='Sleep Schedule Consistency',
                recommendations={
                    'general': {
                        'bedtime_variability_minutes': 30,
                        'wake_time_variability_minutes': 30,
                        'importance': 'critical for circadian rhythm regulation'
                    }
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2023, 1, 15),
                url='https://www.sleepfoundation.org/',
                notes='Consistent sleep-wake times improve sleep quality'
            ),
            MedicalGuideline(
                category=InsightCategory.SLEEP,
                metric_type='sleep_efficiency',
                source='AASM',
                guideline_name='Sleep Efficiency Standards',
                recommendations={
                    'general': {
                        'minimum_efficiency_percent': 85,
                        'optimal_efficiency_percent': 90,
                        'calculation': 'time asleep / time in bed * 100'
                    }
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2021, 6, 1),
                notes='Sleep efficiency below 85% may indicate sleep disorders'
            )
        ]
        
        # Activity Guidelines (WHO, ACSM)
        self.guidelines['activity'] = [
            MedicalGuideline(
                category=InsightCategory.ACTIVITY,
                metric_type='aerobic_activity',
                source='WHO',
                guideline_name='Physical Activity Guidelines for Adults',
                recommendations={
                    'adult_18_64': {
                        'moderate_minutes_weekly': 150,
                        'vigorous_minutes_weekly': 75,
                        'or_combination': True,
                        'sessions_per_week': 3
                    },
                    'adult_65_plus': {
                        'moderate_minutes_weekly': 150,
                        'vigorous_minutes_weekly': 75,
                        'balance_activities': '3+ days/week'
                    },
                    'general': {
                        'moderate_minutes_weekly': 150,
                        'vigorous_minutes_weekly': 75
                    }
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2020, 11, 25),
                url='https://www.who.int/news-room/fact-sheets/detail/physical-activity',
                notes='Based on global health research'
            ),
            MedicalGuideline(
                category=InsightCategory.ACTIVITY,
                metric_type='daily_steps',
                source='ACSM',
                guideline_name='Daily Step Recommendations',
                recommendations={
                    'sedentary_baseline': {'steps': 5000, 'classification': 'low active'},
                    'general_health': {'steps': 7500, 'classification': 'somewhat active'},
                    'active': {'steps': 10000, 'classification': 'active'},
                    'highly_active': {'steps': 12500, 'classification': 'highly active'},
                    'general': {'steps': 8000, 'minimum': 7000}
                },
                evidence_strength=EvidenceLevel.MODERATE,
                last_updated=datetime(2022, 8, 10),
                notes='Step counts correlate with reduced mortality risk'
            ),
            MedicalGuideline(
                category=InsightCategory.ACTIVITY,
                metric_type='strength_training',
                source='ACSM',
                guideline_name='Resistance Training Guidelines',
                recommendations={
                    'general': {
                        'days_per_week': 2,
                        'muscle_groups': 'all major muscle groups',
                        'sets': '2-3',
                        'reps': '8-12'
                    }
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2021, 3, 1),
                notes='Essential for maintaining muscle mass and bone density'
            )
        ]
        
        # Heart Health Guidelines
        self.guidelines['heart_health'] = [
            MedicalGuideline(
                category=InsightCategory.HEART_HEALTH,
                metric_type='resting_heart_rate',
                source='AHA',
                guideline_name='Resting Heart Rate Ranges',
                recommendations={
                    'athlete': {'bpm_range': [40, 60]},
                    'excellent': {'bpm_range': [60, 65]},
                    'good': {'bpm_range': [65, 70]},
                    'average': {'bpm_range': [70, 75]},
                    'below_average': {'bpm_range': [75, 85]},
                    'general': {'normal_range': [60, 100], 'optimal_range': [60, 70]}
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2023, 2, 1),
                notes='Lower resting heart rate generally indicates better fitness'
            ),
            MedicalGuideline(
                category=InsightCategory.HEART_HEALTH,
                metric_type='heart_rate_zones',
                source='ACSM',
                guideline_name='Target Heart Rate Zones',
                recommendations={
                    'moderate_intensity': {'percent_max_hr': [50, 70]},
                    'vigorous_intensity': {'percent_max_hr': [70, 85]},
                    'max_hr_formula': '220 - age',
                    'general': {'training_zone': [50, 85]}
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2022, 5, 15),
                notes='Heart rate zones guide exercise intensity'
            )
        ]
        
        # Recovery Guidelines
        self.guidelines['recovery'] = [
            MedicalGuideline(
                category=InsightCategory.RECOVERY,
                metric_type='hrv_trends',
                source='Sports Science',
                guideline_name='Heart Rate Variability Recovery Indicators',
                recommendations={
                    'general': {
                        'increasing_trend': 'good recovery',
                        'decreasing_trend': 'potential overtraining',
                        'day_to_day_variation': 'normal up to 20%'
                    }
                },
                evidence_strength=EvidenceLevel.MODERATE,
                last_updated=datetime(2023, 1, 20),
                notes='HRV is individual; trends matter more than absolute values'
            )
        ]
        
        # Body Metrics Guidelines
        self.guidelines['body_metrics'] = [
            MedicalGuideline(
                category=InsightCategory.BODY_METRICS,
                metric_type='bmi',
                source='WHO',
                guideline_name='Body Mass Index Classification',
                recommendations={
                    'underweight': {'range': [0, 18.5]},
                    'normal': {'range': [18.5, 24.9]},
                    'overweight': {'range': [25, 29.9]},
                    'obese_class_1': {'range': [30, 34.9]},
                    'obese_class_2': {'range': [35, 39.9]},
                    'obese_class_3': {'range': [40, float('inf')]},
                    'general': {'healthy_range': [18.5, 24.9]}
                },
                evidence_strength=EvidenceLevel.STRONG,
                last_updated=datetime(2022, 6, 1),
                url='https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight',
                notes='BMI has limitations; consider body composition'
            )
        ]
    
    def get_evidence(self, category: str, metric_type: Optional[str] = None) -> List[MedicalGuideline]:
        """Retrieve evidence for a specific category and optionally metric type."""
        guidelines = self.guidelines.get(category, [])
        
        if metric_type:
            guidelines = [g for g in guidelines if g.metric_type == metric_type]
        
        return guidelines
    
    def get_evidence_for_insight(self, category: InsightCategory, 
                                metric_type: str) -> Optional[InsightEvidence]:
        """Get the most relevant evidence for a specific insight."""
        guidelines = self.get_evidence(category.value, metric_type)
        
        if not guidelines:
            return None
        
        # Return the highest quality evidence
        best_guideline = max(guidelines, 
                           key=lambda g: (g.evidence_strength.value, g.last_updated))
        
        return InsightEvidence(
            source_type='guideline',
            source_name=f"{best_guideline.source} {best_guideline.guideline_name}",
            evidence_quality=best_guideline.evidence_strength.value,
            relevance_score=1.0,  # Direct guideline match
            citation=best_guideline.guideline_name,
            url=best_guideline.url,
            key_findings=[str(best_guideline.recommendations)]
        )
    
    def search_evidence(self, query: str) -> List[MedicalGuideline]:
        """Search for evidence across all guidelines."""
        results = []
        query_lower = query.lower()
        
        for category_guidelines in self.guidelines.values():
            for guideline in category_guidelines:
                if (query_lower in guideline.guideline_name.lower() or
                    query_lower in guideline.source.lower() or
                    query_lower in guideline.metric_type.lower() or
                    (guideline.notes and query_lower in guideline.notes.lower())):
                    results.append(guideline)
        
        return results
    
    def get_recommendation_value(self, category: InsightCategory, 
                               metric_type: str,
                               user_demographics: Optional[Dict[str, Any]] = None,
                               recommendation_key: str = 'general') -> Optional[Dict[str, Any]]:
        """Get specific recommendation values for a metric."""
        guidelines = self.get_evidence(category.value, metric_type)
        
        if not guidelines:
            return None
        
        # Get the most authoritative guideline
        guideline = guidelines[0]
        
        if user_demographics:
            recommendation = guideline.get_recommendation_for_user(user_demographics)
            if recommendation:
                return recommendation
        
        return guideline.recommendations.get(recommendation_key)