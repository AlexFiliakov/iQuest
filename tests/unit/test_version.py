"""Tests for version module."""

import pytest
from src.version import __version__, __version_info__, get_version, get_version_info


class TestVersion:
    """Test version information."""
    
    def test_version_format(self):
        """Test version string format."""
        # Version should follow semantic versioning
        parts = __version__.split('.')
        assert len(parts) == 3
        
        # Each part should be a number
        for part in parts:
            assert part.isdigit()
    
    def test_version_info_tuple(self):
        """Test __version_info__ tuple."""
        assert isinstance(__version_info__, tuple)
        assert len(__version_info__) == 3
        
        # Each element should be an integer
        for element in __version_info__:
            assert isinstance(element, int)
            assert element >= 0
    
    def test_version_consistency(self):
        """Test consistency between __version__ and __version_info__."""
        version_from_tuple = '.'.join(str(v) for v in __version_info__)
        assert version_from_tuple == __version__
    
    def test_get_version_function(self):
        """Test get_version function."""
        version_str = get_version()
        
        assert isinstance(version_str, str)
        assert version_str == __version__
        assert version_str == "0.1.0"
    
    def test_get_version_info_function(self):
        """Test get_version_info function."""
        version_info = get_version_info()
        
        assert isinstance(version_info, tuple)
        assert version_info == __version_info__
        assert version_info == (0, 1, 0)
    
    def test_version_comparison(self):
        """Test version can be used for comparison."""
        # Create version tuples for comparison
        current = __version_info__
        older = (0, 0, 9)
        newer = (0, 2, 0)
        
        assert older < current < newer
    
    def test_version_string_components(self):
        """Test version string components."""
        major, minor, patch = __version__.split('.')
        
        assert int(major) == __version_info__[0]
        assert int(minor) == __version_info__[1]
        assert int(patch) == __version_info__[2]
    
    def test_version_immutability(self):
        """Test that version info is immutable."""
        # Tuple should be immutable
        with pytest.raises(TypeError):
            __version_info__[0] = 1
        
        # Get functions should return consistent values
        assert get_version() == get_version()
        assert get_version_info() == get_version_info()