"""
Notification management for anomaly detection system.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .anomaly_models import (
    Anomaly, Notification, Action, Severity, UserFeedback, 
    PersonalThreshold, DetectionMethod
)


class NotificationManager:
    """Manages user notifications for anomalies."""
    
    def __init__(self):
        self.notification_queue = []
        self.notification_history = []
        self.user_preferences = {
            'enabled': True,
            'severity_threshold': Severity.MEDIUM,
            'group_notifications': True,
            'max_notifications_per_hour': 5,
            'quiet_hours': {'start': 22, 'end': 7},  # 10 PM to 7 AM
            'preferred_actions': ['mark_false_positive', 'view_context']
        }
        self.grouped_notifications = defaultdict(list)
    
    def create_notification(self, anomaly: Anomaly) -> Optional[Notification]:
        """Create user-friendly notification for an anomaly."""
        if not self._should_notify(anomaly):
            return None
        
        # Check if we should group this notification
        if self.user_preferences['group_notifications']:
            group_key = self._get_group_key(anomaly)
            if group_key in self.grouped_notifications:
                # Add to existing group
                self.grouped_notifications[group_key].append(anomaly)
                return self._update_grouped_notification(group_key)
            else:
                # Start new group
                self.grouped_notifications[group_key] = [anomaly]
        
        notification = Notification(
            title=self._generate_title(anomaly),
            message=self._generate_message(anomaly),
            explanation=self._generate_explanation(anomaly),
            severity=anomaly.severity,
            actions=self._suggest_actions(anomaly),
            dismissible=True,
            groupable=self.user_preferences['group_notifications'],
            anomaly=anomaly
        )
        
        self.notification_queue.append(notification)
        return notification
    
    def _should_notify(self, anomaly: Anomaly) -> bool:
        """Determine if we should create a notification for this anomaly."""
        if not self.user_preferences['enabled']:
            return False
        
        # Check severity threshold
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        if severity_order.index(anomaly.severity) < severity_order.index(self.user_preferences['severity_threshold']):
            return False
        
        # Check rate limiting
        if self._is_rate_limited():
            return False
        
        # Check quiet hours
        if self._is_quiet_hours():
            return anomaly.severity == Severity.CRITICAL  # Only critical during quiet hours
        
        return True
    
    def _is_rate_limited(self) -> bool:
        """Check if we've exceeded the notification rate limit."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        recent_notifications = [
            n for n in self.notification_history 
            if n.timestamp > hour_ago
        ]
        
        return len(recent_notifications) >= self.user_preferences['max_notifications_per_hour']
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        now = datetime.now()
        current_hour = now.hour
        
        start_hour = self.user_preferences['quiet_hours']['start']
        end_hour = self.user_preferences['quiet_hours']['end']
        
        if start_hour <= end_hour:
            return start_hour <= current_hour <= end_hour
        else:  # Quiet hours span midnight
            return current_hour >= start_hour or current_hour <= end_hour
    
    def _get_group_key(self, anomaly: Anomaly) -> str:
        """Generate a key for grouping similar notifications."""
        return f"{anomaly.metric}_{anomaly.method.value}_{anomaly.severity.value}"
    
    def _update_grouped_notification(self, group_key: str) -> Notification:
        """Update an existing grouped notification."""
        anomalies = self.grouped_notifications[group_key]
        
        # Find existing notification in queue
        for notification in self.notification_queue:
            if (notification.anomaly and 
                self._get_group_key(notification.anomaly) == group_key):
                
                # Update notification with group info
                notification.title = f"Multiple {anomalies[0].metric} anomalies ({len(anomalies)})"
                notification.message = self._generate_grouped_message(anomalies)
                notification.explanation = self._generate_grouped_explanation(anomalies)
                return notification
        
        return None
    
    def _generate_title(self, anomaly: Anomaly) -> str:
        """Generate notification title."""
        metric_name = anomaly.metric.replace('_', ' ').title()
        
        severity_labels = {
            Severity.LOW: "Notice",
            Severity.MEDIUM: "Alert",
            Severity.HIGH: "Warning",
            Severity.CRITICAL: "Critical Alert"
        }
        
        return f"{severity_labels[anomaly.severity]}: {metric_name} Anomaly"
    
    def _generate_message(self, anomaly: Anomaly) -> str:
        """Generate notification message."""
        if isinstance(anomaly.value, dict):
            # Multivariate anomaly
            return f"Unusual pattern detected in {anomaly.metric} data."
        else:
            # Univariate anomaly
            return f"{anomaly.metric.replace('_', ' ').title()}: {anomaly.value}"
    
    def _generate_grouped_message(self, anomalies: List[Anomaly]) -> str:
        """Generate message for grouped notifications."""
        metric = anomalies[0].metric.replace('_', ' ').title()
        timespan = self._get_timespan(anomalies)
        return f"{len(anomalies)} {metric} anomalies detected {timespan}"
    
    def _generate_explanation(self, anomaly: Anomaly) -> str:
        """Generate contextual explanation."""
        explanations = []
        
        # Method-specific context
        if anomaly.method in [DetectionMethod.ZSCORE, DetectionMethod.MODIFIED_ZSCORE]:
            score = abs(anomaly.score)
            explanations.append(
                f"This value is {score:.1f} standard deviations from your typical range."
            )
        elif anomaly.method == DetectionMethod.IQR:
            explanations.append(
                f"This value falls outside your normal range using statistical quartiles."
            )
        elif anomaly.method == DetectionMethod.ISOLATION_FOREST:
            explanations.append(
                f"This pattern is unusual when considering multiple health metrics together."
            )
        elif anomaly.method == DetectionMethod.LOF:
            explanations.append(
                f"This value is significantly different from nearby data points."
            )
        
        # Add severity context
        if anomaly.severity == Severity.CRITICAL:
            explanations.append("This is a rare occurrence that may warrant attention.")
        elif anomaly.severity == Severity.HIGH:
            explanations.append("This deviation is quite significant.")
        elif anomaly.severity == Severity.MEDIUM:
            explanations.append("This is moderately unusual for your patterns.")
        
        # Add time context if available
        time_context = self._get_time_context(anomaly)
        if time_context:
            explanations.append(time_context)
        
        return " ".join(explanations)
    
    def _generate_grouped_explanation(self, anomalies: List[Anomaly]) -> str:
        """Generate explanation for grouped anomalies."""
        metric = anomalies[0].metric.replace('_', ' ').title()
        methods = set(a.method.value for a in anomalies)
        timespan = self._get_timespan(anomalies)
        
        explanation = f"Multiple {metric.lower()} anomalies detected {timespan} using "
        
        if len(methods) == 1:
            explanation += f"{list(methods)[0].replace('_', ' ')} analysis."
        else:
            explanation += f"{len(methods)} different detection methods."
        
        # Add collective severity assessment
        critical_count = sum(1 for a in anomalies if a.severity == Severity.CRITICAL)
        if critical_count > 0:
            explanation += f" {critical_count} are marked as critical."
        
        return explanation
    
    def _suggest_actions(self, anomaly: Anomaly) -> List[Action]:
        """Suggest appropriate actions for the anomaly."""
        actions = []
        
        # Always allow feedback
        actions.append(Action(
            label="This is normal for me",
            callback=lambda: self._mark_false_positive(anomaly),
            description="Mark this as a false positive to improve future detection"
        ))
        
        actions.append(Action(
            label="View details",
            callback=lambda: self._show_anomaly_details(anomaly),
            description="See detailed information about this anomaly"
        ))
        
        # Metric-specific actions
        if 'heart_rate' in anomaly.metric.lower():
            if isinstance(anomaly.value, (int, float)) and anomaly.value > 100:
                actions.append(Action(
                    label="Check recent activity",
                    callback=lambda: self._show_activity_context(anomaly),
                    description="See what activities might have caused this"
                ))
        
        elif 'sleep' in anomaly.metric.lower():
            actions.append(Action(
                label="Add sleep note",
                callback=lambda: self._add_sleep_note(anomaly),
                description="Record any factors that might have affected sleep"
            ))
        
        elif 'steps' in anomaly.metric.lower():
            actions.append(Action(
                label="Check location data",
                callback=lambda: self._check_location_context(anomaly),
                description="See if travel or location changes explain this"
            ))
        
        # Severity-specific actions
        if anomaly.severity in [Severity.HIGH, Severity.CRITICAL]:
            actions.append(Action(
                label="Remind me later",
                callback=lambda: self._schedule_reminder(anomaly),
                description="Get reminded about this anomaly in a few hours"
            ))
        
        return actions
    
    def _get_time_context(self, anomaly: Anomaly) -> str:
        """Generate time-based context for the anomaly."""
        if not isinstance(anomaly.timestamp, datetime):
            return ""
        
        now = datetime.now()
        time_diff = now - anomaly.timestamp
        
        if time_diff.days == 0:
            if time_diff.seconds < 3600:  # Less than 1 hour
                return "This just happened."
            else:
                hours = time_diff.seconds // 3600
                return f"This occurred {hours} hour{'s' if hours > 1 else ''} ago."
        elif time_diff.days == 1:
            return "This happened yesterday."
        elif time_diff.days < 7:
            return f"This occurred {time_diff.days} days ago."
        else:
            return f"This happened on {anomaly.timestamp.strftime('%B %d')}."
    
    def _get_timespan(self, anomalies: List[Anomaly]) -> str:
        """Get timespan description for grouped anomalies."""
        timestamps = [a.timestamp for a in anomalies if isinstance(a.timestamp, datetime)]
        if not timestamps:
            return "recently"
        
        earliest = min(timestamps)
        latest = max(timestamps)
        span = latest - earliest
        
        if span.days == 0:
            return "today"
        elif span.days == 1:
            return "over the past day"
        elif span.days < 7:
            return f"over the past {span.days} days"
        else:
            return f"over the past week"
    
    # Action callbacks (these would integrate with the UI)
    def _mark_false_positive(self, anomaly: Anomaly):
        """Mark anomaly as false positive."""
        # This would be connected to the feedback processor
        print(f"Marked {anomaly.metric} anomaly as false positive")
    
    def _show_anomaly_details(self, anomaly: Anomaly):
        """Show detailed information about the anomaly."""
        print(f"Showing details for {anomaly.metric} anomaly")
    
    def _show_activity_context(self, anomaly: Anomaly):
        """Show activity context around the anomaly time."""
        print(f"Showing activity context for {anomaly.timestamp}")
    
    def _add_sleep_note(self, anomaly: Anomaly):
        """Allow user to add a note about sleep factors."""
        print(f"Adding sleep note for {anomaly.timestamp}")
    
    def _check_location_context(self, anomaly: Anomaly):
        """Check location/travel context."""
        print(f"Checking location context for {anomaly.timestamp}")
    
    def _schedule_reminder(self, anomaly: Anomaly):
        """Schedule a reminder about this anomaly."""
        print(f"Scheduling reminder for {anomaly.metric} anomaly")
    
    def get_pending_notifications(self) -> List[Notification]:
        """Get all pending notifications."""
        return self.notification_queue.copy()
    
    def dismiss_notification(self, notification: Notification):
        """Dismiss a notification."""
        if notification in self.notification_queue:
            self.notification_queue.remove(notification)
            self.notification_history.append(notification)
    
    def clear_all_notifications(self):
        """Clear all pending notifications."""
        self.notification_history.extend(self.notification_queue)
        self.notification_queue.clear()
        self.grouped_notifications.clear()
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user notification preferences."""
        self.user_preferences.update(preferences)