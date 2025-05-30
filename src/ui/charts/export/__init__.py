"""Professional export system for health data visualizations and reports.

This module provides comprehensive export capabilities that transform health data
visualizations into publication-ready documents, shareable reports, and high-quality
presentations. The export system maintains WSJ-inspired design standards while
offering flexibility for different output formats and use cases.

The export system includes:

- **PDF Export**: Multi-page reports with professional typography and layout
- **HTML Export**: Interactive web-based reports with embedded charts and data
- **High-Resolution Images**: Print-quality PNG, SVG, and vector formats
- **Data Export**: Structured CSV, JSON, and Excel formats with metadata
- **Print Layout Management**: Optimized layouts for various paper sizes and printers
- **Sharing and Collaboration**: Secure link generation and email distribution
- **Batch Processing**: Automated export of multiple charts and time periods

The export system is designed for:
- **Clinical Presentations**: Medical-grade reports for healthcare providers
- **Research Publications**: Academic-quality figures and data tables
- **Personal Documentation**: User-friendly health summaries and trend reports
- **Regulatory Compliance**: Structured exports for health record requirements

All exports maintain data integrity, include comprehensive metadata, and follow
accessibility standards for universal document compatibility.

Key Features:
- WSJ-inspired professional styling across all export formats
- Embedded chart interactivity in HTML exports
- High-DPI support for retina displays and high-quality printing
- Automatic chart optimization for different output dimensions
- Comprehensive metadata inclusion for data provenance
- HIPAA-compliant security measures for sensitive health data

Example:
    Exporting a comprehensive health report:
    
    >>> from ui.charts.export import WSJExportManager, ExportConfig
    >>> export_manager = WSJExportManager()
    >>> config = ExportConfig(
    ...     format=ExportFormat.PDF,
    ...     include_data_tables=True,
    ...     include_summary_statistics=True
    ... )
    >>> result = export_manager.export_health_report(charts, config)
    
    Batch exporting multiple time periods:
    
    >>> from ui.charts.export import BatchExportConfig
    >>> batch_config = BatchExportConfig(
    ...     time_periods=['monthly', 'quarterly', 'yearly'],
    ...     formats=[ExportFormat.PDF, ExportFormat.HTML]
    ... )
    >>> results = export_manager.batch_export(data, batch_config)

Note:
    All exports respect user privacy settings and include appropriate disclaimers
    for health data. Exported files can be configured with password protection
    and access controls as needed.
"""

from .export_models import (
    ExportFormat, ExportConfig, PDFExportOptions, HTMLExportOptions,
    ImageExportOptions, DataExportOptions, RenderConfig, ExportResult,
    PDFExportResult, HTMLExportResult, ChartExportResult, ShareableLink,
    EmailExport, BatchExportConfig, ExportProgress, WSJExportConfig,
    PageSize, PrintQuality
)
from .wsj_export_manager import WSJExportManager
from .pdf_export_thread import PDFExportThread
from .html_export_builder import HTMLExportBuilder
from .image_exporter import HighResImageExporter
from .data_exporter import StructuredDataExporter
from .share_manager import VisualizationShareManager
from .print_layout_manager import PrintLayoutManager, PrintMargins, ChartPlacement

__all__ = [
    # Models
    'ExportFormat', 'ExportConfig', 'PDFExportOptions', 'HTMLExportOptions',
    'ImageExportOptions', 'DataExportOptions', 'RenderConfig', 'ExportResult',
    'PDFExportResult', 'HTMLExportResult', 'ChartExportResult', 'ShareableLink',
    'EmailExport', 'BatchExportConfig', 'ExportProgress', 'WSJExportConfig',
    'PageSize', 'PrintQuality',
    
    # Managers and Exporters
    'WSJExportManager', 'PDFExportThread', 'HTMLExportBuilder',
    'HighResImageExporter', 'StructuredDataExporter', 'VisualizationShareManager',
    'PrintLayoutManager', 'PrintMargins', 'ChartPlacement'
]