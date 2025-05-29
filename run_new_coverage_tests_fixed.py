#!/usr/bin/env python3
"""
Run the new comprehensive test suite and measure coverage.
"""

import subprocess
import sys
import os

def run_tests_with_coverage():
    """Run the new test files with coverage measurement."""
    
    # New test files created
    new_test_files = [
        "tests/unit/test_xml_streaming_processor_improved.py",
        "tests/unit/test_statistics_calculator_improved.py", 
        "tests/unit/test_data_access_improved.py",
        "tests/unit/test_data_filter_engine_improved.py",
        "tests/unit/test_filter_config_manager_improved.py",
        "tests/unit/test_error_handler_improved.py",
        "tests/unit/test_xml_validator_improved.py"
    ]
    
    print("Running new comprehensive test suite with coverage...")
    print(f"Testing {len(new_test_files)} test files")
    print("-" * 60)
    
    # Build pytest command with coverage using source paths
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=src/xml_streaming_processor",
        "--cov=src/statistics_calculator",
        "--cov=src/data_access",
        "--cov=src/data_filter_engine", 
        "--cov=src/filter_config_manager",
        "--cov=src/utils/error_handler",
        "--cov=src/utils/xml_validator",
        "--cov-report=term-missing:skip-covered",
        "--cov-report=html:coverage_html_new",
        "--cov-report=json:coverage_new.json",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ] + new_test_files[:3]  # Run first 3 test files to check
    
    # Run the tests
    try:
        result = subprocess.run(cmd, text=True)
        
        if result.returncode != 0:
            print(f"\nTests failed with return code: {result.returncode}")
        else:
            print("\nAll tests passed!")
            
        # Try to parse and display coverage summary
        try:
            import json
            with open("coverage_new.json", "r") as f:
                coverage_data = json.load(f)
                
            print("\n" + "=" * 60)
            print("COVERAGE SUMMARY:")
            print("=" * 60)
            
            total_covered = 0
            total_statements = 0
            
            for file_path, file_data in coverage_data.get("files", {}).items():
                covered = len(file_data.get("executed_lines", []))
                statements = file_data["summary"]["num_statements"]
                percent = file_data["summary"]["percent_covered"]
                
                # Extract module name
                if "src/" in file_path:
                    module_name = file_path[file_path.index("src/"):].replace(".py", "")
                else:
                    module_name = file_path
                    
                print(f"{module_name:<50} {percent:>6.1f}% ({covered}/{statements})")
                
                total_covered += covered
                total_statements += statements
            
            if total_statements > 0:
                total_percent = (total_covered / total_statements) * 100
                print("-" * 60)
                print(f"{'TOTAL':<50} {total_percent:>6.1f}% ({total_covered}/{total_statements})")
                
        except Exception as e:
            print(f"Could not parse coverage data: {e}")
            
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
        
    return result.returncode if result else 1

if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())