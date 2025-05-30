#!/usr/bin/env python3
"""
Apple Health Monitor - Development Entry Point

Centralized development script that provides access to all development utilities,
demos, and tools through a single entry point.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


class DevRunner:
    """Centralized development script runner."""
    
    def __init__(self):
        self.project_root = project_root
        
    def run_main_app(self):
        """Run the main Apple Health Monitor application."""
        print("🚀 Starting Apple Health Monitor Dashboard...")
        try:
            from src.main import main
            main()
        except ImportError as e:
            print(f"❌ Failed to import main app: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to run main app: {e}")
            return False
    
    def run_tests(self, test_type="unit", **kwargs):
        """Run tests using the test runner."""
        print(f"🧪 Running {test_type} tests...")
        try:
            # Import and run the test runner
            sys.path.insert(0, str(self.project_root / "tests"))
            from run_tests import (
                run_unit_tests, run_integration_tests, run_performance_tests,
                run_visual_tests, run_chaos_tests, run_all_tests, check_test_environment
            )
            
            if test_type == "unit":
                return run_unit_tests(
                    coverage=kwargs.get('coverage', True),
                    fail_under=kwargs.get('coverage_threshold', 90)
                )
            elif test_type == "integration":
                return run_integration_tests()
            elif test_type == "performance":
                return run_performance_tests(save_baseline=kwargs.get('save_baseline', False))
            elif test_type == "visual":
                return run_visual_tests()
            elif test_type == "chaos":
                return run_chaos_tests()
            elif test_type == "all":
                return run_all_tests()
            elif test_type == "check":
                return check_test_environment()
            else:
                print(f"❌ Unknown test type: {test_type}")
                return False
                
        except ImportError as e:
            print(f"❌ Failed to import test runner: {e}")
            return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def run_performance_benchmarks(self):
        """Run performance benchmarks."""
        print("📊 Running performance benchmarks...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "tests/performance/run_benchmarks.py"],
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to run benchmarks: {e}")
            return False
    
    def run_visual_tests(self):
        """Run visual regression tests."""
        print("🎨 Running visual regression tests...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "tests/visual/run_visual_tests.py"],
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to run visual tests: {e}")
            return False
    
    def verify_imports(self):
        """Verify all critical imports are working."""
        print("🔍 Verifying imports...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "tests/helpers/verify_imports.py"],
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to verify imports: {e}")
            return False
    
    def verify_syntax(self):
        """Check Python syntax validity of key files."""
        print("✓ Verifying syntax...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "tests/helpers/verify_syntax.py"],
                cwd=str(self.project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to verify syntax: {e}")
            return False
    
    def run_demo(self, demo_name):
        """Run a specific demo application."""
        demos = {
            'bar_chart': {
                'path': 'examples/bar_chart_demo.py',
                'description': 'Interactive bar chart component demo'
            },
            'line_chart': {
                'path': 'src/examples/line_chart_demo.py', 
                'description': 'Enhanced line chart with WSJ styling'
            },
            'table': {
                'path': 'examples/table_usage_example.py',
                'description': 'Metric table component with pagination'
            },
            'journal': {
                'path': 'examples/journal_example.py',
                'description': 'General-purpose journaling system'
            },
            'month_over_month': {
                'path': 'src/ui/month_over_month_demo.py',
                'description': 'Month-over-month trends analysis'
            },
            'annotation': {
                'path': 'examples/annotation_demo.py',
                'description': 'Chart annotation system demo'
            },
            'dashboard': {
                'path': 'examples/dashboard_demo.py',
                'description': 'Dashboard layout demo'
            },
            'interactive': {
                'path': 'examples/interactive_chart_example.py',
                'description': 'Interactive chart features demo'
            },
            'reactive': {
                'path': 'examples/reactive_data_binding_demo.py',
                'description': 'Reactive data binding demo'
            },
            'temporal': {
                'path': 'examples/temporal_anomaly_example.py',
                'description': 'Temporal anomaly detection demo'
            }
        }
        
        if demo_name not in demos:
            print(f"❌ Unknown demo: {demo_name}")
            print("Available demos:")
            for name, info in demos.items():
                print(f"  {name}: {info['description']}")
            return False
        
        demo_info = demos[demo_name]
        demo_path = self.project_root / demo_info['path']
        
        if not demo_path.exists():
            print(f"❌ Demo file not found: {demo_path}")
            return False
        
        print(f"🎨 Running {demo_name} demo: {demo_info['description']}")
        
        try:
            # Execute the demo script
            import subprocess
            result = subprocess.run([sys.executable, str(demo_path)], cwd=str(self.project_root))
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to run demo: {e}")
            return False
    
    def list_demos(self):
        """List all available demos."""
        print("📋 Available Demo Applications:")
        print("-" * 50)
        
        demos = [
            ('bar_chart', 'Interactive bar chart component demo'),
            ('line_chart', 'Enhanced line chart with WSJ styling'),
            ('table', 'Metric table component with pagination'),
            ('journal', 'General-purpose journaling system'),
            ('month_over_month', 'Month-over-month trends analysis'),
            ('annotation', 'Chart annotation system demo'),
            ('dashboard', 'Dashboard layout demo'),
            ('interactive', 'Interactive chart features demo'),
            ('reactive', 'Reactive data binding demo'),
            ('temporal', 'Temporal anomaly detection demo')
        ]
        
        for name, description in demos:
            print(f"  {name:<18} {description}")
        
        print(f"\nUsage: python run_dev.py demo <demo_name>")
    
    def show_status(self):
        """Show development environment status."""
        print("📊 Development Environment Status")
        print("=" * 40)
        
        # Check main components
        components = [
            ('Main Application', 'src/main.py'),
            ('Test Runner', 'tests/run_tests.py'),
            ('Performance Benchmarks', 'tests/performance/run_benchmarks.py'),
            ('Visual Tests', 'tests/visual/run_visual_tests.py'),
            ('Import Verifier', 'tests/helpers/verify_imports.py'),
            ('Syntax Verifier', 'tests/helpers/verify_syntax.py'),
        ]
        
        for name, path in components:
            file_path = self.project_root / path
            status = "✅" if file_path.exists() else "❌"
            print(f"{status} {name:<25} {path}")
        
        # Check demo files
        print("\n📁 Demo Applications:")
        demo_paths = [
            'examples/bar_chart_demo.py',
            'src/examples/line_chart_demo.py',
            'examples/table_usage_example.py', 
            'examples/journal_example.py',
            'src/ui/month_over_month_demo.py',
            'examples/annotation_demo.py',
            'examples/dashboard_demo.py',
            'examples/interactive_chart_example.py',
            'examples/reactive_data_binding_demo.py',
            'examples/temporal_anomaly_example.py'
        ]
        
        for path in demo_paths:
            file_path = self.project_root / path
            status = "✅" if file_path.exists() else "❌"
            demo_name = Path(path).stem.replace('_demo', '').replace('_example', '')
            print(f"{status} {demo_name:<20} {path}")
        
        # Check Python environment
        print(f"\n🐍 Python: {sys.version}")
        print(f"📁 Project Root: {self.project_root}")
        
        # Check key dependencies
        print("\n📦 Key Dependencies:")
        try:
            import PyQt6
            print(f"✅ PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}")
        except ImportError:
            print("❌ PyQt6 not installed")
        
        try:
            import pandas as pd
            print(f"✅ pandas: {pd.__version__}")
        except ImportError:
            print("❌ pandas not installed")
        
        try:
            import matplotlib
            print(f"✅ matplotlib: {matplotlib.__version__}")
        except ImportError:
            print("❌ matplotlib not installed")
        
        try:
            import numpy as np
            print(f"✅ numpy: {np.__version__}")
        except ImportError:
            print("❌ numpy not installed")


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(
        description="Apple Health Monitor Development Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dev.py app                    # Run main application
  python run_dev.py test unit              # Run unit tests
  python run_dev.py test all               # Run all tests
  python run_dev.py benchmark              # Run performance benchmarks
  python run_dev.py visual                 # Run visual regression tests
  python run_dev.py demo bar_chart         # Run bar chart demo
  python run_dev.py demos                  # List available demos
  python run_dev.py verify-imports         # Verify all imports
  python run_dev.py verify-syntax          # Check syntax validity
  python run_dev.py status                 # Show environment status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Development commands')
    
    # App command
    subparsers.add_parser('app', help='Run the main application')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument(
        'test_type',
        choices=['unit', 'integration', 'performance', 'visual', 'chaos', 'all', 'check'],
        help='Type of tests to run'
    )
    test_parser.add_argument('--no-coverage', action='store_true', help='Skip coverage')
    test_parser.add_argument('--coverage-threshold', type=int, default=90, help='Coverage threshold')
    test_parser.add_argument('--save-baseline', action='store_true', help='Save performance baseline')
    
    # Benchmark command
    subparsers.add_parser('benchmark', help='Run performance benchmarks')
    
    # Visual tests command
    subparsers.add_parser('visual', help='Run visual regression tests')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run a demo application')
    demo_parser.add_argument('demo_name', help='Name of demo to run')
    
    # Demos command (list demos)
    subparsers.add_parser('demos', help='List available demos')
    
    # Verify commands
    subparsers.add_parser('verify-imports', help='Verify all critical imports')
    subparsers.add_parser('verify-syntax', help='Check Python syntax validity')
    
    # Status command
    subparsers.add_parser('status', help='Show environment status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    runner = DevRunner()
    
    try:
        if args.command == 'app':
            success = runner.run_main_app()
            
        elif args.command == 'test':
            kwargs = {
                'coverage': not args.no_coverage,
                'coverage_threshold': args.coverage_threshold,
                'save_baseline': args.save_baseline
            }
            success = runner.run_tests(args.test_type, **kwargs)
            
        elif args.command == 'benchmark':
            success = runner.run_performance_benchmarks()
            
        elif args.command == 'visual':
            success = runner.run_visual_tests()
            
        elif args.command == 'demo':
            success = runner.run_demo(args.demo_name)
            
        elif args.command == 'demos':
            runner.list_demos()
            success = True
            
        elif args.command == 'verify-imports':
            success = runner.verify_imports()
            
        elif args.command == 'verify-syntax':
            success = runner.verify_syntax()
            
        elif args.command == 'status':
            runner.show_status()
            success = True
            
        else:
            parser.print_help()
            success = False
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())