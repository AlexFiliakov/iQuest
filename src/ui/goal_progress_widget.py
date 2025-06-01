"""
Goal Progress Widget for displaying goal tracking and progress.
Provides visual representation of different goal types.
"""

import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPalette, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..analytics.goal_management_system import GoalManagementSystem
from ..analytics.goal_models import Goal, GoalProgress, GoalStatus, GoalType


class CircularProgressBar(QWidget):
    """Custom circular progress bar widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.maximum = 100
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        
        # Colors
        self.progress_color = QColor('#4CAF50')
        self.background_color = QColor('#E0E0E0')
        self.text_color = QColor('#333333')
        
    def setValue(self, value: int):
        """Set the progress value."""
        self.value = min(value, self.maximum)
        self.update()
    
    def setMaximum(self, maximum: int):
        """Set the maximum value."""
        self.maximum = maximum
        self.update()
    
    def setColor(self, color: QColor):
        """Set the progress color."""
        self.progress_color = color
        self.update()
    
    def paintEvent(self, event):
        """Paint the circular progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Set up the painting area
        painter.translate(width / 2, height / 2)
        painter.scale(side / 100.0, side / 100.0)
        
        # Draw background circle
        painter.setPen(QPen(self.background_color, 8, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(-35, -35, 70, 70)
        
        # Draw progress arc
        if self.value > 0:
            painter.setPen(QPen(self.progress_color, 8, Qt.PenStyle.SolidLine))
            span_angle = int(360 * self.value / self.maximum)
            painter.drawArc(-35, -35, 70, 70, 90 * 16, -span_angle * 16)
        
        # Draw percentage text
        painter.setPen(self.text_color)
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        percentage = int(self.value * 100 / self.maximum) if self.maximum > 0 else 0
        painter.drawText(-20, 5, f"{percentage}%")


class MiniLineChart(QWidget):
    """Mini line chart for trend visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.target_line = None
        self.milestones = []
        self.setMinimumSize(200, 80)
        self.setMaximumSize(400, 100)
    
    def set_data(self, data: List[float]):
        """Set chart data."""
        self.data = data
        self.update()
    
    def add_target_line(self, target: float):
        """Add a target reference line."""
        self.target_line = target
        self.update()
    
    def highlight_milestones(self, milestones: List[int]):
        """Highlight milestone points."""
        self.milestones = milestones
        self.update()
    
    def paintEvent(self, event):
        """Paint the line chart."""
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width() - 20
        height = self.height() - 20
        margin = 10
        
        # Find data range
        min_val = min(self.data) if self.data else 0
        max_val = max(self.data) if self.data else 1
        if self.target_line:
            max_val = max(max_val, self.target_line)
        
        value_range = max_val - min_val
        if value_range == 0:
            value_range = 1
        
        # Draw target line if present
        if self.target_line is not None:
            painter.setPen(QPen(QColor('#FFA726'), 1, Qt.PenStyle.DashLine))
            y = margin + height - ((self.target_line - min_val) / value_range * height)
            painter.drawLine(margin, int(y), margin + width, int(y))
        
        # Draw the line chart
        painter.setPen(QPen(QColor('#4CAF50'), 2))
        
        points = []
        for i, value in enumerate(self.data):
            x = margin + (i / (len(self.data) - 1) * width if len(self.data) > 1 else 0)
            y = margin + height - ((value - min_val) / value_range * height)
            points.append((int(x), int(y)))
        
        # Draw lines
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Draw points
        painter.setBrush(QBrush(QColor('#4CAF50')))
        for i, (x, y) in enumerate(points):
            if i in self.milestones:
                painter.setBrush(QBrush(QColor('#FFA726')))
                painter.drawEllipse(x - 4, y - 4, 8, 8)
                painter.setBrush(QBrush(QColor('#4CAF50')))
            else:
                painter.drawEllipse(x - 3, y - 3, 6, 6)


class GoalCard(QFrame):
    """Individual goal card widget."""
    
    clicked = pyqtSignal(Goal)
    edit_requested = pyqtSignal(Goal)
    delete_requested = pyqtSignal(Goal)
    
    def __init__(self, goal: Goal, progress: GoalProgress, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.progress = progress
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Set up the goal card UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            GoalCard {
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                background-color: #ffffff;
                padding: 16px;
            }
            GoalCard:hover {
                background-color: #f5f5f5;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with goal name and menu
        header_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.goal.name)
        self.name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.name_label.setWordWrap(True)
        header_layout.addWidget(self.name_label)
        
        self.menu_button = QPushButton("⋮")
        self.menu_button.setMaximumSize(20, 20)
        self.menu_button.clicked.connect(self.show_menu)
        header_layout.addWidget(self.menu_button)
        
        layout.addLayout(header_layout)
        
        # Progress section
        progress_layout = QHBoxLayout()
        
        # Circular progress or other visualization based on goal type
        if self.goal.goal_type in [GoalType.TARGET, GoalType.IMPROVEMENT]:
            self.progress_widget = CircularProgressBar()
            progress_layout.addWidget(self.progress_widget)
        else:
            # For consistency and habit goals, show different visualization
            self.progress_widget = self.create_alternative_progress()
            progress_layout.addWidget(self.progress_widget)
        
        # Progress details
        details_layout = QVBoxLayout()
        
        self.value_label = QLabel(self)
        self.value_label.setFont(QFont("Arial", 9))
        details_layout.addWidget(self.value_label)
        
        self.status_label = QLabel(self)
        self.status_label.setFont(QFont("Arial", 8))
        details_layout.addWidget(self.status_label)
        
        if hasattr(self.goal, 'end_date') and self.goal.end_date:
            days_left = (self.goal.end_date - date.today()).days
            self.deadline_label = QLabel(f"{days_left} days left")
            self.deadline_label.setFont(QFont("Arial", 8))
            self.deadline_label.setStyleSheet("color: #666;")
            details_layout.addWidget(self.deadline_label)
        
        progress_layout.addLayout(details_layout)
        progress_layout.addStretch()
        
        layout.addLayout(progress_layout)
        
        # Mini trend chart
        self.trend_chart = MiniLineChart()
        # self.trend_chart.setMaximumHeight(60)
        layout.addWidget(self.trend_chart)
        
        # Make card clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def create_alternative_progress(self) -> QWidget:
        """Create alternative progress visualization for non-circular goals."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        if self.goal.goal_type == GoalType.CONSISTENCY:
            # Show dots for days of the week
            dots_layout = QHBoxLayout()
            for i in range(7):
                dot = QLabel("●")
                if i < int(self.progress.value):
                    dot.setStyleSheet("color: #4CAF50;")
                else:
                    dot.setStyleSheet("color: #E0E0E0;")
                dots_layout.addWidget(dot)
            layout.addLayout(dots_layout)
            
        elif self.goal.goal_type == GoalType.HABIT:
            # Show streak counter
            streak_label = QLabel(f"🔥 {int(self.progress.value)}")
            streak_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(streak_label)
        
        return widget
    
    def update_display(self):
        """Update the display with current progress."""
        # Update progress widget
        if hasattr(self.progress_widget, 'setValue'):
            self.progress_widget.setValue(int(self.progress.progress_percentage))
            
            # Update color based on progress
            if self.progress.progress_percentage >= 100:
                self.progress_widget.setColor(QColor('#4CAF50'))
            elif self.progress.progress_percentage >= 75:
                self.progress_widget.setColor(QColor('#8BC34A'))
            elif self.progress.progress_percentage >= 50:
                self.progress_widget.setColor(QColor('#FFA726'))
            else:
                self.progress_widget.setColor(QColor('#EF5350'))
        
        # Update value label
        if self.goal.goal_type == GoalType.TARGET:
            self.value_label.setText(f"{self.progress.value:.0f} / {self.goal.target_value:.0f}")
        elif self.goal.goal_type == GoalType.CONSISTENCY:
            self.value_label.setText(f"{int(self.progress.value)} / {self.goal.frequency} days")
        elif self.goal.goal_type == GoalType.IMPROVEMENT:
            improvement = ((self.progress.value - self.goal.baseline_value) / self.goal.baseline_value) * 100
            self.value_label.setText(f"{improvement:+.1f}%")
        elif self.goal.goal_type == GoalType.HABIT:
            self.value_label.setText(f"Day {int(self.progress.value)} of {self.goal.target_days}")
        
        # Update status
        if self.goal.status == GoalStatus.ACTIVE:
            if self.progress.progress_percentage >= 100:
                self.status_label.setText("✓ Complete")
                self.status_label.setStyleSheet("color: #4CAF50;")
            else:
                self.status_label.setText("In Progress")
                self.status_label.setStyleSheet("color: #2196F3;")
        else:
            self.status_label.setText(self.goal.status.value.title())
            self.status_label.setStyleSheet("color: #666;")
    
    def set_trend_data(self, data: List[float]):
        """Set trend data for the mini chart."""
        self.trend_chart.set_data(data)
        if hasattr(self.goal, 'target_value'):
            self.trend_chart.add_target_line(self.goal.target_value)
    
    def show_menu(self):
        """Show context menu for goal actions."""
        menu = QMenu(self)
        
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self.clicked.emit(self.goal))
        
        edit_action = menu.addAction("Edit Goal")
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.goal))
        
        menu.addSeparator()
        
        if self.goal.status == GoalStatus.ACTIVE:
            pause_action = menu.addAction("Pause Goal")
            pause_action.triggered.connect(lambda: self.pause_goal())
        else:
            resume_action = menu.addAction("Resume Goal")
            resume_action.triggered.connect(lambda: self.resume_goal())
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Goal")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.goal))
        
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
    
    def pause_goal(self):
        """Pause the goal."""
        # This would be handled by the parent widget
        pass
    
    def resume_goal(self):
        """Resume the goal."""
        # This would be handled by the parent widget
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.goal)
        super().mousePressEvent(event)


