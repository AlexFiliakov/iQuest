"""
Cross-platform and export compatibility testing for visualizations.

While PyQt applications don't run in browsers, this module tests:
- Export to web-compatible formats (SVG, PNG, HTML)
- Cross-platform rendering consistency (Windows, macOS, Linux)
- Different screen resolutions and DPI settings
- Export quality and compatibility
"""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import pytest
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QScreen, QGuiApplication
from PyQt6.QtWidgets import QWidget
from PIL import Image
import numpy as np

# Optional dependency for enhanced Linux platform detection
try:
    import distro
    HAS_DISTRO = True
except ImportError:
    HAS_DISTRO = False


@dataclass
class PlatformTestResult:
    """Result of cross-platform testing"""
    platform_name: str
    test_name: str
    passed: bool
    details: Dict[str, Any]
    
    
@dataclass
class ExportTestResult:
    """Result of export compatibility testing"""
    format: str
    component: str
    success: bool
    file_size: Optional[int]
    validation_passed: bool
    details: Dict[str, Any]


class CrossPlatformTester:
    """Test visualization rendering across platforms and export formats"""
    
    def __init__(self):
        self.current_platform = platform.system()
        self.platform_info = self._get_platform_info()
        self.platform_configs = self._get_platform_configs()
        self.export_formats = ['PNG', 'SVG', 'HTML', 'PDF']
        self.test_resolutions = [
            (1920, 1080),  # Full HD
            (2560, 1440),  # QHD
            (3840, 2160),  # 4K
            (1366, 768),   # Common laptop
            (1024, 768)    # Legacy
        ]
        self.test_dpis = [96, 120, 144, 192]  # Standard to high DPI
        
    def _get_platform_info(self) -> Dict[str, str]:
        """Get detailed platform information"""
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine()
        }
        
        if self.current_platform == 'Linux' and HAS_DISTRO:
            info['distribution'] = distro.name()
            info['dist_version'] = distro.version()
            
        return info
        
    def test_platform_rendering(self, component_class: type) -> List[PlatformTestResult]:
        """Test component rendering on current platform"""
        results = []
        
        # Test at different resolutions
        for width, height in self.test_resolutions:
            result = self._test_resolution(component_class, width, height)
            results.append(result)
            
        # Test at different DPI settings
        for dpi in self.test_dpis:
            result = self._test_dpi_scaling(component_class, dpi)
            results.append(result)
            
        return results
        
    def test_export_compatibility(self, component: Any) -> List[ExportTestResult]:
        """Test exporting visualizations to different formats"""
        results = []
        
        for format in self.export_formats:
            result = self._test_export_format(component, format)
            results.append(result)
            
        return results
        
    def _get_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get platform-specific configurations"""
        return {
            'Windows': {
                'font_scaling': 1.0,
                'default_dpi': 96,
                'color_profile': 'sRGB',
                'antialiasing': True
            },
            'Darwin': {  # macOS
                'font_scaling': 1.0,
                'default_dpi': 72,
                'color_profile': 'Display P3',
                'antialiasing': True
            },
            'Linux': {
                'font_scaling': 1.0,
                'default_dpi': 96,
                'color_profile': 'sRGB',
                'antialiasing': True
            }
        }
        
    def _test_resolution(self, component_class: type, 
                        width: int, height: int) -> PlatformTestResult:
        """Test rendering at specific resolution"""
        try:
            # Create component
            component = component_class()
            component.resize(width, height)
            
            # Render and check
            if hasattr(component, 'render'):
                component.render()
                
            success = True
            details = {
                'resolution': f"{width}x{height}",
                'rendered_size': (component.width(), component.height())
            }
            
        except Exception as e:
            success = False
            details = {'error': str(e)}
            
        return PlatformTestResult(
            platform_name=self.current_platform,
            test_name=f"resolution_{width}x{height}",
            passed=success,
            details=details
        )
        
    def _test_dpi_scaling(self, component_class: type, dpi: int) -> PlatformTestResult:
        """Test rendering at different DPI settings"""
        try:
            # Create component with DPI awareness
            component = component_class()
            
            # Simulate DPI scaling
            scale_factor = dpi / 96.0
            
            if hasattr(component, 'setDevicePixelRatio'):
                component.setDevicePixelRatio(scale_factor)
                
            success = True
            details = {
                'dpi': dpi,
                'scale_factor': scale_factor
            }
            
        except Exception as e:
            success = False
            details = {'error': str(e)}
            
        return PlatformTestResult(
            platform_name=self.current_platform,
            test_name=f"dpi_{dpi}",
            passed=success,
            details=details
        )
        
    def _test_export_format(self, component: Any, format: str) -> ExportTestResult:
        """Test exporting to specific format"""
        temp_file = Path(f"test_export.{format.lower()}")
        
        try:
            # Export based on format
            if format == 'PNG':
                success = self._export_to_png(component, temp_file)
            elif format == 'SVG':
                success = self._export_to_svg(component, temp_file)
            elif format == 'HTML':
                success = self._export_to_html(component, temp_file)
            elif format == 'PDF':
                success = self._export_to_pdf(component, temp_file)
            else:
                success = False
                
            # Validate export
            validation_passed = False
            file_size = None
            
            if success and temp_file.exists():
                file_size = temp_file.stat().st_size
                validation_passed = self._validate_export(temp_file, format)
                
            result = ExportTestResult(
                format=format,
                component=component.__class__.__name__,
                success=success,
                file_size=file_size,
                validation_passed=validation_passed,
                details={
                    'file_path': str(temp_file),
                    'exists': temp_file.exists()
                }
            )
            
        except Exception as e:
            result = ExportTestResult(
                format=format,
                component=component.__class__.__name__,
                success=False,
                file_size=None,
                validation_passed=False,
                details={'error': str(e)}
            )
            
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
                
        return result
        
    def _export_to_png(self, component: Any, filepath: Path) -> bool:
        """Export component to PNG"""
        if hasattr(component, 'grab'):
            pixmap = component.grab()
            return pixmap.save(str(filepath), 'PNG')
        return False
        
    def _export_to_svg(self, component: Any, filepath: Path) -> bool:
        """Export component to SVG"""
        if hasattr(component, 'export_svg'):
            return component.export_svg(str(filepath))
            
        # Fallback: try to use Qt's SVG generator
        try:
            from PyQt6.QtSvg import QSvgGenerator
            from PyQt6.QtGui import QPainter
            
            generator = QSvgGenerator()
            generator.setFileName(str(filepath))
            generator.setSize(component.size())
            
            painter = QPainter()
            painter.begin(generator)
            component.render(painter)
            painter.end()
            
            return True
        except:
            return False
            
    def _export_to_html(self, component: Any, filepath: Path) -> bool:
        """Export component to HTML"""
        if hasattr(component, 'export_html'):
            return component.export_html(str(filepath))
            
        # Fallback: create simple HTML with embedded image
        try:
            # First export to PNG
            png_path = filepath.with_suffix('.png')
            if self._export_to_png(component, png_path):
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{component.__class__.__name__}</title>
                    <style>
                        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                        .visualization {{ max-width: 100%; height: auto; }}
                    </style>
                </head>
                <body>
                    <h1>{component.__class__.__name__}</h1>
                    <img src="{png_path.name}" class="visualization" alt="Health Visualization">
                </body>
                </html>
                """
                filepath.write_text(html_content)
                return True
        except:
            pass
            
        return False
        
    def _export_to_pdf(self, component: Any, filepath: Path) -> bool:
        """Export component to PDF"""
        if hasattr(component, 'export_pdf'):
            return component.export_pdf(str(filepath))
            
        # Fallback: use Qt's PDF printer
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QPainter
            
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(filepath))
            
            painter = QPainter()
            painter.begin(printer)
            component.render(painter)
            painter.end()
            
            return True
        except:
            return False
            
    def _validate_export(self, filepath: Path, format: str) -> bool:
        """Validate exported file"""
        if not filepath.exists():
            return False
            
        # Basic validation by format
        if format == 'PNG':
            try:
                img = Image.open(filepath)
                return img.format == 'PNG'
            except:
                return False
                
        elif format == 'SVG':
            try:
                content = filepath.read_text()
                return '<svg' in content and '</svg>' in content
            except:
                return False
                
        elif format == 'HTML':
            try:
                content = filepath.read_text()
                return '<html' in content and '</html>' in content
            except:
                return False
                
        elif format == 'PDF':
            try:
                content = filepath.read_bytes()
                return content.startswith(b'%PDF')
            except:
                return False
                
        return False
        

