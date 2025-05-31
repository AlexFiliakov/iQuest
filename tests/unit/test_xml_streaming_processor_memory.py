"""Test memory limit validation for XMLStreamingProcessor."""

import pytest
from src.xml_streaming_processor import XMLStreamingProcessor, MemoryMonitor
from src.config import MIN_MEMORY_LIMIT_MB, MAX_MEMORY_LIMIT_MB, DEFAULT_MEMORY_LIMIT_MB


class TestMemoryLimitValidation:
    """Test memory limit validation in XMLStreamingProcessor."""
    
    def test_valid_memory_limits(self):
        """Test that valid memory limits are accepted."""
        # Test minimum valid limit
        processor = XMLStreamingProcessor(memory_limit_mb=MIN_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MIN_MEMORY_LIMIT_MB
        
        # Test maximum valid limit
        processor = XMLStreamingProcessor(memory_limit_mb=MAX_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MAX_MEMORY_LIMIT_MB
        
        # Test default limit
        processor = XMLStreamingProcessor()
        assert processor.memory_limit_mb == DEFAULT_MEMORY_LIMIT_MB
        
        # Test some valid values in between
        processor = XMLStreamingProcessor(memory_limit_mb=512)
        assert processor.memory_limit_mb == 512
        
        processor = XMLStreamingProcessor(memory_limit_mb=2048)
        assert processor.memory_limit_mb == 2048
    
    def test_memory_limit_too_low(self):
        """Test that memory limits below minimum are rejected."""
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(memory_limit_mb=MIN_MEMORY_LIMIT_MB - 1)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(memory_limit_mb=50)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(memory_limit_mb=0)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
    
    def test_memory_limit_too_high(self):
        """Test that memory limits above maximum are rejected."""
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(memory_limit_mb=MAX_MEMORY_LIMIT_MB + 1)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(memory_limit_mb=10000)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
    
    def test_memory_limit_edge_cases(self):
        """Test edge cases for memory limit validation."""
        # Test exact minimum
        processor = XMLStreamingProcessor(memory_limit_mb=MIN_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MIN_MEMORY_LIMIT_MB
        
        # Test exact maximum
        processor = XMLStreamingProcessor(memory_limit_mb=MAX_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MAX_MEMORY_LIMIT_MB
        
        # Test negative value
        with pytest.raises(ValueError):
            XMLStreamingProcessor(memory_limit_mb=-100)


class TestMemoryMonitorValidation:
    """Test memory limit validation in MemoryMonitor."""
    
    def test_memory_monitor_accepts_valid_limits(self):
        """Test that MemoryMonitor accepts valid memory limits."""
        monitor = MemoryMonitor(limit_mb=512)
        assert monitor.limit_mb == 512
        
        monitor = MemoryMonitor(limit_mb=MIN_MEMORY_LIMIT_MB)
        assert monitor.limit_mb == MIN_MEMORY_LIMIT_MB
        
        monitor = MemoryMonitor(limit_mb=MAX_MEMORY_LIMIT_MB)
        assert monitor.limit_mb == MAX_MEMORY_LIMIT_MB