#!/usr/bin/env python3
"""Minimal build script for quick testing."""

import subprocess
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run PyInstaller directly with the spec file
cmd = [
    sys.executable,
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    'pyinstaller.spec'
]

print("Running minimal build...")
print(" ".join(cmd))

try:
    result = subprocess.run(cmd, check=True)
    print("\nBuild completed successfully!")
    print("Executable should be at: build/dist/HealthMonitor/HealthMonitor.exe")
except subprocess.CalledProcessError as e:
    print(f"\nBuild failed with error: {e}")
    sys.exit(1)