"""
Story Delivery Manager for distributing generated stories through various channels.
Handles in-app cards, email delivery, and push notifications.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, time
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .data_story_generator import Story, StoryType

logger = logging.getLogger(__name__)


@dataclass
class DeliveryPreferences:
    """User preferences for story delivery."""
    channels: Dict[str, bool] = None  # {'in_app': True, 'email': False, 'push': True}
    email_address: Optional[str] = None
    email_frequency: str = 'weekly'  # daily, weekly, monthly
    push_enabled: bool = True
    push_time: Optional[time] = None
    in_app_auto_display: bool = True
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = {
                'in_app': True,
                'email': False,
                'push': False
            }
    
    def get_channel_settings(self, channel: str) -> Dict[str, Any]:
        """Get settings for specific channel."""
        settings = {
            'enabled': self.channels.get(channel, False)
        }
        
        if channel == 'email':
            settings.update({
                'address': self.email_address,
                'frequency': self.email_frequency
            })
        elif channel == 'push':
            settings.update({
                'time': self.push_time
            })
        elif channel == 'in_app':
            settings.update({
                'auto_display': self.in_app_auto_display
            })
        
        return settings


@dataclass
class InAppStory:
    """Story formatted for in-app display."""
    title: str
    sections: List['CardSection']
    visuals: List['StoryVisual']
    actions: List['StoryAction']
    dismissible: bool = True
    shareable: bool = True
    display_priority: int = 5  # 1-10, higher is more important


@dataclass
class CardSection:
    """Section of an in-app story card."""
    type: str  # 'text', 'metric', 'chart', 'insight', 'recommendation'
    title: Optional[str] = None
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    expandable: bool = False
    expanded_content: Optional[str] = None


@dataclass
class StoryVisual:
    """Visual element for story display."""
    type: str  # 'chart', 'icon', 'progress', 'celebration'
    data: Dict[str, Any]
    position: str = 'inline'  # 'header', 'inline', 'footer'
    size: str = 'medium'  # 'small', 'medium', 'large'


@dataclass
class StoryAction:
    """Interactive action for story."""
    type: str  # 'button', 'link', 'share'
    label: str
    action: str  # Action identifier
    style: str = 'primary'  # 'primary', 'secondary', 'text'
    data: Optional[Dict[str, Any]] = None


@dataclass
class EmailContent:
    """Email formatted story content."""
    subject: str
    html_body: str
    plain_body: str
    attachments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class PushNotification:
    """Push notification content."""
    title: str
    body: str
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    priority: str = 'normal'  # 'low', 'normal', 'high'


class DeliveryChannel(ABC):
    """Base class for delivery channels."""
    
    @abstractmethod
    def deliver(self, content: Any, settings: Dict[str, Any]) -> bool:
        """Deliver content through this channel."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if channel is available."""
        pass


class InAppDelivery(DeliveryChannel):
    """In-app story delivery."""
    
    def __init__(self):
        self.story_queue = []
        self.displayed_stories = []
    
    def deliver(self, content: InAppStory, settings: Dict[str, Any]) -> bool:
        """Deliver story to in-app display."""
        try:
            if not settings.get('enabled', True):
                return False
            
            # Add to story queue
            self.story_queue.append({
                'story': content,
                'delivered_at': datetime.now(),
                'displayed': False,
                'settings': settings
            })
            
            # Auto-display if enabled
            if settings.get('auto_display', True):
                self.display_story(content)
            
            logger.info(f"In-app story delivered: {content.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver in-app story: {e}")
            return False
    
    def display_story(self, story: InAppStory):
        """Display story in UI."""
        # This would integrate with the UI to show the story
        self.displayed_stories.append({
            'story': story,
            'displayed_at': datetime.now()
        })
    
    def is_available(self) -> bool:
        """In-app delivery is always available."""
        return True
    
    def get_pending_stories(self) -> List[InAppStory]:
        """Get stories waiting to be displayed."""
        return [
            item['story'] for item in self.story_queue
            if not item['displayed']
        ]
    
    def mark_as_read(self, story_id: str):
        """Mark story as read."""
        for item in self.story_queue:
            if id(item['story']) == story_id:
                item['displayed'] = True
                break