class ScreenCompatibilityTester:
    """Test visualization compatibility across different screen configurations"""
    
    def __init__(self):
        self.app = QGuiApplication.instance()
        
    def get_screen_configurations(self) -> List[Dict[str, Any]]:
        """Get all available screen configurations"""
        if not self.app:
            return []
            
        configs = []
        
        for screen in self.app.screens():
            config = {
                'name': screen.name(),
                'geometry': {
                    'x': screen.geometry().x(),
                    'y': screen.geometry().y(),
                    'width': screen.geometry().width(),
                    'height': screen.geometry().height()
                },
                'physical_size': {
                    'width': screen.physicalSize().width(),
                    'height': screen.physicalSize().height()
                },
                'dpi': {
                    'logical': screen.logicalDotsPerInch(),
                    'physical': screen.physicalDotsPerInch()
                },
                'device_pixel_ratio': screen.devicePixelRatio(),
                'orientation': screen.orientation()
            }
            configs.append(config)
            
        return configs
        
    def test_multi_monitor_setup(self, component_class: type) -> Dict[str, Any]:
        """Test component on multi-monitor setups"""
        screens = self.get_screen_configurations()
        
        results = {
            'screen_count': len(screens),
            'screens': screens,
            'tests': []
        }
        
        for i, screen_config in enumerate(screens):
            try:
                component = component_class()
                
                # Test on each screen
                if self.app and i < len(self.app.screens()):
                    screen = self.app.screens()[i]
                    component.windowHandle().setScreen(screen)
                    
                test_result = {
                    'screen_index': i,
                    'screen_name': screen_config['name'],
                    'success': True
                }
                
            except Exception as e:
                test_result = {
                    'screen_index': i,
                    'screen_name': screen_config['name'],
                    'success': False,
                    'error': str(e)
                }
                
            results['tests'].append(test_result)
            
        return results


