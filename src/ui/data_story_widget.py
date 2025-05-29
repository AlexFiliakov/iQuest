"""
Data Story Widget for displaying generated health narratives.
Shows weekly recaps, monthly journeys, and milestone celebrations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QToolButton, QTextEdit, QSplitter,
    QListWidget, QListWidgetItem, QStackedWidget, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QTextCharFormat, QTextDocument

from ..analytics.data_story_generator import Story, StoryType, Insight, Recommendation
from ..analytics.story_delivery_manager import InAppStory, CardSection, StoryVisual, StoryAction


class DataStoryWidget(QWidget):
    """Main widget for displaying data stories."""
    
    story_dismissed = pyqtSignal(str)  # story_id
    story_shared = pyqtSignal(Story)
    action_clicked = pyqtSignal(str, dict)  # action_type, data
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_story = None
        self.story_history = []
        self.collapsed_sections = set()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header = self.create_header()
        layout.addWidget(self.header)
        
        # Story container
        self.story_container = QScrollArea(self)
        self.story_container.setWidgetResizable(True)
        self.story_container.setFrameShape(QFrame.Shape.NoFrame)
        
        # Story content widget
        self.story_content = QWidget(self)
        self.content_layout = QVBoxLayout(self.story_content)
        self.content_layout.setSpacing(16)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.story_container.setWidget(self.story_content)
        layout.addWidget(self.story_container, 1)
        
        # Initially hidden
        self.hide()
    
    def create_header(self) -> QWidget:
        """Create story header with title and actions."""
        header = QFrame(self)
        header.setObjectName("storyHeader")
        header.setStyleSheet("""
            #storyHeader {
                background-color: #FF8C42;
                padding: 16px;
            }
        """)
        
        layout = QHBoxLayout(header)
        
        # Title
        self.title_label = QLabel("Your Health Story")
        self.title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
        """)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Action buttons
        self.share_button = self.create_action_button("Share", "share")
        self.dismiss_button = self.create_action_button("Dismiss", "close")
        
        layout.addWidget(self.share_button)
        layout.addWidget(self.dismiss_button)
        
        return header
    
    def create_action_button(self, text: str, icon_name: str) -> QPushButton:
        """Create a header action button."""
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        if icon_name == "share":
            button.clicked.connect(self.share_story)
        elif icon_name == "close":
            button.clicked.connect(self.dismiss_story)
        
        return button
    
    def display_story(self, story: Story):
        """Display a story in the widget."""
        self.current_story = story
        self.story_history.append(story)
        
        # Update title
        self.title_label.setText(story.title)
        
        # Clear existing content
        self.clear_content()
        
        # Add story sections
        for section_name, content in story.sections.items():
            if content:
                section_widget = self.create_section_widget(
                    section_name.replace('_', ' ').title(),
                    content
                )
                self.content_layout.addWidget(section_widget)
        
        # Add insights if available
        if story.insights:
            insights_widget = self.create_insights_widget(story.insights)
            self.content_layout.addWidget(insights_widget)
        
        # Add recommendations if available
        if story.recommendations:
            recommendations_widget = self.create_recommendations_widget(
                story.recommendations
            )
            self.content_layout.addWidget(recommendations_widget)
        
        # Add stretch at the end
        self.content_layout.addStretch()
        
        # Show widget with animation
        self.show_with_animation()
    
    def display_in_app_story(self, in_app_story: InAppStory):
        """Display an InAppStory format."""
        # Create a Story object from InAppStory for compatibility
        story = Story(
            title=in_app_story.title,
            text="",
            type=StoryType.WEEKLY_RECAP,  # Default
            sections={},
            insights=[],
            recommendations=[]
        )
        
        # Convert card sections to story sections
        for section in in_app_story.sections:
            if section.type == 'text':
                story.sections[section.title or 'content'] = section.content
            elif section.type == 'insight':
                story.insights.append(Insight(
                    text=section.content,
                    category='general',
                    importance=section.metadata.get('importance', 0.5) if section.metadata else 0.5
                ))
            elif section.type == 'recommendation':
                story.recommendations.append(Recommendation(
                    action=section.content,
                    rationale=section.metadata.get('rationale', '') if section.metadata else '',
                    category='general',
                    difficulty=section.metadata.get('difficulty', 'medium') if section.metadata else 'medium'
                ))
        
        self.display_story(story)
    
    def clear_content(self):
        """Clear all content from the story widget."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def create_section_widget(self, title: str, content: str) -> QWidget:
        """Create a collapsible section widget."""
        section = QFrame(self)
        section.setObjectName("storySection")
        section.setStyleSheet("""
            #storySection {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                border: none;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
        """)
        
        layout = QVBoxLayout(section)
        
        # Section header
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #5D4E37;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Expand/collapse button if content is long
        if len(content) > 300:
            toggle_button = QToolButton()
            toggle_button.setArrowType(Qt.ArrowType.DownArrow)
            toggle_button.setStyleSheet("""
                QToolButton {
                    border: none;
                    background: none;
                }
            """)
            toggle_button.clicked.connect(lambda: self.toggle_section(section, toggle_button))
            header_layout.addWidget(toggle_button)
            
            # Store full content
            section.setProperty("full_content", content)
            section.setProperty("toggle_button", toggle_button)
            
            # Show truncated content initially
            content = content[:300] + "..."
        
        layout.addLayout(header_layout)
        
        # Content
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("""
            color: #8B7355;
            line-height: 1.6;
        """)
        content_label.setObjectName("sectionContent")
        layout.addWidget(content_label)
        
        return section
    
    def create_insights_widget(self, insights: List[Insight]) -> QWidget:
        """Create widget for displaying insights."""
        widget = QGroupBox("Key Insights")
        widget.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
                border: none;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 0 8px 0;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        for insight in insights[:3]:  # Limit to 3 insights
            insight_frame = QFrame(self)
            insight_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFF8F0;
                    border: none;
                    border-left: 4px solid #FFD166;
                    padding: 16px;
                    border-radius: 4px;
                    margin: 4px 0;
                }
            """)
            
            insight_layout = QHBoxLayout(insight_frame)
            
            # Insight icon
            icon_label = QLabel("💡")
            icon_label.setStyleSheet("font-size: 20px;")
            insight_layout.addWidget(icon_label)
            
            # Insight text
            text_label = QLabel(insight.text)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("""
                color: #5D4E37;
                padding-left: 8px;
            """)
            insight_layout.addWidget(text_label, 1)
            
            layout.addWidget(insight_frame)
        
        return widget
    
    def create_recommendations_widget(self, recommendations: List[Recommendation]) -> QWidget:
        """Create widget for displaying recommendations."""
        widget = QGroupBox("Recommendations")
        widget.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #5D4E37;
                border: none;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 0 8px 0;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        for rec in recommendations[:3]:  # Limit to 3 recommendations
            rec_frame = QFrame(self)
            rec_frame.setStyleSheet("""
                QFrame {
                    background-color: #F5E6D3;
                    border: none;
                    border-left: 4px solid #FF8C42;
                    padding: 16px;
                    border-radius: 4px;
                    margin: 4px 0;
                }
            """)
            
            rec_layout = QVBoxLayout(rec_frame)
            rec_layout.setSpacing(4)
            
            # Action
            action_label = QLabel(f"✓ {rec.action}")
            action_label.setWordWrap(True)
            action_label.setStyleSheet("""
                color: #5D4E37;
                font-weight: 500;
            """)
            rec_layout.addWidget(action_label)
            
            # Rationale
            if rec.rationale:
                rationale_label = QLabel(rec.rationale)
                rationale_label.setWordWrap(True)
                rationale_label.setStyleSheet("""
                    color: #8B7355;
                    font-size: 14px;
                    padding-left: 20px;
                """)
                rec_layout.addWidget(rationale_label)
            
            # Difficulty indicator
            if rec.difficulty:
                difficulty_label = QLabel(f"Difficulty: {rec.difficulty}")
                difficulty_label.setStyleSheet("""
                    color: #A69583;
                    font-size: 12px;
                    padding-left: 20px;
                """)
                rec_layout.addWidget(difficulty_label)
            
            layout.addWidget(rec_frame)
        
        return widget
    
    def toggle_section(self, section: QWidget, toggle_button: QToolButton):
        """Toggle section expansion."""
        content_label = section.findChild(QLabel, "sectionContent")
        full_content = section.property("full_content")
        
        if toggle_button.arrowType() == Qt.ArrowType.DownArrow:
            # Expand
            content_label.setText(full_content)
            toggle_button.setArrowType(Qt.ArrowType.UpArrow)
        else:
            # Collapse
            content_label.setText(full_content[:300] + "...")
            toggle_button.setArrowType(Qt.ArrowType.DownArrow)
    
    def show_with_animation(self):
        """Show widget with slide animation."""
        self.show()
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animate from right to current position
        current_pos = self.pos()
        self.move(current_pos.x() + self.width(), current_pos.y())
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(current_pos)
        
        self.animation.start()
    
    def dismiss_story(self):
        """Dismiss the current story."""
        if self.current_story:
            story_id = str(id(self.current_story))
            self.story_dismissed.emit(story_id)
        
        # Hide with animation
        self.hide_with_animation()
    
    def hide_with_animation(self):
        """Hide widget with slide animation."""
        # Create animation
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # Animate to right
        current_pos = self.pos()
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(current_pos + self.width())
        
        self.animation.finished.connect(self.hide)
        self.animation.start()
    
    def share_story(self):
        """Share the current story."""
        if self.current_story:
            self.story_shared.emit(self.current_story)
    
    def get_story_history(self) -> List[Story]:
        """Get list of previously displayed stories."""
        return self.story_history.copy()
    
    def clear_history(self):
        """Clear story history."""
        self.story_history.clear()


