"""
Setup script for packaging test environments.

This script helps prepare clean Windows test environments for
packaging validation tests.
"""

import os
import sys
import shutil
import json
import subprocess
from pathlib import Path
from datetime import datetime
import platform


class TestEnvironmentSetup:
    """Manages test environment setup and validation."""
    
    def __init__(self):
        """Initialize test environment setup."""
        self.os_info = self._get_os_info()
        self.test_dir = Path("packaging_tests")
        self.log_file = self.test_dir / "setup_log.txt"
        
    def _get_os_info(self) -> dict:
        """Gather OS information."""
        info = {
            "platform": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
        
        if platform.system() == "Windows":
            info["windows_version"] = platform.win32_ver()[0]
            info["windows_edition"] = platform.win32_edition()
            
        return info
        
    def log(self, message: str):
        """Log message to console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
            
    def check_prerequisites(self) -> dict:
        """Check system prerequisites for testing."""
        self.log("Checking prerequisites...")
        
        checks = {
            "os_windows": platform.system() == "Windows",
            "python_version": sys.version_info >= (3, 10),
            "memory_available": self._check_memory(),
            "disk_space": self._check_disk_space(),
            "admin_rights": self._check_admin_rights(),
        }
        
        # Check for required redistributables
        checks["vcredist"] = self._check_vcredist()
        checks["dotnet"] = self._check_dotnet()
        
        return checks
        
    def _check_memory(self) -> bool:
        """Check if system has enough memory (4GB minimum)."""
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            return memory_gb >= 4.0
        except ImportError:
            self.log("Warning: psutil not installed, cannot check memory")
            return True
            
    def _check_disk_space(self) -> bool:
        """Check if enough disk space is available (10GB minimum)."""
        try:
            import psutil
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            return free_gb >= 10.0
        except:
            return True
            
    def _check_admin_rights(self) -> bool:
        """Check if running with admin rights (for installer tests)."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
            
    def _check_vcredist(self) -> bool:
        """Check for Visual C++ Redistributables."""
        # Check registry for VC++ redistributables
        vcredist_keys = [
            r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
            r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
        ]
        
        try:
            import winreg
            for key_path in vcredist_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    return True
                except:
                    pass
        except ImportError:
            self.log("Warning: Cannot check Windows registry")
            
        return False
        
    def _check_dotnet(self) -> bool:
        """Check for .NET Framework."""
        try:
            # Check for .NET Framework 4.8
            import winreg
            key_path = r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            value, _ = winreg.QueryValueEx(key, "Release")
            # .NET 4.8 = 528040 or higher
            return value >= 528040
        except:
            return False
            
    def create_test_directories(self):
        """Create directory structure for tests."""
        self.log("Creating test directories...")
        
        directories = [
            self.test_dir,
            self.test_dir / "exe_tests",
            self.test_dir / "installer_tests",
            self.test_dir / "portable_tests",
            self.test_dir / "results",
            self.test_dir / "logs",
            self.test_dir / "screenshots",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"  Created: {directory}")
            
    def download_test_files(self):
        """Download or prepare test data files."""
        self.log("Preparing test data files...")
        
        # Create sample Apple Health export XML
        sample_xml = self.test_dir / "sample_export.xml"
        if not sample_xml.exists():
            self._create_sample_xml(sample_xml)
            
        # Create large test file for performance testing
        large_xml = self.test_dir / "large_export.xml"
        if not large_xml.exists():
            self._create_large_xml(large_xml)
            
    def _create_sample_xml(self, path: Path):
        """Create a minimal valid Apple Health export XML."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HealthData [
<!ELEMENT HealthData (ExportDate,Me,Record*)>
<!ATTLIST ExportDate value CDATA #REQUIRED>
<!ELEMENT Me EMPTY>
<!ATTLIST Me HKCharacteristicTypeIdentifierBiologicalSex CDATA #REQUIRED>
<!ELEMENT Record EMPTY>
<!ATTLIST Record type CDATA #REQUIRED>
]>
<HealthData locale="en_US">
 <ExportDate value="2024-01-01 12:00:00 -0500"/>
 <Me HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexNotSet"/>
 <Record type="HKQuantityTypeIdentifierStepCount" value="5000" 
         startDate="2024-01-01 09:00:00 -0500" 
         endDate="2024-01-01 10:00:00 -0500"/>
 <Record type="HKQuantityTypeIdentifierHeartRate" value="72" 
         startDate="2024-01-01 09:30:00 -0500" 
         endDate="2024-01-01 09:30:00 -0500"/>
</HealthData>'''
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        self.log(f"  Created sample XML: {path}")
        
    def _create_large_xml(self, path: Path, records: int = 100000):
        """Create a large test XML file."""
        self.log(f"  Creating large XML with {records} records...")
        
        with open(path, "w", encoding="utf-8") as f:
            # Write header
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<HealthData locale="en_US">\n')
            f.write(' <ExportDate value="2024-01-01 12:00:00 -0500"/>\n')
            f.write(' <Me HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexNotSet"/>\n')
            
            # Write records
            from datetime import datetime, timedelta
            start_date = datetime(2023, 1, 1)
            
            for i in range(records):
                date = start_date + timedelta(minutes=i * 5)
                date_str = date.strftime("%Y-%m-%d %H:%M:%S -0500")
                
                if i % 3 == 0:
                    # Steps
                    f.write(f' <Record type="HKQuantityTypeIdentifierStepCount" '
                           f'value="{5000 + i % 1000}" '
                           f'startDate="{date_str}" endDate="{date_str}"/>\n')
                elif i % 3 == 1:
                    # Heart rate
                    f.write(f' <Record type="HKQuantityTypeIdentifierHeartRate" '
                           f'value="{60 + i % 40}" '
                           f'startDate="{date_str}" endDate="{date_str}"/>\n')
                else:
                    # Active energy
                    f.write(f' <Record type="HKQuantityTypeIdentifierActiveEnergyBurned" '
                           f'value="{100 + i % 50}" '
                           f'startDate="{date_str}" endDate="{date_str}"/>\n')
                           
                if i % 10000 == 0:
                    self.log(f"    Progress: {i}/{records} records")
                    
            f.write('</HealthData>\n')
            
        size_mb = path.stat().st_size / (1024 * 1024)
        self.log(f"  Created large XML: {path} ({size_mb:.1f} MB)")
        
    def clean_system_state(self):
        """Clean any existing app data to ensure clean state."""
        self.log("Cleaning system state...")
        
        # Clean AppData
        appdata_dir = Path(os.environ.get('APPDATA', '')) / 'AppleHealthDashboard'
        if appdata_dir.exists():
            try:
                shutil.rmtree(appdata_dir)
                self.log(f"  Removed AppData: {appdata_dir}")
            except Exception as e:
                self.log(f"  Warning: Could not remove AppData: {e}")
                
        # Clean registry entries (if any)
        # Note: In practice, we'd use winreg to clean registry
        
    def create_test_report_template(self):
        """Create test report template."""
        template = {
            "test_environment": self.os_info,
            "test_date": datetime.now().isoformat(),
            "tester_name": "",
            "package_info": {
                "version": "",
                "build_date": "",
                "file_size": "",
                "signature": ""
            },
            "test_results": {
                "installation": {},
                "features": {},
                "performance": {},
                "security": {},
                "update": {},
                "uninstall": {}
            },
            "issues": [],
            "notes": ""
        }
        
        report_path = self.test_dir / "test_report_template.json"
        with open(report_path, "w") as f:
            json.dump(template, f, indent=2)
            
        self.log(f"Created test report template: {report_path}")
        
    def setup_all(self):
        """Run all setup steps."""
        print("=" * 60)
        print("PACKAGING TEST ENVIRONMENT SETUP")
        print("=" * 60)
        
        # Create log directory first
        self.test_dir.mkdir(exist_ok=True)
        
        self.log("Starting test environment setup...")
        self.log(f"OS: {self.os_info['platform']} {self.os_info['version']}")
        
        # Check prerequisites
        prereqs = self.check_prerequisites()
        all_passed = all(prereqs.values())
        
        print("\nPrerequisite Checks:")
        for check, passed in prereqs.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}: {passed}")
            
        if not all_passed:
            self.log("ERROR: Not all prerequisites met!")
            if not prereqs["os_windows"]:
                self.log("This script must be run on Windows for packaging tests")
            return False
            
        # Continue with setup
        self.create_test_directories()
        self.download_test_files()
        self.clean_system_state()
        self.create_test_report_template()
        
        # Create batch file for easy test execution
        self._create_test_runner_batch()
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print(f"\nTest environment ready in: {self.test_dir.absolute()}")
        print("\nNext steps:")
        print("1. Copy packaged executables to test directories")
        print("2. Run tests using: run_packaging_tests.bat")
        print("3. Review results in the results/ directory")
        
        return True
        
    def _create_test_runner_batch(self):
        """Create batch file for running tests."""
        batch_content = '''@echo off
echo ========================================
echo Apple Health Dashboard Packaging Tests
echo ========================================

set TEST_DIR=%~dp0

echo.
echo Select test type:
echo 1. Direct EXE Test
echo 2. NSIS Installer Test  
echo 3. Portable ZIP Test
echo 4. All Tests
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto exe_test
if "%choice%"=="2" goto installer_test
if "%choice%"=="3" goto portable_test
if "%choice%"=="4" goto all_tests

echo Invalid choice!
goto end

:exe_test
echo.
echo Running EXE tests...
python test_packaged_app.py "%TEST_DIR%exe_tests\\AppleHealthDashboard.exe"
goto end

:installer_test
echo.
echo Running installer tests...
echo Please run the installer first, then press any key to continue...
pause
python test_packaged_app.py "C:\\Program Files\\Apple Health Dashboard\\AppleHealthDashboard.exe"
goto end

:portable_test
echo.
echo Running portable tests...
python test_packaged_app.py "%TEST_DIR%portable_tests\\AppleHealthDashboard.exe"
goto end

:all_tests
echo.
echo Running all tests...
call :exe_test
call :installer_test
call :portable_test
goto end

:end
echo.
echo Tests complete! Check results in the results/ directory.
pause
'''
        
        batch_path = self.test_dir / "run_packaging_tests.bat"
        with open(batch_path, "w") as f:
            f.write(batch_content)
            
        self.log(f"Created test runner: {batch_path}")


def main():
    """Main entry point."""
    setup = TestEnvironmentSetup()
    success = setup.setup_all()
    
    if not success:
        sys.exit(1)
        

if __name__ == "__main__":
    main()