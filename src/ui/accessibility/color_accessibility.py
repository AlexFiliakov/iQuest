"""
Color accessibility management for health visualizations.

Ensures color schemes meet WCAG standards and support colorblind users.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import colorsys
import numpy as np

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ContrastResult:
    """Result of contrast ratio calculation."""
    
    foreground: str
    background: str
    ratio: float
    passes_aa: bool
    passes_aaa: bool
    passes_aa_large: bool
    passes_aaa_large: bool
    
    def __str__(self) -> str:
        return (f"Contrast {self.ratio:.2f}:1 - "
                f"AA: {'✓' if self.passes_aa else '✗'}, "
                f"AAA: {'✓' if self.passes_aaa else '✗'}")


class ColorAccessibilityManager:
    """Manages color accessibility for visualizations."""
    
    # WCAG contrast requirements
    WCAG_AA_NORMAL = 4.5
    WCAG_AA_LARGE = 3.0
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5
    
    # Colorblind-friendly palettes
    COLORBLIND_PALETTES = {
        'default': [
            '#FF8C42',  # Orange
            '#2E86AB',  # Blue  
            '#A23B72',  # Purple
            '#F18F01',  # Dark orange
            '#C73E1D'   # Red-orange
        ],
        'deuteranopia': [  # Red-green colorblind (most common)
            '#0173B2',  # Blue
            '#DE8F05',  # Orange
            '#029E73',  # Green
            '#CC78BC',  # Pink
            '#CA9161'   # Brown
        ],
        'protanopia': [  # Red-green colorblind
            '#0173B2',  # Blue
            '#ECE133',  # Yellow
            '#56B4E9',  # Light blue
            '#009E73',  # Green
            '#D55E00'   # Orange
        ],
        'tritanopia': [  # Blue-yellow colorblind
            '#E69F00',  # Orange
            '#56B4E9',  # Sky blue
            '#009E73',  # Green
            '#F0E442',  # Yellow
            '#D55E00'   # Dark orange
        ]
    }
    
    # Accessibility patterns
    PATTERNS = {
        'solid': None,
        'dashed': [5, 3],
        'dotted': [2, 2],
        'dashdot': [5, 2, 2, 2],
        'crosshatch': 'xxx',
        'diagonal': '///',
        'horizontal': '---',
        'vertical': '|||'
    }
    
    def __init__(self):
        self.current_palette = 'default'
        self.high_contrast_enabled = False
        
        logger.info("Initialized ColorAccessibilityManager")
    
    def check_contrast_issues(self, colors: Dict[str, str]) -> List[ContrastResult]:
        """Check for contrast issues in color scheme."""
        issues = []
        
        # Common color pairs to check
        pairs_to_check = [
            ('text', 'background'),
            ('primary', 'background'),
            ('secondary', 'background'),
            ('text', 'surface')
        ]
        
        for fg_key, bg_key in pairs_to_check:
            if fg_key in colors and bg_key in colors:
                result = self.calculate_contrast(
                    colors[fg_key], 
                    colors[bg_key]
                )
                
                if not result.passes_aa:
                    issues.append(result)
        
        return issues
    
    def calculate_contrast(self, fg: str, bg: str) -> ContrastResult:
        """Calculate WCAG contrast ratio between two colors."""
        # Convert hex to RGB
        fg_rgb = self._hex_to_rgb(fg)
        bg_rgb = self._hex_to_rgb(bg)
        
        # Calculate relative luminance
        fg_lum = self._relative_luminance(fg_rgb)
        bg_lum = self._relative_luminance(bg_rgb)
        
        # Calculate contrast ratio
        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)
        ratio = (lighter + 0.05) / (darker + 0.05)
        
        return ContrastResult(
            foreground=fg,
            background=bg,
            ratio=ratio,
            passes_aa=ratio >= self.WCAG_AA_NORMAL,
            passes_aaa=ratio >= self.WCAG_AAA_NORMAL,
            passes_aa_large=ratio >= self.WCAG_AA_LARGE,
            passes_aaa_large=ratio >= self.WCAG_AAA_LARGE
        )
    
    def get_accessibility_patterns(self) -> Dict[str, Any]:
        """Get patterns for accessibility (alternative to color coding)."""
        return self.PATTERNS.copy()
    
    def get_colorblind_palette(self, type: str = 'deuteranopia') -> List[str]:
        """Get colorblind-friendly palette."""
        if type in self.COLORBLIND_PALETTES:
            return self.COLORBLIND_PALETTES[type].copy()
        
        logger.warning(f"Unknown colorblind type: {type}, using default")
        return self.COLORBLIND_PALETTES['default'].copy()
    
    def simulate_colorblind_view(self, color: str, type: str = 'deuteranopia') -> str:
        """Simulate how a color appears to colorblind users."""
        rgb = self._hex_to_rgb(color)
        
        # Simplified simulation matrices
        matrices = {
            'deuteranopia': [
                [0.625, 0.375, 0.0],
                [0.7, 0.3, 0.0],
                [0.0, 0.3, 0.7]
            ],
            'protanopia': [
                [0.567, 0.433, 0.0],
                [0.558, 0.442, 0.0],
                [0.0, 0.242, 0.758]
            ],
            'tritanopia': [
                [0.95, 0.05, 0.0],
                [0.0, 0.433, 0.567],
                [0.0, 0.475, 0.525]
            ]
        }
        
        if type not in matrices:
            return color
        
        matrix = np.array(matrices[type])
        rgb_array = np.array([rgb[0], rgb[1], rgb[2]])
        
        # Apply transformation
        transformed = matrix.dot(rgb_array)
        transformed = np.clip(transformed, 0, 1)
        
        return self._rgb_to_hex(tuple(transformed))
    
    def enhance_color_for_contrast(self, fg: str, bg: str, 
                                  target_ratio: float = 4.5) -> str:
        """Enhance foreground color to meet contrast requirements."""
        current_result = self.calculate_contrast(fg, bg)
        
        if current_result.ratio >= target_ratio:
            return fg  # Already meets requirements
        
        # Try adjusting lightness
        fg_rgb = self._hex_to_rgb(fg)
        bg_lum = self._relative_luminance(self._hex_to_rgb(bg))
        
        # Convert to HSL for easier manipulation
        h, l, s = colorsys.rgb_to_hls(*fg_rgb)
        
        # Binary search for optimal lightness
        low, high = 0.0, 1.0
        best_color = fg
        best_ratio = current_result.ratio
        
        for _ in range(10):  # Max iterations
            mid = (low + high) / 2
            test_rgb = colorsys.hls_to_rgb(h, mid, s)
            test_hex = self._rgb_to_hex(test_rgb)
            
            test_result = self.calculate_contrast(test_hex, bg)
            
            if test_result.ratio >= target_ratio:
                best_color = test_hex
                best_ratio = test_result.ratio
                
                # Try to get closer to target without going under
                if test_result.ratio > target_ratio * 1.2:
                    if mid > l:
                        high = mid
                    else:
                        low = mid
                else:
                    break
            else:
                if mid > l:
                    low = mid
                else:
                    high = mid
        
        return best_color
    
    def create_high_contrast_palette(self, base_colors: Dict[str, str]) -> Dict[str, str]:
        """Create high contrast version of color palette."""
        high_contrast = base_colors.copy()
        
        # Define high contrast overrides
        overrides = {
            'background': '#FFFFFF',
            'surface': '#FFFFFF',
            'text_primary': '#000000',
            'text_secondary': '#333333',
            'primary': '#0066CC',
            'secondary': '#FF6600',
            'positive': '#008800',
            'negative': '#CC0000',
            'grid': '#666666'
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if key in high_contrast:
                high_contrast[key] = value
        
        # Ensure all colors meet contrast requirements
        bg = high_contrast.get('background', '#FFFFFF')
        
        for key, color in high_contrast.items():
            if key not in ['background', 'surface']:
                enhanced = self.enhance_color_for_contrast(color, bg)
                if enhanced != color:
                    high_contrast[key] = enhanced
        
        return high_contrast
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to RGB tuple (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """Convert RGB tuple (0-1 range) to hex color."""
        return '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
    
    def _relative_luminance(self, rgb: Tuple[float, float, float]) -> float:
        """Calculate relative luminance per WCAG."""
        def adjust(val):
            if val <= 0.03928:
                return val / 12.92
            return ((val + 0.055) / 1.055) ** 2.4
        
        r, g, b = [adjust(v) for v in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    def validate_palette_accessibility(self, palette: List[str]) -> Dict[str, Any]:
        """Validate accessibility of a color palette."""
        results = {
            'min_contrast': float('inf'),
            'max_contrast': 0,
            'issues': [],
            'distinguishable': True
        }
        
        # Check all color pairs
        for i, color1 in enumerate(palette):
            for j, color2 in enumerate(palette[i+1:], i+1):
                result = self.calculate_contrast(color1, color2)
                
                results['min_contrast'] = min(results['min_contrast'], result.ratio)
                results['max_contrast'] = max(results['max_contrast'], result.ratio)
                
                # Colors should be distinguishable (ratio > 3:1)
                if result.ratio < 3.0:
                    results['distinguishable'] = False
                    results['issues'].append(
                        f"Colors {i} and {j} are too similar (ratio: {result.ratio:.2f})"
                    )
        
        # Check against white and black backgrounds
        for i, color in enumerate(palette):
            white_result = self.calculate_contrast(color, '#FFFFFF')
            black_result = self.calculate_contrast(color, '#000000')
            
            if not (white_result.passes_aa or black_result.passes_aa):
                results['issues'].append(
                    f"Color {i} doesn't have sufficient contrast on any background"
                )
        
        return results