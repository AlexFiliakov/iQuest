"""Matplotlib chart factory for high-quality health visualization exports."""

from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from datetime import datetime
import io

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.collections import LineCollection
import matplotlib.dates as mdates
# import seaborn as sns  # Optional dependency - commented out for now

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from .wsj_style_manager import WSJStyleManager
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class MatplotlibChartWidget(QWidget):
    """Widget wrapper for matplotlib figures."""
    
    def __init__(self, figure: Figure, parent=None):
        super().__init__(parent)
        self.figure = figure
        self.canvas = FigureCanvas(figure)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
    
    def export(self, filename: str, dpi: int = 300, format: str = 'png'):
        """Export the chart to file."""
        self.figure.savefig(filename, dpi=dpi, format=format, 
                           bbox_inches='tight', facecolor=self.figure.get_facecolor())


class MatplotlibChartFactory:
    """Factory for creating publication-quality charts using Matplotlib."""
    
    def __init__(self, style_manager: WSJStyleManager):
        """Initialize the chart factory."""
        self.style_manager = style_manager
        logger.debug("Initialized MatplotlibChartFactory")
    
    def create_chart(self, chart_type: str, data: Any, config: Dict[str, Any]) -> Figure:
        """Create a publication-quality chart of the specified type."""
        chart_creators = {
            'multi_metric_line': self._create_multi_metric_line,
            'correlation_heatmap': self._create_correlation_heatmap,
            'sparkline': self._create_sparkline,
            'timeline': self._create_timeline_chart,
            'polar': self._create_polar_chart,
            'scatter': self._create_scatter_chart,
            'box_plot': self._create_box_plot,
            'waterfall': self._create_waterfall_chart,
            'small_multiples': self._create_small_multiples,
            'bump_chart': self._create_bump_chart
        }
        
        creator = chart_creators.get(chart_type)
        if creator:
            return creator(data, config)
        else:
            logger.warning(f"Unknown chart type: {chart_type}")
            return self._create_fallback_chart(chart_type, config)
    
    def _create_fallback_chart(self, chart_type: str, config: Dict[str, Any]) -> Figure:
        """Create a fallback chart for unknown types."""
        fig, ax = plt.subplots(figsize=(10, 6))
        self.style_manager.apply_chart_style(ax, 
                                           title=f"{chart_type} Chart",
                                           subtitle="Chart type not implemented")
        ax.text(0.5, 0.5, f"{chart_type}\n(Not implemented)", 
               transform=ax.transAxes, ha='center', va='center',
               fontsize=14, color=self.style_manager.WARM_PALETTE['text_secondary'])
        return fig
    
    def _create_multi_metric_line(self, data: Dict[str, pd.DataFrame], 
                                 config: Dict[str, Any]) -> Figure:
        """Create multi-metric line chart with independent y-axes."""
        # Determine figure size
        fig_size = config.get('figure_size', (12, 8))
        fig = plt.figure(figsize=fig_size)
        
        # Create main axis
        ax1 = fig.add_subplot(111)
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax1,
            title=config.get('title', ''),
            subtitle=config.get('subtitle', ''),
            show_grid=config.get('grid_style', 'subtle') != 'none'
        )
        
        # Track axes and lines for legend
        axes = [ax1]
        lines = []
        labels = []
        
        # Get y-axis configuration
        y_axes_config = config.get('y_axes', {})
        colors_config = config.get('colors', {})
        
        # Plot each metric
        for i, (metric_name, metric_data) in enumerate(data.items()):
            # Get configuration for this metric
            metric_config = y_axes_config.get(metric_name, {})
            
            # Handle both dict and list color configs
            if isinstance(colors_config, dict):
                color = colors_config.get(metric_name, 
                                        self.style_manager.get_metric_color(metric_name, i))
            elif isinstance(colors_config, list):
                color = colors_config[i % len(colors_config)]
            else:
                color = self.style_manager.get_metric_color(metric_name, i)
            
            # Prepare data
            if isinstance(metric_data, pd.DataFrame):
                x_data = metric_data.index
                y_data = metric_data.iloc[:, 0].values
            else:
                x_data = np.arange(len(metric_data))
                y_data = metric_data.values
            
            # Create axis
            if i == 0:
                ax = ax1
                ax.set_ylabel(metric_name, color=color,
                            fontsize=self.style_manager.TYPOGRAPHY['axis_label']['size'])
                ax.tick_params(axis='y', labelcolor=color)
            else:
                # Create twin axis
                ax = ax1.twinx()
                axes.append(ax)
                
                # Position the axis
                if i > 1:
                    # Offset additional y-axes
                    ax.spines['right'].set_position(('outward', 60 * (i - 1)))
                
                ax.set_ylabel(metric_name, color=color,
                            fontsize=self.style_manager.TYPOGRAPHY['axis_label']['size'])
                ax.tick_params(axis='y', labelcolor=color)
                
                # Hide grid for secondary axes
                ax.grid(False)
            
            # Plot line
            line = ax.plot(x_data, y_data, color=color, linewidth=2.5,
                          label=metric_name, zorder=10 - i)[0]
            lines.append(line)
            labels.append(metric_name)
            
            # Format y-axis
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: self.style_manager.format_number(x))
            )
        
        # Format x-axis
        if isinstance(x_data[0], (datetime, pd.Timestamp)):
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
            fig.autofmt_xdate()
        
        # Add legend
        if config.get('legend_position', 'top') != 'none':
            legend = ax1.legend(lines, labels, 
                              loc='upper left' if config.get('legend_position') == 'top' else 'best',
                              frameon=False,
                              fontsize=self.style_manager.TYPOGRAPHY['legend']['size'])
            self.style_manager.apply_legend_style(legend)
        
        # Add annotations if provided
        if 'annotations' in config:
            for ann in config['annotations']:
                self.style_manager.create_smart_annotation(
                    ax1, ann['x'], ann['y'], ann['text'],
                    arrow=ann.get('arrow', True),
                    offset=ann.get('offset', (20, 20))
                )
        
        plt.tight_layout()
        return fig
    
    def _create_correlation_heatmap(self, data: Dict[str, pd.DataFrame],
                                   config: Dict[str, Any]) -> Figure:
        """Create correlation heatmap with significance indicators."""
        # Get data
        corr_matrix = data.get('correlation', pd.DataFrame())
        sig_matrix = data.get('significance', pd.DataFrame())
        
        # Create figure
        fig_size = config.get('figure_size', (10, 8))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Create heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool)) if config.get('mask_upper', True) else None
        
        # Use WSJ colormap
        cmap = self.style_manager.get_correlation_colormap()
        
        # Plot heatmap using matplotlib instead of seaborn
        im = ax.imshow(corr_matrix, cmap=cmap, aspect='auto', vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Correlation Coefficient", rotation=270, labelpad=15)
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(corr_matrix.columns)))
        ax.set_yticks(np.arange(len(corr_matrix.index)))
        ax.set_xticklabels(corr_matrix.columns)
        ax.set_yticklabels(corr_matrix.index)
        
        # Rotate the tick labels and set their alignment
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add values if requested
        if config.get('show_values', True):
            for i in range(len(corr_matrix)):
                for j in range(len(corr_matrix)):
                    if mask is None or not mask[i, j]:
                        text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                                     ha="center", va="center", color="black", fontsize=9)
        
        # Add significance stars if provided
        if sig_matrix is not None and not sig_matrix.empty and config.get('significance_indicators', True):
            for i in range(len(corr_matrix)):
                for j in range(len(corr_matrix)):
                    if mask is None or not mask[i, j]:
                        if i < len(sig_matrix) and j < len(sig_matrix.columns):
                            if sig_matrix.iloc[i, j] < 0.001:
                                stars = '***'
                            elif sig_matrix.iloc[i, j] < 0.01:
                                stars = '**'
                            elif sig_matrix.iloc[i, j] < 0.05:
                                stars = '*'
                            else:
                                stars = ''
                        else:
                            stars = ''
                        
                        if stars:
                            ax.text(j + 0.5, i + 0.7, stars,
                                   ha='center', va='center',
                                   fontsize=12, color='black', weight='bold')
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=config.get('title', 'Correlation Matrix'),
            subtitle=config.get('subtitle', '')
        )
        
        # Rotate labels
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        plt.setp(ax.yaxis.get_majorticklabels(), rotation=0)
        
        plt.tight_layout()
        return fig
    
    def _create_sparkline(self, data: Union[pd.Series, np.ndarray], 
                         config: Dict[str, Any]) -> Figure:
        """Create compact sparkline visualization."""
        # Create small figure
        fig_size = config.get('figure_size', (3, 1))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Prepare data
        if isinstance(data, pd.Series):
            y_data = data.values
        else:
            y_data = np.array(data)
        
        x_data = np.arange(len(y_data))
        
        # Determine color based on trend
        if len(y_data) > 1:
            trend = y_data[-1] - y_data[0]
            if trend > 0:
                color = self.style_manager.WARM_PALETTE['positive']
            elif trend < 0:
                color = self.style_manager.WARM_PALETTE['negative']
            else:
                color = self.style_manager.WARM_PALETTE['neutral']
        else:
            color = self.style_manager.WARM_PALETTE['primary']
        
        # Plot sparkline
        ax.plot(x_data, y_data, color=color, linewidth=2)
        
        # Fill area under curve if requested
        if config.get('fill', False):
            ax.fill_between(x_data, y_data, alpha=0.2, color=color)
        
        # Remove all axes and labels for minimal look
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Add reference line if requested
        if config.get('show_reference', False):
            ref_value = config.get('reference_value', np.mean(y_data))
            ax.axhline(y=ref_value, color=self.style_manager.WARM_PALETTE['grid'],
                      linestyle='--', linewidth=1, alpha=0.5)
        
        # Add value label if requested
        if config.get('show_value', True):
            current_value = y_data[-1] if len(y_data) > 0 else 0
            ax.text(1.02, 0.5, self.style_manager.format_number(current_value),
                   transform=ax.transAxes, va='center',
                   fontsize=12, color=color, weight='bold')
        
        plt.tight_layout()
        return fig
    
    def _create_timeline_chart(self, data: Dict[str, Any], config: Dict[str, Any]) -> Figure:
        """Create timeline chart with events and background metrics."""
        fig_size = config.get('figure_size', (14, 8))
        fig, (ax_metric, ax_timeline) = plt.subplots(2, 1, figsize=fig_size,
                                                     gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot background metrics
        if 'background_metrics' in data:
            for metric_name, metric_data in data['background_metrics'].items():
                if isinstance(metric_data, pd.DataFrame):
                    x_data = metric_data.index
                    y_data = metric_data.iloc[:, 0].values
                else:
                    x_data = np.arange(len(metric_data))
                    y_data = metric_data.values
                
                color = self.style_manager.get_metric_color(metric_name)
                ax_metric.plot(x_data, y_data, label=metric_name,
                             color=color, linewidth=2, alpha=0.8)
        
        # Apply styling to metric axis
        self.style_manager.apply_chart_style(
            ax_metric,
            title=config.get('title', 'Health Timeline'),
            subtitle=config.get('subtitle', ''),
            y_label=config.get('metric_label', 'Metric Value')
        )
        
        # Plot events on timeline
        events = data.get('events', [])
        event_times = [e['time'] for e in events]
        event_labels = [e['label'] for e in events]
        event_types = [e.get('type', 'default') for e in events]
        
        # Color mapping for event types
        event_colors = {
            'medication': self.style_manager.WARM_PALETTE['primary'],
            'symptom': self.style_manager.WARM_PALETTE['negative'],
            'milestone': self.style_manager.WARM_PALETTE['positive'],
            'default': self.style_manager.WARM_PALETTE['secondary']
        }
        
        # Plot events
        for i, (time, label, event_type) in enumerate(zip(event_times, event_labels, event_types)):
            color = event_colors.get(event_type, event_colors['default'])
            
            # Add vertical line to metric plot
            ax_metric.axvline(x=time, color=color, linestyle='--', alpha=0.5, linewidth=1)
            
            # Add event marker on timeline
            ax_timeline.scatter(time, 0, s=100, c=color, zorder=10, edgecolors='white', linewidth=2)
            
            # Add event label
            ax_timeline.annotate(label, xy=(time, 0), xytext=(0, 20),
                               textcoords='offset points', ha='center',
                               fontsize=9, color=self.style_manager.WARM_PALETTE['text_secondary'],
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor=self.style_manager.WARM_PALETTE['surface'],
                                       edgecolor=color, alpha=0.8))
        
        # Style timeline axis
        ax_timeline.set_ylim(-0.5, 0.5)
        ax_timeline.set_xlim(ax_metric.get_xlim())
        ax_timeline.set_yticks([])
        for spine in ax_timeline.spines.values():
            spine.set_visible(False)
        ax_timeline.grid(False)
        
        # Add timeline line
        ax_timeline.axhline(y=0, color=self.style_manager.WARM_PALETTE['text_secondary'],
                          linewidth=2, alpha=0.5)
        
        # Format x-axis
        if event_times and isinstance(event_times[0], (datetime, pd.Timestamp)):
            ax_timeline.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax_timeline.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Add legend to metric plot
        if data.get('background_metrics'):
            ax_metric.legend(frameon=False, loc='upper left')
        
        plt.tight_layout()
        return fig
    
    def _create_polar_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """Create polar chart for cyclical patterns."""
        fig_size = config.get('figure_size', (8, 8))
        fig = plt.figure(figsize=fig_size)
        ax = fig.add_subplot(111, projection='polar')
        
        # Prepare data for polar plot
        pattern_type = config.get('pattern_type', 'daily')
        
        if pattern_type == 'daily':
            # 24-hour pattern
            theta = np.linspace(0, 2 * np.pi, 24, endpoint=False)
            labels = [f"{i:02d}:00" for i in range(24)]
        elif pattern_type == 'weekly':
            # 7-day pattern
            theta = np.linspace(0, 2 * np.pi, 7, endpoint=False)
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        else:
            # Custom pattern
            n_points = len(data)
            theta = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
            labels = [str(i) for i in range(n_points)]
        
        # Get values
        if isinstance(data, pd.DataFrame):
            values = data.iloc[:, 0].values
        else:
            values = np.array(data)
        
        # Ensure values match theta length
        if len(values) != len(theta):
            values = np.interp(theta, np.linspace(0, 2 * np.pi, len(values), endpoint=False), values)
        
        # Close the plot
        theta = np.append(theta, theta[0])
        values = np.append(values, values[0])
        
        # Plot
        ax.plot(theta, values, color=self.style_manager.WARM_PALETTE['primary'], linewidth=2)
        ax.fill(theta, values, color=self.style_manager.WARM_PALETTE['primary'], alpha=0.2)
        
        # Styling
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xticks(theta[:-1])
        ax.set_xticklabels(labels)
        
        # Grid styling
        ax.grid(True, linestyle='--', alpha=0.3, color=self.style_manager.WARM_PALETTE['grid'])
        ax.set_facecolor(self.style_manager.WARM_PALETTE['surface'])
        
        # Title
        if 'title' in config:
            ax.set_title(config['title'], pad=20,
                        fontsize=self.style_manager.TYPOGRAPHY['title']['size'],
                        fontweight=self.style_manager.TYPOGRAPHY['title']['weight'])
        
        plt.tight_layout()
        return fig
    
    def _create_scatter_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """Create scatter plot with trend line and correlation."""
        fig_size = config.get('figure_size', (10, 8))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Get x and y data
        if isinstance(data, pd.DataFrame) and len(data.columns) >= 2:
            x_data = data.iloc[:, 0].values
            y_data = data.iloc[:, 1].values
            x_label = data.columns[0]
            y_label = data.columns[1]
        else:
            x_data = config.get('x_data', [])
            y_data = config.get('y_data', [])
            x_label = config.get('x_label', 'X')
            y_label = config.get('y_label', 'Y')
        
        # Plot scatter points
        scatter = ax.scatter(x_data, y_data, 
                           color=self.style_manager.WARM_PALETTE['primary'],
                           s=50, alpha=0.6, edgecolors='white', linewidth=1)
        
        # Add trend line if requested
        if config.get('show_trend', True):
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            ax.plot(x_data, p(x_data), color=self.style_manager.WARM_PALETTE['secondary'],
                   linewidth=2, linestyle='--', label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
        
        # Calculate and display correlation
        if config.get('show_correlation', True):
            corr = np.corrcoef(x_data, y_data)[0, 1]
            ax.text(0.05, 0.95, f'R = {corr:.3f}', transform=ax.transAxes,
                   fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor=self.style_manager.WARM_PALETTE['surface'],
                           edgecolor=self.style_manager.WARM_PALETTE['grid'], alpha=0.8))
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=config.get('title', ''),
            subtitle=config.get('subtitle', ''),
            x_label=x_label,
            y_label=y_label
        )
        
        # Add legend if trend line shown
        if config.get('show_trend', True):
            legend = ax.legend(frameon=False)
            self.style_manager.apply_legend_style(legend)
        
        plt.tight_layout()
        return fig
    
    def _create_box_plot(self, data: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """Create box plot for distribution comparison."""
        fig_size = config.get('figure_size', (10, 6))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Prepare data
        if isinstance(data, pd.DataFrame):
            plot_data = [data[col].dropna().values for col in data.columns]
            labels = list(data.columns)
        else:
            plot_data = data
            labels = config.get('labels', [f'Group {i+1}' for i in range(len(data))])
        
        # Create box plot
        bp = ax.boxplot(plot_data, labels=labels, patch_artist=True,
                       showmeans=config.get('show_means', True),
                       meanline=config.get('show_means', True))
        
        # Style the box plot with WSJ colors
        colors = self.style_manager.get_warm_palette()
        
        for i, (box, median, whisker1, whisker2, cap1, cap2) in enumerate(zip(
            bp['boxes'], bp['medians'], 
            bp['whiskers'][::2], bp['whiskers'][1::2],
            bp['caps'][::2], bp['caps'][1::2]
        )):
            # Box styling
            box.set_facecolor(colors[i % len(colors)])
            box.set_alpha(0.6)
            box.set_edgecolor(self.style_manager.WARM_PALETTE['text_secondary'])
            
            # Median line
            median.set_color(self.style_manager.WARM_PALETTE['text_primary'])
            median.set_linewidth(2)
            
            # Whiskers and caps
            for item in [whisker1, whisker2, cap1, cap2]:
                item.set_color(self.style_manager.WARM_PALETTE['text_secondary'])
                item.set_linewidth(1.5)
        
        # Style means if shown
        if config.get('show_means', True) and 'meanlines' in bp:
            for meanline in bp['meanlines']:
                meanline.set_color(self.style_manager.WARM_PALETTE['secondary'])
                meanline.set_linewidth(2)
                meanline.set_linestyle('--')
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=config.get('title', ''),
            subtitle=config.get('subtitle', ''),
            y_label=config.get('y_label', 'Value')
        )
        
        # Rotate x labels if many groups
        if len(labels) > 5:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_waterfall_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """Create waterfall chart for showing cumulative effect."""
        fig_size = config.get('figure_size', (12, 8))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Prepare data
        if isinstance(data, pd.DataFrame):
            values = data.iloc[:, 0].values
            labels = list(data.index)
        else:
            values = data
            labels = config.get('labels', [f'Step {i+1}' for i in range(len(values))])
        
        # Calculate cumulative values
        cumulative = np.cumsum(values)
        
        # Determine bar positions
        x = np.arange(len(values))
        
        # Create bars
        for i, (val, cum) in enumerate(zip(values, cumulative)):
            if i == 0:
                # First bar starts at 0
                bottom = 0
            else:
                # Subsequent bars start at previous cumulative
                bottom = cumulative[i-1]
            
            # Determine color
            if val >= 0:
                color = self.style_manager.WARM_PALETTE['positive']
            else:
                color = self.style_manager.WARM_PALETTE['negative']
            
            # Draw bar
            ax.bar(x[i], abs(val), bottom=min(bottom, cum),
                  color=color, alpha=0.7, edgecolor='white', linewidth=2)
            
            # Add value label
            ax.text(x[i], cum + (val/2 if val > 0 else -val/2),
                   self.style_manager.format_number(val),
                   ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Add connectors
        for i in range(len(x) - 1):
            ax.plot([x[i] + 0.4, x[i+1] - 0.4], 
                   [cumulative[i], cumulative[i]],
                   'k--', alpha=0.5, linewidth=1)
        
        # Set labels
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=config.get('title', 'Waterfall Chart'),
            subtitle=config.get('subtitle', ''),
            y_label=config.get('y_label', 'Cumulative Value')
        )
        
        # Rotate x labels if many
        if len(labels) > 8:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_small_multiples(self, data: Dict[str, pd.DataFrame], 
                               config: Dict[str, Any]) -> Figure:
        """Create small multiples for comparing patterns across groups."""
        # Determine grid size
        n_charts = len(data)
        n_cols = config.get('n_cols', min(3, n_charts))
        n_rows = (n_charts + n_cols - 1) // n_cols
        
        fig_size = config.get('figure_size', (4 * n_cols, 3 * n_rows))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=fig_size,
                               sharex=config.get('share_x', True),
                               sharey=config.get('share_y', True))
        
        # Flatten axes array for easier iteration
        if n_charts == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_rows > 1 or n_cols > 1 else [axes]
        
        # Plot each small multiple
        for i, (group_name, group_data) in enumerate(data.items()):
            if i >= len(axes):
                break
            
            ax = axes[i]
            
            # Plot data
            if isinstance(group_data, pd.DataFrame):
                x_data = group_data.index
                y_data = group_data.iloc[:, 0].values
            else:
                x_data = np.arange(len(group_data))
                y_data = group_data.values
            
            color = self.style_manager.get_metric_color(group_name, i)
            ax.plot(x_data, y_data, color=color, linewidth=2)
            
            # Add title
            ax.set_title(group_name, fontsize=12, pad=10)
            
            # Apply minimal styling
            self.style_manager.apply_chart_style(ax, show_grid=True, grid_style='subtle')
            
            # Remove individual axis labels for cleaner look
            if i % n_cols != 0:
                ax.set_ylabel('')
            if i < len(axes) - n_cols:
                ax.set_xlabel('')
        
        # Hide unused subplots
        for i in range(n_charts, len(axes)):
            axes[i].set_visible(False)
        
        # Add overall title
        if 'title' in config:
            fig.suptitle(config['title'], 
                        fontsize=self.style_manager.TYPOGRAPHY['title']['size'],
                        fontweight=self.style_manager.TYPOGRAPHY['title']['weight'],
                        y=0.98)
        
        plt.tight_layout()
        return fig
    
    def _create_bump_chart(self, data: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """Create bump chart showing ranking changes over time."""
        fig_size = config.get('figure_size', (12, 8))
        fig, ax = plt.subplots(figsize=fig_size)
        
        # Prepare ranking data
        # Data should have time periods as index and entities as columns
        rankings = data.rank(axis=1, ascending=False, method='min')
        
        # Plot lines for each entity
        colors = self.style_manager.get_warm_palette()
        
        for i, col in enumerate(rankings.columns):
            y_values = rankings[col].values
            x_values = np.arange(len(rankings.index))
            
            color = colors[i % len(colors)]
            
            # Plot line with markers
            ax.plot(x_values, y_values, 'o-', color=color, linewidth=3,
                   markersize=8, label=col, zorder=10 - i)
            
            # Add rank labels at start and end
            ax.text(-0.1, y_values[0], str(int(y_values[0])),
                   ha='right', va='center', fontsize=10, fontweight='bold')
            ax.text(x_values[-1] + 0.1, y_values[-1], str(int(y_values[-1])),
                   ha='left', va='center', fontsize=10, fontweight='bold')
        
        # Invert y-axis so rank 1 is at top
        ax.invert_yaxis()
        
        # Set x labels
        ax.set_xticks(x_values)
        ax.set_xticklabels(rankings.index)
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=config.get('title', 'Ranking Over Time'),
            subtitle=config.get('subtitle', ''),
            x_label=config.get('x_label', 'Time Period'),
            y_label='Rank'
        )
        
        # Add legend
        legend = ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False)
        self.style_manager.apply_legend_style(legend)
        
        # Grid only on y-axis
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        return fig