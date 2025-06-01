"""HTML export builder for interactive health reports."""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..wsj_style_manager import WSJStyleManager
from .export_models import HTMLExportOptions


class HTMLExportBuilder:
    """Builds interactive HTML reports with WSJ styling."""
    
    def __init__(self, style_manager: WSJStyleManager):
        """Initialize HTML builder."""
        self.style_manager = style_manager
        
    def build_dashboard_report(self, dashboard: Any, 
                             options: HTMLExportOptions) -> str:
        """Build complete HTML report for dashboard."""
        html_parts = []
        
        # HTML header
        html_parts.append(self._create_html_header(
            title=dashboard.title,
            options=options
        ))
        
        # Body content
        html_parts.append('<body>')
        
        # Report container
        html_parts.append('<div class="wsj-report-container">')
        
        # Header section
        html_parts.append(self._create_report_header(dashboard))
        
        # Navigation
        if len(dashboard.charts) > 3:
            html_parts.append(self._create_navigation(dashboard))
        
        # Main content
        html_parts.append('<main class="wsj-content">')
        
        # Executive summary
        html_parts.append(self._create_executive_summary(dashboard))
        
        # Chart sections
        for chart_id, chart in dashboard.charts.items():
            html_parts.append(self._create_chart_section(chart_id, chart, options))
            
        html_parts.append('</main>')
        
        # Data download section
        if options.include_data_download:
            html_parts.append(self._create_download_section(dashboard))
            
        # Footer
        html_parts.append(self._create_report_footer())
        
        html_parts.append('</div>')  # End container
        
        # Scripts
        if options.include_scripts:
            html_parts.append(self._create_interactive_scripts())
            
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
        
    def _create_html_header(self, title: str, options: HTMLExportOptions) -> str:
        """Create HTML header with styles and meta tags."""
        header = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Health Dashboard Report - {title}">
    <title>{title} - Health Report</title>
    {self._get_favicon()}
    {self._get_wsj_styles() if options.include_styles else ''}
    {self._get_chart_styles() if options.include_styles else ''}
    {self._get_responsive_styles() if options.responsive else ''}
    {self._get_print_styles()}
</head>"""
        return header
        
    def _get_favicon(self) -> str:
        """Get favicon for the report."""
        return '''<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23FF8C42'/%3E%3Ctext x='16' y='22' text-anchor='middle' fill='white' font-family='Arial' font-size='20' font-weight='bold'%3EH%3C/text%3E%3C/svg%3E">'''
        
    def _get_wsj_styles(self) -> str:
        """Get WSJ-inspired CSS styles."""
        colors = self.style_manager.WARM_PALETTE
        return f"""<style>
:root {{
    --wsj-bg: {colors['background']};
    --wsj-primary: {colors['primary']};
    --wsj-secondary: {colors['secondary']};
    --wsj-surface: {colors['surface']};
    --wsj-text-primary: {colors['text_primary']};
    --wsj-text-secondary: {colors['text_secondary']};
    --wsj-grid: {colors['grid']};
    --wsj-positive: {colors['positive']};
    --wsj-negative: {colors['negative']};
    --wsj-neutral: {colors['neutral']};
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Arial, sans-serif;
    background-color: var(--wsj-bg);
    color: var(--wsj-text-primary);
    line-height: 1.6;
    font-size: 16px;
}}

