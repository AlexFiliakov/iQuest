"""Unit tests for XML streaming processor parameter validation.

This module tests the bounds checking and validation logic for the
XMLStreamingProcessor and MemoryMonitor classes.
"""

import pytest
from src.xml_streaming_processor import XMLStreamingProcessor, MemoryMonitor
from src.config import MIN_MEMORY_LIMIT_MB, MAX_MEMORY_LIMIT_MB, DEFAULT_MEMORY_LIMIT_MB


class TestMemoryMonitorValidation:
    """Test memory monitor parameter validation."""
    
    def test_valid_memory_limits(self):
        """Test that valid memory limits are accepted."""
        # Test minimum valid limit
        monitor = MemoryMonitor(MIN_MEMORY_LIMIT_MB)
        assert monitor.limit_mb == MIN_MEMORY_LIMIT_MB
        
        # Test maximum valid limit
        monitor = MemoryMonitor(MAX_MEMORY_LIMIT_MB)
        assert monitor.limit_mb == MAX_MEMORY_LIMIT_MB
        
        # Test default limit
        monitor = MemoryMonitor()
        assert monitor.limit_mb == DEFAULT_MEMORY_LIMIT_MB
        
        # Test various valid limits
        for limit in [100, 256, 512, 1024, 2048, 4096]:
            monitor = MemoryMonitor(limit)
            assert monitor.limit_mb == limit
    
    def test_memory_limit_too_low(self):
        """Test that memory limits below minimum raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MemoryMonitor(MIN_MEMORY_LIMIT_MB - 1)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            MemoryMonitor(0)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            MemoryMonitor(-100)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
    
    def test_memory_limit_too_high(self):
        """Test that memory limits above maximum raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            MemoryMonitor(MAX_MEMORY_LIMIT_MB + 1)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            MemoryMonitor(10000)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)


class TestXMLStreamingProcessorValidation:
    """Test XML streaming processor parameter validation."""
    
    def test_valid_memory_limits(self):
        """Test that valid memory limits are accepted."""
        # Test minimum valid limit
        processor = XMLStreamingProcessor(MIN_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MIN_MEMORY_LIMIT_MB
        assert processor.memory_monitor.limit_mb == MIN_MEMORY_LIMIT_MB
        
        # Test maximum valid limit
        processor = XMLStreamingProcessor(MAX_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MAX_MEMORY_LIMIT_MB
        assert processor.memory_monitor.limit_mb == MAX_MEMORY_LIMIT_MB
        
        # Test default limit
        processor = XMLStreamingProcessor()
        assert processor.memory_limit_mb == DEFAULT_MEMORY_LIMIT_MB
        assert processor.memory_monitor.limit_mb == DEFAULT_MEMORY_LIMIT_MB
        
        # Test various valid limits
        for limit in [100, 256, 512, 1024, 2048, 4096]:
            processor = XMLStreamingProcessor(limit)
            assert processor.memory_limit_mb == limit
            assert processor.memory_monitor.limit_mb == limit
    
    def test_memory_limit_too_low(self):
        """Test that memory limits below minimum raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(MIN_MEMORY_LIMIT_MB - 1)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(0)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(-100)
        assert f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
    
    def test_memory_limit_too_high(self):
        """Test that memory limits above maximum raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(MAX_MEMORY_LIMIT_MB + 1)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            XMLStreamingProcessor(10000)
        assert f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB" in str(exc_info.value)
    
    def test_edge_cases(self):
        """Test edge cases for memory limits."""
        # Test exactly at boundaries
        processor = XMLStreamingProcessor(MIN_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MIN_MEMORY_LIMIT_MB
        
        processor = XMLStreamingProcessor(MAX_MEMORY_LIMIT_MB)
        assert processor.memory_limit_mb == MAX_MEMORY_LIMIT_MB
        
        # Test one below and above boundaries
        with pytest.raises(ValueError):
            XMLStreamingProcessor(MIN_MEMORY_LIMIT_MB - 1)
        
        with pytest.raises(ValueError):
            XMLStreamingProcessor(MAX_MEMORY_LIMIT_MB + 1)