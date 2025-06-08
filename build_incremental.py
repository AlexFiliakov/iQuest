#!/usr/bin/env python3
"""
Quick incremental build script for Apple Health Monitor Dashboard
Uses incremental builds by default for faster development iterations
"""

import subprocess
import sys
import os

def main():
    """Run incremental build with common options."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Build command with incremental flag
    cmd = [sys.executable, "build.py", "--incremental"]
    
    # Add any command line arguments passed to this script
    cmd.extend(sys.argv[1:])
    
    print("Running incremental build...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the build
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Incremental build completed successfully!")
        print("\nExecutable location: build/dist/HealthMonitor/HealthMonitor.exe")
        print("\nTip: Use 'python build_incremental.py --all-formats' to build all distribution formats")
    else:
        print("\n❌ Build failed!")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()