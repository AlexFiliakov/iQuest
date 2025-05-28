---
task_id: G065
status: open
created: 2025-05-28
complexity: medium
sprint_ref: S05_M01_Visualization
dependencies: [G058]
parallel_group: quality
---

# Task G065: Accessibility Compliance System

## Description
Implement comprehensive accessibility features for health visualizations including WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast modes, and alternative data representations.

## Goals
- [ ] Achieve WCAG 2.1 AA compliance for all visualizations
- [ ] Implement screen reader support with meaningful descriptions
- [ ] Add keyboard navigation for all chart interactions
- [ ] Create high contrast and colorblind-friendly themes
- [ ] Build alternative data representation modes (sonification, haptics)
- [ ] Add accessibility testing and validation tools

## Acceptance Criteria
- [ ] All charts pass WCAG 2.1 AA automated testing
- [ ] Screen readers announce chart data and interactions clearly
- [ ] Complete keyboard navigation without mouse dependency
- [ ] High contrast mode maintains data readability
- [ ] Color schemes work for all types of color blindness
- [ ] Alternative representations convey the same information
- [ ] Accessibility features work across all supported browsers

## Technical Details

### Accessibility Architecture
```python
class VisualizationAccessibilityManager:
    """Comprehensive accessibility management for health visualizations"""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.screen_reader_manager = ScreenReaderManager()
        self.keyboard_navigation = KeyboardNavigationManager()
        self.color_accessibility = ColorAccessibilityManager()
        self.alternative_representations = AlternativeRepresentationManager()
        
    def make_chart_accessible(self, chart: VisualizationComponent) -> AccessibleChart:
        """Apply comprehensive accessibility features to chart"""
        pass
        
    def validate_accessibility(self, chart: VisualizationComponent) -> AccessibilityReport:
        """Validate chart accessibility compliance"""
        pass
```

### WCAG 2.1 Requirements
1. **Perceivable**: Alternative text, color contrast, resize support
2. **Operable**: Keyboard navigation, no seizure triggers, sufficient time
3. **Understandable**: Clear labels, consistent navigation, error identification
4. **Robust**: Compatible with assistive technologies

### Alternative Representations
- **Data Tables**: Structured data accessible to screen readers
- **Text Summaries**: Narrative descriptions of chart insights
- **Sonification**: Audio representation of data patterns
- **Tactile Feedback**: Haptic patterns for touch interfaces

### WSJ Accessibility Standards

Based on WSJ's commitment to accessibility:

1. **Visual Accessibility**
   - Minimum contrast ratio: 4.5:1 (text), 3:1 (graphics)
   - No information conveyed by color alone
   - Clear focus indicators
   - Readable at 200% zoom

2. **Navigation Standards**
   ```python
   KEYBOARD_SHORTCUTS = {
       # Navigation
       'Tab': 'Next element',
       'Shift+Tab': 'Previous element',
       'Enter/Space': 'Activate',
       'Escape': 'Exit/Cancel',
       
       # Chart specific
       'Arrow keys': 'Navigate data points',
       'Home': 'First data point',
       'End': 'Last data point',
       'Page Up/Down': 'Time period navigation',
       
       # Accessibility
       'A': 'Announce current value',
       'S': 'Toggle sonification',
       'T': 'Show data table',
       'H': 'Help/shortcuts'
   }
   ```

3. **Screen Reader Support**
   - Meaningful chart descriptions
   - Progressive disclosure of detail
   - Logical reading order
   - Context-aware announcements

### Implementation Approaches - Pros and Cons

#### Approach 1: ARIA-based Accessibility
**Pros:**
- Standard web approach
- Good screen reader support
- Well documented
- Works with existing tools

**Cons:**
- Complex for dynamic content
- Browser inconsistencies
- Limited for complex interactions

#### Approach 2: Native Qt Accessibility
**Pros:**
- Deep OS integration
- Consistent behavior
- Good performance
- Platform-specific features

