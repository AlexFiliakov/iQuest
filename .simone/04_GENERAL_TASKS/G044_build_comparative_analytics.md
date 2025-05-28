---
task_id: G044
status: open
created: 2025-01-27
complexity: medium
sprint_ref: S03
---

# Task G044: Build Comparative Analytics

## Description
Compare user metrics to personal historical averages, age/gender demographics (if available), seasonal/weather norms, and user-defined peer groups. Implement privacy-first design with opt-in comparisons, anonymous aggregation, and local processing where possible.

## Goals
- [ ] Compare to personal historical averages
- [ ] Implement age/gender demographic comparisons
- [ ] Add seasonal/weather norm comparisons
- [ ] Create user-defined peer group comparisons
- [ ] Build privacy-first architecture
- [ ] Implement opt-in consent system
- [ ] Use anonymous aggregation only
- [ ] Process locally when possible
- [ ] Generate percentile rankings with context
- [ ] Create respectful comparison visualizations

## Acceptance Criteria
- [ ] Personal average comparisons work correctly
- [ ] Demographic comparisons respect privacy
- [ ] Seasonal comparisons use appropriate baselines
- [ ] Peer groups maintain anonymity
- [ ] All comparisons are opt-in
- [ ] No personal data leaves device without consent
- [ ] Anonymous aggregation preserves privacy
- [ ] Local processing used where feasible
- [ ] Insights are constructive and respectful
- [ ] Visual design avoids negative comparisons

## Technical Details

### Comparison Types
1. **Personal Historical**:
   - Rolling averages (7, 30, 90, 365 days)
   - Same period last year
   - Personal best/worst periods
   - Trend comparisons

2. **Demographic Comparisons**:
   - Age brackets (5-year ranges)
   - Gender categories (optional)
   - Activity level cohorts
   - Health condition groups

3. **Seasonal/Weather**:
   - Monthly baselines
   - Weather-adjusted norms
   - Daylight hour correlations
   - Regional variations

4. **Peer Groups**:
   - Friend circles (invited only)
   - Challenge groups
   - Anonymous cohorts
   - Professional teams

### Privacy-First Design
- **Opt-in Everything**:
  - Explicit consent for each comparison
  - Granular privacy controls
  - Easy opt-out mechanisms
  - Clear data usage explanations

- **Anonymous Aggregation**:
  - K-anonymity (minimum group size)
  - Differential privacy
  - No individual identification
  - Aggregate statistics only

- **Local Processing**:
  - On-device calculations
  - Federated learning approach
  - Minimal server communication
  - Encrypted when transmitted

### Insights Engine
- **Constructive Messaging**:
  - Focus on personal progress
  - Celebrate improvements
  - Gentle suggestions
  - Avoid shame/guilt

- **Contextual Information**:
  - Why differences exist
  - Factors affecting metrics
  - Actionable insights
  - Educational content

## Dependencies
- G019, G020, G021 (Calculator classes)
- Privacy/encryption libraries
- Weather API (optional)
- Federated learning framework

## Implementation Notes
```python
# Example structure
class ComparativeAnalytics:
    def __init__(self, privacy_manager: PrivacyManager):
        self.privacy = privacy_manager
        self.comparison_engine = ComparisonEngine()
        self.insights_generator = InsightsGenerator()
        self.anonymizer = DataAnonymizer()
        
    def compare_to_historical(self, metric: str, current_period: DateRange) -> Comparison:
        """Compare current period to historical data"""
        # Always allowed - personal data only
        historical_periods = [
            self.get_rolling_average(metric, 30),
            self.get_rolling_average(metric, 90),
            self.get_same_period_last_year(metric, current_period),
            self.get_personal_best_period(metric)
        ]
        
        comparison = Comparison(
            current=self.calculate_current_stats(metric, current_period),
            historical=historical_periods,
            insights=self.generate_historical_insights(metric, current_period, historical_periods)
        )
        
        return comparison
        
    def compare_to_demographics(self, metric: str, demographic_data: Dict) -> Optional[Comparison]:
        """Compare to demographic cohort if permitted"""
        # Check privacy permissions
        if not self.privacy.has_permission('demographic_comparison'):
            return None
            
        # Get anonymous cohort data
        cohort = self.get_demographic_cohort(demographic_data)
        
        if cohort.size < self.privacy.minimum_cohort_size:
            return Comparison(
                error="Insufficient data for comparison",
                reason="Cohort too small to preserve privacy"
            )
            
        # Calculate comparison
        return Comparison(
            user_percentile=cohort.calculate_percentile(metric),
            cohort_stats=cohort.get_anonymous_stats(),
            insights=self.generate_demographic_insights(metric, cohort)
        )
```

