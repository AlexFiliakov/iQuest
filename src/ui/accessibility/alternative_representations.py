"""
Alternative representations for chart data.

Provides data tables, sonification, and other accessible formats.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView,
                           QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
# from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer  # Optional dependency
from PyQt6.QtGui import QKeySequence
import io
import wave
from datetime import datetime

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AudioConfig:
    """Configuration for data sonification."""
    
    sample_rate: int = 44100
    base_frequency: float = 440.0  # A4
    min_frequency: float = 220.0   # A3
    max_frequency: float = 880.0   # A5
    duration_per_point: int = 150  # milliseconds
    gap_between_points: int = 50   # milliseconds
    volume: float = 0.5


class AccessibleDataTable(QTableWidget):
    """Accessible data table representation of chart data."""
    
    def __init__(self, data: pd.DataFrame, title: str = "Data Table"):
        super().__init__()
        self.data = data
        self.title = title
        self._setup_table()
        self._apply_accessibility()
    
    def _setup_table(self):
        """Set up table structure and data."""
        # Set dimensions
        self.setRowCount(len(self.data))
        self.setColumnCount(len(self.data.columns))
        
        # Set headers
        self.setHorizontalHeaderLabels([str(col) for col in self.data.columns])
        
        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Populate data
        for row_idx in range(len(self.data)):
            for col_idx, col in enumerate(self.data.columns):
                value = self.data.iloc[row_idx, col_idx]
                item = QTableWidgetItem(self._format_value(value, col))
                item.setData(Qt.ItemDataRole.UserRole, value)
                self.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.resizeColumnsToContents()
        
        # Add keyboard shortcuts
        self._add_shortcuts()
    
    def _apply_accessibility(self):
        """Apply accessibility enhancements."""
        # Set accessible name and description
        self.setAccessibleName(self.title)
        self.setAccessibleDescription(
            f"Data table with {self.rowCount()} rows and "
            f"{self.columnCount()} columns of health data"
        )
        
        # Enable keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Connect signals for announcements
        self.currentCellChanged.connect(self._announce_cell_change)
        self.itemSelectionChanged.connect(self._announce_selection_change)
    
    def _add_shortcuts(self):
        """Add keyboard shortcuts for table navigation."""
        shortcuts = {
            'Ctrl+Home': self._go_to_first_cell,
            'Ctrl+End': self._go_to_last_cell,
            'Ctrl+S': self._sort_current_column,
            'Ctrl+F': self._focus_search,
            'F2': self._read_current_row
        }
        
        for key_seq, handler in shortcuts.items():
            shortcut = QKeySequence(key_seq)
            self.addAction(self._create_action(shortcut, handler))
    
    def _create_action(self, shortcut, handler):
        """Create action with shortcut."""
        from PyQt6.QtGui import QAction
        action = QAction(self)
        action.setShortcut(shortcut)
        action.triggered.connect(handler)
        return action
    
    def _format_value(self, value: Any, column: str) -> str:
        """Format value for display."""
        if pd.isna(value):
            return ""
        elif isinstance(value, (int, float)):
            # Format based on column name
            if 'heart' in str(column).lower():
                return f"{value:.0f} bpm"
            elif 'step' in str(column).lower():
                return f"{value:,.0f}"
            elif 'distance' in str(column).lower():
                return f"{value:.2f} km"
            else:
                return f"{value:.2f}"
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return str(value)
    
    def _announce_cell_change(self, row: int, col: int, 
                             prev_row: int, prev_col: int):
        """Announce cell content on navigation."""
        if row >= 0 and col >= 0:
            value = self.item(row, col).text()
            header = self.horizontalHeaderItem(col).text()
            
            announcement = f"{header}: {value}"
            
            # Add context
            if row != prev_row:
                announcement += f", Row {row + 1} of {self.rowCount()}"
            
            # This would integrate with screen reader
            logger.debug(f"Announcing: {announcement}")
    
    def _announce_selection_change(self):
        """Announce selection changes."""
        selected = self.selectedItems()
        if selected:
            announcement = f"{len(selected)} cells selected"
            logger.debug(f"Announcing: {announcement}")
    
    def _go_to_first_cell(self):
        """Navigate to first cell."""
        self.setCurrentCell(0, 0)
    
    def _go_to_last_cell(self):
        """Navigate to last cell."""
        self.setCurrentCell(self.rowCount() - 1, self.columnCount() - 1)
    
    def _sort_current_column(self):
        """Sort by current column."""
        col = self.currentColumn()
        if col >= 0:
            current_order = self.horizontalHeader().sortIndicatorOrder()
            new_order = (Qt.SortOrder.DescendingOrder 
                        if current_order == Qt.SortOrder.AscendingOrder 
                        else Qt.SortOrder.AscendingOrder)
            self.sortItems(col, new_order)
    
    def _focus_search(self):
        """Focus search functionality."""
        # This would open a search dialog
        logger.info("Search functionality triggered")
    
    def _read_current_row(self):
        """Read entire current row."""
        row = self.currentRow()
        if row >= 0:
            values = []
            for col in range(self.columnCount()):
                header = self.horizontalHeaderItem(col).text()
                value = self.item(row, col).text()
                values.append(f"{header}: {value}")
            
            announcement = ", ".join(values)
            logger.debug(f"Reading row: {announcement}")


class DataSonification(QObject):
    """Convert data to audio representation."""
    
    # Signals
    audio_ready = pyqtSignal(bytes)
    playback_finished = pyqtSignal()
    
    def __init__(self, config: Optional[AudioConfig] = None):
        super().__init__()
        self.config = config or AudioConfig()
        self.audio_data = []
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        logger.info("Initialized DataSonification")
    
    def sonify_series(self, data: pd.Series, name: str = "Data") -> bytes:
        """Convert data series to audio."""
        try:
            values = data.dropna().values
            if len(values) == 0:
                return b''
            
            # Normalize values to frequency range
            min_val, max_val = values.min(), values.max()
            if min_val == max_val:
                # All values are the same
                frequencies = [self.config.base_frequency] * len(values)
            else:
                # Map to frequency range
                normalized = (values - min_val) / (max_val - min_val)
                frequencies = (self.config.min_frequency + 
                             normalized * (self.config.max_frequency - 
                                          self.config.min_frequency))
            
            # Generate audio
            audio_samples = []
            
            for i, freq in enumerate(frequencies):
                # Generate tone
                tone = self._generate_tone(freq, self.config.duration_per_point)
                audio_samples.extend(tone)
                
                # Add gap between points
                if i < len(frequencies) - 1:
                    gap = [0] * int(self.config.sample_rate * 
                                   self.config.gap_between_points / 1000)
                    audio_samples.extend(gap)
            
            # Convert to bytes
            audio_bytes = self._samples_to_wav_bytes(audio_samples)
            
            self.audio_ready.emit(audio_bytes)
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error in sonification: {e}")
            return b''
    
    def sonify_comparison(self, series1: pd.Series, series2: pd.Series,
                         names: Tuple[str, str] = ("Series 1", "Series 2")) -> bytes:
        """Sonify two series for comparison (stereo)."""
        try:
            # Ensure same length
            min_len = min(len(series1), len(series2))
            s1 = series1.iloc[:min_len]
            s2 = series2.iloc[:min_len]
            
            # Generate audio for each series
            audio1 = self._generate_series_audio(s1)
            audio2 = self._generate_series_audio(s2)
            
            # Combine as stereo (series1 = left, series2 = right)
            stereo_samples = []
            for i in range(len(audio1)):
                stereo_samples.append(audio1[i])  # Left channel
                stereo_samples.append(audio2[i] if i < len(audio2) else 0)  # Right
            
            return self._samples_to_wav_bytes(stereo_samples, channels=2)
            
        except Exception as e:
            logger.error(f"Error in comparison sonification: {e}")
            return b''
    
    def _generate_tone(self, frequency: float, duration_ms: int) -> List[float]:
        """Generate sine wave tone."""
        num_samples = int(self.config.sample_rate * duration_ms / 1000)
        samples = []
        
        for i in range(num_samples):
            t = i / self.config.sample_rate
            sample = self.config.volume * np.sin(2 * np.pi * frequency * t)
            samples.append(sample)
        
        # Apply fade in/out to prevent clicks
        fade_samples = int(0.01 * self.config.sample_rate)  # 10ms fade
        for i in range(min(fade_samples, len(samples) // 2)):
            samples[i] *= i / fade_samples
            samples[-(i+1)] *= i / fade_samples
        
        return samples
    
    def _generate_series_audio(self, series: pd.Series) -> List[float]:
        """Generate audio samples for a series."""
        values = series.dropna().values
        if len(values) == 0:
            return []
        
        # Normalize and map to frequencies
        min_val, max_val = values.min(), values.max()
        if min_val == max_val:
            frequencies = [self.config.base_frequency] * len(values)
        else:
            normalized = (values - min_val) / (max_val - min_val)
            frequencies = (self.config.min_frequency + 
                         normalized * (self.config.max_frequency - 
                                      self.config.min_frequency))
        
        # Generate audio
        audio_samples = []
        for freq in frequencies:
            tone = self._generate_tone(freq, self.config.duration_per_point)
            audio_samples.extend(tone)
            
            # Gap
            gap = [0] * int(self.config.sample_rate * 
                           self.config.gap_between_points / 1000)
            audio_samples.extend(gap)
        
        return audio_samples
    
    def _samples_to_wav_bytes(self, samples: List[float], 
                             channels: int = 1) -> bytes:
        """Convert samples to WAV format bytes."""
        # Convert to 16-bit PCM
        int_samples = np.array(samples) * 32767
        int_samples = int_samples.astype(np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(int_samples.tobytes())
        
        return buffer.getvalue()
    
    def play_audio(self, audio_bytes: bytes):
        """Play audio bytes."""
        try:
            # Save to temporary file (QMediaPlayer needs a file)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            # Play audio
            from PyQt6.QtCore import QUrl
            self.player.setSource(QUrl.fromLocalFile(tmp_path))
            self.player.play()
            
            # Clean up after playback
            self.player.mediaStatusChanged.connect(
                lambda status: self._cleanup_temp_file(tmp_path, status)
            )
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def _cleanup_temp_file(self, path: str, status):
        """Clean up temporary audio file."""
        from PyQt6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                import os
                os.unlink(path)
                self.playback_finished.emit()
            except:
                pass


@dataclass 
class HapticPattern:
    """Haptic feedback pattern for data representation."""
    pattern_type: str  # 'vibration', 'pulse', 'wave'
    intensity: float  # 0.0 to 1.0
    duration_ms: int
    gap_ms: int = 0
    repetitions: int = 1


class HapticFeedbackGenerator:
    """Generate haptic feedback patterns for touch interfaces."""
    
    def __init__(self):
        self.patterns = {
            'low_value': HapticPattern('pulse', 0.3, 100, 50, 1),
            'medium_value': HapticPattern('pulse', 0.6, 150, 50, 2),
            'high_value': HapticPattern('vibration', 0.9, 200, 0, 1),
            'peak': HapticPattern('wave', 1.0, 300, 100, 2),
            'valley': HapticPattern('pulse', 0.5, 100, 100, 3),
            'anomaly': HapticPattern('vibration', 1.0, 500, 200, 3),
            'trend_up': HapticPattern('wave', 0.7, 150, 50, 1),
            'trend_down': HapticPattern('wave', 0.4, 150, 50, 1)
        }
    
    def generate_pattern_for_value(self, value: float, min_val: float, 
                                  max_val: float) -> HapticPattern:
        """Generate haptic pattern based on value in range."""
        if min_val == max_val:
            return self.patterns['medium_value']
        
        normalized = (value - min_val) / (max_val - min_val)
        
        if normalized < 0.33:
            return self.patterns['low_value']
        elif normalized < 0.67:
            return self.patterns['medium_value']
        else:
            return self.patterns['high_value']
    
    def generate_pattern_sequence(self, data: pd.Series) -> List[HapticPattern]:
        """Generate sequence of haptic patterns for data series."""
        if data.empty:
            return []
        
        patterns = []
        min_val, max_val = data.min(), data.max()
        
        for i, value in enumerate(data):
            pattern = self.generate_pattern_for_value(value, min_val, max_val)
            
            # Check for special conditions
            if i > 0:
                prev_val = data.iloc[i-1]
                if value > prev_val * 1.2:  # 20% increase
                    pattern = self.patterns['trend_up']
                elif value < prev_val * 0.8:  # 20% decrease
                    pattern = self.patterns['trend_down']
            
            # Check for peaks/valleys
            if i > 0 and i < len(data) - 1:
                if data.iloc[i] > data.iloc[i-1] and data.iloc[i] > data.iloc[i+1]:
                    pattern = self.patterns['peak']
                elif data.iloc[i] < data.iloc[i-1] and data.iloc[i] < data.iloc[i+1]:
                    pattern = self.patterns['valley']
            
            patterns.append(pattern)
        
        return patterns
    
    def encode_for_device(self, patterns: List[HapticPattern]) -> Dict[str, Any]:
        """Encode haptic patterns for device-specific format."""
        # This would be device-specific encoding
        # For now, return a generic format
        return {
            'format': 'haptic_sequence_v1',
            'patterns': [
                {
                    'type': p.pattern_type,
                    'intensity': p.intensity,
                    'duration': p.duration_ms,
                    'gap': p.gap_ms,
                    'repeat': p.repetitions
                }
                for p in patterns
            ],
            'total_duration': sum(
                p.duration_ms * p.repetitions + p.gap_ms * (p.repetitions - 1)
                for p in patterns
            )
        }


class AlternativeRepresentationManager:
    """Manages alternative representations for charts."""
    
    def __init__(self):
        self.sonification = DataSonification()
        self.haptic_generator = HapticFeedbackGenerator()
        logger.info("Initialized AlternativeRepresentationManager")
    
    def create_data_table(self, data: pd.DataFrame, title: str) -> AccessibleDataTable:
        """Create accessible data table from chart data."""
        return AccessibleDataTable(data, title)
    
    def create_text_summary(self, chart_data: str, 
                           insights: List[str]) -> str:
        """Create text summary of chart."""
        parts = ["Chart Summary:", chart_data]
        
        if insights:
            parts.append("Key Insights:")
            parts.extend([f"- {insight}" for insight in insights])
        
        return "\n".join(parts)
    
    def create_sonification(self, data: pd.Series) -> DataSonification:
        """Create sonification of time series data."""
        audio_bytes = self.sonification.sonify_series(data)
        return self.sonification
    
    def create_haptic_feedback(self, data: pd.Series) -> Dict[str, Any]:
        """Create haptic feedback patterns for data."""
        patterns = self.haptic_generator.generate_pattern_sequence(data)
        return self.haptic_generator.encode_for_device(patterns)
    
    def export_to_csv(self, data: pd.DataFrame, filename: str):
        """Export data to CSV for external analysis."""
        try:
            data.to_csv(filename, index=False)
            logger.info(f"Exported data to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def export_to_json(self, data: pd.DataFrame, filename: str):
        """Export data to JSON format."""
        try:
            data.to_json(filename, orient='records', date_format='iso')
            logger.info(f"Exported data to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")