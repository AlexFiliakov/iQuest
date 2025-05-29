#!/usr/bin/env python3
"""Clean test artifacts that might cause Windows fatal exceptions."""

import os
import shutil
import sys
from pathlib import Path

def clean_test_artifacts():
    """Remove test artifacts and caches."""
    root_dir = Path(__file__).parent
    
    # Patterns to clean
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "**/*.pyd",
        "**/pytest_cache",
        "**/.pytest_cache",
        "**/.coverage",
        "**/htmlcov",
        "**/*.orig",
        "**/.hypothesis"
    ]
    
    cleaned = []
    
    for pattern in patterns:
        for path in root_dir.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                cleaned.append(str(path))
            elif path.is_file():
                path.unlink()
                cleaned.append(str(path))
    
    # Clean specific test database files
    test_db_pattern = root_dir / "tests" / "**" / "*.db"
    for db_file in test_db_pattern.glob("*.db"):
        if db_file.is_file():
            db_file.unlink()
            cleaned.append(str(db_file))
    
    print(f"Cleaned {len(cleaned)} artifacts:")
    for item in cleaned[:10]:  # Show first 10
        print(f"  - {item}")
    if len(cleaned) > 10:
        print(f"  ... and {len(cleaned) - 10} more")
    
    return len(cleaned)

if __name__ == "__main__":
    count = clean_test_artifacts()
    print(f"\nTotal artifacts cleaned: {count}")
    sys.exit(0)