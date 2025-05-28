# G072: Repair Visual Regression Testing Framework

## Status: ACTIVE
Priority: MEDIUM
Type: BUG_FIX
Parallel: Yes (independent of other test fixes)

## Problem Summary
Visual regression tests failing (19 failures in `test_visual_regression.py`):
- Missing baseline images
- Qt rendering differences across platforms
- Screenshot comparison tolerance issues
- Missing visual testing dependencies

## Root Cause Analysis
1. Baseline images not committed or outdated
2. Platform-specific rendering differences
3. Incorrect image comparison thresholds
4. Qt backend configuration issues

## Implementation Options Analysis

### Option A: Pixel-Perfect Comparison
**Pros:**
- Catches any visual change
- Simple to implement
- No false negatives

**Cons:**
- Platform differences cause failures
- Font rendering varies
- Anti-aliasing differences
- High maintenance burden

### Option B: Perceptual Comparison (Recommended)
**Pros:**
- Tolerates minor rendering differences
- Cross-platform compatible
- Focuses on significant changes
- Industry best practice

**Cons:**
- May miss subtle issues
- Requires tuning thresholds
- More complex algorithms

### Option C: Structural Comparison
**Pros:**
- Platform independent
- Tests layout/structure
- No image storage needed

**Cons:**
- Misses styling issues
- Can't catch visual bugs
- Limited coverage

## Detailed Implementation Plan

### Phase 1: Visual Testing Infrastructure
1. **Install and configure dependencies**
   ```ini
   # requirements-test.txt additions
   pytest-qt>=4.2.0
   pillow>=9.3.0
   scikit-image>=0.19.0
   imagehash>=4.3.0
   opencv-python>=4.6.0
   playwright>=1.30.0  # For browser testing
   ```

2. **Configure Qt for headless testing**
   ```python
   # tests/visual/qt_config.py
   import os
   import sys
   from PyQt6.QtCore import QCoreApplication
   from PyQt6.QtGui import QGuiApplication, QFontDatabase
   from PyQt6.QtWidgets import QApplication
   
   class VisualTestConfig:
       """Configure Qt for consistent visual testing."""
       
       @staticmethod
       def setup_qt_for_testing():
           """Configure Qt for reproducible rendering."""
           # Force software rendering for consistency
           os.environ['QT_QUICK_BACKEND'] = 'software'
           os.environ['QSG_RHI_BACKEND'] = 'software'
           
           # Disable animations
           os.environ['QT_SCALE_FACTOR'] = '1'
           os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
           
           # Set consistent DPI
           os.environ['QT_FONT_DPI'] = '96'
           
           # Create application if needed
           app = QApplication.instance()
           if app is None:
               app = QApplication(sys.argv)
           
           # Configure application
           app.setStyle('Fusion')  # Consistent style
           app.setApplicationName('HealthMonitorTest')
           
           # Load consistent fonts
           VisualTestConfig._load_test_fonts()
           
           return app
       
       @staticmethod
       def _load_test_fonts():
           """Load consistent fonts for testing."""
           # Use embedded fonts for consistency
           font_paths = [
               'tests/visual/fonts/Roboto-Regular.ttf',
               'tests/visual/fonts/Roboto-Bold.ttf'
           ]
           
           for font_path in font_paths:
               if os.path.exists(font_path):
                   QFontDatabase.addApplicationFont(font_path)
   ```

### Phase 2: Smart Image Comparison
1. **Perceptual comparison utilities**
   ```python
   # tests/visual/image_comparison.py
   import numpy as np
   from PIL import Image, ImageChops, ImageDraw
   from skimage.metrics import structural_similarity as ssim
   import imagehash
   import cv2
   from typing import Tuple, Optional, Dict
   
   class ImageComparator:
       """Smart image comparison for visual regression tests."""
       
       def __init__(self, threshold: float = 0.95):
           self.threshold = threshold
           self.comparison_methods = {
               'ssim': self._compare_ssim,
               'phash': self._compare_phash,
               'histogram': self._compare_histogram,
               'mse': self._compare_mse
           }
       
       def compare(
           self, 
           actual: Image.Image, 
           expected: Image.Image,
           method: str = 'ssim'
       ) -> Dict[str, any]:
           """Compare images using specified method."""
           # Ensure same size
           if actual.size != expected.size:
               return {
                   'match': False,
                   'score': 0.0,
                   'reason': f'Size mismatch: {actual.size} vs {expected.size}'
               }
           
           # Run comparison
           comparison_func = self.comparison_methods.get(method)
           if not comparison_func:
               raise ValueError(f"Unknown method: {method}")
           
           score, diff_image = comparison_func(actual, expected)
           
           return {
               'match': score >= self.threshold,
               'score': score,
               'method': method,
               'diff_image': diff_image,
               'threshold': self.threshold
           }
       
       def _compare_ssim(
           self, 
           actual: Image.Image, 
           expected: Image.Image
       ) -> Tuple[float, Optional[Image.Image]]:
           """Structural similarity comparison."""
           # Convert to grayscale numpy arrays
           actual_gray = np.array(actual.convert('L'))
           expected_gray = np.array(expected.convert('L'))
           
           # Calculate SSIM
           score, diff = ssim(
               actual_gray, 
               expected_gray, 
               full=True,
               gaussian_weights=True,
               sigma=1.5,
               use_sample_covariance=False
           )
           
           # Create diff image
           diff_image = self._create_diff_image(actual, expected, diff)
           
           return score, diff_image
       
       def _create_diff_image(
           self, 
           actual: Image.Image, 
           expected: Image.Image,
           diff_map: np.ndarray
       ) -> Image.Image:
           """Create visual diff highlighting changes."""
           # Create base diff
           diff = ImageChops.difference(actual, expected)
           
           # Enhance differences
           diff_enhanced = Image.new('RGB', actual.size)
           diff_draw = ImageDraw.Draw(diff_enhanced)
           
           # Overlay diff map
           diff_normalized = (1 - diff_map) * 255
           diff_mask = Image.fromarray(diff_normalized.astype(np.uint8))
           
           # Composite with color coding
           # Red = removed, Green = added, Yellow = changed
           diff_colored = Image.merge('RGB', [
               diff_mask,  # Red channel
               Image.new('L', actual.size, 0),  # Green channel  
               Image.new('L', actual.size, 0)   # Blue channel
           ])
           
           return Image.blend(actual, diff_colored, 0.5)
   ```

