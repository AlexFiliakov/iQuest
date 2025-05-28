---
task_id: G047
status: open
created: 2025-01-27
complexity: high
sprint_ref: S03
---

# Task G047: Design Data Story Generator

## Description
Create a narrative insights generator that produces weekly recap stories, monthly journey narratives, year in review summaries, and milestone celebrations. Implement natural language generation with template variations, tone matching, personalized insights, and actionable recommendations.

## Goals
- [ ] Create narrative insights from data
- [ ] Generate weekly recap stories
- [ ] Build monthly journey narratives
- [ ] Create year in review summaries
- [ ] Design milestone celebration stories
- [ ] Implement template-based generation with variations
- [ ] Add tone matching (encouraging, neutral, motivating)
- [ ] Generate personalized insights
- [ ] Provide actionable recommendations
- [ ] Support in-app cards and email summaries
- [ ] Implement user preference learning

## Acceptance Criteria
- [ ] Weekly recaps summarize key achievements
- [ ] Monthly narratives tell cohesive stories
- [ ] Year in review captures major themes
- [ ] Milestones celebrated appropriately
- [ ] Templates produce varied, natural text
- [ ] Tone matches user preferences
- [ ] Insights are personally relevant
- [ ] Recommendations are actionable
- [ ] Delivery methods work correctly
- [ ] User preferences influence generation

## Technical Details

### Story Types
1. **Weekly Recap**:
   - Key achievements
   - Comparison to previous week
   - Standout moments
   - Areas of improvement
   - Next week preview

2. **Monthly Journey**:
   - Overall theme/narrative arc
   - Progress toward goals
   - Habit formation
   - Challenges overcome
   - Personal growth

3. **Year in Review**:
   - Major milestones
   - Transformation story
   - Statistical highlights
   - Best moments
   - Lessons learned

4. **Milestone Celebrations**:
   - Achievement context
   - Journey to milestone
   - Significance explanation
   - Next challenges
   - Encouragement

### Natural Language Generation
- **Template System**:
  - Base templates with variations
  - Dynamic content insertion
  - Grammar handling
  - Sentence variety

- **Tone Matching**:
  - Encouraging: Focus on positives
  - Neutral: Balanced reporting
  - Motivating: Challenge-oriented
  - Celebratory: Achievement focus

- **Personalization**:
  - Name usage preferences
  - Metric priorities
  - Communication style
  - Cultural considerations

- **Recommendations**:
  - Data-driven suggestions
  - Achievable next steps
  - Personalized to goals
  - Clear action items

## Dependencies
- G019, G020, G021 (Calculator classes)
- NLG libraries (spaCy, NLTK)
- Template engines
- Email service integration

## Implementation Notes
```python
# Example structure
class DataStoryGenerator:
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.template_engine = StoryTemplateEngine()
        self.insight_generator = InsightGenerator()
        self.tone_manager = ToneManager(user_profile.preferred_tone)
        self.preference_learner = PreferenceLearner()
        
    def generate_weekly_recap(self, week_data: WeekData) -> Story:
        """Generate weekly recap story"""
        # Analyze week data
        analysis = self.analyze_week(week_data)
        
        # Select narrative structure
        structure = self.select_weekly_structure(analysis)
        
        # Generate story sections
        sections = {
            'opening': self.generate_opening(analysis, 'weekly'),
            'achievements': self.generate_achievements_section(analysis),
            'comparison': self.generate_comparison_section(analysis),
            'insights': self.generate_insights_section(analysis),
            'recommendations': self.generate_recommendations_section(analysis),
            'closing': self.generate_closing(analysis, 'weekly')
        }
        
        # Apply tone
        sections = self.tone_manager.apply_tone(sections)
        
        # Assemble story
        story = self.assemble_story(sections, structure)
        
        # Add metadata
        story.metadata = StoryMetadata(
            type='weekly_recap',
            generated_at=datetime.now(),
            data_period=week_data.period,
            word_count=len(story.text.split())
        )
        
        return story
        
    def analyze_week(self, week_data: WeekData) -> WeekAnalysis:
        """Comprehensive week analysis for story generation"""
        return WeekAnalysis(
            achievements=self.identify_achievements(week_data),
            comparisons=self.compare_to_previous_weeks(week_data),
            patterns=self.identify_patterns(week_data),
            challenges=self.identify_challenges(week_data),
            highlights=self.find_standout_moments(week_data),
            progress=self.assess_goal_progress(week_data)
        )
```

