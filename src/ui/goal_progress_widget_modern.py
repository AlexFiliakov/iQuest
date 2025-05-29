"""
Modern Goal Progress Widget with updated styling and animations.
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMenu, QDialog, QTextEdit,
    QProgressBar, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPalette, QLinearGradient
import math
from datetime import date, timedelta

from ..analytics.goal_models import Goal, GoalType, GoalStatus, GoalProgress
from ..analytics.goal_management_system import GoalManagementSystem
from .style_manager import StyleManager


class ModernCircularProgressBar(QWidget):
    """Modern circular progress bar with gradient and animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.maximum = 100
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)
        
        self.style_manager = StyleManager()
        
        # Modern colors
        self.progress_color = QColor(self.style_manager.ACCENT_SUCCESS)
        self.background_color = QColor(self.style_manager.TERTIARY_BG)
        self.text_color = QColor(self.style_manager.TEXT_PRIMARY)
        
        # Animation
        self._animated_value = 0
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(800)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    @property
    def animated_value(self):
        return self._animated_value
        
    @animated_value.setter
    def animated_value(self, value):
        self._animated_value = value
        self.update()
        
    def setValue(self, value: int, animate: bool = True):
        """Set the progress value with animation."""
        target_value = min(value, self.maximum)
        
        if animate:
            self.animation.setStartValue(self.value)
            self.animation.setEndValue(target_value)
            self.animation.start()
        else:
            self._animated_value = target_value
            self.update()
            
        self.value = target_value
    
    def setMaximum(self, maximum: int):
        """Set the maximum value."""
        self.maximum = maximum
        self.update()
    
    def setColor(self, color: QColor):
        """Set the progress color."""
        self.progress_color = color
        self.update()
    
    def paintEvent(self, event):
        """Paint the modern circular progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Set up the painting area
        painter.translate(width / 2, height / 2)
        painter.scale(side / 120.0, side / 120.0)
        
        # Draw background circle with gradient
        gradient = QLinearGradient(-60, -60, 60, 60)
        gradient.setColorAt(0, self.background_color.lighter(105))
        gradient.setColorAt(1, self.background_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(-50, -50, 100, 100)
        
        # Draw progress arc
        if self._animated_value > 0:
            # Create gradient for progress
            progress_gradient = QLinearGradient(-60, -60, 60, 60)
            progress_gradient.setColorAt(0, self.progress_color.lighter(120))
            progress_gradient.setColorAt(1, self.progress_color)
            
            painter.setPen(QPen(QBrush(progress_gradient), 12, Qt.PenStyle.SolidLine, 
                               Qt.PenCapStyle.RoundCap))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            span_angle = int(360 * self._animated_value / self.maximum)
            painter.drawArc(-40, -40, 80, 80, 90 * 16, -span_angle * 16)
        
        # Draw inner circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(-35, -35, 70, 70)
        
        # Draw percentage text
        painter.setPen(self.text_color)
        painter.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        percentage = int(self._animated_value * 100 / self.maximum) if self.maximum > 0 else 0
        painter.drawText(QRect(-30, -10, 60, 20), Qt.AlignmentFlag.AlignCenter, f"{percentage}%")
        
        # Draw label
        painter.setFont(QFont("Inter", 10))
        painter.setPen(QColor(self.style_manager.TEXT_SECONDARY))
        painter.drawText(QRect(-30, 10, 60, 20), Qt.AlignmentFlag.AlignCenter, "Complete")


class ModernGoalCard(QFrame):
    """Modern goal card with clean design and animations."""
    
    clicked = pyqtSignal(Goal)
    
    def __init__(self, goal: Goal, goal_system: GoalManagementSystem, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.goal_system = goal_system
        self.style_manager = StyleManager()
        
        self.setup_ui()
        self.update_progress()
        
    def setup_ui(self):
        """Set up the modern goal card UI."""
        self.setObjectName("goalCard")
        self.setFixedHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Modern card styling
        self.setStyleSheet(f"""
            QFrame#goalCard {{
                background-color: {self.style_manager.PRIMARY_BG};
                border-radius: 12px;
                border: none;
                padding: 20px;
            }}
            QFrame#goalCard:hover {{
                background-color: {self.style_manager.TERTIARY_BG};
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - Goal info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # Goal name
        self.name_label = QLabel(self.goal.name)
        self.name_label.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        self.name_label.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.name_label)
        
        # Goal type and period
        type_text = self.goal.goal_type.value.replace('_', ' ').title()
        period_text = f"{self.goal.period_days} days"
        self.type_label = QLabel(f"{type_text} • {period_text}")
        self.type_label.setFont(QFont("Inter", 11))
        self.type_label.setStyleSheet(f"color: {self.style_manager.TEXT_SECONDARY};")
        info_layout.addWidget(self.type_label)
        
        # Progress details
        self.progress_label = QLabel()
        self.progress_label.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        info_layout.addWidget(self.progress_label)
        
        # Status indicator
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Inter", 11))
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)
        
        # Right side - Circular progress
        self.progress_bar = ModernCircularProgressBar()
        main_layout.addWidget(self.progress_bar)
        
    def update_progress(self):
        """Update the goal progress display."""
        progress = self.goal_system.get_goal_progress(self.goal.id)
        
        if progress:
            # Update progress bar
            percentage = int(progress.percentage)
            self.progress_bar.setValue(percentage)
            
            # Update progress label
            if self.goal.goal_type == GoalType.DAILY_AVERAGE:
                avg_text = f"{progress.current_value:.1f}" if progress.current_value else "0"
                self.progress_label.setText(f"Average: {avg_text} / {self.goal.target_value}")
            else:
                current_text = f"{progress.current_value:.0f}" if progress.current_value else "0"
                self.progress_label.setText(f"Progress: {current_text} / {self.goal.target_value}")
            
            # Update status with color
            if self.goal.status == GoalStatus.ACTIVE:
                if progress.is_on_track:
                    self.status_label.setText("✓ On Track")
                    self.status_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
                    self.progress_bar.setColor(QColor(self.style_manager.ACCENT_SUCCESS))
                else:
                    self.status_label.setText("⚠ Behind Schedule")
                    self.status_label.setStyleSheet(f"color: {self.style_manager.ACCENT_WARNING};")
                    self.progress_bar.setColor(QColor(self.style_manager.ACCENT_WARNING))
            elif self.goal.status == GoalStatus.COMPLETED:
                self.status_label.setText("🏆 Completed!")
                self.status_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
                self.progress_bar.setColor(QColor(self.style_manager.ACCENT_SUCCESS))
            elif self.goal.status == GoalStatus.FAILED:
                self.status_label.setText("✗ Not Achieved")
                self.status_label.setStyleSheet(f"color: {self.style_manager.ACCENT_ERROR};")
                self.progress_bar.setColor(QColor(self.style_manager.ACCENT_ERROR))
            
            # Style based on percentage
            if percentage >= 100:
                self.progress_label.setStyleSheet(f"color: {self.style_manager.ACCENT_SUCCESS};")
            elif percentage >= 70:
                self.progress_label.setStyleSheet(f"color: {self.style_manager.DATA_ORANGE};")
            else:
                self.progress_label.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.goal)
        super().mousePressEvent(event)


