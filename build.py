#!/usr/bin/env python3
"""
Build script for Apple Health Monitor Dashboard
Creates Windows executable using PyInstaller

Supports multiple distribution formats:
- Standalone executable
- NSIS installer
- Portable ZIP package
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


# Set up logging
def setup_logging(log_dir: Path = None):
    """Set up logging configuration."""
    if log_dir is None:
        log_dir = Path('build/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_file = log_dir / f'build-{timestamp}.log'
    
    # Configure handlers with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # For Windows console, use a custom stream handler with UTF-8
    import sys
    if sys.platform == 'win32':
        # Try to set console to UTF-8 on Windows
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    stream_handler = logging.StreamHandler()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler, stream_handler]
    )
    return logging.getLogger(__name__)

def load_build_config() -> Dict:
    """Load build configuration from build_config.json."""
    config_file = Path('build_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Default configuration
    return {
        "app_name": "HealthMonitor",
        "app_display_name": "Apple Health Monitor",
        "icon": "assets/icon.ico",
        "upx_enabled": True,
        "upx_level": "--best",
        "hidden_imports": [
            "PyQt6.QtPrintSupport",
            "matplotlib.backends.backend_qtagg",
            "matplotlib.backends.backend_qt",
            "pandas._libs.tslibs.parsing"
        ],
        "excludes": [
            "PyQt5",
            "PySide2",
            "PySide6",
            "matplotlib.backends.backend_qt5agg",
            "matplotlib.backends.backend_qt5",
            "tkinter",
            "unittest",
            "pip",
            "setuptools"
        ],
        "nsis_template": "installer.nsi",
        "output_formats": ["exe", "zip", "installer"]
    }

def extract_version() -> str:
    """Extract version from src/version.py."""
    version_file = Path('src/version.py')
    if not version_file.exists():
        return "0.1.0"  # Default version
    
    with open(version_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    
    return "0.1.0"

def clean_build_artifacts():
    """Remove previous build artifacts."""
    logger = logging.getLogger(__name__)
    logger.info("Cleaning previous build artifacts...")
    
    dirs_to_remove = ['build/dist', 'build/work', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                # On Windows, try to remove read-only attributes first
                if sys.platform == 'win32':
                    import time
                    # Handle OneDrive sync issues
                    logger.info(f"  Preparing to remove {dir_name}/ (handling Windows/OneDrive)")
                    
                    # Remove read-only attributes recursively
                    for root, dirs, files in os.walk(dir_name):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0o777)
                        for f in files:
                            os.chmod(os.path.join(root, f), 0o777)
                    
                    # Give OneDrive/antivirus time to release files
                    time.sleep(1)
                
                logger.info(f"  Removing {dir_name}/")
                shutil.rmtree(dir_name, ignore_errors=False)
                
                # Double-check removal
                if os.path.exists(dir_name):
                    logger.warning(f"  Directory still exists, trying again...")
                    time.sleep(2)
                    shutil.rmtree(dir_name, ignore_errors=True)
                    
            except PermissionError as e:
                logger.warning(f"  Could not remove {dir_name}/ - {e}")
                logger.warning(f"  Try closing any programs using these files")
                logger.warning(f"  You may also need to pause OneDrive sync temporarily")
    
    # Remove .spec file if it exists (we'll use our custom one)
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec') and f != 'pyinstaller.spec']
    for spec_file in spec_files:
        logger.info(f"  Removing {spec_file}")
        os.remove(spec_file)

def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    logger = logging.getLogger(__name__)
    logger.info("Checking dependencies...")
    
    # Check for conflicting Qt packages
    qt_packages = ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']
    installed_qt = []
    
    logger.info("Checking for Qt bindings conflicts...")
    for qt_pkg in qt_packages:
        try:
            __import__(qt_pkg)
            installed_qt.append(qt_pkg)
            logger.info(f"  Found: {qt_pkg}")
        except ImportError:
            pass
    
    if 'PyQt5' in installed_qt and 'PyQt6' in installed_qt:
        logger.error("ERROR: Both PyQt5 and PyQt6 are installed!")
        logger.error("This will cause PyInstaller to fail.")
        logger.error("Please uninstall PyQt5 with: pip uninstall PyQt5")
        return False
    
    required_packages = ['PyInstaller', 'PyQt6', 'pandas', 'matplotlib', 'sqlalchemy']
    missing_packages = []
    
    for package in required_packages:
        try:
            # Import with proper case handling
            import_name = package.replace('-', '_')
            # Try original case first (for PyQt6, PyInstaller, etc.)
            try:
                __import__(import_name)
            except ImportError:
                # Fall back to lowercase for packages that use it
                __import__(import_name.lower())
            logger.info(f"  [OK] {package} is installed")
        except ImportError:
            logger.error(f"  [FAIL] {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error("Error: Missing required packages:")
        logger.error(f"Please install them with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_build_tools() -> Dict[str, bool]:
    """Check for optional build tools."""
    logger = logging.getLogger(__name__)
    tools = {}
    
    # Check for UPX
    try:
        result = subprocess.run(['upx', '--version'], capture_output=True, text=True)
        tools['upx'] = result.returncode == 0
        if tools['upx']:
            logger.info("  [OK] UPX is available")
        else:
            logger.warning("  [SKIP] UPX not found - compression will be skipped")
    except FileNotFoundError:
        tools['upx'] = False
        logger.warning("  [SKIP] UPX not found - compression will be skipped")
    
    # Check for NSIS
    try:
        result = subprocess.run(['makensis', '/VERSION'], capture_output=True, text=True)
        tools['nsis'] = result.returncode == 0
        if tools['nsis']:
            logger.info("  [OK] NSIS is available")
        else:
            logger.warning("  [SKIP] NSIS not found - installer creation will be skipped")
    except FileNotFoundError:
        tools['nsis'] = False
        logger.warning("  [SKIP] NSIS not found - installer creation will be skipped")
    
    return tools

def create_version_info_file(version: str, config: Dict) -> Path:
    """Create version info file for Windows executable."""
    logger = logging.getLogger(__name__)
    version_parts = version.split('.')
    if len(version_parts) < 4:
        version_parts.extend(['0'] * (4 - len(version_parts)))
    
    version_info_content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({', '.join(version_parts)}),
    prodvers=({', '.join(version_parts)}),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Apple Health Monitor'),
        StringStruct(u'FileDescription', u'{config["app_display_name"]}'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'{config["app_name"]}'),
        StringStruct(u'LegalCopyright', u'Copyright (C) {datetime.datetime.now().year}'),
        StringStruct(u'OriginalFilename', u'{config["app_name"]}.exe'),
        StringStruct(u'ProductName', u'{config["app_display_name"]}'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    version_file = Path('version_info.txt')
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    logger.info(f"Created version info file: {version_file}")
    return version_file

def build_executable(config: Dict, version: str, build_type: str = 'release', 
                    debug: bool = False, clean: bool = True, onefile: bool = False) -> bool:
    """Build the executable using PyInstaller."""
    logger = logging.getLogger(__name__)
    
    if clean:
        clean_build_artifacts()
    
    if not check_dependencies():
        return False
    
    # Create build directories
    build_dir = Path('build')
    dist_dir = build_dir / 'dist'
    work_dir = build_dir / 'work'
    
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)
    work_dir.mkdir(exist_ok=True)
    
    logger.info(f"\nBuilding {build_type} executable with PyInstaller...")
    if onefile:
        logger.info("Building single-file executable for direct distribution")
    
    # Create version info file
    version_info_file = create_version_info_file(version, config)
    
    # Build command
    # Choose spec file based on build mode
    if onefile:
        spec_file = Path('pyinstaller_onefile.spec')
    else:
        spec_file = Path('pyinstaller.spec')
    
    # Build base command
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--noconfirm',  # Don't ask for confirmation
        '--distpath', str(dist_dir),
        '--workpath', str(work_dir),
    ]
    
    if spec_file.exists():
        # When using spec file, just add the spec file path
        cmd.append(str(spec_file))
    else:
        # Build from main.py with options
        cmd.extend([
            'src/main.py',
            '--name', config['app_name'] if not onefile else 'AppleHealthMonitor',
            '--onefile' if onefile else '--onedir',  # Single file or directory bundle
            '--windowed' if build_type == 'release' else '--console',
            '--version-file', str(version_info_file),
            # Force exclude PyQt5 and other Qt bindings
            '--exclude-module', 'PyQt5',
            '--exclude-module', 'PySide2',
            '--exclude-module', 'PySide6',
        ])
        
        if config.get('icon'):
            icon_path = Path(config['icon'])
            if icon_path.exists():
                cmd.extend(['--icon', str(icon_path)])
        
        # Add hidden imports
        for hidden_import in config.get('hidden_imports', []):
            cmd.extend(['--hidden-import', hidden_import])
        
        # Add excludes
        for exclude in config.get('excludes', []):
            cmd.extend(['--exclude-module', exclude])
    
    if debug:
        cmd.append('--log-level=DEBUG')
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True)
        
        logger.info("\nBuild completed successfully!")
        
        # Determine executable path based on build mode
        if onefile:
            exe_path = dist_dir / "AppleHealthMonitor.exe"
        else:
            exe_path = dist_dir / config['app_name'] / f"{config['app_name']}.exe"
        
        if exe_path.exists():
            original_size = exe_path.stat().st_size / (1024 * 1024)
            logger.info(f"Original executable size: {original_size:.1f} MB")
            
            if config.get('upx_enabled') and check_build_tools().get('upx'):
                logger.info("Applying UPX compression...")
                upx_cmd = ['upx', config.get('upx_level', '--best'), str(exe_path)]
                try:
                    subprocess.run(upx_cmd, check=True)
                    compressed_size = exe_path.stat().st_size / (1024 * 1024)
                    reduction = (1 - compressed_size / original_size) * 100
                    logger.info(f"Compressed size: {compressed_size:.1f} MB ({reduction:.1f}% reduction)")
                except subprocess.CalledProcessError:
                    logger.warning("UPX compression failed, continuing without compression")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"\nError: Build failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"\nError during build: {e}")
        return False
    finally:
        # Clean up version info file
        if version_info_file.exists():
            version_info_file.unlink()

def test_executable(config: Dict) -> bool:
    """Run basic tests on the built executable."""
    logger = logging.getLogger(__name__)
    logger.info("\nTesting executable...")
    
    exe_path = Path('build/dist') / config['app_name'] / f"{config['app_name']}.exe"
    
    if not exe_path.exists():
        logger.error("Error: Executable not found. Build may have failed.")
        return False
    
    # Test 1: Check if executable runs with --version
    logger.info("  Testing --version flag...")
    try:
        result = subprocess.run(
            [str(exe_path), '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"    [OK] Version output: {result.stdout.strip()}")
        else:
            logger.error(f"    [FAIL] Failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"    Error output: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"    [FAIL] Error: {e}")
        return False
    
    logger.info("\nAll tests passed!")
    return True

def create_portable_zip(config: Dict, version: str) -> bool:
    """Create portable ZIP distribution."""
    logger = logging.getLogger(__name__)
    logger.info("\nCreating portable ZIP distribution...")
    
    dist_dir = Path('build/dist') / config['app_name']
    if not dist_dir.exists():
        logger.error("Error: Distribution directory not found. Build first.")
        return False
    
    output_dir = Path('build/dist')
    output_name = f"{config['app_name']}-{version}-portable"
    output_file = output_dir / f"{output_name}.zip"
    
    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files from distribution
            for file_path in dist_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(dist_dir.parent)
                    zf.write(file_path, arcname)
            
            # Add portable marker file
            zf.writestr(f"{config['app_name']}/portable.marker", 
                       "This file indicates portable mode. Do not delete.")
            
            # Add README for portable version
            readme_content = f"""Apple Health Monitor - Portable Version {version}
