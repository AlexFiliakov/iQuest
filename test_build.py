#!/usr/bin/env python3
"""Test script to verify build process functionality."""

import subprocess
import sys
import os
from pathlib import Path

def test_build_script():
    """Test the build script execution."""
    print("Testing build script...")
    
    # Test 1: Check if build.py exists
    if not Path('build.py').exists():
        print("❌ build.py not found")
        return False
    print("✅ build.py exists")
    
    # Test 2: Test build script help
    try:
        result = subprocess.run([sys.executable, 'build.py', '--help'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ build.py --help works")
        else:
            print("❌ build.py --help failed")
            return False
    except Exception as e:
        print(f"❌ Error running build.py: {e}")
        return False
    
    # Test 3: Check build configuration
    if Path('build_config.json').exists():
        print("✅ build_config.json exists")
    else:
        print("⚠️  build_config.json not found (will be created on first run)")
    
    # Test 4: Check pyinstaller.spec
    if Path('pyinstaller.spec').exists():
        print("✅ pyinstaller.spec exists")
    else:
        print("❌ pyinstaller.spec not found")
        return False
    
    # Test 5: Check version.py
    version_file = Path('src/version.py')
    if version_file.exists():
        print("✅ src/version.py exists")
        # Extract version
        try:
            exec_globals = {}
            with open(version_file, 'r') as f:
                exec(f.read(), exec_globals)
            version = exec_globals.get('__version__', 'Unknown')
            print(f"   Version: {version}")
        except Exception as e:
            print(f"⚠️  Could not extract version: {e}")
    else:
        print("❌ src/version.py not found")
        return False
    
    # Test 6: Check GitHub Actions workflow
    workflow_file = Path('.github/workflows/build-release.yml')
    if workflow_file.exists():
        print("✅ GitHub Actions workflow exists")
    else:
        print("❌ GitHub Actions workflow not found")
        return False
    
    # Test 7: Check for required directories
    required_dirs = ['src', 'assets', 'docs']
    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory not found")
            return False
    
    # Test 8: Check for icon file
    icon_file = Path('assets/icon.ico')
    if icon_file.exists():
        print("✅ Icon file exists")
    else:
        print("⚠️  Icon file not found (build will use default)")
    
    return True

def test_dependencies():
    """Test if build dependencies are available."""
    print("\nTesting build dependencies...")
    
    # Test PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} is installed")
    except ImportError:
        print("❌ PyInstaller not installed")
        print("   Install with: pip install pyinstaller")
    
    # Test PyQt6
    try:
        import PyQt6
        print("✅ PyQt6 is installed")
    except ImportError:
        print("❌ PyQt6 not installed")
        print("   Install with: pip install PyQt6")
    
    # Test pandas
    try:
        import pandas
        print(f"✅ pandas {pandas.__version__} is installed")
    except ImportError:
        print("❌ pandas not installed")
        print("   Install with: pip install pandas")
    
    # Test matplotlib
    try:
        import matplotlib
        print(f"✅ matplotlib {matplotlib.__version__} is installed")
    except ImportError:
        print("❌ matplotlib not installed")
        print("   Install with: pip install matplotlib")

def main():
    """Run all tests."""
    print("Apple Health Monitor - Build System Test")
    print("=" * 50)
    
    # Test build script
    if not test_build_script():
        print("\n❌ Build script tests failed")
        sys.exit(1)
    
    # Test dependencies
    test_dependencies()
    
    print("\n" + "=" * 50)
    print("Build system test completed!")
    print("\nTo perform a test build, run:")
    print("  python build.py --debug")
    print("\nTo create all packages, run:")
    print("  python build.py --package")

if __name__ == '__main__':
    main()