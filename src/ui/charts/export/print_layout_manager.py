"""Print layout optimization for health visualizations."""

from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import math
from dataclasses import dataclass

from .export_models import PageSize, PrintQuality
from ..wsj_style_manager import WSJStyleManager


@dataclass
class PrintMargins:
    """Print margins in millimeters."""
    top: float = 20
    right: float = 15
    bottom: float = 20
    left: float = 15


@dataclass
class ChartPlacement:
    """Chart placement on page."""
    x: float  # mm from left
    y: float  # mm from top
    width: float  # mm
    height: float  # mm
    page: int


class PrintLayoutManager:
    """Manages print layouts for health visualizations."""
    
    # Standard DPI conversions
    MM_TO_INCH = 0.0393701
    INCH_TO_MM = 25.4
    
    def __init__(self, style_manager: WSJStyleManager):
        """Initialize print layout manager."""
        self.style_manager = style_manager
        
    def optimize_layout(self, charts: List[Any], 
                       page_size: PageSize = PageSize.A4,
                       orientation: str = "portrait",
                       margins: Optional[PrintMargins] = None) -> List[ChartPlacement]:
        """Optimize chart layout for printing."""
        margins = margins or PrintMargins()
        
        # Get page dimensions
        page_width, page_height = self._get_page_dimensions(page_size, orientation)
        
        # Calculate printable area
        printable_width = page_width - margins.left - margins.right
        printable_height = page_height - margins.top - margins.bottom
        
        # Determine optimal layout based on chart count
        placements = []
        
        if len(charts) == 1:
            # Single chart - use full page
            placements.append(ChartPlacement(
                x=margins.left,
                y=margins.top,
                width=printable_width,
                height=printable_height,
                page=1
            ))
        elif len(charts) == 2:
            # Two charts - stack vertically or side by side
            if orientation == "portrait":
                # Stack vertically
                chart_height = (printable_height - 10) / 2  # 10mm gap
                for i in range(2):
                    placements.append(ChartPlacement(
                        x=margins.left,
                        y=margins.top + i * (chart_height + 10),
                        width=printable_width,
                        height=chart_height,
                        page=1
                    ))
            else:
                # Side by side
                chart_width = (printable_width - 10) / 2  # 10mm gap
                for i in range(2):
                    placements.append(ChartPlacement(
                        x=margins.left + i * (chart_width + 10),
                        y=margins.top,
                        width=chart_width,
                        height=printable_height,
                        page=1
                    ))
        else:
            # Multiple charts - use grid layout
            placements = self._create_grid_layout(
                len(charts), page_width, page_height, margins
            )
            
        return placements[:len(charts)]
        
    def create_print_css(self, page_size: PageSize = PageSize.A4,
                        orientation: str = "portrait") -> str:
        """Generate print-specific CSS."""
        page_width, page_height = self._get_page_dimensions(page_size, orientation)
        
        # Convert to CSS units (inches work well for print)
        width_in = page_width * self.MM_TO_INCH
        height_in = page_height * self.MM_TO_INCH
        
        colors = self.style_manager.WARM_PALETTE
        
        return f"""
@media print {{
    /* Page setup */
    @page {{
        size: {width_in}in {height_in}in;
        margin: 0.75in;
        
        @top-center {{
            content: "Health Dashboard Report";
            font-family: Arial, sans-serif;
            font-size: 10pt;
            color: {colors['text_secondary']};
        }}
        
        @bottom-center {{
            content: counter(page) " of " counter(pages);
            font-family: Arial, sans-serif;
            font-size: 10pt;
            color: {colors['text_secondary']};
        }}
    }}
    
    /* General print styles */
    body {{
        margin: 0;
        padding: 0;
        background: white;
        color: black;
        font-family: Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.4;
    }}
    
    /* Hide non-print elements */
    .no-print,
    .navigation,
    .interactive-controls,
    .download-buttons {{
        display: none !important;
    }}
    
    /* Chart containers */
    .chart-container {{
        page-break-inside: avoid;
        break-inside: avoid;
        margin-bottom: 20pt;
        border: 1pt solid #ccc;
        padding: 10pt;
    }}
    
    /* Ensure charts fit on page */
    .chart-image,
    svg {{
        max-width: 100% !important;
        height: auto !important;
    }}
    
    /* Headers and titles */
    h1, h2, h3 {{
        page-break-after: avoid;
        break-after: avoid;
        color: {colors['text_primary']};
    }}
    
    h1 {{
        font-size: 18pt;
        margin-bottom: 12pt;
        border-bottom: 2pt solid {colors['primary']};
        padding-bottom: 6pt;
    }}
    
    h2 {{
        font-size: 14pt;
        margin-bottom: 8pt;
        color: {colors['primary']};
    }}
    
    /* Tables */
    table {{
        page-break-inside: avoid;
        border-collapse: collapse;
        width: 100%;
        margin: 10pt 0;
    }}
    
    th {{
        background-color: {colors['primary']};
        color: white;
        padding: 6pt;
        text-align: left;
        font-weight: bold;
    }}
    
    td {{
        padding: 4pt 6pt;
        border-bottom: 0.5pt solid #ddd;
    }}
    
    tr:nth-child(even) {{
        background-color: #f9f9f9;
    }}
    
    /* Insights and notes */
    .chart-insights {{
        background-color: #f5f5f5;
        border-left: 3pt solid {colors['primary']};
        padding: 8pt;
        margin: 10pt 0;
        font-size: 10pt;
    }}
    
    /* Force new page for major sections */
    .page-break {{
        page-break-before: always;
        break-before: always;
    }}
    
    /* Optimize images for print */
    img {{
        max-resolution: 300dpi;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
    }}
    
    /* Links - show URL */
    a[href]:after {{
        content: " (" attr(href) ")";
        font-size: 9pt;
        color: #666;
    }}
    
    /* Ensure good contrast */
    * {{
        background: white !important;
        color: black !important;
        text-shadow: none !important;
    }}
    
    /* Keep important colors */
    .chart-line,
    .chart-bar,
    .data-point {{
        color: inherit !important;
        fill: currentColor !important;
    }}
}}

/* High-quality print */
@media print and (min-resolution: 300dpi) {{
    .chart-container {{
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
    }}
}}
        """
        
    def calculate_chart_dimensions(self, aspect_ratio: float,
                                 available_width: float,
                                 available_height: float) -> Tuple[float, float]:
        """Calculate optimal chart dimensions maintaining aspect ratio."""
        # Try width-constrained first
        width = available_width
        height = width / aspect_ratio
        
        # Check if height fits
        if height > available_height:
            # Height-constrained instead
            height = available_height
            width = height * aspect_ratio
            
        return width, height
        
    def get_recommended_dpi(self, quality: PrintQuality,
                          chart_type: str = "generic") -> int:
        """Get recommended DPI for chart type and quality."""
        # Base DPI from quality setting
        base_dpi = quality.value
        
        # Adjust based on chart type
        adjustments = {
            'line_chart': 1.0,  # Line charts look good at base DPI
            'bar_chart': 0.9,   # Bar charts can use slightly lower
            'heatmap': 1.2,     # Heatmaps benefit from higher DPI
            'scatter': 1.1,     # Scatter plots need good point definition
            'text_heavy': 1.3,  # Charts with lots of text need higher DPI
            'generic': 1.0
        }
        
        multiplier = adjustments.get(chart_type, 1.0)
        return int(base_dpi * multiplier)
        
    def create_page_header(self, title: str, page_num: int, 
                         total_pages: int) -> Dict[str, Any]:
        """Create page header configuration."""
        return {
            'title': title,
            'page_text': f"Page {page_num} of {total_pages}",
            'style': {
                'font_family': 'Arial, sans-serif',
                'font_size': 12,
                'color': self.style_manager.WARM_PALETTE['text_secondary'],
                'border_bottom': f"1px solid {self.style_manager.WARM_PALETTE['grid']}"
            }
        }
        
    def create_page_footer(self, text: str = "Health Dashboard Report") -> Dict[str, Any]:
        """Create page footer configuration."""
        return {
            'text': text,
            'timestamp': True,
            'style': {
                'font_family': 'Arial, sans-serif',
                'font_size': 10,
                'color': self.style_manager.WARM_PALETTE['text_secondary'],
                'border_top': f"1px solid {self.style_manager.WARM_PALETTE['grid']}"
            }
        }
        
    def _get_page_dimensions(self, page_size: PageSize, 
                           orientation: str) -> Tuple[float, float]:
        """Get page dimensions in mm."""
        if page_size == PageSize.CUSTOM:
            # Default to A4 for custom
            width, height = 210, 297
        else:
            width, height = page_size.value
            
        # Swap for landscape
        if orientation == "landscape":
            width, height = height, width
            
        return width, height
        
    def _create_grid_layout(self, num_charts: int, 
                          page_width: float, page_height: float,
                          margins: PrintMargins) -> List[ChartPlacement]:
        """Create grid layout for multiple charts."""
        placements = []
        
        # Calculate printable area
        printable_width = page_width - margins.left - margins.right
        printable_height = page_height - margins.top - margins.bottom
        
        # Determine grid size
        if num_charts <= 4:
            cols, rows = 2, 2
        elif num_charts <= 6:
            cols, rows = 2, 3
        elif num_charts <= 9:
            cols, rows = 3, 3
        else:
            cols = 3
            rows = math.ceil(num_charts / cols)
            
        # Calculate cell size with gaps
        gap = 10  # mm between charts
        cell_width = (printable_width - (cols - 1) * gap) / cols
        cell_height = (printable_height - (rows - 1) * gap) / rows
        
        # Limit to reasonable aspect ratio
        max_aspect_ratio = 1.5
        if cell_width / cell_height > max_aspect_ratio:
            cell_width = cell_height * max_aspect_ratio
        elif cell_height / cell_width > max_aspect_ratio:
            cell_height = cell_width * max_aspect_ratio
            
        # Create placements
        current_page = 1
        charts_per_page = cols * rows
        
        for i in range(num_charts):
            page_index = i % charts_per_page
            if i > 0 and page_index == 0:
                current_page += 1
                
            row = page_index // cols
            col = page_index % cols
            
            x = margins.left + col * (cell_width + gap)
            y = margins.top + row * (cell_height + gap)
            
            placements.append(ChartPlacement(
                x=x,
                y=y,
                width=cell_width,
                height=cell_height,
                page=current_page
            ))
            
        return placements
        
    def optimize_for_paper_size(self, content_width: float, 
                              content_height: float) -> PageSize:
        """Recommend optimal paper size for content."""
        # Add margins
        required_width = content_width + 30  # 15mm margins each side
        required_height = content_height + 40  # 20mm margins top/bottom
        
        # Check standard sizes
        sizes = [
            (PageSize.A4, 210, 297),
            (PageSize.LETTER, 216, 279),
            (PageSize.A3, 297, 420),
            (PageSize.TABLOID, 279, 432)
        ]
        
        for page_size, width, height in sizes:
            if required_width <= width and required_height <= height:
                return page_size
            # Also check landscape
            if required_width <= height and required_height <= width:
                return page_size
                
        # Default to largest if content is very big
        return PageSize.TABLOID