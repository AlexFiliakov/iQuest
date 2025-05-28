"""
Goal Notification Integration for Apple Health Monitor Dashboard.
Bridges the goal management system with the notification manager.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging

from .goal_models import Goal, GoalType, GoalStatus, GoalProgress
from .notification_manager import NotificationManager
from .anomaly_models import Notification, Action, Severity

logger = logging.getLogger(__name__)


class GoalNotificationBridge:
    """Bridges goal events with the notification system."""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.enabled = True
        
        # Configure notification preferences for goals
        self.preferences = {
            'goal_achieved': True,
            'goal_milestone': True,
            'goal_at_risk': True,
            'goal_streak_reminder': True,
            'goal_deadline_approaching': True,
            'goal_suggestion': True,
            'goal_correlation': True
        }
    
    def notify_goal_achieved(self, goal: Goal, progress: GoalProgress):
        """Send notification when a goal is achieved."""
        if not self.enabled or not self.preferences['goal_achieved']:
            return
        
        notification = Notification(
            title=f"🎉 Goal Achieved: {goal.name}!",
            message=self._get_achievement_message(goal, progress),
            severity=Severity.INFO,
            created_at=datetime.now(),
            anomaly_id=None,  # Not an anomaly
            actions=[
                Action(
                    action_id="view_achievement",
                    label="View Achievement",
                    description="See your achievement details"
                ),
                Action(
                    action_id="set_new_goal",
                    label="Set New Goal",
                    description="Create a new challenge"
                )
            ]
        )
        
        self._send_notification(notification)
        logger.info(f"Goal achieved notification sent for: {goal.name}")
    
    def notify_goal_milestone(self, goal: Goal, milestone: str, progress: GoalProgress):
        """Send notification for goal milestones (25%, 50%, 75% complete)."""
        if not self.enabled or not self.preferences['goal_milestone']:
            return
        
        notification = Notification(
            title=f"📊 Milestone Reached: {milestone}",
            message=f"Great progress on {goal.name}! You're {progress.progress_percentage:.0f}% of the way there.",
            severity=Severity.INFO,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="view_progress",
                    label="View Progress",
                    description="See detailed progress"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def notify_goal_at_risk(self, goal: Goal, reason: str):
        """Send notification when a goal is at risk of not being achieved."""
        if not self.enabled or not self.preferences['goal_at_risk']:
            return
        
        notification = Notification(
            title=f"⚠️ Goal at Risk: {goal.name}",
            message=f"{reason}. Consider adjusting your approach or goal parameters.",
            severity=Severity.MEDIUM,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="view_suggestions",
                    label="Get Suggestions",
                    description="See recommendations to get back on track"
                ),
                Action(
                    action_id="adjust_goal",
                    label="Adjust Goal",
                    description="Modify goal parameters"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def notify_streak_reminder(self, goal: Goal, current_streak: int):
        """Send reminder to maintain a streak."""
        if not self.enabled or not self.preferences['goal_streak_reminder']:
            return
        
        notification = Notification(
            title=f"🔥 Keep Your Streak Alive!",
            message=f"Don't forget about {goal.name} today! You're on a {current_streak}-day streak.",
            severity=Severity.LOW,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="log_activity",
                    label="Log Activity",
                    description="Record today's progress"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def notify_deadline_approaching(self, goal: Goal, days_left: int):
        """Send notification when goal deadline is approaching."""
        if not self.enabled or not self.preferences['goal_deadline_approaching']:
            return
        
        urgency = "soon" if days_left > 3 else "very soon"
        severity = Severity.LOW if days_left > 3 else Severity.MEDIUM
        
        notification = Notification(
            title=f"⏰ Goal Deadline Approaching",
            message=f"{goal.name} ends {urgency} ({days_left} days left). Make the most of the remaining time!",
            severity=severity,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="view_progress",
                    label="Check Progress",
                    description="See how close you are to completion"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def notify_goal_suggestion(self, suggestions: List[Dict[str, Any]]):
        """Send notification with personalized goal suggestions."""
        if not self.enabled or not self.preferences['goal_suggestion']:
            return
        
        if not suggestions:
            return
        
        top_suggestion = suggestions[0]
        message = f"Based on your recent performance in {top_suggestion['metric']}, "
        message += f"we suggest: {top_suggestion['reasoning']}"
        
        notification = Notification(
            title="💡 New Goal Suggestion",
            message=message,
            severity=Severity.INFO,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="view_suggestions",
                    label="View All Suggestions",
                    description="See personalized goal recommendations"
                ),
                Action(
                    action_id="create_goal",
                    label="Create Goal",
                    description="Set up this suggested goal"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def notify_goal_correlation(self, goal1: Goal, goal2: Goal, relationship: str):
        """Send notification about goal relationships."""
        if not self.enabled or not self.preferences['goal_correlation']:
            return
        
        if relationship == 'synergistic':
            title = "🤝 Goals Working Together"
            message = f"{goal1.name} and {goal2.name} are helping each other! Keep up the great work on both."
        elif relationship == 'conflicting':
            title = "⚡ Potential Goal Conflict"
            message = f"{goal1.name} and {goal2.name} may be competing for your time. Consider scheduling them separately."
        else:
            return  # Don't notify for independent goals
        
        notification = Notification(
            title=title,
            message=message,
            severity=Severity.INFO,
            created_at=datetime.now(),
            actions=[
                Action(
                    action_id="view_analysis",
                    label="View Analysis",
                    description="See detailed goal relationship analysis"
                )
            ]
        )
        
        self._send_notification(notification)
    
    def schedule_goal_notifications(self, goal: Goal):
        """Schedule recurring notifications for a goal."""
        # This would integrate with a scheduler to send regular reminders
        # For now, we'll just log the intention
        logger.info(f"Scheduling notifications for goal: {goal.name}")
        
        if goal.goal_type == GoalType.HABIT:
            # Daily reminders for habit goals
            logger.info(f"Daily reminders scheduled for habit goal: {goal.name}")
        elif goal.goal_type == GoalType.CONSISTENCY:
            # Reminders based on frequency
            logger.info(f"Frequency-based reminders scheduled for: {goal.name}")
    
    def _get_achievement_message(self, goal: Goal, progress: GoalProgress) -> str:
        """Generate achievement message based on goal type."""
        if goal.goal_type == GoalType.TARGET:
            return f"You reached {progress.value:.0f} {goal.metric}! Fantastic work!"
        elif goal.goal_type == GoalType.CONSISTENCY:
            return f"You maintained {goal.frequency} days per week consistently. Great job!"
        elif goal.goal_type == GoalType.IMPROVEMENT:
            improvement = ((progress.value - goal.baseline_value) / goal.baseline_value) * 100
            return f"You improved by {improvement:.1f}%! Amazing progress!"
        elif goal.goal_type == GoalType.HABIT:
            return f"You completed your {goal.target_days}-day challenge! New habit formed!"
        else:
            return "Congratulations on achieving your goal!"
    
    def _send_notification(self, notification: Notification):
        """Send notification through the notification manager."""
        try:
            # The notification manager will handle the actual delivery
            # For now, we'll just add it to the queue
            if hasattr(self.notification_manager, 'notification_queue'):
                self.notification_manager.notification_queue.append(notification)
            
            # Log the notification
            logger.debug(f"Notification queued: {notification.title}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def update_preferences(self, preferences: Dict[str, bool]):
        """Update notification preferences."""
        self.preferences.update(preferences)
        logger.info(f"Goal notification preferences updated: {preferences}")
    
    def disable_notifications(self):
        """Disable all goal notifications."""
        self.enabled = False
        logger.info("Goal notifications disabled")
    
    def enable_notifications(self):
        """Enable goal notifications."""
        self.enabled = True
        logger.info("Goal notifications enabled")