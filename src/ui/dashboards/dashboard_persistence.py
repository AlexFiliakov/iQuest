"""Dashboard layout persistence and sharing functionality."""

import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
import logging

from .dashboard_models import DashboardTemplate, ChartConfig, GridSpec
from ..settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class DashboardPersistence(QObject):
    """Handles saving, loading, and sharing of dashboard layouts."""
    
    # Signals
    layout_saved = pyqtSignal(str)  # layout_name
    layout_loaded = pyqtSignal(dict)  # layout_data
    
    LAYOUTS_FILE = "dashboard_layouts.json"
    
    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        super().__init__()
        self.settings_manager = settings_manager or SettingsManager()
        self.layouts_path = Path(self.settings_manager.get_data_directory()) / self.LAYOUTS_FILE
        self._ensure_layouts_file()
        
    def _ensure_layouts_file(self):
        """Ensure the layouts file exists."""
        if not self.layouts_path.exists():
            self.layouts_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_layouts_data({})
            
    def _load_layouts_data(self) -> Dict[str, Any]:
        """Load all saved layouts."""
        try:
            with open(self.layouts_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load layouts: {e}")
            return {}
            
    def _save_layouts_data(self, data: Dict[str, Any]):
        """Save layouts data to file."""
        try:
            with open(self.layouts_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save layouts: {e}")
            
    def save_layout(self, name: str, layout_data: Dict[str, Any], 
                   description: str = "", tags: List[str] = None) -> bool:
        """Save a dashboard layout."""
        try:
            layouts = self._load_layouts_data()
            
            # Add metadata
            layout_entry = {
                'name': name,
                'description': description,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'version': '1.0',
                'data': layout_data
            }
            
            # Update modified time if layout exists
            if name in layouts:
                layout_entry['created_at'] = layouts[name].get('created_at', 
                                                               datetime.now().isoformat())
                
            layouts[name] = layout_entry
            self._save_layouts_data(layouts)
            
            self.layout_saved.emit(name)
            logger.info(f"Saved layout: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save layout {name}: {e}")
            return False
            
    def load_layout(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a saved dashboard layout."""
        try:
            layouts = self._load_layouts_data()
            if name in layouts:
                layout_data = layouts[name]['data']
                self.layout_loaded.emit(layout_data)
                return layout_data
            else:
                logger.warning(f"Layout not found: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load layout {name}: {e}")
            return None
            
    def delete_layout(self, name: str) -> bool:
        """Delete a saved layout."""
        try:
            layouts = self._load_layouts_data()
            if name in layouts:
                del layouts[name]
                self._save_layouts_data(layouts)
                logger.info(f"Deleted layout: {name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete layout {name}: {e}")
            return False
            
    def list_layouts(self) -> List[Dict[str, Any]]:
        """List all saved layouts with metadata."""
        layouts = self._load_layouts_data()
        return [
            {
                'name': name,
                'description': data.get('description', ''),
                'tags': data.get('tags', []),
                'created_at': data.get('created_at'),
                'modified_at': data.get('modified_at')
            }
            for name, data in layouts.items()
        ]
        
    def export_layout(self, name: str) -> Optional[str]:
        """Export a layout as a shareable string."""
        layout_data = self.load_layout(name)
        if layout_data:
            try:
                # Create export package
                export_data = {
                    'name': name,
                    'version': '1.0',
                    'app_version': '1.0.0',  # Would get from app
                    'exported_at': datetime.now().isoformat(),
                    'layout': layout_data
                }
                
                # Encode to base64 for easy sharing
                json_str = json.dumps(export_data, separators=(',', ':'))
                encoded = base64.b64encode(json_str.encode()).decode()
                
                # Add header for identification
                return f"HEALTH_DASHBOARD_LAYOUT_V1:{encoded}"
                
            except Exception as e:
                logger.error(f"Failed to export layout {name}: {e}")
                return None
        return None
        
    def import_layout(self, import_string: str, new_name: Optional[str] = None) -> bool:
        """Import a layout from a shared string."""
        try:
            # Check header
            if not import_string.startswith("HEALTH_DASHBOARD_LAYOUT_V1:"):
                logger.error("Invalid import string format")
                return False
                
            # Decode
            encoded = import_string.split(":", 1)[1]
            json_str = base64.b64decode(encoded).decode()
            export_data = json.loads(json_str)
            
            # Extract layout
            layout_name = new_name or export_data['name']
            layout_data = export_data['layout']
            
            # Save with import metadata
            return self.save_layout(
                layout_name,
                layout_data,
                f"Imported from {export_data.get('name', 'unknown')} on {datetime.now().strftime('%Y-%m-%d')}",
                ['imported']
            )
            
        except Exception as e:
            logger.error(f"Failed to import layout: {e}")
            return False
            
    def save_as_template(self, name: str, template: DashboardTemplate) -> bool:
        """Save a dashboard template for reuse."""
        try:
            # Convert template to serializable format
            template_data = {
                'name': template.name,
                'title': template.title,
                'description': template.description,
                'layout_type': template.layout_type.value,
                'chart_configs': []
            }
            
            for config in template.chart_configs:
                config_data = {
                    'chart_id': config.chart_id,
                    'metric_type': config.metric_type,
                    'chart_type': config.chart_type,
                    'grid_spec': {
                        'row': config.grid_spec.row,
                        'col': config.grid_spec.col,
                        'row_span': config.grid_spec.row_span,
                        'col_span': config.grid_spec.col_span
                    },
                    'config': config.config,
                    'min_width': config.min_width,
                    'min_height': config.min_height
                }
                if config.aspect_ratio:
                    config_data['aspect_ratio'] = config.aspect_ratio
                    
                template_data['chart_configs'].append(config_data)
                
            return self.save_layout(
                f"template_{name}",
                template_data,
                f"Template: {template.description}",
                ['template']
            )
            
        except Exception as e:
            logger.error(f"Failed to save template {name}: {e}")
            return False
            
    def load_template(self, name: str) -> Optional[DashboardTemplate]:
        """Load a saved template."""
        layout_data = self.load_layout(f"template_{name}")
        if layout_data:
            try:
                # Reconstruct template from data
                chart_configs = []
                for config_data in layout_data.get('chart_configs', []):
                    grid_spec = GridSpec(
                        row=config_data['grid_spec']['row'],
                        col=config_data['grid_spec']['col'],
                        row_span=config_data['grid_spec']['row_span'],
                        col_span=config_data['grid_spec']['col_span']
                    )
                    
                    config = ChartConfig(
                        chart_id=config_data['chart_id'],
                        metric_type=config_data['metric_type'],
                        chart_type=config_data['chart_type'],
                        grid_spec=grid_spec,
                        config=config_data['config'],
                        min_width=config_data.get('min_width', 300),
                        min_height=config_data.get('min_height', 200),
                        aspect_ratio=config_data.get('aspect_ratio')
                    )
                    chart_configs.append(config)
                    
                template = DashboardTemplate(
                    name=layout_data['name'],
                    title=layout_data['title'],
                    description=layout_data.get('description', ''),
                    chart_configs=chart_configs
                )
                
                return template
                
            except Exception as e:
                logger.error(f"Failed to load template {name}: {e}")
                return None
        return None
        
    def get_recent_layouts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently used layouts."""
        layouts = self.list_layouts()
        # Sort by modified time
        layouts.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
        return layouts[:limit]
        
    def duplicate_layout(self, source_name: str, new_name: str) -> bool:
        """Duplicate an existing layout."""
        layout_data = self.load_layout(source_name)
        if layout_data:
            return self.save_layout(
                new_name,
                layout_data,
                f"Duplicated from {source_name}",
                ['duplicate']
            )
        return False