# Modern UI Component Examples for PyQt6

## 1. Modern Metric Card with Shadow Effect

```python
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

class ModernMetricCard(QFrame):
    def __init__(self, title="", value="", trend="", parent=None):
        super().__init__(parent)
        self.setup_ui(title, value, trend)
        self.apply_modern_style()
        
    def setup_ui(self, title, value, trend):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #57606A; letter-spacing: 0.5px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Inter", 32, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #0D1117;")
        layout.addWidget(value_label)
        
        # Trend
        if trend:
            trend_layout = QHBoxLayout()
            trend_icon = QLabel("↑" if "+" in trend else "↓")
            trend_icon.setStyleSheet(
                f"color: {'#06D6A0' if '+' in trend else '#EF476F'}; font-size: 18px;"
            )
            trend_layout.addWidget(trend_icon)
            
            trend_label = QLabel(trend)
            trend_label.setStyleSheet(
                f"color: {'#06D6A0' if '+' in trend else '#EF476F'}; font-size: 14px; font-weight: 500;"
            )
            trend_layout.addWidget(trend_label)
            trend_layout.addStretch()
            layout.addLayout(trend_layout)
    
    def apply_modern_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
```

## 2. Modern Navigation Tab Bar

```python
from PyQt6.QtWidgets import QTabBar, QStylePainter, QStyleOptionTab, QStyle
from PyQt6.QtCore import QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPainterPath

class ModernTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabBar {
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                color: #57606A;
                padding: 12px 24px;
                margin: 0 4px;
                font-weight: 500;
                font-size: 15px;
            }
            QTabBar::tab:selected {
                color: #FF6B35;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                color: #0D1117;
            }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw pill-shaped indicator under selected tab
        selected = self.currentIndex()
        if selected >= 0:
            rect = self.tabRect(selected)
            
            # Draw indicator
            indicator_height = 3
            indicator_rect = QRect(
                rect.x() + 20,
                rect.bottom() - indicator_height - 5,
                rect.width() - 40,
                indicator_height
            )
            
            painter.setBrush(QColor("#FF6B35"))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Rounded rectangle
            path = QPainterPath()
            path.addRoundedRect(indicator_rect, indicator_height // 2, indicator_height // 2)
            painter.drawPath(path)
```

## 3. Modern Button with Hover Effects

```python
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QPalette

class ModernButton(QPushButton):
    def __init__(self, text="", variant="primary", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self._animation = QPropertyAnimation(self, b"color")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.apply_style()
        
    def apply_style(self):
        styles = {
            "primary": """
                QPushButton {
                    background-color: #FF6B35;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #E85D2F;
                }
                QPushButton:pressed {
                    background-color: #CC4125;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #F6F8FA;
                    color: #0D1117;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 500;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #E9ECEF;
                }
            """,
            "outline": """
                QPushButton {
                    background-color: transparent;
                    color: #FF6B35;
                    border: 2px solid #FF6B35;
                    padding: 10px 22px;
                    border-radius: 8px;
                    font-weight: 500;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 107, 53, 0.08);
                    border-color: #E85D2F;
                }
            """
        }
        self.setStyleSheet(styles.get(self.variant, styles["primary"]))
```

## 4. Modern Input Field with Floating Label

```python
from PyQt6.QtWidgets import QWidget, QLineEdit, QLabel, QVBoxLayout
from PyQt6.QtCore import QPropertyAnimation, pyqtProperty, QRect
from PyQt6.QtGui import QFont

class ModernTextField(QWidget):
    def __init__(self, label="", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(70)
        
        # Floating label
        self.label = QLabel(self.label_text, self)
        self.label.setStyleSheet("color: #8B949E; font-size: 15px;")
        self.label.move(12, 25)
        
        # Input field
        self.input = QLineEdit(self)
        self.input.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 2px solid #E9ECEF;
                padding: 25px 12px 8px 12px;
                font-size: 15px;
                background: transparent;
                color: #0D1117;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #FF6B35;
            }
        """)
        self.input.setGeometry(0, 0, self.width(), 70)
        
        # Animations
        self.label_animation = QPropertyAnimation(self.label, b"geometry")
        self.label_animation.setDuration(200)
        
        # Connect signals
        self.input.textChanged.connect(self.on_text_changed)
        self.input.focusInEvent = self.on_focus_in
        self.input.focusOutEvent = self.on_focus_out
        
    def on_text_changed(self, text):
        if text and self.label.y() == 25:
            self.float_label_up()
        elif not text and not self.input.hasFocus():
            self.float_label_down()
            
    def on_focus_in(self, event):
        if not self.input.text():
            self.float_label_up()
        super(QLineEdit, self.input).focusInEvent(event)
        
    def on_focus_out(self, event):
        if not self.input.text():
            self.float_label_down()
        super(QLineEdit, self.input).focusOutEvent(event)
        
    def float_label_up(self):
        self.label_animation.setStartValue(self.label.geometry())
        self.label_animation.setEndValue(QRect(12, 8, self.label.width(), self.label.height()))
        self.label_animation.start()
        self.label.setStyleSheet("color: #FF6B35; font-size: 12px; font-weight: 500;")
        
    def float_label_down(self):
        self.label_animation.setStartValue(self.label.geometry())
        self.label_animation.setEndValue(QRect(12, 25, self.label.width(), self.label.height()))
        self.label_animation.start()
        self.label.setStyleSheet("color: #8B949E; font-size: 15px; font-weight: 400;")
```

