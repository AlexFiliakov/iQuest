#!/usr/bin/env python3
"""Safe pytest runner with proper environment setup."""

import os
import sys
import subprocess

# Set environment variables
env = os.environ.copy()
env['QT_QPA_PLATFORM'] = 'offscreen'
env['QT_LOGGING_RULES'] = '*.debug=false'
env['PYTEST_QT_API'] = 'pyqt6'

# Run pytest with safe options
cmd = [
    sys.executable, '-m', 'pytest',
    '--tb=short',
    '--maxfail=5',
    '-v',
    '--no-header',
    'tests/',
    *sys.argv[1:]  # Pass through any additional arguments
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
