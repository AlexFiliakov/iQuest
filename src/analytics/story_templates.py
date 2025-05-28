"""
Story Templates for natural language generation.
Provides varied templates for different story types and sections.
"""

from typing import Dict, List, Any, Optional
import random
import json
import os
from pathlib import Path


class StoryTemplates:
    """Manages story templates for natural language generation."""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or self._get_default_template_dir()
        self.templates = self.load_all_templates()
    
    def _get_default_template_dir(self) -> str:
        """Get default template directory."""
        return os.path.join(os.path.dirname(__file__), 'templates')
    
    def load_all_templates(self) -> Dict[str, Any]:
        """Load all templates from files or defaults."""
        # For now, return hardcoded templates
        # In production, these would be loaded from JSON files
        return {
            'weekly_recap': self._get_weekly_templates(),
            'monthly_journey': self._get_monthly_templates(),
            'year_in_review': self._get_yearly_templates(),
            'milestone_celebration': self._get_milestone_templates()
        }
    
    def _get_weekly_templates(self) -> Dict[str, Any]:
        """Get weekly recap templates."""
        return {
            'openings': {
                'exceptional': [
                    "What an incredible week, {name}! Your {key_metric} improved by {improvement_percent}%, making this {week_summary}.",
                    "{name}, this week stands out! With {week_summary}, you've shown remarkable progress in {key_metric}.",
                    "Exceptional work this week, {name}! {week_summary} with a {improvement_percent}% boost in {key_metric}.",
                    "This was truly {week_summary}, {name}! Your dedication to {key_metric} really paid off.",
                    "{name}, you've outdone yourself! {week_summary} featuring outstanding {key_metric} performance."
                ],
                'improving': [
                    "Great progress this week, {name}! Your dedication is showing with {week_summary}.",
                    "{name}, you're building momentum! This was {week_summary} with consistent improvements.",
                    "Nice work, {name}! {week_summary} shows you're on the right track.",
                    "Keep it up, {name}! This was {week_summary} with positive trends across the board.",
                    "{name}, your efforts are paying off! {week_summary} with measurable progress."
                ],
                'consistent': [
                    "Another solid week, {name}! Your consistency continues with {week_summary}.",
                    "Staying the course, {name}! This was {week_summary} with reliable patterns.",
                    "{name}, your steady approach shows in {week_summary}.",
                    "Consistency is key, {name}! {week_summary} demonstrates your commitment.",
                    "Well done maintaining your routine, {name}! This was {week_summary}."
                ],
                'standard': [
                    "Let's review your week, {name}. This was {week_summary}.",
                    "Here's your weekly summary, {name}. Overall, {week_summary}.",
                    "{name}, looking at your week: {week_summary}.",
                    "Time for your weekly recap, {name}. {week_summary}.",
                    "Your week in review, {name}: {week_summary}."
                ],
                'challenging': [
                    "{name}, this week had its challenges, but {week_summary}.",
                    "Not every week is easy, {name}. This was {week_summary}.",
                    "{name}, despite some obstacles, {week_summary}.",
                    "A learning week, {name}. {week_summary} with opportunities for growth.",
                    "{name}, this week's data shows {week_summary} - every journey has its ups and downs."
                ]
            },
            'achievements': {
                'single_record': [
                    "You set a new personal record for {metric} at {value}! {context}",
                    "New personal best! Your {metric} reached {value} - {context}",
                    "Record broken! {metric} hit {value}, {context}",
                    "Achievement unlocked: {metric} at {value}! {context}",
                    "Milestone reached! Your {metric} peaked at {value} - {context}"
                ],
                'multiple_records': [
                    "Multiple personal records this week in {metrics_list}! You're on fire!",
                    "Record-breaking week with new highs in {metrics_list}!",
                    "Impressive! You've set new personal bests in {metrics_list}.",
                    "What a week - new records in {metrics_list}!",
                    "You've pushed past previous limits in {metrics_list}!"
                ],
                'streak_single': [
                    "Your {metric} streak has reached {days} days! Keep the momentum going!",
                    "{days} days and counting! Your {metric} streak is impressive.",
                    "Consistency champion! {days} consecutive days of {metric}.",
                    "Your {metric} streak hits {days} days - that's dedication!",
                    "Amazing consistency - {days} days straight of {metric}!"
                ],
                'streak_multiple': [
                    "You're maintaining {count} active streaks totaling {total_days} days!",
                    "Impressive dedication with {count} streaks running for {total_days} combined days!",
                    "{count} active streaks show your commitment - {total_days} total days!",
                    "Multiple wins! {count} streaks adding up to {total_days} days.",
                    "Juggling {count} streaks successfully - {total_days} days combined!"
                ],
                'goal_single': [
                    "Goal achieved! {context}",
                    "You did it! {context}",
                    "Success! {context}",
                    "Target hit! {context}",
                    "Objective complete! {context}"
                ],
                'goal_multiple': [
                    "Fantastic progress - you've achieved {count} goals this week!",
                    "{count} goals completed! You're unstoppable!",
                    "Goal crusher! {count} objectives met this week.",
                    "Impressive goal completion - {count} targets achieved!",
                    "{count} goals down! Your focus is paying off."
                ],
                'improvement': [
                    "Your {metric} improved by {percent}% - excellent progress!",
                    "Great improvement in {metric} with a {percent}% increase!",
                    "{percent}% better in {metric} - keep up the great work!",
                    "Solid gains in {metric} - up {percent}% from last week!",
                    "Your {metric} is trending up with {percent}% improvement!"
                ]
            },
            'comparisons': {
                'overall_positive': [
                    "Overall, your metrics improved by {percent}% compared to last week.",
                    "This week showed a {percent}% improvement across your health metrics.",
                    "You're up {percent}% from last week - great progress!",
                    "Compared to last week, you've improved by {percent}% overall.",
                    "A {percent}% boost from last week's performance!"
                ],
                'overall_stable': [
                    "Your metrics remained stable compared to last week.",
                    "This week maintained similar patterns to last week.",
                    "Consistency across the board - metrics holding steady.",
                    "Your performance matched last week's levels.",
                    "Stable week with metrics in line with recent averages."
                ],
                'overall_negative': [
                    "This week saw a {percent}% dip in overall metrics.",
                    "Metrics were down {percent}% - these variations are normal.",
                    "A {percent}% decrease this week - part of the natural rhythm.",
                    "This week's metrics were {percent}% lower - don't be discouraged!",
                    "Down {percent}% this week - opportunity to refocus."
                ],
                'metric_improved': [
                    "{metric} showed excellent improvement at {percent}% increase.",
                    "Your {metric} is up {percent}% - fantastic!",
                    "Great news: {metric} improved by {percent}%!",
                    "{metric} performance boosted by {percent}%.",
                    "Notable improvement in {metric} - up {percent}%!"
                ],
                'metric_declined': [
                    "{metric} was down {percent}% - room for focus next week.",
                    "{metric} decreased by {percent}% - these fluctuations happen.",
                    "A {percent}% dip in {metric} - tomorrow is a new day.",
                    "{metric} down {percent}% - opportunity for improvement.",
                    "{metric} saw a {percent}% decrease - stay consistent."
                ]
            },
            'insights': {
                'pattern_intro': [
                    "Your data reveals interesting patterns worth noting.",
                    "Some notable trends emerged this week.",
                    "Here's what your data is telling us.",
                    "A few insights from your weekly patterns.",
                    "Your health data shows some interesting trends."
                ],
                'specific_insight': [
                    "{insight_text}",
                    "Did you know? {insight_text}",
                    "Interesting finding: {insight_text}",
                    "Data insight: {insight_text}",
                    "Worth noting: {insight_text}"
                ]
            },
            'recommendations': {
                'intro': [
                    "Based on your progress, here are some suggestions:",
                    "To build on this week's performance:",
                    "Looking ahead, consider these actions:",
                    "Here's how to maintain your momentum:",
                    "Some ideas for next week:"
                ],
                'specific_recommendation': [
                    "{action} - {rationale}",
                    "Try this: {action}. Why? {rationale}",
                    "Suggestion: {action} because {rationale}",
                    "Consider {action} - {rationale}",
                    "Next step: {action} ({rationale})"
                ]
            },
            'closings': {
                'encouraging': [
                    "Keep up the great work! Every step forward counts!",
                    "You're doing amazing - keep going!",
                    "Proud of your progress - onwards and upwards!",
                    "Keep building on this momentum!",
                    "You've got this - see you next week!"
                ],
                'motivating': [
                    "Ready to make next week even better? You have the power!",
                    "Challenge yourself to reach new heights next week!",
                    "Next week is full of possibilities - seize them!",
                    "Push yourself a little further - you're capable of amazing things!",
                    "Let's make next week your best yet!"
                ],
                'neutral': [
                    "See you next week for another summary.",
                    "Until next time, take care.",
                    "That's your week in review.",
                    "Check back next week for your progress update.",
                    "Your next summary will be ready in a week."
                ],
                'supportive': [
                    "Remember, progress isn't always linear - you're doing great!",
                    "Every week is a fresh start - be kind to yourself.",
                    "Your health journey is unique - celebrate your efforts!",
                    "Small steps lead to big changes - keep going!",
                    "You're exactly where you need to be - trust the process."
                ]
            }
        }
    
    def _get_monthly_templates(self) -> Dict[str, Any]:
        """Get monthly journey templates."""
        return {
            'openings': {
                'exceptional': [
                    "What a remarkable month, {name}! {month} was {theme} with incredible achievements.",
                    "{name}, {month} stands out as {theme} - truly exceptional!",
                    "An outstanding {month}, {name}! This month's journey was {theme}.",
                    "{month} will be remembered as {theme}, {name} - what a month!",
                    "Exceptional progress in {month}, {name}! A month of {theme}."
                ],
                'positive': [
                    "{name}, {month} was {theme} with steady progress throughout.",
                    "Great month, {name}! {month} brought {theme}.",
                    "{name}, your {month} journey was {theme} - well done!",
                    "A positive {month}, {name}, characterized by {theme}.",
                    "{month} delivered {theme} - nice work, {name}!"
                ],
                'standard': [
                    "Let's explore your {month} journey, {name}. This month was about {theme}.",
                    "{name}, your {month} story: {theme}.",
                    "Time to review {month}, {name}. The theme was {theme}.",
                    "{month} in review, {name}: a month of {theme}.",
                    "Your {month} narrative, {name}: {theme}."
                ]
            },
            'themes': {
                'growth': [
                    "consistent growth and improvement",
                    "building strength and endurance",
                    "pushing past previous limits",
                    "expanding your capabilities",
                    "reaching new heights"
                ],
                'consistency': [
                    "remarkable consistency and dedication",
                    "steady commitment to your goals",
                    "maintaining strong habits",
                    "reliable daily practices",
                    "unwavering focus"
                ],
                'discovery': [
                    "discovering new patterns and insights",
                    "learning about your body's rhythms",
                    "uncovering hidden strengths",
                    "exploring new possibilities",
                    "finding your optimal balance"
                ],
                'transformation': [
                    "meaningful transformation",
                    "significant positive changes",
                    "evolving health patterns",
                    "personal evolution",
                    "remarkable adaptation"
                ],
                'resilience': [
                    "resilience and determination",
                    "overcoming challenges",
                    "bouncing back stronger",
                    "persistent effort",
                    "adaptability and strength"
                ]
            },
            'progress': {
                'excellent': [
                    "Your progress this month has been exceptional - {details}",
                    "Remarkable advancement in {details}",
                    "You've made significant strides: {details}",
                    "Outstanding progress across {details}",
                    "Major improvements in {details}"
                ],
                'good': [
                    "Solid progress this month in {details}",
                    "Good advancement in {details}",
                    "Positive movement in {details}",
                    "Steady gains in {details}",
                    "Nice progress with {details}"
                ],
                'mixed': [
                    "Mixed results this month - gains in {positive}, challenges in {negative}",
                    "Some wins ({positive}) and areas to focus on ({negative})",
                    "Progress in {positive}, with room to improve {negative}",
                    "Strengths in {positive}, opportunities in {negative}",
                    "Advances in {positive}, while {negative} needs attention"
                ]
            },
            'habits': {
                'forming': [
                    "New habits are taking shape: {habits_list}",
                    "You're building strong routines around {habits_list}",
                    "Habit formation in progress: {habits_list}",
                    "Establishing patterns in {habits_list}",
                    "Creating lasting habits: {habits_list}"
                ],
                'strengthening': [
                    "Your {habit} habit is becoming second nature",
                    "Consistency in {habit} is paying off",
                    "{habit} is now part of your routine",
                    "Strong adherence to {habit}",
                    "{habit} habit is well-established"
                ],
                'struggling': [
                    "Still working on consistency with {habit}",
                    "{habit} remains a work in progress",
                    "Building momentum with {habit}",
                    "Gradual improvement in {habit}",
                    "Developing {habit} takes time"
                ]
            },
            'challenges': {
                'overcome': [
                    "You successfully navigated {challenge}",
                    "Overcame {challenge} with determination",
                    "Pushed through {challenge}",
                    "Conquered {challenge} this month",
                    "Rose above {challenge}"
                ],
                'ongoing': [
                    "Continue working on {challenge}",
                    "{challenge} remains an area of focus",
                    "Making progress with {challenge}",
                    "Gradually improving {challenge}",
                    "Steady effort on {challenge}"
                ]
            },
            'growth': {
                'personal': [
                    "Personal growth is evident in {area}",
                    "You've expanded your capabilities in {area}",
                    "New strengths discovered in {area}",
                    "Development in {area} is impressive",
                    "Growth in {area} shows your potential"
                ],
                'metrics': [
                    "Your {metric} improved by {percent}% this month",
                    "{metric} shows {percent}% growth",
                    "Significant {percent}% gain in {metric}",
                    "{metric} up {percent}% - excellent!",
                    "{percent}% improvement in {metric}"
                ]
            },
            'closings': {
                'forward_looking': [
                    "As {next_month} begins, build on these achievements!",
                    "Take these lessons into {next_month}!",
                    "Ready for what {next_month} will bring?",
                    "{next_month} awaits - keep up the momentum!",
                    "Onwards to {next_month} with confidence!"
                ],
                'reflective': [
                    "Take a moment to appreciate your {month} journey.",
                    "Reflect on how far you've come this month.",
                    "{month} brought growth - celebrate it!",
                    "Be proud of your {month} achievements.",
                    "Another month of progress in the books!"
                ]
            }
        }
    
    def _get_yearly_templates(self) -> Dict[str, Any]:
        """Get year in review templates."""
        return {
            'openings': {
                'transformative': [
                    "What an incredible year of transformation, {name}! {year} has been {summary}.",
                    "{name}, {year} will be remembered as {summary} - truly remarkable!",
                    "A year of {summary}, {name}! {year} brought extraordinary changes.",
                    "{year} has been {summary}, {name} - what a journey!",
                    "Transformative doesn't begin to describe your {year}, {name}. {summary}!"
                ],
                'positive': [
                    "{name}, {year} has been {summary} with consistent progress.",
                    "A year of {summary}, {name} - well done!",
                    "{year} brought {summary}, {name}. Be proud!",
                    "Looking back at {year}, {name}: {summary}.",
                    "Your {year} story is one of {summary}, {name}!"
                ],
                'reflective': [
                    "As {year} comes to a close, {name}, let's celebrate {summary}.",
                    "Time to reflect on {year}, {name}. A year of {summary}.",
                    "{name}, your {year} journey: {summary}.",
                    "The story of your {year}, {name}: {summary}.",
                    "Reviewing {year}, {name} - a year defined by {summary}."
                ]
            },
            'summaries': {
                'exceptional': [
                    "unprecedented growth and achievement",
                    "breaking through barriers",
                    "extraordinary dedication and results",
                    "remarkable transformation",
                    "outstanding progress"
                ],
                'positive': [
                    "steady improvement and learning",
                    "consistent effort and progress",
                    "building healthy habits",
                    "positive momentum",
                    "meaningful advancement"
                ],
                'mixed': [
                    "ups and downs with valuable lessons",
                    "challenges and victories",
                    "growth through perseverance",
                    "learning and adapting",
                    "resilience and discovery"
                ]
            },
            'milestones': {
                'intro': [
                    "This year's major milestones tell your story:",
                    "Key achievements that defined your {year}:",
                    "Celebrating your {year} milestones:",
                    "The highlights of your {year} journey:",
                    "Milestone moments from {year}:"
                ],
                'achievement': [
                    "{date}: {achievement} - {significance}",
                    "{achievement} achieved in {date}! {significance}",
                    "{date} marked {achievement}. {significance}",
                    "Remember {date}? That's when {achievement}. {significance}",
                    "{achievement} ({date}) - {significance}"
                ]
            },
            'transformation': {
                'physical': [
                    "Your physical transformation shows {change}",
                    "Physically, you've {change}",
                    "Your body has {change}",
                    "Physical changes include {change}",
                    "Transformation evident in {change}"
                ],
                'habits': [
                    "Your habits evolved from {old} to {new}",
                    "Habit transformation: {old} became {new}",
                    "You've replaced {old} with {new}",
                    "From {old} to {new} - impressive change!",
                    "Habits shifted from {old} to {new}"
                ],
                'mindset': [
                    "Your approach to health has {change}",
                    "Mentally, you've {change}",
                    "Your health mindset {change}",
                    "Perspective shift: {change}",
                    "Your outlook has {change}"
                ]
            },
            'statistics': {
                'impressive': [
                    "{statistic} - that's {comparison}!",
                    "Consider this: {statistic}. {comparison}!",
                    "{statistic}. To put that in perspective: {comparison}",
                    "The numbers: {statistic}. {comparison}!",
                    "Stats don't lie: {statistic} ({comparison})"
                ],
                'summary': [
                    "Total {metric}: {value} across {days} days",
                    "{days} days tracked, {value} total {metric}",
                    "You logged {value} {metric} over {days} days",
                    "{metric} totaled {value} in {days} days",
                    "Across {days} days: {value} {metric}"
                ]
            },
            'best_moments': {
                'intro': [
                    "Your {year} highlight reel:",
                    "Moments that made {year} special:",
                    "The best of your {year}:",
                    "Peak moments from {year}:",
                    "{year}'s greatest hits:"
                ],
                'moment': [
                    "{date}: {moment} - unforgettable!",
                    "That time in {date} when {moment}",
                    "{moment} on {date} - what a day!",
                    "Remember {date}? {moment}!",
                    "{date}'s highlight: {moment}"
                ]
            },
            'lessons': {
                'intro': [
                    "Key lessons from your {year} journey:",
                    "What {year} taught you:",
                    "Wisdom gained in {year}:",
                    "Lessons learned this year:",
                    "{year}'s teachings:"
                ],
                'lesson': [
                    "{lesson}",
                    "You learned that {lesson}",
                    "Discovery: {lesson}",
                    "Important realization: {lesson}",
                    "Truth discovered: {lesson}"
                ]
            },
            'looking_forward': {
                'next_year': [
                    "As {next_year} approaches, you're equipped with {strength}",
                    "{next_year} holds infinite possibilities - you have {strength}",
                    "Entering {next_year} with {strength}",
                    "You're ready for {next_year} with {strength}",
                    "{next_year} awaits, and you bring {strength}"
                ],
                'goals': [
                    "Potential {next_year} goals: {goals_list}",
                    "Consider these for {next_year}: {goals_list}",
                    "{next_year} opportunities: {goals_list}",
                    "Areas to explore in {next_year}: {goals_list}",
                    "{next_year} possibilities: {goals_list}"
                ]
            },
            'closings': {
                'celebratory': [
                    "Here's to an incredible {year} and an even better {next_year}!",
                    "Celebrate your {year} journey - you've earned it!",
                    "What a year! Onwards to {next_year}!",
                    "Bravo on a fantastic {year}! {next_year} awaits!",
                    "Toast to your {year} achievements! Bring on {next_year}!"
                ],
                'reflective': [
                    "Thank you for trusting us with your {year} journey.",
                    "Honored to be part of your {year} story.",
                    "Your {year} journey inspires us. Here's to {next_year}!",
                    "Grateful to witness your {year} transformation.",
                    "Your {year} story is uniquely yours - own it!"
                ]
            }
        }
    
    def _get_milestone_templates(self) -> Dict[str, Any]:
        """Get milestone celebration templates."""
        return {
            'openings': {
                'celebration': [
                    "🎉 Incredible achievement, {name}! You've {achievement}!",
                    "🎊 Milestone unlocked! {name}, you've {achievement}!",
                    "🏆 Outstanding, {name}! {achievement} is no small feat!",
                    "✨ Celebration time! {name} has {achievement}!",
                    "🌟 What an accomplishment! {name}, you've {achievement}!"
                ],
                'record': [
                    "🎯 New personal record! {name}, you've {achievement}!",
                    "📈 Record shattered! {achievement}, {name}!",
                    "🚀 Breaking barriers! {name} just {achievement}!",
                    "💪 Personal best alert! {name} has {achievement}!",
                    "⭐ History made! {name}, you've {achievement}!"
                ],
                'streak': [
                    "🔥 Incredible consistency! {name}, you've {achievement}!",
                    "💫 Streak milestone! {achievement}, {name}!",
                    "🎯 Dedication pays off! {name} has {achievement}!",
                    "⚡ Unstoppable! {name}, you've {achievement}!",
                    "🌟 Consistency champion! {name} just {achievement}!"
                ]
            },
            'context': {
                'significance': [
                    "This achievement places you in the top {percentile}% of users!",
                    "Only {percentage}% of people reach this milestone!",
                    "This level of {metric} is exceptional!",
                    "You've joined an elite group with this achievement!",
                    "This milestone represents extraordinary dedication!"
                ],
                'comparison': [
                    "That's {comparison} than your starting point!",
                    "You've improved by {percentage}% since beginning!",
                    "This is {multiplier}x better than average!",
                    "You've surpassed your previous best by {margin}!",
                    "This beats your old record by {difference}!"
                ]
            },
            'journey': {
                'time_based': [
                    "It took {days} days of dedication to reach this point.",
                    "After {weeks} weeks of consistent effort, you've made it!",
                    "{months} months ago, this seemed impossible. Look at you now!",
                    "Your {days}-day journey to this milestone is inspiring!",
                    "From day 1 to day {days} - what a transformation!"
                ],
                'effort_based': [
                    "Through {sessions} sessions, you've built up to this moment.",
                    "Each of your {efforts} efforts contributed to this success.",
                    "This represents {hours} hours of commitment!",
                    "Your {total_amount} total {metric} led to this milestone!",
                    "Accumulated over {count} activities - amazing dedication!"
                ]
            },
            'significance': {
                'health': [
                    "This milestone indicates {health_benefit}.",
                    "Achieving this means {health_impact}.",
                    "Your body is now {health_improvement}.",
                    "This level of {metric} contributes to {health_outcome}.",
                    "Research shows this achievement {health_correlation}."
                ],
                'personal': [
                    "You've proven you can {capability}.",
                    "This shows your ability to {strength}.",
                    "You've demonstrated {quality}.",
                    "This milestone reflects your {attribute}.",
                    "You've shown that {personal_growth}."
                ]
            },
            'next_challenges': {
                'progression': [
                    "Ready for the next level? Aim for {next_milestone}!",
                    "Your next target: {next_milestone}!",
                    "Challenge accepted? Go for {next_milestone}!",
                    "What's next? How about {next_milestone}?",
                    "Keep pushing - {next_milestone} awaits!"
                ],
                'maintenance': [
                    "Now, maintain this level for {duration}!",
                    "Can you keep this up for {duration}?",
                    "Challenge: Hold this standard for {duration}!",
                    "Sustain this achievement for {duration}!",
                    "Your next goal: Consistency for {duration}!"
                ]
            },
            'encouragement': {
                'proud': [
                    "Take a moment to feel proud - you've earned it!",
                    "This is YOUR moment - celebrate it!",
                    "Pat yourself on the back - seriously!",
                    "You should be incredibly proud!",
                    "Savor this victory - it's all yours!"
                ],
                'inspiring': [
                    "You're an inspiration to others on this journey!",
                    "Your dedication motivates everyone around you!",
                    "You're showing what's possible with commitment!",
                    "Your success story inspires others!",
                    "You're proof that goals are achievable!"
                ],
                'future': [
                    "This is just the beginning of what you can achieve!",
                    "If you can do this, imagine what else is possible!",
                    "You've unlocked a new level of potential!",
                    "The sky's the limit from here!",
                    "This milestone is a stepping stone to greatness!"
                ]
            },
            'closings': {
                'celebration': [
                    "Celebrate this win - you've absolutely earned it! 🎉",
                    "Enjoy this moment of triumph! 🏆",
                    "Victory is yours - celebrate accordingly! 🎊",
                    "Cheers to your incredible achievement! 🥳",
                    "Bask in this success - well done! ⭐"
                ],
                'motivation': [
                    "Keep reaching for the stars! ⭐",
                    "Onwards and upwards! 🚀",
                    "The best is yet to come! 💫",
                    "Keep crushing those goals! 💪",
                    "Your journey continues - stay amazing! 🌟"
                ]
            }
        }
    
    def get_template(self, story_type: str, section: str, 
                     subsection: Optional[str] = None) -> List[str]:
        """Get template variations for a specific section."""
        try:
            templates = self.templates.get(story_type, {})
            section_templates = templates.get(section, {})
            
            if subsection:
                return section_templates.get(subsection, [])
            else:
                # Return all templates for the section
                all_templates = []
                for sub_templates in section_templates.values():
                    if isinstance(sub_templates, list):
                        all_templates.extend(sub_templates)
                return all_templates
                
        except Exception as e:
            # Return fallback template
            return [f"[{story_type} {section} content]"]
    
    def get_random_template(self, story_type: str, section: str,
                           subsection: Optional[str] = None) -> str:
        """Get a random template for a section."""
        templates = self.get_template(story_type, section, subsection)
        if templates:
            return random.choice(templates)
        return f"[{story_type} {section} content]"
    
    def fill_template(self, template: str, data: Dict[str, Any]) -> str:
        """Fill a template with provided data."""
        try:
            # Handle special formatting cases
            filled = template
            
            # Replace name with fallback if not provided
            if '{name}' in filled and 'name' not in data:
                data['name'] = 'there'
            
            # Format lists properly
            for key, value in data.items():
                if isinstance(value, list) and f'{{{key}}}' in filled:
                    # Convert list to comma-separated string
                    if len(value) > 2:
                        data[key] = ', '.join(value[:-1]) + f', and {value[-1]}'
                    elif len(value) == 2:
                        data[key] = f'{value[0]} and {value[1]}'
                    elif len(value) == 1:
                        data[key] = value[0]
                    else:
                        data[key] = ''
            
            return filled.format(**data)
            
        except Exception as e:
            # Return template as-is if formatting fails
            return template
    
    def save_custom_template(self, story_type: str, section: str,
                           templates: List[str], subsection: Optional[str] = None):
        """Save custom templates for a section."""
        if story_type not in self.templates:
            self.templates[story_type] = {}
        
        if section not in self.templates[story_type]:
            self.templates[story_type][section] = {}
        
        if subsection:
            self.templates[story_type][section][subsection] = templates
        else:
            self.templates[story_type][section] = templates
    
    def export_templates(self, filepath: str):
        """Export all templates to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.templates, f, indent=2)
    
    def import_templates(self, filepath: str):
        """Import templates from a JSON file."""
        with open(filepath, 'r') as f:
            imported = json.load(f)
            self.templates.update(imported)