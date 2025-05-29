"""Animation utilities for modern dialog effects."""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize, pyqtProperty
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


class DialogAnimationMixin:
    """Mixin class to add smooth animations to dialogs."""
    
    def setup_animations(self):
        """Setup animation properties for the dialog."""
        # Opacity effect for fade animations
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)
        
        # Opacity animation
        self._opacity_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_animation.setDuration(200)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Position animation for slide effects
        self._position_animation = QPropertyAnimation(self, b"pos")
        self._position_animation.setDuration(300)
        self._position_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Size animation for scale effects
        self._size_animation = QPropertyAnimation(self, b"size")
        self._size_animation.setDuration(300)
        self._size_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def animate_show(self):
        """Animate dialog appearance with fade and scale effect."""
        # Start with dialog slightly smaller and transparent
        original_size = self.size()
        start_size = QSize(int(original_size.width() * 0.95), 
                          int(original_size.height() * 0.95))
        
        # Calculate center position
        if self.parent():
            parent_center = self.parent().rect().center()
            final_pos = QPoint(parent_center.x() - original_size.width() // 2,
                             parent_center.y() - original_size.height() // 2)
            start_pos = QPoint(final_pos.x() + (original_size.width() - start_size.width()) // 2,
                             final_pos.y() + (original_size.height() - start_size.height()) // 2 + 20)
        else:
            final_pos = self.pos()
            start_pos = QPoint(final_pos.x(), final_pos.y() + 20)
        
        # Setup animations
        self.resize(start_size)
        self.move(start_pos)
        self._opacity_effect.setOpacity(0.0)
        
        # Animate opacity
        self._opacity_animation.setStartValue(0.0)
        self._opacity_animation.setEndValue(1.0)
        
        # Animate position
        self._position_animation.setStartValue(start_pos)
        self._position_animation.setEndValue(final_pos)
        
        # Animate size
        self._size_animation.setStartValue(start_size)
        self._size_animation.setEndValue(original_size)
        
        # Start animations
        self._opacity_animation.start()
        self._position_animation.start()
        self._size_animation.start()
    
    def animate_hide(self):
        """Animate dialog disappearance with fade effect."""
        self._opacity_animation.setStartValue(1.0)
        self._opacity_animation.setEndValue(0.0)
        self._opacity_animation.finished.connect(self.hide)
        self._opacity_animation.start()


class AnimatedProgressBar(QWidget):
    """Custom progress bar with smooth animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._animation = QPropertyAnimation(self, b"progress")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    
    @pyqtProperty(int)
    def progress(self):
        """Get current progress value."""
        return self._progress
    
    @progress.setter
    def progress(self, value):
        """Set progress value with animation."""
        self._progress = value
        self.update()
    
    def setProgress(self, value):
        """Animate to new progress value."""
        self._animation.setStartValue(self._progress)
        self._animation.setEndValue(value)
        self._animation.start()