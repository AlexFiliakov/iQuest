#!/usr/bin/env python3
"""
Test Coverage Analysis Tool

Analyzes test files to identify duplicates, overlapping coverage,
and consolidation opportunities.
"""

import ast
import os
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import re


class TestAnalyzer:
    """Analyzes test files for coverage overlap and duplication."""
    
    def __init__(self, test_dir: str = "tests"):
        self.test_dir = Path(test_dir)
        self.test_map = defaultdict(list)
        self.duplicate_tests = []
        self.coverage_map = {}
        self.test_files = []
        
    def analyze_all_tests(self):
        """Analyze all test files in the test directory."""
        print(f"Analyzing tests in {self.test_dir}")
        
        # Find all test files
        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.is_file():
                self.test_files.append(test_file)
                try:
                    self.analyze_test_file(test_file)
                except Exception as e:
                    print(f"Error analyzing {test_file}: {e}")
                    
        self.find_duplicates()
        return self.generate_report()
    
    def analyze_test_file(self, filepath: Path):
        """Analyze single test file for coverage."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError) as e:
            print(f"Could not parse {filepath}: {e}")
            return
            
        test_info = {
            'file': str(filepath.relative_to(self.test_dir)),
            'total_lines': len(content.splitlines()),
            'imports': self._extract_imports(tree),
            'test_classes': [],
            'test_functions': [],
            'fixtures': [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_info['test_functions'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
                    })
                elif any(dec.id == 'pytest.fixture' if hasattr(dec, 'id') else 'fixture' in str(dec) 
                        for dec in node.decorator_list):
                    test_info['fixtures'].append(node.name)
                    
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    class_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [],
                        'docstring': ast.get_docstring(node),
                    }
                    
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                            class_info['methods'].append({
                                'name': method.name,
                                'line': method.lineno,
                                'docstring': ast.get_docstring(method),
                            })
                    
                    test_info['test_classes'].append(class_info)
        
        # Categorize by what it tests
        category = self._categorize_test(test_info)
        self.test_map[category].append(test_info)
        
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    def _categorize_test(self, test_info: Dict) -> str:
        """Categorize test by what component it tests."""
        filepath = test_info['file']
        imports = test_info['imports']
        
        # UI tests
        if 'ui/' in filepath or any('PyQt' in imp or 'QApplication' in imp for imp in imports):
            if 'widget' in filepath.lower():
                return 'ui_widgets'
            elif 'chart' in filepath.lower():
                return 'ui_charts'
            else:
                return 'ui_general'
        
        # Analytics tests
        if ('analytics' in filepath or 
            any('analytics' in imp for imp in imports) or
            'calculator' in filepath.lower()):
            if 'daily' in filepath.lower():
                return 'analytics_daily'
            elif 'weekly' in filepath.lower():
                return 'analytics_weekly'
            elif 'monthly' in filepath.lower():
                return 'analytics_monthly'
            else:
                return 'analytics_general'
        
        # Data processing tests
        if ('data' in filepath or 
            any('data' in imp for imp in imports) or
            'loader' in filepath.lower() or
            'database' in filepath.lower()):
            return 'data_processing'
        
        # Integration tests
        if 'integration' in filepath:
            return 'integration'
        
        # Performance tests
        if 'performance' in filepath or 'benchmark' in filepath:
            return 'performance'
        
        # Comprehensive or general tests
        if 'comprehensive' in filepath.lower():
            return 'comprehensive'
            
        return 'other'
    
    def find_duplicates(self):
        """Identify duplicate and overlapping tests."""
        seen_tests = {}
        
        for category, tests in self.test_map.items():
            for test_file in tests:
                # Check for duplicate test functions
                for func in test_file['test_functions']:
                    signature = self._create_test_signature(func, test_file)
                    
                    if signature in seen_tests:
                        similarity = self._calculate_similarity(
                            seen_tests[signature], 
                            {'function': func, 'file': test_file}
                        )
                        
                        if similarity > 0.7:  # 70% similarity threshold
                            self.duplicate_tests.append({
                                'original': seen_tests[signature],
                                'duplicate': {'function': func, 'file': test_file},
                                'similarity': similarity,
                                'type': 'function'
                            })
                    else:
                        seen_tests[signature] = {'function': func, 'file': test_file}
                
                # Check for duplicate test classes
                for test_class in test_file['test_classes']:
                    for method in test_class['methods']:
                        signature = self._create_class_method_signature(method, test_class, test_file)
                        
                        if signature in seen_tests:
                            similarity = self._calculate_similarity(
                                seen_tests[signature],
                                {'method': method, 'class': test_class, 'file': test_file}
                            )
                            
                            if similarity > 0.7:
                                self.duplicate_tests.append({
                                    'original': seen_tests[signature],
                                    'duplicate': {'method': method, 'class': test_class, 'file': test_file},
                                    'similarity': similarity,
                                    'type': 'method'
                                })
                        else:
                            seen_tests[signature] = {'method': method, 'class': test_class, 'file': test_file}
    
    def _create_test_signature(self, func: Dict, test_file: Dict) -> str:
        """Create a signature for test function comparison."""
        # Extract key words from test name and docstring
        name_words = set(re.findall(r'\w+', func['name'].lower()))
        doc_words = set()
        
        if func['docstring']:
            doc_words = set(re.findall(r'\w+', func['docstring'].lower()))
        
        # Create signature from imports and test focus
        imports = set(imp.split('.')[-1].lower() for imp in test_file['imports'])
        
        return f"{name_words}:{doc_words}:{imports}"
    
    def _create_class_method_signature(self, method: Dict, test_class: Dict, test_file: Dict) -> str:
        """Create signature for class method comparison."""
        class_words = set(re.findall(r'\w+', test_class['name'].lower()))
        method_words = set(re.findall(r'\w+', method['name'].lower()))
        
        return f"{class_words}:{method_words}"
    
    def _calculate_similarity(self, test1: Dict, test2: Dict) -> float:
        """Calculate similarity between two tests."""
        # Simple similarity based on name and documentation overlap
        
        if 'function' in test1 and 'function' in test2:
            name1 = test1['function']['name'].lower()
            name2 = test2['function']['name'].lower()
            
            doc1 = test1['function'].get('docstring', '').lower()
            doc2 = test2['function'].get('docstring', '').lower()
        else:
            # Handle class methods
            name1 = test1.get('method', {}).get('name', '').lower()
            name2 = test2.get('method', {}).get('name', '').lower()
            
            doc1 = test1.get('method', {}).get('docstring', '').lower()
            doc2 = test2.get('method', {}).get('docstring', '').lower()
        
        # Calculate name similarity
        name_words1 = set(re.findall(r'\w+', name1))
        name_words2 = set(re.findall(r'\w+', name2))
        
        name_similarity = len(name_words1 & name_words2) / max(len(name_words1 | name_words2), 1)
        
        # Calculate doc similarity
        doc_words1 = set(re.findall(r'\w+', doc1))
        doc_words2 = set(re.findall(r'\w+', doc2))
        
        doc_similarity = len(doc_words1 & doc_words2) / max(len(doc_words1 | doc_words2), 1)
        
        return (name_similarity * 0.7 + doc_similarity * 0.3)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        total_test_functions = sum(
            len(test_file['test_functions']) + 
            sum(len(cls['methods']) for cls in test_file['test_classes'])
            for tests in self.test_map.values() 
            for test_file in tests
        )
        
        total_files = len(self.test_files)
        
        report = {
            'summary': {
                'total_test_files': total_files,
                'total_test_functions': total_test_functions,
                'categories': len(self.test_map),
                'duplicates_found': len(self.duplicate_tests),
                'potential_savings': len(self.duplicate_tests)
            },
            'categories': {
                category: {
                    'file_count': len(tests),
                    'test_count': sum(
                        len(test_file['test_functions']) + 
                        sum(len(cls['methods']) for cls in test_file['test_classes'])
                        for test_file in tests
                    ),
                    'files': [test['file'] for test in tests]
                }
                for category, tests in self.test_map.items()
            },
            'duplicates': self.duplicate_tests,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate consolidation recommendations."""
        recommendations = []
        
        # Recommend consolidating comprehensive test file
        comprehensive_tests = self.test_map.get('comprehensive', [])
        if comprehensive_tests:
            recommendations.append({
                'type': 'consolidate_comprehensive',
                'priority': 'high',
                'description': 'Distribute comprehensive unit coverage tests to specific component tests',
                'files': [test['file'] for test in comprehensive_tests],
                'estimated_reduction': 50  # Estimated test reduction percentage
            })
        
        # Recommend consolidating UI widgets
        ui_widget_tests = self.test_map.get('ui_widgets', [])
        if len(ui_widget_tests) > 3:
            recommendations.append({
                'type': 'consolidate_ui_widgets',
                'priority': 'medium',
                'description': 'Merge similar widget tests into parametrized test classes',
                'files': [test['file'] for test in ui_widget_tests],
                'estimated_reduction': 30
            })
        
        # Recommend consolidating analytics tests
        analytics_categories = ['analytics_daily', 'analytics_weekly', 'analytics_monthly']
        analytics_files = []
        for cat in analytics_categories:
            analytics_files.extend(self.test_map.get(cat, []))
        
        if len(analytics_files) > 2:
            recommendations.append({
                'type': 'consolidate_analytics',
                'priority': 'medium', 
                'description': 'Consolidate calculator tests using base test classes',
                'files': [test['file'] for test in analytics_files],
                'estimated_reduction': 25
            })
        
        return recommendations


