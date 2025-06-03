#!/usr/bin/env python3
"""
Build script for Apple Health Monitor Dashboard
Creates Windows executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse

def clean_build_artifacts():
    """Remove previous build artifacts."""
    print("Cleaning previous build artifacts...")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"  Removing {dir_name}/")
            shutil.rmtree(dir_name)
    
    # Remove .spec file if it exists (we'll use our custom one)
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec') and f != 'pyinstaller.spec']
    for spec_file in spec_files:
        print(f"  Removing {spec_file}")
        os.remove(spec_file)

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = ['PyInstaller', 'PyQt6', 'pandas', 'matplotlib']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"  ✓ {package} is installed")
        except ImportError:
            print(f"  ✗ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print("\nError: Missing required packages:")
        print(f"Please install them with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def build_executable(debug=False, clean=True):
    """Build the executable using PyInstaller."""
    
    if clean:
        clean_build_artifacts()
    
    if not check_dependencies():
        return False
    
    print("\nBuilding executable with PyInstaller...")
    
    # Build command
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        'pyinstaller.spec',
        '--noconfirm',  # Don't ask for confirmation
    ]
    
    if debug:
        cmd.append('--log-level=DEBUG')
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True)
        
        print("\nBuild completed successfully!")
        print(f"Executable location: dist/HealthMonitor/HealthMonitor.exe")
        
        # Check output size
        exe_path = Path('dist/HealthMonitor/HealthMonitor.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable size: {size_mb:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\nError: Build failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\nError during build: {e}")
        return False

def test_executable():
    """Run basic tests on the built executable."""
    print("\nTesting executable...")
    
    exe_path = Path('dist/HealthMonitor/HealthMonitor.exe')
    
    if not exe_path.exists():
        print("Error: Executable not found. Build may have failed.")
        return False
    
    # Test 1: Check if executable runs with --version
    print("  Testing --version flag...")
    try:
        result = subprocess.run(
            [str(exe_path), '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"    ✓ Version output: {result.stdout.strip()}")
        else:
            print(f"    ✗ Failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    print("\nAll tests passed!")
    return True

def package_distribution(format='zip'):
    """Package the distribution for release."""
    print(f"\nPackaging distribution as {format}...")
    
    dist_dir = Path('dist/HealthMonitor')
    if not dist_dir.exists():
        print("Error: Distribution directory not found. Build first.")
        return False
    
    # Get version from version.py
    version = "0.1.0"  # Default
    try:
        version_file = Path('src/version.py')
        if version_file.exists():
            with open(version_file, 'r') as f:
                for line in f:
                    if line.startswith('__version__'):
                        version = line.split('=')[1].strip().strip('"\'')
                        break
    except:
        pass
    
    output_name = f"HealthMonitor-{version}-Windows"
    
    if format == 'zip':
        # Create ZIP file
        output_file = f"{output_name}.zip"
        print(f"  Creating {output_file}...")
        shutil.make_archive(output_name, 'zip', 'dist', 'HealthMonitor')
        print(f"  ✓ Created {output_file}")
    
    return True

def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description='Build Apple Health Monitor Dashboard')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--no-clean', action='store_true', help='Skip cleaning build artifacts')
    parser.add_argument('--test', action='store_true', help='Test the built executable')
    parser.add_argument('--package', action='store_true', help='Package for distribution')
    
    args = parser.parse_args()
    
    print("Apple Health Monitor Dashboard - Build Script")
    print("=" * 50)
    
    # Build executable
    if not build_executable(debug=args.debug, clean=not args.no_clean):
        print("\nBuild failed!")
        sys.exit(1)
    
    # Test if requested
    if args.test:
        if not test_executable():
            print("\nTests failed!")
            sys.exit(1)
    
    # Package if requested
    if args.package:
        if not package_distribution():
            print("\nPackaging failed!")
            sys.exit(1)
    
    print("\nBuild process completed successfully!")
    print("\nTo run the executable:")
    print("  dist\\HealthMonitor\\HealthMonitor.exe")
    
    print("\nTo create a packaged release:")
    print("  python build.py --package")

if __name__ == '__main__':
    main()