# PyQt6 Implementation Code Samples for UI Improvements

## 1. Updated StyleManager Class

```python
# src/ui/style_manager.py

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QWidget

class ModernStyleManager:
    """Enhanced style manager with WSJ-inspired design system"""
    
    # WSJ-inspired color palette
    COLORS = {
        # Primary colors
        'background': '#FFFFFF',
        'surface': '#F8F9FA',
        'surface_variant': '#F3F4F6',
        'border': '#E9ECEF',
        'border_subtle': '#F1F3F4',
        
        # Text colors
        'text_primary': '#212529',
        'text_secondary': '#6C757D',
        'text_tertiary': '#ADB5BD',
        'text_inverse': '#FFFFFF',
        
        # Brand colors
        'primary': '#5B6770',
        'primary_hover': '#4A5560',
        'primary_pressed': '#3A4550',
        
        # Semantic colors
        'success': '#28A745',
        'success_light': '#D4EDDA',
        'warning': '#FFC107',
        'warning_light': '#FFF3CD',
        'danger': '#DC3545',
        'danger_light': '#F8D7DA',
        'info': '#17A2B8',
        'info_light': '#D1ECF1',
        
        # Chart colors
        'chart_primary': '#5B6770',
        'chart_secondary': '#ADB5BD',
        'chart_tertiary': '#DEE2E6',
        'chart_quaternary': '#F8F9FA',
        
        # Special colors
        'shadow': 'rgba(0, 0, 0, 0.08)',
        'shadow_hover': 'rgba(0, 0, 0, 0.12)',
        'focus_ring': 'rgba(91, 103, 112, 0.25)'
    }
    
    # Typography scale
    TYPOGRAPHY = {
        'h1': {'size': 32, 'weight': QFont.Weight.Bold, 'spacing': -0.02},
        'h2': {'size': 24, 'weight': QFont.Weight.DemiBold, 'spacing': -0.02},
        'h3': {'size': 20, 'weight': QFont.Weight.DemiBold, 'spacing': -0.01},
        'body_large': {'size': 16, 'weight': QFont.Weight.Normal, 'spacing': 0},
        'body': {'size': 14, 'weight': QFont.Weight.Normal, 'spacing': 0},
        'body_small': {'size': 12, 'weight': QFont.Weight.Normal, 'spacing': 0},
        'caption': {'size': 11, 'weight': QFont.Weight.Normal, 'spacing': 0.03},
        'button': {'size': 14, 'weight': QFont.Weight.Medium, 'spacing': 0.02}
    }
    
    # Spacing system (4px base)
    SPACING = {
        'xxs': 2,
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
        'xxxl': 64
    }
    
    # Border radius values
    RADIUS = {
        'none': 0,
        'sm': 4,
        'md': 8,
        'lg': 12,
        'xl': 16,
        'full': 9999
    }
    
    @classmethod
    def apply_theme(cls, app: QApplication):
        """Apply the modern theme to the entire application"""
        # Load custom fonts
        cls._load_fonts()
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and set palette
        palette = cls._create_palette()
        app.setPalette(palette)
        
        # Apply global stylesheet
        app.setStyleSheet(cls._get_global_stylesheet())
    
    @classmethod
    def _load_fonts(cls):
        """Load custom fonts for WSJ-style typography"""
        # Note: In production, load actual font files
        # QFontDatabase.addApplicationFont("path/to/PlayfairDisplay.ttf")
        # QFontDatabase.addApplicationFont("path/to/SourceSansPro.ttf")
        pass
    
    @classmethod
    def _create_palette(cls) -> QPalette:
        """Create a custom color palette"""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.COLORS['background']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.COLORS['text_primary']))
        
        # Base colors (for input fields)
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.COLORS['surface']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.COLORS['surface_variant']))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.COLORS['surface']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.COLORS['text_primary']))
        
        # Selection colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.COLORS['primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.COLORS['text_inverse']))
        
        return palette
    
    @classmethod
    def _get_global_stylesheet(cls) -> str:
        """Generate the global application stylesheet"""
        return f"""
        /* Global font settings */
        * {{
            font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: {cls.TYPOGRAPHY['body']['size']}px;
        }}
        
        /* Headers with serif font */
        QLabel[class="heading"] {{
            font-family: 'Playfair Display', Georgia, serif;
        }}
        
        /* Remove all borders by default */
        QWidget {{
            border: none;
            outline: none;
        }}
        
        /* Scrollbar styling */
        QScrollBar:vertical {{
            background: {cls.COLORS['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {cls.COLORS['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {cls.COLORS['text_tertiary']};
        }}
        
        /* Tool tips */
        QToolTip {{
            background-color: {cls.COLORS['text_primary']};
            color: {cls.COLORS['text_inverse']};
            border: none;
            padding: {cls.SPACING['xs']}px {cls.SPACING['sm']}px;
            border-radius: {cls.RADIUS['sm']}px;
            font-size: {cls.TYPOGRAPHY['body_small']['size']}px;
        }}
        """
    
    @classmethod
    def get_button_style(cls, variant: str = 'primary', size: str = 'medium') -> str:
        """Get button stylesheet for different variants"""
        # Base button styles
        base_padding = {
            'small': f"{cls.SPACING['sm']}px {cls.SPACING['md']}px",
            'medium': f"{cls.SPACING['sm'] + 4}px {cls.SPACING['lg']}px",
            'large': f"{cls.SPACING['md']}px {cls.SPACING['xl']}px"
        }
        
        base_style = f"""
        QPushButton {{
            border-radius: {cls.RADIUS['sm']}px;
            padding: {base_padding.get(size, base_padding['medium'])};
            font-size: {cls.TYPOGRAPHY['button']['size']}px;
            font-weight: 500;
            letter-spacing: {cls.TYPOGRAPHY['button']['spacing']}em;
            border: none;
            background-color: {cls.COLORS.get(variant, cls.COLORS['primary'])};
            color: {cls.COLORS['text_inverse'] if variant == 'primary' else cls.COLORS['text_primary']};
        }}
        
        QPushButton:hover {{
            background-color: {cls.COLORS.get(f'{variant}_hover', cls.COLORS['primary_hover'])};
        }}
        
        QPushButton:pressed {{
            background-color: {cls.COLORS.get(f'{variant}_pressed', cls.COLORS['primary_pressed'])};
        }}
        
        QPushButton:focus {{
            outline: none;
            border: 2px solid {cls.COLORS['primary']};
        }}
        
        QPushButton:disabled {{
            background-color: {cls.COLORS['border']};
            color: {cls.COLORS['text_tertiary']};
        }}
        """
        
        # Variant-specific styles
        if variant == 'secondary':
            base_style = f"""
            QPushButton {{
                border-radius: {cls.RADIUS['sm']}px;
                padding: {base_padding.get(size, base_padding['medium'])};
                font-size: {cls.TYPOGRAPHY['button']['size']}px;
                font-weight: 500;
                letter-spacing: {cls.TYPOGRAPHY['button']['spacing']}em;
                border: 1px solid {cls.COLORS['border']};
                background-color: {cls.COLORS['surface']};
                color: {cls.COLORS['text_primary']};
            }}
            
            QPushButton:hover {{
                background-color: {cls.COLORS['surface_variant']};
                border-color: {cls.COLORS['text_tertiary']};
            }}
            """
        
        elif variant == 'ghost':
            base_style = f"""
            QPushButton {{
                border-radius: {cls.RADIUS['sm']}px;
                padding: {base_padding.get(size, base_padding['medium'])};
                font-size: {cls.TYPOGRAPHY['button']['size']}px;
                font-weight: 500;
                letter-spacing: {cls.TYPOGRAPHY['button']['spacing']}em;
                border: none;
                background-color: transparent;
                color: {cls.COLORS['primary']};
            }}
            
            QPushButton:hover {{
                background-color: {cls.COLORS['surface']};
            }}
            """
        
        return base_style
    
    @classmethod
    def get_card_style(cls, elevated: bool = True) -> str:
        """Get card/panel stylesheet"""
        shadow = f"0 2px 4px {cls.COLORS['shadow']}" if elevated else "none"
        
        return f"""
        QFrame {{
            background-color: {cls.COLORS['background']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['md']}px;
            padding: {cls.SPACING['lg']}px;
        }}
        
        QFrame:hover {{
            border-color: {cls.COLORS['text_tertiary']};
        }}
        """
    
    @classmethod
    def get_input_style(cls) -> str:
        """Get input field stylesheet"""
        return f"""
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            height: 40px;
            padding: 0 {cls.SPACING['md']}px;
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['sm']}px;
            background-color: {cls.COLORS['surface']};
            color: {cls.COLORS['text_primary']};
            font-size: {cls.TYPOGRAPHY['body']['size']}px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border-color: {cls.COLORS['primary']};
            background-color: {cls.COLORS['background']};
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
            background-color: {cls.COLORS['surface_variant']};
            color: {cls.COLORS['text_tertiary']};
        }}
        
        /* Combo box dropdown button */
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {cls.COLORS['text_secondary']};
            margin-right: 8px;
        }}
        """
    
    @classmethod
    def get_tab_style(cls) -> str:
        """Get tab widget stylesheet for WSJ-style navigation"""
        return f"""
        QTabWidget::pane {{
            border: none;
            background-color: {cls.COLORS['background']};
        }}
        
        QTabBar {{
            background-color: {cls.COLORS['surface']};
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {cls.COLORS['text_secondary']};
            padding: {cls.SPACING['sm']}px {cls.SPACING['lg']}px;
            margin-right: {cls.SPACING['xs']}px;
            border-bottom: 2px solid transparent;
            font-weight: 500;
            font-size: {cls.TYPOGRAPHY['body']['size']}px;
        }}
        
        QTabBar::tab:hover {{
            color: {cls.COLORS['text_primary']};
            background-color: {cls.COLORS['surface_variant']};
        }}
        
        QTabBar::tab:selected {{
            color: {cls.COLORS['primary']};
            border-bottom: 2px solid {cls.COLORS['primary']};
            background-color: {cls.COLORS['background']};
        }}
        """
    
    @classmethod
    def get_label_style(cls, variant: str = 'body') -> str:
        """Get label stylesheet for different text styles"""
        typography = cls.TYPOGRAPHY.get(variant, cls.TYPOGRAPHY['body'])
        
        color = cls.COLORS['text_primary']
        if variant == 'secondary':
            color = cls.COLORS['text_secondary']
        elif variant == 'caption':
            color = cls.COLORS['text_tertiary']
        
        return f"""
        QLabel {{
            color: {color};
            font-size: {typography['size']}px;
            font-weight: {typography['weight'].value if hasattr(typography['weight'], 'value') else typography['weight']};
            letter-spacing: {typography['spacing']}em;
        }}
        """
    
    @classmethod
    def get_progress_bar_style(cls) -> str:
        """Get progress bar stylesheet"""
        return f"""
        QProgressBar {{
            border: none;
            border-radius: {cls.RADIUS['sm']}px;
            background-color: {cls.COLORS['surface']};
            height: 8px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {cls.COLORS['primary']};
            border-radius: {cls.RADIUS['sm']}px;
        }}
        """


## 2. Enhanced Calendar Heatmap Component

```python
# src/ui/charts/calendar_heatmap.py

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient
from PyQt6.QtWidgets import QWidget, QToolTip
from datetime import datetime, timedelta
import math

