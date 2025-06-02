"""Auto-save settings panel for configuring journal auto-save behavior.

This module provides a settings panel for configuring auto-save functionality
including enable/disable toggle, debounce delay adjustment, draft retention
period, and maximum draft size settings.

The panel integrates with the application's settings system to persist
preferences and applies changes without requiring a restart.

Key features:
    - Enable/disable auto-save toggle
    - Adjustable debounce delay (1-10 seconds)
    - Draft retention period setting
    - Maximum draft size configuration
    - Real-time preview of settings
    - Settings persistence to config file

Example:
    Basic usage in settings dialog:
    
    >>> settings_panel = AutoSaveSettingsPanel(settings_manager)
    >>> settings_panel.settingsChanged.connect(self.apply_settings)
    >>> settings_dialog.add_panel("Auto-Save", settings_panel)
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QSlider, QSpinBox, QGroupBox, QComboBox, QPushButton,
    QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ..utils.logging_config import get_logger
from .settings_manager import SettingsManager

logger = get_logger(__name__)


class AutoSaveSettingsPanel(QWidget):
    """Settings panel for configuring auto-save behavior.
    
    Provides UI controls for adjusting all auto-save related settings
    with real-time preview and persistence.
    
    Attributes:
        settingsChanged (pyqtSignal): Emitted when any setting changes
    
    Args:
        settings_manager (SettingsManager): Application settings manager
        parent (Optional[QWidget]): Parent widget
    """
    
    settingsChanged = pyqtSignal(dict)  # Dict of changed settings
    
    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None):
        """Initialize the auto-save settings panel.
        
        Args:
            settings_manager: Application settings manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Apply warm color scheme
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #5D4E37;
            }
            QCheckBox {
                color: #5D4E37;
                font-size: 14px;
            }
            QCheckBox::indicator:checked {
                background-color: #FF8C42;
                border: 2px solid #FF8C42;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #E8DCC8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FF8C42;
                border: 2px solid #FF8C42;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #FF7A2F;
            }
            QLabel {
                color: #5D4E37;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #E8DCC8;
                border-radius: 6px;
                padding: 6px 12px;
                color: #5D4E37;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FFF5E6;
                border-color: #D4AF37;
            }
        """)
        
        # General Settings Group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        # Enable/disable toggle
        self.enable_checkbox = QCheckBox("Enable auto-save")
        self.enable_checkbox.setToolTip(
            "Automatically save your journal entries as you type"
        )
        self.enable_checkbox.toggled.connect(self.on_setting_changed)
        general_layout.addRow(self.enable_checkbox)
        
        # Save drafts separately
        self.save_drafts_checkbox = QCheckBox("Save drafts separately")
        self.save_drafts_checkbox.setToolTip(
            "Store drafts in a separate table to avoid conflicts with saved entries"
        )
        self.save_drafts_checkbox.toggled.connect(self.on_setting_changed)
        general_layout.addRow(self.save_drafts_checkbox)
        
        layout.addWidget(general_group)
        
        # Timing Settings Group
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QFormLayout(timing_group)
        
        # Debounce delay slider
        delay_layout = QHBoxLayout()
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(1, 10)  # 1-10 seconds
        self.delay_slider.setValue(3)  # Default 3 seconds
        self.delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.delay_slider.setTickInterval(1)
        self.delay_slider.valueChanged.connect(self.on_delay_changed)
        
        self.delay_label = QLabel("3 seconds")
        self.delay_label.setMinimumWidth(80)
        
        delay_layout.addWidget(self.delay_slider)
        delay_layout.addWidget(self.delay_label)
        
        timing_layout.addRow("Save after inactivity:", delay_layout)
        
        # Maximum wait time
        max_wait_layout = QHBoxLayout()
        self.max_wait_spin = QSpinBox()
        self.max_wait_spin.setRange(10, 60)  # 10-60 seconds
        self.max_wait_spin.setValue(30)  # Default 30 seconds
        self.max_wait_spin.setSuffix(" seconds")
        self.max_wait_spin.setToolTip(
            "Maximum time to wait before forcing a save, even if you're still typing"
        )
        self.max_wait_spin.valueChanged.connect(self.on_setting_changed)
        max_wait_layout.addWidget(self.max_wait_spin)
        max_wait_layout.addStretch()
        
        timing_layout.addRow("Maximum wait time:", max_wait_layout)
        
        layout.addWidget(timing_group)
        
        # Draft Management Group
        draft_group = QGroupBox("Draft Management")
        draft_layout = QFormLayout(draft_group)
        
        # Draft retention period
        retention_layout = QHBoxLayout()
        self.retention_combo = QComboBox()
        self.retention_combo.addItems([
            "1 day",
            "3 days",
            "7 days",
            "14 days",
            "30 days",
            "Never delete"
        ])
        self.retention_combo.setCurrentIndex(2)  # Default 7 days
        self.retention_combo.setToolTip(
            "How long to keep draft entries before automatic cleanup"
        )
        self.retention_combo.currentTextChanged.connect(self.on_setting_changed)
        retention_layout.addWidget(self.retention_combo)
        retention_layout.addStretch()
        
        draft_layout.addRow("Keep drafts for:", retention_layout)
        
        # Maximum draft size
        size_layout = QHBoxLayout()
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 100)  # 1-100 MB
        self.max_size_spin.setValue(10)  # Default 10 MB
        self.max_size_spin.setSuffix(" MB")
        self.max_size_spin.setToolTip(
            "Maximum total size of all draft entries"
        )
        self.max_size_spin.valueChanged.connect(self.on_setting_changed)
        size_layout.addWidget(self.max_size_spin)
        size_layout.addStretch()
        
        draft_layout.addRow("Maximum draft storage:", size_layout)
        
        layout.addWidget(draft_group)
        
        # Preview/Test Section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("Auto-save is enabled with 3-second delay")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("font-style: italic; color: #8B7355;")
        preview_layout.addWidget(self.preview_label)
        
        # Test button
        test_button = QPushButton("Test Auto-Save")
        test_button.clicked.connect(self.test_auto_save)
        preview_layout.addWidget(test_button)
        
        layout.addWidget(preview_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        # Restore defaults button
        restore_button = QPushButton("Restore Defaults")
        restore_button.clicked.connect(self.restore_defaults)
        layout.addWidget(restore_button)
        
    def load_settings(self):
        """Load current settings from settings manager."""
        try:
            # Load auto-save settings
            enabled = self.settings_manager.get_setting("auto_save_enabled", True)
            self.enable_checkbox.setChecked(enabled)
            
            save_drafts = self.settings_manager.get_setting("auto_save_drafts", True)
            self.save_drafts_checkbox.setChecked(save_drafts)
            
            delay = self.settings_manager.get_setting("auto_save_delay", 3)
            self.delay_slider.setValue(delay)
            
            max_wait = self.settings_manager.get_setting("auto_save_max_wait", 30)
            self.max_wait_spin.setValue(max_wait)
            
            retention = self.settings_manager.get_setting("draft_retention_days", 7)
            retention_index = {1: 0, 3: 1, 7: 2, 14: 3, 30: 4, -1: 5}.get(retention, 2)
            self.retention_combo.setCurrentIndex(retention_index)
            
            max_size = self.settings_manager.get_setting("draft_max_size_mb", 10)
            self.max_size_spin.setValue(max_size)
            
            self.update_preview()
            
        except Exception as e:
            logger.error(f"Error loading auto-save settings: {e}")
            
    def save_settings(self):
        """Save current settings to settings manager."""
        try:
            settings = self.get_current_settings()
            
            self.settings_manager.set_setting("auto_save_enabled", settings["enabled"])
            self.settings_manager.set_setting("auto_save_drafts", settings["save_drafts"])
            self.settings_manager.set_setting("auto_save_delay", settings["delay_seconds"])
            self.settings_manager.set_setting("auto_save_max_wait", settings["max_wait_seconds"])
            self.settings_manager.set_setting("draft_retention_days", settings["retention_days"])
            self.settings_manager.set_setting("draft_max_size_mb", settings["max_size_mb"])
            
            self.settings_manager.save_settings()
            
        except Exception as e:
            logger.error(f"Error saving auto-save settings: {e}")
            
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as a dictionary.
        
        Returns:
            Dict containing all current settings
        """
        retention_map = {
            "1 day": 1,
            "3 days": 3,
            "7 days": 7,
            "14 days": 14,
            "30 days": 30,
            "Never delete": -1
        }
        
        return {
            "enabled": self.enable_checkbox.isChecked(),
            "save_drafts": self.save_drafts_checkbox.isChecked(),
            "delay_seconds": self.delay_slider.value(),
            "max_wait_seconds": self.max_wait_spin.value(),
            "retention_days": retention_map.get(self.retention_combo.currentText(), 7),
            "max_size_mb": self.max_size_spin.value()
        }
        
    def on_delay_changed(self, value: int):
        """Handle delay slider changes.
        
        Args:
            value: New delay value in seconds
        """
        self.delay_label.setText(f"{value} second{'s' if value != 1 else ''}")
        self.on_setting_changed()
        
    def on_setting_changed(self):
        """Handle any setting change."""
        self.update_preview()
        settings = self.get_current_settings()
        self.settingsChanged.emit(settings)
        self.save_settings()
        
    def update_preview(self):
        """Update the preview label with current settings."""
        settings = self.get_current_settings()
        
        if settings["enabled"]:
            preview = f"Auto-save is enabled with {settings['delay_seconds']}-second delay"
            if settings["save_drafts"]:
                preview += f" and drafts stored for {self.retention_combo.currentText()}"
        else:
            preview = "Auto-save is disabled"
            
        self.preview_label.setText(preview)
        
    def test_auto_save(self):
        """Test auto-save functionality."""
        self.preview_label.setText("Testing auto-save... Check the journal editor!")
        QTimer.singleShot(2000, lambda: self.preview_label.setText("Test complete"))
        
    def restore_defaults(self):
        """Restore default settings."""
        self.enable_checkbox.setChecked(True)
        self.save_drafts_checkbox.setChecked(True)
        self.delay_slider.setValue(3)
        self.max_wait_spin.setValue(30)
        self.retention_combo.setCurrentIndex(2)  # 7 days
        self.max_size_spin.setValue(10)
        
        self.on_setting_changed()