2. **Platform-specific baseline management**
   ```python
   # tests/visual/baseline_manager.py
   import platform
   from pathlib import Path
   from typing import Optional
   
   class BaselineManager:
       """Manage platform-specific baseline images."""
       
       def __init__(self, base_path: str = "tests/visual/baselines"):
           self.base_path = Path(base_path)
           self.platform = self._get_platform_key()
       
       def _get_platform_key(self) -> str:
           """Get platform-specific key."""
           system = platform.system().lower()
           version = platform.release()
           
           # Normalize platform names
           if system == 'darwin':
               system = 'macos'
           elif system == 'windows':
               # Group Windows versions
               if '10' in version or '11' in version:
                   version = 'modern'
               else:
                   version = 'legacy'
           
           return f"{system}_{version}"
       
       def get_baseline_path(self, test_name: str) -> Path:
           """Get path to baseline image."""
           # Try platform-specific first
           platform_path = self.base_path / self.platform / f"{test_name}.png"
           if platform_path.exists():
               return platform_path
           
           # Fall back to generic
           generic_path = self.base_path / 'generic' / f"{test_name}.png"
           if generic_path.exists():
               return generic_path
           
           # No baseline found
           return platform_path  # Return expected path
       
       def save_baseline(
           self, 
           test_name: str, 
           image: Image.Image,
           platform_specific: bool = True
       ):
           """Save baseline image."""
           if platform_specific:
               path = self.base_path / self.platform / f"{test_name}.png"
           else:
               path = self.base_path / 'generic' / f"{test_name}.png"
           
           path.parent.mkdir(parents=True, exist_ok=True)
           image.save(path, 'PNG', optimize=True)
   ```

### Phase 3: Visual Test Implementation
1. **Base visual test class**
   ```python
   # tests/visual/visual_test_base.py
   import pytest
   from PyQt6.QtCore import QTimer, Qt
   from PyQt6.QtGui import QPixmap, QPainter
   from PyQt6.QtWidgets import QWidget
   from PIL import Image
   import io
   
   class VisualTestBase:
       """Base class for visual regression tests."""
       
       @pytest.fixture(autouse=True)
       def setup_visual_test(self, qtbot):
           """Set up visual test environment."""
           from tests.visual.qt_config import VisualTestConfig
           self.app = VisualTestConfig.setup_qt_for_testing()
           self.qtbot = qtbot
           self.comparator = ImageComparator()
           self.baseline_manager = BaselineManager()
       
       def capture_widget(
           self, 
           widget: QWidget,
           wait_ms: int = 100
       ) -> Image.Image:
           """Capture widget as image."""
           # Ensure widget is shown and stable
           widget.show()
           self.qtbot.waitExposed(widget, timeout=5000)
           QTimer.singleShot(wait_ms, lambda: None)
           self.qtbot.wait(wait_ms)
           
           # Capture to pixmap
           pixmap = QPixmap(widget.size())
           pixmap.fill(Qt.GlobalColor.white)
           
           painter = QPainter(pixmap)
           widget.render(painter)
           painter.end()
           
           # Convert to PIL Image
           buffer = io.BytesIO()
           pixmap.save(buffer, 'PNG')
           buffer.seek(0)
           
           return Image.open(buffer)
       
       def assert_visual_match(
           self, 
           widget: QWidget,
           test_name: str,
           threshold: float = 0.95,
           update_baseline: bool = False
       ):
           """Assert widget matches baseline."""
           # Capture current
           actual = self.capture_widget(widget)
           
           # Get baseline
           baseline_path = self.baseline_manager.get_baseline_path(test_name)
           
           if update_baseline or not baseline_path.exists():
               # Save new baseline
               self.baseline_manager.save_baseline(test_name, actual)
               pytest.skip(f"Baseline updated for {test_name}")
           
           # Load and compare
           expected = Image.open(baseline_path)
           result = self.comparator.compare(actual, expected)
           
           if not result['match']:
               # Save artifacts for debugging
               self._save_failure_artifacts(
                   test_name, 
                   actual, 
                   expected, 
                   result
               )
               
               pytest.fail(
                   f"Visual mismatch for {test_name}: "
                   f"score={result['score']:.3f} "
                   f"(threshold={threshold})"
               )
   ```

