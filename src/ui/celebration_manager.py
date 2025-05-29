"""
Celebration Manager for Personal Records Tracker.
Handles confetti animations, achievement notifications, and celebration effects.
"""

import sys
import random
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import logging

from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QFrame, QPushButton, QApplication, QGraphicsEffect,
                            QGraphicsOpacityEffect, QMessageBox)
from PyQt6.QtCore import (QTimer, QPropertyAnimation, QEasingCurve, 
                         QParallelAnimationGroup, QSequentialAnimationGroup,
                         QRect, QPoint, QSize, pyqtSignal, QObject, QThread)
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QLinearGradient,
                        QFont, QFontMetrics, QPalette, QPixmap, QIcon)

from ..analytics.personal_records_tracker import Record, Achievement, CelebrationLevel, RecordType

logger = logging.getLogger(__name__)


@dataclass
class ConfettiConfig:
    """Configuration for confetti animation."""
    particle_count: int = 150
    duration: int = 3000  # milliseconds
    colors: List[str] = None
    gravity: float = 0.3
    wind: float = 0.1
    spread: float = 45
    size_range: Tuple[int, int] = (3, 8)
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = ["#5B6770", "#6C757D", "#ADB5BD", "#28A745", "#495057"]


@dataclass
class Particle:
    """A single confetti particle."""
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    size: int = 5
    color: str = "#FF8C42"
    rotation: float = 0.0
    rotation_speed: float = 0.0
    life: float = 1.0
    decay: float = 0.01