class ModernCalendarHeatmap(QWidget):
    """WSJ-style calendar heatmap with sophisticated design"""
    
    cellHovered = pyqtSignal(datetime, float)  # date, value
    cellClicked = pyqtSignal(datetime)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        
        # Data
        self.data = {}  # {datetime: value}
        self.min_value = 0
        self.max_value = 100
        
        # Visual settings
        self.cell_size = 16
        self.cell_spacing = 3
        self.corner_radius = 3
        
        # Colors (WSJ-inspired gradient)
        self.empty_color = QColor('#F8F9FA')
        self.colors = [
            QColor('#F8F9FA'),  # Lightest
            QColor('#E9ECEF'),
            QColor('#CED4DA'),
            QColor('#ADB5BD'),
            QColor('#6C757D'),
            QColor('#5B6770')   # Darkest (primary)
        ]
        
        # Fonts
        self.label_font = QFont('Source Sans Pro', 10)
        self.month_font = QFont('Source Sans Pro', 11, QFont.Weight.Medium)
        
        # Interaction
        self.hovered_date = None
        self.setMouseTracking(True)
        
    def set_data(self, data: dict):
        """Set the heatmap data"""
        self.data = data
        if data:
            values = [v for v in data.values() if v is not None]
            if values:
                self.min_value = min(values)
                self.max_value = max(values)
        self.update()
    
    def paintEvent(self, event):
        """Paint the calendar heatmap with modern styling"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor('#FFFFFF'))
        
        # Calculate dimensions
        cell_total = self.cell_size + self.cell_spacing
        left_margin = 50  # Space for day labels
        top_margin = 30   # Space for month labels
        
        # Get date range
        if not self.data:
            self._draw_empty_state(painter)
            return
        
        dates = sorted(self.data.keys())
        start_date = dates[0]
        end_date = dates[-1]
        
        # Draw month labels
        painter.setFont(self.month_font)
        painter.setPen(QPen(QColor('#212529')))
        
        current_month = None
        x = left_margin
        
        # Draw cells
        current_date = start_date
        week_col = 0
        
        while current_date <= end_date:
            # Check if new month
            if current_date.month != current_month:
                current_month = current_date.month
                month_x = x - self.cell_spacing
                painter.drawText(
                    month_x, 
                    top_margin - 10, 
                    current_date.strftime('%b')
                )
            
            # Calculate position
            weekday = current_date.weekday()
            y = top_margin + weekday * cell_total
            
            # Get value and color
            value = self.data.get(current_date, None)
            color = self._get_color_for_value(value)
            
            # Draw cell with rounded corners
            cell_rect = QRectF(x, y, self.cell_size, self.cell_size)
            
            # Add subtle shadow for cells with data
            if value is not None and value > self.min_value:
                shadow_rect = cell_rect.adjusted(1, 1, 1, 1)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
                painter.drawRoundedRect(shadow_rect, self.corner_radius, self.corner_radius)
            
            # Draw main cell
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(cell_rect, self.corner_radius, self.corner_radius)
            
            # Hover effect
            if self.hovered_date == current_date:
                painter.setPen(QPen(QColor('#5B6770'), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(cell_rect, self.corner_radius, self.corner_radius)
            
            # Move to next date
            current_date += timedelta(days=1)
            if current_date.weekday() == 0:  # New week
                x += cell_total
                week_col += 1
        
        # Draw day labels
        painter.setFont(self.label_font)
        painter.setPen(QPen(QColor('#6C757D')))
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            y = top_margin + i * cell_total + self.cell_size // 2 + 4
            painter.drawText(5, y, day)
        
        # Draw color legend
        self._draw_legend(painter, left_margin, top_margin + 8 * cell_total)
    
    def _get_color_for_value(self, value):
        """Get color based on value with smooth gradient"""
        if value is None:
            return self.empty_color
        
        if self.max_value == self.min_value:
            return self.colors[-1]
        
        # Normalize value to 0-1
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        
        # Get color index
        index = int(normalized * (len(self.colors) - 1))
        index = max(0, min(index, len(self.colors) - 1))
        
        return self.colors[index]
    
    def _draw_legend(self, painter, x, y):
        """Draw a gradient legend"""
        painter.setFont(self.label_font)
        painter.setPen(QPen(QColor('#6C757D')))
        
        # Label
        painter.drawText(x, y + 15, "Less")
        
        # Gradient boxes
        box_width = 12
        box_spacing = 2
        current_x = x + 35
        
        for color in self.colors:
            rect = QRectF(current_x, y, box_width, box_width)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(rect, 2, 2)
            current_x += box_width + box_spacing
        
        # End label
        painter.setPen(QPen(QColor('#6C757D')))
        painter.drawText(current_x + 5, y + 15, "More")
    
    def _draw_empty_state(self, painter):
        """Draw empty state with guidance"""
        painter.setPen(QPen(QColor('#6C757D')))
        painter.setFont(QFont('Source Sans Pro', 14))
        
        text = "No data available"
        text_rect = painter.fontMetrics().boundingRect(text)
        x = (self.width() - text_rect.width()) // 2
        y = (self.height() + text_rect.height()) // 2
        
        painter.drawText(x, y, text)
    
    def mouseMoveEvent(self, event):
        """Handle mouse hover with tooltip"""
        date = self._get_date_at_position(event.position())
        
        if date != self.hovered_date:
            self.hovered_date = date
            self.update()
            
            if date and date in self.data:
                value = self.data[date]
                tooltip_text = f"{date.strftime('%b %d, %Y')}\nValue: {value:.0f}"
                QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
            else:
                QToolTip.hideText()
    
    def _get_date_at_position(self, pos):
        """Get the date at the given position"""
        # Implementation depends on layout calculation
        # This is a simplified version
        return None  # Implement based on actual layout


## 3. Modern Tab Navigation

```python
# src/ui/components/modern_tab_bar.py

from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QTabBar, QStyleOptionTab, QStyle

class ModernTabBar(QTabBar):
    """Custom tab bar with modern animations and styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Animation properties
        self._hover_index = -1
        self._animation_progress = 0.0
        
        # Style settings
        self.indicator_height = 3
        self.indicator_color = QColor('#5B6770')
        
        # Animation
        self.animation = QPropertyAnimation(self, b"animationProgress")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    @pyqtProperty(float)
    def animationProgress(self):
        return self._animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        self._animation_progress = value
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for modern tab appearance"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw each tab
        for index in range(self.count()):
            self._draw_tab(painter, index)
        
        # Draw selection indicator with animation
        if self.currentIndex() >= 0:
            self._draw_indicator(painter, self.currentIndex())
    
    def _draw_tab(self, painter, index):
        """Draw individual tab"""
        rect = self.tabRect(index)
        is_selected = index == self.currentIndex()
        is_hovered = index == self._hover_index
        
        # Background
        if is_selected:
            painter.fillRect(rect, QColor('#FFFFFF'))
        elif is_hovered:
            painter.fillRect(rect, QColor('#F8F9FA'))
        
        # Text
        text_color = QColor('#5B6770') if is_selected else QColor('#6C757D')
        if is_hovered and not is_selected:
            text_color = QColor('#212529')
        
        painter.setPen(QPen(text_color))
        painter.setFont(self.font())
        
        # Draw text centered
        text = self.tabText(index)
        text_rect = rect.adjusted(16, 0, -16, 0)
        painter.drawText(
            text_rect, 
            Qt.AlignmentFlag.AlignCenter, 
            text
        )
    
    def _draw_indicator(self, painter, index):
        """Draw the selection indicator with smooth animation"""
        rect = self.tabRect(index)
        
        # Calculate indicator position
        indicator_rect = QRect(
            rect.x(),
            rect.bottom() - self.indicator_height,
            rect.width(),
            self.indicator_height
        )
        
        # Draw with rounded ends
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.indicator_color))
        painter.drawRoundedRect(indicator_rect, 1.5, 1.5)
    
    def enterEvent(self, event):
        """Start hover animation"""
        # Implement hover tracking
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """End hover animation"""
        self._hover_index = -1
        self.update()
        super().leaveEvent(event)


