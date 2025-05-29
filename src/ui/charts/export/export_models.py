"""Data models for visualization export system."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class PageSize(Enum):
    """Standard page sizes for print layouts."""
    A4 = (210, 297)  # mm
    LETTER = (216, 279)  # mm
    TABLOID = (279, 432)  # mm
    A3 = (297, 420)  # mm
    CUSTOM = None


class PrintQuality(Enum):
    """Print quality settings."""
    DRAFT = 150  # DPI
    STANDARD = 300  # DPI
    HIGH = 600  # DPI
    PROFESSIONAL = 1200  # DPI


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    format: ExportFormat
    date_range: str = ""
    include_data_appendix: bool = False
    include_data_downloads: bool = True
    page_size: PageSize = PageSize.A4
    quality: PrintQuality = PrintQuality.STANDARD
    background_color: str = "white"
    embed_fonts: bool = True
    compress: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PDFExportOptions:
    """PDF-specific export options."""
    include_summary: bool = True
    include_data: bool = True
    include_metadata: bool = True
    page_size: PageSize = PageSize.A4
    orientation: str = "portrait"
    margins: Tuple[float, float, float, float] = (20, 20, 20, 20)  # mm
    compress_images: bool = True
    embed_fonts: bool = True
    author: str = "Health Dashboard"
    title: str = "Health Report"


@dataclass
class HTMLExportOptions:
    """HTML-specific export options."""
    include_scripts: bool = True
    include_styles: bool = True
    self_contained: bool = True
    interactive: bool = True
    responsive: bool = True
    include_data_download: bool = True
    theme: str = "wsj"


@dataclass
class ImageExportOptions:
    """Image-specific export options."""
    width: int = 1920
    height: int = 1080
    dpi: int = 300
    transparent_background: bool = False
    include_watermark: bool = False
    compression_quality: int = 95  # For JPEG


@dataclass
class DataExportOptions:
    """Data export options."""
    include_metadata: bool = True
    include_calculations: bool = True
    include_visualizations: bool = False
    date_format: str = "%Y-%m-%d"
    decimal_places: int = 2
    null_value: str = ""


@dataclass
class RenderConfig:
    """Configuration for chart rendering."""
    width: int
    height: int
    dpi: int = 300
    format: str = 'vector'
    background: str = 'white'
    font_scaling: float = 1.0
    anti_alias: bool = True
    color_space: str = 'RGB'  # RGB or CMYK for print


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    file_path: Optional[Path] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    export_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PDFExportResult(ExportResult):
    """PDF-specific export result."""
    page_count: int = 0
    embedded_fonts: List[str] = field(default_factory=list)


@dataclass
class HTMLExportResult(ExportResult):
    """HTML-specific export result."""
    includes_scripts: bool = False
    includes_styles: bool = False
    is_self_contained: bool = False


@dataclass
class ChartExportResult:
    """Result of individual chart export."""
    image: Any  # PIL Image or matplotlib figure
    metadata: Dict[str, Any] = field(default_factory=dict)
    render_time: float = 0.0
    memory_usage: int = 0


@dataclass
class ShareableLink:
    """Shareable link for visualization."""
    url: str
    share_id: str
    expires_at: datetime
    qr_code: Optional[str] = None  # Base64 encoded QR code
    access_mode: str = "view_only"
    password_protected: bool = False


@dataclass
class EmailExport:
    """Email export data."""
    html: str
    plain_text: str
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    subject: str = "Health Dashboard Report"
    
    
@dataclass
class BatchExportConfig:
    """Configuration for batch exports."""
    charts: List[str]  # Chart IDs to export
    format: ExportFormat
    output_directory: Path
    file_prefix: str = "health_export"
    combine_into_single_file: bool = False
    parallel_processing: bool = True
    max_workers: int = 4


@dataclass
class ExportProgress:
    """Progress tracking for export operations."""
    total_items: int
    completed_items: int = 0
    current_item: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    
    @property
    def percentage(self) -> int:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 0
        return int((self.completed_items / self.total_items) * 100)
    
    @property
    def elapsed_time(self) -> timedelta:
        """Calculate elapsed time."""
        return datetime.now() - self.start_time
    
    def estimate_completion(self) -> Optional[datetime]:
        """Estimate completion time based on current progress."""
        if self.completed_items == 0:
            return None
        
        elapsed = self.elapsed_time.total_seconds()
        rate = self.completed_items / elapsed
        remaining = self.total_items - self.completed_items
        estimated_seconds = remaining / rate
        
        return datetime.now() + timedelta(seconds=estimated_seconds)


@dataclass
class WSJExportConfig:
    """WSJ-specific export configuration."""
    # Color profiles for different media
    color_profiles = {
        'screen': {
            'background': '#FFFFFF',
            'primary': '#5B6770',
            'secondary': '#ADB5BD',
            'text': '#212529'
        },
        'print': {
            'background': 'white',
            'primary': '#5B6770',
            'secondary': '#ADB5BD',
            'text': '#000000'
        }
    }
    
    # Font configurations
    fonts = {
        'title': {'family': 'Arial', 'size': 24, 'weight': 'bold'},
        'subtitle': {'family': 'Arial', 'size': 18, 'weight': 'normal'},
        'body': {'family': 'Arial', 'size': 12, 'weight': 'normal'},
        'caption': {'family': 'Arial', 'size': 10, 'weight': 'normal'}
    }
    
    # Layout configurations
    layouts = {
        'single_chart': {'columns': 1, 'rows': 1},
        'two_charts': {'columns': 2, 'rows': 1},
        'four_charts': {'columns': 2, 'rows': 2},
        'dashboard': {'columns': 3, 'rows': 3}
    }
    
    # Branding elements
    branding = {
        'show_logo': False,
        'show_watermark': False,
        'footer_text': 'Health Dashboard Report',
        'header_text': None
    }