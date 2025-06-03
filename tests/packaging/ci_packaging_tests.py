"""
CI/CD integration script for packaging tests.

This script is designed to be run in CI/CD pipelines to validate
packaged builds automatically.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class CIPackagingTests:
    """Automated packaging tests for CI/CD pipelines."""
    
    def __init__(self, build_dir: str, artifact_dir: str):
        """Initialize CI test runner.
        
        Args:
            build_dir: Directory containing built executables
            artifact_dir: Directory for test artifacts
        """
        self.build_dir = Path(build_dir)
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "build_dir": str(self.build_dir),
            "tests_passed": 0,
            "tests_failed": 0,
            "tests": {}
        }
        
    def find_executable(self) -> Optional[Path]:
        """Find the packaged executable in build directory.
        
        Returns:
            Path to executable or None if not found
        """
        patterns = [
            "AppleHealthDashboard.exe",
            "*/AppleHealthDashboard.exe",
            "dist/AppleHealthDashboard.exe",
        ]
        
        for pattern in patterns:
            matches = list(self.build_dir.glob(pattern))
            if matches:
                return matches[0]
                
        return None
        
    def run_test(self, test_name: str, command: List[str]) -> bool:
        """Run a test command and capture results.
        
        Args:
            test_name: Name of the test
            command: Command to execute
            
        Returns:
            True if test passed
        """
        print(f"\nRunning: {test_name}")
        print(f"Command: {' '.join(command)}")
        
        start_time = datetime.now()
        
        try:
            # Run test
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Check result
            success = result.returncode == 0
            
            # Store results
            self.results["tests"][test_name] = {
                "success": success,
                "duration": duration,
                "stdout": result.stdout[-1000:],  # Last 1000 chars
                "stderr": result.stderr[-1000:],
                "returncode": result.returncode
            }
            
            # Save output
            output_file = self.artifact_dir / f"{test_name}_output.txt"
            with open(output_file, "w") as f:
                f.write(f"=== {test_name} ===\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write(f"\n--- STDOUT ---\n{result.stdout}")
                f.write(f"\n--- STDERR ---\n{result.stderr}")
                
            if success:
                print(f"✓ {test_name} PASSED ({duration:.1f}s)")
                self.results["tests_passed"] += 1
            else:
                print(f"✗ {test_name} FAILED ({duration:.1f}s)")
                self.results["tests_failed"] += 1
                
            return success
            
        except subprocess.TimeoutExpired:
            print(f"✗ {test_name} TIMEOUT")
            self.results["tests"][test_name] = {
                "success": False,
                "error": "Test timed out after 300 seconds"
            }
            self.results["tests_failed"] += 1
            return False
            
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            self.results["tests"][test_name] = {
                "success": False,
                "error": str(e)
            }
            self.results["tests_failed"] += 1
            return False
            
    def run_all_tests(self) -> bool:
        """Run all CI packaging tests.
        
        Returns:
            True if all tests passed
        """
        print("=" * 60)
        print("CI PACKAGING TESTS")
        print("=" * 60)
        
        # Find executable
        exe_path = self.find_executable()
        if not exe_path:
            print("ERROR: No executable found in build directory!")
            return False
            
        print(f"Testing executable: {exe_path}")
        
        # Validate test setup
        self.run_test(
            "validate_setup",
            [sys.executable, "tests/packaging/validate_test_setup.py"]
        )
        
        # Run automated tests
        self.run_test(
            "automated_tests",
            [sys.executable, "tests/packaging/test_packaged_app.py", str(exe_path)]
        )
        
        # Run performance benchmarks
        self.run_test(
            "performance_benchmarks",
            [sys.executable, "tests/packaging/performance_benchmarks.py", str(exe_path)]
        )
        
        # Generate summary
        self._generate_summary()
        
        return self.results["tests_failed"] == 0
        
    def _generate_summary(self):
        """Generate test summary and artifacts."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total = self.results["tests_passed"] + self.results["tests_failed"]
        print(f"Total tests: {total}")
        print(f"Passed: {self.results['tests_passed']}")
        print(f"Failed: {self.results['tests_failed']}")
        
        # Save JSON results
        results_file = self.artifact_dir / "ci_test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {results_file}")
        
        # Generate JUnit XML for CI systems
        self._generate_junit_xml()
        
        # Generate markdown summary
        self._generate_markdown_summary()
        
    def _generate_junit_xml(self):
        """Generate JUnit XML format for CI systems."""
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<testsuites>')
        
        # Add test suite
        total = len(self.results["tests"])
        failures = self.results["tests_failed"]
        
        xml_content.append(f'  <testsuite name="PackagingTests" tests="{total}" failures="{failures}">')
        
        for test_name, test_data in self.results["tests"].items():
            duration = test_data.get("duration", 0)
            
            if test_data.get("success", False):
                xml_content.append(f'    <testcase name="{test_name}" time="{duration:.2f}"/>')
            else:
                xml_content.append(f'    <testcase name="{test_name}" time="{duration:.2f}">')
                error_msg = test_data.get("error", "Test failed")
                xml_content.append(f'      <failure message="{error_msg}"/>')
                xml_content.append('    </testcase>')
                
        xml_content.append('  </testsuite>')
        xml_content.append('</testsuites>')
        
        # Save XML
        junit_file = self.artifact_dir / "junit_results.xml"
        with open(junit_file, "w") as f:
            f.write("\n".join(xml_content))
        print(f"JUnit XML saved to: {junit_file}")
        
    def _generate_markdown_summary(self):
        """Generate markdown summary for PR comments."""
        md = ["# Packaging Test Results\n"]
        
        # Summary table
        md.append("## Summary")
        md.append(f"- **Total Tests**: {len(self.results['tests'])}")
        md.append(f"- **Passed**: {self.results['tests_passed']} ✅")
        md.append(f"- **Failed**: {self.results['tests_failed']} ❌")
        md.append("")
        
        # Test details
        md.append("## Test Details")
        md.append("| Test | Result | Duration |")
        md.append("|------|--------|----------|")
        
        for test_name, test_data in self.results["tests"].items():
            status = "✅ Pass" if test_data.get("success", False) else "❌ Fail"
            duration = test_data.get("duration", 0)
            md.append(f"| {test_name} | {status} | {duration:.1f}s |")
            
        # Add failures details if any
        if self.results["tests_failed"] > 0:
            md.append("\n## Failed Tests")
            for test_name, test_data in self.results["tests"].items():
                if not test_data.get("success", False):
                    md.append(f"\n### {test_name}")
                    if "error" in test_data:
                        md.append(f"**Error**: {test_data['error']}")
                    if "stderr" in test_data and test_data["stderr"]:
                        md.append("```")
                        md.append(test_data["stderr"][-500:])  # Last 500 chars
                        md.append("```")
                        
        # Save markdown
        md_file = self.artifact_dir / "test_summary.md"
        with open(md_file, "w") as f:
            f.write("\n".join(md))
        print(f"Markdown summary saved to: {md_file}")


def main():
    """Main entry point for CI testing."""
    if len(sys.argv) < 3:
        print("Usage: python ci_packaging_tests.py <build_dir> <artifact_dir>")
        print("\nExample:")
        print("  python ci_packaging_tests.py ./dist ./test-artifacts")
        sys.exit(1)
        
    build_dir = sys.argv[1]
    artifact_dir = sys.argv[2]
    
    # Run tests
    ci_tests = CIPackagingTests(build_dir, artifact_dir)
    success = ci_tests.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()