## 4. Modern Button Component

```python
# src/ui/components/modern_button.py

from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import QPushButton
import math

class ModernButton(QPushButton):
    """Enhanced button with ripple effect and modern styling"""
    
    def __init__(self, text="", variant="primary", size="medium", parent=None):
        super().__init__(text, parent)
        
        self.variant = variant
        self.size = size
        
        # Animation properties
        self._ripple_position = None
        self._ripple_radius = 0
        self._hover_progress = 0
        
        # Colors based on variant
        self.colors = self._get_variant_colors()
        
        # Setup animations
        self.ripple_animation = QPropertyAnimation(self, b"rippleRadius")
        self.ripple_animation.setDuration(600)
        self.ripple_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        self.hover_animation = QPropertyAnimation(self, b"hoverProgress")
        self.hover_animation.setDuration(200)
        
        # Apply size
        self._apply_size()
        
        # Enable hover
        self.setMouseTracking(True)
    
    def _get_variant_colors(self):
        """Get colors based on variant"""
        variants = {
            'primary': {
                'background': QColor('#5B6770'),
                'hover': QColor('#4A5560'),
                'pressed': QColor('#3A4550'),
                'text': QColor('#FFFFFF'),
                'ripple': QColor(255, 255, 255, 50)
            },
            'secondary': {
                'background': QColor('#F8F9FA'),
                'hover': QColor('#E9ECEF'),
                'pressed': QColor('#DEE2E6'),
                'text': QColor('#212529'),
                'ripple': QColor(91, 103, 112, 30)
            },
            'success': {
                'background': QColor('#28A745'),
                'hover': QColor('#218838'),
                'pressed': QColor('#1E7E34'),
                'text': QColor('#FFFFFF'),
                'ripple': QColor(255, 255, 255, 50)
            }
        }
        return variants.get(self.variant, variants['primary'])
    
    def _apply_size(self):
        """Apply size-based styling"""
        sizes = {
            'small': (28, 8, 16),    # height, h_padding, v_padding
            'medium': (36, 12, 24),
            'large': (44, 16, 32)
        }
        
        height, v_pad, h_pad = sizes.get(self.size, sizes['medium'])
        self.setFixedHeight(height)
        self.setContentsMargins(h_pad, v_pad, h_pad, v_pad)
    
    @pyqtProperty(int)
    def rippleRadius(self):
        return self._ripple_radius
    
    @rippleRadius.setter
    def rippleRadius(self, value):
        self._ripple_radius = value
        self.update()
    
    @pyqtProperty(float)
    def hoverProgress(self):
        return self._hover_progress
    
    @hoverProgress.setter
    def hoverProgress(self, value):
        self._hover_progress = value
        self.update()
    
    def paintEvent(self, event):
        """Custom paint with ripple effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get current colors
        if self.isDown():
            bg_color = self.colors['pressed']
        else:
            # Interpolate between normal and hover
            bg_color = self._interpolate_color(
                self.colors['background'],
                self.colors['hover'],
                self._hover_progress
            )
        
        # Draw background with rounded corners
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), 4, 4)
        
        # Draw ripple effect
        if self._ripple_position and self._ripple_radius > 0:
            painter.setBrush(QBrush(self.colors['ripple']))
            painter.drawEllipse(
                self._ripple_position,
                self._ripple_radius,
                self._ripple_radius
            )
        
        # Draw text
        painter.setPen(QPen(self.colors['text']))
        painter.setFont(self.font())
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.text()
        )
    
    def _interpolate_color(self, start, end, progress):
        """Interpolate between two colors"""
        r = start.red() + (end.red() - start.red()) * progress
        g = start.green() + (end.green() - start.green()) * progress
        b = start.blue() + (end.blue() - start.blue()) * progress
        return QColor(int(r), int(g), int(b))
    
    def mousePressEvent(self, event):
        """Start ripple animation on click"""
        self._ripple_position = event.position()
        
        # Calculate max radius
        distances = [
            math.sqrt(event.position().x()**2 + event.position().y()**2),
            math.sqrt((self.width() - event.position().x())**2 + event.position().y()**2),
            math.sqrt(event.position().x()**2 + (self.height() - event.position().y())**2),
            math.sqrt((self.width() - event.position().x())**2 + (self.height() - event.position().y())**2)
        ]
        max_radius = max(distances)
        
        # Start animation
        self.ripple_animation.setStartValue(0)
        self.ripple_animation.setEndValue(int(max_radius))
        self.ripple_animation.start()
        
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Animate hover state"""
        self.hover_animation.setStartValue(self._hover_progress)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animate leave state"""
        self.hover_animation.setStartValue(self._hover_progress)
        self.hover_animation.setEndValue(0.0)
        self.hover_animation.start()
        super().leaveEvent(event)


## 5. Implementation Guide for Main Window

```python
# Example usage in main_window.py

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from .style_manager import ModernStyleManager
from .components.modern_button import ModernButton
from .components.modern_tab_bar import ModernTabBar