.wsj-report-container {{
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.wsj-header {{
    background: var(--wsj-surface);
    padding: 40px;
    border-bottom: 3px solid var(--wsj-primary);
    text-align: center;
}}

.wsj-header h1 {{
    margin: 0 0 10px 0;
    color: var(--wsj-text-primary);
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -0.02em;
}}

.wsj-header .subtitle {{
    color: var(--wsj-text-secondary);
    font-size: 18px;
    margin: 0;
}}

.wsj-header .date {{
    color: var(--wsj-primary);
    font-size: 16px;
    margin-top: 10px;
}}

.wsj-nav {{
    background: var(--wsj-surface);
    padding: 20px 40px;
    border-bottom: 1px solid var(--wsj-grid);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.wsj-nav ul {{
    list-style: none;
    display: flex;
    gap: 30px;
    flex-wrap: wrap;
    justify-content: center;
}}

.wsj-nav a {{
    color: var(--wsj-text-primary);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}}

.wsj-nav a:hover {{
    color: var(--wsj-primary);
}}

.wsj-content {{
    padding: 40px;
}}

.chart-section {{
    margin-bottom: 60px;
    padding: 30px;
    background: var(--wsj-surface);
    border-radius: 8px;
    border: 1px solid var(--wsj-grid);
}}

.chart-section h2 {{
    color: var(--wsj-text-primary);
    font-size: 24px;
    margin-bottom: 10px;
    font-weight: 600;
}}

.chart-section .description {{
    color: var(--wsj-text-secondary);
    margin-bottom: 20px;
}}

.chart-container {{
    position: relative;
    width: 100%;
    min-height: 400px;
    background: white;
    border-radius: 4px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}}

.chart-insights {{
    margin-top: 20px;
    padding: 15px;
    background: #FFF9F0;
    border-left: 4px solid var(--wsj-primary);
    border-radius: 4px;
}}

.chart-insights h3 {{
    color: var(--wsj-primary);
    font-size: 16px;
    margin-bottom: 8px;
}}

.metric-card {{
    background: white;
    border: 1px solid var(--wsj-grid);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}}

.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}

.metric-value {{
    font-size: 36px;
    font-weight: 700;
    color: var(--wsj-primary);
    margin: 10px 0;
}}

.metric-name {{
    color: var(--wsj-text-secondary);
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.metric-trend {{
    font-size: 18px;
    margin-top: 10px;
}}

.trend-up {{ color: var(--wsj-positive); }}
.trend-down {{ color: var(--wsj-negative); }}
.trend-stable {{ color: var(--wsj-neutral); }}

.wsj-footer {{
    background: var(--wsj-surface);
    padding: 30px 40px;
    text-align: center;
    border-top: 1px solid var(--wsj-grid);
    color: var(--wsj-text-secondary);
    font-size: 14px;
}}

.download-section {{
    background: var(--wsj-surface);
    padding: 30px;
    margin: 40px 0;
    border-radius: 8px;
    text-align: center;
}}

.download-btn {{
    display: inline-block;
    padding: 12px 24px;
    background: var(--wsj-primary);
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 500;
    transition: background 0.2s;
    margin: 5px;
}}

.download-btn:hover {{
    background: #E67C32;
}}

.executive-summary {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin: 40px 0;
}}
</style>"""

    def _get_chart_styles(self) -> str:
        """Get styles specific to chart rendering."""
        return """<style>
.chart-svg {
    width: 100%;
    height: auto;
    max-width: 100%;
}

.chart-image {
    width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}

.chart-interactive {
    position: relative;
    overflow: hidden;
}

.chart-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: var(--wsj-text-secondary);
}

.chart-error {
    padding: 40px;
    text-align: center;
    color: var(--wsj-negative);
    background: #FFF0F0;
    border-radius: 4px;
}

.tooltip {
    position: absolute;
    padding: 10px;
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid var(--wsj-grid);
    border-radius: 4px;
    font-size: 14px;
    pointer-events: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    z-index: 1000;
}
</style>"""

    def _get_responsive_styles(self) -> str:
        """Get responsive CSS for mobile devices."""
        return """<style>
@media (max-width: 768px) {
    .wsj-header {
        padding: 20px;
    }
    
    .wsj-header h1 {
        font-size: 28px;
    }
    
    .wsj-content {
        padding: 20px;
    }
    
    .chart-section {
        padding: 20px;
    }
    
    .executive-summary {
        grid-template-columns: 1fr;
    }
    
    .wsj-nav ul {
        flex-direction: column;
        gap: 10px;
    }
    
    .metric-value {
        font-size: 28px;
    }
}

@media (max-width: 480px) {
    .wsj-header h1 {
        font-size: 24px;
    }
    
    .chart-container {
        min-height: 300px;
        padding: 10px;
    }
}
</style>"""

    def _get_print_styles(self) -> str:
        """Get print-specific styles."""
        return """<style>
@media print {
    body {
        background: white;
        color: black;
    }
    
    .wsj-report-container {
        box-shadow: none;
    }
    
    .wsj-nav {
        display: none;
    }
    
    .download-section {
        display: none;
    }
    
    .chart-section {
        page-break-inside: avoid;
        border: 1px solid #ccc;
    }
    
    .wsj-header {
        background: white;
        border-bottom: 2px solid black;
    }
    
    a {
        color: black;
        text-decoration: none;
    }
}
</style>"""

    def _create_report_header(self, dashboard: Any) -> str:
        """Create report header section."""
        date_range = getattr(dashboard, 'date_range', 'All Available Data')
        return f"""
<header class="wsj-header">
    <h1>{dashboard.title}</h1>
    <p class="subtitle">Comprehensive Health Analytics Report</p>
    <p class="date">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
    <p class="date">Period: {date_range}</p>
</header>"""

    def _create_navigation(self, dashboard: Any) -> str:
        """Create navigation menu for charts."""
        nav_items = []
        nav_items.append('<a href="#summary">Summary</a>')
        
        for chart_id in dashboard.charts.keys():
            display_name = chart_id.replace('_', ' ').title()
            nav_items.append(f'<a href="#{chart_id}">{display_name}</a>')
            
        return f"""
<nav class="wsj-nav">
    <ul>
        {''.join(f'<li>{item}</li>' for item in nav_items)}
    </ul>
</nav>"""

    def _create_executive_summary(self, dashboard: Any) -> str:
        """Create executive summary section."""
        summary_html = ['<section id="summary" class="executive-summary">']
        
        # Get key metrics
        if hasattr(dashboard, 'get_key_metrics'):
            metrics = dashboard.get_key_metrics()
        else:
            # Fallback metrics
            metrics = {
                'Total Charts': {'value': len(dashboard.charts), 'trend': 'stable'},
                'Report Date': {'value': datetime.now().strftime('%Y-%m-%d'), 'trend': 'stable'}
            }
            
        for metric_name, metric_data in metrics.items():
            trend = metric_data.get('trend', 'stable')
            trend_symbol = {'up': '↑', 'down': '↓', 'stable': '→'}.get(trend, '→')
            trend_class = f'trend-{trend}'
            
            summary_html.append(f"""
<div class="metric-card">
    <div class="metric-name">{metric_name}</div>
    <div class="metric-value">{metric_data.get('value', 'N/A')}</div>
    <div class="metric-trend {trend_class}">{trend_symbol} {metric_data.get('change', '')}</div>
</div>""")
            
        summary_html.append('</section>')
        return ''.join(summary_html)
        
    def _create_chart_section(self, chart_id: str, chart: Any, 
                            options: HTMLExportOptions) -> str:
        """Create section for individual chart."""
        title = getattr(chart, 'title', chart_id.replace('_', ' ').title())
        description = getattr(chart, 'description', '')
        
        section_html = [f'<section id="{chart_id}" class="chart-section">']
        section_html.append(f'<h2>{title}</h2>')
        
        if description:
            section_html.append(f'<p class="description">{description}</p>')
            
        section_html.append('<div class="chart-container">')
        
        # Render chart
        if options.interactive and hasattr(chart, 'to_html'):
            # Interactive chart
            section_html.append(chart.to_html())
        else:
            # Static image
            image_data = self._chart_to_base64(chart)
            section_html.append(f'<img class="chart-image" src="{image_data}" alt="{title}">')
            
        section_html.append('</div>')
        
        # Add insights if available
        if hasattr(chart, 'get_insights'):
            insights = chart.get_insights()
            if insights:
                section_html.append(f"""
<div class="chart-insights">
    <h3>Key Insights</h3>
    <p>{insights}</p>
</div>""")
                
        section_html.append('</section>')
        return ''.join(section_html)
        
    def _chart_to_base64(self, chart: Any) -> str:
        """Convert chart to base64 encoded image."""
        try:
            # Try to get image data from chart
            if hasattr(chart, 'to_image'):
                img_bytes = chart.to_image(format='png')
            elif hasattr(chart, 'get_image_data'):
                img_bytes = chart.get_image_data()
            else:
                # Fallback - create placeholder
                return self._create_placeholder_image()
                
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode()
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error converting chart to image: {e}")
            return self._create_placeholder_image()
            
    def _create_placeholder_image(self) -> str:
        """Create placeholder image for missing charts."""
        svg = """<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="#F5E6D3"/>
            <text x="300" y="200" text-anchor="middle" fill="#6B4226" 
                  font-family="Arial" font-size="18">Chart Placeholder</text>
        </svg>"""
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"
        
    def _create_download_section(self, dashboard: Any) -> str:
        """Create data download section."""
        return """
<section class="download-section">
    <h2>Download Data</h2>
    <p>Export this report and underlying data in various formats:</p>
    <div>
        <a href="#" class="download-btn" onclick="window.print(); return false;">Print Report</a>
        <a href="#" class="download-btn" data-export="csv">Download CSV</a>
        <a href="#" class="download-btn" data-export="json">Download JSON</a>
        <a href="#" class="download-btn" data-export="excel">Download Excel</a>
    </div>
</section>"""

    def _create_report_footer(self) -> str:
        """Create report footer."""
        return f"""
<footer class="wsj-footer">
    <p>© {datetime.now().year} Health Dashboard Report</p>
    <p>Generated by Health Analytics System</p>
</footer>"""

    def _create_interactive_scripts(self) -> str:
        """Create JavaScript for interactivity."""
        return """<script>
// Smooth scrolling for navigation
document.querySelectorAll('.wsj-nav a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Download handlers
document.querySelectorAll('[data-export]').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const format = this.getAttribute('data-export');
        alert(`Export to ${format.toUpperCase()} would be implemented here`);
    });
});

// Print optimization
window.addEventListener('beforeprint', function() {
    document.body.classList.add('printing');
});

window.addEventListener('afterprint', function() {
    document.body.classList.remove('printing');
});

// Add interactive tooltips if supported
if (typeof Chart !== 'undefined') {
    // Chart.js tooltip configuration
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.95)';
    Chart.defaults.plugins.tooltip.borderColor = '#E9ECEF';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.titleColor = '#2C2C2C';
    Chart.defaults.plugins.tooltip.bodyColor = '#666666';
}
</script>"""