# Pytest test cases
@pytest.mark.platform
class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment"""
        self.tester = CrossPlatformTester()
        
    def test_current_platform_detection(self):
        """Test platform detection"""
        assert self.tester.current_platform in ['Windows', 'Darwin', 'Linux']
        
    def test_platform_configs_complete(self):
        """Test platform configurations are defined"""
        configs = self.tester.platform_configs
        
        for platform in ['Windows', 'Darwin', 'Linux']:
            assert platform in configs
            assert 'default_dpi' in configs[platform]
            assert 'font_scaling' in configs[platform]
            
    @pytest.mark.parametrize("resolution", [
        (1920, 1080),
        (1366, 768),
        (1024, 768)
    ])
    def test_resolution_support(self, resolution):
        """Test that common resolutions are supported"""
        width, height = resolution
        assert width > 0 and height > 0
        assert width / height > 0  # Valid aspect ratio
        

@pytest.mark.export
class TestExportCompatibility:
    """Test export functionality"""
    
    def test_export_format_validation(self):
        """Test export format validation logic"""
        tester = CrossPlatformTester()
        
        # Test PNG validation
        test_png = Path("test.png")
        test_png.write_bytes(b'\x89PNG\r\n\x1a\n')  # PNG header
        assert tester._validate_export(test_png, 'PNG') is False  # Invalid PNG
        test_png.unlink()
        
        # Test SVG validation  
        test_svg = Path("test.svg")
        test_svg.write_text('<svg></svg>')
        assert tester._validate_export(test_svg, 'SVG') is True
        test_svg.unlink()
        
        # Test HTML validation
        test_html = Path("test.html") 
        test_html.write_text('<html><body></body></html>')
        assert tester._validate_export(test_html, 'HTML') is True
        test_html.unlink()
        
        # Test PDF validation
        test_pdf = Path("test.pdf")
        test_pdf.write_bytes(b'%PDF-1.4')
        assert tester._validate_export(test_pdf, 'PDF') is True
        test_pdf.unlink()
        

class MockVisualizationComponent(QWidget):
    """Mock component for testing"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        
    def export_svg(self, filepath: str) -> bool:
        """Mock SVG export"""
        svg_content = '''<svg width="400" height="300">
            <rect width="400" height="300" fill="white"/>
            <text x="200" y="150" text-anchor="middle">Test Visualization</text>
        </svg>'''
        Path(filepath).write_text(svg_content)
        return True
        
    def export_html(self, filepath: str) -> bool:
        """Mock HTML export"""
        html_content = '''<!DOCTYPE html>
        <html><body>
            <h1>Test Visualization</h1>
            <canvas id="chart"></canvas>
        </body></html>'''
        Path(filepath).write_text(html_content)
        return True
        

def test_mock_component_export():
    """Test export with mock component"""
    component = MockVisualizationComponent()
    tester = CrossPlatformTester()
    
    results = tester.test_export_compatibility(component)
    
    # Should have results for all formats
    assert len(results) == len(tester.export_formats)
    
    # Check specific formats
    svg_results = [r for r in results if r.format == 'SVG']
    assert len(svg_results) == 1
    assert svg_results[0].success
    
    html_results = [r for r in results if r.format == 'HTML']
    assert len(html_results) == 1
    assert html_results[0].success