class StoryListWidget(QWidget):
    """Widget for displaying a list of available stories."""
    
    story_selected = pyqtSignal(Story)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.stories = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Your Health Stories")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #5D4E37;
            padding: 16px;
        """)
        layout.addWidget(title_label)
        
        # Story list
        self.story_list = QListWidget(self)
        self.story_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #F5E6D3;
            }
            QListWidget::item {
                background-color: white;
                margin: 8px;
                padding: 16px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background-color: #FFF8F0;
            }
            QListWidget::item:selected {
                background-color: #FFE4CC;
            }
        """)
        self.story_list.itemClicked.connect(self.on_story_clicked)
        
        layout.addWidget(self.story_list)
    
    def add_story(self, story: Story):
        """Add a story to the list."""
        self.stories.append(story)
        
        # Create list item
        item = QListWidgetItem()
        
        # Create custom widget for the item
        item_widget = self.create_story_item_widget(story)
        
        # Set size hint
        item.setSizeHint(item_widget.sizeHint())
        
        # Add to list
        self.story_list.addItem(item)
        self.story_list.setItemWidget(item, item_widget)
    
    def create_story_item_widget(self, story: Story) -> QWidget:
        """Create a custom widget for story list item."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # Header with title and date
        header_layout = QHBoxLayout()
        
        # Type icon
        icon_map = {
            StoryType.WEEKLY_RECAP: "📅",
            StoryType.MONTHLY_JOURNEY: "📆",
            StoryType.YEAR_IN_REVIEW: "📊",
            StoryType.MILESTONE_CELEBRATION: "🎉"
        }
        icon_label = QLabel(icon_map.get(story.type, "📄"))
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(story.title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #5D4E37;
        """)
        header_layout.addWidget(title_label, 1)
        
        # Date
        if story.metadata:
            date_label = QLabel(
                story.metadata.generated_at.strftime("%b %d, %Y")
            )
            date_label.setStyleSheet("""
                color: #A69583;
                font-size: 14px;
            """)
            header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Preview text
        preview_text = self.get_story_preview(story)
        preview_label = QLabel(preview_text)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("""
            color: #8B7355;
            font-size: 14px;
        """)
        layout.addWidget(preview_label)
        
        # Stats
        stats_layout = QHBoxLayout()
        
        # Word count
        if story.metadata:
            word_count_label = QLabel(f"📝 {story.metadata.word_count} words")
            word_count_label.setStyleSheet("""
                color: #A69583;
                font-size: 12px;
            """)
            stats_layout.addWidget(word_count_label)
        
        # Insights count
        if story.insights:
            insights_label = QLabel(f"💡 {len(story.insights)} insights")
            insights_label.setStyleSheet("""
                color: #A69583;
                font-size: 12px;
            """)
            stats_layout.addWidget(insights_label)
        
        # Recommendations count
        if story.recommendations:
            rec_label = QLabel(f"✓ {len(story.recommendations)} recommendations")
            rec_label.setStyleSheet("""
                color: #A69583;
                font-size: 12px;
            """)
            stats_layout.addWidget(rec_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Store story reference
        widget.setProperty("story", story)
        
        return widget
    
    def get_story_preview(self, story: Story) -> str:
        """Get preview text for a story."""
        # Try to get first non-empty section content
        for content in story.sections.values():
            if content:
                return content[:150] + "..." if len(content) > 150 else content
        
        return story.text[:150] + "..." if story.text and len(story.text) > 150 else story.text
    
    def on_story_clicked(self, item: QListWidgetItem):
        """Handle story item click."""
        widget = self.story_list.itemWidget(item)
        if widget:
            story = widget.property("story")
            if story:
                self.story_selected.emit(story)
    
    def clear_stories(self):
        """Clear all stories from the list."""
        self.stories.clear()
        self.story_list.clear()
    
    def get_stories_by_type(self, story_type: StoryType) -> List[Story]:
        """Get stories of a specific type."""
        return [s for s in self.stories if s.type == story_type]


class StoryNotificationWidget(QWidget):
    """Compact notification widget for new stories."""
    
    clicked = pyqtSignal()
    dismissed = pyqtSignal()
    
    def __init__(self, story_title: str, story_type: StoryType,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.story_title = story_title
        self.story_type = story_type
        self.setup_ui()
        
        # Auto-dismiss timer
        self.auto_dismiss_timer = QTimer()
        self.auto_dismiss_timer.timeout.connect(self.dismiss)
        self.auto_dismiss_timer.start(10000)  # 10 seconds
    
    def setup_ui(self):
        """Set up the notification UI."""
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QWidget {
                background-color: #FF8C42;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon_map = {
            StoryType.WEEKLY_RECAP: "📅",
            StoryType.MONTHLY_JOURNEY: "📆",
            StoryType.YEAR_IN_REVIEW: "📊",
            StoryType.MILESTONE_CELEBRATION: "🎉"
        }
        icon_label = QLabel(icon_map.get(self.story_type, "📄"))
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        title_label = QLabel("New Story Available!")
        title_label.setStyleSheet("""
            color: white;
            font-weight: 600;
            font-size: 14px;
        """)
        content_layout.addWidget(title_label)
        
        # Story title
        story_label = QLabel(self.story_title)
        story_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 16px;
        """)
        content_layout.addWidget(story_label)
        
        layout.addLayout(content_layout, 1)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        # View button
        view_button = QPushButton("View")
        view_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #FF8C42;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FFF8F0;
            }
        """)
        view_button.clicked.connect(self.on_view_clicked)
        actions_layout.addWidget(view_button)
        
        # Dismiss button
        dismiss_button = QPushButton("×")
        dismiss_button.setFixedSize(24, 24)
        dismiss_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        dismiss_button.clicked.connect(self.dismiss)
        actions_layout.addWidget(dismiss_button)
        
        layout.addLayout(actions_layout)
        
        # Mouse events
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_view_clicked()
    
    def on_view_clicked(self):
        """Handle view button click."""
        self.auto_dismiss_timer.stop()
        self.clicked.emit()
        self.dismiss()
    
    def dismiss(self):
        """Dismiss the notification."""
        self.auto_dismiss_timer.stop()
        self.dismissed.emit()
        
        # Fade out animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.deleteLater)
        self.fade_animation.start()