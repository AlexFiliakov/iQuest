---
task_id: G063
status: open
created: 2025-05-28
complexity: medium
sprint_ref: S05_M01_Visualization
dependencies: [G058, G061]
parallel_group: export
---

# Task G063: Export Visualization System

## Description
Implement comprehensive export system for health visualizations including high-resolution images, PDFs, interactive HTML reports, and data exports. Support sharing, printing, and external analysis workflows.

## Goals
- [ ] Create high-resolution image export (PNG, SVG, PDF)
- [ ] Build interactive HTML report generation
- [ ] Implement data export with visualization context
- [ ] Add print optimization with page layouts
- [ ] Create shareable visualization links
- [ ] Build batch export for multiple charts

## Acceptance Criteria
- [ ] Images export at 300+ DPI for print quality
- [ ] PDF exports maintain vector graphics and fonts
- [ ] HTML reports are self-contained and interactive
- [ ] Data exports include metadata and context
- [ ] Print layouts optimize for standard paper sizes
- [ ] Batch exports complete within 30 seconds for 10 charts
- [ ] Export formats preserve WSJ styling and branding

## Technical Details

### Export Architecture
```python
class VisualizationExportSystem:
    """Comprehensive export system for health visualizations"""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.image_exporter = HighResImageExporter()
        self.pdf_exporter = VectorPDFExporter()
        self.html_exporter = InteractiveHTMLExporter()
        self.data_exporter = StructuredDataExporter()
        
    def export_chart(self, chart: VisualizationComponent, 
                    format: ExportFormat, options: ExportOptions) -> ExportResult:
        """Export single chart in specified format"""
        pass
        
    def export_dashboard(self, dashboard: HealthDashboard, 
                        format: ExportFormat) -> ExportResult:
        """Export entire dashboard as unified report"""
        pass
```

### Export Formats
1. **High-Resolution Images**: PNG, SVG with print optimization
2. **Vector PDFs**: Scalable graphics with embedded fonts
3. **Interactive HTML**: Self-contained reports with JavaScript
4. **Data Exports**: CSV, JSON with visualization metadata
5. **Print Layouts**: Optimized for A4, Letter, and tabloid sizes

### WSJ Export Standards

Based on WSJ publication quality:

1. **Print Requirements**
   - 300 DPI minimum for images
   - CMYK color space for print
   - Embedded fonts (Arial, Georgia)
   - Bleed margins for full-page charts

2. **Digital Requirements**
   - Responsive HTML exports
   - Retina display support (2x assets)
   - Accessibility metadata
   - SEO-friendly markup

3. **Color Adjustments**
   ```python
   class WSJExportColorProfiles:
       PRINT_CMYK = {
           '#F5E6D3': 'CMYK(3, 9, 17, 0)',    # Tan background
           '#FF8C42': 'CMYK(0, 45, 74, 0)',   # Orange
           '#FFD166': 'CMYK(0, 18, 60, 0)',   # Yellow
           '#6B4226': 'CMYK(30, 60, 80, 30)'  # Brown text
       }
       
       WEB_OPTIMIZED = {
           'background': '#F5E6D3',
           'primary': '#FF8C42',
           'secondary': '#FFD166',
           'text': '#6B4226'
       }
   ```

### Implementation Approaches - Pros and Cons

#### Approach 1: Native Qt Print/Export
**Pros:**
- Direct integration with Qt widgets
- Good control over rendering
- No external dependencies
- Fast for simple exports

**Cons:**
- Limited SVG support
- Complex PDF generation
- No interactive HTML

#### Approach 2: Matplotlib Export Backend
**Pros:**
- Excellent quality exports
- Multiple format support
- Publication-ready output
- Good font handling

**Cons:**
- Requires matplotlib rendering
- Less flexible for custom layouts
- Memory intensive for large exports

#### Approach 3: Web-based Export (Plotly/D3)
**Pros:**
- Interactive HTML exports
- Modern web standards
- Responsive by default
- Easy sharing

**Cons:**
- Requires web engine
- Complex print optimization
- Security considerations

### Recommended Export Strategy

1. **Primary: Matplotlib for static exports**
   - PDF reports
   - High-res images
   - Print layouts

2. **Secondary: Custom HTML generator**
   - Interactive reports
   - Web sharing
   - Email reports

3. **Tertiary: Qt native for quick exports**
   - Screenshots
   - Clipboard
   - Quick sharing