def main():
    """Run the test coverage analysis."""
    print("Test Coverage Analysis Tool")
    print("=" * 40)
    
    analyzer = TestAnalyzer("tests")
    report = analyzer.analyze_all_tests()
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total test files: {report['summary']['total_test_files']}")
    print(f"  Total test functions: {report['summary']['total_test_functions']}")
    print(f"  Test categories: {report['summary']['categories']}")
    print(f"  Duplicate tests found: {report['summary']['duplicates_found']}")
    
    # Print categories
    print(f"\nTest Categories:")
    for category, info in report['categories'].items():
        print(f"  {category}: {info['file_count']} files, {info['test_count']} tests")
    
    # Print duplicates
    if report['duplicates']:
        print(f"\nDuplicate Tests Found:")
        for i, duplicate in enumerate(report['duplicates'][:5], 1):  # Show first 5
            print(f"  {i}. Similarity: {duplicate['similarity']:.2f}")
            print(f"     Type: {duplicate['type']}")
    
    # Print recommendations
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  Priority {rec['priority']}: {rec['description']}")
        print(f"    Estimated reduction: {rec['estimated_reduction']}%")
        print(f"    Files: {len(rec['files'])}")
    
    # Save detailed report
    with open('test_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: test_analysis_report.json")
    return report


if __name__ == "__main__":
    main()