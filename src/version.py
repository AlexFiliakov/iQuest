"""Version information for Apple Health Monitor.

This module provides version information and utilities for the Apple Health Monitor
Dashboard application. It centralizes version management and provides convenient
functions to access version data.

Example:
    >>> from version import get_version, get_version_info
    >>> print(f"Version: {get_version()}")
    Version: 0.1.0
    >>> print(f"Version tuple: {get_version_info()}")
    Version tuple: (0, 1, 0)
"""

__version__ = "1.0.0"
__version_info__ = tuple(int(x) for x in __version__.split('.'))
__release_date__ = "2025-01-15"
__release_channel__ = "stable"  # stable, beta, dev

def get_version() -> str:
    """Return the version string.
    
    Returns:
        str: The current version string (e.g., "0.1.0").
    """
    return __version__

def get_version_info() -> tuple:
    """Return version as a tuple of integers.
    
    Returns:
        tuple: Version as a tuple of integers (e.g., (0, 1, 0)).
        
    Example:
        >>> version_tuple = get_version_info()
        >>> major, minor, patch = version_tuple
        >>> print(f"Major: {major}, Minor: {minor}, Patch: {patch}")
        Major: 0, Minor: 1, Patch: 0
    """
    return __version_info__