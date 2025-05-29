"""Data models for dashboard layout system."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class LayoutType(Enum):
    """Available dashboard layout types."""
    GRID = "grid"
    SIDEBAR = "sidebar"
    STACKED = "stacked"
    MOSAIC = "mosaic"


@dataclass
class GridSpec:
    """Grid specification for placing a chart in the dashboard."""
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    
    def __post_init__(self):
        """Validate grid specifications."""
        if self.row < 0 or self.col < 0:
            raise ValueError("Row and column must be non-negative")
        if self.row_span < 1 or self.col_span < 1:
            raise ValueError("Spans must be at least 1")
        if self.col + self.col_span > 12:
            raise ValueError("Grid system uses 12 columns maximum")


@dataclass
class ChartConfig:
    """Configuration for a chart in the dashboard."""
    chart_id: str
    metric_type: str
    chart_type: str
    grid_spec: GridSpec
    config: Dict[str, Any]
    min_width: int = 300
    min_height: int = 200
    aspect_ratio: Optional[float] = None  # Width/height ratio


@dataclass
class DashboardTemplate:
    """Predefined dashboard template."""
    name: str
    title: str
    description: str = ""
    chart_configs: List[ChartConfig] = None
    layout_type: LayoutType = LayoutType.GRID
    
    def __post_init__(self):
        if self.chart_configs is None:
            self.chart_configs = []


@dataclass
class GridConfiguration:
    """Grid configuration for responsive layouts."""
    primary_size: Tuple[int, int]  # (width, height)
    secondary_size: Tuple[int, int]
    layout: str  # 'grid', 'sidebar', 'stacked'
    columns: int = 12
    gutter: int = 16
    margin: int = 24


@dataclass
class DashboardState:
    """Current state of the dashboard."""
    layout_name: str
    chart_states: Dict[str, Dict[str, Any]]  # chart_id -> state
    zoom_level: float = 1.0
    focused_chart: Optional[str] = None
    synchronized_time_range: Optional[Tuple[Any, Any]] = None