## Dependencies
- G058: Visualization Component Architecture
- G061: Multi-Metric Dashboard Layouts

## Parallel Work
- Can be developed in parallel with G064 (Performance optimization)
- Independent from other interactive features

## Implementation Notes
```python
class WSJVisualizationExporter:
    """WSJ-styled export system for health visualizations."""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.export_templates = self._load_export_templates()
        
    def export_health_report(self, dashboard: HealthDashboard, 
                           export_config: ExportConfig) -> ExportResult:
        """Export comprehensive health report with WSJ styling."""
        
        if export_config.format == ExportFormat.PDF:
            return self._export_pdf_report(dashboard, export_config)
        elif export_config.format == ExportFormat.HTML:
            return self._export_html_report(dashboard, export_config)
        elif export_config.format == ExportFormat.IMAGE:
            return self._export_image_collection(dashboard, export_config)
        else:
            raise ValueError(f"Unsupported export format: {export_config.format}")
            
    def _export_pdf_report(self, dashboard: HealthDashboard, 
                          config: ExportConfig) -> PDFExportResult:
        """Export dashboard as publication-quality PDF report."""
        
        # Create PDF with WSJ branding
        pdf_builder = WSJPDFReportBuilder(self.theme_manager)
        
        # Title page
        pdf_builder.add_title_page(
            title=dashboard.title,
            subtitle=f"Health Report - {config.date_range}",
            branding=self.theme_manager.get_export_branding()
        )
        
        # Executive summary
        summary = self._generate_executive_summary(dashboard)
        pdf_builder.add_summary_page(summary)
        
        # Individual charts
        for chart in dashboard.charts:
            # Export chart as high-resolution vector
            chart_export = self._export_chart_for_pdf(chart, config)
            
            # Add to PDF with context
            pdf_builder.add_chart_page(
                chart_image=chart_export.image,
                chart_title=chart.title,
                chart_description=chart.get_description(),
                insights=chart.get_generated_insights(),
                data_summary=chart.get_data_summary()
            )
            
        # Data appendix
        if config.include_data_appendix:
            data_tables = self._create_data_appendix(dashboard)
            pdf_builder.add_data_appendix(data_tables)
            
        return pdf_builder.build()
        
    def _export_html_report(self, dashboard: HealthDashboard, 
                           config: ExportConfig) -> HTMLExportResult:
        """Export dashboard as interactive HTML report."""
        
        html_builder = InteractiveHTMLReportBuilder(self.theme_manager)
        
        # HTML structure with embedded interactivity
        html_content = html_builder.create_report_structure(
            title=dashboard.title,
            styles=self.theme_manager.get_html_export_styles(),
            scripts=self._get_interactivity_scripts()
        )
        
        # Add dashboard content
        for chart in dashboard.charts:
            # Convert chart to interactive HTML element
            interactive_chart = self._convert_chart_to_html(chart, config)
            html_content.add_chart_section(interactive_chart)
            
        # Add data download links
        if config.include_data_downloads:
            data_links = self._create_data_download_links(dashboard)
            html_content.add_data_section(data_links)
            
        return html_builder.build_self_contained_report(html_content)
        
    def _export_chart_for_pdf(self, chart: HealthVisualizationComponent, 
                             config: ExportConfig) -> ChartExportResult:
        """Export individual chart optimized for PDF inclusion."""
        
        # Calculate optimal size for PDF
        pdf_size = self._calculate_pdf_chart_size(chart, config.page_size)
        
        # Render at high DPI
        high_res_config = RenderConfig(
            width=pdf_size.width,
            height=pdf_size.height,
            dpi=300,
            format='vector',
            background='white',
            font_scaling=1.2  # Larger fonts for print
        )
        
        # Apply print-specific styling
        print_style = self.theme_manager.get_print_chart_style(chart.chart_type)
        chart.apply_temporary_style(print_style)
        
        try:
            # Render chart
            chart_result = chart.render_for_export(high_res_config)
            
            # Add metadata
            chart_result.metadata = {
                'title': chart.title,
                'description': chart.get_description(),
                'data_range': chart.get_data_range(),
                'export_timestamp': datetime.now().isoformat(),
                'chart_type': chart.chart_type,
                'metric_types': chart.get_metric_types()
            }
            
            return chart_result
            
        finally:
            # Restore original styling
            chart.restore_original_style()
            
    def create_shareable_link(self, visualization: VisualizationComponent) -> ShareableLink:
        """Create shareable link for visualization."""
        
        # Serialize visualization state
        viz_state = {
            'chart_config': visualization.get_config(),
            'data_query': visualization.get_data_query(),
            'styling': visualization.get_current_style(),
            'interactions': visualization.get_interaction_state()
        }
        
        # Create secure share token
        share_token = self._generate_share_token(viz_state)
        
        # Store state with expiration
        self._store_shared_visualization(share_token, viz_state, ttl_days=30)
        
        return ShareableLink(
            url=f"/share/visualization/{share_token}",
            expires_at=datetime.now() + timedelta(days=30),
            access_mode='view_only'
        )
```