================================================

This is a portable version that can be run from any location.
No installation required.

INSTRUCTIONS:
-------------
1. Extract this ZIP file to any location (USB drive, folder, etc.)
2. Double-click {config['app_name']}.exe to run
3. All data will be stored in the 'data' folder next to the executable

PORTABLE MODE:
--------------
This version stores all data locally in the application folder:
- Database: data/health_monitor.db
- Journal entries: data/journals/
- Preferences: data/preferences.json

You can move the entire folder to any location and your data will travel with it.

SYSTEM REQUIREMENTS:
-------------------
- Windows 10 or later
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space

NOTES:
------
- First run may take a moment as Windows verifies the executable
- Windows Defender may scan the file on first run - this is normal
- Your antivirus may flag the executable - add an exception if needed

For support, visit: https://github.com/yourusername/apple-health-monitor
"""
            zf.writestr(f"{config['app_name']}/README.txt", readme_content)
            
            # Create empty data directory structure
            zf.writestr(f"{config['app_name']}/data/README.txt", 
                       "This folder contains your health data and application settings.")
        
        size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"  [OK] Created {output_file.name} ({size_mb:.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"Error creating ZIP: {e}")
        return False

def create_nsis_installer(config: Dict, version: str) -> bool:
    """Create NSIS installer."""
    logger = logging.getLogger(__name__)
    
    if not check_build_tools().get('nsis'):
        logger.warning("NSIS not available, skipping installer creation")
        return False
    
    logger.info("\nCreating NSIS installer...")
    
    # Check if NSIS template exists
    nsis_template = Path(config.get('nsis_template', 'installer.nsi'))
    if not nsis_template.exists():
        logger.info("Creating default NSIS script...")
        nsis_content = f"""!define PRODUCT_NAME "{config['app_display_name']}"
