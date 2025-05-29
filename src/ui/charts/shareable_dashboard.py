"""Shareable dashboard functionality for health visualizations."""

import json
import base64
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path
import uuid

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QLineEdit, QTextEdit, QDialog, QMessageBox,
                            QGroupBox, QCheckBox, QDateEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QDate, QTimer
from PyQt6.QtGui import QGuiApplication

from .wsj_style_manager import WSJStyleManager
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class DashboardShareConfig:
    """Configuration for shareable dashboard."""
    
    def __init__(self):
        self.share_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.title = "Health Dashboard"
        self.description = ""
        self.view_config = {}
        self.permissions = {
            'allow_drill_down': True,
            'allow_export': False,
            'allow_date_change': True,
            'show_personal_info': False
        }
        self.expiration_date = None
        self.password_protected = False
        self.password_hash = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'share_id': self.share_id,
            'created_at': self.created_at.isoformat(),
            'title': self.title,
            'description': self.description,
            'view_config': self.view_config,
            'permissions': self.permissions,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'password_protected': self.password_protected,
            'password_hash': self.password_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardShareConfig':
        """Create from dictionary."""
        config = cls()
        config.share_id = data.get('share_id', str(uuid.uuid4()))
        config.created_at = datetime.fromisoformat(data['created_at'])
        config.title = data.get('title', 'Health Dashboard')
        config.description = data.get('description', '')
        config.view_config = data.get('view_config', {})
        config.permissions = data.get('permissions', config.permissions)
        if data.get('expiration_date'):
            config.expiration_date = datetime.fromisoformat(data['expiration_date'])
        config.password_protected = data.get('password_protected', False)
        config.password_hash = data.get('password_hash')
        return config


class ShareableDashboardManager:
    """Manages creation and access of shareable dashboards."""
    
    def __init__(self, style_manager: WSJStyleManager):
        self.style_manager = style_manager
        self.shares_dir = Path.home() / '.health_dashboard' / 'shares'
        self.shares_dir.mkdir(parents=True, exist_ok=True)
        
        # In production, this would use a proper database
        self.active_shares = self._load_active_shares()
    
    def _load_active_shares(self) -> Dict[str, DashboardShareConfig]:
        """Load active dashboard shares."""
        shares = {}
        
        # Load from files (in production, use database)
        for share_file in self.shares_dir.glob('*.json'):
            try:
                with open(share_file, 'r') as f:
                    data = json.load(f)
                    config = DashboardShareConfig.from_dict(data)
                    
                    # Check if expired
                    if config.expiration_date and config.expiration_date < datetime.now():
                        share_file.unlink()  # Delete expired share
                        continue
                    
                    shares[config.share_id] = config
            except Exception as e:
                logger.error(f"Error loading share {share_file}: {e}")
        
        return shares
    
    def create_share(self, view_config: Dict[str, Any], 
                    share_config: DashboardShareConfig) -> str:
        """Create a shareable dashboard link."""
        # Save configuration
        share_config.view_config = view_config
        self.active_shares[share_config.share_id] = share_config
        
        # Persist to file (in production, use database)
        share_file = self.shares_dir / f"{share_config.share_id}.json"
        with open(share_file, 'w') as f:
            json.dump(share_config.to_dict(), f, indent=2)
        
        # Generate shareable link
        # In production, this would be a proper URL
        share_data = {
            'id': share_config.share_id,
            'v': 1  # Version for future compatibility
        }
        
        # Encode as base64 for URL
        encoded = base64.urlsafe_b64encode(
            json.dumps(share_data).encode()
        ).decode().rstrip('=')
        
        # Create link (in production, use actual domain)
        link = f"healthdashboard://share/{encoded}"
        
        return link
    
    def get_share(self, share_id: str) -> Optional[DashboardShareConfig]:
        """Retrieve a share configuration."""
        return self.active_shares.get(share_id)
    
    def delete_share(self, share_id: str):
        """Delete a share."""
        if share_id in self.active_shares:
            del self.active_shares[share_id]
            
            # Delete file
            share_file = self.shares_dir / f"{share_id}.json"
            if share_file.exists():
                share_file.unlink()
    
    def parse_share_link(self, link: str) -> Optional[str]:
        """Parse a share link and return share ID."""
        try:
            if link.startswith('healthdashboard://share/'):
                encoded = link.replace('healthdashboard://share/', '')
                # Add padding if needed
                padding = 4 - (len(encoded) % 4)
                if padding != 4:
                    encoded += '=' * padding
                
                decoded = base64.urlsafe_b64decode(encoded)
                data = json.loads(decoded)
                return data.get('id')
        except Exception as e:
            logger.error(f"Error parsing share link: {e}")
        
        return None


