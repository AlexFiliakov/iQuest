"""
Health Insights Widget for displaying personalized health recommendations.

This widget integrates the health insights engine with the PyQt6 UI,
providing an interactive display of evidence-based health insights.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QSpinBox, QTabWidget,
    QTextEdit, QProgressBar, QGroupBox, QGridLayout,
    QSizePolicy, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QBrush, QPen

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging

from ..analytics.health_insights_engine import EnhancedHealthInsightsEngine
from ..analytics.health_insights_models import (
    HealthInsight, InsightCategory, Priority, EvidenceLevel,
    InsightBatch
)
from ..analytics.wsj_style_manager import WSJStyleManager
from ..analytics.progressive_loader import ProgressiveLoaderCallbacks, ProgressiveResult, LoadingStage
from .style_manager import StyleManager

logger = logging.getLogger(__name__)


class InsightCardWidget(QFrame):
    """Individual insight card with WSJ-style presentation."""
    
    clicked = pyqtSignal(HealthInsight)
    
    def __init__(self, insight: HealthInsight, style_manager: StyleManager, parent=None):
        super().__init__(parent)
        self.insight = insight
        self.style_manager = style_manager
        self._expanded = False
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Set up the UI for the insight card."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with title and evidence indicator
        header_layout = QHBoxLayout()
        
        # Category icon
        self.category_icon = QLabel()
        self.category_icon.setFixedSize(24, 24)
        self.category_icon.setText(self._get_category_icon())
        header_layout.addWidget(self.category_icon)
        
        # Title
        self.title_label = QLabel(self.insight.title)
        self.title_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label, 1)
        
        # Evidence indicator
        self.evidence_badge = QLabel()
        self._setup_evidence_badge()
        header_layout.addWidget(self.evidence_badge)
        
        layout.addLayout(header_layout)
        
        # Summary
        self.summary_label = QLabel(self.insight.summary)
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        
        # Expandable content
        self.expandable_widget = QWidget()
        expandable_layout = QVBoxLayout(self.expandable_widget)
        expandable_layout.setContentsMargins(0, 0, 0, 0)
        
        # Description
        if self.insight.description:
            desc_label = QLabel(self.insight.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666;")
            expandable_layout.addWidget(desc_label)
        
        # Recommendation box
        if self.insight.recommendation:
            rec_frame = QFrame()
            rec_frame.setFrameStyle(QFrame.Shape.Box)
            rec_layout = QVBoxLayout(rec_frame)
            
            rec_title = QLabel("Recommendation")
            rec_title.setStyleSheet("font-weight: bold;")
            rec_layout.addWidget(rec_title)
            
            rec_text = QLabel(self.insight.recommendation)
            rec_text.setWordWrap(True)
            rec_layout.addWidget(rec_text)
            
            expandable_layout.addWidget(rec_frame)
        
        # Metadata
        metadata_layout = QHBoxLayout()
        
        # Confidence
        conf_label = QLabel(f"Confidence: {self.insight.confidence:.0f}%")
        conf_label.setStyleSheet("color: #888; font-size: 11px;")
        metadata_layout.addWidget(conf_label)
        
        # Impact
        impact_label = QLabel(f"Impact: {self.insight.impact_potential.value}")
        impact_label.setStyleSheet("color: #888; font-size: 11px;")
        metadata_layout.addWidget(impact_label)
        
        # Achievability
        achieve_label = QLabel(f"Difficulty: {self.insight.achievability.value}")
        achieve_label.setStyleSheet("color: #888; font-size: 11px;")
        metadata_layout.addWidget(achieve_label)
        
        metadata_layout.addStretch()
        expandable_layout.addLayout(metadata_layout)
        
        # Medical disclaimer
        if self.insight.medical_disclaimer:
            disclaimer = QLabel(self.insight.medical_disclaimer)
            disclaimer.setWordWrap(True)
            disclaimer.setStyleSheet("color: #999; font-size: 10px; font-style: italic;")
            expandable_layout.addWidget(disclaimer)
        
        self.expandable_widget.setVisible(False)
        layout.addWidget(self.expandable_widget)
        
        # Expand/collapse button
        self.expand_button = QToolButton()
        self.expand_button.setText("Show more ▼")
        self.expand_button.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.expand_button)
        
        # Make card clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _get_category_icon(self) -> str:
        """Get icon for category."""
        icons = {
            InsightCategory.SLEEP: "🌙",
            InsightCategory.ACTIVITY: "🏃",
            InsightCategory.RECOVERY: "💚",
            InsightCategory.NUTRITION: "🍎",
            InsightCategory.BODY_METRICS: "⚖️",
            InsightCategory.HEART_HEALTH: "❤️"
        }
        return icons.get(self.insight.category, "📊")
    
    def _setup_evidence_badge(self):
        """Set up evidence level badge."""
        if self.insight.wsj_presentation and self.insight.wsj_presentation.evidence_indicator:
            indicator = self.insight.wsj_presentation.evidence_indicator
            self.evidence_badge.setText(indicator.get('icon', ''))
            self.evidence_badge.setToolTip(indicator.get('tooltip', ''))
        else:
            # Fallback
            evidence_icons = {
                EvidenceLevel.STRONG: "⭐⭐⭐",
                EvidenceLevel.MODERATE: "⭐⭐",
                EvidenceLevel.WEAK: "⭐",
                EvidenceLevel.PATTERN_BASED: "📊"
            }
            self.evidence_badge.setText(evidence_icons.get(self.insight.evidence_level, ""))
    
    def apply_styling(self):
        """Apply WSJ-style styling to the card."""
        # Get colors from WSJ presentation or use defaults
        if self.insight.wsj_presentation and self.insight.wsj_presentation.color_coding:
            colors = self.insight.wsj_presentation.color_coding
        else:
            # Default colors based on priority
            if self.insight.priority == Priority.HIGH:
                bg_color = "#FFF3E0"  # Light orange
                border_color = "#FF8C42"
            elif self.insight.priority == Priority.MEDIUM:
                bg_color = "#FFF9C4"  # Light yellow
                border_color = "#FFD166"
            else:
                bg_color = "#F5F5F5"  # Light gray
                border_color = "#E0E0E0"
            
            colors = {
                'background': bg_color,
                'border': border_color
            }
        
        self.setStyleSheet(f"""
            InsightCardWidget {{
                background-color: {colors.get('background', '#FFFFFF')};
                border: 2px solid {colors.get('border', '#E0E0E0')};
                border-radius: 8px;
                padding: 12px;
            }}
            InsightCardWidget:hover {{
                border-color: {colors.get('primary', '#FF8C42')};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
    
    def toggle_expanded(self):
        """Toggle expanded state."""
        self._expanded = not self._expanded
        self.expandable_widget.setVisible(self._expanded)
        self.expand_button.setText("Show less ▲" if self._expanded else "Show more ▼")
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.insight)
        super().mousePressEvent(event)


class InsightGenerationThread(QThread):
    """Background thread for generating insights."""
    
    insights_ready = pyqtSignal(list)  # List[HealthInsight]
    progress_update = pyqtSignal(int, str)  # progress%, message
    error_occurred = pyqtSignal(str)
    
    def __init__(self, engine: EnhancedHealthInsightsEngine, 
                 user_data: Dict[str, Any],
                 time_period: str = "monthly",
                 max_insights: int = 5):
        super().__init__()
        self.engine = engine
        self.user_data = user_data
        self.time_period = time_period
        self.max_insights = max_insights
    
    def run(self):
        """Generate insights in background."""
        try:
            self.progress_update.emit(10, "Analyzing health patterns...")
            
            # Generate insights
            insights = self.engine.generate_prioritized_insights(
                self.user_data,
                self.time_period,
                self.max_insights
            )
            
            self.progress_update.emit(100, "Analysis complete")
            self.insights_ready.emit(insights)
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            self.error_occurred.emit(str(e))


class HealthInsightsWidget(QWidget):
    """Main widget for displaying health insights and recommendations."""
    
    insight_selected = pyqtSignal(HealthInsight)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize components
        self.style_manager = StyleManager()
        self.wsj_style_manager = WSJStyleManager()
        self.insights_engine = None
        self.current_insights: List[HealthInsight] = []
        self.insight_cards: List[InsightCardWidget] = []
        
        # Generation thread
        self.generation_thread = None
        
        # Progressive loading support
        self.progressive_callbacks = ProgressiveLoaderCallbacks()
        self._setup_progressive_callbacks()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Health Insights & Recommendations")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Time period selector
        period_label = QLabel("Time Period:")
        header_layout.addWidget(period_label)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Weekly", "Monthly", "Quarterly"])
        self.period_combo.setCurrentText("Monthly")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        header_layout.addWidget(self.period_combo)
        
        # Max insights selector
        insights_label = QLabel("Show:")
        header_layout.addWidget(insights_label)
        
        self.max_insights_spin = QSpinBox()
        self.max_insights_spin.setRange(3, 10)
        self.max_insights_spin.setValue(5)
        self.max_insights_spin.setSuffix(" insights")
        self.max_insights_spin.valueChanged.connect(self.on_max_insights_changed)
        header_layout.addWidget(self.max_insights_spin)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_insights)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget for different insight views
        self.tab_widget = QTabWidget()
        
        # All insights tab
        self.all_insights_widget = self._create_insights_scroll_area()
        self.tab_widget.addTab(self.all_insights_widget, "All Insights")
        
        # Category tabs
        self.category_tabs = {}
        for category in InsightCategory:
            scroll_area = self._create_insights_scroll_area()
            self.category_tabs[category] = scroll_area
            self.tab_widget.addTab(scroll_area, category.value.replace("_", " ").title())
        
        layout.addWidget(self.tab_widget)
        
        # Summary section
        self.summary_widget = self._create_summary_widget()
        layout.addWidget(self.summary_widget)
    
    def _create_insights_scroll_area(self) -> QScrollArea:
        """Create scroll area for insights."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        return scroll_area
    
    def _create_summary_widget(self) -> QWidget:
        """Create summary widget."""
        summary_group = QGroupBox("Insights Summary")
        layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        layout.addWidget(self.summary_text)
        
        return summary_group
    
    def _setup_progressive_callbacks(self):
        """Set up callbacks for progressive loading."""
        self.progressive_callbacks.on_loading_started = self._on_loading_started
        self.progressive_callbacks.on_skeleton_ready = self._on_skeleton_ready
        self.progressive_callbacks.on_first_data_ready = self._on_first_data_ready
        self.progressive_callbacks.on_progress_update = self._on_progress_update
        self.progressive_callbacks.on_loading_complete = self._on_loading_complete
        self.progressive_callbacks.on_loading_error = self._on_loading_error
    
    def set_insights_engine(self, engine: EnhancedHealthInsightsEngine):
        """Set the insights engine."""
        self.insights_engine = engine
    
    def load_insights(self, user_data: Dict[str, Any]):
        """Load insights from user data."""
        if not self.insights_engine:
            logger.error("No insights engine set")
            return
        
        # Stop any existing generation
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.quit()
            self.generation_thread.wait()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start generation thread
        self.generation_thread = InsightGenerationThread(
            self.insights_engine,
            user_data,
            self.period_combo.currentText().lower(),
            self.max_insights_spin.value()
        )
        
        self.generation_thread.insights_ready.connect(self._on_insights_ready)
        self.generation_thread.progress_update.connect(self._on_generation_progress)
        self.generation_thread.error_occurred.connect(self._on_generation_error)
        
        self.generation_thread.start()
    
    @pyqtSlot(list)
    def _on_insights_ready(self, insights: List[HealthInsight]):
        """Handle insights ready."""
        self.current_insights = insights
        self._display_insights()
        self._update_summary()
        self.progress_bar.setVisible(False)
    
    @pyqtSlot(int, str)
    def _on_generation_progress(self, progress: int, message: str):
        """Handle generation progress."""
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{message} ({progress}%)")
    
    @pyqtSlot(str)
    def _on_generation_error(self, error: str):
        """Handle generation error."""
        logger.error(f"Insight generation error: {error}")
        self.progress_bar.setVisible(False)
        # Could show error dialog here
    
    def _display_insights(self):
        """Display insights in the UI."""
        # Clear existing cards
        for card in self.insight_cards:
            card.deleteLater()
        self.insight_cards.clear()
        
        # Group insights by category
        insights_by_category = {}
        for insight in self.current_insights:
            if insight.category not in insights_by_category:
                insights_by_category[insight.category] = []
            insights_by_category[insight.category].append(insight)
        
        # Create cards for all insights
        all_layout = QVBoxLayout()
        all_layout.setSpacing(12)
        
        for insight in self.current_insights:
            card = InsightCardWidget(insight, self.style_manager)
            card.clicked.connect(self.insight_selected.emit)
            self.insight_cards.append(card)
            all_layout.addWidget(card)
        
        all_layout.addStretch()
        
        # Update all insights tab
        if self.all_insights_widget.widget():
            self.all_insights_widget.widget().deleteLater()
        all_content = QWidget()
        all_content.setLayout(all_layout)
        self.all_insights_widget.setWidget(all_content)
        
        # Update category tabs
        for category, scroll_area in self.category_tabs.items():
            if scroll_area.widget():
                scroll_area.widget().deleteLater()
            
            cat_layout = QVBoxLayout()
            cat_layout.setSpacing(12)
            
            if category in insights_by_category:
                for insight in insights_by_category[category]:
                    card = InsightCardWidget(insight, self.style_manager)
                    card.clicked.connect(self.insight_selected.emit)
                    cat_layout.addWidget(card)
            else:
                # No insights for this category
                no_insights = QLabel("No insights available for this category")
                no_insights.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_insights.setStyleSheet("color: #999; padding: 20px;")
                cat_layout.addWidget(no_insights)
            
            cat_layout.addStretch()
            
            cat_content = QWidget()
            cat_content.setLayout(cat_layout)
            scroll_area.setWidget(cat_content)
    
    def _update_summary(self):
        """Update the summary text."""
        if not self.current_insights:
            self.summary_text.setPlainText("No insights available. Load health data to generate personalized insights.")
            return
        
        # Generate summary using the insights engine
        summary = self.insights_engine.generate_weekly_summary(self.current_insights)
        self.summary_text.setHtml(summary.replace('\n', '<br>').replace('**', '<b>').replace('*', '<i>'))
    
    def refresh_insights(self):
        """Refresh insights."""
        self.refresh_requested.emit()
    
    def on_period_changed(self, period: str):
        """Handle period change."""
        self.refresh_insights()
    
    def on_max_insights_changed(self, value: int):
        """Handle max insights change."""
        self.refresh_insights()
    
    # Progressive loading callbacks
    def _on_loading_started(self):
        """Handle loading started."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Loading insights...")
    
    def _on_skeleton_ready(self, skeleton_config: dict):
        """Handle skeleton ready."""
        # Could show skeleton UI here
        pass
    
    def _on_first_data_ready(self, result: ProgressiveResult):
        """Handle first data ready."""
        if result.data and isinstance(result.data, list):
            # Show first insights immediately
            self.current_insights = result.data[:3]  # Show top 3 first
            self._display_insights()
    
    def _on_progress_update(self, result: ProgressiveResult):
        """Handle progress update."""
        self.progress_bar.setValue(int(result.progress * 100))
        self.progress_bar.setFormat(result.message)
    
    def _on_loading_complete(self, result: ProgressiveResult):
        """Handle loading complete."""
        if result.data and isinstance(result.data, list):
            self.current_insights = result.data
            self._display_insights()
            self._update_summary()
        self.progress_bar.setVisible(False)
    
    def _on_loading_error(self, error: str):
        """Handle loading error."""
        logger.error(f"Loading error: {error}")
        self.progress_bar.setVisible(False)