class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Apply modern theme
        ModernStyleManager.apply_theme(QApplication.instance())
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        # Create central widget with modern styling
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("""
            #centralWidget {
                background-color: #FFFFFF;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(ModernStyleManager.SPACING['md'])
        layout.setContentsMargins(
            ModernStyleManager.SPACING['lg'],
            ModernStyleManager.SPACING['lg'],
            ModernStyleManager.SPACING['lg'],
            ModernStyleManager.SPACING['lg']
        )
        
        # Add modern button examples
        primary_btn = ModernButton("Import Data", variant="primary")
        secondary_btn = ModernButton("Cancel", variant="secondary")
        
        # Apply additional styling
        for widget in [primary_btn, secondary_btn]:
            widget.setStyleSheet(ModernStyleManager.get_button_style(widget.variant))
        
        # Add widgets to layout
        layout.addWidget(primary_btn)
        layout.addWidget(secondary_btn)
        
        self.setCentralWidget(central_widget)
```

This implementation provides:

1. **Complete StyleManager** with WSJ-inspired design system
2. **Modern Calendar Heatmap** with smooth gradients and hover effects
3. **Custom Tab Bar** with animated indicators
4. **Enhanced Button Component** with ripple effects
5. **Integration examples** showing how to use these components

The design follows Wall Street Journal's aesthetic principles while maintaining modern UI patterns and excellent user experience.