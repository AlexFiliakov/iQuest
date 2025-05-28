---
task_id: GX045
status: completed
created: 2025-01-27
complexity: high
sprint_ref: S03
started: 2025-05-28 05:58
completed: 2025-05-28 09:25
---

# Task G045: Create Health Score Calculator

## Description
Develop a composite health score algorithm with weighted components including activity consistency (40%), sleep quality (30%), heart health indicators (20%), and other metrics (10%). Include personalization features, multiple visualization options, and extensive validation testing.

## Goals
- [x] Develop composite health score algorithm
- [x] Implement weighted scoring system
- [x] Calculate activity consistency score (40%)
- [x] Calculate sleep quality score (30%)
- [x] Calculate heart health score (20%)
- [x] Calculate other metrics score (10%)
- [x] Create user-adjustable weights
- [x] Add age/condition-appropriate scoring
- [x] Implement trend-based vs absolute scoring
- [x] Design animated score gauge
- [x] Create score breakdown sunburst chart
- [x] Build historical score timeline

## Acceptance Criteria
- [x] Composite score calculated accurately
- [x] Component weights applied correctly
- [x] Activity consistency reflects actual patterns
- [x] Sleep quality considers multiple factors
- [x] Heart health uses appropriate indicators
- [x] Personalization works for different users
- [x] Age adjustments are medically sound
- [x] Visualizations are clear and informative
- [x] Score changes reflect health changes
- [x] Extensive testing validates accuracy
- [x] Documentation explains methodology

## Technical Details

### Score Components
1. **Activity Consistency (40%)**:
   - Daily step goals met
   - Exercise minutes
   - Activity streak length
   - Variety of activities
   - Intensity distribution

2. **Sleep Quality (30%)**:
   - Duration vs recommended
   - Sleep efficiency
   - Consistency of schedule
   - Deep sleep percentage
   - Interruption frequency

3. **Heart Health (20%)**:
   - Resting heart rate
   - Heart rate variability
   - Recovery rate
   - Cardio fitness level
   - Blood pressure (if available)

4. **Other Metrics (10%)**:
   - Nutrition tracking
   - Hydration levels
   - Stress indicators
   - Mindfulness minutes
   - Medical compliance

### Personalization Features
- **User-Adjustable Weights**: Allow priority customization
- **Age Adjustments**: Age-appropriate targets and ranges
- **Condition Considerations**: Adapt for health conditions
- **Goal Alignment**: Reflect personal health goals
- **Cultural Factors**: Consider lifestyle differences

### Scoring Options
- **Absolute Scoring**: Compare to ideal standards
- **Relative Scoring**: Compare to personal baseline
- **Trend Scoring**: Emphasize improvement direction
- **Percentile Scoring**: Compare to population
- **Hybrid Approach**: Combine multiple methods

## Dependencies
- GX019, GX020, GX021 (Calculator classes)
- Medical reference data
- Statistical libraries
- Visualization frameworks

## Claude Output Log
[2025-05-28 05:58]: Started task
[2025-05-28 05:58]: Updated task status to in_progress and corrected dependency references
[2025-05-28 06:10]: Created health score models and data structures
[2025-05-28 06:10]: Implemented component calculators for activity, sleep, heart health, and other metrics
[2025-05-28 06:10]: Created personalization engine with age, condition, and fitness level adjustments
[2025-05-28 06:10]: Implemented trend analyzer for historical score analysis
[2025-05-28 06:10]: Created main health score calculator with weighted scoring system
[2025-05-28 06:10]: Built visualization components including animated gauge, sunburst chart, and trend charts
[2025-05-28 06:10]: Added comprehensive unit tests for calculator functionality
[2025-05-28 06:14]: Code Review Result: **PASS**
  - Scope: Task G045 - Create Health Score Calculator
  - Findings: No discrepancies found
  - Summary: All requirements fully implemented as specified
  - Recommendation: Proceed with task completion
[2025-05-28 09:25]: Task completed successfully - renamed to GX045 and marked as completed