### Template Engine
```python
class StoryTemplateEngine:
    def __init__(self):
        self.templates = self.load_templates()
        self.variations = self.load_variations()
        
    def generate_opening(self, analysis: Analysis, story_type: str) -> str:
        """Generate story opening with variations"""
        templates = self.templates[story_type]['openings']
        
        # Select template based on analysis
        if analysis.is_exceptional_week:
            template_key = 'exceptional'
        elif analysis.shows_improvement:
            template_key = 'improving'
        elif analysis.shows_consistency:
            template_key = 'consistent'
        else:
            template_key = 'standard'
            
        # Get template with variations
        template_options = templates[template_key]
        selected = random.choice(template_options)
        
        # Fill template
        return selected.format(
            name=self.get_user_name(),
            week_summary=analysis.summary_phrase,
            key_metric=analysis.top_achievement.metric,
            improvement_percent=analysis.overall_improvement
        )
        
    def generate_achievements_section(self, analysis: Analysis) -> str:
        """Generate achievements narrative"""
        achievements = analysis.achievements
        
        if not achievements:
            return self.get_no_achievements_message()
            
        # Group achievements by type
        grouped = self.group_achievements(achievements)
        
        sections = []
        for group_type, group_achievements in grouped.items():
            narrative = self.create_achievement_narrative(group_type, group_achievements)
            sections.append(narrative)
            
        return self.connect_sections(sections)
        
    def create_achievement_narrative(self, achievement_type: str, achievements: List[Achievement]) -> str:
        """Create narrative for achievement group"""
        if achievement_type == 'personal_records':
            return self.create_record_narrative(achievements)
        elif achievement_type == 'streaks':
            return self.create_streak_narrative(achievements)
        elif achievement_type == 'goals_met':
            return self.create_goal_narrative(achievements)
        else:
            return self.create_general_achievement_narrative(achievements)
```

### Insight Generation
```python
class InsightGenerator:
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        
    def generate_insights(self, data: Union[WeekData, MonthData, YearData]) -> List[Insight]:
        """Generate personalized insights from data"""
        insights = []
        
        # Pattern-based insights
        patterns = self.pattern_detector.detect_patterns(data)
        for pattern in patterns:
            insight = self.create_pattern_insight(pattern)
            insights.append(insight)
            
        # Correlation insights
        correlations = self.correlation_analyzer.find_correlations(data)
        for correlation in correlations:
            insight = self.create_correlation_insight(correlation)
            insights.append(insight)
            
        # Trend insights
        trends = self.analyze_trends(data)
        for trend in trends:
            insight = self.create_trend_insight(trend)
            insights.append(insight)
            
        # Prioritize and select top insights
        prioritized = self.prioritize_insights(insights, max_count=3)
        
        return prioritized
        
    def create_pattern_insight(self, pattern: Pattern) -> Insight:
        """Create insight from detected pattern"""
        templates = {
            'weekend_warrior': "Your activity peaks on weekends - {detail}",
            'morning_person': "You're most active in the mornings, with {percent}% of activity before noon",
            'consistency_champion': "Your {metric} has been remarkably consistent, varying by only {variance}%",
            'improvement_streak': "You've improved your {metric} for {days} consecutive days!"
        }
        
        template = templates.get(pattern.type, "Interesting pattern in your {metric}: {detail}")
        
        return Insight(
            text=template.format(**pattern.details),
            category='pattern',
            importance=pattern.significance,
            visual_hint=pattern.suggested_visual
        )
```

### Tone Management
```python
class ToneManager:
    def __init__(self, preferred_tone: str = 'encouraging'):
        self.tone = preferred_tone
        self.tone_adjusters = {
            'encouraging': EncouragingToneAdjuster(),
            'neutral': NeutralToneAdjuster(),
            'motivating': MotivatingToneAdjuster(),
            'celebratory': CelebratoryToneAdjuster()
        }
        
    def apply_tone(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Apply tone adjustments to story sections"""
        adjuster = self.tone_adjusters[self.tone]
        
        adjusted_sections = {}
        for section_name, content in sections.items():
            adjusted_sections[section_name] = adjuster.adjust(content, section_name)
            
        return adjusted_sections

class EncouragingToneAdjuster:
    def adjust(self, content: str, section_type: str) -> str:
        """Apply encouraging tone to content"""
        # Replace neutral phrases with encouraging ones
        replacements = {
            "didn't meet": "came close to meeting",
            "failed to": "had opportunity to",
            "decreased": "had room for growth",
            "worse than": "different from",
            "below average": "building momentum"
        }
        
        adjusted = content
        for neutral, encouraging in replacements.items():
            adjusted = adjusted.replace(neutral, encouraging)
            
        # Add encouraging phrases
        if section_type == 'closing':
            adjusted += " Keep up the great work - every step counts!"
            
        return adjusted
```

