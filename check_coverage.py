#!/usr/bin/env python3
"""Quick coverage checker to identify modules below 90% coverage."""

import json
import sys

def analyze_coverage(coverage_file):
    """Analyze coverage and report modules below 90%."""
    with open(coverage_file, 'r') as f:
        data = json.load(f)
    
    # Get the files section
    files = data.get('files', {})
    
    low_coverage_modules = []
    total_lines = 0
    covered_lines = 0
    
    for filename, file_data in files.items():
        if not filename.startswith('src/'):
            continue
            
        summary = file_data.get('summary', {})
        percent_covered = summary.get('percent_covered', 0)
        num_statements = summary.get('num_statements', 0)
        missing_lines = summary.get('missing_lines', 0)
        
        total_lines += num_statements
        covered_lines += (num_statements - missing_lines)
        
        if percent_covered < 90:
            low_coverage_modules.append({
                'file': filename,
                'coverage': percent_covered,
                'statements': num_statements,
                'missing': missing_lines
            })
    
    # Sort by coverage percentage
    low_coverage_modules.sort(key=lambda x: x['coverage'])
    
    # Calculate overall coverage
    overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
    
    print(f"Overall Coverage: {overall_coverage:.1f}%")
    print(f"Total Lines: {total_lines}, Covered: {covered_lines}, Missing: {total_lines - covered_lines}")
    print(f"\nModules below 90% coverage ({len(low_coverage_modules)} files):\n")
    
    for module in low_coverage_modules[:20]:  # Show top 20
        print(f"{module['coverage']:5.1f}% - {module['file']} ({module['missing']} lines missing)")
    
    return overall_coverage, low_coverage_modules

if __name__ == "__main__":
    coverage_file = "coverage_analysis/current_coverage.json"
    overall, modules = analyze_coverage(coverage_file)
    
    if overall >= 90:
        print(f"\n✅ Goal achieved! Overall coverage is {overall:.1f}%")
        sys.exit(0)
    else:
        print(f"\n❌ Need to improve coverage from {overall:.1f}% to 90%")
        sys.exit(1)