class ShareDashboardDialog(QDialog):
    """Dialog for creating shareable dashboard."""
    
    def __init__(self, current_view: Dict[str, Any], 
                 style_manager: WSJStyleManager, parent=None):
        super().__init__(parent)
        self.current_view = current_view
        self.style_manager = style_manager
        self.share_config = DashboardShareConfig()
        
        self.setWindowTitle("Share Dashboard")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title and description
        info_group = QGroupBox("Dashboard Information")
        info_layout = QVBoxLayout(info_group)
        
        info_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(self.share_config.title)
        info_layout.addWidget(self.title_edit)
        
        info_layout.addWidget(QLabel("Description:"))
        self.desc_edit = QTextEdit(self)
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlainText(self.share_config.description)
        info_layout.addWidget(self.desc_edit)
        
        layout.addWidget(info_group)
        
        # Permissions
        perm_group = QGroupBox("Permissions")
        perm_layout = QVBoxLayout(perm_group)
        
        self.allow_drill_down = QCheckBox("Allow drill-down navigation")
        self.allow_drill_down.setChecked(True)
        perm_layout.addWidget(self.allow_drill_down)
        
        self.allow_export = QCheckBox("Allow data export")
        self.allow_export.setChecked(False)
        perm_layout.addWidget(self.allow_export)
        
        self.allow_date_change = QCheckBox("Allow date range changes")
        self.allow_date_change.setChecked(True)
        perm_layout.addWidget(self.allow_date_change)
        
        self.show_personal = QCheckBox("Show personal information")
        self.show_personal.setChecked(False)
        perm_layout.addWidget(self.show_personal)
        
        layout.addWidget(perm_group)
        
        # Security
        security_group = QGroupBox("Security")
        security_layout = QVBoxLayout(security_group)
        
        # Expiration
        exp_layout = QHBoxLayout()
        self.use_expiration = QCheckBox("Set expiration date:")
        exp_layout.addWidget(self.use_expiration)
        
        self.expiration_date = QDateEdit(self)
        self.expiration_date.setCalendarPopup(True)
        self.expiration_date.setDate(QDate.currentDate().addDays(30))
        self.expiration_date.setEnabled(False)
        self.use_expiration.toggled.connect(self.expiration_date.setEnabled)
        exp_layout.addWidget(self.expiration_date)
        exp_layout.addStretch()
        
        security_layout.addLayout(exp_layout)
        
        # Password protection
        self.use_password = QCheckBox("Password protect")
        security_layout.addWidget(self.use_password)
        
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password")
        self.password_edit.setEnabled(False)
        self.use_password.toggled.connect(self.password_edit.setEnabled)
        security_layout.addWidget(self.password_edit)
        
        layout.addWidget(security_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Share Link")
        self.create_btn.clicked.connect(self.create_share)
        self.create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.WARM_PALETTE['primary']};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #E67A35;
            }}
        """)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        # Apply overall styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.style_manager.WARM_PALETTE['surface']};
            }}
            QGroupBox {{
                font-weight: 600;
                border: 1px solid {self.style_manager.WARM_PALETTE['grid']};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
    
    def create_share(self):
        """Create the share configuration."""
        # Update config from UI
        self.share_config.title = self.title_edit.text()
        self.share_config.description = self.desc_edit.toPlainText()
        
        # Permissions
        self.share_config.permissions = {
            'allow_drill_down': self.allow_drill_down.isChecked(),
            'allow_export': self.allow_export.isChecked(),
            'allow_date_change': self.allow_date_change.isChecked(),
            'show_personal_info': self.show_personal.isChecked()
        }
        
        # Security
        if self.use_expiration.isChecked():
            self.share_config.expiration_date = datetime.combine(
                self.expiration_date.date().toPyDate(),
                datetime.min.time()
            )
        
        if self.use_password.isChecked():
            password = self.password_edit.text()
            if not password:
                QMessageBox.warning(self, "Password Required", 
                                  "Please enter a password or disable password protection.")
                return
            
            # Hash password (in production, use proper hashing like bcrypt)
            self.share_config.password_protected = True
            self.share_config.password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.accept()
    
    def get_share_config(self) -> DashboardShareConfig:
        """Get the configured share settings."""
        return self.share_config


class ShareLinkDisplay(QDialog):
    """Dialog to display generated share link."""
    
    def __init__(self, share_link: str, style_manager: WSJStyleManager, parent=None):
        super().__init__(parent)
        self.share_link = share_link
        self.style_manager = style_manager
        
        self.setWindowTitle("Share Link Created")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Success message
        success_label = QLabel("✅ Your shareable dashboard link has been created!")
        success_label.setStyleSheet(f"""
            color: {self.style_manager.WARM_PALETTE['positive']};
            font-size: 16px;
            font-weight: 600;
            padding: 10px;
        """)
        layout.addWidget(success_label)
        
        # Link display
        link_group = QGroupBox("Share Link")
        link_layout = QVBoxLayout(link_group)
        
        self.link_edit = QLineEdit(self.share_link)
        self.link_edit.setReadOnly(True)
        self.link_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                font-family: monospace;
                background-color: {self.style_manager.WARM_PALETTE['background']};
                border: 1px solid {self.style_manager.WARM_PALETTE['grid']};
                border-radius: 4px;
            }}
        """)
        link_layout.addWidget(self.link_edit)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_link)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.style_manager.WARM_PALETTE['secondary']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {self.style_manager.WARM_PALETTE['primary']};
                color: white;
            }}
        """)
        link_layout.addWidget(copy_btn)
        
        layout.addWidget(link_group)
        
        # Instructions
        instructions = QLabel(
            "Share this link with others to give them access to this dashboard view. "
            "The link will respect the permissions and security settings you configured."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {self.style_manager.WARM_PALETTE['text_secondary']};")
        layout.addWidget(instructions)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def copy_link(self):
        """Copy link to clipboard."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.share_link)
        
        # Show feedback
        self.link_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                font-family: monospace;
                background-color: {self.style_manager.WARM_PALETTE['positive']};
                color: white;
                border: 1px solid {self.style_manager.WARM_PALETTE['positive']};
                border-radius: 4px;
            }}
        """)
        
        # Reset after delay
        QTimer.singleShot(1000, lambda: self.link_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                font-family: monospace;
                background-color: {self.style_manager.WARM_PALETTE['background']};
                border: 1px solid {self.style_manager.WARM_PALETTE['grid']};
                border-radius: 4px;
            }}
        """))


