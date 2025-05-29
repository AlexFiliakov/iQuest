"""WSJ-styled export manager for health visualizations."""

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt6.QtWidgets import QProgressDialog, QFileDialog, QMessageBox
from PyQt6.QtGui import QImage, QPainter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import base64
import json
import io
from datetime import datetime
import logging

from .export_models import (
    ExportFormat, ExportConfig, PDFExportOptions, HTMLExportOptions,
    ImageExportOptions, DataExportOptions, ExportResult, PDFExportResult,
    HTMLExportResult, ChartExportResult, WSJExportConfig, ExportProgress,
    BatchExportConfig
)
from .pdf_export_thread import PDFExportThread
from .html_export_builder import HTMLExportBuilder
from .image_exporter import HighResImageExporter
from .data_exporter import StructuredDataExporter
from ..wsj_style_manager import WSJStyleManager

logger = logging.getLogger(__name__)


class WSJExportManager(QObject):
    """Manages all visualization exports with WSJ quality standards."""
    
    # Signals
    export_started = pyqtSignal(str)  # export_type
    export_progress = pyqtSignal(int)  # percentage
    export_completed = pyqtSignal(str)  # file_path
    export_error = pyqtSignal(str)  # error_message
    export_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the export manager."""
        super().__init__(parent)
        self.style_manager = WSJStyleManager()
        self.export_config = WSJExportConfig()
        self.current_export = None
        self.mutex = QMutex()
        
        # Initialize exporters
        self.image_exporter = HighResImageExporter(self.style_manager)
        self.html_builder = HTMLExportBuilder(self.style_manager)
        self.data_exporter = StructuredDataExporter()
        
        # Progress tracking
        self.progress_tracker = None
        
    def export_chart(self, chart: Any, format: ExportFormat, 
                    options: Optional[Dict[str, Any]] = None) -> ExportResult:
        """Export a single chart in the specified format."""
        with QMutexLocker(self.mutex):
            if self.current_export:
                return ExportResult(
                    success=False,
                    error_message="Another export is in progress"
                )
        
        try:
            self.export_started.emit(format.value)
            
            if format == ExportFormat.PNG:
                return self._export_chart_as_png(chart, options or {})
            elif format == ExportFormat.SVG:
                return self._export_chart_as_svg(chart, options or {})
            elif format == ExportFormat.PDF:
                return self._export_chart_as_pdf(chart, options or {})
            else:
                return ExportResult(
                    success=False,
                    error_message=f"Format {format.value} not supported for single charts"
                )
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            self.export_error.emit(str(e))
            return ExportResult(success=False, error_message=str(e))
        finally:
            self.current_export = None
            
    def export_dashboard(self, dashboard: Any, format: ExportFormat,
                        file_path: Optional[Path] = None,
                        options: Optional[Dict[str, Any]] = None) -> None:
        """Export entire dashboard in the specified format."""
        if not file_path:
            file_path = self._get_save_file_path(format)
            if not file_path:
                return
                
        if format == ExportFormat.PDF:
            self._export_dashboard_as_pdf(dashboard, file_path, options)
        elif format == ExportFormat.HTML:
            self._export_dashboard_as_html(dashboard, file_path, options)
        elif format in [ExportFormat.PNG, ExportFormat.SVG]:
            self._export_dashboard_as_image(dashboard, file_path, format, options)
        elif format in [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.EXCEL]:
            self._export_dashboard_data(dashboard, file_path, format, options)
        else:
            self.export_error.emit(f"Unsupported format: {format.value}")
            
    def _export_dashboard_as_pdf(self, dashboard: Any, file_path: Path,
                                options: Optional[Dict[str, Any]] = None):
        """Export dashboard to PDF in background thread."""
        pdf_options = PDFExportOptions(**(options or {}))
        
        # Create export thread
        self.current_export = PDFExportThread(
            dashboard, str(file_path), pdf_options, self.export_config
        )
        
        # Connect signals
        self.current_export.progress.connect(self.export_progress)
        self.current_export.completed.connect(self._on_pdf_export_completed)
        self.current_export.error.connect(self.export_error)
        
        # Start export
        self.export_started.emit('PDF')
        self.current_export.start()
        
    def _export_dashboard_as_html(self, dashboard: Any, file_path: Path,
                                 options: Optional[Dict[str, Any]] = None):
        """Export dashboard as interactive HTML report."""
        try:
            self.export_started.emit('HTML')
            
            html_options = HTMLExportOptions(**(options or {}))
            html_content = self.html_builder.build_dashboard_report(
                dashboard, html_options
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.export_completed.emit(str(file_path))
            
        except Exception as e:
            logger.error(f"HTML export failed: {str(e)}")
            self.export_error.emit(str(e))
            
    def _export_dashboard_as_image(self, dashboard: Any, file_path: Path,
                                  format: ExportFormat, 
                                  options: Optional[Dict[str, Any]] = None):
        """Export dashboard as a single image."""
        try:
            self.export_started.emit(format.value)
            
            # Create composite image
            image_options = ImageExportOptions(**(options or {}))
            result = self.image_exporter.export_dashboard_composite(
                dashboard, format, image_options
            )
            
            if result.success:
                # Save to file
                if format == ExportFormat.PNG:
                    result.image.save(str(file_path), 'PNG', 
                                    quality=image_options.compression_quality)
                elif format == ExportFormat.SVG:
                    with open(file_path, 'w') as f:
                        f.write(result.image)
                        
                self.export_completed.emit(str(file_path))
            else:
                self.export_error.emit(result.error_message)
                
        except Exception as e:
            logger.error(f"Image export failed: {str(e)}")
            self.export_error.emit(str(e))
            
    def _export_dashboard_data(self, dashboard: Any, file_path: Path,
                              format: ExportFormat,
                              options: Optional[Dict[str, Any]] = None):
        """Export dashboard data in various formats."""
        try:
            self.export_started.emit(format.value)
            
            data_options = DataExportOptions(**(options or {}))
            
            # Collect all data from dashboard
            all_data = self._collect_dashboard_data(dashboard, data_options)
            
            # Export based on format
            if format == ExportFormat.CSV:
                self._save_as_csv(all_data, file_path, data_options)
            elif format == ExportFormat.JSON:
                self._save_as_json(all_data, file_path, data_options)
            elif format == ExportFormat.EXCEL:
                self._save_as_excel(all_data, file_path, data_options)
                
            self.export_completed.emit(str(file_path))
            
        except Exception as e:
            logger.error(f"Data export failed: {str(e)}")
            self.export_error.emit(str(e))
            
    def batch_export(self, charts: List[Any], config: BatchExportConfig) -> None:
        """Export multiple charts in batch."""
        self.progress_tracker = ExportProgress(
            total_items=len(charts),
            completed_items=0
        )
        
        try:
            self.export_started.emit(f"Batch {config.format.value}")
            
            if config.combine_into_single_file and config.format == ExportFormat.PDF:
                self._batch_export_pdf(charts, config)
            else:
                self._batch_export_individual(charts, config)
                
        except Exception as e:
            logger.error(f"Batch export failed: {str(e)}")
            self.export_error.emit(str(e))
            
    def _batch_export_pdf(self, charts: List[Any], config: BatchExportConfig):
        """Export multiple charts into a single PDF."""
        output_path = config.output_directory / f"{config.file_prefix}.pdf"
        
        with PdfPages(str(output_path)) as pdf:
            for i, chart in enumerate(charts):
                self.progress_tracker.current_item = f"Chart {i+1}/{len(charts)}"
                
                # Export chart
                fig = self._render_chart_for_pdf(chart)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
                
                # Update progress
                self.progress_tracker.completed_items = i + 1
                self.export_progress.emit(self.progress_tracker.percentage)
                
        self.export_completed.emit(str(output_path))
        
    def _batch_export_individual(self, charts: List[Any], config: BatchExportConfig):
        """Export charts as individual files."""
        for i, chart in enumerate(charts):
            self.progress_tracker.current_item = f"Chart {i+1}/{len(charts)}"
            
            # Generate filename
            filename = f"{config.file_prefix}_{i+1}.{config.format.value}"
            output_path = config.output_directory / filename
            
            # Export based on format
            if config.format in [ExportFormat.PNG, ExportFormat.SVG]:
                result = self.export_chart(chart, config.format)
                if result.success and result.file_path:
                    result.file_path.rename(output_path)
                    
            # Update progress
            self.progress_tracker.completed_items = i + 1
            self.export_progress.emit(self.progress_tracker.percentage)
            
        self.export_completed.emit(str(config.output_directory))
        
    def _export_chart_as_png(self, chart: Any, options: Dict[str, Any]) -> ExportResult:
        """Export chart as PNG image."""
        image_options = ImageExportOptions(**options)
        return self.image_exporter.export_chart(chart, ExportFormat.PNG, image_options)
        
    def _export_chart_as_svg(self, chart: Any, options: Dict[str, Any]) -> ExportResult:
        """Export chart as SVG image."""
        image_options = ImageExportOptions(**options)
        return self.image_exporter.export_chart(chart, ExportFormat.SVG, image_options)
        
    def _export_chart_as_pdf(self, chart: Any, options: Dict[str, Any]) -> ExportResult:
        """Export single chart as PDF."""
        try:
            # Get save location
            file_path = self._get_save_file_path(ExportFormat.PDF)
            if not file_path:
                return ExportResult(success=False, error_message="Export cancelled")
                
            # Render chart
            fig = self._render_chart_for_pdf(chart)
            
            # Save as PDF
            fig.savefig(str(file_path), format='pdf', bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            return PDFExportResult(
                success=True,
                file_path=file_path,
                page_count=1
            )
            
        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            return ExportResult(success=False, error_message=str(e))
            
    def _render_chart_for_pdf(self, chart: Any) -> plt.Figure:
        """Render chart for PDF export."""
        # Create figure with WSJ styling
        fig = plt.figure(figsize=(10, 6), facecolor='white')
        ax = fig.add_subplot(111)
        
        # Apply WSJ style
        self.style_manager.apply_chart_style(
            ax,
            title=getattr(chart, 'title', 'Health Chart'),
            subtitle=getattr(chart, 'subtitle', None)
        )
        
        # Render chart data
        if hasattr(chart, 'render_to_axes'):
            chart.render_to_axes(ax)
        else:
            # Fallback rendering
            ax.text(0.5, 0.5, 'Chart Export', ha='center', va='center',
                   transform=ax.transAxes, fontsize=20)
            
        return fig
        
    def _collect_dashboard_data(self, dashboard: Any, 
                               options: DataExportOptions) -> Dict[str, pd.DataFrame]:
        """Collect all data from dashboard charts."""
        data_collection = {}
        
        for chart_id, chart in dashboard.charts.items():
            if hasattr(chart, 'get_data'):
                df = chart.get_data()
                
                if options.include_metadata:
                    # Add metadata columns
                    df['_chart_type'] = chart.__class__.__name__
                    df['_export_date'] = datetime.now().strftime(options.date_format)
                    
                if options.include_calculations and hasattr(chart, 'get_calculations'):
                    # Merge calculations
                    calcs = chart.get_calculations()
                    for calc_name, calc_value in calcs.items():
                        df[f'_calc_{calc_name}'] = calc_value
                        
                data_collection[chart_id] = df
                
        return data_collection
        
    def _save_as_csv(self, data: Dict[str, pd.DataFrame], file_path: Path,
                    options: DataExportOptions):
        """Save data as CSV files."""
        if len(data) == 1:
            # Single dataset - save directly
            df = list(data.values())[0]
            df.to_csv(file_path, index=False, 
                     date_format=options.date_format,
                     float_format=f'%.{options.decimal_places}f')
        else:
            # Multiple datasets - save as separate files
            base_path = file_path.with_suffix('')
            for name, df in data.items():
                csv_path = f"{base_path}_{name}.csv"
                df.to_csv(csv_path, index=False,
                         date_format=options.date_format,
                         float_format=f'%.{options.decimal_places}f')
                         
    def _save_as_json(self, data: Dict[str, pd.DataFrame], file_path: Path,
                     options: DataExportOptions):
        """Save data as JSON."""
        json_data = {}
        
        for name, df in data.items():
            json_data[name] = df.to_dict(orient='records')
            
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
            
    def _save_as_excel(self, data: Dict[str, pd.DataFrame], file_path: Path,
                      options: DataExportOptions):
        """Save data as Excel file with multiple sheets."""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for name, df in data.items():
                # Truncate sheet name if too long
                sheet_name = name[:31] if len(name) > 31 else name
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
    def _get_save_file_path(self, format: ExportFormat) -> Optional[Path]:
        """Get file path from user via dialog."""
        file_filter = {
            ExportFormat.PNG: "PNG Image (*.png)",
            ExportFormat.SVG: "SVG Image (*.svg)",
            ExportFormat.PDF: "PDF Document (*.pdf)",
            ExportFormat.HTML: "HTML Document (*.html)",
            ExportFormat.CSV: "CSV File (*.csv)",
            ExportFormat.JSON: "JSON File (*.json)",
            ExportFormat.EXCEL: "Excel File (*.xlsx)"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            f"Export as {format.value.upper()}",
            f"health_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format.value}",
            file_filter.get(format, "All Files (*.*)")
        )
        
        return Path(file_path) if file_path else None
        
    def _on_pdf_export_completed(self, file_path: str):
        """Handle PDF export completion."""
        self.export_completed.emit(file_path)
        self.current_export = None
        
    def cancel_export(self):
        """Cancel current export operation."""
        if self.current_export and hasattr(self.current_export, 'cancel'):
            self.current_export.cancel()
            self.export_cancelled.emit()
            self.current_export = None