**Cons:**
- Platform differences
- Less flexible
- Limited documentation

#### Approach 3: Custom Accessibility Layer
**Pros:**
- Full control
- Optimized for health data
- Innovative features
- Consistent experience

**Cons:**
- More development work
- Testing complexity
- Maintenance burden

## Dependencies
- G058: Visualization Component Architecture

## Parallel Work
- Can be developed in parallel with all other visualization tasks
- Integrates with all chart components

## Implementation Notes
```python
class WSJAccessibleVisualization:
    """WSJ-styled accessible visualization implementation."""
    
    def __init__(self, theme_manager: WSJThemeManager):
        self.theme_manager = theme_manager
        self.accessibility_validator = WCAGValidator()
        self.screen_reader_narrator = HealthDataNarrator()
        
    def create_accessible_health_chart(self, data: pd.DataFrame, 
                                      chart_config: ChartConfig) -> AccessibleHealthChart:
        """Create health chart with full accessibility compliance."""
        
        # Create base chart
        chart = HealthVisualizationComponent(data, chart_config)
        
        # Apply accessibility enhancements
        accessible_chart = self._enhance_chart_accessibility(chart)
        
        # Validate compliance
        compliance_report = self.accessibility_validator.validate(accessible_chart)
        
        if not compliance_report.is_compliant():
            raise AccessibilityComplianceError(
                f"Chart fails accessibility requirements: {compliance_report.failures}"
            )
            
        return accessible_chart
        
    def _enhance_chart_accessibility(self, chart: HealthVisualizationComponent) -> AccessibleHealthChart:
        """Apply comprehensive accessibility enhancements."""
        
        accessible_chart = AccessibleHealthChart(chart)
        
        # 1. Screen reader support
        self._add_screen_reader_support(accessible_chart)
        
        # 2. Keyboard navigation
        self._enable_keyboard_navigation(accessible_chart)
        
        # 3. Color accessibility
        self._ensure_color_accessibility(accessible_chart)
        
        # 4. Alternative representations
        self._add_alternative_representations(accessible_chart)
        
        # 5. ARIA attributes
        self._add_aria_attributes(accessible_chart)
        
        return accessible_chart
        
    def _add_screen_reader_support(self, chart: AccessibleHealthChart) -> None:
        """Add comprehensive screen reader support."""
        
        # Chart description
        chart_description = self.screen_reader_narrator.create_chart_description(
            chart_type=chart.chart_type,
            data_summary=chart.get_data_summary(),
            key_insights=chart.get_key_insights()
        )
        chart.set_description(chart_description)
        
        # Data table alternative
        data_table = self._create_accessible_data_table(chart)
        chart.set_data_table_alternative(data_table)
        
        # Live region for dynamic updates
        if chart.supports_real_time_updates():
            chart.enable_live_region(politeness='polite')
            
        # Sonification for data patterns
        if chart.has_time_series_data():
            sonification = self._create_data_sonification(chart)
            chart.add_sonification(sonification)
            
    def _enable_keyboard_navigation(self, chart: AccessibleHealthChart) -> None:
        """Enable comprehensive keyboard navigation."""
        
        # Focus management
        chart.enable_focus_management(
            focus_indicators=True,
            focus_trap_enabled=True,
            initial_focus='chart_summary'
        )
        
        # Keyboard shortcuts
        keyboard_shortcuts = {
            'arrow_keys': 'navigate_data_points',
            'enter': 'activate_selected_point',
            'space': 'toggle_data_point_details',
            'escape': 'exit_chart_focus',
            'home': 'go_to_first_data_point',
            'end': 'go_to_last_data_point',
            'page_up': 'previous_time_period',
            'page_down': 'next_time_period',
            'tab': 'navigate_chart_elements'
        }
        
        chart.configure_keyboard_shortcuts(keyboard_shortcuts)
        
        # Announce navigation changes
        chart.on_keyboard_navigation(
            lambda event: self._announce_navigation_change(chart, event)
        )
        
    def _ensure_color_accessibility(self, chart: AccessibleHealthChart) -> None:
        """Ensure color accessibility for all users."""
        
        # Check color contrast ratios
        current_colors = chart.get_color_palette()
        contrast_issues = self._check_color_contrast(current_colors)
        
        if contrast_issues:
            # Apply high contrast color scheme
            high_contrast_colors = self.theme_manager.get_high_contrast_palette()
            chart.apply_color_palette(high_contrast_colors)
            
        # Add pattern/texture alternatives to color coding
        if chart.uses_color_coding():
            patterns = self.theme_manager.get_accessibility_patterns()
            chart.add_pattern_coding(patterns)
            
        # Colorblind-friendly adjustments
        colorblind_palette = self.theme_manager.get_colorblind_friendly_palette()
        chart.add_alternative_color_scheme('colorblind_friendly', colorblind_palette)
        
    def _add_alternative_representations(self, chart: AccessibleHealthChart) -> None:
        """Add alternative representations for chart data."""
        
        # 1. Structured data table
        data_table = AccessibleDataTable(
            data=chart.get_chart_data(),
            headers=chart.get_column_headers(),
            caption=chart.get_table_caption(),
            summary=chart.get_table_summary()
        )
        chart.add_alternative_representation('data_table', data_table)
        
        # 2. Text summary
        text_summary = self.screen_reader_narrator.create_detailed_summary(
            chart_data=chart.get_chart_data(),
            insights=chart.get_generated_insights(),
            trends=chart.get_trend_analysis()
        )
        chart.add_alternative_representation('text_summary', text_summary)
        
        # 3. Sonification for time series
        if chart.has_time_series_data():
            sonification = DataSonification(
                data=chart.get_time_series_data(),
                mapping_strategy='value_to_pitch',
                duration_per_point=100,  # ms
                audio_format='web_audio'
            )
            chart.add_alternative_representation('sonification', sonification)
            
        # 4. Haptic feedback for touch devices
        if chart.supports_touch_interaction():
            haptic_patterns = HapticFeedbackGenerator(
                data=chart.get_chart_data(),
                pattern_type='vibration_intensity',
                duration_scaling=True
            )
            chart.add_alternative_representation('haptic', haptic_patterns)
            
    def _add_aria_attributes(self, chart: AccessibleHealthChart) -> None:
        """Add comprehensive ARIA attributes for screen readers."""
        
        # Root chart container
        chart.set_aria_attributes({
            'role': 'img',
            'aria-label': chart.get_accessible_title(),
            'aria-describedby': chart.get_description_id(),
            'aria-live': 'polite' if chart.supports_real_time_updates() else 'off'
        })
        
        # Interactive elements
        for interactive_element in chart.get_interactive_elements():
            interactive_element.set_aria_attributes({
                'role': 'button',
                'aria-label': interactive_element.get_accessible_label(),
                'aria-pressed': interactive_element.is_active(),
                'tabindex': '0'
            })
            
        # Data points
        for data_point in chart.get_data_points():
            data_point.set_aria_attributes({
                'role': 'listitem',
                'aria-label': data_point.get_accessible_description(),
                'aria-setsize': chart.get_total_data_points(),
                'aria-posinset': data_point.get_position_in_set()
            })
            
    def _create_accessible_data_table(self, chart: AccessibleHealthChart) -> AccessibleDataTable:
        """Create accessible data table representation of chart."""
        
        data = chart.get_chart_data()
        
        # Create table structure
        table = AccessibleDataTable()
        
        # Table caption and summary
        table.set_caption(f"Data table for {chart.get_title()}")
        table.set_summary(chart.get_data_summary())
        
        # Headers
        headers = chart.get_column_headers()
        for i, header in enumerate(headers):
            table.add_header(
                text=header,
                scope='col',
                id=f"header_{i}",
                aria_sort=chart.get_column_sort_state(i)
            )
            
        # Data rows
        for row_index, row_data in data.iterrows():
            table_row = table.add_row()
            
            for col_index, cell_value in enumerate(row_data):
                formatted_value = chart.format_cell_value(cell_value, col_index)
                table_row.add_cell(
                    value=formatted_value,
                    headers=f"header_{col_index}",
                    aria_label=chart.get_cell_accessible_label(row_index, col_index)
                )
                
        return table
        
    def _create_data_sonification(self, chart: AccessibleHealthChart) -> DataSonification:
        """Create audio representation of chart data."""
        
        time_series_data = chart.get_time_series_data()
        
        sonification = DataSonification()
        
        # Map data values to audio properties
        sonification.configure_mapping(
            value_to_pitch=True,
            pitch_range=(200, 800),  # Hz
            value_to_volume=False,  # Keep volume constant for accessibility
            time_to_duration=True,
            note_duration=150,  # ms
            inter_note_gap=50   # ms
        )
        
        # Add audio descriptions
        sonification.add_intro_description(
            f"Audio representation of {chart.get_title()}. "
            f"Higher pitches represent higher values. "
            f"Data spans from {chart.get_date_range()}."
        )
        
        # Process data into audio
        for timestamp, value in time_series_data.items():
            sonification.add_data_point(
                timestamp=timestamp,
                value=value,
                context=chart.get_point_context(timestamp)
            )
            
        return sonification
        
class WCAGValidator:
    """WCAG 2.1 compliance validator for visualizations."""
    
    def __init__(self):
        self.contrast_checker = ColorContrastChecker()
        self.keyboard_tester = KeyboardAccessibilityTester()
        self.screen_reader_tester = ScreenReaderTester()
        
    def validate(self, chart: AccessibleHealthChart) -> AccessibilityReport:
        """Perform comprehensive WCAG 2.1 validation."""
        
        report = AccessibilityReport()
        
        # Level A requirements
        report.add_test_results(self._test_level_a_requirements(chart))
        
        # Level AA requirements
        report.add_test_results(self._test_level_aa_requirements(chart))
        
        # Health-specific accessibility requirements
        report.add_test_results(self._test_health_specific_requirements(chart))
        
        return report
        
    def _test_level_aa_requirements(self, chart: AccessibleHealthChart) -> List[TestResult]:
        """Test WCAG 2.1 Level AA requirements."""
        
        results = []
        
        # 1.4.3 Contrast (Minimum)
        contrast_result = self.contrast_checker.check_minimum_contrast(
            chart.get_color_combinations()
        )
        results.append(TestResult(
            criterion='1.4.3',
            name='Contrast (Minimum)',
            passed=contrast_result.all_pass,
            details=contrast_result.details
        ))
        
        # 2.1.1 Keyboard
        keyboard_result = self.keyboard_tester.test_keyboard_accessibility(chart)
        results.append(TestResult(
            criterion='2.1.1',
            name='Keyboard',
            passed=keyboard_result.all_functions_accessible,
            details=keyboard_result.details
        ))
        
        # 2.1.2 No Keyboard Trap
        trap_result = self.keyboard_tester.test_no_keyboard_trap(chart)
        results.append(TestResult(
            criterion='2.1.2',
            name='No Keyboard Trap',
            passed=trap_result.no_traps_found,
            details=trap_result.details
        ))
        
        # 3.1.1 Language of Page
        lang_result = self._test_language_identification(chart)
        results.append(TestResult(
            criterion='3.1.1',
            name='Language of Page',
            passed=lang_result.language_identified,
            details=lang_result.details
        ))
        
        return results
```

