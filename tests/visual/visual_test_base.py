"""
Base class for visual regression tests.
Provides common functionality for widget capture and comparison.
"""

import pytest
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QWidget, QApplication
from PIL import Image
import io
import os
from pathlib import Path

from .qt_config import VisualTestConfig
from .image_comparison import ImageComparator
from .baseline_manager import BaselineManager


class VisualTestBase:
    """Base class for visual regression tests."""
    
    @pytest.fixture(autouse=True)
    def setup_visual_test(self, qtbot):
        """Set up visual test environment."""
        self.app = VisualTestConfig.setup_qt_for_testing()
        self.qtbot = qtbot
        self.comparator = ImageComparator(threshold=0.95)
        self.baseline_manager = BaselineManager()
        
        # Check for baseline update mode
        self.update_baselines = os.environ.get('UPDATE_BASELINES', 'false').lower() == 'true'
    
    def capture_widget(
        self, 
        widget: QWidget,
        wait_ms: int = 100
    ) -> Image.Image:
        """Capture widget as image."""
        # Ensure widget is shown and stable
        widget.show()
        
        # Wait for widget to be exposed
        if hasattr(self.qtbot, 'waitExposed'):
            self.qtbot.waitExposed(widget, timeout=5000)
        else:
            # Fallback for older pytest-qt versions
            self.qtbot.wait(1000)
        
        # Additional wait for rendering to stabilize
        QTimer.singleShot(wait_ms, lambda: None)
        self.qtbot.wait(wait_ms)
        
        # Force a repaint
        widget.repaint()
        
        # Capture to pixmap
        pixmap = QPixmap(widget.size())
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        try:
            widget.render(painter)
        finally:
            painter.end()
        
        # Convert to PIL Image
        # PyQt6 requires QBuffer for in-memory operations
        from PyQt6.QtCore import QBuffer, QIODevice
        
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, 'PNG')
        buffer.close()
        
        # Get the data and convert to PIL Image
        image_data = buffer.data().data()
        return Image.open(io.BytesIO(image_data))
    
    def assert_visual_match(
        self, 
        widget: QWidget,
        test_name: str,
        threshold: float = 0.95,
        comparison_method: str = 'ssim',
        update_baseline: bool = None
    ):
        """Assert widget matches baseline."""
        # Use instance setting if update_baseline not specified
        if update_baseline is None:
            update_baseline = self.update_baselines
        
        # Capture current state
        actual = self.capture_widget(widget)
        
        # Get baseline path
        baseline_path = self.baseline_manager.get_baseline_path(test_name)
        
        if update_baseline or not baseline_path.exists():
            # Save new baseline
            self.baseline_manager.save_baseline(test_name, actual)
            pytest.skip(f"Baseline {'updated' if baseline_path.exists() else 'created'} for {test_name}")
        
        # Load and compare
        try:
            expected = Image.open(baseline_path)
        except Exception as e:
            pytest.fail(f"Failed to load baseline for {test_name}: {e}")
        
        # Set comparison threshold
        self.comparator.threshold = threshold
        result = self.comparator.compare(actual, expected, method=comparison_method)
        
        if not result['match']:
            # Save artifacts for debugging
            self._save_failure_artifacts(
                test_name, 
                actual, 
                expected, 
                result
            )
            
            # Provide detailed failure message
            failure_msg = (
                f"Visual mismatch for {test_name}:\\n"
                f"  Score: {result['score']:.3f} (threshold: {threshold})\\n"
                f"  Method: {comparison_method}\\n"
                f"  Platform: {self.baseline_manager.platform}"
            )
            
            if 'reason' in result:
                failure_msg += f"\\n  Reason: {result['reason']}"
            
            pytest.fail(failure_msg)
    
    def _save_failure_artifacts(
        self, 
        test_name: str,
        actual: Image.Image,
        expected: Image.Image,
        result: dict
    ):
        """Save debugging artifacts for failed tests."""
        failures_dir = Path('tests/visual/failures')
        failures_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean test name for filename
        clean_name = self.baseline_manager._clean_filename(test_name)
        timestamp = self._get_timestamp()
        
        # Save actual image
        actual_path = failures_dir / f"{clean_name}_actual_{timestamp}.png"
        actual.save(actual_path)
        
        # Save expected image
        expected_path = failures_dir / f"{clean_name}_expected_{timestamp}.png"
        expected.save(expected_path)
        
        # Save diff image if available
        if result.get('diff_image'):
            diff_path = failures_dir / f"{clean_name}_diff_{timestamp}.png"
            result['diff_image'].save(diff_path)
        
        # Save comparison info
        info_path = failures_dir / f"{clean_name}_info_{timestamp}.txt"
        with open(info_path, 'w') as f:
            f.write(f"Visual Test Failure Report\\n")
            f.write(f"========================\\n")
            f.write(f"Test: {test_name}\\n")
            f.write(f"Platform: {self.baseline_manager.platform}\\n")
            f.write(f"Score: {result['score']:.3f}\\n")
            f.write(f"Threshold: {result['threshold']}\\n")
            f.write(f"Method: {result['method']}\\n")
            f.write(f"Baseline: {self.baseline_manager.get_baseline_path(test_name)}\\n")
            f.write(f"\\nPlatform Info:\\n")
            platform_info = self.baseline_manager.get_platform_info()
            for key, value in platform_info.items():
                f.write(f"  {key}: {value}\\n")
    
    def _get_timestamp(self) -> str:
        """Get timestamp for failure artifacts."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_baseline(self, widget: QWidget, test_name: str):
        """Explicitly create a baseline for a test."""
        actual = self.capture_widget(widget)
        self.baseline_manager.save_baseline(test_name, actual)
    
    def get_baseline_info(self, test_name: str) -> dict:
        """Get information about a baseline."""
        baseline_path = self.baseline_manager.get_baseline_path(test_name)
        return {
            'exists': baseline_path.exists(),
            'path': baseline_path,
            'platform': self.baseline_manager.platform,
            'is_platform_specific': baseline_path.parent.name == self.baseline_manager.platform
        }