### Privacy Manager
```python
class PrivacyManager:
    def __init__(self):
        self.permissions = self.load_permissions()
        self.minimum_cohort_size = 50  # K-anonymity
        self.differential_privacy = DifferentialPrivacy(epsilon=1.0)
        
    def request_permission(self, permission_type: str) -> bool:
        """Request user permission for data comparison"""
        dialog = PrivacyConsentDialog(permission_type)
        dialog.set_explanation(self.get_permission_explanation(permission_type))
        dialog.set_data_usage(self.get_data_usage_details(permission_type))
        
        if dialog.exec():
            self.permissions[permission_type] = {
                'granted': True,
                'timestamp': datetime.now(),
                'scope': dialog.get_selected_scope()
            }
            self.save_permissions()
            return True
            
        return False
        
    def anonymize_data(self, data: pd.DataFrame, method: str = 'k_anonymity') -> pd.DataFrame:
        """Anonymize data before aggregation"""
        if method == 'k_anonymity':
            return self.apply_k_anonymity(data)
        elif method == 'differential_privacy':
            return self.differential_privacy.add_noise(data)
        elif method == 'aggregation':
            return self.aggregate_only(data)
```

### Demographic Comparison
```python
class DemographicComparison:
    def __init__(self, anonymizer: DataAnonymizer):
        self.anonymizer = anonymizer
        self.cohort_manager = CohortManager()
        
    def get_demographic_cohort(self, user_demographics: Dict) -> Cohort:
        """Get appropriate comparison cohort"""
        # Build cohort criteria
        criteria = {
            'age_range': self.get_age_range(user_demographics.get('age')),
            'gender': user_demographics.get('gender') if self.include_gender() else None,
            'activity_level': self.estimate_activity_level()
        }
        
        # Get anonymous cohort stats
        cohort = self.cohort_manager.get_cohort(criteria)
        
        # Ensure privacy
        if cohort.size >= self.minimum_cohort_size:
            return cohort
        else:
            # Broaden criteria to get larger cohort
            return self.broaden_cohort_criteria(criteria)
            
    def calculate_percentile(self, metric: str, value: float, cohort: Cohort) -> PercentileResult:
        """Calculate user's percentile within cohort"""
        # Get distribution
        distribution = cohort.get_metric_distribution(metric)
        
        # Calculate percentile
        percentile = scipy.stats.percentileofscore(distribution, value)
        
        # Add context
        return PercentileResult(
            percentile=percentile,
            interpretation=self.interpret_percentile(percentile),
            comparison_points={
                'median': np.median(distribution),
                '25th': np.percentile(distribution, 25),
                '75th': np.percentile(distribution, 75)
            }
        )
```

### Seasonal/Weather Comparison
```python
class SeasonalComparison:
    def __init__(self, weather_service: Optional[WeatherService] = None):
        self.weather_service = weather_service
        self.seasonal_baselines = self.load_seasonal_baselines()
        
    def compare_to_seasonal_norm(self, metric: str, date: datetime, location: Optional[Location] = None) -> SeasonalComparison:
        """Compare to seasonal norms"""
        month = date.month
        
        # Get baseline for month
        baseline = self.seasonal_baselines.get(metric, {}).get(month)
        
        if not baseline:
            return None
            
        comparison = {
            'seasonal_average': baseline['average'],
            'seasonal_range': (baseline['p25'], baseline['p75']),
            'typical_variation': baseline['std_dev']
        }
        
        # Add weather context if available
        if self.weather_service and location:
            weather_data = self.weather_service.get_historical_weather(date, location)
            comparison['weather_adjusted'] = self.adjust_for_weather(
                metric, baseline, weather_data
            )
            
        return comparison
```

