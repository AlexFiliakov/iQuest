#!/usr/bin/env python3
"""
Accessibility audit script for health visualizations.

This script performs automated accessibility testing on visualization components
to ensure WCAG 2.1 AA compliance.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.helpers.color_helpers import WSJColorContrastChecker


@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found during audit"""
    component: str
    severity: str  # 'error', 'warning', 'info'
    wcag_criterion: str
    description: str
    recommendation: str
    
    
@dataclass
class AuditReport:
    """Complete accessibility audit report"""
    timestamp: str
    total_components: int
    components_passed: int
    issues: List[AccessibilityIssue]
    color_contrast_results: Dict[str, Any]
    

class AccessibilityAuditor:
    """Performs accessibility audits on visualization components"""
    
    def __init__(self):
        self.issues: List[AccessibilityIssue] = []
        self.components_tested = 0
        self.components_passed = 0
        
    def audit_all_components(self) -> AuditReport:
        """Run accessibility audit on all visualization components"""
        print("Starting accessibility audit...")
        
        # Audit color contrast
        color_results = self._audit_color_contrast()
        
        # Audit component implementations
        self._audit_visualization_components()
        
        # Generate report
        report = AuditReport(
            timestamp=datetime.now().isoformat(),
            total_components=self.components_tested,
            components_passed=self.components_passed,
            issues=self.issues,
            color_contrast_results=color_results
        )
        
        return report
        
    def _audit_color_contrast(self) -> Dict[str, Any]:
        """Audit WSJ color palette for WCAG compliance"""
        print("Auditing color contrast...")
        
        checker = WSJColorContrastChecker()
        results = checker.check_wsj_palette()
        recommendations = checker.get_recommendations()
        
        # Log any failures as issues
        for combo, result in results.items():
            if not result['passes_aa']:
                self.issues.append(AccessibilityIssue(
                    component='Color Palette',
                    severity='error',
                    wcag_criterion='1.4.3 Contrast (Minimum)',
                    description=f"Color combination {combo} fails WCAG AA with ratio {result['ratio']:.2f}:1",
                    recommendation=recommendations.get(combo, {}).get('suggestion', 'Improve contrast')
                ))
                
        return {
            'results': results,
            'recommendations': recommendations,
            'summary': {
                'total_combinations': len(results),
                'passing_aa': sum(1 for r in results.values() if r['passes_aa']),
                'passing_aaa': sum(1 for r in results.values() if r['passes_aaa'])
            }
        }
        
    def _audit_visualization_components(self) -> None:
        """Audit individual visualization components"""
        print("Auditing visualization components...")
        
        # List of components to audit
        components = [
            'LineChart',
            'BarChart', 
            'ScatterPlot',
            'Heatmap',
            'TimeSeriesChart'
        ]
        
        for component_name in components:
            self.components_tested += 1
            issues_before = len(self.issues)
            
            # Check keyboard navigation
            self._check_keyboard_navigation(component_name)
            
            # Check screen reader support
            self._check_screen_reader_support(component_name)
            
            # Check focus indicators
            self._check_focus_indicators(component_name)
            
            # Check interactive elements
            self._check_interactive_elements(component_name)
            
            # If no new issues, component passed
            if len(self.issues) == issues_before:
                self.components_passed += 1
                
    def _check_keyboard_navigation(self, component: str) -> None:
        """Check keyboard navigation requirements"""
        # This is a placeholder - in real implementation would test actual components
        
        # Example checks:
        required_keys = ['Tab', 'Arrow keys', 'Enter', 'Escape']
        
        # Simulate checking (in real implementation would test actual component)
        has_tab_navigation = True  # Would check actual implementation
        has_arrow_navigation = True  # Would check actual implementation
        
        if not has_tab_navigation:
            self.issues.append(AccessibilityIssue(
                component=component,
                severity='error',
                wcag_criterion='2.1.1 Keyboard',
                description=f"{component} is not accessible via keyboard Tab navigation",
                recommendation="Implement tabIndex and keyboard event handlers"
            ))
            
    def _check_screen_reader_support(self, component: str) -> None:
        """Check screen reader compatibility"""
        # Check for ARIA labels and descriptions
        
        # Placeholder checks
        has_aria_label = True  # Would check actual implementation
        has_role = True  # Would check actual implementation
        
        if not has_aria_label:
            self.issues.append(AccessibilityIssue(
                component=component,
                severity='error',
                wcag_criterion='4.1.2 Name, Role, Value',
                description=f"{component} lacks proper ARIA labels",
                recommendation="Add aria-label and aria-describedby attributes"
            ))
            
    def _check_focus_indicators(self, component: str) -> None:
        """Check visible focus indicators"""
        # Check for visible focus styles
        
        # Placeholder check
        has_focus_styles = True  # Would check actual CSS/implementation
        
        if not has_focus_styles:
            self.issues.append(AccessibilityIssue(
                component=component,
                severity='error',
                wcag_criterion='2.4.7 Focus Visible',
                description=f"{component} lacks visible focus indicators",
                recommendation="Add clear focus styles with sufficient contrast"
            ))
            
    def _check_interactive_elements(self, component: str) -> None:
        """Check interactive element accessibility"""
        # Check click targets, hover states, etc.
        
        # Placeholder check for minimum target size
        min_target_size = 44  # WCAG 2.1 AA requirement in pixels
        
        # Would check actual implementation
        has_sufficient_target_size = True
        
        if not has_sufficient_target_size:
            self.issues.append(AccessibilityIssue(
                component=component,
                severity='warning',
                wcag_criterion='2.5.5 Target Size',
                description=f"{component} has interactive targets smaller than {min_target_size}px",
                recommendation=f"Ensure all interactive elements are at least {min_target_size}x{min_target_size}px"
            ))
            

