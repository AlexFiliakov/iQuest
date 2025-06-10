"""Background thread for PDF export with WSJ styling."""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PyQt6.QtCore import QThread, pyqtSignal

from ..wsj_style_manager import WSJStyleManager
from .export_models import PDFExportOptions, WSJExportConfig

logger = logging.getLogger(__name__)


class PDFExportThread(QThread):
    """Background thread for PDF export with progress tracking."""
    
    progress = pyqtSignal(int)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    
    def __init__(self, dashboard: Any, file_path: str,
                 options: PDFExportOptions, config: WSJExportConfig):
        """Initialize PDF export thread."""
        super().__init__()
        self.dashboard = dashboard
        self.file_path = file_path
        self.options = options
        self.config = config
        self.style_manager = WSJStyleManager()
        self._cancelled = False
        
    def run(self):
        """Execute PDF export with WSJ styling."""
        try:
            with PdfPages(self.file_path) as pdf:
                # Title page
                self.status_update.emit("Creating title page...")
                self._create_title_page(pdf)
                self.progress.emit(10)
                
                if self._cancelled:
                    return
                
                # Executive summary
                if self.options.include_summary:
                    self.status_update.emit("Generating executive summary...")
                    self._create_summary_page(pdf)
                    self.progress.emit(20)
                    
                if self._cancelled:
                    return
                
                # Export each chart
                total_charts = len(self.dashboard.charts)
                for i, (chart_id, chart) in enumerate(self.dashboard.charts.items()):
                    if self._cancelled:
                        return
                        
                    self.status_update.emit(f"Exporting chart {i+1}/{total_charts}: {chart_id}")
                    self._export_chart_to_pdf(pdf, chart, chart_id)
                    progress = 20 + int((i + 1) / total_charts * 60)
                    self.progress.emit(progress)
                    
                # Data appendix
                if self.options.include_data:
                    self.status_update.emit("Creating data appendix...")
                    self._create_data_appendix(pdf)
                    self.progress.emit(90)
                    
                # PDF metadata
                if self.options.include_metadata:
                    d = pdf.infodict()
                    d['Title'] = self.options.title or self.dashboard.title
                    d['Author'] = self.options.author
                    d['Subject'] = 'Health Data Report'
                    d['Keywords'] = 'Health, Dashboard, Analytics, WSJ Style'
                    d['StartDate'] = datetime.now()
                
            self.progress.emit(100)
            self.completed.emit(self.file_path)
            
        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            logger.error(traceback.format_exc())
            self.error.emit(f"PDF export failed: {str(e)}")
            
    def _create_title_page(self, pdf: PdfPages):
        """Create WSJ-styled title page."""
        fig = plt.figure(figsize=(8.5, 11))
        fig.patch.set_facecolor(self.style_manager.WARM_PALETTE['background'])
        
        # Remove axes
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Title background
        title_bg = Rectangle((0.05, 0.65), 0.9, 0.15,
                           facecolor=self.style_manager.WARM_PALETTE['surface'],
                           edgecolor='none', alpha=0.8,
                           transform=ax.transAxes)
        ax.add_patch(title_bg)
        
        # Title
        ax.text(0.5, 0.72, self.dashboard.title,
                ha='center', va='center',
                fontsize=32, fontweight='bold',
                color=self.style_manager.WARM_PALETTE['text_primary'],
                transform=ax.transAxes)
                
        # Subtitle
        ax.text(0.5, 0.62, 'Comprehensive Health Analytics Report',
                ha='center', va='center',
                fontsize=18,
                color=self.style_manager.WARM_PALETTE['text_secondary'],
                transform=ax.transAxes)
                
        # Date range
        date_range = getattr(self.dashboard, 'date_range', 'All Available Data')
        ax.text(0.5, 0.55, f'Period: {date_range}',
                ha='center', va='center',
                fontsize=14,
                color=self.style_manager.WARM_PALETTE['primary'],
                transform=ax.transAxes)
                
        # Generation date
        ax.text(0.5, 0.48, f'Generated on {datetime.now().strftime("%B %d, %Y")}',
                ha='center', va='center',
                fontsize=12,
                color=self.style_manager.WARM_PALETTE['text_secondary'],
                transform=ax.transAxes)
                
        # Decorative border
        border = Rectangle((0.05, 0.05), 0.9, 0.9,
                         fill=False, 
                         edgecolor=self.style_manager.WARM_PALETTE['primary'],
                         linewidth=2,
                         transform=ax.transAxes)
        ax.add_patch(border)
        
        # WSJ-style accent line
        ax.plot([0.2, 0.8], [0.4, 0.4], 
               color=self.style_manager.WARM_PALETTE['secondary'],
               linewidth=3, transform=ax.transAxes)
        
        # Footer
        ax.text(0.5, 0.1, self.config.branding['footer_text'],
                ha='center', va='center',
                fontsize=10,
                color=self.style_manager.WARM_PALETTE['text_secondary'],
                transform=ax.transAxes)
        
        pdf.savefig(fig, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        
    def _create_summary_page(self, pdf: PdfPages):
        """Create executive summary page with key metrics."""
        fig = plt.figure(figsize=(8.5, 11))
        fig.patch.set_facecolor('white')
        
        # Create grid for summary
        gs = fig.add_gridspec(5, 2, hspace=0.4, wspace=0.3,
                            left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # Title
        fig.text(0.5, 0.95, 'Executive Summary',
                ha='center', va='center',
                fontsize=24, fontweight='bold',
                color=self.style_manager.WARM_PALETTE['text_primary'])
        
        # Collect key metrics from dashboard
        metrics = self._collect_key_metrics()
        
        # Display metrics in grid
        for i, (metric_name, metric_data) in enumerate(metrics.items()):
            if i >= 8:  # Max 8 metrics per page
                break
                
            row = (i // 2) + 1
            col = i % 2
            ax = fig.add_subplot(gs[row, col])
            
            self._create_metric_card(ax, metric_name, metric_data)
            
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
    def _create_metric_card(self, ax, metric_name: str, metric_data: Dict[str, Any]):
        """Create a metric card in WSJ style."""
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Card background
        card_bg = Rectangle((0, 0), 1, 1,
                          facecolor=self.style_manager.WARM_PALETTE['surface'],
                          edgecolor=self.style_manager.WARM_PALETTE['grid'],
                          linewidth=1)
        ax.add_patch(card_bg)
        
        # Metric name
        ax.text(0.5, 0.85, metric_name,
                ha='center', va='center',
                fontsize=14, fontweight='bold',
                color=self.style_manager.WARM_PALETTE['text_primary'])
        
        # Metric value
        value = metric_data.get('value', 'N/A')
        ax.text(0.5, 0.5, str(value),
                ha='center', va='center',
                fontsize=24, fontweight='bold',
                color=self.style_manager.WARM_PALETTE['primary'])
        
        # Trend indicator
        trend = metric_data.get('trend', 'stable')
        trend_color = {
            'up': self.style_manager.WARM_PALETTE['positive'],
            'down': self.style_manager.WARM_PALETTE['negative'],
            'stable': self.style_manager.WARM_PALETTE['neutral']
        }.get(trend, self.style_manager.WARM_PALETTE['neutral'])
        
        trend_symbol = {'up': '↑', 'down': '↓', 'stable': '→'}.get(trend, '→')
        
        ax.text(0.8, 0.5, trend_symbol,
                ha='center', va='center',
                fontsize=20, color=trend_color)
        
        # Context
        context = metric_data.get('context', '')
        if context:
            ax.text(0.5, 0.2, context,
                    ha='center', va='center',
                    fontsize=10,
                    color=self.style_manager.WARM_PALETTE['text_secondary'])
                    
    def _export_chart_to_pdf(self, pdf: PdfPages, chart: Any, chart_id: str):
        """Export individual chart with WSJ styling."""
        # Determine page orientation based on chart type
        if hasattr(chart, 'preferred_size'):
            fig_size = chart.preferred_size
        else:
            fig_size = (10, 6) if self.options.orientation == 'landscape' else (8.5, 11)
            
        fig = plt.figure(figsize=fig_size)
        fig.patch.set_facecolor('white')
        
        # Create main plot area
        ax = fig.add_subplot(111)
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=getattr(chart, 'title', chart_id),
            subtitle=getattr(chart, 'subtitle', None)
        )
        
        # Render chart
        if hasattr(chart, 'render_to_axes'):
            chart.render_to_axes(ax)
        elif hasattr(chart, 'get_figure'):
            # If chart provides its own figure
            plt.close(fig)
            fig = chart.get_figure()
        else:
            # Fallback - try to extract data and plot
            self._render_fallback_chart(ax, chart, chart_id)
            
        # Add insights if available
        if hasattr(chart, 'get_insights'):
            insights = chart.get_insights()
            if insights:
                fig.text(0.1, 0.02, f"Key Insights: {insights}",
                        fontsize=10,
                        color=self.style_manager.WARM_PALETTE['text_secondary'],
                        wrap=True)
                        
        # Save to PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
    def _render_fallback_chart(self, ax, chart: Any, chart_id: str):
        """Fallback rendering for charts without render method."""
        # Try to get data
        if hasattr(chart, 'data'):
            data = chart.data
            if isinstance(data, pd.DataFrame) and not data.empty:
                # Simple line plot for time series
                if 'date' in data.columns or data.index.name == 'date':
                    data.plot(ax=ax, color=self.style_manager.get_warm_palette())
                else:
                    # Bar plot for categorical
                    data.plot(kind='bar', ax=ax, 
                            color=self.style_manager.get_warm_palette())
            else:
                ax.text(0.5, 0.5, f'Chart: {chart_id}',
                       ha='center', va='center',
                       transform=ax.transAxes, fontsize=16)
        else:
            ax.text(0.5, 0.5, f'No data available for {chart_id}',
                   ha='center', va='center',
                   transform=ax.transAxes, fontsize=14,
                   color=self.style_manager.WARM_PALETTE['text_secondary'])
                   
    def _create_data_appendix(self, pdf: PdfPages):
        """Create data appendix with tables."""
        fig = plt.figure(figsize=(8.5, 11))
        fig.patch.set_facecolor('white')
        
        # Title
        fig.text(0.5, 0.95, 'Data Appendix',
                ha='center', va='center',
                fontsize=24, fontweight='bold',
                color=self.style_manager.WARM_PALETTE['text_primary'])
                
        # Create table of available data
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Collect data summary
        data_summary = []
        for chart_id, chart in self.dashboard.charts.items():
            if hasattr(chart, 'get_data_summary'):
                summary = chart.get_data_summary()
                data_summary.append([
                    chart_id,
                    summary.get('rows', 'N/A'),
                    summary.get('date_range', 'N/A'),
                    summary.get('metrics', 'N/A')
                ])
                
        if data_summary:
            # Create table
            table = ax.table(cellText=data_summary,
                           colLabels=['Chart', 'Data Points', 'Date Range', 'Metrics'],
                           cellLoc='left',
                           loc='center',
                           colWidths=[0.25, 0.15, 0.3, 0.3])
                           
            # Style table
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)
            
            # Apply WSJ colors
            for i in range(len(data_summary) + 1):
                for j in range(4):
                    cell = table[(i, j)]
                    if i == 0:  # Header row
                        cell.set_facecolor(self.style_manager.WARM_PALETTE['primary'])
                        cell.set_text_props(weight='bold', 
                                          color='white')
                    else:
                        cell.set_facecolor(self.style_manager.WARM_PALETTE['surface']
                                         if i % 2 == 0 else 'white')
                        cell.set_text_props(
                            color=self.style_manager.WARM_PALETTE['text_primary'])
                            
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
    def _collect_key_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Collect key metrics from dashboard for summary."""
        metrics = {}
        
        # Try to get metrics from dashboard
        if hasattr(self.dashboard, 'get_key_metrics'):
            return self.dashboard.get_key_metrics()
            
        # Fallback - collect from individual charts
        for chart_id, chart in self.dashboard.charts.items():
            if hasattr(chart, 'get_summary_metric'):
                metric = chart.get_summary_metric()
                if metric:
                    metrics[metric['name']] = metric
                    
        # If no metrics found, create placeholder
        if not metrics:
            metrics = {
                'Total Charts': {'value': len(self.dashboard.charts), 'trend': 'stable'},
                'Date Range': {'value': getattr(self.dashboard, 'date_range', 'All Data'), 
                             'trend': 'stable'}
            }
            
        return metrics
        
    def cancel(self):
        """Cancel the export operation."""
        self._cancelled = True