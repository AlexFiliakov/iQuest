#!/usr/bin/env python3
"""Extract version information for build processes."""

import sys
import os
import re

def extract_version():
    """Extract version from src/version.py."""
    version_file = os.path.join('src', 'version.py')
    
    if not os.path.exists(version_file):
        print("0.1.0")
        return
    
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Find version string
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        print(match.group(1))
    else:
        print("0.1.0")

if __name__ == '__main__':
    extract_version()