class ConfettiWidget(QWidget):
    """Widget that displays confetti animation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.config = ConfettiConfig()
        self.setStyleSheet("background: transparent;")
        
    def start_confetti(self, config: ConfettiConfig):
        """Start confetti animation with given configuration."""
        self.config = config
        self.particles = []
        self.create_particles()
        self.timer.start(16)  # ~60 FPS
        
        # Auto-stop after duration
        QTimer.singleShot(config.duration, self.stop_confetti)
        
    def create_particles(self):
        """Create initial particles."""
        widget_rect = self.rect()
        center_x = widget_rect.width() // 2
        
        for _ in range(self.config.particle_count):
            # Random spawn position at top of widget
            x = center_x + random.randint(-100, 100)
            y = random.randint(-50, 0)
            
            # Random velocity with spread
            angle = random.uniform(-self.config.spread, self.config.spread)
            speed = random.uniform(2, 8)
            vx = speed * math.sin(math.radians(angle)) + random.uniform(-self.config.wind, self.config.wind)
            vy = speed * math.cos(math.radians(angle))
            
            particle = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                size=random.randint(*self.config.size_range),
                color=random.choice(self.config.colors),
                rotation=random.uniform(0, 360),
                rotation_speed=random.uniform(-10, 10),
                life=1.0,
                decay=random.uniform(0.005, 0.02)
            )
            self.particles.append(particle)
    
    def update_particles(self):
        """Update particle positions and properties."""
        widget_rect = self.rect()
        
        for particle in self.particles[:]:  # Copy list to allow removal
            # Apply gravity
            particle.vy += self.config.gravity
            
            # Apply wind
            particle.vx += random.uniform(-self.config.wind/10, self.config.wind/10)
            
            # Update position
            particle.x += particle.vx
            particle.y += particle.vy
            
            # Update rotation
            particle.rotation += particle.rotation_speed
            
            # Update life
            particle.life -= particle.decay
            
            # Remove dead or off-screen particles
            if (particle.life <= 0 or 
                particle.y > widget_rect.height() + 50 or
                particle.x < -50 or 
                particle.x > widget_rect.width() + 50):
                self.particles.remove(particle)
        
        # Stop animation when no particles left
        if not self.particles:
            self.stop_confetti()
        
        self.update()  # Trigger repaint
    
    def stop_confetti(self):
        """Stop confetti animation."""
        self.timer.stop()
        self.particles = []
        self.update()
    
    def paintEvent(self, event):
        """Paint the confetti particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for particle in self.particles:
            # Set color with alpha based on life
            color = QColor(particle.color)
            color.setAlphaF(particle.life)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color))
            
            # Draw particle as small rectangle
            painter.save()
            painter.translate(particle.x, particle.y)
            painter.rotate(particle.rotation)
            painter.drawRect(-particle.size//2, -particle.size//2, particle.size, particle.size)
            painter.restore()


class AchievementNotificationWidget(QWidget):
    """Widget for displaying achievement notifications."""
    
    finished = pyqtSignal()
    
    def __init__(self, achievement: Achievement, parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the notification UI."""
        self.setFixedSize(350, 100)
        self.setStyleSheet("""
            QWidget {
                background-color: #F5E6D3;
                border: 2px solid #FF8C42;
                border-radius: 10px;
            }
            QLabel {
                color: #2D3142;
                background: transparent;
            }
        """)
        
        layout = QHBoxLayout()
        
        # Icon (placeholder for now)
        icon_label = QLabel("🏆")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedSize(50, 50)
        
        # Text content
        text_layout = QVBoxLayout()
        
        title_label = QLabel(f"Achievement Unlocked!")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        name_label = QLabel(self.achievement.name)
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        desc_label = QLabel(self.achievement.description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        
        self.setLayout(layout)
        
        # Setup animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
    def show_animated(self):
        """Show notification with animation."""
        self.show()
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Stay visible for 3 seconds, then fade out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self.finished.emit)
        
        # Create animation sequence
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(self.fade_in)
        self.animation_group.addPause(3000)  # Show for 3 seconds
        self.animation_group.addAnimation(self.fade_out)
        
        self.animation_group.start()


class CelebrationManager(QObject):
    """Manages celebrations for achievements and records."""
    
    celebration_triggered = pyqtSignal(str, dict)  # celebration_type, data
    
    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.confetti_widget = None
        self.notification_widgets = []
        self.sound_enabled = True
        self.animations_enabled = True
        
    def celebrate(self, record: Record, achievements: List[Achievement]):
        """Orchestrate celebration for new record."""
        try:
            # Determine celebration level
            level = self._determine_celebration_level(record, achievements)
            
            # Visual celebration
            if self.animations_enabled and level.value >= CelebrationLevel.MEDIUM.value:
                self._trigger_confetti(level, record)
            
            # Show achievement notifications
            for achievement in achievements:
                self._show_achievement_notification(achievement)
            
            # Emit signal for other components
            self.celebration_triggered.emit("record_achieved", {
                "record": record,
                "achievements": achievements,
                "level": level.name
            })
            
            logger.info(f"Celebration triggered for {record.metric} {record.record_type.value}")
            
        except Exception as e:
            logger.error(f"Error in celebration: {e}")
    
    def _determine_celebration_level(self, record: Record, achievements: List[Achievement]) -> CelebrationLevel:
        """Determine appropriate celebration level."""
        # High level for major milestones
        if any(a.rarity in ["legendary", "rare"] for a in achievements):
            return CelebrationLevel.LEGENDARY
        
        # High level for big improvements
        if record.improvement_margin and record.improvement_margin > 50:
            return CelebrationLevel.HIGH
        
        # High level for long streaks
        if record.record_type == RecordType.CONSISTENCY_STREAK and record.value >= 30:
            return CelebrationLevel.HIGH
        
        # Medium level for achievements or good improvements
        if achievements or (record.improvement_margin and record.improvement_margin > 20):
            return CelebrationLevel.MEDIUM
        
        # Low level for any record
        return CelebrationLevel.LOW
    
    def _trigger_confetti(self, level: CelebrationLevel, record: Record):
        """Trigger confetti animation."""
        if not self.parent_widget:
            return
            
        # Create confetti widget if doesn't exist
        if not self.confetti_widget:
            self.confetti_widget = ConfettiWidget(self.parent_widget)
            self.confetti_widget.resize(self.parent_widget.size())
            self.confetti_widget.move(0, 0)
        
        # Configure confetti based on level
        config = ConfettiConfig(
            particle_count=self._get_particle_count(level),
            duration=self._get_duration(level),
            colors=self._get_colors(record.metric),
            gravity=0.3,
            wind=0.1,
            spread=45
        )
        
        self.confetti_widget.start_confetti(config)
        self.confetti_widget.show()
        self.confetti_widget.raise_()  # Bring to front
    
    def _get_particle_count(self, level: CelebrationLevel) -> int:
        """Get particle count based on celebration level."""
        counts = {
            CelebrationLevel.LOW: 50,
            CelebrationLevel.MEDIUM: 100,
            CelebrationLevel.HIGH: 200,
            CelebrationLevel.LEGENDARY: 300
        }
        return counts.get(level, 100)
    
    def _get_duration(self, level: CelebrationLevel) -> int:
        """Get animation duration based on celebration level."""
        durations = {
            CelebrationLevel.LOW: 2000,
            CelebrationLevel.MEDIUM: 3000,
            CelebrationLevel.HIGH: 4000,
            CelebrationLevel.LEGENDARY: 5000
        }
        return durations.get(level, 3000)
    
    def _get_colors(self, metric: str) -> List[str]:
        """Get colors based on metric type."""
        # Metric-specific color schemes
        color_schemes = {
            "heart_rate": ["#FF6B6B", "#FFE66D", "#FF8E53"],
            "steps": ["#4ECDC4", "#45B7D1", "#96CEB4"],
            "weight": ["#DDA0DD", "#98D8C8", "#F7DC6F"],
            "sleep": ["#6C5CE7", "#A29BFE", "#FD79A8"],
            "default": ["#5B6770", "#6C757D", "#ADB5BD", "#28A745", "#495057"]
        }
        
        # Try to match metric to color scheme
        for key, colors in color_schemes.items():
            if key.lower() in metric.lower():
                return colors
        
        return color_schemes["default"]
    
    def _show_achievement_notification(self, achievement: Achievement):
        """Show achievement notification."""
        try:
            notification = AchievementNotificationWidget(achievement, self.parent_widget)
            
            # Position notification
            parent_rect = self.parent_widget.rect()
            notification_count = len(self.notification_widgets)
            y_offset = 20 + (notification_count * 120)  # Stack notifications
            
            notification.move(parent_rect.width() - 370, y_offset)
            
            # Connect cleanup
            notification.finished.connect(lambda: self._cleanup_notification(notification))
            
            # Show with animation
            notification.show_animated()
            self.notification_widgets.append(notification)
            
        except Exception as e:
            logger.error(f"Error showing achievement notification: {e}")
    
    def _cleanup_notification(self, notification: AchievementNotificationWidget):
        """Clean up finished notification."""
        if notification in self.notification_widgets:
            self.notification_widgets.remove(notification)
        notification.deleteLater()
    
    def resize_confetti(self):
        """Resize confetti widget when parent resizes."""
        if self.confetti_widget and self.parent_widget:
            self.confetti_widget.resize(self.parent_widget.size())
    
    def set_animations_enabled(self, enabled: bool):
        """Enable or disable animations."""
        self.animations_enabled = enabled
    
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable sound effects."""
        self.sound_enabled = enabled


class SocialShareManager:
    """Manages social sharing functionality for records."""
    
    def __init__(self):
        self.template_engine = ShareTemplateEngine()
    
    def create_share_text(self, record: Record, achievements: List[Achievement]) -> str:
        """Create shareable text for record."""
        try:
            # Create base message
            if record.record_type == RecordType.SINGLE_DAY_MAX:
                message = f"🎉 New personal best in {record.metric}: {record.value:.1f}!"
            elif record.record_type == RecordType.CONSISTENCY_STREAK:
                message = f"🔥 {int(record.value)}-day streak in {record.metric}!"
            else:
                message = f"📈 New {record.record_type.value.replace('_', ' ')} record in {record.metric}: {record.value:.1f}!"
            
            # Add improvement info
            if record.improvement_margin:
                message += f" ({record.improvement_margin:+.1f}% improvement)"
            
            # Add achievements
            if achievements:
                badge_names = [a.name for a in achievements]
                message += f"\n🏆 Unlocked: {', '.join(badge_names)}"
            
            # Add motivational quote
            quote = self._get_motivational_quote(record)
            if quote:
                message += f"\n\n💪 {quote}"
            
            # Add app signature
            message += "\n\n#HealthProgress #PersonalBest #AppleHealthMonitor"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating share text: {e}")
            return f"New personal record in {record.metric}! 🎉"
    
    def _get_motivational_quote(self, record: Record) -> str:
        """Get relevant motivational quote."""
        quotes = [
            "Progress, not perfection!",
            "Every step forward counts!",
            "Consistency is key to success!",
            "You're stronger than you think!",
            "Small improvements lead to big results!",
            "Keep pushing your limits!",
            "Your commitment is paying off!"
        ]
        return random.choice(quotes)
    
    def copy_to_clipboard(self, text: str):
        """Copy text to system clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            return True
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False


class ShareTemplateEngine:
    """Creates shareable content templates."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load message templates."""
        return {
            "single_day_max": "🎉 New personal best in {metric}: {value}! {improvement}",
            "single_day_min": "💪 New low in {metric}: {value}! {improvement}",
            "streak": "🔥 {value}-day streak in {metric}! {motivation}",
            "rolling_average": "📊 Best {window}-day average in {metric}: {value}! {improvement}",
            "default": "📈 New record in {metric}: {value}! {motivation}"
        }
    
    def get_template(self, record_type: RecordType) -> str:
        """Get template for record type."""
        template_key = record_type.value
        return self.templates.get(template_key, self.templates["default"])