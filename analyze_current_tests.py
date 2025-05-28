#!/usr/bin/env python3
"""
Analyze current test structure to understand duplicates and consolidation opportunities.
"""

import os
import ast
import sys
from collections import defaultdict
from pathlib import Path

def extract_test_functions(file_path):
    """Extract test function names from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                functions.append(node.name)
        
        return functions
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def analyze_test_files():
    """Analyze all test files for duplicates and patterns."""
    test_dir = Path('tests')
    if not test_dir.exists():
        print("Tests directory not found")
        return
    
    all_functions = defaultdict(list)  # function_name -> [file_paths]
    file_function_counts = {}  # file_path -> function_count
    
    # Walk through all test files
    for py_file in test_dir.rglob('*.py'):
        if py_file.name.startswith('test_'):
            functions = extract_test_functions(py_file)
            file_function_counts[str(py_file)] = len(functions)
            
            for func in functions:
                all_functions[func].append(str(py_file))
    
    # Find duplicates
    duplicates = {func: files for func, files in all_functions.items() if len(files) > 1}
    
    # Statistics
    total_files = len(file_function_counts)
    total_functions = sum(file_function_counts.values())
    duplicate_instances = sum(len(files) - 1 for files in duplicates.values())
    
    print("=== CURRENT TEST ANALYSIS ===")
    print(f"Total test files: {total_files}")
    print(f"Total test functions: {total_functions}")
    print(f"Duplicate function names: {len(duplicates)}")
    print(f"Duplicate instances: {duplicate_instances}")
    print()
    
    print("=== TOP 10 FILES BY FUNCTION COUNT ===")
    sorted_files = sorted(file_function_counts.items(), key=lambda x: x[1], reverse=True)
    for file_path, count in sorted_files[:10]:
        print(f"{count:3d} functions: {file_path}")
    print()
    
    if duplicates:
        print("=== DUPLICATE FUNCTIONS (first 10) ===")
        for i, (func, files) in enumerate(list(duplicates.items())[:10]):
            print(f"{i+1}. {func} appears in {len(files)} files:")
            for file_path in files:
                print(f"   - {file_path}")
        print()
    
    # Look for similar patterns
    function_patterns = defaultdict(list)
    for func in all_functions.keys():
        # Group by common patterns
        if 'empty' in func and ('data' in func or 'input' in func):
            function_patterns['empty_data_tests'].append(func)
        elif 'calculate' in func and 'statistics' in func:
            function_patterns['calculate_statistics_tests'].append(func)
        elif 'init' in func or 'initialization' in func:
            function_patterns['initialization_tests'].append(func)
        elif 'error' in func or 'exception' in func:
            function_patterns['error_handling_tests'].append(func)
    
    if function_patterns:
        print("=== SIMILAR PATTERNS (consolidation candidates) ===")
        for pattern, functions in function_patterns.items():
            if len(functions) > 3:  # Only show patterns with multiple instances
                print(f"{pattern}: {len(functions)} functions")
                for func in functions[:5]:  # Show first 5
                    print(f"   - {func}")
                if len(functions) > 5:
                    print(f"   ... and {len(functions) - 5} more")
                print()

if __name__ == "__main__":
    analyze_test_files()