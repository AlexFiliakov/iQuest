"""
Validation script to ensure packaging test infrastructure is properly set up.

This script checks that all required files and dependencies are in place
for running packaging tests.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Tuple


def check_file_exists(file_path: str, description: str) -> Tuple[bool, str]:
    """Check if a required file exists.
    
    Args:
        file_path: Path to check
        description: Description of the file
        
    Returns:
        Tuple of (success, message)
    """
    path = Path(file_path)
    if path.exists():
        return True, f"✓ {description}: {file_path}"
    else:
        return False, f"✗ {description}: {file_path} (NOT FOUND)"


def check_module_available(module_name: str) -> Tuple[bool, str]:
    """Check if a Python module is available.
    
    Args:
        module_name: Name of module to check
        
    Returns:
        Tuple of (success, message)
    """
    try:
        importlib.import_module(module_name)
        return True, f"✓ Module '{module_name}' available"
    except ImportError:
        return False, f"✗ Module '{module_name}' not available (install with: pip install {module_name})"


def validate_test_infrastructure():
    """Validate that all test infrastructure is in place."""
    print("=" * 60)
    print("PACKAGING TEST INFRASTRUCTURE VALIDATION")
    print("=" * 60)
    
    checks = []
    
    # Check test files exist
    test_files = [
        ("packaging_test_checklist.md", "Manual test checklist"),
        ("test_packaged_app.py", "Automated test suite"),
        ("setup_test_environment.py", "Environment setup script"),
        ("performance_benchmarks.py", "Performance benchmark suite"),
        ("packaging_issues_template.md", "Issue tracking template"),
        ("README.md", "Documentation"),
        ("validate_test_setup.py", "This validation script"),
    ]
    
    print("\nChecking test files:")
    for file_name, description in test_files:
        file_path = Path(__file__).parent / file_name
        success, message = check_file_exists(file_path, description)
        print(f"  {message}")
        checks.append(success)
    
    # Check required Python modules
    required_modules = [
        "psutil",  # For process monitoring
        "PyQt6",   # For the application itself
    ]
    
    print("\nChecking Python dependencies:")
    for module in required_modules:
        success, message = check_module_available(module)
        print(f"  {message}")
        checks.append(success)
    
    # Check optional but recommended modules
    optional_modules = [
        "pywin32",  # For Windows-specific testing
    ]
    
    print("\nChecking optional dependencies:")
    for module in optional_modules:
        success, message = check_module_available(module)
        print(f"  {message}")
        # Don't add to checks as these are optional
    
    # Check if we're on Windows
    print("\nChecking platform:")
    if sys.platform == "win32":
        print("  ✓ Running on Windows")
        checks.append(True)
    else:
        print("  ⚠ Not running on Windows - packaging tests require Windows")
        checks.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    print(f"\nTotal checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    
    if all(checks):
        print("\n✓ All validation checks passed!")
        print("\nNext steps:")
        print("1. Run setup_test_environment.py to prepare test environment")
        print("2. Build/obtain packaged executables")
        print("3. Run automated tests with test_packaged_app.py")
        print("4. Follow manual test checklist")
        return True
    else:
        print("\n✗ Some validation checks failed!")
        print("\nPlease address the issues above before running tests.")
        print("\nCommon fixes:")
        print("- Install missing modules: pip install psutil pywin32")
        print("- Ensure you're running on Windows for packaging tests")
        print("- Check that all test files are present")
        return False


def check_executable_exists():
    """Check if any packaged executables are available for testing."""
    print("\nChecking for packaged executables:")
    
    common_locations = [
        "dist/AppleHealthDashboard.exe",
        "build/AppleHealthDashboard.exe",
        "../../../dist/AppleHealthDashboard.exe",
        "../../../build/AppleHealthDashboard.exe",
    ]
    
    found = False
    for location in common_locations:
        path = Path(location)
        if path.exists():
            print(f"  ✓ Found executable: {path.absolute()}")
            found = True
            
    if not found:
        print("  ⚠ No packaged executables found")
        print("  Build the application first using PyInstaller")
        

def main():
    """Main entry point."""
    # Run validation
    success = validate_test_infrastructure()
    
    # Check for executables
    check_executable_exists()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()