### Phase 4: Fix Specific Visual Tests
1. **Chart rendering tests**
   ```python
   # tests/visual/test_chart_rendering.py
   class TestChartRendering(VisualTestBase):
       
       def test_line_chart_rendering(self):
           """Test line chart visual appearance."""
           from src.ui.charts import LineChart
           
           # Create chart with test data
           chart = LineChart()
           chart.set_data(self.sample_time_series)
           chart.resize(800, 600)
           
           # Visual assertion
           self.assert_visual_match(
               chart, 
               'line_chart_basic',
               threshold=0.98  # High threshold for charts
           )
       
       def test_chart_theme_consistency(self):
           """Test chart theme changes."""
           from src.ui.charts import LineChart
           from src.ui.style_manager import StyleManager
           
           chart = LineChart()
           chart.set_data(self.sample_time_series)
           
           for theme in ['light', 'dark', 'warm']:
               StyleManager.set_theme(theme)
               chart.update_theme()
               
               self.assert_visual_match(
                   chart,
                   f'line_chart_{theme}_theme',
                   threshold=0.95
               )
   ```

### Phase 5: CI/CD Integration
1. **Visual test workflow**
   ```yaml
   # .github/workflows/visual-tests.yml
   name: Visual Regression Tests
   on:
     pull_request:
     push:
       branches: [main]
   
   jobs:
     visual-tests:
       runs-on: ${{ matrix.os }}
       strategy:
         matrix:
           os: [ubuntu-latest, windows-latest, macos-latest]
       
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up display (Linux)
           if: runner.os == 'Linux'
           run: |
             sudo apt-get update
             sudo apt-get install -y xvfb
             export DISPLAY=:99
             Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
         
         - name: Run visual tests
           run: |
             pytest tests/visual/ -v \
               --visual-baseline-dir=baselines/${{ runner.os }}
         
         - name: Upload diff artifacts
           if: failure()
           uses: actions/upload-artifact@v3
           with:
             name: visual-diffs-${{ runner.os }}
             path: tests/visual/failures/
   ```

### Phase 6: Baseline Management Tools
1. **Update baseline script**
   ```python
   # tools/update_visual_baselines.py
   """Script to update visual regression baselines."""
   import argparse
   import subprocess
   from pathlib import Path
   
   def update_baselines(tests: list = None, platform: str = None):
       """Update visual baselines."""
       cmd = [
           'pytest', 
           'tests/visual/',
           '--update-baselines'
       ]
       
       if tests:
           cmd.extend(['-k', ' or '.join(tests)])
       
       if platform:
           cmd.extend(['--platform', platform])
       
       print(f"Running: {' '.join(cmd)}")
       subprocess.run(cmd)
   
   if __name__ == '__main__':
       parser = argparse.ArgumentParser()
       parser.add_argument(
           '--tests', 
           nargs='+',
           help='Specific tests to update'
       )
       parser.add_argument(
           '--platform',
           help='Platform to update (default: current)'
       )
       
       args = parser.parse_args()
       update_baselines(args.tests, args.platform)
   ```

## Affected Files (Detailed)
- **Files to create:**
  - `tests/visual/qt_config.py`
  - `tests/visual/image_comparison.py`
  - `tests/visual/baseline_manager.py`
  - `tests/visual/visual_test_base.py`
  - `tools/update_visual_baselines.py`
  - `.github/workflows/visual-tests.yml`
  - `docs/visual_testing_guide.md`

- **Files to update:**
  - `requirements-test.txt`
  - `tests/visual/test_visual_regression.py`
  - All visual test files

- **Baseline structure:**
  ```
  tests/visual/baselines/
  ├── generic/          # Cross-platform baselines
  ├── windows_modern/   # Windows 10/11
  ├── macos_12/        # macOS Monterey+
  └── linux_ubuntu/    # Ubuntu Linux
  ```

## Risk Mitigation
1. **Platform differences**
   - Use perceptual comparison
   - Platform-specific baselines
   - Flexible thresholds

2. **Maintenance burden**
   - Easy baseline updates
   - Clear diff reports
   - Automated updates in CI

## Success Criteria
- [ ] All 19 visual tests passing
- [ ] Cross-platform compatibility achieved
- [ ] Baseline update process documented
- [ ] Visual diff reports generated on failure
- [ ] CI/CD integration working
- [ ] < 5% false positive rate
- [ ] Baseline storage optimized