!define PRODUCT_VERSION "{version}"
!define PRODUCT_PUBLISHER "Apple Health Monitor"
!define PRODUCT_DIR_REGKEY "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{config['app_name']}.exe"
!define PRODUCT_UNINST_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}"

!include "MUI2.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\\{config['app_name']}.exe"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

Name "${{PRODUCT_NAME}} ${{PRODUCT_VERSION}}"
OutFile "build\\dist\\{config['app_name']}-${{PRODUCT_VERSION}}-installer.exe"
InstallDir "$PROGRAMFILES\\{config['app_display_name']}"
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "build\\dist\\{config['app_name']}\\*.*"
  CreateDirectory "$SMPROGRAMS\\{config['app_display_name']}"
  CreateShortCut "$SMPROGRAMS\\{config['app_display_name']}\\{config['app_display_name']}.lnk" "$INSTDIR\\{config['app_name']}.exe"
  CreateShortCut "$DESKTOP\\{config['app_display_name']}.lnk" "$INSTDIR\\{config['app_name']}.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\\uninst.exe"
  WriteRegStr HKLM "${{PRODUCT_DIR_REGKEY}}" "" "$INSTDIR\\{config['app_name']}.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayName" "$(^Name)"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "UninstallString" "$INSTDIR\\uninst.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayIcon" "$INSTDIR\\{config['app_name']}.exe"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
  WriteRegStr HKLM "${{PRODUCT_UNINST_KEY}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