class GoalProgressWidget(QWidget):
    """Main widget for displaying goal progress and management."""
    
    goal_selected = pyqtSignal(Goal)
    refresh_requested = pyqtSignal()
    
    def __init__(self, goal_system: GoalManagementSystem, parent=None):
        super().__init__(parent)
        self.goal_system = goal_system
        self.goal_cards = {}
        self.setup_ui()
        self.load_goals()
        
        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_progress)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Your Goals")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add goal button
        add_button = QPushButton("+ New Goal")
        add_button.clicked.connect(self.show_new_goal_dialog)
        header_layout.addWidget(add_button)
        
        # Analyze relationships button
        analyze_button = QPushButton("Analyze Goals")
        analyze_button.clicked.connect(self.analyze_relationships)
        header_layout.addWidget(analyze_button)
        
        layout.addLayout(header_layout)
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        
        self.filter_buttons = {
            'all': self.create_filter_button("All", True),
            'active': self.create_filter_button("Active"),
            'completed': self.create_filter_button("Completed"),
            'paused': self.create_filter_button("Paused")
        }
        
        for button in self.filter_buttons.values():
            filter_layout.addWidget(button)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Scroll area for goals
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.goals_container = QWidget(self)
        self.goals_layout = QGridLayout(self.goals_container)
        self.goals_layout.setSpacing(12)
        
        scroll_area.setWidget(self.goals_container)
        layout.addWidget(scroll_area)
        
        # Summary section
        self.summary_widget = self.create_summary_widget()
        layout.addWidget(self.summary_widget)
    
    def create_filter_button(self, text: str, checked: bool = False) -> QPushButton:
        """Create a filter toggle button."""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(checked)
        button.clicked.connect(self.apply_filters)
        return button
    
    def create_summary_widget(self) -> QWidget:
        """Create summary statistics widget."""
        widget = QFrame(self)
        widget.setFrameStyle(QFrame.Shape.Box)
        # widget.setMaximumHeight(80)
        
        layout = QHBoxLayout(widget)
        
        # Active goals
        self.active_count_label = QLabel("0")
        self.active_count_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.active_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        active_layout = QVBoxLayout()
        active_layout.addWidget(self.active_count_label)
        active_layout.addWidget(QLabel("Active Goals"))
        
        # Completed this week
        self.completed_week_label = QLabel("0")
        self.completed_week_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.completed_week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        completed_layout = QVBoxLayout()
        completed_layout.addWidget(self.completed_week_label)
        completed_layout.addWidget(QLabel("Completed This Week"))
        
        # Average progress
        self.avg_progress_label = QLabel("0%")
        self.avg_progress_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.avg_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.avg_progress_label)
        progress_layout.addWidget(QLabel("Average Progress"))
        
        layout.addLayout(active_layout)
        layout.addLayout(completed_layout)
        layout.addLayout(progress_layout)
        
        return widget
    
    def load_goals(self):
        """Load and display goals."""
        # Clear existing cards
        for card in self.goal_cards.values():
            card.deleteLater()
        self.goal_cards.clear()
        
        # Get goals
        goals = self.goal_system.get_active_goals()
        
        # Create cards
        row = 0
        col = 0
        for goal in goals:
            progress = self.goal_system.progress_tracker.get_current_progress(goal)
            
            card = GoalCard(goal, progress)
            card.clicked.connect(self.on_goal_clicked)
            card.edit_requested.connect(self.edit_goal)
            card.delete_requested.connect(self.delete_goal)
            
            # Load trend data
            history = self.goal_system.progress_tracker.get_progress_history(goal.id, days=30)
            if history:
                trend_data = [p.value for p in history[-7:]]  # Last 7 days
                card.set_trend_data(trend_data)
            
            self.goals_layout.addWidget(card, row, col)
            self.goal_cards[goal.id] = card
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        # Add stretch to push cards to top
        self.goals_layout.setRowStretch(row + 1, 1)
        
        # Update summary
        self.update_summary()
    
    def refresh_progress(self):
        """Refresh progress for all goals."""
        for goal_id, card in self.goal_cards.items():
            goal = self.goal_system.get_goal_by_id(goal_id)
            if goal:
                progress = self.goal_system.progress_tracker.get_current_progress(goal)
                card.progress = progress
                card.update_display()
        
        self.update_summary()
    
    def update_summary(self):
        """Update summary statistics."""
        active_goals = self.goal_system.get_active_goals()
        self.active_count_label.setText(str(len(active_goals)))
        
        # Calculate completed this week
        # This would query the database for recently completed goals
        self.completed_week_label.setText("0")  # Placeholder
        
        # Calculate average progress
        if active_goals:
            total_progress = sum(
                self.goal_system.progress_tracker.get_current_progress(g).progress_percentage
                for g in active_goals
            )
            avg_progress = total_progress / len(active_goals)
            self.avg_progress_label.setText(f"{avg_progress:.0f}%")
        else:
            self.avg_progress_label.setText("0%")
    
    def apply_filters(self):
        """Apply filter to displayed goals."""
        # This would filter the displayed goals based on selected filters
        pass
    
    def show_new_goal_dialog(self):
        """Show dialog to create a new goal."""
        # This would open a dialog for creating a new goal
        pass
    
    def analyze_relationships(self):
        """Analyze and display goal relationships."""
        analysis = self.goal_system.analyze_goal_relationships()
        
        # Show results in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Goal Relationships")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        
        # Format the analysis results
        text = "Goal Relationship Analysis\n\n"
        
        if analysis['relationships']:
            text += "Relationships Found:\n"
            for rel in analysis['relationships']:
                text += f"- {rel.description}\n"
                text += f"  Strength: {rel.strength:.2f}\n\n"
        else:
            text += "No significant relationships found between your goals.\n\n"
        
        if analysis['recommendations']:
            text += "\nRecommendations:\n"
            for rec in analysis['recommendations']:
                text += f"- {rec}\n"
        
        text_edit.setText(text)
        layout.addWidget(text_edit)
        
        dialog.exec()
    
    def on_goal_clicked(self, goal: Goal):
        """Handle goal selection."""
        self.goal_selected.emit(goal)
    
    def edit_goal(self, goal: Goal):
        """Edit a goal."""
        # This would open an edit dialog
        pass
    
    def delete_goal(self, goal: Goal):
        """Delete a goal."""
        # This would confirm and delete the goal
        pass