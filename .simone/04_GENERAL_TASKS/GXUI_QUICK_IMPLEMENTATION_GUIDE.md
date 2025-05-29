# Quick UI Modernization Implementation Guide

## Step 1: Update StyleManager (Immediate Impact)

Replace the color palette in `src/ui/style_manager.py`:

```python
# Line 11-27, replace with:
# Modern color palette
PRIMARY_BG = "#FAFBFC"      # Clean near-white
SECONDARY_BG = "#FFFFFF"    # Pure white for cards
TERTIARY_BG = "#F6F8FA"     # Light gray for sections

ACCENT_PRIMARY = "#FF6B35"   # Vibrant orange-red
ACCENT_SECONDARY = "#FFB700" # Golden yellow
ACCENT_SUCCESS = "#06D6A0"   # Modern teal-green
ACCENT_WARNING = "#FFB700"   # Consistent with secondary
ACCENT_ERROR = "#EF476F"     # Modern pink-red
ACCENT_LIGHT = "#FFF4ED"     # Light orange for selections

TEXT_PRIMARY = "#0D1117"     # Near-black
TEXT_SECONDARY = "#57606A"   # Medium gray
TEXT_MUTED = "#8B949E"       # Light gray
TEXT_INVERSE = "#FFFFFF"     # White on dark

# Add new design tokens after line 27:
SHADOW_SM = "0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.06)"
SHADOW_MD = "0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.05)"
SHADOW_LG = "0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)"
```

## Step 2: Update Base Font Size

In `src/ui/style_manager.py`, update the font size in `get_main_window_style()`:

```python
# Line 48, change from:
font-size: 13px;
# To:
font-size: 15px;
```

## Step 3: Modernize Card Styles

Replace `get_borderless_card_style()` method (line 225):

```python
def get_borderless_card_style(self, padding: int = 24, radius: int = 16):
    """Get modern card widget stylesheet with subtle shadow."""
    return f"""
        QFrame {{
            background-color: {self.SECONDARY_BG};
            border-radius: {radius}px;
            padding: {padding}px;
            border: none;
        }}
        
        QFrame:hover {{
            background-color: {self.SECONDARY_BG};
            transform: translateY(-2px);
        }}
        
        QLabel {{
            background: transparent;
            border: none;
            color: {self.TEXT_PRIMARY};
        }}
    """
```

## Step 4: Update Button Styles

Replace the primary button style (line 148):

```python
def get_button_style(self, button_type="primary"):
    if button_type == "primary":
        return f"""
            QPushButton {{
                background-color: {self.ACCENT_PRIMARY};
                color: {self.TEXT_INVERSE};
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
            }}
            
            QPushButton:hover {{
                background-color: #E85D2F;
            }}
            
            QPushButton:pressed {{
                background-color: #CC4125;
            }}
            
            QPushButton:disabled {{
                background-color: {self.TEXT_MUTED};
                color: {self.SECONDARY_BG};
            }}
            
            QPushButton:focus {{
                outline: 3px solid rgba(255, 107, 53, 0.3);
                outline-offset: 2px;
            }}
        """
```

## Step 5: Update Tab Widget Style

Replace `get_tab_widget_style()` (line 102):

```python
def get_tab_widget_style(self):
    """Get modern tab widget stylesheet."""
    return f"""
        QTabWidget::pane {{
            background-color: {self.SECONDARY_BG};
            border: none;
            border-radius: 12px;
            top: -1px;
        }}
        
        QTabBar {{
            background-color: transparent;
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {self.TEXT_SECONDARY};
            padding: 10px 20px;
            margin-right: 8px;
            border-radius: 8px;
            font-weight: 500;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.ACCENT_PRIMARY};
            color: {self.TEXT_INVERSE};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {self.TERTIARY_BG};
            color: {self.TEXT_PRIMARY};
        }}
    """
```

## Step 6: Update Summary Cards

In `src/ui/summary_cards.py`, update the card styling (line 109):

```python
def apply_card_style(self):
    """Apply modern card styling."""
    style = f"""
        QFrame#summaryCard {{
            background-color: {self.style_manager.SECONDARY_BG};
            border-radius: 16px;
            border: none;
            padding: {self.SIZE_CONFIGS[self.size]['padding'] + 8}px;
        }}
        
        QFrame#summaryCard:hover {{
            background-color: {self.style_manager.SECONDARY_BG};
            transform: translateY(-2px);
        }}
    """
    self.setStyleSheet(style)
```

## Step 7: Fix Scroll Bar Style

In `src/ui/style_manager.py`, update scroll bar colors (line 318):

```python
def get_scroll_bar_style(self):
    """Get modern scroll bar stylesheet."""
    return f"""
        QScrollBar:vertical {{
            background-color: {self.TERTIARY_BG};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.TEXT_MUTED};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.TEXT_SECONDARY};
        }}
        
        /* Hide add/sub line buttons */
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """
```

## Testing the Changes

1. Save all files
2. Run the application: `python src/main.py`
3. You should see:
   - Cleaner, brighter interface
   - Better contrast
   - More modern button and card styles
   - Improved readability with larger fonts

## Next Steps

After implementing these quick fixes:

1. Test on different screen sizes
2. Verify color contrast meets WCAG AA standards
3. Consider adding CSS transitions for smooth interactions
4. Implement the shadow effects (may require custom painting)
5. Add icon support for better visual communication

## Common Issues and Solutions

**Issue**: Shadows not appearing in PyQt6
**Solution**: PyQt6 doesn't support CSS box-shadow. Consider using `QGraphicsDropShadowEffect`:

```python
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(15)
shadow.setXOffset(0)
shadow.setYOffset(2)
shadow.setColor(QColor(0, 0, 0, 50))
widget.setGraphicsEffect(shadow)
```

**Issue**: Transform property not working
**Solution**: Remove transform properties, use QPropertyAnimation for animations instead

**Issue**: Colors look different on screen
**Solution**: Ensure your monitor is calibrated and test on multiple displays