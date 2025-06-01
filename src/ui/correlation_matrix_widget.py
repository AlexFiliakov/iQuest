"""
Interactive Correlation Matrix Widget
Provides WSJ-style correlation matrix visualization with progressive disclosure.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QToolTip, QMenu, QWidgetAction, QCheckBox,
    QSpinBox, QProgressBar, QTextEdit, QSplitter, QTabWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF, QRectF, QThread, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPixmap, QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from ..analytics.correlation_discovery import LayeredCorrelationEngine, WSJStyleManager
from ..analytics.correlation_models import (
    CorrelationInsight, CorrelationNetwork, CorrelationMatrixStyle,
    CorrelationType, EffectSize, CorrelationStrength
)
from ..analytics.correlation_analyzer import CorrelationAnalyzer
from ..analytics.causality_detector import CausalityDetector
from .style_manager import StyleManager

logger = logging.getLogger(__name__)


class CorrelationMatrixWidget(QWidget):
    """Interactive correlation matrix visualization with analysis controls."""
    
    correlation_selected = pyqtSignal(str, str, float, float)  # metric1, metric2, correlation, p_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = None
        self.causality_detector = None
        self.current_correlation_data = None
        self.current_p_values = None
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel for controls
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # Right panel for visualization
        viz_panel = self.create_visualization_panel()
        splitter.addWidget(viz_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 800])
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel with analysis options."""
        panel = QFrame(self)
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Correlation method selection
        method_group = QGroupBox("Correlation Method")
        method_layout = QVBoxLayout(method_group)
        
        self.method_combo = QComboBox(self)
        self.method_combo.addItems(["Pearson", "Spearman"])
        self.method_combo.currentTextChanged.connect(self.update_correlation_matrix)
        method_layout.addWidget(self.method_combo)
        
        layout.addWidget(method_group)
        
        # Filtering options
        filter_group = QGroupBox("Display Options")
        filter_layout = QGridLayout(filter_group)
        
        # Significance threshold
        filter_layout.addWidget(QLabel("Significance Threshold:"), 0, 0)
        self.significance_slider = QSlider(Qt.Orientation.Horizontal)
        self.significance_slider.setRange(1, 10)  # 0.01 to 0.10
        self.significance_slider.setValue(5)  # 0.05
        self.significance_slider.valueChanged.connect(self.update_significance_threshold)
        filter_layout.addWidget(self.significance_slider, 0, 1)
        
        self.significance_label = QLabel("0.05")
        filter_layout.addWidget(self.significance_label, 0, 2)
        
        # Minimum correlation strength
        filter_layout.addWidget(QLabel("Min Correlation:"), 1, 0)
        self.min_corr_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_corr_slider.setRange(0, 80)  # 0.0 to 0.8
        self.min_corr_slider.setValue(30)  # 0.3
        self.min_corr_slider.valueChanged.connect(self.update_min_correlation)
        filter_layout.addWidget(self.min_corr_slider, 1, 1)
        
        self.min_corr_label = QLabel("0.30")
        filter_layout.addWidget(self.min_corr_label, 1, 2)
        
        # Display options
        self.show_values_cb = QCheckBox("Show Values")
        self.show_values_cb.setChecked(True)
        self.show_values_cb.toggled.connect(self.update_correlation_matrix)
        filter_layout.addWidget(self.show_values_cb, 2, 0, 1, 3)
        
        self.show_significance_cb = QCheckBox("Show Significance Stars")
        self.show_significance_cb.setChecked(True)
        self.show_significance_cb.toggled.connect(self.update_correlation_matrix)
        filter_layout.addWidget(self.show_significance_cb, 3, 0, 1, 3)
        
        self.mask_upper_cb = QCheckBox("Mask Upper Triangle")
        self.mask_upper_cb.setChecked(True)
        self.mask_upper_cb.toggled.connect(self.update_correlation_matrix)
        filter_layout.addWidget(self.mask_upper_cb, 4, 0, 1, 3)
        
        layout.addWidget(filter_group)
        
        # Action buttons
        button_group = QGroupBox("Actions")
        button_layout = QVBoxLayout(button_group)
        
        self.export_btn = QPushButton("Export Matrix")
        self.export_btn.clicked.connect(self.export_correlation_matrix)
        button_layout.addWidget(self.export_btn)
        
        self.causality_btn = QPushButton("Analyze Causality")
        self.causality_btn.clicked.connect(self.analyze_causality)
        button_layout.addWidget(self.causality_btn)
        
        layout.addWidget(button_group)
        
        # Summary statistics
        self.summary_text = QTextEdit(self)
        self.summary_text.setMaximumHeight(200)
        self.summary_text.setReadOnly(True)
        layout.addWidget(QLabel("Analysis Summary:"))
        layout.addWidget(self.summary_text)
        
        layout.addStretch()
        return panel
    
    def create_visualization_panel(self) -> QWidget:
        """Create the visualization panel with tabs."""
        panel = QTabWidget(self)
        
        # Correlation matrix tab
        self.matrix_tab = self.create_matrix_tab()
        panel.addTab(self.matrix_tab, "Correlation Matrix")
        
        # Significant correlations tab
        self.significant_tab = self.create_significant_correlations_tab()
        panel.addTab(self.significant_tab, "Significant Correlations")
        
        # Causality network tab
        self.network_tab = self.create_network_tab()
        panel.addTab(self.network_tab, "Causal Network")
        
        return panel
    
    def create_matrix_tab(self) -> QWidget:
        """Create the correlation matrix visualization tab."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        return widget
    
    def create_significant_correlations_tab(self) -> QWidget:
        """Create tab for displaying significant correlations."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        self.significant_correlations_text = QTextEdit(self)
        self.significant_correlations_text.setReadOnly(True)
        layout.addWidget(self.significant_correlations_text)
        
        return widget
    
    def create_network_tab(self) -> QWidget:
        """Create tab for causal network visualization."""
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        
        # Network visualization figure
        self.network_figure = Figure(figsize=(12, 10))
        self.network_canvas = FigureCanvas(self.network_figure)
        layout.addWidget(self.network_canvas)
        
        return widget
    
    def setup_styles(self):
        """Apply styling to the widget."""
        style_manager = StyleManager()
        
        # Set background colors
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {style_manager.colors['border']};
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QTextEdit {{
                border: 1px solid {style_manager.colors['border']};
                border-radius: 3px;
                background-color: {style_manager.colors['background']};
            }}
        """)
    
    def set_data(self, analyzer: CorrelationAnalyzer):
        """Set the correlation analyzer and refresh the display."""
        self.analyzer = analyzer
        self.causality_detector = CausalityDetector(analyzer)
        self.refresh_analysis()
    
    def update_significance_threshold(self, value: int):
        """Update significance threshold from slider."""
        threshold = value / 100.0  # Convert to 0.01-0.10 range
        self.significance_label.setText(f"{threshold:.2f}")
        self.analyzer.significance_threshold = threshold
        self.update_correlation_matrix()
    
    def update_min_correlation(self, value: int):
        """Update minimum correlation threshold from slider."""
        min_corr = value / 100.0  # Convert to 0.0-0.8 range
        self.min_corr_label.setText(f"{min_corr:.2f}")
        self.update_correlation_matrix()
    
    def _perform_analysis(self):
        """Perform the actual analysis (called asynchronously)."""
        try:
            # Calculate correlation matrix
            method = self.method_combo.currentText().lower()
            self.current_correlation_data = self.analyzer.calculate_correlations(method)
            
            # Update all visualizations
            self.update_correlation_matrix()
            self.update_significant_correlations()
            self.update_summary()
            
            self.status_label.setText("Analysis complete")
            
        except Exception as e:
            self.status_label.setText(f"Analysis failed: {str(e)}")
    
    def update_correlation_matrix(self):
        """Update the correlation matrix visualization."""
        if self.current_correlation_data is None:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Extract numeric correlation values for plotting
        plot_data = self._extract_numeric_correlations(self.current_correlation_data)
        
        # Create mask if requested
        mask = None
        if self.mask_upper_cb.isChecked():
            mask = np.triu(np.ones_like(plot_data, dtype=bool))
        
        # Create heatmap
        sns.heatmap(
            plot_data,
            mask=mask,
            annot=self.show_values_cb.isChecked(),
            cmap='RdBu_r',
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.5},
            fmt='.2f',
            ax=ax
        )
        
        # Add significance stars if requested
        if self.show_significance_cb.isChecked():
            self._add_significance_stars(ax)
        
        ax.set_title(f'{self.method_combo.currentText()} Correlation Matrix')
        
        # Make plot interactive
        self.canvas.mpl_connect('button_press_event', self._on_matrix_click)
        
        self.canvas.draw()
    
    def _extract_numeric_correlations(self, corr_data: pd.DataFrame) -> pd.DataFrame:
        """Extract numeric correlation values from potentially marked data."""
        numeric_data = corr_data.copy()
        
        for i in range(len(numeric_data)):
            for j in range(len(numeric_data.columns)):
                value = numeric_data.iloc[i, j]
                if isinstance(value, str):
                    # Extract numeric part from marked correlation
                    try:
                        numeric_value = float(value.split('*')[0])
                        numeric_data.iloc[i, j] = numeric_value
                    except (ValueError, IndexError):
                        numeric_data.iloc[i, j] = np.nan
        
        return numeric_data.astype(float)
    
    def _add_significance_stars(self, ax):
        """Add significance stars to correlation matrix."""
        if not hasattr(self.analyzer, 'p_value_cache') or not self.analyzer.p_value_cache:
            return
        
        # Get current p-values
        method = self.method_combo.currentText().lower()
        cache_key = f"{method}_30"  # Default min_periods
        p_values = self.analyzer.p_value_cache.get(cache_key)
        
        if p_values is None:
            return
        
        # Add stars based on significance levels
        for i in range(len(p_values)):
            for j in range(len(p_values.columns)):
                if i != j and (not self.mask_upper_cb.isChecked() or i > j):
                    p_val = p_values.iloc[i, j]
                    
                    if pd.isna(p_val):
                        continue
                    
                    stars = ''
                    if p_val < 0.001:
                        stars = '***'
                    elif p_val < 0.01:
                        stars = '**'
                    elif p_val < self.analyzer.significance_threshold:
                        stars = '*'
                    
                    if stars:
                        ax.text(j + 0.5, i + 0.7, stars,
                               ha='center', va='center',
                               color='black', fontsize=10, fontweight='bold')
    
    def _on_matrix_click(self, event):
        """Handle clicks on correlation matrix."""
        if event.inaxes is None or self.current_correlation_data is None:
            return
        
        # Get clicked cell coordinates
        col = int(event.xdata + 0.5)
        row = int(event.ydata + 0.5)
        
        if (0 <= row < len(self.current_correlation_data) and 
            0 <= col < len(self.current_correlation_data.columns)):
            
            metric1 = self.current_correlation_data.index[row]
            metric2 = self.current_correlation_data.columns[col]
            
            # Get correlation and p-value
            corr_value = self.current_correlation_data.iloc[row, col]
            if isinstance(corr_value, str):
                corr_value = float(corr_value.split('*')[0])
            
            # Get p-value
            method = self.method_combo.currentText().lower()
            cache_key = f"{method}_30"
            p_values = self.analyzer.p_value_cache.get(cache_key)
            p_value = p_values.iloc[row, col] if p_values is not None else 1.0
            
            # Emit signal
            self.correlation_selected.emit(metric1, metric2, corr_value, p_value)
            
            # Update status
            self.status_label.setText(
                f"Selected: {metric1} ↔ {metric2}, r={corr_value:.3f}, p={p_value:.3f}"
            )
    
    def update_significant_correlations(self):
        """Update the significant correlations display."""
        if self.analyzer is None:
            return
        
        try:
            method = self.method_combo.currentText().lower()
            min_strength = self.min_corr_slider.value() / 100.0
            
            significant_corrs = self.analyzer.get_significant_correlations(
                method=method, 
                min_strength=min_strength
            )
            
            # Format results
            text = f"Significant Correlations ({method.title()})\\n"
            text += f"Minimum strength: {min_strength:.2f}\\n"
            text += f"Significance threshold: {self.analyzer.significance_threshold:.3f}\\n\\n"
            
            if significant_corrs:
                for i, corr in enumerate(significant_corrs, 1):
                    text += f"{i}. {corr['metric1']} ↔ {corr['metric2']}\\n"
                    text += f"   Correlation: {corr['correlation']:.3f} ({corr['strength_category']})\\n"
                    text += f"   P-value: {corr['p_value']:.4f}\\n"
                    text += f"   Direction: {corr['direction']}\\n\\n"
            else:
                text += "No significant correlations found with current thresholds."
            
            self.significant_correlations_text.setPlainText(text)
            
        except Exception as e:
            self.significant_correlations_text.setPlainText(f"Error: {str(e)}")
    
    def update_summary(self):
        """Update the analysis summary."""
        if self.analyzer is None:
            return
        
        try:
            summary = self.analyzer.get_correlation_summary()
            
            text = "Correlation Analysis Summary\\n"
            text += "=" * 30 + "\\n\\n"
            
            # Data quality info
            data_quality = summary['data_quality']
            text += f"Data Quality:\\n"
            text += f"• Metrics: {data_quality['metrics_count']}\\n"
            text += f"• Observations: {data_quality['total_observations']}\\n"
            text += f"• Date range: {data_quality['date_range']['start']} to {data_quality['date_range']['end']}\\n\\n"
            
            # Pearson summary
            pearson = summary['pearson_summary']
            text += f"Pearson Correlations:\\n"
            text += f"• Mean correlation: {pearson['mean_correlation']:.3f}\\n"
            text += f"• Max correlation: {pearson['max_correlation']:.3f}\\n"
            text += f"• Significant: {pearson['significant_correlations']}\\n"
            text += f"• Strong (≥0.6): {pearson['strong_correlations']}\\n\\n"
            
            # Spearman summary
            spearman = summary['spearman_summary']
            text += f"Spearman Correlations:\\n"
            text += f"• Mean correlation: {spearman['mean_correlation']:.3f}\\n"
            text += f"• Max correlation: {spearman['max_correlation']:.3f}\\n"
            text += f"• Significant: {spearman['significant_correlations']}\\n"
            text += f"• Strong (≥0.6): {spearman['strong_correlations']}\\n"
            
            self.summary_text.setPlainText(text)
            
        except Exception as e:
            self.summary_text.setPlainText(f"Error generating summary: {str(e)}")
    
    def analyze_causality(self):
        """Perform causality analysis and update network visualization."""
        if self.causality_detector is None:
            self.status_label.setText("No causality detector available")
            return
        
        try:
            self.status_label.setText("Analyzing causality...")
            QTimer.singleShot(10, self._perform_causality_analysis)
            
        except Exception as e:
            self.status_label.setText(f"Causality analysis failed: {str(e)}")
    
    def _perform_causality_analysis(self):
        """Perform causality analysis (called asynchronously)."""
        try:
            # Get causality summary
            causality_summary = self.causality_detector.get_causality_summary()
            
            # Update network visualization
            self._update_network_visualization()
            
            # Update status
            causal_rels = causality_summary['causal_relationships']
            feedback_loops = causality_summary['relationship_breakdown']['feedback_loops']
            
            self.status_label.setText(
                f"Causality analysis complete: {causal_rels} relationships, {feedback_loops} feedback loops"
            )
            
        except Exception as e:
            self.status_label.setText(f"Causality analysis failed: {str(e)}")
    
    def _update_network_visualization(self):
        """Update the causal network visualization."""
        if self.causality_detector is None:
            return
        
        self.network_figure.clear()
        ax = self.network_figure.add_subplot(111)
        
        try:
            # Get network analysis
            min_correlation = self.min_corr_slider.value() / 100.0
            network_analysis = self.causality_detector.analyze_causal_network(min_correlation)
            
            if not network_analysis['causal_relationships']:
                ax.text(0.5, 0.5, 'No causal relationships found\\nwith current thresholds',
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=14, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
                self.network_canvas.draw()
                return
            
            # Create network graph
            import networkx as nx
            G = nx.DiGraph()
            
            # Add nodes and edges
            for rel in network_analysis['causal_relationships']:
                G.add_edge(rel['cause'], rel['effect'], 
                          correlation=rel['correlation'],
                          lag=rel['lag'])
            
            # Layout
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, ax=ax,
                                 node_color='#FF8C42',
                                 node_size=3000,
                                 alpha=0.8)
            
            # Draw edges with varying properties
            for edge in G.edges(data=True):
                correlation = edge[2]['correlation']
                width = abs(correlation) * 5
                color = '#4CAF50' if correlation > 0 else '#F44336'
                
                nx.draw_networkx_edges(G, pos, ax=ax,
                                     edgelist=[edge[:2]],
                                     width=width,
                                     edge_color=color,
                                     alpha=0.6,
                                     arrowsize=20)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
            
            ax.set_title(f'Causal Network\\n({len(G.edges())} relationships)')
            ax.axis('off')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Network visualization failed:\\n{str(e)}',
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
        
        self.network_canvas.draw()
    
    def export_correlation_matrix(self):
        """Export correlation matrix to CSV file."""
        if self.current_correlation_data is None:
            self.status_label.setText("No correlation data to export")
            return
        
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Correlation Matrix",
                f"correlation_matrix_{self.method_combo.currentText().lower()}.csv",
                "CSV Files (*.csv)"
            )
            
            if filename:
                # Export numeric correlation data
                numeric_data = self._extract_numeric_correlations(self.current_correlation_data)
                numeric_data.to_csv(filename)
                self.status_label.setText(f"Correlation matrix exported to {filename}")
                
        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")


if __name__ == "__main__":
    # Test the widget
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = {
        'steps': np.random.normal(8000, 2000, 100),
        'heart_rate': np.random.normal(70, 10, 100),
        'sleep_hours': np.random.normal(7.5, 1, 100)
    }
    
    # Add some correlations
    data['calories'] = data['steps'] * 0.05 + np.random.normal(2000, 200, 100)
    data['weight'] = 70 + np.cumsum(np.random.normal(0, 0.1, 100))
    
    df = pd.DataFrame(data, index=dates)
    
    # Create analyzer and widget
    analyzer = CorrelationAnalyzer(df)
    widget = CorrelationMatrixWidget()
    widget.set_data(analyzer)
    widget.show()
    
    sys.exit(app.exec())