class SharedDashboardViewer(QWidget):
    """Widget for viewing shared dashboards with restricted permissions."""
    
    def __init__(self, share_config: DashboardShareConfig, 
                 visualization_suite, style_manager: WSJStyleManager,
                 parent=None):
        super().__init__(parent)
        self.share_config = share_config
        self.visualization_suite = visualization_suite
        self.style_manager = style_manager
        
        self._setup_ui()
        self._apply_permissions()
    
    def _setup_ui(self):
        """Set up the viewer UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main visualization
        self.viz_container = QWidget(self)
        viz_layout = QVBoxLayout(self.viz_container)
        viz_layout.addWidget(self.visualization_suite)
        layout.addWidget(self.viz_container, 1)
        
        # Restore view configuration
        if self.share_config.view_config:
            self.visualization_suite.restore_view_config(self.share_config.view_config)
    
    def _create_header(self) -> QWidget:
        """Create header with share info."""
        header = QWidget(self)
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 20, 20, 10)
        
        # Title
        title = QLabel(self.share_config.title)
        title.setStyleSheet(f"""
            font-size: {self.style_manager.TYPOGRAPHY['title']['size']}px;
            font-weight: {self.style_manager.TYPOGRAPHY['title']['weight']};
            color: {self.style_manager.TYPOGRAPHY['title']['color']};
        """)
        layout.addWidget(title)
        
        # Description
        if self.share_config.description:
            desc = QLabel(self.share_config.description)
            desc.setWordWrap(True)
            desc.setStyleSheet(f"""
                color: {self.style_manager.TYPOGRAPHY['subtitle']['color']};
                margin-top: 5px;
            """)
            layout.addWidget(desc)
        
        # Share info
        info_text = f"Shared on {self.share_config.created_at.strftime('%B %d, %Y')}"
        if self.share_config.expiration_date:
            info_text += f" • Expires {self.share_config.expiration_date.strftime('%B %d, %Y')}"
        
        info = QLabel(info_text)
        info.setStyleSheet(f"""
            color: {self.style_manager.WARM_PALETTE['text_muted']};
            font-size: 12px;
            margin-top: 10px;
        """)
        layout.addWidget(info)
        
        return header
    
    def _apply_permissions(self):
        """Apply permission restrictions."""
        perms = self.share_config.permissions
        
        # Disable features based on permissions
        if not perms.get('allow_drill_down', True):
            # Disable drill-down in visualization suite
            if hasattr(self.visualization_suite, 'set_drill_down_enabled'):
                self.visualization_suite.set_drill_down_enabled(False)
        
        if not perms.get('allow_export', False):
            # Hide export button
            if hasattr(self.visualization_suite, 'export_btn'):
                self.visualization_suite.export_btn.setVisible(False)
        
        if not perms.get('allow_date_change', True):
            # Disable date selection
            if hasattr(self.visualization_suite, 'set_date_selection_enabled'):
                self.visualization_suite.set_date_selection_enabled(False)
        
        if not perms.get('show_personal_info', False):
            # Apply anonymization
            if hasattr(self.visualization_suite, 'set_anonymized_mode'):
                self.visualization_suite.set_anonymized_mode(True)