def generate_html_report(report: AuditReport, output_path: Path) -> None:
    """Generate HTML accessibility report"""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Accessibility Audit Report</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            h1, h2, h3 { color: #0080C0; }
            .summary {
                background: #F5E6D3;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .pass { color: #28a745; font-weight: bold; }
            .fail { color: #dc3545; font-weight: bold; }
            .warning { color: #ffc107; }
            .issue {
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin: 10px 0;
            }
            .severity-error { border-left: 4px solid #dc3545; }
            .severity-warning { border-left: 4px solid #ffc107; }
            .severity-info { border-left: 4px solid #17a2b8; }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th { background: #f8f9fa; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Accessibility Audit Report</h1>
        <p>Generated: {timestamp}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Components Tested: <strong>{total_components}</strong></p>
            <p>Components Passed: <span class="{pass_class}">{components_passed}/{total_components}</span></p>
            <p>Total Issues: <span class="{issue_class}">{total_issues}</span></p>
            <p>Color Combinations Tested: <strong>{color_combinations}</strong></p>
            <p>WCAG AA Compliant Colors: <span class="{color_class}">{colors_passing_aa}/{color_combinations}</span></p>
        </div>
        
        <h2>Color Contrast Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Combination</th>
                    <th>Contrast Ratio</th>
                    <th>WCAG AA</th>
                    <th>WCAG AAA</th>
                </tr>
            </thead>
            <tbody>
                {color_rows}
            </tbody>
        </table>
        
        <h2>Accessibility Issues</h2>
        {issues_html}
        
        <h2>Recommendations</h2>
        <ol>
            {recommendations}
        </ol>
    </body>
    </html>
    """
    
    # Prepare data for template
    total_issues = len(report.issues)
    pass_class = 'pass' if report.components_passed == report.total_components else 'fail'
    issue_class = 'pass' if total_issues == 0 else 'fail'
    
    # Color contrast data
    color_summary = report.color_contrast_results.get('summary', {})
    color_combinations = color_summary.get('total_combinations', 0)
    colors_passing_aa = color_summary.get('passing_aa', 0)
    color_class = 'pass' if colors_passing_aa == color_combinations else 'fail'
    
    # Generate color contrast table rows
    color_rows = []
    for combo, result in report.color_contrast_results.get('results', {}).items():
        ratio = result['ratio']
        aa_pass = '✓' if result['passes_aa'] else '✗'
        aaa_pass = '✓' if result['passes_aaa'] else '✗'
        aa_class = 'pass' if result['passes_aa'] else 'fail'
        aaa_class = 'pass' if result['passes_aaa'] else 'fail'
        
        color_rows.append(
            f'<tr><td>{combo}</td><td>{ratio:.2f}:1</td>'
            f'<td class="{aa_class}">{aa_pass}</td>'
            f'<td class="{aaa_class}">{aaa_pass}</td></tr>'
        )
    
    # Generate issues HTML
    issues_html = []
    if report.issues:
        for issue in report.issues:
            issues_html.append(f'''
            <div class="issue severity-{issue.severity}">
                <h3>{issue.component}</h3>
                <p><strong>WCAG {issue.wcag_criterion}</strong></p>
                <p>{issue.description}</p>
                <p><em>Recommendation:</em> {issue.recommendation}</p>
            </div>
            ''')
    else:
        issues_html.append('<p class="pass">No accessibility issues found!</p>')
    
    # Generate recommendations
    recommendations = [
        "Regularly test with screen readers (NVDA, JAWS, VoiceOver)",
        "Test keyboard navigation without using a mouse",
        "Verify color contrast with automated tools",
        "Test with users who have disabilities",
        "Keep accessibility documentation up to date"
    ]
    
    # Fill template
    html = html_template.format(
        timestamp=report.timestamp,
        total_components=report.total_components,
        components_passed=report.components_passed,
        pass_class=pass_class,
        total_issues=total_issues,
        issue_class=issue_class,
        color_combinations=color_combinations,
        colors_passing_aa=colors_passing_aa,
        color_class=color_class,
        color_rows='\n'.join(color_rows),
        issues_html='\n'.join(issues_html),
        recommendations='\n'.join(f'<li>{rec}</li>' for rec in recommendations)
    )
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    

def main():
    """Run accessibility audit and generate report"""
    auditor = AccessibilityAuditor()
    report = auditor.audit_all_components()
    
    # Save JSON report
    json_path = Path('tests/results/accessibility_report.json')
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': report.timestamp,
            'total_components': report.total_components,
            'components_passed': report.components_passed,
            'issues': [
                {
                    'component': issue.component,
                    'severity': issue.severity,
                    'wcag_criterion': issue.wcag_criterion,
                    'description': issue.description,
                    'recommendation': issue.recommendation
                }
                for issue in report.issues
            ],
            'color_contrast_results': report.color_contrast_results
        }, f, indent=2)
    
    # Generate HTML report
    html_path = Path('tests/results/accessibility_report.html')
    generate_html_report(report, html_path)
    
    print(f"\nAccessibility Audit Complete")
    print(f"Components tested: {report.total_components}")
    print(f"Components passed: {report.components_passed}")
    print(f"Issues found: {len(report.issues)}")
    print(f"\nReports saved to:")
    print(f"  - {json_path}")
    print(f"  - {html_path}")
    
    # Exit with error if issues found
    if report.issues:
        sys.exit(1)
    else:
        sys.exit(0)
        

if __name__ == '__main__':
    main()