class ModernGoalProgressWidget(QWidget):
    """Modern goal progress widget with clean design."""
    
    goal_selected = pyqtSignal(Goal)
    
    def __init__(self, goal_system: GoalManagementSystem, parent=None):
        super().__init__(parent)
        self.goal_system = goal_system
        self.style_manager = StyleManager()
        self.goal_cards = []
        
        self.setup_ui()
        self.refresh_goals()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_goals)
        self.refresh_timer.start(60000)  # Refresh every minute
        
    def setup_ui(self):
        """Set up the modern UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        title = QLabel("Active Goals")
        title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.style_manager.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add goal button
        add_button = QPushButton("+ New Goal")
        add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.ACCENT_SECONDARY};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #1D4ED8;
            }}
            QPushButton:pressed {{
                background-color: #1E40AF;
            }}
        """)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self.show_add_goal_dialog)
        header_layout.addWidget(add_button)
        
        layout.addLayout(header_layout)
        
        # Scroll area for goals
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {self.style_manager.TERTIARY_BG};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.style_manager.TEXT_MUTED};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.style_manager.TEXT_SECONDARY};
            }}
        """)
        
        # Container for goal cards
        self.goals_container = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_container)
        self.goals_layout.setSpacing(12)
        self.goals_layout.setContentsMargins(0, 0, 8, 0)
        
        scroll.setWidget(self.goals_container)
        layout.addWidget(scroll)
        
    def refresh_goals(self):
        """Refresh the goals display."""
        # Clear existing cards
        for card in self.goal_cards:
            card.deleteLater()
        self.goal_cards.clear()
        
        # Get active goals
        active_goals = self.goal_system.get_active_goals()
        
        if not active_goals:
            # Show empty state
            empty_label = QLabel("No active goals. Click '+ New Goal' to create one!")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {self.style_manager.TEXT_MUTED};
                    font-size: 14px;
                    padding: 40px;
                    background-color: {self.style_manager.PRIMARY_BG};
                    border-radius: 12px;
                }}
            """)
            self.goals_layout.addWidget(empty_label)
            self.goal_cards.append(empty_label)
        else:
            # Create cards for each goal
            for goal in active_goals:
                card = ModernGoalCard(goal, self.goal_system)
                card.clicked.connect(self.goal_selected.emit)
                self.goals_layout.addWidget(card)
                self.goal_cards.append(card)
        
        self.goals_layout.addStretch()
        
    def show_add_goal_dialog(self):
        """Show dialog to add a new goal."""
        # TODO: Implement goal creation dialog
        pass