### Recommendation Engine
```python
class RecommendationEngine:
    def __init__(self):
        self.recommendation_db = RecommendationDatabase()
        self.success_predictor = SuccessPredictor()
        
    def generate_recommendations(self, analysis: Analysis, user_profile: UserProfile) -> List[Recommendation]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Goal-based recommendations
        if analysis.goal_progress:
            goal_recs = self.generate_goal_recommendations(analysis.goal_progress)
            recommendations.extend(goal_recs)
            
        # Pattern-based recommendations
        if analysis.patterns:
            pattern_recs = self.generate_pattern_recommendations(analysis.patterns)
            recommendations.extend(pattern_recs)
            
        # Improvement opportunities
        improvement_recs = self.identify_improvement_opportunities(analysis)
        recommendations.extend(improvement_recs)
        
        # Filter and prioritize
        filtered = self.filter_recommendations(recommendations, user_profile)
        prioritized = self.prioritize_recommendations(filtered)
        
        # Add success probability
        for rec in prioritized:
            rec.success_probability = self.success_predictor.predict(rec, user_profile)
            
        return prioritized[:3]  # Top 3 recommendations
        
    def generate_goal_recommendations(self, goal_progress: GoalProgress) -> List[Recommendation]:
        """Generate recommendations based on goal progress"""
        recs = []
        
        for goal in goal_progress.active_goals:
            if goal.progress < 50:
                # Struggling with goal
                rec = Recommendation(
                    action=f"Try breaking down your {goal.name} goal into smaller daily targets",
                    rationale=f"You're at {goal.progress}% - smaller steps can build momentum",
                    category='goal_support',
                    difficulty='easy'
                )
                recs.append(rec)
                
            elif goal.progress > 90:
                # Close to achieving
                rec = Recommendation(
                    action=f"Push for your {goal.name} goal - you're almost there!",
                    rationale=f"At {goal.progress}%, just a little more effort needed",
                    category='goal_achievement',
                    difficulty='medium'
                )
                recs.append(rec)
                
        return recs
```

### Delivery System
```python
class StoryDeliveryManager:
    def __init__(self):
        self.delivery_channels = {
            'in_app': InAppDelivery(),
            'email': EmailDelivery(),
            'push': PushNotificationDelivery()
        }
        self.scheduler = DeliveryScheduler()
        
    def deliver_story(self, story: Story, user_preferences: DeliveryPreferences):
        """Deliver story through preferred channels"""
        # Format for each channel
        formatted_stories = {
            'in_app': self.format_for_app(story),
            'email': self.format_for_email(story),
            'push': self.create_push_summary(story)
        }
        
        # Deliver to enabled channels
        for channel, enabled in user_preferences.channels.items():
            if enabled:
                self.delivery_channels[channel].deliver(
                    formatted_stories[channel],
                    user_preferences.get_channel_settings(channel)
                )
                
    def format_for_app(self, story: Story) -> InAppStory:
        """Format story for in-app display"""
        return InAppStory(
            title=story.title,
            sections=self.create_card_sections(story),
            visuals=self.generate_story_visuals(story),
            actions=self.create_story_actions(story),
            dismissible=True,
            shareable=True
        )
        
    def format_for_email(self, story: Story) -> EmailContent:
        """Format story for email delivery"""
        html_content = self.render_email_template(story)
        plain_content = self.create_plain_text_version(story)
        
        return EmailContent(
            subject=self.generate_email_subject(story),
            html_body=html_content,
            plain_body=plain_content,
            attachments=self.create_email_attachments(story)
        )
```

### Preference Learning
```python
class PreferenceLearner:
    def __init__(self):
        self.interaction_tracker = InteractionTracker()
        self.preference_model = PreferenceModel()
        
    def learn_from_interaction(self, story: Story, interaction: UserInteraction):
        """Learn user preferences from story interactions"""
        # Track interaction
        self.interaction_tracker.record(story, interaction)
        
        # Update preference model
        if interaction.type == 'read_time':
            self.update_length_preference(story, interaction.duration)
        elif interaction.type == 'section_expanded':
            self.update_section_preference(interaction.section)
        elif interaction.type == 'shared':
            self.update_content_preference(story)
        elif interaction.type == 'dismissed_quickly':
            self.update_negative_preference(story)
            
    def get_learned_preferences(self) -> LearnedPreferences:
        """Get current learned preferences"""
        return LearnedPreferences(
            preferred_length=self.preference_model.optimal_length,
            favorite_sections=self.preference_model.top_sections,
            preferred_insights=self.preference_model.insight_types,
            best_delivery_time=self.calculate_optimal_delivery_time(),
            engagement_patterns=self.get_engagement_patterns()
        )
```

## Testing Requirements
- Unit tests for each story type
- Template variation testing
- Tone consistency validation
- Insight relevance testing
- Recommendation quality assessment
- NLG output quality checks
- Delivery system tests
- Preference learning validation

## Notes
- Keep language natural and varied
- Avoid repetitive phrases across stories
- Ensure medical/health claims are accurate
- Consider localization needs
- Plan for story archive/history
- Allow users to customize story frequency
- Consider privacy in story sharing features