### Peer Group Comparison
```python
class PeerGroupComparison:
    def __init__(self, privacy_manager: PrivacyManager):
        self.privacy = privacy_manager
        self.group_manager = GroupManager()
        
    def create_peer_group(self, group_name: str, invite_codes: List[str]) -> PeerGroup:
        """Create a private peer comparison group"""
        group = PeerGroup(
            name=group_name,
            creator=self.get_current_user(),
            privacy_level='private',
            min_members=5  # Minimum for privacy
        )
        
        # Send invitations
        for code in invite_codes:
            self.send_invitation(group, code)
            
        return group
        
    def compare_to_peer_group(self, metric: str, group: PeerGroup) -> GroupComparison:
        """Compare to peer group with privacy preservation"""
        if group.member_count < group.min_members:
            return GroupComparison(
                error="Group too small for comparison",
                required_members=group.min_members
            )
            
        # Get anonymized group stats
        stats = group.get_anonymous_stats(metric)
        
        # Calculate relative position
        my_value = self.get_my_value(metric)
        
        return GroupComparison(
            group_average=stats['mean'],
            group_range=(stats['min'], stats['max']),
            my_ranking=self.calculate_anonymous_ranking(my_value, group),
            trend_comparison=self.compare_trends(metric, group),
            insights=self.generate_peer_insights(metric, stats)
        )
```

### Respectful Visualization
```python
class ComparativeVisualization(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def create_percentile_gauge(self, percentile: float, context: str) -> QWidget:
        """Create respectful percentile visualization"""
        gauge = PercentileGauge()
        
        # Use encouraging colors
        if percentile >= 75:
            color = '#4CAF50'  # Green - doing great!
        elif percentile >= 50:
            color = '#2196F3'  # Blue - on track
        elif percentile >= 25:
            color = '#FF9800'  # Orange - room to grow
        else:
            color = '#9C27B0'  # Purple - unique journey
            
        gauge.set_value(percentile)
        gauge.set_color(color)
        gauge.set_label(f"{context}")
        
        # Add encouraging message
        message = self.get_encouraging_message(percentile)
        gauge.set_subtitle(message)
        
        return gauge
        
    def get_encouraging_message(self, percentile: float) -> str:
        """Generate encouraging message regardless of percentile"""
        if percentile >= 75:
            return "You're inspiring others! 🌟"
        elif percentile >= 50:
            return "You're on a great path! 💪"
        elif percentile >= 25:
            return "Every step counts! 🚶"
        else:
            return "Your journey is unique! 🌱"
```

### Insights Generator
```python
class InsightsGenerator:
    def generate_insights(self, comparisons: Dict[str, Comparison]) -> List[Insight]:
        """Generate constructive insights from comparisons"""
        insights = []
        
        # Personal progress insights (always positive)
        if 'historical' in comparisons:
            insights.extend(self.generate_progress_insights(comparisons['historical']))
            
        # Demographic insights (if permitted)
        if 'demographic' in comparisons:
            insights.extend(self.generate_demographic_insights(
                comparisons['demographic'],
                focus='opportunities'  # Focus on opportunities, not deficits
            ))
            
        # Seasonal insights
        if 'seasonal' in comparisons:
            insights.extend(self.generate_seasonal_insights(comparisons['seasonal']))
            
        # Peer insights (if in group)
        if 'peer' in comparisons:
            insights.extend(self.generate_peer_insights(
                comparisons['peer'],
                tone='supportive'  # Supportive, not competitive
            ))
            
        # Prioritize and filter insights
        insights = self.prioritize_insights(insights)
        insights = self.filter_negative_insights(insights)
        
        return insights[:5]  # Top 5 most relevant
```

## Testing Requirements
- Unit tests for all comparison types
- Privacy preservation validation
- Anonymization effectiveness tests
- Minimum cohort size enforcement
- Consent flow testing
- Local processing verification
- Visualization tone testing
- Integration tests

## Notes
- Privacy is paramount - when in doubt, don't share
- Focus on personal growth, not competition
- Make all comparisons optional and reversible
- Provide education about what comparisons mean
- Consider cultural sensitivity in messaging
- Plan for offline/local-only mode