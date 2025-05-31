"""WSJ-inspired style manager for health visualizations."""

from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class WSJStyleManager:
    """Manages WSJ-inspired styling for health visualizations."""
    
    # WSJ-inspired color palette
    WARM_PALETTE = {
        'primary': '#FF8C42',      # Warm orange - main metrics
        'secondary': '#FFD166',    # Warm yellow - comparisons
        'background': '#F5E6D3',   # Tan - subtle context
        'surface': '#FAF8F5',      # Off-white - clean backgrounds
        'text_primary': '#2C2C2C', # Dark gray - primary text
        'text_secondary': '#666666', # Medium gray - secondary text
        'grid': '#E8DCC8',         # Light tan - subtle grids
        'positive': '#95C17B',     # Soft green - positive trends
        'negative': '#E76F51',     # Coral - negative trends
        'neutral': '#A8A8A8'       # Gray - neutral elements
    }
    
    # Typography configuration
    TYPOGRAPHY = {
        'title': {
            'family': 'Roboto Condensed',
            'size': 18,
            'weight': 600,
            'color': WARM_PALETTE['text_primary']
        },
        'subtitle': {
            'family': 'Roboto Condensed',
            'size': 14,
            'weight': 400,
            'color': WARM_PALETTE['text_secondary']
        },
        'axis_label': {
            'family': 'Roboto',
            'size': 12,
            'weight': 400,
            'color': WARM_PALETTE['text_secondary']
        },
        'tick_label': {
            'family': 'Roboto',
            'size': 10,
            'weight': 400,
            'color': WARM_PALETTE['text_secondary']
        },
        'legend': {
            'family': 'Roboto',
            'size': 11,
            'weight': 400,
            'color': WARM_PALETTE['text_primary']
        },
        'annotation': {
            'family': 'Roboto',
            'size': 10,
            'weight': 400,
            'style': 'italic',
            'color': WARM_PALETTE['text_secondary']
        }
    }
    
    # Spacing configuration
    SPACING = {
        'title_margin': 20,
        'subtitle_margin': 10,
        'axis_label_pad': 10,
        'legend_spacing': 1.0,
        'figure_padding': 0.15
    }
    
    # Accessibility configuration
    ACCESSIBILITY = {
        'min_contrast_ratio': 4.5,
        'focus_width': 3,
        'focus_color': WARM_PALETTE['primary'],
        'min_touch_target': 44,
        'colorblind_safe': True
    }
    
    def __init__(self):
        """Initialize the WSJ style manager."""
        logger.debug("Initializing WSJStyleManager")
        self._setup_matplotlib_style()
        self._create_colormaps()
    
    def _setup_matplotlib_style(self):
        """Configure matplotlib with WSJ-inspired defaults."""
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Update matplotlib rcParams for WSJ style
        plt.rcParams.update({
            # Figure
            'figure.facecolor': self.WARM_PALETTE['surface'],
            'figure.edgecolor': 'none',
            'figure.dpi': 100,
            
            # Axes
            'axes.facecolor': self.WARM_PALETTE['surface'],
            'axes.edgecolor': self.WARM_PALETTE['grid'],
            'axes.linewidth': 0.5,
            'axes.grid': True,
            'axes.axisbelow': True,
            'axes.labelcolor': self.TYPOGRAPHY['axis_label']['color'],
            'axes.labelsize': self.TYPOGRAPHY['axis_label']['size'],
            'axes.labelweight': self.TYPOGRAPHY['axis_label']['weight'],
            'axes.titlesize': self.TYPOGRAPHY['title']['size'],
            'axes.titleweight': self.TYPOGRAPHY['title']['weight'],
            
            # Grid
            'grid.color': self.WARM_PALETTE['grid'],
            'grid.linestyle': '--',
            'grid.linewidth': 0.5,
            'grid.alpha': 0.5,
            
            # Ticks
            'xtick.color': self.TYPOGRAPHY['tick_label']['color'],
            'xtick.labelsize': self.TYPOGRAPHY['tick_label']['size'],
            'xtick.major.size': 0,
            'ytick.color': self.TYPOGRAPHY['tick_label']['color'],
            'ytick.labelsize': self.TYPOGRAPHY['tick_label']['size'],
            'ytick.major.size': 0,
            
            # Legend
            'legend.frameon': False,
            'legend.fontsize': self.TYPOGRAPHY['legend']['size'],
            'legend.labelcolor': self.TYPOGRAPHY['legend']['color'],
            
            # Font
            'font.family': 'sans-serif',
            'font.sans-serif': ['Roboto', 'Arial', 'DejaVu Sans'],
            'font.size': 12,
            
            # Lines
            'lines.linewidth': 2,
            'lines.solid_capstyle': 'round',
            'lines.solid_joinstyle': 'round',
        })
    
    def _create_colormaps(self):
        """Create custom colormaps for health visualizations."""
        # Warm gradient colormap
        colors_warm = [
            self.WARM_PALETTE['background'],
            self.WARM_PALETTE['secondary'],
            self.WARM_PALETTE['primary']
        ]
        self.cmap_warm = LinearSegmentedColormap.from_list('warm_health', colors_warm)
        
        # Diverging colormap for correlations
        colors_diverging = [
            self.WARM_PALETTE['negative'],
            self.WARM_PALETTE['surface'],
            self.WARM_PALETTE['positive']
        ]
        self.cmap_diverging = LinearSegmentedColormap.from_list('correlation', colors_diverging)
        
        # Sequential colormap for heatmaps
        colors_sequential = [
            self.WARM_PALETTE['surface'],
            self.WARM_PALETTE['background'],
            self.WARM_PALETTE['secondary'],
            self.WARM_PALETTE['primary']
        ]
        self.cmap_sequential = LinearSegmentedColormap.from_list('sequential_health', colors_sequential)
    
    def get_warm_palette(self) -> List[str]:
        """Get the warm color palette for charts."""
        return [
            self.WARM_PALETTE['primary'],
            self.WARM_PALETTE['secondary'],
            self.WARM_PALETTE['positive'],
            '#6C9BD1',  # Soft blue for variety
            '#B79FCB',  # Soft purple for variety
            self.WARM_PALETTE['negative']
        ]
    
    def get_typography_config(self) -> Dict[str, Any]:
        """Get typography configuration."""
        return self.TYPOGRAPHY.copy()
    
    def get_spacing_config(self) -> Dict[str, Any]:
        """Get spacing configuration."""
        return self.SPACING.copy()
    
    def get_accessibility_config(self) -> Dict[str, Any]:
        """Get accessibility configuration."""
        return self.ACCESSIBILITY.copy()
    
    def get_correlation_colormap(self):
        """Get colormap for correlation matrices."""
        return self.cmap_diverging
    
    def apply_chart_style(self, ax, title: str = None, subtitle: str = None,
                         x_label: str = None, y_label: str = None,
                         show_grid: bool = True, grid_style: str = 'subtle'):
        """Apply WSJ styling to a matplotlib axes."""
        # Background
        ax.set_facecolor(self.WARM_PALETTE['surface'])
        
        # Spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Grid
        if show_grid:
            ax.grid(True, linestyle='--' if grid_style == 'subtle' else '-',
                   color=self.WARM_PALETTE['grid'], alpha=0.3, linewidth=0.5)
            ax.set_axisbelow(True)
        else:
            ax.grid(False)
        
        # Title and subtitle
        if title:
            ax.set_title(title, fontsize=self.TYPOGRAPHY['title']['size'],
                        fontweight=self.TYPOGRAPHY['title']['weight'],
                        color=self.TYPOGRAPHY['title']['color'],
                        pad=self.SPACING['title_margin'])
        
        if subtitle:
            ax.text(0.5, 1.02, subtitle, transform=ax.transAxes,
                   fontsize=self.TYPOGRAPHY['subtitle']['size'],
                   color=self.TYPOGRAPHY['subtitle']['color'],
                   ha='center', va='bottom')
        
        # Labels
        if x_label:
            ax.set_xlabel(x_label, fontsize=self.TYPOGRAPHY['axis_label']['size'],
                         color=self.TYPOGRAPHY['axis_label']['color'],
                         labelpad=self.SPACING['axis_label_pad'])
        
        if y_label:
            ax.set_ylabel(y_label, fontsize=self.TYPOGRAPHY['axis_label']['size'],
                         color=self.TYPOGRAPHY['axis_label']['color'],
                         labelpad=self.SPACING['axis_label_pad'])
        
        # Tick styling
        ax.tick_params(colors=self.TYPOGRAPHY['tick_label']['color'],
                      labelsize=self.TYPOGRAPHY['tick_label']['size'],
                      length=0)
    
    def format_number(self, value: float, precision: int = 1) -> str:
        """Format numbers in WSJ style (e.g., 1.5K, 2.3M)."""
        if abs(value) >= 1e6:
            return f'{value/1e6:.{precision}f}M'
        elif abs(value) >= 1e3:
            return f'{value/1e3:.{precision}f}K'
        else:
            return f'{value:.{precision}f}'
    
    def get_pyqtgraph_style(self) -> Dict[str, Any]:
        """Get styling configuration for PyQtGraph."""
        return {
            'background': self.WARM_PALETTE['surface'],
            'foreground': self.WARM_PALETTE['text_primary'],
            'grid': {
                'color': self.WARM_PALETTE['grid'],
                'width': 0.5,
                'style': Qt.PenStyle.DashLine
            },
            'axis': {
                'color': self.WARM_PALETTE['text_secondary'],
                'font': QFont(self.TYPOGRAPHY['axis_label']['family'],
                            self.TYPOGRAPHY['axis_label']['size'])
            },
            'title': {
                'color': self.WARM_PALETTE['text_primary'],
                'font': QFont(self.TYPOGRAPHY['title']['family'],
                            self.TYPOGRAPHY['title']['size'],
                            self.TYPOGRAPHY['title']['weight'])
            }
        }
    
    def create_smart_annotation(self, ax, x: float, y: float, text: str,
                              arrow: bool = True, offset: Tuple[float, float] = (20, 20)):
        """Create a smart annotation in WSJ style."""
        annotation_style = {
            'fontsize': self.TYPOGRAPHY['annotation']['size'],
            'color': self.TYPOGRAPHY['annotation']['color'],
            'fontstyle': self.TYPOGRAPHY['annotation']['style'],
            'bbox': dict(boxstyle='round,pad=0.3', 
                        facecolor=self.WARM_PALETTE['surface'],
                        edgecolor=self.WARM_PALETTE['grid'],
                        alpha=0.9),
            'ha': 'left',
            'va': 'bottom'
        }
        
        if arrow:
            annotation_style['arrowprops'] = dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0.3',
                color=self.WARM_PALETTE['text_secondary'],
                lw=1
            )
            ax.annotate(text, xy=(x, y), xytext=offset,
                       textcoords='offset points', **annotation_style)
        else:
            ax.text(x, y, text, transform=ax.transData, **annotation_style)
    
    def apply_legend_style(self, legend):
        """Apply WSJ styling to a legend."""
        legend.get_frame().set_facecolor(self.WARM_PALETTE['surface'])
        legend.get_frame().set_edgecolor('none')
        legend.get_frame().set_alpha(0.9)
        
        for text in legend.get_texts():
            text.set_color(self.TYPOGRAPHY['legend']['color'])
            text.set_fontsize(self.TYPOGRAPHY['legend']['size'])
    
    def get_metric_color(self, metric_name: str, index: int = 0) -> str:
        """Get color for a specific metric."""
        # Define metric-specific colors
        metric_colors = {
            'steps': self.WARM_PALETTE['primary'],
            'heart_rate': self.WARM_PALETTE['negative'],
            'calories': self.WARM_PALETTE['secondary'],
            'distance': '#6C9BD1',
            'sleep': '#B79FCB',
            'active_energy': self.WARM_PALETTE['positive']
        }
        
        # Return specific color if defined, otherwise use palette
        if metric_name.lower() in metric_colors:
            return metric_colors[metric_name.lower()]
        else:
            palette = self.get_warm_palette()
            return palette[index % len(palette)]
    
    def configure_independent_axes(self, metrics: List[str]) -> Dict[str, Any]:
        """Configure independent y-axes for multi-metric charts."""
        config = {}
        for i, metric in enumerate(metrics):
            config[metric] = {
                'color': self.get_metric_color(metric, i),
                'position': 'left' if i == 0 else 'right',
                'offset': 60 * max(0, i - 1) if i > 1 else 0,
                'label_style': {
                    'color': self.get_metric_color(metric, i),
                    'fontsize': self.TYPOGRAPHY['axis_label']['size']
                }
            }
        return config
    
    def create_accessibility_description(self, chart_type: str, data_summary: Dict[str, Any]) -> str:
        """Generate accessibility description for charts."""
        descriptions = {
            'line': f"Line chart showing {data_summary.get('metric', 'data')} over time. "
                   f"Range: {data_summary.get('min', 'N/A')} to {data_summary.get('max', 'N/A')}. "
                   f"Trend: {data_summary.get('trend', 'stable')}.",
            
            'bar': f"Bar chart comparing {data_summary.get('categories', 'categories')}. "
                  f"Highest value: {data_summary.get('max', 'N/A')}. "
                  f"Lowest value: {data_summary.get('min', 'N/A')}.",
            
            'heatmap': f"Heatmap showing correlations between {data_summary.get('variables', 'variables')}. "
                      f"Strongest correlation: {data_summary.get('max_corr', 'N/A')}. "
                      f"Weakest correlation: {data_summary.get('min_corr', 'N/A')}.",
            
            'scatter': f"Scatter plot showing relationship between {data_summary.get('x_var', 'X')} "
                      f"and {data_summary.get('y_var', 'Y')}. "
                      f"Correlation: {data_summary.get('correlation', 'N/A')}."
        }
        
        return descriptions.get(chart_type, f"{chart_type} chart displaying health data.")
    
    def get_high_contrast_palette(self) -> Dict[str, str]:
        """Get high contrast color palette for accessibility."""
        return {
            'background': '#000000',
            'text': '#FFFFFF',
            'primary': '#00FF00',
            'secondary': '#FFFF00',
            'surface': '#1A1A1A',
            'positive': '#00FF00',
            'negative': '#FF0000',
            'neutral': '#FFFFFF',
            'grid': '#333333'
        }