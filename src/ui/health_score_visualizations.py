"""Visualization components for health score display."""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGridLayout, QFrame, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

from ..analytics.health_score import HealthScore, ComponentScore, TrendDirection


class AnimatedHealthScoreGauge(QWidget):
    """Animated circular gauge for health score display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self._target_score = 0
        self._animation = QPropertyAnimation(self, b"score")
        self._animation.setDuration(1000)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self.setMinimumSize(200, 200)
        self.setMaximumSize(300, 300)
    
    def set_score(self, score: float, animate: bool = True):
        """Set health score with optional animation."""
        self._target_score = score
        
        if animate:
            self._animation.setStartValue(self._score)
            self._animation.setEndValue(score)
            self._animation.start()
        else:
            self._score = score
            self.update()
    
    @pyqtProperty(float)
    def score(self):
        return self._score
    
    @score.setter
    def score(self, value):
        self._score = value
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 20
        
        # Draw background arc
        painter.setPen(QPen(QColor('#E0E0E0'), 15))
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            225 * 16, -270 * 16
        )
        
        # Draw score arc
        color = self._get_score_color(self._score)
        painter.setPen(QPen(color, 15))
        angle = int(-270 * (self._score / 100) * 16)
        painter.drawArc(
            center.x() - radius, center.y() - radius,
            radius * 2, radius * 2,
            225 * 16, angle
        )
        
        # Draw score text
        painter.setPen(QPen(color, 2))
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self._score)}")
        
        # Draw label
        font.setPointSize(14)
        font.setBold(False)
        painter.setFont(font)
        label_rect = QRect(rect.x(), rect.y() + 60, rect.width(), rect.height())
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "Health Score")
        
        # Draw category
        category = self._get_score_category(self._score)
        font.setPointSize(12)
        painter.setFont(font)
        category_rect = QRect(rect.x(), rect.y() + 80, rect.width(), rect.height())
        painter.drawText(category_rect, Qt.AlignmentFlag.AlignCenter, category)
    
    def _get_score_color(self, score: float) -> QColor:
        """Get color based on score value."""
        if score >= 80:
            return QColor('#4CAF50')  # Green
        elif score >= 60:
            return QColor('#FFC107')  # Amber
        else:
            return QColor('#F44336')  # Red
    
    def _get_score_category(self, score: float) -> str:
        """Get category name for score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Attention"


