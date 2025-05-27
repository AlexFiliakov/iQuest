"""
Version information for Apple Health Monitor
"""

__version__ = "0.1.0"
__version_info__ = tuple(int(x) for x in __version__.split('.'))

def get_version():
    """Return the version string"""
    return __version__

def get_version_info():
    """Return version as a tuple of integers"""
    return __version_info__