## 5. Modern Progress Indicator

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QConicalGradient

class ModernCircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 100
        self.setFixedSize(120, 120)
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_value)
        
    def set_value(self, value):
        self.target_value = value
        self.animation_timer.start(10)
        
    def update_value(self):
        if self.value < self.target_value:
            self.value += 2
            if self.value >= self.target_value:
                self.value = self.target_value
                self.animation_timer.stop()
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background circle
        pen = QPen(QColor("#F6F8FA"), 8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(10, 10, 100, 100, 0, 360 * 16)
        
        # Progress arc
        gradient = QConicalGradient(60, 60, 90)
        gradient.setColorAt(0, QColor("#FF6B35"))
        gradient.setColorAt(1, QColor("#FFB700"))
        
        pen = QPen(gradient, 8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw progress
        span_angle = int((self.value / self.max_value) * 360 * 16)
        painter.drawArc(10, 10, 100, 100, 90 * 16, -span_angle)
        
        # Draw percentage text
        painter.setPen(QColor("#0D1117"))
        painter.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value}%")
```

## 6. Modern Toast Notification

```python
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, QPropertyAnimation, Qt
from PyQt6.QtGui import QFont

class ModernToast(QWidget):
    def __init__(self, message, toast_type="info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.toast_type = toast_type
        self.setup_ui(message)
        self.setup_animation()
        
    def setup_ui(self, message):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Icon
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        
        icon_label = QLabel(icons.get(self.toast_type, "ℹ"))
        icon_label.setStyleSheet(f"""
            font-size: 20px;
            color: {self.get_color()};
        """)
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setFont(QFont("Inter", 14))
        message_label.setStyleSheet("color: white; margin-left: 12px;")
        layout.addWidget(message_label)
        
        # Style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.get_background_color()};
                border-radius: 8px;
            }}
        """)
        
    def get_color(self):
        colors = {
            "success": "#FFFFFF",
            "error": "#FFFFFF",
            "warning": "#0D1117",
            "info": "#FFFFFF"
        }
        return colors.get(self.toast_type, "#FFFFFF")
        
    def get_background_color(self):
        colors = {
            "success": "#06D6A0",
            "error": "#EF476F",
            "warning": "#FFB700",
            "info": "#118AB2"
        }
        return colors.get(self.toast_type, "#118AB2")
        
    def setup_animation(self):
        # Fade in
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        
        # Auto hide
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.fade_out)
        self.hide_timer.setSingleShot(True)
        
    def show_toast(self):
        self.show()
        self.fade_in.start()
        self.hide_timer.start(3000)
        
    def fade_out(self):
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()
```

## Usage Examples

```python
# 1. Create modern metric cards
steps_card = ModernMetricCard("Daily Steps", "12,450", "+15% from yesterday")
calories_card = ModernMetricCard("Calories Burned", "2,340", "-5% from yesterday")

# 2. Create modern buttons
primary_btn = ModernButton("Save Changes", "primary")
secondary_btn = ModernButton("Cancel", "secondary")
outline_btn = ModernButton("Learn More", "outline")

# 3. Create modern input fields
name_field = ModernTextField("Full Name")
email_field = ModernTextField("Email Address")

# 4. Show toast notifications
success_toast = ModernToast("Data saved successfully!", "success", parent_window)
success_toast.move(parent_window.width() - 350, 50)
success_toast.show_toast()

# 5. Create circular progress
progress = ModernCircularProgress()
progress.set_value(75)  # Animates to 75%
```

## Integration Tips

1. **Consistent Spacing**: Use multiples of 4px (4, 8, 12, 16, 20, 24, 32, 48)
2. **Shadow Effects**: Use QGraphicsDropShadowEffect sparingly for performance
3. **Animations**: Keep animations under 300ms for responsiveness
4. **Colors**: Use the defined color palette consistently
5. **Icons**: Consider using Font Awesome or Material Icons fonts
6. **Responsive**: Use layouts instead of fixed positions when possible

## Performance Considerations

- Limit shadow effects to important elements only
- Cache complex painted widgets
- Use style sheets efficiently (apply to parent when possible)
- Minimize animation complexity
- Test on lower-end hardware