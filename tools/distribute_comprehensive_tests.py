#!/usr/bin/env python3
"""
Comprehensive Test Distribution Tool

Analyzes test_comprehensive_unit_coverage.py and distributes tests
to their appropriate component-specific test files.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class TestDistributor:
    """Distributes comprehensive tests to appropriate component files."""
    
    def __init__(self, comprehensive_file: str = "tests/test_comprehensive_unit_coverage.py"):
        self.comprehensive_file = Path(comprehensive_file)
        self.test_classes = {}
        self.standalone_tests = []
        self.distribution_map = {}
        self.target_files = {}
        
    def analyze_comprehensive_file(self):
        """Analyze the comprehensive test file structure."""
        if not self.comprehensive_file.exists():
            print(f"Error: {self.comprehensive_file} not found")
            return False
            
        try:
            with open(self.comprehensive_file, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"Error parsing {self.comprehensive_file}: {e}")
            return False
        
        # Extract imports
        imports = self._extract_imports(tree)
        
        # Analyze classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith('Test'):
                    class_info = self._analyze_test_class(node, content)
                    self.test_classes[node.name] = class_info
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    func_info = self._analyze_test_function(node, content)
                    self.standalone_tests.append(func_info)
        
        self._create_distribution_map()
        return True
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        return imports
    
    def _analyze_test_class(self, class_node: ast.ClassDef, content: str) -> Dict:
        """Analyze a test class and its methods."""
        lines = content.split('\n')
        start_line = class_node.lineno - 1
        
        # Find end line of class
        end_line = len(lines)
        for i, line in enumerate(lines[start_line + 1:], start_line + 1):
            if line and not line.startswith(' ') and not line.startswith('\t'):
                end_line = i
                break
        
        class_content = '\n'.join(lines[start_line:end_line])
        
        # Extract methods
        methods = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node),
                    'is_test': node.name.startswith('test_'),
                    'is_fixture': any('fixture' in str(dec) for dec in node.decorator_list),
                }
                methods.append(method_info)
        
        return {
            'name': class_node.name,
            'docstring': ast.get_docstring(class_node),
            'start_line': start_line,
            'end_line': end_line,
            'content': class_content,
            'methods': methods,
            'component': self._identify_component(class_node.name, class_content),
        }
    
    def _analyze_test_function(self, func_node: ast.FunctionDef, content: str) -> Dict:
        """Analyze a standalone test function."""
        lines = content.split('\n')
        start_line = func_node.lineno - 1
        
        # Find function end (simple heuristic)
        end_line = start_line + 1
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        
        for i, line in enumerate(lines[start_line + 1:], start_line + 1):
            if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                end_line = i
                break
        else:
            end_line = len(lines)
        
        func_content = '\n'.join(lines[start_line:end_line])
        
        return {
            'name': func_node.name,
            'docstring': ast.get_docstring(func_node),
            'start_line': start_line,
            'end_line': end_line,
            'content': func_content,
            'component': self._identify_component(func_node.name, func_content),
        }
    
    def _identify_component(self, name: str, content: str) -> str:
        """Identify which component a test belongs to."""
        name_lower = name.lower()
        content_lower = content.lower()
        
        # Analytics components
        if any(term in name_lower for term in ['daily', 'dailymetrics']):
            return 'daily_metrics_calculator'
        elif any(term in name_lower for term in ['weekly', 'weeklymetrics']):
            return 'weekly_metrics_calculator'
        elif any(term in name_lower for term in ['monthly', 'monthlymetrics']):
            return 'monthly_metrics_calculator'
        elif any(term in name_lower for term in ['statistics', 'stats']):
            return 'statistics_calculator'
        elif any(term in name_lower for term in ['comparison', 'overlay']):
            return 'comparison_overlay_calculator'
        elif any(term in name_lower for term in ['trend', 'weekoverweek']):
            return 'week_over_week_trends'
        
        # Data processing
        elif any(term in name_lower for term in ['loader', 'dataloader']):
            return 'data_loader'
        elif any(term in name_lower for term in ['database', 'db']):
            return 'database'
        elif any(term in name_lower for term in ['filter', 'filtering']):
            return 'data_filter_engine'
        
        # Content-based detection
        if 'DailyMetricsCalculator' in content:
            return 'daily_metrics_calculator'
        elif 'WeeklyMetricsCalculator' in content:
            return 'weekly_metrics_calculator'
        elif 'MonthlyMetricsCalculator' in content:
            return 'monthly_metrics_calculator'
        elif 'StatisticsCalculator' in content:
            return 'statistics_calculator'
        elif 'DataLoader' in content:
            return 'data_loader'
        elif 'Database' in content:
            return 'database'
        
        return 'general'
    
    def _create_distribution_map(self):
        """Create mapping of tests to target files."""
        component_to_file = {
            'daily_metrics_calculator': 'tests/unit/test_daily_metrics_calculator.py',
            'weekly_metrics_calculator': 'tests/unit/test_weekly_metrics_calculator.py',
            'monthly_metrics_calculator': 'tests/unit/test_monthly_metrics_calculator.py',
            'statistics_calculator': 'tests/unit/test_statistics_calculator.py',
            'comparison_overlay_calculator': 'tests/unit/test_comparison_overlay_calculator.py',
            'week_over_week_trends': 'tests/unit/test_week_over_week_trends.py',
            'data_loader': 'tests/unit/test_data_loader.py',
            'database': 'tests/unit/test_database.py',
            'data_filter_engine': 'tests/unit/test_data_filter_engine.py',
            'general': 'tests/unit/test_general_components.py',
        }
        
        self.distribution_map = defaultdict(list)
        
        # Map test classes
        for class_name, class_info in self.test_classes.items():
            component = class_info['component']
            target_file = component_to_file.get(component, component_to_file['general'])
            self.distribution_map[target_file].append(('class', class_info))
        
        # Map standalone functions
        for func_info in self.standalone_tests:
            component = func_info['component']
            target_file = component_to_file.get(component, component_to_file['general'])
            self.distribution_map[target_file].append(('function', func_info))
    
    def generate_distribution_plan(self) -> Dict:
        """Generate a plan for distributing tests."""
        plan = {
            'source_file': str(self.comprehensive_file),
            'total_classes': len(self.test_classes),
            'total_functions': len(self.standalone_tests),
            'target_files': {},
            'recommendations': []
        }
        
        for target_file, items in self.distribution_map.items():
            classes = [item[1] for item in items if item[0] == 'class']
            functions = [item[1] for item in items if item[0] == 'function']
            
            plan['target_files'][target_file] = {
                'classes': len(classes),
                'functions': len(functions),
                'class_names': [cls['name'] for cls in classes],
                'function_names': [func['name'] for func in functions],
            }
        
        # Generate recommendations
        if len(self.test_classes) > 0:
            plan['recommendations'].append({
                'type': 'distribute_classes',
                'description': f'Distribute {len(self.test_classes)} test classes to component files',
                'priority': 'high'
            })
        
        if len(self.standalone_tests) > 0:
            plan['recommendations'].append({
                'type': 'distribute_functions',
                'description': f'Distribute {len(self.standalone_tests)} standalone test functions',
                'priority': 'medium'
            })
        
        return plan
    
    def create_distributed_test_files(self, dry_run: bool = True):
        """Create the distributed test files."""
        print(f"{'DRY RUN: ' if dry_run else ''}Creating distributed test files...")
        
        for target_file, items in self.distribution_map.items():
            target_path = Path(target_file)
            
            if not dry_run:
                # Create directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate file content
            file_content = self._generate_test_file_content(target_file, items)
            
            if dry_run:
                print(f"Would create/update: {target_file}")
                print(f"  Classes: {len([i for i in items if i[0] == 'class'])}")
                print(f"  Functions: {len([i for i in items if i[0] == 'function'])}")
            else:
                # Check if file exists and merge or create
                if target_path.exists():
                    self._merge_with_existing_file(target_path, file_content)
                else:
                    with open(target_path, 'w') as f:
                        f.write(file_content)
                print(f"Created: {target_file}")
    
    def _generate_test_file_content(self, target_file: str, items: List[Tuple]) -> str:
        """Generate content for a distributed test file."""
        component_name = Path(target_file).stem.replace('test_', '')
        
        header = f'''"""
