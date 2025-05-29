"""High-resolution image exporter for health visualizations."""

import io
from typing import Any, Optional, Union
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
import numpy as np
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPainter, QImage, QPixmap
from PyQt6.QtWidgets import QWidget
import logging

from .export_models import (
    ExportFormat, ImageExportOptions, ExportResult, 
    ChartExportResult, RenderConfig
)
from ..wsj_style_manager import WSJStyleManager

logger = logging.getLogger(__name__)


class HighResImageExporter:
    """Exports charts as high-resolution images with WSJ styling."""
    
    def __init__(self, style_manager: WSJStyleManager):
        """Initialize image exporter."""
        self.style_manager = style_manager
        
    def export_chart(self, chart: Any, format: ExportFormat,
                    options: ImageExportOptions) -> ExportResult:
        """Export single chart as image."""
        try:
            if format == ExportFormat.PNG:
                return self._export_as_png(chart, options)
            elif format == ExportFormat.SVG:
                return self._export_as_svg(chart, options)
            else:
                return ExportResult(
                    success=False,
                    error_message=f"Unsupported image format: {format}"
                )
        except Exception as e:
            logger.error(f"Image export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
            
    def export_dashboard_composite(self, dashboard: Any, format: ExportFormat,
                                 options: ImageExportOptions) -> ExportResult:
        """Export entire dashboard as composite image."""
        try:
            # Calculate grid layout
            num_charts = len(dashboard.charts)
            cols = min(3, num_charts)
            rows = (num_charts + cols - 1) // cols
            
            # Create figure with subplots
            fig_width = options.width / options.dpi
            fig_height = options.height / options.dpi
            
            fig = plt.figure(figsize=(fig_width, fig_height), dpi=options.dpi)
            fig.patch.set_facecolor('white' if not options.transparent_background 
                                  else 'none')
            
            # Add title
            fig.suptitle(dashboard.title, fontsize=24, fontweight='bold',
                        color=self.style_manager.WARM_PALETTE['text_primary'],
                        y=0.98)
            
            # Create subplots for each chart
            for i, (chart_id, chart) in enumerate(dashboard.charts.items()):
                ax = fig.add_subplot(rows, cols, i + 1)
                self._render_chart_to_axes(chart, ax)
                
            # Adjust layout
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            # Export based on format
            if format == ExportFormat.PNG:
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', 
                          bbox_inches='tight',
                          facecolor=fig.get_facecolor(),
                          edgecolor='none',
                          dpi=options.dpi)
                img_buffer.seek(0)
                
                # Convert to PIL Image
                image = Image.open(img_buffer)
                
                # Add watermark if requested
                if options.include_watermark:
                    image = self._add_watermark(image)
                    
                return ExportResult(
                    success=True,
                    metadata={'format': 'PNG', 'size': image.size}
                )
                
            elif format == ExportFormat.SVG:
                svg_buffer = io.StringIO()
                fig.savefig(svg_buffer, format='svg', 
                          bbox_inches='tight')
                svg_content = svg_buffer.getvalue()
                
                return ExportResult(
                    success=True,
                    metadata={'format': 'SVG', 'content': svg_content}
                )
                
        except Exception as e:
            logger.error(f"Dashboard composite export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
        finally:
            plt.close(fig)
            
    def _export_as_png(self, chart: Any, options: ImageExportOptions) -> ExportResult:
        """Export chart as PNG image."""
        try:
            # Check if chart is a Qt widget
            if isinstance(chart, QWidget):
                return self._export_qt_widget_as_png(chart, options)
            
            # Otherwise assume matplotlib figure or axes
            fig = self._get_figure_from_chart(chart, options)
            
            # Create buffer
            img_buffer = io.BytesIO()
            
            # Configure DPI and size
            fig.set_size_inches(options.width / options.dpi, 
                              options.height / options.dpi)
            
            # Save to buffer
            fig.savefig(img_buffer, format='png',
                      dpi=options.dpi,
                      bbox_inches='tight',
                      facecolor='white' if not options.transparent_background else 'none',
                      edgecolor='none')
                      
            img_buffer.seek(0)
            
            # Load as PIL Image for potential post-processing
            image = Image.open(img_buffer)
            
            # Add watermark if requested
            if options.include_watermark:
                image = self._add_watermark(image)
                
            # Compress if needed
            final_buffer = io.BytesIO()
            image.save(final_buffer, 'PNG', 
                      optimize=True,
                      quality=options.compression_quality)
            final_buffer.seek(0)
            
            return ExportResult(
                success=True,
                metadata={
                    'format': 'PNG',
                    'size': image.size,
                    'dpi': options.dpi,
                    'file_size': final_buffer.getbuffer().nbytes
                }
            )
            
        except Exception as e:
            logger.error(f"PNG export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
        finally:
            if 'fig' in locals():
                plt.close(fig)
                
    def _export_as_svg(self, chart: Any, options: ImageExportOptions) -> ExportResult:
        """Export chart as SVG vector image."""
        try:
            fig = self._get_figure_from_chart(chart, options)
            
            # Create SVG buffer
            svg_buffer = io.StringIO()
            
            # Configure size
            fig.set_size_inches(options.width / 100, options.height / 100)
            
            # Save as SVG
            canvas = FigureCanvasSVG(fig)
            canvas.print_svg(svg_buffer)
            
            svg_content = svg_buffer.getvalue()
            
            # Post-process SVG
            svg_content = self._optimize_svg(svg_content, options)
            
            return ExportResult(
                success=True,
                metadata={
                    'format': 'SVG',
                    'content': svg_content,
                    'scalable': True
                }
            )
            
        except Exception as e:
            logger.error(f"SVG export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
        finally:
            if 'fig' in locals():
                plt.close(fig)
                
    def _export_qt_widget_as_png(self, widget: QWidget, 
                                options: ImageExportOptions) -> ExportResult:
        """Export Qt widget as PNG."""
        try:
            # Create QImage with desired size and DPI
            scale_factor = options.dpi / 96.0  # 96 DPI is typical screen DPI
            img_width = int(options.width * scale_factor)
            img_height = int(options.height * scale_factor)
            
            image = QImage(img_width, img_height, QImage.Format.Format_ARGB32)
            image.setDotsPerMeterX(int(options.dpi * 39.37))  # Convert DPI to dots per meter
            image.setDotsPerMeterY(int(options.dpi * 39.37))
            
            # Fill background
            if options.transparent_background:
                image.fill(Qt.GlobalColor.transparent)
            else:
                image.fill(Qt.GlobalColor.white)
                
            # Render widget to image
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Scale if needed
            if scale_factor != 1.0:
                painter.scale(scale_factor, scale_factor)
                
            widget.render(painter)
            painter.end()
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, 'PNG', options.compression_quality)
            img_buffer.seek(0)
            
            return ExportResult(
                success=True,
                metadata={
                    'format': 'PNG',
                    'size': (img_width, img_height),
                    'dpi': options.dpi,
                    'source': 'Qt Widget'
                }
            )
            
        except Exception as e:
            logger.error(f"Qt widget PNG export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
            
    def _get_figure_from_chart(self, chart: Any, options: ImageExportOptions) -> plt.Figure:
        """Extract or create matplotlib figure from chart."""
        # If chart has get_figure method
        if hasattr(chart, 'get_figure'):
            return chart.get_figure()
            
        # If chart is already a figure
        if isinstance(chart, plt.Figure):
            return chart
            
        # If chart is axes
        if isinstance(chart, plt.Axes):
            return chart.get_figure()
            
        # Create new figure and render chart
        fig = plt.figure(figsize=(options.width / options.dpi, 
                                options.height / options.dpi))
        ax = fig.add_subplot(111)
        
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=getattr(chart, 'title', 'Health Chart')
        )
        
        # Try to render chart
        if hasattr(chart, 'render_to_axes'):
            chart.render_to_axes(ax)
        elif hasattr(chart, 'plot'):
            chart.plot(ax=ax)
        else:
            # Fallback - just show title
            ax.text(0.5, 0.5, 'Chart Export',
                   ha='center', va='center',
                   transform=ax.transAxes,
                   fontsize=20)
                   
        return fig
        
    def _render_chart_to_axes(self, chart: Any, ax: plt.Axes):
        """Render chart to matplotlib axes."""
        # Apply WSJ styling
        self.style_manager.apply_chart_style(
            ax,
            title=getattr(chart, 'title', ''),
            subtitle=getattr(chart, 'subtitle', '')
        )
        
        # Render chart data
        if hasattr(chart, 'render_to_axes'):
            chart.render_to_axes(ax)
        elif hasattr(chart, 'data') and hasattr(chart.data, 'plot'):
            # Assume pandas DataFrame
            chart.data.plot(ax=ax, color=self.style_manager.get_warm_palette())
        else:
            # Placeholder
            ax.text(0.5, 0.5, getattr(chart, 'title', 'Chart'),
                   ha='center', va='center',
                   transform=ax.transAxes)
                   
    def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to image."""
        # Create drawing context
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # Watermark text
        watermark_text = "Health Dashboard Report"
        
        # Try to load font (fallback to default if not available)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            
        # Calculate position (bottom right)
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = image.width - text_width - 20
        y = image.height - text_height - 20
        
        # Draw semi-transparent watermark
        draw.text((x, y), watermark_text, 
                 fill=(200, 200, 200, 128), 
                 font=font)
                 
        return image
        
    def _optimize_svg(self, svg_content: str, options: ImageExportOptions) -> str:
        """Optimize SVG content."""
        # Remove unnecessary whitespace
        lines = svg_content.split('\n')
        optimized_lines = [line.strip() for line in lines if line.strip()]
        
        # Add title and description for accessibility
        if '</title>' not in svg_content:
            # Insert after opening SVG tag
            for i, line in enumerate(optimized_lines):
                if '<svg' in line and '>' in line:
                    optimized_lines.insert(i + 1, '<title>Health Chart</title>')
                    optimized_lines.insert(i + 2, '<desc>Exported health visualization</desc>')
                    break
                    
        return '\n'.join(optimized_lines)
        
    def render_chart_for_export(self, chart: Any, config: RenderConfig) -> ChartExportResult:
        """Render chart with specific configuration for export."""
        try:
            # Create figure with exact dimensions
            fig = plt.figure(figsize=(config.width / config.dpi, 
                                    config.height / config.dpi),
                           dpi=config.dpi)
            fig.patch.set_facecolor(config.background)
            
            # Create axes
            ax = fig.add_subplot(111)
            
            # Apply font scaling
            original_sizes = {}
            for key in ['axes.labelsize', 'axes.titlesize', 'xtick.labelsize', 
                       'ytick.labelsize', 'legend.fontsize']:
                original_sizes[key] = plt.rcParams[key]
                plt.rcParams[key] = plt.rcParams[key] * config.font_scaling
                
            try:
                # Render chart
                self._render_chart_to_axes(chart, ax)
                
                # Convert to desired format
                if config.format == 'vector':
                    # Return figure for vector processing
                    result = ChartExportResult(
                        image=fig,
                        metadata={'type': 'matplotlib.figure'}
                    )
                else:
                    # Rasterize to image
                    canvas = FigureCanvasAgg(fig)
                    canvas.draw()
                    
                    # Get image data
                    buf = canvas.buffer_rgba()
                    w, h = canvas.get_width_height()
                    image = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'RGBA', 0, 1)
                    
                    # Convert color space if needed
                    if config.color_space == 'CMYK':
                        image = image.convert('CMYK')
                        
                    result = ChartExportResult(
                        image=image,
                        metadata={'type': 'PIL.Image', 'color_space': config.color_space}
                    )
                    
            finally:
                # Restore font sizes
                for key, value in original_sizes.items():
                    plt.rcParams[key] = value
                    
            return result
            
        except Exception as e:
            logger.error(f"Chart render for export failed: {str(e)}")
            raise
        finally:
            if 'fig' in locals() and config.format != 'vector':
                plt.close(fig)