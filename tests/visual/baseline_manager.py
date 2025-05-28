"""
Platform-specific baseline image management for visual regression tests.
Handles cross-platform baseline storage and fallback mechanisms.
"""

import platform
from pathlib import Path
from typing import Optional
from PIL import Image


class BaselineManager:
    """Manage platform-specific baseline images."""
    
    def __init__(self, base_path: str = "tests/visual/baselines"):
        self.base_path = Path(base_path)
        self.platform = self._get_platform_key()
        self._ensure_directories()
    
    def _get_platform_key(self) -> str:
        """Get platform-specific key."""
        system = platform.system().lower()
        version = platform.release()
        
        # Normalize platform names
        if system == 'darwin':
            system = 'macos'
            # Group macOS versions
            try:
                mac_version = platform.mac_ver()[0]
                if mac_version.startswith('10.'):
                    version = 'legacy'
                else:
                    version = 'modern'
            except:
                version = 'modern'
        elif system == 'windows':
            # Group Windows versions
            if '10' in version or '11' in version:
                version = 'modern'
            else:
                version = 'legacy'
        elif system == 'linux':
            # For Linux, use distribution if available
            try:
                import distro
                distro_name = distro.id()
                if distro_name in ['ubuntu', 'debian']:
                    version = 'debian'
                elif distro_name in ['fedora', 'centos', 'rhel']:
                    version = 'redhat'
                else:
                    version = 'generic'
            except ImportError:
                version = 'generic'
        
        return f"{system}_{version}"
    
    def _ensure_directories(self):
        """Ensure baseline directories exist."""
        # Create platform-specific directory
        platform_dir = self.base_path / self.platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        # Create generic fallback directory
        generic_dir = self.base_path / 'generic'
        generic_dir.mkdir(parents=True, exist_ok=True)
    
    def get_baseline_path(self, test_name: str) -> Path:
        """Get path to baseline image, with platform fallback."""
        # Clean test name for filesystem
        clean_name = self._clean_filename(test_name)
        
        # Try platform-specific first
        platform_path = self.base_path / self.platform / f"{clean_name}.png"
        if platform_path.exists():
            return platform_path
        
        # Fall back to generic
        generic_path = self.base_path / 'generic' / f"{clean_name}.png"
        if generic_path.exists():
            return generic_path
        
        # Return expected platform-specific path for new baselines
        return platform_path
    
    def save_baseline(
        self, 
        test_name: str, 
        image: Image.Image,
        platform_specific: bool = True
    ):
        """Save baseline image."""
        clean_name = self._clean_filename(test_name)
        
        if platform_specific:
            path = self.base_path / self.platform / f"{clean_name}.png"
        else:
            path = self.base_path / 'generic' / f"{clean_name}.png"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with optimization for smaller file sizes
        image.save(path, 'PNG', optimize=True, compress_level=9)
    
    def baseline_exists(self, test_name: str) -> bool:
        """Check if baseline exists (either platform-specific or generic)."""
        return self.get_baseline_path(test_name).exists()
    
    def list_baselines(self) -> list:
        """List all available baselines for current platform."""
        baselines = []
        
        # Platform-specific baselines
        platform_dir = self.base_path / self.platform
        if platform_dir.exists():
            for png_file in platform_dir.glob('*.png'):
                baselines.append({
                    'name': png_file.stem,
                    'type': 'platform',
                    'path': png_file
                })
        
        # Generic baselines (only if no platform-specific version exists)
        generic_dir = self.base_path / 'generic'
        if generic_dir.exists():
            for png_file in generic_dir.glob('*.png'):
                if not any(b['name'] == png_file.stem for b in baselines):
                    baselines.append({
                        'name': png_file.stem,
                        'type': 'generic',
                        'path': png_file
                    })
        
        return sorted(baselines, key=lambda x: x['name'])
    
    def _clean_filename(self, test_name: str) -> str:
        """Clean test name for use as filename."""
        # Replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        clean_name = test_name
        
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Replace spaces and special characters
        clean_name = clean_name.replace(' ', '_')
        clean_name = clean_name.replace('[', '_')
        clean_name = clean_name.replace(']', '_')
        clean_name = clean_name.replace('(', '_')
        clean_name = clean_name.replace(')', '_')
        
        # Remove multiple underscores
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        
        return clean_name
    
    def get_platform_info(self) -> dict:
        """Get detailed platform information for debugging."""
        return {
            'platform_key': self.platform,
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }