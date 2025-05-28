"""
Month-over-Month Trends Widget for comprehensive trend analysis.

Integrates all visualization components (waterfall, bump, stream, small multiples)
with the analytics engine for a complete month-over-month analysis dashboard.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QFrame,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QTextEdit, QScrollArea,
    QGroupBox, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter

from ..analytics.month_over_month_trends import MonthOverMonthTrends, TrendAnalysis
from ..analytics.monthly_metrics_calculator import MonthlyMetricsCalculator
from .charts.waterfall_chart import WaterfallChartContainer
from .charts.bump_chart import BumpChartContainer
from .charts.stream_graph import StreamGraphContainer
from .charts.small_multiples import SmallMultiplesContainer, SmallMultipleChart
from .charts.calendar_heatmap import CalendarHeatmapComponent
from .summary_cards import SummaryCard, SummaryCardType
from .style_manager import StyleManager


class TrendAnalysisWorker(QThread):
    """Background worker for trend analysis to avoid UI blocking."""
    
    analysis_completed = pyqtSignal(object)  # TrendAnalysis
    analysis_failed = pyqtSignal(str)  # error message
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, trend_analyzer: MonthOverMonthTrends, metric: str, months: int):
        super().__init__()
        self.trend_analyzer = trend_analyzer
        self.metric = metric
        self.months = months
    
    def run(self):
        """Run trend analysis in background."""
        try:
            self.progress_updated.emit(10)
            
            # Perform analysis
            analysis = self.trend_analyzer.analyze_trends(
                self.metric, 
                self.months,
                include_forecast=True,
                include_population_comparison=False
            )
            
            self.progress_updated.emit(100)
            self.analysis_completed.emit(analysis)
            
        except Exception as e:
            self.analysis_failed.emit(str(e))


class InsightPanel(QFrame):
    """Panel displaying generated insights and milestones."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the insight panel UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📊 Key Insights")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Insights area
        self.insights_area = QScrollArea()
        self.insights_area.setWidgetResizable(True)
        self.insights_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.insights_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        
        self.insights_widget = QWidget()
        self.insights_layout = QVBoxLayout(self.insights_widget)
        self.insights_area.setWidget(self.insights_widget)
        
        layout.addWidget(self.insights_area)
    
    def set_insights(self, insights: List, milestones: List):
        """Display insights and milestones."""
        # Clear existing insights
        for i in reversed(range(self.insights_layout.count())):
            self.insights_layout.itemAt(i).widget().setParent(None)
        
        # Add insights
        for insight in insights[:5]:  # Show top 5 insights
            insight_frame = self._create_insight_frame(insight)
            self.insights_layout.addWidget(insight_frame)
        
        # Add milestones
        if milestones:
            milestone_label = QLabel("🏆 Recent Milestones")
            milestone_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            milestone_label.setStyleSheet("color: #E74C3C; margin-top: 15px;")
            self.insights_layout.addWidget(milestone_label)
            
            for milestone in milestones[:3]:  # Show top 3 milestones
                milestone_frame = self._create_milestone_frame(milestone)
                self.insights_layout.addWidget(milestone_frame)
        
        self.insights_layout.addStretch()
    
    def _create_insight_frame(self, insight) -> QFrame:
        """Create a frame for a single insight."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px;
                margin: 3px 0;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Insight title
        title_label = QLabel(insight.title)
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #495057;")
        layout.addWidget(title_label)
        
        # Insight description
        desc_label = QLabel(insight.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6C757D; font-size: 10px; margin-top: 2px;")
        layout.addWidget(desc_label)
        
        # Confidence indicator
        confidence_text = f"Confidence: {insight.confidence:.0%}"
        confidence_label = QLabel(confidence_text)
        confidence_label.setStyleSheet("color: #28A745; font-size: 9px; font-weight: bold;")
        layout.addWidget(confidence_label)
        
        return frame
    
    def _create_milestone_frame(self, milestone) -> QFrame:
        """Create a frame for a single milestone."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border: 1px solid #FFB74D;
                border-radius: 6px;
                padding: 8px;
                margin: 3px 0;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Milestone type icon
        type_icons = {
            'record': '🏆',
            'streak': '🔥',
            'improvement': '📈',
            'goal': '🎯'
        }
        icon = type_icons.get(milestone.type, '⭐')
        
        title_text = f"{icon} {milestone.description}"
        title_label = QLabel(title_text)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #E65100;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Date
        date_label = QLabel(milestone.date.strftime("%B %d, %Y"))
        date_label.setStyleSheet("color: #BF360C; font-size: 9px;")
        layout.addWidget(date_label)
        
        return frame