Tests for {component_name.replace('_', ' ').title()}

This file contains tests distributed from test_comprehensive_unit_coverage.py
for better organization and maintainability.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tests.base_test_classes import BaseCalculatorTest, BaseAnalyticsTest

'''
        
        content_parts = [header]
        
        # Add classes
        for item_type, item_info in items:
            if item_type == 'class':
                content_parts.append(item_info['content'])
                content_parts.append('\n\n')
            elif item_type == 'function':
                content_parts.append(item_info['content'])
                content_parts.append('\n\n')
        
        return ''.join(content_parts)
    
    def _merge_with_existing_file(self, target_path: Path, new_content: str):
        """Merge new content with existing test file."""
        if target_path.exists():
            with open(target_path, 'r') as f:
                existing_content = f.read()
            
            # Simple merge strategy: append new content
            merged_content = existing_content + '\n\n# Distributed from comprehensive tests\n\n' + new_content
        else:
            merged_content = new_content
        
        with open(target_path, 'w') as f:
            f.write(merged_content)
    
    def create_backup(self):
        """Create backup of comprehensive test file."""
        backup_path = self.comprehensive_file.with_suffix('.py.backup')
        if self.comprehensive_file.exists():
            with open(self.comprehensive_file, 'r') as src:
                with open(backup_path, 'w') as dst:
                    dst.write(src.read())
            print(f"Backup created: {backup_path}")
            return backup_path
        return None


def main():
    """Run the test distribution tool."""
    print("Comprehensive Test Distribution Tool")
    print("=" * 40)
    
    distributor = TestDistributor()
    
    # Analyze the comprehensive file
    if not distributor.analyze_comprehensive_file():
        print("Failed to analyze comprehensive test file")
        return
    
    # Generate distribution plan
    plan = distributor.generate_distribution_plan()
    
    print(f"\nDistribution Plan:")
    print(f"Source: {plan['source_file']}")
    print(f"Total test classes: {plan['total_classes']}")
    print(f"Total test functions: {plan['total_functions']}")
    print(f"Target files: {len(plan['target_files'])}")
    
    print(f"\nTarget File Breakdown:")
    for target_file, info in plan['target_files'].items():
        print(f"  {target_file}:")
        print(f"    Classes: {info['classes']} - {info['class_names']}")
        print(f"    Functions: {info['functions']}")
    
    print(f"\nRecommendations:")
    for rec in plan['recommendations']:
        print(f"  {rec['priority'].upper()}: {rec['description']}")
    
    # Proceed with distribution automatically
    print("\nProceeding with distribution...")
    
    # Create backup first
    backup_path = distributor.create_backup()
    
    # Create distributed files
    distributor.create_distributed_test_files(dry_run=False)
    
    print(f"\nDistribution complete!")
    print(f"Original file backed up to: {backup_path}")
    print(f"You can now review the distributed files and remove the original if satisfied.")
    
    return plan


if __name__ == "__main__":
    main()