### Practical Accessibility Implementation

```python
# src/ui/visualizations/accessibility/health_accessibility_manager.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QAccessible, QAccessibleEvent
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QKeyEvent, QFocusEvent
from PyQt6.QtMultimedia import QAudioOutput
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import pyttsx3  # Text-to-speech

class HealthChartAccessibilityManager(QObject):
    """Comprehensive accessibility manager for health visualizations"""
    
    # Signals
    announcement = pyqtSignal(str)  # Screen reader announcement
    focus_changed = pyqtSignal(str, dict)  # element_type, data
    
    def __init__(self):
        super().__init__()
        self.tts_engine = pyttsx3.init()
        self.current_focus = None
        self.navigation_mode = 'browse'
        self.announcement_queue = []
        self.tts_enabled = False
        
    def make_chart_accessible(self, chart: HealthVisualizationComponent) -> None:
        """Apply comprehensive accessibility features to chart"""
        
        # 1. Set up keyboard navigation
        self._setup_keyboard_navigation(chart)
        
        # 2. Add screen reader support
        self._add_screen_reader_support(chart)
        
        # 3. Create alternative representations
        self._create_alternatives(chart)
        
        # 4. Ensure visual accessibility
        self._ensure_visual_accessibility(chart)
        
        # 5. Add interaction feedback
        self._setup_interaction_feedback(chart)
        
    def _setup_keyboard_navigation(self, chart: HealthVisualizationComponent):
        """Set up comprehensive keyboard navigation"""
        
        # Install event filter
        chart.installEventFilter(self)
        
        # Make focusable
        chart.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set up navigation handlers
        self.navigation_handlers = {
            Qt.Key.Key_Tab: self._handle_tab_navigation,
            Qt.Key.Key_Left: self._handle_left_navigation,
            Qt.Key.Key_Right: self._handle_right_navigation,
            Qt.Key.Key_Up: self._handle_up_navigation,
            Qt.Key.Key_Down: self._handle_down_navigation,
            Qt.Key.Key_Home: self._handle_home_navigation,
            Qt.Key.Key_End: self._handle_end_navigation,
            Qt.Key.Key_Enter: self._handle_activation,
            Qt.Key.Key_Space: self._handle_activation,
            Qt.Key.Key_A: self._announce_current,
            Qt.Key.Key_T: self._show_table_view,
            Qt.Key.Key_S: self._toggle_sonification,
            Qt.Key.Key_H: self._show_help
        }
        
    def eventFilter(self, obj, event):
        """Handle keyboard events for accessibility"""
        
        if event.type() == QKeyEvent.Type.KeyPress:
            key = event.key()
            if key in self.navigation_handlers:
                return self.navigation_handlers[key](obj, event)
                
        elif event.type() == QFocusEvent.Type.FocusIn:
            self._handle_focus_in(obj)
            
        elif event.type() == QFocusEvent.Type.FocusOut:
            self._handle_focus_out(obj)
            
        return False
        
    def _handle_left_navigation(self, chart, event):
        """Navigate to previous data point"""
        
        current_index = chart.get_focused_data_index()
        if current_index > 0:
            chart.set_focused_data_index(current_index - 1)
            self._announce_data_point(chart, current_index - 1)
            return True
        else:
            self._announce("Beginning of data")
            return True
            
    def _announce_data_point(self, chart, index: int):
        """Announce data point details"""
        
        data_point = chart.get_data_point(index)
        
        # Create descriptive announcement
        announcement = self._create_data_announcement(data_point, chart)
        
        # Queue announcement
        self.announcement.emit(announcement)
        
        # Optional: Use TTS
        if self.tts_enabled:
            self.tts_engine.say(announcement)
            self.tts_engine.runAndWait()
            
    def _create_data_announcement(self, data_point: HealthDataPoint, 
                                chart: HealthVisualizationComponent) -> str:
        """Create descriptive announcement for data point"""
        
        # Basic information
        parts = [
            f"{data_point.metric_name}:",
            f"{data_point.value} {data_point.unit}",
            f"at {data_point.timestamp.strftime('%B %d, %I:%M %p')}"
        ]
        
        # Add context
        if data_point.is_anomaly:
            parts.append("Warning: Unusual value")
            
        if data_point.is_achievement:
            parts.append("Achievement: Personal record")
            
        # Add trend information
        trend = chart.get_trend_at_point(data_point)
        if trend:
            parts.append(f"Trend: {trend}")
            
        return ". ".join(parts)
        
    def _announce(self, text: str):
        """Make announcement through screen reader"""
        self.announcement.emit(text)

# src/ui/visualizations/accessibility/data_table_alternative.py
class AccessibleDataTableWidget(QTableWidget):
    """Accessible data table representation of chart"""
    
    def __init__(self, chart_data: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.chart_data = chart_data
        self._setup_table()
        self._apply_accessibility_features()
        
    def _setup_table(self):
        """Set up table structure"""
        
        # Set dimensions
        self.setRowCount(len(self.chart_data))
        self.setColumnCount(len(self.chart_data.columns))
        
        # Set headers
        self.setHorizontalHeaderLabels(self.chart_data.columns.tolist())
        
        # Populate data
        for row_idx, (index, row) in enumerate(self.chart_data.iterrows()):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(self._format_value(value, col_idx))
                item.setData(Qt.ItemDataRole.UserRole, value)  # Store raw value
                self.setItem(row_idx, col_idx, item)
                
    def _apply_accessibility_features(self):
        """Apply accessibility enhancements"""
        
        # Enable keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Add descriptions
        self.setAccessibleName("Chart data table")
        self.setAccessibleDescription(
            f"Table containing {self.rowCount()} rows of health data"
        )
        
        # Connect signals for announcements
        self.currentCellChanged.connect(self._announce_cell_change)
        
    def _announce_cell_change(self, row, col, prev_row, prev_col):
        """Announce cell content on navigation"""
        
        if row >= 0 and col >= 0:
            value = self.item(row, col).text()
            header = self.horizontalHeaderItem(col).text()
            
            announcement = f"{header}: {value}"
            
            # Add row context
            if col == 0:  # First column
                announcement += f", Row {row + 1} of {self.rowCount()}"
                
            QAccessible.updateAccessibility(
                QAccessibleEvent(self, QAccessible.Event.Focus)
            )
            
    def _format_value(self, value, col_idx: int) -> str:
        """Format value for display"""
        if isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return str(value)

# src/ui/visualizations/accessibility/sonification_engine.py            
class HealthDataSonificationEngine:
    """Convert health data to audio representation"""
    
    def __init__(self):
        self.audio_engine = QAudioOutput()
        self.sample_rate = 44100
        self.base_frequency = 440  # A4
        self.duration_per_point = 100  # ms
        
    def sonify_time_series(self, data: pd.DataFrame, 
                          metric: str) -> bytes:
        """Convert time series data to audio"""
        
        values = data[metric].values
        
        # Normalize values to frequency range
        min_val, max_val = values.min(), values.max()
        freq_range = (220, 880)  # A3 to A5
        
        # Generate audio samples
        audio_data = []
        
        for value in values:
            # Map value to frequency
            normalized = (value - min_val) / (max_val - min_val)
            frequency = freq_range[0] + normalized * (freq_range[1] - freq_range[0])
            
            # Generate sine wave
            samples = self._generate_tone(frequency, self.duration_per_point)
            audio_data.extend(samples)
            
        # Convert to byte array
        return self._samples_to_bytes(audio_data)
        
    def _generate_tone(self, frequency: float, duration_ms: int) -> List[float]:
        """Generate sine wave tone"""
        
        num_samples = int(self.sample_rate * duration_ms / 1000)
        samples = []
        
        for i in range(num_samples):
            t = i / self.sample_rate
            sample = 0.5 * np.sin(2 * np.pi * frequency * t)
            samples.append(sample)
            
        # Add fade in/out to prevent clicks
        fade_samples = int(0.01 * self.sample_rate)  # 10ms fade
        for i in range(fade_samples):
            samples[i] *= i / fade_samples
            samples[-(i+1)] *= i / fade_samples
            
        return samples
        
    def _samples_to_bytes(self, samples: List[float]) -> bytes:
        """Convert float samples to byte array"""
        # Convert to 16-bit PCM
        int_samples = np.array(samples) * 32767
        return int_samples.astype(np.int16).tobytes()

# src/ui/visualizations/accessibility/color_contrast_checker.py
class WSJColorContrastChecker:
    """Ensure WSJ colors meet accessibility standards"""
    
    def __init__(self):
        self.wcag_aa_normal = 4.5
        self.wcag_aa_large = 3.0
        self.wcag_aaa_normal = 7.0
        self.wcag_aaa_large = 4.5
        
    def check_wsj_palette(self) -> Dict[str, ContrastResult]:
        """Check all WSJ color combinations"""
        
        results = {}
        
        # WSJ colors
        colors = {
            'background': '#F5E6D3',
            'text': '#6B4226',
            'primary': '#FF8C42',
            'secondary': '#FFD166',
            'success': '#7CB342',
            'warning': '#F4511E'
        }
        
        # Check all combinations
        for fg_name, fg_color in colors.items():
            for bg_name, bg_color in colors.items():
                if fg_name != bg_name:
                    key = f"{fg_name}_on_{bg_name}"
                    ratio = self.calculate_contrast_ratio(fg_color, bg_color)
                    results[key] = ContrastResult(
                        foreground=fg_color,
                        background=bg_color,
                        ratio=ratio,
                        passes_aa=ratio >= self.wcag_aa_normal,
                        passes_aaa=ratio >= self.wcag_aaa_normal
                    )
                    
        return results
        
    def calculate_contrast_ratio(self, fg: str, bg: str) -> float:
        """Calculate WCAG contrast ratio"""
        
        # Convert hex to RGB
        fg_rgb = self._hex_to_rgb(fg)
        bg_rgb = self._hex_to_rgb(bg)
        
        # Calculate relative luminance
        fg_lum = self._relative_luminance(fg_rgb)
        bg_lum = self._relative_luminance(bg_rgb)
        
        # Calculate contrast ratio
        lighter = max(fg_lum, bg_lum)
        darker = min(fg_lum, bg_lum)
        
        return (lighter + 0.05) / (darker + 0.05)
        
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
    def _relative_luminance(self, rgb: tuple) -> float:
        """Calculate relative luminance"""
        def adjust(val):
            if val <= 0.03928:
                return val / 12.92
            return ((val + 0.055) / 1.055) ** 2.4
            
        r, g, b = [adjust(v) for v in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
    def suggest_alternatives(self, fg: str, bg: str, 
                           target_ratio: float = 4.5) -> List[str]:
        """Suggest color alternatives that meet contrast requirements"""
        
        current_ratio = self.calculate_contrast_ratio(fg, bg)
        
        if current_ratio >= target_ratio:
            return []  # Already meets requirements
            
        suggestions = []
        
        # Try darkening/lightening the foreground
        for adjustment in range(5, 50, 5):
            darker = self._adjust_lightness(fg, -adjustment)
            lighter = self._adjust_lightness(fg, adjustment)
            
            if self.calculate_contrast_ratio(darker, bg) >= target_ratio:
                suggestions.append(darker)
            if self.calculate_contrast_ratio(lighter, bg) >= target_ratio:
                suggestions.append(lighter)
                
        return suggestions[:3]  # Return top 3 suggestions
        
    def _adjust_lightness(self, hex_color: str, percent: int) -> str:
        """Adjust color lightness by percentage"""
        rgb = self._hex_to_rgb(hex_color)
        
        # Convert to HSL, adjust L, convert back
        # Simplified version - in practice use colorsys
        factor = 1 + (percent / 100.0)
        new_rgb = tuple(min(1.0, max(0.0, c * factor)) for c in rgb)
        
        # Convert back to hex
        return '#{:02x}{:02x}{:02x}'.format(
            int(new_rgb[0] * 255),
            int(new_rgb[1] * 255),
            int(new_rgb[2] * 255)
        )
```