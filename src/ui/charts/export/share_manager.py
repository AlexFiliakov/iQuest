"""Visualization share manager for creating shareable links."""

import uuid
import json
import base64
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import secrets
import logging

from .export_models import ShareableLink, ExportResult
from ..wsj_style_manager import WSJStyleManager

logger = logging.getLogger(__name__)


class VisualizationShareManager:
    """Manages sharing of visualizations with secure links."""
    
    def __init__(self, base_url: str = "https://health-dashboard.example.com/share/"):
        """Initialize share manager."""
        self.base_url = base_url
        self.share_cache = {}  # In production, use database
        self.style_manager = WSJStyleManager()
        
    def create_shareable_link(self, visualization: Any,
                            expiry_days: int = 30,
                            password: Optional[str] = None,
                            access_mode: str = "view_only") -> ShareableLink:
        """Create shareable link for visualization."""
        try:
            # Generate unique share ID
            share_id = self._generate_share_id()
            
            # Serialize visualization state
            viz_data = self._serialize_visualization(visualization)
            
            # Create share metadata
            share_metadata = {
                'id': share_id,
                'created': datetime.now().isoformat(),
                'expires': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
                'access_mode': access_mode,
                'password_protected': password is not None,
                'password_hash': self._hash_password(password) if password else None,
                'view_count': 0,
                'last_accessed': None,
                'visualization': viz_data
            }
            
            # Store in cache (in production, persist to database)
            self.share_cache[share_id] = share_metadata
            
            # Generate URL
            share_url = f"{self.base_url}{share_id}"
            
            # Generate QR code
            qr_code_data = self._generate_qr_code(share_url)
            
            # Create shareable link object
            return ShareableLink(
                url=share_url,
                share_id=share_id,
                expires_at=datetime.now() + timedelta(days=expiry_days),
                qr_code=qr_code_data,
                access_mode=access_mode,
                password_protected=password is not None
            )
            
        except Exception as e:
            logger.error(f"Failed to create shareable link: {str(e)}")
            raise
            
    def get_shared_visualization(self, share_id: str, 
                               password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve shared visualization by ID."""
        # Get from cache (in production, from database)
        share_data = self.share_cache.get(share_id)
        
        if not share_data:
            return None
            
        # Check expiration
        expires = datetime.fromisoformat(share_data['expires'])
        if datetime.now() > expires:
            # Remove expired share
            del self.share_cache[share_id]
            return None
            
        # Check password if protected
        if share_data['password_protected']:
            if not password or not self._verify_password(password, share_data['password_hash']):
                return None
                
        # Update access metadata
        share_data['view_count'] += 1
        share_data['last_accessed'] = datetime.now().isoformat()
        
        return share_data['visualization']
        
    def revoke_share(self, share_id: str) -> bool:
        """Revoke a shared link."""
        if share_id in self.share_cache:
            del self.share_cache[share_id]
            return True
        return False
        
    def extend_share_expiry(self, share_id: str, additional_days: int) -> bool:
        """Extend expiry date of shared link."""
        if share_id in self.share_cache:
            current_expires = datetime.fromisoformat(self.share_cache[share_id]['expires'])
            new_expires = current_expires + timedelta(days=additional_days)
            self.share_cache[share_id]['expires'] = new_expires.isoformat()
            return True
        return False
        
    def get_share_analytics(self, share_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for shared link."""
        share_data = self.share_cache.get(share_id)
        
        if not share_data:
            return None
            
        return {
            'view_count': share_data['view_count'],
            'created': share_data['created'],
            'last_accessed': share_data['last_accessed'],
            'expires': share_data['expires'],
            'days_until_expiry': (datetime.fromisoformat(share_data['expires']) - 
                                datetime.now()).days
        }
        
    def create_embed_code(self, visualization: Any, 
                         width: int = 800, 
                         height: int = 600) -> str:
        """Generate embed code for visualization."""
        # Create shareable link
        share_link = self.create_shareable_link(visualization, expiry_days=90)
        
        # Generate iframe embed code
        embed_code = f"""<iframe 
    src="{share_link.url}?embed=true" 
    width="{width}" 
    height="{height}"
    frameborder="0"
    style="border: 1px solid #E8DCC8; border-radius: 4px;"
    title="Health Dashboard Visualization">
</iframe>"""
        
        return embed_code
        
    def export_for_social_media(self, visualization: Any, 
                              platform: str = "generic") -> Dict[str, Any]:
        """Export visualization optimized for social media sharing."""
        # Platform-specific dimensions
        dimensions = {
            'twitter': (1200, 675),  # 16:9 ratio
            'facebook': (1200, 630),  # 1.91:1 ratio
            'instagram': (1080, 1080),  # 1:1 ratio
            'linkedin': (1200, 627),  # 1.91:1 ratio
            'generic': (1200, 675)
        }
        
        width, height = dimensions.get(platform, dimensions['generic'])
        
        # Generate optimized image
        from .image_exporter import HighResImageExporter, ImageExportOptions
        
        exporter = HighResImageExporter(self.style_manager)
        options = ImageExportOptions(
            width=width,
            height=height,
            dpi=150,  # Lower DPI for web
            include_watermark=True
        )
        
        result = exporter.export_chart(visualization, 'png', options)
        
        if result.success:
            # Create sharing metadata
            return {
                'image_data': result.metadata.get('image_data'),
                'dimensions': (width, height),
                'platform': platform,
                'title': getattr(visualization, 'title', 'Health Visualization'),
                'description': getattr(visualization, 'description', 
                                     'Insights from your health data'),
                'hashtags': ['#HealthData', '#DataVisualization', '#Wellness']
            }
        else:
            raise Exception(f"Failed to export for social media: {result.error_message}")
            
    def _serialize_visualization(self, visualization: Any) -> Dict[str, Any]:
        """Serialize visualization state for sharing."""
        viz_data = {
            'type': visualization.__class__.__name__,
            'title': getattr(visualization, 'title', 'Health Visualization'),
            'description': getattr(visualization, 'description', ''),
            'theme': 'wsj',
            'created': datetime.now().isoformat()
        }
        
        # Get chart configuration
        if hasattr(visualization, 'get_config'):
            viz_data['config'] = visualization.get_config()
            
        # Get data (limited for security)
        if hasattr(visualization, 'get_shareable_data'):
            viz_data['data'] = visualization.get_shareable_data()
        elif hasattr(visualization, 'get_data'):
            # Limit data size for sharing
            data = visualization.get_data()
            if hasattr(data, 'to_dict'):
                data_dict = data.head(1000).to_dict('records')  # Limit to 1000 rows
                viz_data['data'] = data_dict
                
        # Get current view state
        if hasattr(visualization, 'get_view_state'):
            viz_data['view_state'] = visualization.get_view_state()
            
        return viz_data
        
    def _generate_share_id(self) -> str:
        """Generate unique share ID."""
        # Use UUID4 for randomness
        return str(uuid.uuid4()).replace('-', '')[:16]
        
    def _generate_qr_code(self, url: str) -> str:
        """Generate QR code for URL."""
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create image with WSJ colors
            img = qr.make_image(
                fill_color=self.style_manager.WARM_PALETTE['text_primary'],
                back_color=self.style_manager.WARM_PALETTE['surface']
            )
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {str(e)}")
            return ""
            
    def _hash_password(self, password: str) -> str:
        """Hash password for storage."""
        if not password:
            return ""
            
        # Use secure salt
        salt = secrets.token_bytes(32)
        
        # Hash with PBKDF2
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
        
        # Return salt + hash
        return base64.b64encode(salt + key).decode()
        
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        if not password or not password_hash:
            return False
            
        try:
            # Decode hash
            decoded = base64.b64decode(password_hash.encode())
            salt = decoded[:32]
            stored_key = decoded[32:]
            
            # Hash provided password with same salt
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            # Compare hashes
            return new_key == stored_key
            
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
            
    def cleanup_expired_shares(self) -> int:
        """Remove expired shares from cache."""
        expired_ids = []
        now = datetime.now()
        
        for share_id, share_data in self.share_cache.items():
            expires = datetime.fromisoformat(share_data['expires'])
            if now > expires:
                expired_ids.append(share_id)
                
        # Remove expired shares
        for share_id in expired_ids:
            del self.share_cache[share_id]
            
        return len(expired_ids)