SectionEnd

Section Uninstall
  Delete "$INSTDIR\\uninst.exe"
  Delete "$INSTDIR\\*.*"
  Delete "$SMPROGRAMS\\{config['app_display_name']}\\*.*"
  Delete "$DESKTOP\\{config['app_display_name']}.lnk"
  
  RMDir "$SMPROGRAMS\\{config['app_display_name']}"
  RMDir "$INSTDIR"
  
  DeleteRegKey HKLM "${{PRODUCT_UNINST_KEY}}"
  DeleteRegKey HKLM "${{PRODUCT_DIR_REGKEY}}"
  SetAutoClose true
SectionEnd
"""
        with open(nsis_template, 'w') as f:
            f.write(nsis_content)
    
    # Run NSIS
    try:
        cmd = ['makensis', str(nsis_template)]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        installer_path = Path('build/dist') / f"{config['app_name']}-{version}-installer.exe"
        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            logger.info(f"  [OK] Created installer: {installer_path.name} ({size_mb:.1f} MB)")
            return True
        else:
            logger.error("Installer file not found after NSIS execution")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"NSIS failed: {e}")
        if e.stderr:
            logger.error(e.stderr)
        return False
    except Exception as e:
        logger.error(f"Error creating installer: {e}")
        return False

def create_all_distribution_formats(config: Dict, version: str) -> Dict[str, bool]:
    """Create all three distribution formats as specified in ADR-003."""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "="*60)
    logger.info("Creating All Three Distribution Formats")
    logger.info("="*60)
    
    results = {}
    
    # 1. Build directory bundle for installer
    logger.info("\n1. Building directory bundle for installer...")
    results['bundle'] = build_executable(config, version, onefile=False)
    
    if results['bundle']:
        # 2. Create NSIS installer
        logger.info("\n2. Creating NSIS installer...")
        results['installer'] = create_nsis_installer(config, version)
        
        # 3. Create portable ZIP
        logger.info("\n3. Creating portable ZIP distribution...")
        results['zip'] = create_portable_zip(config, version)
    
    # 4. Build single-file executable
    logger.info("\n4. Building single-file executable...")
    results['onefile'] = build_executable(config, version, onefile=True, clean=False)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Distribution Creation Summary:")
    logger.info("="*60)
    
    if results.get('bundle'):
        logger.info("[OK] Directory bundle: build/dist/HealthMonitor/")
    else:
        logger.error("[FAIL] Directory bundle: FAILED")
    
    if results.get('installer'):
        installer_path = Path('build/dist') / f"{config['app_name']}-{version}-installer.exe"
        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            logger.info(f"[OK] NSIS installer: {installer_path.name} ({size_mb:.1f} MB)")
    else:
        logger.error("[FAIL] NSIS installer: FAILED or skipped")
    
    if results.get('zip'):
        zip_path = Path('build/dist') / f"{config['app_name']}-{version}-portable.zip"
        if zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            logger.info(f"[OK] Portable ZIP: {zip_path.name} ({size_mb:.1f} MB)")
    else:
        logger.error("[FAIL] Portable ZIP: FAILED")
    
    if results.get('onefile'):
        exe_path = Path('build/dist') / "AppleHealthMonitor.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            logger.info(f"[OK] Single executable: {exe_path.name} ({size_mb:.1f} MB)")
    else:
        logger.error("[FAIL] Single executable: FAILED")
    
    logger.info("\n" + "="*60)
    
    return results

def package_all_formats(config: Dict, version: str) -> Dict[str, bool]:
    """Package all configured distribution formats (legacy function)."""
    return create_all_distribution_formats(config, version)

def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description='Build Apple Health Monitor Dashboard')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--no-clean', action='store_true', help='Skip cleaning build artifacts')
    parser.add_argument('--test', action='store_true', help='Test the built executable')
    parser.add_argument('--package', action='store_true', help='Package all distribution formats')
    parser.add_argument('--all-formats', action='store_true', help='Create all three distribution formats (exe, installer, zip)')
    parser.add_argument('--format', choices=['exe', 'zip', 'installer', 'onefile', 'all'], 
                       default='all', help='Distribution format to create')
    parser.add_argument('--build-type', choices=['debug', 'release'], 
                       default='release', help='Build type (debug includes console)')
    parser.add_argument('--config', type=str, help='Path to build configuration file')
    parser.add_argument('--version', type=str, help='Override version number')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    
    logger.info("Apple Health Monitor Dashboard - Build Script")
    logger.info("=" * 50)
    
    # Load configuration
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)
    else:
        config = load_build_config()
    
    # Get version
    version = args.version or extract_version()
    logger.info(f"Building version: {version}")
    
    # Check build tools
    logger.info("\nChecking build tools...")
    tools = check_build_tools()
    
    # Handle --all-formats flag
    if args.all_formats:
        results = create_all_distribution_formats(config, version)
        if not all(results.values()):
            logger.warning("\nSome distribution formats failed to build")
            sys.exit(1)
        else:
            logger.info("\nAll distribution formats created successfully!")
        return
    
    # Build executable
    if not build_executable(config, version, build_type=args.build_type, 
                          debug=args.debug, clean=not args.no_clean,
                          onefile=(args.format == 'onefile')):
        logger.error("\nBuild failed!")
        sys.exit(1)
    
    # Test if requested
    if args.test:
        if not test_executable(config):
            logger.error("\nTests failed!")
            sys.exit(1)
    
    # Package if requested
    if args.package:
        if args.format == 'all':
            results = package_all_formats(config, version)
            if not all(results.values()):
                logger.warning("Some packaging formats failed")
                for fmt, success in results.items():
                    if not success:
                        logger.error(f"  [FAIL] {fmt} packaging failed")
        else:
            # Package specific format
            if args.format == 'zip':
                if not create_portable_zip(config, version):
                    logger.error("ZIP packaging failed!")
                    sys.exit(1)
            elif args.format == 'installer':
                if not create_nsis_installer(config, version):
                    logger.error("Installer creation failed!")
                    sys.exit(1)
            elif args.format == 'onefile':
                logger.info("Single-file executable already built.")
    
    logger.info("\nBuild process completed successfully!")
    logger.info("\nBuild artifacts:")
    if args.format == 'onefile':
        logger.info(f"  Single executable: build/dist/AppleHealthMonitor.exe")
    else:
        logger.info(f"  Executable: build/dist/{config['app_name']}/{config['app_name']}.exe")
    
    if args.package:
        logger.info(f"  Portable ZIP: build/dist/{config['app_name']}-{version}-portable.zip")
        if tools.get('nsis'):
            logger.info(f"  Installer: build/dist/{config['app_name']}-{version}-installer.exe")
    
    logger.info("\nTo create all three distribution formats:")
    logger.info("  python build.py --all-formats")

def create_default_build_config():
    """Create default build_config.json if it doesn't exist."""
    config_file = Path('build_config.json')
    if not config_file.exists():
        default_config = {
            "app_name": "HealthMonitor",
            "app_display_name": "Apple Health Monitor",
            "icon": "assets/icon.ico",
            "upx_enabled": True,
            "upx_level": "--best",
            "hidden_imports": [
                "PyQt6.QtPrintSupport",
                "matplotlib.backends.backend_qtagg",
                "matplotlib.backends.backend_qt",
                "pandas._libs.tslibs.parsing",
                "sqlalchemy.sql.default_comparator"
            ],
            "excludes": [
                "PyQt5",
                "PySide2",
                "PySide6",
                "matplotlib.backends.backend_qt5agg",
                "matplotlib.backends.backend_qt5",
                "tkinter",
                "unittest",
                "pip",
                "setuptools",
                "wheel",
                "pytest",
                "sphinx"
            ],
            "nsis_template": "installer.nsi",
            "output_formats": ["exe", "zip", "installer"],
            "data_files": [
                {"source": "assets", "destination": "assets"},
                {"source": "LICENSE.txt", "destination": "."},
                {"source": "README.md", "destination": "."}
            ]
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Created default build configuration: {config_file}")

if __name__ == '__main__':
    # Create default config if needed
    create_default_build_config()
    main()