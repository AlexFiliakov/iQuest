#!/usr/bin/env python3
"""Verify that all test collection errors have been resolved."""

import subprocess
import sys

def run_test_collection():
    """Run pytest collection to check for errors."""
    print("Running pytest collection to verify fixes...")
    print("=" * 80)
    
    try:
        # Run pytest with collection only
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "tests/"],
            capture_output=True,
            text=True
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print("\nReturn code:", result.returncode)
        
        # Check for specific error patterns
        errors = []
        
        if "ModuleNotFoundError: No module named 'PySide6'" in result.stderr:
            errors.append("Still have PySide6 import errors")
            
        if "'timeout' not found in `markers` configuration option" in result.stderr:
            errors.append("Timeout marker still missing")
            
        if "ImportError" in result.stderr:
            errors.append("Import errors still present")
            
        if result.returncode != 0:
            errors.append(f"pytest returned non-zero exit code: {result.returncode}")
            
        if errors:
            print("\n❌ ERRORS FOUND:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("\n✅ All test collection errors appear to be fixed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error running pytest: {e}")
        return False

if __name__ == "__main__":
    success = run_test_collection()
    sys.exit(0 if success else 1)