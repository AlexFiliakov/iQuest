#!/usr/bin/env python3
"""
Coverage Gap Analysis Tool
Compares coverage between original and consolidated test suites
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_coverage_data(json_path: str) -> Dict:
    """Load coverage data from JSON report."""
    with open(json_path, 'r') as f:
        return json.load(f)


def analyze_coverage_gaps(original_data: Dict, consolidated_data: Dict) -> Dict:
    """Analyze gaps between original and consolidated coverage."""
    gaps = {
        'coverage_decreased': [],
        'coverage_increased': [],
        'coverage_maintained': [],
        'new_files': [],
        'removed_files': []
    }
    
    original_files = set(original_data['files'].keys())
    consolidated_files = set(consolidated_data['files'].keys())
    
    # Files only in original
    gaps['removed_files'] = list(original_files - consolidated_files)
    
    # Files only in consolidated  
    gaps['new_files'] = list(consolidated_files - original_files)
    
    # Files in both - compare coverage
    common_files = original_files & consolidated_files
    
    for file_path in common_files:
        orig_coverage = original_data['files'][file_path]['summary']['percent_covered']
        cons_coverage = consolidated_data['files'][file_path]['summary']['percent_covered']
        
        if orig_coverage > cons_coverage:
            gaps['coverage_decreased'].append({
                'file': file_path,
                'original': orig_coverage,
                'consolidated': cons_coverage,
                'decrease': orig_coverage - cons_coverage
            })
        elif cons_coverage > orig_coverage:
            gaps['coverage_increased'].append({
                'file': file_path,
                'original': orig_coverage,
                'consolidated': cons_coverage,
                'increase': cons_coverage - orig_coverage
            })
        else:
            gaps['coverage_maintained'].append({
                'file': file_path,
                'coverage': orig_coverage
            })
    
    return gaps


def generate_report(gaps: Dict, original_total: float, consolidated_total: float) -> str:
    """Generate a human-readable coverage gap report."""
    report = []
    report.append("COVERAGE GAP ANALYSIS REPORT")
    report.append("=" * 50)
    report.append("")
    
    report.append(f"Overall Coverage:")
    report.append(f"  Original Test Suite:    {original_total:.1f}%")
    report.append(f"  Consolidated Test Suite: {consolidated_total:.1f}%")
    report.append(f"  Overall Change:         {consolidated_total - original_total:+.1f}%")
    report.append("")
    
    if gaps['coverage_decreased']:
        report.append("FILES WITH DECREASED COVERAGE:")
        report.append("-" * 35)
        for item in sorted(gaps['coverage_decreased'], key=lambda x: x['decrease'], reverse=True):
            report.append(f"  {item['file']}")
            report.append(f"    {item['original']:.1f}% → {item['consolidated']:.1f}% (-{item['decrease']:.1f}%)")
        report.append("")
    
    if gaps['coverage_increased']:
        report.append("FILES WITH INCREASED COVERAGE:")
        report.append("-" * 35)
        for item in sorted(gaps['coverage_increased'], key=lambda x: x['increase'], reverse=True):
            report.append(f"  {item['file']}")
            report.append(f"    {item['original']:.1f}% → {item['consolidated']:.1f}% (+{item['increase']:.1f}%)")
        report.append("")
    
    if gaps['coverage_maintained']:
        report.append(f"FILES WITH MAINTAINED COVERAGE: {len(gaps['coverage_maintained'])} files")
        report.append("")
    
    if gaps['removed_files']:
        report.append("FILES NO LONGER TESTED:")
        report.append("-" * 25)
        for file_path in gaps['removed_files']:
            report.append(f"  {file_path}")
        report.append("")
    
    if gaps['new_files']:
        report.append("NEW FILES BEING TESTED:")
        report.append("-" * 25)
        for file_path in gaps['new_files']:
            report.append(f"  {file_path}")
        report.append("")
    
    # Critical gaps analysis
    critical_gaps = [item for item in gaps['coverage_decreased'] if item['decrease'] > 10]
    if critical_gaps:
        report.append("CRITICAL COVERAGE GAPS (>10% decrease):")
        report.append("-" * 40)
        for item in critical_gaps:
            report.append(f"  {item['file']}: -{item['decrease']:.1f}%")
        report.append("")
    
    return "\n".join(report)


def main():
    """Main function to run coverage gap analysis."""
    if len(sys.argv) != 3:
        print("Usage: python coverage_gap_analyzer.py <original_coverage.json> <consolidated_coverage.json>")
        sys.exit(1)
    
    original_path = sys.argv[1]
    consolidated_path = sys.argv[2]
    
    # Load coverage data
    original_data = load_coverage_data(original_path)
    consolidated_data = load_coverage_data(consolidated_path)
    
    # Analyze gaps
    gaps = analyze_coverage_gaps(original_data, consolidated_data)
    
    # Get overall totals
    original_total = original_data['totals']['percent_covered']
    consolidated_total = consolidated_data['totals']['percent_covered']
    
    # Generate report
    report = generate_report(gaps, original_total, consolidated_total)
    
    # Save report
    with open('coverage_gap_report.txt', 'w') as f:
        f.write(report)
    
    print(report)
    print(f"\nReport saved to coverage_gap_report.txt")


if __name__ == "__main__":
    main()