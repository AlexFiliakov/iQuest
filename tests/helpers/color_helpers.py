"""
Color utility functions for testing.

This module provides utilities for color analysis, including contrast ratio
calculations for WCAG compliance testing.
"""

from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
        
    Returns:
        Tuple of (red, green, blue) values (0-255)
    """
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate relative luminance of a color.
    
    Uses the WCAG formula for relative luminance.
    
    Args:
        rgb: Tuple of (red, green, blue) values (0-255)
        
    Returns:
        Relative luminance value (0-1)
    """
    # Normalize to 0-1 range
    rgb_normalized = [val / 255.0 for val in rgb]
    
    # Apply gamma correction
    rgb_linear = []
    for val in rgb_normalized:
        if val <= 0.03928:
            rgb_linear.append(val / 12.92)
        else:
            rgb_linear.append(((val + 0.055) / 1.055) ** 2.4)
    
    # Calculate luminance using WCAG formula
    luminance = (0.2126 * rgb_linear[0] + 
                 0.7152 * rgb_linear[1] + 
                 0.0722 * rgb_linear[2])
    
    return luminance


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate contrast ratio between two colors.
    
    Uses the WCAG contrast ratio formula.
    
    Args:
        color1: First color in hex format
        color2: Second color in hex format
        
    Returns:
        Contrast ratio (1-21)
    """
    # Convert colors to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Calculate luminance
    lum1 = calculate_luminance(rgb1)
    lum2 = calculate_luminance(rgb2)
    
    # Calculate contrast ratio
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    contrast_ratio = (lighter + 0.05) / (darker + 0.05)
    
    return contrast_ratio


def meets_wcag_aa(foreground: str, background: str, 
                  large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG AA standards.
    
    Args:
        foreground: Foreground color in hex format
        background: Background color in hex format
        large_text: Whether this is for large text (14pt+ bold or 18pt+)
        
    Returns:
        True if meets WCAG AA standards
    """
    ratio = calculate_contrast_ratio(foreground, background)
    
    # WCAG AA requirements
    if large_text:
        return ratio >= 3.0
    else:
        return ratio >= 4.5


def meets_wcag_aaa(foreground: str, background: str,
                   large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG AAA standards.
    
    Args:
        foreground: Foreground color in hex format
        background: Background color in hex format
        large_text: Whether this is for large text
        
    Returns:
        True if meets WCAG AAA standards
    """
    ratio = calculate_contrast_ratio(foreground, background)
    
    # WCAG AAA requirements
    if large_text:
        return ratio >= 4.5
    else:
        return ratio >= 7.0


class WSJColorContrastChecker:
    """Check WSJ color palette for WCAG compliance"""
    
    def __init__(self):
        self.wsj_palette = {
            'background': '#FFFFFF',
            'text': '#333333',
            'primary': '#0080C0',
            'secondary': '#F5E6D3',
            'accent': '#FF8C42',
            'muted': '#666666',
            'light_gray': '#E5E5E5',
            'dark_gray': '#999999'
        }
        
    def check_wsj_palette(self) -> dict:
        """
        Check all WSJ color combinations for WCAG compliance.
        
        Returns:
            Dictionary with contrast check results
        """
        results = {}
        
        # Check text colors on backgrounds
        backgrounds = ['background', 'secondary', 'light_gray']
        text_colors = ['text', 'primary', 'accent', 'muted', 'dark_gray']
        
        for bg in backgrounds:
            for fg in text_colors:
                key = f"{fg}_on_{bg}"
                ratio = calculate_contrast_ratio(
                    self.wsj_palette[fg], 
                    self.wsj_palette[bg]
                )
                
                results[key] = {
                    'ratio': ratio,
                    'passes_aa': ratio >= 4.5,
                    'passes_aaa': ratio >= 7.0,
                    'passes_aa_large': ratio >= 3.0,
                    'passes_aaa_large': ratio >= 4.5
                }
                
        return results
        
    def get_recommendations(self) -> dict:
        """
        Get recommendations for improving contrast.
        
        Returns:
            Dictionary with improvement recommendations
        """
        results = self.check_wsj_palette()
        recommendations = {}
        
        for combo, result in results.items():
            if not result['passes_aa']:
                fg, bg = combo.split('_on_')
                recommendations[combo] = {
                    'current_ratio': result['ratio'],
                    'required_ratio': 4.5,
                    'suggestion': self._suggest_improvement(fg, bg, result['ratio'])
                }
                
        return recommendations
        
    def _suggest_improvement(self, foreground: str, background: str, 
                           current_ratio: float) -> str:
        """Suggest how to improve contrast ratio"""
        if current_ratio < 3.0:
            return f"Significant adjustment needed. Consider darkening {foreground} or using different color."
        elif current_ratio < 4.5:
            return f"Minor adjustment needed. Slightly darken {foreground} or lighten {background}."
        else:
            return "Meets AA for large text. Consider for body text only if large."