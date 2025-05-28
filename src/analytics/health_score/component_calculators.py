"""Component calculators for health score calculation."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from collections import Counter

from .health_score_models import HealthData, ComponentScore


class ActivityConsistencyCalculator:
    """Calculate activity consistency score."""
    
    def calculate(self, data: HealthData, date_range: Tuple[date, date]) -> ComponentScore:
        """Calculate activity consistency score (0-100)."""
        start_date, end_date = date_range
        current = start_date
        
        scores = {
            'daily_goals': self.score_daily_goals(data, date_range),
            'exercise_minutes': self.score_exercise_minutes(data, date_range),
            'streak_length': self.score_activity_streaks(data, date_range),
            'variety': self.score_activity_variety(data, date_range),
            'intensity': self.score_intensity_distribution(data, date_range)
        }
        
        weights = {
            'daily_goals': 0.30,
            'exercise_minutes': 0.25,
            'streak_length': 0.20,
            'variety': 0.15,
            'intensity': 0.10
        }
        
        # Calculate weighted score
        total_score = sum(scores[k] * weights[k] for k in scores)
        
        # Calculate confidence based on data availability
        data_days = sum(1 for d in self._date_range(start_date, end_date) 
                       if data.has_data(d))
        total_days = (end_date - start_date).days + 1
        confidence = data_days / total_days if total_days > 0 else 0
        
        # Generate insights
        insights = self._generate_insights(scores, data, date_range)
        
        return ComponentScore(
            component='activity',
            score=total_score,
            weight=0.40,  # Default weight
            breakdown=scores,
            insights=insights,
            confidence=confidence
        )
    
    def score_daily_goals(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on daily goal achievement."""
        start_date, end_date = date_range
        goals_met = 0
        total_days = 0
        
        for current_date in self._date_range(start_date, end_date):
            if data.has_data(current_date):
                total_days += 1
                steps = data.get_steps(current_date)
                goal = data.get_step_goal(current_date)
                if steps and steps >= goal:
                    goals_met += 1
        
        if total_days == 0:
            return 0
        
        percentage = (goals_met / total_days) * 100
        
        # Non-linear scoring curve
        if percentage >= 90:
            return 100
        elif percentage >= 70:
            return 80 + (percentage - 70) * 0.67
        elif percentage >= 50:
            return 60 + (percentage - 50) * 1.0
        else:
            return percentage * 1.2
    
    def score_exercise_minutes(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on exercise minutes."""
        start_date, end_date = date_range
        exercise_days = []
        
        for current_date in self._date_range(start_date, end_date):
            if data.has_data(current_date):
                minutes = data.get_exercise_minutes(current_date)
                if minutes is not None:
                    exercise_days.append(minutes)
        
        if not exercise_days:
            return 0
        
        avg_minutes = np.mean(exercise_days)
        
        # WHO recommends 150 minutes moderate or 75 minutes vigorous per week
        # That's about 21 minutes per day
        target_daily = 21
        
        if avg_minutes >= target_daily * 1.5:  # 31.5 minutes
            return 100
        elif avg_minutes >= target_daily:  # 21 minutes
            return 85 + (avg_minutes - target_daily) / (target_daily * 0.5) * 15
        elif avg_minutes >= target_daily * 0.5:  # 10.5 minutes
            return 50 + (avg_minutes - target_daily * 0.5) / (target_daily * 0.5) * 35
        else:
            return (avg_minutes / (target_daily * 0.5)) * 50
    
    def score_activity_streaks(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on consecutive active days."""
        start_date, end_date = date_range
        streaks = []
        current_streak = 0
        
        for current_date in self._date_range(start_date, end_date):
            if data.has_data(current_date):
                steps = data.get_steps(current_date)
                goal = data.get_step_goal(current_date)
                
                if steps and steps >= goal * 0.8:  # 80% of goal counts
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streaks.append(current_streak)
                    current_streak = 0
        
        if current_streak > 0:
            streaks.append(current_streak)
        
        if not streaks:
            return 0
        
        max_streak = max(streaks)
        avg_streak = np.mean(streaks)
        
        # Score based on longest streak and average
        if max_streak >= 14:  # 2 weeks
            streak_score = 100
        elif max_streak >= 7:  # 1 week
            streak_score = 70 + (max_streak - 7) / 7 * 30
        else:
            streak_score = max_streak / 7 * 70
        
        # Adjust for average streak length
        avg_factor = min(avg_streak / 5, 1.0)  # 5 days is good average
        
        return streak_score * 0.7 + avg_factor * 30
    
    def score_activity_variety(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on variety of activities."""
        # This would need activity type data from the health export
        # For now, return a default score
        return 70
    
    def score_intensity_distribution(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on intensity distribution."""
        # This would analyze heart rate zones during activities
        # For now, return a default score
        return 75
    
    def _date_range(self, start: date, end: date):
        """Generate dates in range."""
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    
    def _generate_insights(self, scores: Dict[str, float], data: HealthData, 
                          date_range: Tuple[date, date]) -> List[str]:
        """Generate insights based on scores."""
        insights = []
        
        if scores['daily_goals'] < 60:
            insights.append("Try to meet your daily step goal more consistently")
        elif scores['daily_goals'] > 90:
            insights.append("Excellent consistency meeting daily goals!")
        
        if scores['exercise_minutes'] < 50:
            insights.append("Aim for at least 150 minutes of moderate exercise per week")
        
        if scores['streak_length'] < 50:
            insights.append("Build longer activity streaks for better consistency")
        
        return insights


class SleepQualityCalculator:
    """Calculate sleep quality score."""
    
    def calculate(self, data: HealthData, date_range: Tuple[date, date]) -> ComponentScore:
        """Calculate sleep quality score (0-100)."""
        components = {
            'duration': self.score_sleep_duration(data, date_range),
            'efficiency': self.score_sleep_efficiency(data, date_range),
            'consistency': self.score_sleep_consistency(data, date_range),
            'deep_sleep': self.score_deep_sleep(data, date_range),
            'interruptions': self.score_interruptions(data, date_range)
        }
        
        weights = {
            'duration': 0.30,
            'efficiency': 0.25,
            'consistency': 0.20,
            'deep_sleep': 0.15,
            'interruptions': 0.10
        }
        
        total_score = sum(components[k] * weights[k] for k in components)
        
        # Calculate confidence
        start_date, end_date = date_range
        data_days = sum(1 for d in self._date_range(start_date, end_date) 
                       if data.get_sleep_duration(d) is not None)
        total_days = (end_date - start_date).days + 1
        confidence = data_days / total_days if total_days > 0 else 0
        
        insights = self._generate_insights(components, data, date_range)
        
        return ComponentScore(
            component='sleep',
            score=total_score,
            weight=0.30,
            breakdown=components,
            insights=insights,
            confidence=confidence
        )
    
    def score_sleep_duration(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on sleep duration vs recommended."""
        age = data.user_profile.age
        recommended = self.get_recommended_sleep_hours(age)
        
        durations = []
        start_date, end_date = date_range
        
        for current_date in self._date_range(start_date, end_date):
            duration = data.get_sleep_duration(current_date)
            if duration is not None:
                durations.append(duration)
        
        if not durations:
            return 0
        
        avg_duration = np.mean(durations)
        
        # Score based on deviation from recommended
        deviation = abs(avg_duration - recommended)
        
        if deviation <= 0.5:
            return 100
        elif deviation <= 1.0:
            return 90
        elif deviation <= 1.5:
            return 70
        else:
            return max(0, 100 - deviation * 20)
    
    def score_sleep_efficiency(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on sleep efficiency (time asleep vs time in bed)."""
        # Would need time in bed vs actual sleep time
        # For now, return default
        return 80
    
    def score_sleep_consistency(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on consistency of sleep schedule."""
        durations = []
        start_date, end_date = date_range
        
        for current_date in self._date_range(start_date, end_date):
            duration = data.get_sleep_duration(current_date)
            if duration is not None:
                durations.append(duration)
        
        if len(durations) < 2:
            return 0
        
        # Calculate standard deviation
        std_dev = np.std(durations)
        
        # Lower std dev is better (more consistent)
        if std_dev <= 0.5:
            return 100
        elif std_dev <= 1.0:
            return 85
        elif std_dev <= 1.5:
            return 70
        else:
            return max(0, 100 - std_dev * 30)
    
    def score_deep_sleep(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on deep sleep percentage."""
        # Would need sleep phase data
        return 75
    
    def score_interruptions(self, data: HealthData, date_range: Tuple[date, date]) -> float:
        """Score based on sleep interruptions."""
        # Would need interruption data
        return 85
    
    def get_recommended_sleep_hours(self, age: int) -> float:
        """Get recommended sleep hours by age."""
        if age < 1:
            return 14
        elif age <= 2:
            return 13
        elif age <= 5:
            return 11
        elif age <= 13:
            return 10
        elif age <= 17:
            return 9
        elif age <= 25:
            return 8
        elif age <= 64:
            return 7.5
        else:
            return 7
    
    def _date_range(self, start: date, end: date):
        """Generate dates in range."""
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    
    def _generate_insights(self, scores: Dict[str, float], data: HealthData, 
                          date_range: Tuple[date, date]) -> List[str]:
        """Generate sleep insights."""
        insights = []
        
        if scores['duration'] < 70:
            age = data.user_profile.age
            recommended = self.get_recommended_sleep_hours(age)
            insights.append(f"Aim for {recommended:.1f} hours of sleep per night")
        
        if scores['consistency'] < 70:
            insights.append("Try to maintain a more consistent sleep schedule")
        
        return insights


class HeartHealthCalculator:
    """Calculate heart health score."""
    
    def calculate(self, data: HealthData, date_range: Tuple[date, date]) -> ComponentScore:
        """Calculate heart health score (0-100)."""
        components = {
            'resting_hr': self.score_resting_heart_rate(data, date_range),
            'hrv': self.score_heart_rate_variability(data, date_range),
            'recovery': self.score_recovery_rate(data, date_range),
            'fitness': self.score_cardio_fitness(data, date_range),
            'blood_pressure': self.score_blood_pressure(data, date_range)
        }
        
        weights = {
            'resting_hr': 0.25,
            'hrv': 0.25,
            'recovery': 0.20,
            'fitness': 0.20,
            'blood_pressure': 0.10
        }
        
        # Calculate weighted score, handling missing data
        total_weight = 0
        total_score = 0
        
        for component, score in components.items():
            if score is not None:
                total_score += score * weights[component]
                total_weight += weights[component]
        
        if total_weight > 0:
            final_score = total_score / total_weight * 100
        else:
            final_score = 0
        
        # Calculate confidence
        available_components = sum(1 for s in components.values() if s is not None)
        confidence = available_components / len(components)
        
        insights = self._generate_insights(components, data, date_range)
        
        return ComponentScore(
            component='heart',
            score=final_score,
            weight=0.20,
            breakdown={k: v for k, v in components.items() if v is not None},
            insights=insights,
            confidence=confidence
        )
    
    def score_resting_heart_rate(self, data: HealthData, date_range: Tuple[date, date]) -> Optional[float]:
        """Score based on resting heart rate."""
        rates = []
        start_date, end_date = date_range
        
        for current_date in self._date_range(start_date, end_date):
            hr = data.get_heart_rate_resting(current_date)
            if hr is not None:
                rates.append(hr)
        
        if not rates:
            return None
        
        avg_hr = np.mean(rates)
        age = data.user_profile.age
        
        # Age-adjusted scoring
        if age < 30:
            if avg_hr < 60:
                return 100
            elif avg_hr < 70:
                return 85
            elif avg_hr < 80:
                return 70
            else:
                return max(0, 150 - avg_hr)
        else:
            # Adjust expectations for older adults
            if avg_hr < 65:
                return 100
            elif avg_hr < 75:
                return 85
            elif avg_hr < 85:
                return 70
            else:
                return max(0, 155 - avg_hr)
    
    def score_heart_rate_variability(self, data: HealthData, date_range: Tuple[date, date]) -> Optional[float]:
        """Score based on HRV."""
        hrvs = []
        start_date, end_date = date_range
        
        for current_date in self._date_range(start_date, end_date):
            hrv = data.get_hrv(current_date)
            if hrv is not None:
                hrvs.append(hrv)
        
        if not hrvs:
            return None
        
        avg_hrv = np.mean(hrvs)
        
        # Higher HRV is generally better
        if avg_hrv >= 60:
            return 100
        elif avg_hrv >= 50:
            return 85
        elif avg_hrv >= 40:
            return 70
        elif avg_hrv >= 30:
            return 55
        else:
            return avg_hrv / 30 * 55
    
    def score_recovery_rate(self, data: HealthData, date_range: Tuple[date, date]) -> Optional[float]:
        """Score based on heart rate recovery after exercise."""
        # Would need post-exercise heart rate data
        return None
    
    def score_cardio_fitness(self, data: HealthData, date_range: Tuple[date, date]) -> Optional[float]:
        """Score based on VO2 max or similar fitness metric."""
        # Would need VO2 max data
        return None
    
    def score_blood_pressure(self, data: HealthData, date_range: Tuple[date, date]) -> Optional[float]:
        """Score based on blood pressure if available."""
        # Would need blood pressure data
        return None
    
    def _date_range(self, start: date, end: date):
        """Generate dates in range."""
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    
    def _generate_insights(self, scores: Dict[str, Optional[float]], data: HealthData, 
                          date_range: Tuple[date, date]) -> List[str]:
        """Generate heart health insights."""
        insights = []
        
        if scores.get('resting_hr') and scores['resting_hr'] < 70:
            insights.append("Your resting heart rate is higher than optimal")
        
        if scores.get('hrv') and scores['hrv'] < 60:
            insights.append("Consider stress reduction techniques to improve HRV")
        
        return insights


class OtherMetricsCalculator:
    """Calculate score for other health metrics."""
    
    def calculate(self, data: HealthData, date_range: Tuple[date, date]) -> ComponentScore:
        """Calculate other metrics score (0-100)."""
        # Placeholder implementation
        # Would include nutrition, hydration, stress, mindfulness, etc.
        
        return ComponentScore(
            component='other',
            score=75,
            weight=0.10,
            breakdown={
                'nutrition': 70,
                'hydration': 80,
                'stress': 75,
                'mindfulness': 75
            },
            insights=["Track nutrition and hydration for more accurate health scoring"],
            confidence=0.5  # Lower confidence for estimated data
        )