class ComponentScoreCard(QFrame):
    """Card widget for displaying component scores."""
    
    def __init__(self, component: str, score: ComponentScore, parent=None):
        super().__init__(parent)
        self.component = component
        self.score = score
        
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                background-color: white;
                padding: 16px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Component name
        name_label = QLabel(self.component.title())
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)
        
        # Score with progress bar
        score_layout = QHBoxLayout()
        
        score_label = QLabel(f"{self.score.score:.0f}")
        score_label.setStyleSheet(f"font-size: 24px; color: {self._get_color()};")
        score_layout.addWidget(score_label)
        
        progress = QProgressBar(self)
        progress.setRange(0, 100)
        progress.setValue(int(self.score.score))
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #F0F0F0;
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self._get_color()};
                border-radius: 5px;
            }}
        """)
        score_layout.addWidget(progress, 1)
        
        layout.addLayout(score_layout)
        
        # Weight and confidence
        info_label = QLabel(f"Weight: {self.score.weight:.0%} | Confidence: {self.score.confidence:.0%}")
        info_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(info_label)
        
        # Breakdown if available
        if self.score.breakdown:
            breakdown_label = QLabel("Breakdown:")
            breakdown_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
            layout.addWidget(breakdown_label)
            
            for sub_component, sub_score in self.score.breakdown.items():
                sub_layout = QHBoxLayout()
                sub_name = QLabel(sub_component.replace('_', ' ').title())
                sub_name.setStyleSheet("font-size: 12px;")
                sub_layout.addWidget(sub_name)
                
                sub_score_label = QLabel(f"{sub_score:.0f}")
                sub_score_label.setStyleSheet("font-size: 12px; font-weight: bold;")
                sub_layout.addWidget(sub_score_label)
                
                layout.addLayout(sub_layout)
        
        # Insights
        if self.score.insights:
            insights_label = QLabel("Insights:")
            insights_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
            layout.addWidget(insights_label)
            
            for insight in self.score.insights[:2]:  # Show max 2 insights
                insight_label = QLabel(f"• {insight}")
                insight_label.setWordWrap(True)
                insight_label.setStyleSheet("font-size: 12px; color: #666; margin-left: 10px;")
                layout.addWidget(insight_label)
    
    def _get_color(self) -> str:
        """Get color based on score."""
        if self.score.score >= 80:
            return '#4CAF50'
        elif self.score.score >= 60:
            return '#FFC107'
        else:
            return '#F44336'


class HealthScoreSunburstChart(FigureCanvas):
    """Sunburst chart showing score breakdown."""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 8))
        super().__init__(self.figure)
        self.setParent(parent)
    
    def update_chart(self, health_score: HealthScore):
        """Update chart with new health score data."""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='polar')
        
        # Prepare data for sunburst
        labels = ['Overall']
        sizes = [health_score.overall]
        colors = [self._get_score_color(health_score.overall)]
        
        # Add components
        for component, comp_score in health_score.components.items():
            labels.append(component.title())
            sizes.append(comp_score.score * comp_score.weight)
            colors.append(self._get_score_color(comp_score.score))
            
            # Add sub-components if available
            if comp_score.breakdown:
                for sub_name, sub_score in comp_score.breakdown.items():
                    labels.append(f"  {sub_name.replace('_', ' ').title()}")
                    sizes.append(sub_score * comp_score.weight / len(comp_score.breakdown))
                    colors.append(self._get_score_color(sub_score, lighter=True))
        
        # Create sunburst
        angle = 0
        for i, (label, size, color) in enumerate(zip(labels, sizes, colors)):
            if i == 0:  # Center circle for overall
                circle = plt.Circle((0, 0), 0.3, color=color)
                ax.add_patch(circle)
                ax.text(0, 0, f"{int(health_score.overall)}", 
                       ha='center', va='center', fontsize=24, fontweight='bold')
            else:
                # Determine ring level based on indentation
                level = 0 if not label.startswith('  ') else 1
                inner_radius = 0.3 + level * 0.3
                outer_radius = inner_radius + 0.3
                
                # Calculate angle for this segment
                theta = size / 100 * 2 * np.pi
                
                # Create wedge
                wedge = mpatches.Wedge((0, 0), outer_radius, 
                                      np.degrees(angle), np.degrees(angle + theta),
                                      width=outer_radius - inner_radius,
                                      facecolor=color, edgecolor='white', linewidth=2)
                ax.add_patch(wedge)
                
                # Add label
                label_angle = angle + theta / 2
                label_radius = (inner_radius + outer_radius) / 2
                x = label_radius * np.cos(label_angle)
                y = label_radius * np.sin(label_angle)
                
                ax.text(x, y, label.strip(), ha='center', va='center', fontsize=10)
                
                angle += theta
        
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis('off')
        
        self.figure.suptitle('Health Score Breakdown', fontsize=16, fontweight='bold')
        self.figure.tight_layout()
        self.draw()
    
    def _get_score_color(self, score: float, lighter: bool = False) -> str:
        """Get color based on score value."""
        if score >= 80:
            base_color = '#4CAF50'  # Green
        elif score >= 60:
            base_color = '#FFC107'  # Amber
        else:
            base_color = '#F44336'  # Red
        
        if lighter:
            # Lighten the color
            color = QColor(base_color)
            color = color.lighter(120)
            return color.name()
        
        return base_color


class HealthScoreTrendChart(FigureCanvas):
    """Line chart showing health score trends over time."""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(10, 6))
        super().__init__(self.figure)
        self.setParent(parent)
    
    def update_chart(self, score_history: List[HealthScore]):
        """Update chart with score history."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not score_history:
            ax.text(0.5, 0.5, 'No historical data available', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
            self.draw()
            return
        
        # Extract data
        dates = [score.timestamp for score in score_history]
        overall_scores = [score.overall for score in score_history]
        
        # Plot overall score
        ax.plot(dates, overall_scores, 'b-', linewidth=3, label='Overall Score')
        ax.fill_between(dates, overall_scores, alpha=0.3)
        
        # Plot component scores
        components = list(score_history[0].components.keys())
        colors = ['#FF8C42', '#FFD166', '#06D6A0', '#118AB2']
        
        for i, component in enumerate(components):
            comp_scores = [score.components[component].score for score in score_history]
            ax.plot(dates, comp_scores, '--', 
                   color=colors[i % len(colors)], 
                   linewidth=2, 
                   label=component.title())
        
        # Add trend indicators
        if len(overall_scores) >= 2:
            trend = overall_scores[-1] - overall_scores[-2]
            trend_color = '#4CAF50' if trend > 0 else '#F44336'
            ax.annotate(f"{trend:+.1f}", 
                       xy=(dates[-1], overall_scores[-1]),
                       xytext=(10, 10), 
                       textcoords='offset points',
                       fontsize=12, 
                       fontweight='bold',
                       color=trend_color)
        
        # Formatting
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Health Score Trends', fontsize=16, fontweight='bold')
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        # Format dates
        self.figure.autofmt_xdate()
        
        self.figure.tight_layout()
        self.draw()


class HealthScoreDashboard(QWidget):
    """Main dashboard widget for health score display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dashboard UI."""
        layout = QVBoxLayout(self)
        
        # Top section: Score gauge and summary
        top_layout = QHBoxLayout()
        
        # Score gauge
        self.gauge = AnimatedHealthScoreGauge()
        top_layout.addWidget(self.gauge)
        
        # Summary info
        summary_frame = QFrame(self)
        summary_frame.setFrameStyle(QFrame.Shape.Box)
        summary_layout = QVBoxLayout(summary_frame)
        
        self.category_label = QLabel("Category: -")
        self.category_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        summary_layout.addWidget(self.category_label)
        
        self.trend_label = QLabel("Trend: -")
        self.trend_label.setStyleSheet("font-size: 16px;")
        summary_layout.addWidget(self.trend_label)
        
        self.confidence_label = QLabel("Confidence: -")
        self.confidence_label.setStyleSheet("font-size: 14px; color: #666;")
        summary_layout.addWidget(self.confidence_label)
        
        self.date_range_label = QLabel("Date Range: -")
        self.date_range_label.setStyleSheet("font-size: 14px; color: #666;")
        summary_layout.addWidget(self.date_range_label)
        
        summary_layout.addStretch()
        top_layout.addWidget(summary_frame, 1)
        
        layout.addLayout(top_layout)
        
        # Component scores
        components_group = QGroupBox("Component Scores")
        components_layout = QGridLayout(components_group)
        
        self.component_cards = {}
        layout.addWidget(components_group)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Sunburst chart
        self.sunburst_chart = HealthScoreSunburstChart()
        charts_layout.addWidget(self.sunburst_chart)
        
        # Trend chart
        self.trend_chart = HealthScoreTrendChart()
        charts_layout.addWidget(self.trend_chart)
        
        layout.addLayout(charts_layout)
        
        # Insights section
        insights_group = QGroupBox("Insights & Recommendations")
        insights_layout = QVBoxLayout(insights_group)
        
        self.insights_area = QScrollArea(self)
        self.insights_widget = QWidget(self)
        self.insights_layout = QVBoxLayout(self.insights_widget)
        self.insights_area.setWidget(self.insights_widget)
        self.insights_area.setWidgetResizable(True)
        insights_layout.addWidget(self.insights_area)
        
        layout.addWidget(insights_group)
    
    def update_score(self, health_score: HealthScore, score_history: Optional[List[HealthScore]] = None):
        """Update dashboard with new health score."""
        # Update gauge
        self.gauge.set_score(health_score.overall)
        
        # Update summary
        self.category_label.setText(f"Category: {health_score.get_category()}")
        self.trend_label.setText(f"Trend: {health_score.trend.value}")
        self.confidence_label.setText(f"Confidence: {health_score.confidence:.0%}")
        
        start_date = health_score.date_range[0].strftime('%Y-%m-%d')
        end_date = health_score.date_range[1].strftime('%Y-%m-%d')
        self.date_range_label.setText(f"Date Range: {start_date} to {end_date}")
        
        # Update component cards
        # Clear existing cards
        for card in self.component_cards.values():
            card.deleteLater()
        self.component_cards.clear()
        
        # Add new cards
        components_layout = self.findChild(QGroupBox, "Component Scores").layout()
        for i, (component, score) in enumerate(health_score.components.items()):
            card = ComponentScoreCard(component, score)
            row = i // 2
            col = i % 2
            components_layout.addWidget(card, row, col)
            self.component_cards[component] = card
        
        # Update charts
        self.sunburst_chart.update_chart(health_score)
        if score_history:
            self.trend_chart.update_chart(score_history + [health_score])
        
        # Update insights
        self._update_insights(health_score)
    
    def _update_insights(self, health_score: HealthScore):
        """Update insights section."""
        # Clear existing insights
        while self.insights_layout.count():
            child = self.insights_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new insights
        for insight in health_score.insights:
            insight_frame = QFrame(self)
            insight_frame.setFrameStyle(QFrame.Shape.Box)
            
            # Set color based on severity
            if insight.severity == 'success':
                color = '#4CAF50'
            elif insight.severity == 'warning':
                color = '#FFC107'
            else:
                color = '#2196F3'
            
            insight_frame.setStyleSheet(f"""
                QFrame {{
                    border: none;
                    border-left: 4px solid {color};
                    border-radius: 5px;
                    background-color: {color}20;
                    padding: 16px;
                    margin: 8px 0;
                }}
            """)
            
            insight_layout = QVBoxLayout(insight_frame)
            
            # Category and message
            message_label = QLabel(f"[{insight.category.upper()}] {insight.message}")
            message_label.setWordWrap(True)
            message_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            insight_layout.addWidget(message_label)
            
            # Recommendation if available
            if insight.recommendation:
                rec_label = QLabel(f"→ {insight.recommendation}")
                rec_label.setWordWrap(True)
                rec_label.setStyleSheet("font-size: 12px; color: #666; margin-left: 20px;")
                insight_layout.addWidget(rec_label)
            
            self.insights_layout.addWidget(insight_frame)
        
        self.insights_layout.addStretch()