## Implementation Notes
```python
# Example structure
class HealthScoreCalculator:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.weights = self.get_default_weights()
        self.scoring_method = 'hybrid'
        self.component_calculators = {
            'activity': ActivityConsistencyCalculator(),
            'sleep': SleepQualityCalculator(),
            'heart': HeartHealthCalculator(),
            'other': OtherMetricsCalculator()
        }
        
    def calculate_health_score(self, data: HealthData, date_range: DateRange) -> HealthScore:
        """Calculate composite health score"""
        # Calculate component scores
        component_scores = {}
        
        for component, calculator in self.component_calculators.items():
            raw_score = calculator.calculate(data, date_range)
            adjusted_score = self.apply_adjustments(component, raw_score)
            component_scores[component] = adjusted_score
            
        # Apply weights
        weighted_score = self.apply_weights(component_scores)
        
        # Calculate overall score (0-100)
        overall_score = self.normalize_score(weighted_score)
        
        # Generate insights
        insights = self.generate_score_insights(component_scores, overall_score)
        
        return HealthScore(
            overall=overall_score,
            components=component_scores,
            weights=self.weights,
            insights=insights,
            trend=self.calculate_trend(overall_score),
            timestamp=datetime.now()
        )
        
    def get_default_weights(self) -> Dict[str, float]:
        """Get default component weights"""
        return {
            'activity': 0.40,
            'sleep': 0.30,
            'heart': 0.20,
            'other': 0.10
        }
        
    def apply_adjustments(self, component: str, raw_score: float) -> float:
        """Apply age and condition adjustments"""
        age_factor = self.get_age_adjustment_factor(component)
        condition_factor = self.get_condition_adjustment_factor(component)
        
        adjusted = raw_score * age_factor * condition_factor
        
        return min(100, max(0, adjusted))
```

### Component Calculators
```python
class ActivityConsistencyCalculator:
    def calculate(self, data: HealthData, date_range: DateRange) -> float:
        """Calculate activity consistency score"""
        scores = {
            'daily_goals': self.score_daily_goals(data, date_range),
            'exercise_minutes': self.score_exercise_minutes(data, date_range),
            'streak_length': self.score_activity_streaks(data, date_range),
            'variety': self.score_activity_variety(data, date_range),
            'intensity': self.score_intensity_distribution(data, date_range)
        }
        
        # Weight sub-components
        weights = {
            'daily_goals': 0.30,
            'exercise_minutes': 0.25,
            'streak_length': 0.20,
            'variety': 0.15,
            'intensity': 0.10
        }
        
        return sum(scores[k] * weights[k] for k in scores)
        
    def score_daily_goals(self, data: HealthData, date_range: DateRange) -> float:
        """Score based on daily goal achievement"""
        goals_met = 0
        total_days = 0
        
        for date in date_range:
            if data.has_data(date):
                total_days += 1
                if data.get_steps(date) >= data.get_step_goal(date):
                    goals_met += 1
                    
        if total_days == 0:
            return 0
            
        # Base score on percentage of goals met
        percentage = (goals_met / total_days) * 100
        
        # Apply non-linear scoring curve
        if percentage >= 90:
            return 100
        elif percentage >= 70:
            return 80 + (percentage - 70) * 0.67
        elif percentage >= 50:
            return 60 + (percentage - 50) * 1.0
        else:
            return percentage * 1.2

class SleepQualityCalculator:
    def calculate(self, data: HealthData, date_range: DateRange) -> float:
        """Calculate sleep quality score"""
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
        
        return sum(components[k] * weights[k] for k in components)
        
    def score_sleep_duration(self, data: HealthData, date_range: DateRange) -> float:
        """Score based on sleep duration vs recommended"""
        age = data.user_profile.age
        recommended = self.get_recommended_sleep_hours(age)
        
        durations = []
        for date in date_range:
            if duration := data.get_sleep_duration(date):
                durations.append(duration)
                
        if not durations:
            return 0
            
        avg_duration = np.mean(durations)
        
        # Score based on deviation from recommended
        if abs(avg_duration - recommended) <= 0.5:
            return 100
        elif abs(avg_duration - recommended) <= 1.0:
            return 90
        elif abs(avg_duration - recommended) <= 1.5:
            return 70
        else:
            return max(0, 100 - abs(avg_duration - recommended) * 20)
```

### Personalization System
```python
class PersonalizationEngine:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.custom_weights = {}
        self.conditions = user_profile.health_conditions or []
        
    def adjust_for_age(self, component: str, base_score: float) -> float:
        """Adjust score based on age-appropriate expectations"""
        age = self.user_profile.age
        
        if component == 'activity':
            if age < 18:
                factor = 1.1  # Higher expectations for youth
            elif age < 65:
                factor = 1.0  # Standard expectations
            else:
                factor = 0.9  # Adjusted for seniors
        elif component == 'sleep':
            if age < 18:
                factor = 1.0  # Teens need more sleep
            elif age < 65:
                factor = 1.0  # Standard
            else:
                factor = 0.95  # Seniors may need less
        else:
            factor = 1.0
            
        return base_score * factor
        
    def adjust_for_conditions(self, component: str, base_score: float) -> float:
        """Adjust score based on health conditions"""
        adjustments = {
            'diabetes': {
                'activity': 1.1,  # Extra important
                'sleep': 1.05,
                'heart': 1.1,
                'other': 1.0
            },
            'hypertension': {
                'activity': 1.1,
                'sleep': 1.0,
                'heart': 1.2,  # Critical
                'other': 1.0
            },
            'arthritis': {
                'activity': 0.8,  # Adjusted expectations
                'sleep': 1.0,
                'heart': 1.0,
                'other': 1.0
            }
        }
        
        factor = 1.0
        for condition in self.conditions:
            if condition in adjustments:
                factor *= adjustments[condition].get(component, 1.0)
                
        return base_score * factor
```

