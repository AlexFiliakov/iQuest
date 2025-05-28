#!/usr/bin/env python3
"""
Script to migrate from TestDataGenerator to new generator system.
"""

import ast
import os
import sys
from pathlib import Path
import argparse
import re


def migrate_test_file(filepath: Path) -> bool:
    """Migrate single test file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace imports
        content = content.replace(
            'from tests.utils import TestDataGenerator',
            'from tests.generators import HealthDataGenerator'
        )
        content = content.replace(
            'from tests.test_data_generator import TestDataGenerator',
            'from tests.generators import HealthDataGenerator'
        )
        content = content.replace(
            'from test_data_generator import TestDataGenerator',
            'from tests.generators import HealthDataGenerator'
        )
        
        # Replace class names
        content = content.replace(
            'TestDataGenerator(',
            'HealthDataGenerator('
        )
        
        # Update method calls
        replacements = {
            'generate_test_data': 'generate',
            'create_test_dataframe': 'create_health_dataframe',
            'generate_synthetic_data': 'generate',
            'create_test_database_data': 'create_sample_datasets'
        }
        
        for old, new in replacements.items():
            content = re.sub(rf'\.{old}\(', f'.{new}(', content)
        
        # Update fixture imports if needed
        if 'HealthDataFixtures' in content and 'from tests.fixtures import HealthDataFixtures' not in content:
            # Add import at the top after other imports
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_index = i
            
            lines.insert(import_index + 1, 'from tests.fixtures import HealthDataFixtures')
            content = '\n'.join(lines)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✓ Migrated: {filepath}")
            return True
        else:
            print(f"  No changes needed: {filepath}")
            return False
            
    except Exception as e:
        print(f"✗ Error migrating {filepath}: {e}")
        return False


def find_test_files(root_dir: Path) -> list[Path]:
    """Find all Python test files in the project."""
    test_files = []
    
    # Look for test files
    for pattern in ['test_*.py', '*_test.py']:
        test_files.extend(root_dir.glob(f'**/{pattern}'))
    
    # Also check specific directories
    test_dirs = ['tests', 'test']
    for test_dir in test_dirs:
        test_path = root_dir / test_dir
        if test_path.exists():
            test_files.extend(test_path.glob('**/*.py'))
    
    # Remove duplicates and return
    return list(set(test_files))


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description='Migrate TestDataGenerator to new generator system'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=Path.cwd(),
        help='Root path to search for test files (default: current directory)'
    )
    
    args = parser.parse_args()
    
    print(f"Searching for test files in: {args.path}")
    test_files = find_test_files(args.path)
    
    print(f"Found {len(test_files)} test files")
    
    if args.dry_run:
        print("\n--- DRY RUN MODE ---")
        for filepath in test_files:
            with open(filepath, 'r') as f:
                content = f.read()
            if 'TestDataGenerator' in content:
                print(f"Would migrate: {filepath}")
    else:
        migrated_count = 0
        for filepath in test_files:
            if migrate_test_file(filepath):
                migrated_count += 1
        
        print(f"\nMigration complete: {migrated_count} files updated")
        
        if migrated_count > 0:
            print("\nNext steps:")
            print("1. Run tests to ensure everything works")
            print("2. Review changes with git diff")
            print("3. Update any custom generator usage")


if __name__ == '__main__':
    main()