class MonthOverMonthWidget(QWidget):
    """
    Comprehensive month-over-month trends analysis widget.
    
    Features:
    - Multiple visualization modes (waterfall, bump, stream, small multiples)
    - Statistical analysis results
    - Generated insights and milestones
    - Interactive controls and filters
    - Export capabilities
    """
    
    def __init__(self, monthly_calculator: MonthlyMetricsCalculator, parent=None):
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.monthly_calculator = monthly_calculator
        self.trend_analyzer = MonthOverMonthTrends(monthly_calculator)
        
        # State
        self.current_analysis: Optional[TrendAnalysis] = None
        self.available_metrics = []
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with controls
        header_layout = self._create_header_controls()
        layout.addLayout(header_layout)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Visualizations
        viz_panel = self._create_visualization_panel()
        main_splitter.addWidget(viz_panel)
        
        # Right panel: Insights and statistics
        insights_panel = self._create_insights_panel()
        main_splitter.addWidget(insights_panel)
        
        # Set splitter proportions (70% viz, 30% insights)
        main_splitter.setSizes([700, 300])
        
        layout.addWidget(main_splitter)
    
    def _create_header_controls(self) -> QHBoxLayout:
        """Create the header control panel."""
        layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("📈 Month-over-Month Trends Analysis")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2C3E50; margin-right: 20px;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Metric selector
        layout.addWidget(QLabel("Metric:"))
        self.metric_combo = QComboBox()
        self.metric_combo.setMinimumWidth(150)
        layout.addWidget(self.metric_combo)
        
        # Months selector
        layout.addWidget(QLabel("Months:"))
        self.months_spinbox = QSpinBox()
        self.months_spinbox.setRange(6, 36)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setSuffix(" months")
        layout.addWidget(self.months_spinbox)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze Trends")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        layout.addWidget(self.analyze_button)
        
        return layout
    
    def _create_visualization_panel(self) -> QWidget:
        """Create the visualization panel with tabs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Visualization tabs
        self.viz_tabs = QTabWidget()
        self.viz_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F0F0F0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007BFF;
            }
        """)
        
        # Waterfall chart tab
        self.waterfall_chart = WaterfallChartContainer()
        self.viz_tabs.addTab(self.waterfall_chart, "Waterfall")
        
        # Bump chart tab
        self.bump_chart = BumpChartContainer()
        self.viz_tabs.addTab(self.bump_chart, "Rankings")
        
        # Stream graph tab
        self.stream_chart = StreamGraphContainer()
        self.viz_tabs.addTab(self.stream_chart, "Composition")
        
        # Small multiples tab
        self.multiples_chart = SmallMultiplesContainer()
        self.viz_tabs.addTab(self.multiples_chart, "Multiple Views")
        
        # Calendar heatmap tab
        self.heatmap_chart = CalendarHeatmapComponent()
        self.viz_tabs.addTab(self.heatmap_chart, "Calendar")
        
        layout.addWidget(self.viz_tabs)
        
        # Summary cards row
        self.summary_cards_layout = QHBoxLayout()
        layout.addLayout(self.summary_cards_layout)
        
        return panel
    
    def _create_insights_panel(self) -> QWidget:
        """Create the insights and statistics panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Insights panel
        self.insights_panel = InsightPanel()
        layout.addWidget(self.insights_panel)
        
        # Statistics summary
        stats_group = QGroupBox("Statistical Summary")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #495057;
            }
        """)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        return panel
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.analyze_button.clicked.connect(self.run_analysis)
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        self.months_spinbox.valueChanged.connect(self._on_months_changed)
    
    def set_available_metrics(self, metrics: List[str]):
        """Set the available metrics for analysis."""
        self.available_metrics = metrics
        self.metric_combo.clear()
        self.metric_combo.addItems(metrics)
    
    def run_analysis(self):
        """Run month-over-month trend analysis."""
        metric = self.metric_combo.currentText()
        months = self.months_spinbox.value()
        
        if not metric:
            return
        
        # Disable controls and show progress
        self.analyze_button.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Start background analysis
        self.analysis_worker = TrendAnalysisWorker(self.trend_analyzer, metric, months)
        self.analysis_worker.analysis_completed.connect(self._on_analysis_completed)
        self.analysis_worker.analysis_failed.connect(self._on_analysis_failed)
        self.analysis_worker.progress_updated.connect(self.progress_bar.setValue)
        self.analysis_worker.start()
    
    def _on_analysis_completed(self, analysis: TrendAnalysis):
        """Handle completed analysis."""
        self.current_analysis = analysis
        self._update_visualizations()
        self._update_insights()
        self._update_statistics()
        self._update_summary_cards()
        
        # Re-enable controls
        self.analyze_button.setEnabled(True)
        self.progress_bar.hide()
    
    def _on_analysis_failed(self, error_message: str):
        """Handle analysis failure."""
        self.stats_text.setText(f"Analysis failed: {error_message}")
        
        # Re-enable controls
        self.analyze_button.setEnabled(True)
        self.progress_bar.hide()
    
    def _update_visualizations(self):
        """Update all visualization components."""
        if not self.current_analysis:
            return
        
        analysis = self.current_analysis
        
        # Update waterfall chart
        if analysis.waterfall_data:
            self.waterfall_chart.set_chart_data(
                analysis.waterfall_data.categories,
                analysis.waterfall_data.values,
                analysis.waterfall_data.cumulative,
                analysis.waterfall_data.colors,
                analysis.waterfall_data.labels,
                f"{analysis.metric_name} - Month-over-Month Changes"
            )
        
        # Update bump chart (single metric version)
        if analysis.raw_values and analysis.dates:
            # Create rankings based on percentile within the data
            values = analysis.raw_values
            rankings = []
            for value in values:
                percentile = sum(1 for v in values if v <= value) / len(values)
                rank = max(1, int((1 - percentile) * 5) + 1)  # Scale to 1-5 ranking
                rankings.append(rank)
            
            self.bump_chart.set_chart_data(
                [analysis.metric_name],
                [d.strftime('%b %Y') for d in analysis.dates],
                {analysis.metric_name: rankings},
                {analysis.metric_name: values},
                f"{analysis.metric_name} - Performance Ranking"
            )
        
        # Update stream graph (single metric as 100% composition)
        if analysis.stream_data:
            self.stream_chart.set_chart_data(
                analysis.stream_data.categories,
                [d.strftime('%b %Y') for d in analysis.stream_data.dates],
                analysis.stream_data.values,
                analysis.stream_data.baseline,
                f"{analysis.metric_name} - Composition Over Time"
            )
        
        # Update small multiples
        if analysis.raw_values and analysis.dates:
            multiples_charts = []
            
            # Raw values chart
            multiples_charts.append(SmallMultipleChart(
                title="Raw Values",
                chart_type="line",
                x_data=[d.strftime('%b %Y') for d in analysis.dates],
                y_data=analysis.raw_values
            ))
            
            # Monthly changes chart
            if len(analysis.raw_values) > 1:
                changes = [analysis.raw_values[i] - analysis.raw_values[i-1] 
                          for i in range(1, len(analysis.raw_values))]
                multiples_charts.append(SmallMultipleChart(
                    title="Monthly Changes",
                    chart_type="bar",
                    x_data=[d.strftime('%b %Y') for d in analysis.dates[1:]],
                    y_data=changes
                ))
            
            # Trend component (if available)
            if analysis.decomposition and analysis.decomposition.trend:
                multiples_charts.append(SmallMultipleChart(
                    title="Trend Component",
                    chart_type="line",
                    x_data=[d.strftime('%b %Y') for d in analysis.decomposition.dates],
                    y_data=analysis.decomposition.trend
                ))
            
            # Rolling 3-month average
            if len(analysis.raw_values) >= 3:
                rolling_avg = []
                for i in range(2, len(analysis.raw_values)):
                    avg = np.mean(analysis.raw_values[i-2:i+1])
                    rolling_avg.append(avg)
                
                multiples_charts.append(SmallMultipleChart(
                    title="3-Month Rolling Average",
                    chart_type="area",
                    x_data=[d.strftime('%b %Y') for d in analysis.dates[2:]],
                    y_data=rolling_avg
                ))
            
            self.multiples_chart.set_chart_data(
                multiples_charts,
                f"{analysis.metric_name} - Multiple Views"
            )
        
        # Update calendar heatmap
        if analysis.monthly_data:
            heatmap_data = {}
            for monthly_metric in analysis.monthly_data:
                date_key = monthly_metric.month_start.strftime('%Y-%m-%d')
                heatmap_data[date_key] = monthly_metric.avg
            
            self.heatmap_chart.set_data(
                heatmap_data,
                f"{analysis.metric_name} - Monthly Values"
            )
    
    def _update_insights(self):
        """Update the insights panel."""
        if not self.current_analysis:
            return
        
        self.insights_panel.set_insights(
            self.current_analysis.insights,
            self.current_analysis.milestones
        )
    
    def _update_statistics(self):
        """Update the statistics summary."""
        if not self.current_analysis:
            return
        
        analysis = self.current_analysis
        stats_text = []
        
        # Basic statistics
        stats_text.append(f"Metric: {analysis.metric_name}")
        stats_text.append(f"Analysis Period: {analysis.analysis_period[0].strftime('%b %Y')} - {analysis.analysis_period[1].strftime('%b %Y')}")
        stats_text.append(f"Data Points: {len(analysis.raw_values)}")
        stats_text.append("")
        
        # Trend statistics
        if analysis.momentum:
            momentum = analysis.momentum
            stats_text.append("Momentum Analysis:")
            stats_text.append(f"  Score: {momentum.score:.3f}")
            stats_text.append(f"  Direction: {momentum.direction.value}")
            stats_text.append(f"  Strength: {momentum.strength}")
            stats_text.append(f"  Consistency: {momentum.consistency:.3f}")
            stats_text.append("")
        
        # Change points
        if analysis.change_points:
            stats_text.append("Significant Changes:")
            for cp in analysis.change_points[:3]:  # Show top 3
                direction = "↑" if cp.after_avg > cp.before_avg else "↓"
                stats_text.append(f"  {cp.date.strftime('%b %Y')}: {direction} {cp.change_magnitude:.1f} ({cp.significance})")
            stats_text.append("")
        
        # Forecast
        if analysis.forecast:
            forecast = analysis.forecast
            next_value = forecast.point_forecast[0] if forecast.point_forecast else 0
            current_value = analysis.raw_values[-1] if analysis.raw_values else 0
            change_pct = ((next_value - current_value) / current_value * 100) if current_value != 0 else 0
            
            stats_text.append("Forecast:")
            stats_text.append(f"  Next Month: {next_value:.1f} ({change_pct:+.1f}%)")
            stats_text.append(f"  Confidence: {forecast.confidence_level:.0%}")
            stats_text.append(f"  Method: {forecast.method}")
        
        self.stats_text.setText("\n".join(stats_text))
    
    def _update_summary_cards(self):
        """Update summary cards with key metrics."""
        # Clear existing cards
        for i in reversed(range(self.summary_cards_layout.count())):
            self.summary_cards_layout.itemAt(i).widget().setParent(None)
        
        if not self.current_analysis:
            return
        
        analysis = self.current_analysis
        
        # Current value card
        current_value = analysis.raw_values[-1] if analysis.raw_values else 0
        current_card = SummaryCard(SummaryCardType.METRIC)
        current_card.set_data(
            title="Current Value",
            value=f"{current_value:.1f}",
            subtitle=analysis.dates[-1].strftime('%B %Y') if analysis.dates else "",
            trend_direction="neutral"
        )
        self.summary_cards_layout.addWidget(current_card)
        
        # Total change card
        if len(analysis.raw_values) >= 2:
            total_change = analysis.raw_values[-1] - analysis.raw_values[0]
            change_pct = (total_change / analysis.raw_values[0] * 100) if analysis.raw_values[0] != 0 else 0
            
            change_card = SummaryCard(SummaryCardType.CHANGE)
            change_card.set_data(
                title="Total Change",
                value=f"{change_pct:+.1f}%",
                subtitle=f"{total_change:+.1f} units",
                trend_direction="up" if total_change > 0 else "down" if total_change < 0 else "neutral"
            )
            self.summary_cards_layout.addWidget(change_card)
        
        # Momentum card
        if analysis.momentum:
            momentum_card = SummaryCard(SummaryCardType.TREND)
            momentum_card.set_data(
                title="Momentum",
                value=analysis.momentum.strength.title(),
                subtitle=analysis.momentum.direction.value.title(),
                trend_direction="up" if analysis.momentum.score > 0.1 else "down" if analysis.momentum.score < -0.1 else "neutral"
            )
            self.summary_cards_layout.addWidget(momentum_card)
        
        # Milestones card
        milestone_count = len(analysis.milestones)
        milestone_card = SummaryCard(SummaryCardType.COUNT)
        milestone_card.set_data(
            title="Milestones",
            value=str(milestone_count),
            subtitle="Achievements",
            trend_direction="neutral"
        )
        self.summary_cards_layout.addWidget(milestone_card)
    
    def _on_metric_changed(self):
        """Handle metric selection change."""
        # Could trigger auto-analysis or data preview
        pass
    
    def _on_months_changed(self):
        """Handle months selection change."""
        # Could trigger auto-analysis or update estimates
        pass
    
    def export_analysis(self, filepath: str) -> bool:
        """Export current analysis to file."""
        if not self.current_analysis:
            return False
        
        try:
            # Export charts
            base_path = filepath.rsplit('.', 1)[0]
            
            self.waterfall_chart.chart.export_chart(f"{base_path}_waterfall.png")
            self.bump_chart.chart.export_chart(f"{base_path}_bump.png")
            
            # Export summary data
            with open(f"{base_path}_summary.txt", 'w') as f:
                f.write(self.stats_text.toPlainText())
            
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False