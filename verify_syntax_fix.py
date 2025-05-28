#!/usr/bin/env python3
"""Verify the syntax error fix in enhanced_line_chart.py"""

import ast
import sys

def check_file_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the file as AST
        ast.parse(source)
        print(f"✅ {filepath} - Syntax is valid!")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath} - Syntax Error:")
        print(f"   Line {e.lineno}: {e.msg}")
        print(f"   Text: {e.text}")
        print(f"   Offset: {' ' * (e.offset - 1) if e.offset else ''}^")
        return False
    except Exception as e:
        print(f"❌ {filepath} - Error: {e}")
        return False

def main():
    files_to_check = [
        "src/ui/charts/enhanced_line_chart.py",
        "src/ui/charts/line_chart.py",
        "src/ui/charts/base_chart.py",
        "src/ui/charts/chart_config.py"
    ]
    
    all_valid = True
    print("Checking syntax of chart files...")
    print("=" * 80)
    
    for filepath in files_to_check:
        if not check_file_syntax(filepath):
            all_valid = False
    
    print("=" * 80)
    if all_valid:
        print("\n✅ All files have valid syntax!")
    else:
        print("\n❌ Some files have syntax errors")
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())