class EmailDelivery(DeliveryChannel):
    """Email story delivery."""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        self.smtp_config = smtp_config or {}
        self.sent_emails = []
    
    def deliver(self, content: EmailContent, settings: Dict[str, Any]) -> bool:
        """Send story via email."""
        try:
            if not settings.get('enabled', False):
                return False
            
            email_address = settings.get('address')
            if not email_address:
                logger.warning("No email address provided")
                return False
            
            # In production, this would use actual SMTP
            # For now, we'll simulate email sending
            self.sent_emails.append({
                'to': email_address,
                'subject': content.subject,
                'content': content,
                'sent_at': datetime.now()
            })
            
            logger.info(f"Email sent to {email_address}: {content.subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if email is configured."""
        return bool(self.smtp_config)
    
    def create_mime_message(self, content: EmailContent, to_address: str) -> MIMEMultipart:
        """Create MIME message for email."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = content.subject
        msg['From'] = self.smtp_config.get('from_address', 'health@example.com')
        msg['To'] = to_address
        
        # Add plain text part
        text_part = MIMEText(content.plain_body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(content.html_body, 'html')
        msg.attach(html_part)
        
        return msg


class PushNotificationDelivery(DeliveryChannel):
    """Push notification delivery."""
    
    def __init__(self, push_service_config: Optional[Dict[str, Any]] = None):
        self.push_service_config = push_service_config or {}
        self.sent_notifications = []
    
    def deliver(self, content: PushNotification, settings: Dict[str, Any]) -> bool:
        """Send push notification."""
        try:
            if not settings.get('enabled', False):
                return False
            
            # In production, this would use actual push service
            # For now, we'll simulate notification sending
            self.sent_notifications.append({
                'notification': content,
                'sent_at': datetime.now(),
                'settings': settings
            })
            
            logger.info(f"Push notification sent: {content.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if push service is configured."""
        return bool(self.push_service_config)


class StoryDeliveryManager:
    """Manages story delivery across multiple channels."""
    
    def __init__(self):
        self.delivery_channels = {
            'in_app': InAppDelivery(),
            'email': EmailDelivery(),
            'push': PushNotificationDelivery()
        }
        self.scheduler = DeliveryScheduler()
        self.formatter = StoryFormatter()
    
    def deliver_story(self, story: Story, user_preferences: DeliveryPreferences):
        """Deliver story through preferred channels."""
        delivered_channels = []
        
        # Format for each channel
        formatted_stories = {
            'in_app': self.formatter.format_for_app(story),
            'email': self.formatter.format_for_email(story),
            'push': self.formatter.create_push_summary(story)
        }
        
        # Deliver to enabled channels
        for channel, enabled in user_preferences.channels.items():
            if enabled and channel in self.delivery_channels:
                channel_obj = self.delivery_channels[channel]
                if channel_obj.is_available():
                    content = formatted_stories.get(channel)
                    settings = user_preferences.get_channel_settings(channel)
                    
                    if channel_obj.deliver(content, settings):
                        delivered_channels.append(channel)
        
        # Log delivery
        self.log_delivery(story, delivered_channels)
        
        return delivered_channels
    
    def schedule_delivery(self, story: Story, user_preferences: DeliveryPreferences, 
                         delivery_time: Optional[datetime] = None):
        """Schedule story for future delivery."""
        if delivery_time is None:
            delivery_time = self.calculate_optimal_delivery_time(user_preferences)
        
        self.scheduler.schedule(
            story=story,
            preferences=user_preferences,
            delivery_time=delivery_time,
            callback=lambda: self.deliver_story(story, user_preferences)
        )
    
    def calculate_optimal_delivery_time(self, preferences: DeliveryPreferences) -> datetime:
        """Calculate optimal delivery time based on preferences."""
        now = datetime.now()
        
        # Use preferred push time if available
        if preferences.push_time:
            delivery_date = now.date()
            if now.time() > preferences.push_time:
                # Schedule for tomorrow
                delivery_date = now.date() + timedelta(days=1)
            
            return datetime.combine(delivery_date, preferences.push_time)
        
        # Default to 9 AM next day
        return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    def log_delivery(self, story: Story, channels: List[str]):
        """Log story delivery for analytics."""
        log_entry = {
            'story_type': story.type.value if story.type else 'unknown',
            'delivered_at': datetime.now().isoformat(),
            'channels': channels,
            'word_count': story.metadata.word_count if story.metadata else 0
        }
        
        logger.info(f"Story delivered: {json.dumps(log_entry)}")
    
    def get_delivery_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get delivery history for user."""
        history = []
        
        # Collect from all channels
        for channel_name, channel in self.delivery_channels.items():
            if hasattr(channel, 'sent_emails'):
                history.extend([
                    {'channel': 'email', 'item': item}
                    for item in channel.sent_emails
                ])
            elif hasattr(channel, 'sent_notifications'):
                history.extend([
                    {'channel': 'push', 'item': item}
                    for item in channel.sent_notifications
                ])
            elif hasattr(channel, 'displayed_stories'):
                history.extend([
                    {'channel': 'in_app', 'item': item}
                    for item in channel.displayed_stories
                ])
        
        # Sort by timestamp
        history.sort(key=lambda x: x['item'].get('sent_at', datetime.min), reverse=True)
        
        return history


class StoryFormatter:
    """Formats stories for different delivery channels."""
    
    def format_for_app(self, story: Story) -> InAppStory:
        """Format story for in-app display."""
        sections = self.create_card_sections(story)
        visuals = self.generate_story_visuals(story)
        actions = self.create_story_actions(story)
        
        # Determine priority based on story type
        priority_map = {
            StoryType.MILESTONE_CELEBRATION: 9,
            StoryType.YEAR_IN_REVIEW: 8,
            StoryType.MONTHLY_JOURNEY: 6,
            StoryType.WEEKLY_RECAP: 5
        }
        
        return InAppStory(
            title=story.title,
            sections=sections,
            visuals=visuals,
            actions=actions,
            display_priority=priority_map.get(story.type, 5)
        )
    
    def create_card_sections(self, story: Story) -> List[CardSection]:
        """Create card sections from story."""
        sections = []
        
        # Title section
        sections.append(CardSection(
            type='text',
            content=story.title,
            metadata={'style': 'title'}
        ))
        
        # Main content sections
        for section_name, content in story.sections.items():
            if content and section_name != 'title':
                card_section = CardSection(
                    type='text',
                    title=section_name.replace('_', ' ').title(),
                    content=content[:200] + '...' if len(content) > 200 else content,
                    expandable=len(content) > 200,
                    expanded_content=content if len(content) > 200 else None
                )
                sections.append(card_section)
        
        # Insights section
        if story.insights:
            for insight in story.insights[:2]:  # Top 2 insights
                sections.append(CardSection(
                    type='insight',
                    content=insight.text,
                    metadata={'importance': insight.importance}
                ))
        
        # Recommendations section
        if story.recommendations:
            for rec in story.recommendations[:2]:  # Top 2 recommendations
                sections.append(CardSection(
                    type='recommendation',
                    content=rec.action,
                    metadata={
                        'rationale': rec.rationale,
                        'difficulty': rec.difficulty
                    }
                ))
        
        return sections
    
    def generate_story_visuals(self, story: Story) -> List[StoryVisual]:
        """Generate visual elements for story."""
        visuals = []
        
        # Add celebration icon for milestones
        if story.type == StoryType.MILESTONE_CELEBRATION:
            visuals.append(StoryVisual(
                type='celebration',
                data={'animation': 'confetti'},
                position='header',
                size='large'
            ))
        
        # Add mini charts for weekly/monthly stories
        if story.type in [StoryType.WEEKLY_RECAP, StoryType.MONTHLY_JOURNEY]:
            visuals.append(StoryVisual(
                type='chart',
                data={'chart_type': 'trend_line', 'metrics': []},
                position='inline',
                size='medium'
            ))
        
        return visuals
    
    def create_story_actions(self, story: Story) -> List[StoryAction]:
        """Create interactive actions for story."""
        actions = []
        
        # Share action
        actions.append(StoryAction(
            type='share',
            label='Share',
            action='share_story',
            style='secondary',
            data={'story_id': id(story)}
        ))
        
        # View details action
        if story.type != StoryType.MILESTONE_CELEBRATION:
            actions.append(StoryAction(
                type='button',
                label='View Details',
                action='view_full_story',
                style='primary',
                data={'story_id': id(story)}
            ))
        
        # Dismiss action
        actions.append(StoryAction(
            type='button',
            label='Dismiss',
            action='dismiss_story',
            style='text',
            data={'story_id': id(story)}
        ))
        
        return actions
    
    def format_for_email(self, story: Story) -> EmailContent:
        """Format story for email delivery."""
        html_content = self.render_email_template(story)
        plain_content = self.create_plain_text_version(story)
        
        return EmailContent(
            subject=self.generate_email_subject(story),
            html_body=html_content,
            plain_body=plain_content
        )
    
    def render_email_template(self, story: Story) -> str:
        """Render HTML email template."""
        # Simple HTML template
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<style>',
            'body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }',
            '.container { max-width: 600px; margin: 0 auto; padding: 20px; }',
            'h1 { color: #FF8C42; }',
            'h2 { color: #5D4E37; margin-top: 30px; }',
            '.insight { background: #FFF8F0; padding: 15px; margin: 10px 0; border-left: 4px solid #FFD166; }',
            '.recommendation { background: #F5E6D3; padding: 15px; margin: 10px 0; border-left: 4px solid #FF8C42; }',
            '.footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; }',
            '</style>',
            '</head>',
            '<body>',
            '<div class="container">',
            f'<h1>{story.title}</h1>'
        ]
        
        # Add sections
        for section_name, content in story.sections.items():
            if content:
                html_parts.extend([
                    f'<h2>{section_name.replace("_", " ").title()}</h2>',
                    f'<p>{content}</p>'
                ])
        
        # Add insights
        if story.insights:
            html_parts.append('<h2>Key Insights</h2>')
            for insight in story.insights:
                html_parts.append(
                    f'<div class="insight">{insight.text}</div>'
                )
        
        # Add recommendations
        if story.recommendations:
            html_parts.append('<h2>Recommendations</h2>')
            for rec in story.recommendations:
                html_parts.extend([
                    '<div class="recommendation">',
                    f'<strong>{rec.action}</strong><br>',
                    f'<em>{rec.rationale}</em>',
                    '</div>'
                ])
        
        # Footer
        html_parts.extend([
            '<div class="footer">',
            'Generated by Your Health Dashboard<br>',
            'To update your preferences, visit the app settings.',
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def create_plain_text_version(self, story: Story) -> str:
        """Create plain text version of story."""
        text_parts = [
            story.title,
            '=' * len(story.title),
            ''
        ]
        
        # Add sections
        for section_name, content in story.sections.items():
            if content:
                text_parts.extend([
                    section_name.replace('_', ' ').upper(),
                    '-' * len(section_name),
                    content,
                    ''
                ])
        
        # Add insights
        if story.insights:
            text_parts.extend([
                'KEY INSIGHTS',
                '-' * 12,
                ''
            ])
            for i, insight in enumerate(story.insights, 1):
                text_parts.append(f"{i}. {insight.text}")
            text_parts.append('')
        
        # Add recommendations
        if story.recommendations:
            text_parts.extend([
                'RECOMMENDATIONS',
                '-' * 15,
                ''
            ])
            for i, rec in enumerate(story.recommendations, 1):
                text_parts.extend([
                    f"{i}. {rec.action}",
                    f"   ({rec.rationale})",
                    ''
                ])
        
        # Footer
        text_parts.extend([
            '-' * 40,
            'Generated by Your Health Dashboard',
            'To update your preferences, visit the app settings.'
        ])
        
        return '\n'.join(text_parts)
    
    def generate_email_subject(self, story: Story) -> str:
        """Generate email subject line."""
        subject_templates = {
            StoryType.WEEKLY_RECAP: "Your Weekly Health Summary - {date}",
            StoryType.MONTHLY_JOURNEY: "Your {month} Health Journey",
            StoryType.YEAR_IN_REVIEW: "Your {year} Year in Review",
            StoryType.MILESTONE_CELEBRATION: "🎉 Milestone Achieved: {achievement}"
        }
        
        template = subject_templates.get(
            story.type,
            "Your Health Story"
        )
        
        # Format with appropriate data
        if story.metadata:
            period = story.metadata.data_period
            if story.type == StoryType.WEEKLY_RECAP:
                date = period.get('end_date', datetime.now()).strftime('%b %d')
                return template.format(date=date)
            elif story.type == StoryType.MONTHLY_JOURNEY:
                month = period.get('month', datetime.now().strftime('%B'))
                return template.format(month=month)
            elif story.type == StoryType.YEAR_IN_REVIEW:
                year = period.get('year', datetime.now().year)
                return template.format(year=year)
        
        return template
    
    def create_push_summary(self, story: Story) -> PushNotification:
        """Create push notification summary."""
        # Create concise summary
        if story.type == StoryType.MILESTONE_CELEBRATION:
            title = "🎉 Milestone Achieved!"
            body = story.insights[0].text if story.insights else "Check out your achievement!"
            priority = 'high'
        elif story.type == StoryType.WEEKLY_RECAP:
            title = "Your Weekly Summary"
            body = f"Ready to review? {story.title}"
            priority = 'normal'
        elif story.type == StoryType.MONTHLY_JOURNEY:
            title = "Monthly Journey Available"
            body = "Your monthly health story is ready"
            priority = 'normal'
        else:
            title = "New Health Story"
            body = story.title
            priority = 'normal'
        
        return PushNotification(
            title=title,
            body=body[:100],  # Limit to 100 chars
            action='open_story',
            data={'story_id': id(story), 'story_type': story.type.value},
            priority=priority
        )


class DeliveryScheduler:
    """Schedules story deliveries."""
    
    def __init__(self):
        self.scheduled_deliveries = []
    
    def schedule(self, story: Story, preferences: DeliveryPreferences,
                 delivery_time: datetime, callback):
        """Schedule a story delivery."""
        self.scheduled_deliveries.append({
            'story': story,
            'preferences': preferences,
            'delivery_time': delivery_time,
            'callback': callback,
            'scheduled_at': datetime.now(),
            'delivered': False
        })
        
        logger.info(f"Story scheduled for delivery at {delivery_time}")
    
    def check_pending_deliveries(self) -> List[Dict[str, Any]]:
        """Check for deliveries that should be sent now."""
        now = datetime.now()
        pending = []
        
        for delivery in self.scheduled_deliveries:
            if not delivery['delivered'] and delivery['delivery_time'] <= now:
                pending.append(delivery)
        
        return pending
    
    def execute_pending_deliveries(self):
        """Execute all pending deliveries."""
        pending = self.check_pending_deliveries()
        
        for delivery in pending:
            try:
                delivery['callback']()
                delivery['delivered'] = True
                logger.info(f"Scheduled delivery executed for {delivery['story'].title}")
            except Exception as e:
                logger.error(f"Failed to execute scheduled delivery: {e}")
    
    def cancel_delivery(self, story_id: str):
        """Cancel a scheduled delivery."""
        self.scheduled_deliveries = [
            d for d in self.scheduled_deliveries
            if id(d['story']) != story_id
        ]