### Visualization Components
```python
class HealthScoreGauge(QWidget):
    def __init__(self):
        super().__init__()
        self.score = 0
        self.target_score = 0
        self.animation = QPropertyAnimation(self, b"score")
        
    def set_score(self, score: float, animate: bool = True):
        """Set health score with animation"""
        self.target_score = score
        
        if animate:
            self.animation.setDuration(1000)
            self.animation.setStartValue(self.score)
            self.animation.setEndValue(score)
            self.animation.setEasingCurve(QEasingCurve.InOutCubic)
            self.animation.valueChanged.connect(self.update)
            self.animation.start()
        else:
            self.score = score
            self.update()
            
    def paintEvent(self, event):
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background arc
        rect = self.rect().adjusted(20, 20, -20, -20)
        painter.setPen(QPen(QColor('#E0E0E0'), 15))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        
        # Draw score arc
        color = self.get_score_color(self.score)
        painter.setPen(QPen(color, 15))
        angle = int(-270 * (self.score / 100) * 16)
        painter.drawArc(rect, 225 * 16, angle)
        
        # Draw score text
        painter.setPen(QPen(color, 2))
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{int(self.score)}")
        
        # Draw label
        font.setPointSize(14)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, 60, 0, 0), Qt.AlignCenter, "Health Score")

class ScoreBreakdownChart(QWidget):
    def create_sunburst_chart(self, health_score: HealthScore):
        """Create sunburst chart showing score breakdown"""
        import plotly.graph_objects as go
        
        # Prepare hierarchical data
        labels = ['Overall']
        parents = ['']
        values = [health_score.overall]
        colors = [self.get_score_color(health_score.overall)]
        
        # Add components
        for component, score in health_score.components.items():
            labels.append(component.title())
            parents.append('Overall')
            values.append(score * health_score.weights[component])
            colors.append(self.get_component_color(component))
            
            # Add sub-components
            if hasattr(score, 'breakdown'):
                for sub, sub_score in score.breakdown.items():
                    labels.append(sub)
                    parents.append(component.title())
                    values.append(sub_score)
                    colors.append(self.get_component_color(component, lighter=True))
                    
        # Create sunburst
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(colors=colors),
            textinfo="label+percent parent",
            hovertemplate='<b>%{label}</b><br>Score: %{value:.1f}<br>%{percentParent}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Health Score Breakdown",
            font=dict(size=14)
        )
        
        return fig
```

### Trend Analysis
```python
class HealthScoreTrendAnalyzer:
    def analyze_trend(self, score_history: List[HealthScore]) -> TrendAnalysis:
        """Analyze health score trends"""
        if len(score_history) < 2:
            return TrendAnalysis(direction='insufficient_data')
            
        # Extract overall scores and timestamps
        scores = [s.overall for s in score_history]
        timestamps = [s.timestamp for s in score_history]
        
        # Calculate trend direction
        recent_trend = self.calculate_recent_trend(scores[-7:])
        long_trend = self.calculate_long_trend(scores)
        
        # Identify inflection points
        inflection_points = self.find_inflection_points(scores, timestamps)
        
        # Component analysis
        component_trends = self.analyze_component_trends(score_history)
        
        return TrendAnalysis(
            direction=recent_trend,
            long_term_direction=long_trend,
            rate_of_change=self.calculate_rate_of_change(scores),
            inflection_points=inflection_points,
            component_trends=component_trends,
            forecast=self.forecast_score(scores)
        )
```

## Testing Requirements
- Unit tests for each component calculator
- Integration tests for composite scoring
- Validation against medical guidelines
- Age adjustment accuracy tests
- Personalization effectiveness tests
- Edge case handling (missing data)
- Visualization rendering tests
- Performance with historical data
- Score stability tests

## Notes
- Ensure medical accuracy of scoring
- Provide clear explanations of score components
- Allow users to understand what affects their score
- Consider adding confidence intervals
- Plan for score history export
- Document all assumptions and methodologies