### Practical Export Implementation

```python
# src/ui/visualizations/export/wsj_export_manager.py
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QProgressDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from typing import List, Dict, Optional
import base64
import json

class WSJExportManager(QObject):
    """Manages all visualization exports with WSJ quality standards"""
    
    # Signals
    export_started = pyqtSignal(str)  # export_type
    export_progress = pyqtSignal(int)  # percentage
    export_completed = pyqtSignal(str)  # file_path
    export_error = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self.export_config = WSJExportConfig()
        self.current_export = None
        
    def export_dashboard_to_pdf(self, dashboard: HealthDashboard, 
                              file_path: str,
                              options: PDFExportOptions) -> None:
        """Export dashboard to publication-quality PDF"""
        
        # Create export thread
        self.current_export = PDFExportThread(
            dashboard, file_path, options, self.export_config
        )
        
        # Connect signals
        self.current_export.progress.connect(self.export_progress)
        self.current_export.completed.connect(self._on_export_completed)
        self.current_export.error.connect(self.export_error)
        
        # Start export
        self.export_started.emit('PDF')
        self.current_export.start()
        
    def export_to_interactive_html(self, dashboard: HealthDashboard,
                                 file_path: str) -> None:
        """Export dashboard as interactive HTML report"""
        
        html_content = self._generate_html_report(dashboard)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.export_completed.emit(file_path)
        except Exception as e:
            self.export_error.emit(str(e))
            
    def _generate_html_report(self, dashboard: HealthDashboard) -> str:
        """Generate self-contained HTML report"""
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{dashboard.title} - Health Report</title>
            {self._get_wsj_styles()}
            {self._get_interactive_scripts()}
        </head>
        <body>
            <div class="wsj-report-container">
                <header class="wsj-header">
                    <h1>{dashboard.title}</h1>
                    <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
                </header>
                
                <main class="wsj-content">
                    {self._generate_chart_sections(dashboard)}
                </main>
                
                <footer class="wsj-footer">
                    <p>© {datetime.now().year} Health Dashboard Report</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
    def _get_wsj_styles(self) -> str:
        """Get WSJ-styled CSS for HTML export"""
        
        return """<style>
        :root {
            --wsj-bg: #F5E6D3;
            --wsj-primary: #FF8C42;
            --wsj-secondary: #FFD166;
            --wsj-text: #6B4226;
            --wsj-border: #D4B5A0;
        }
        
        body {
            font-family: Arial, sans-serif;
            background-color: var(--wsj-bg);
            color: var(--wsj-text);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        
        .wsj-report-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border: 1px solid var(--wsj-border);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .wsj-header {
            background: var(--wsj-bg);
            padding: 30px;
            border-bottom: 2px solid var(--wsj-primary);
        }
        
        .wsj-header h1 {
            margin: 0;
            color: var(--wsj-text);
            font-size: 32px;
        }
        
        .chart-section {
            padding: 30px;
            border-bottom: 1px solid var(--wsj-border);
        }
        
        .chart-container {
            position: relative;
            width: 100%;
            min-height: 400px;
        }
        
        @media print {
            body { background: white; }
            .wsj-report-container { box-shadow: none; }
            .no-print { display: none; }
        }
        </style>"""

# src/ui/visualizations/export/pdf_export_thread.py        
class PDFExportThread(QThread):
    """Background thread for PDF export"""
    
    progress = pyqtSignal(int)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, dashboard: HealthDashboard, file_path: str,
                 options: PDFExportOptions, config: WSJExportConfig):
        super().__init__()
        self.dashboard = dashboard
        self.file_path = file_path
        self.options = options
        self.config = config
        
    def run(self):
        """Execute PDF export"""
        
        try:
            with PdfPages(self.file_path) as pdf:
                # Title page
                self._create_title_page(pdf)
                self.progress.emit(10)
                
                # Executive summary
                if self.options.include_summary:
                    self._create_summary_page(pdf)
                    self.progress.emit(20)
                
                # Export each chart
                total_charts = len(self.dashboard.charts)
                for i, (chart_id, chart) in enumerate(self.dashboard.charts.items()):
                    self._export_chart_to_pdf(pdf, chart, chart_id)
                    progress = 20 + int((i + 1) / total_charts * 60)
                    self.progress.emit(progress)
                    
                # Data appendix
                if self.options.include_data:
                    self._create_data_appendix(pdf)
                    self.progress.emit(90)
                    
                # PDF metadata
                d = pdf.infodict()
                d['Title'] = self.dashboard.title
                d['Author'] = 'Health Dashboard'
                d['Subject'] = 'Health Data Report'
                d['Keywords'] = 'Health, Dashboard, Report'
                d['CreationDate'] = datetime.now()
                
            self.progress.emit(100)
            self.completed.emit(self.file_path)
            
        except Exception as e:
            self.error.emit(f"PDF export failed: {str(e)}")
            
    def _create_title_page(self, pdf: PdfPages):
        """Create WSJ-styled title page"""
        
        fig = plt.figure(figsize=(8.5, 11))
        fig.patch.set_facecolor('#F5E6D3')
        
        # Remove axes
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.7, self.dashboard.title,
                ha='center', va='center',
                fontsize=28, fontweight='bold',
                color='#6B4226')
                
        # Subtitle
        ax.text(0.5, 0.6, 'Health Data Report',
                ha='center', va='center',
                fontsize=18,
                color='#6B4226')
                
        # Date
        ax.text(0.5, 0.5, datetime.now().strftime('%B %d, %Y'),
                ha='center', va='center',
                fontsize=14,
                color='#FF8C42')
                
        # Border
        rect = plt.Rectangle((0.1, 0.1), 0.8, 0.8,
                           fill=False, edgecolor='#D4B5A0',
                           linewidth=2)
        ax.add_patch(rect)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

# src/ui/visualizations/export/share_manager.py
class VisualizationShareManager:
    """Manages sharing of visualizations"""
    
    def __init__(self):
        self.share_cache = {}
        self.base_url = "https://health-dashboard.example.com/share/"
        
    def create_shareable_link(self, visualization: VisualizationComponent,
                            expiry_days: int = 30) -> ShareableLink:
        """Create shareable link for visualization"""
        
        # Generate unique ID
        share_id = self._generate_share_id()
        
        # Serialize visualization state
        viz_data = {
            'type': visualization.__class__.__name__,
            'data': visualization.get_data().to_json(),
            'config': visualization.get_config(),
            'theme': 'wsj',
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=expiry_days)).isoformat()
        }
        
        # Store in cache (in production, use database)
        self.share_cache[share_id] = viz_data
        
        # Create shareable link
        return ShareableLink(
            url=f"{self.base_url}{share_id}",
            share_id=share_id,
            expires_at=datetime.now() + timedelta(days=expiry_days),
            qr_code=self._generate_qr_code(f"{self.base_url}{share_id}")
        )
        
    def export_for_email(self, visualization: VisualizationComponent) -> EmailExport:
        """Export visualization for email embedding"""
        
        # Render as image
        img_buffer = visualization.render_to_buffer(
            width=600, height=400, dpi=150
        )
        
        # Convert to base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Generate HTML snippet
        html_snippet = f"""
        <div style="background: #F5E6D3; padding: 20px; border-radius: 8px;">
            <h2 style="color: #6B4226; font-family: Arial;">{visualization.title}</h2>
            <img src="data:image/png;base64,{img_base64}" 
                 style="width: 100%; max-width: 600px; border: 1px solid #D4B5A0;">
            <p style="color: #6B4226; margin-top: 10px;">
                {visualization.get_description()}
            </p>
        </div>
        """
        
        return EmailExport(
            html=html_snippet,
            plain_text=visualization.get_text_summary(),
            attachments=[{
                'filename': f'{visualization.title}.png',
                'content': img_buffer.getvalue(),
                'content_type': 'image/png'
            }]
        )
```