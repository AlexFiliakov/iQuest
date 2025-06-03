# Build Process Documentation

## Overview

The Apple Health Monitor Dashboard uses an automated build system to create Windows executables and distribution packages. The build process is designed to be reproducible both locally and in CI/CD environments.

## Prerequisites

### Required Dependencies
- Python 3.10 or later
- PyInstaller
- All packages in `requirements.txt`

### Optional Build Tools
- **UPX** (Ultimate Packer for eXecutables): For executable compression
  - Download from: https://github.com/upx/upx/releases
  - Reduces executable size by ~40%
- **NSIS** (Nullsoft Scriptable Install System): For creating Windows installers
  - Download from: https://nsis.sourceforge.io/
  - Required only for installer creation

## Build Configuration

The build process is configured via `build_config.json`:

```json
{
  "app_name": "HealthMonitor",
  "app_display_name": "Apple Health Monitor",
  "icon": "assets/icon.ico",
  "upx_enabled": true,
  "upx_level": "--best",
  "hidden_imports": [...],
  "excludes": [...],
  "output_formats": ["exe", "zip", "installer"]
}
```

## Local Build Process

### Basic Build
```bash
python build.py
```

### Build with All Distribution Formats
```bash
python build.py --package
```

### Build Options
- `--debug`: Enable debug output and console window
- `--no-clean`: Skip cleaning previous build artifacts
- `--test`: Run basic tests on the built executable
- `--package`: Create all distribution formats
- `--format [exe|zip|installer|all]`: Specific format to build
- `--build-type [debug|release]`: Build type (default: release)
- `--version X.Y.Z`: Override version number

### Examples

Debug build with console:
```bash
python build.py --build-type debug
```

Create only portable ZIP:
```bash
python build.py --package --format zip
```

Build specific version:
```bash
python build.py --version 1.2.3 --package
```

## CI/CD Build Process

### GitHub Actions Workflow

The automated build is triggered by:
1. Pushing a tag matching `v*` (e.g., `v1.0.0`)
2. Manual workflow dispatch

### Workflow Steps
1. Set up Windows environment
2. Install Python and dependencies
3. Run unit tests
4. Extract version from tag or `src/version.py`
5. Install build tools (UPX, NSIS)
6. Build executable with PyInstaller
7. Apply UPX compression
8. Create distribution packages
9. Upload artifacts
10. Create GitHub release (for tags)

### Triggering a Release Build

```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0
```

## Build Outputs

### Directory Structure
```
build/
├── dist/
│   ├── HealthMonitor/              # Standalone executable bundle
│   │   ├── HealthMonitor.exe
│   │   └── (supporting files)
│   ├── HealthMonitor-X.Y.Z-portable.zip
│   └── HealthMonitor-X.Y.Z-installer.exe
├── work/                           # Temporary build files
└── logs/
    └── build-YYYYMMDD-HHMMSS.log
```

### Distribution Formats

1. **Standalone Executable** (`HealthMonitor.exe`)
   - One-folder bundle with all dependencies
   - Can be run from any location
   - ~70MB compressed with UPX

2. **Portable ZIP** (`HealthMonitor-X.Y.Z-portable.zip`)
   - Compressed archive of standalone executable
   - Includes README for portable usage
   - Data stored next to executable

3. **Windows Installer** (`HealthMonitor-X.Y.Z-installer.exe`)
   - Standard Windows installer experience
   - Creates Start Menu shortcuts
   - Includes uninstaller
   - Registers with Windows Programs

## Version Management

Version is extracted from `src/version.py`:
```python
__version__ = "0.1.0"
```

The version is embedded in:
- Executable metadata
- File names
- Installer registry entries
- About dialog (in app)

## Troubleshooting

### Common Issues

1. **Missing dependencies**
   ```
   Error: Missing required packages
   ```
   Solution: `pip install -r requirements.txt pyinstaller`

2. **UPX not found**
   ```
   ⚠ UPX not found - compression will be skipped
   ```
   Solution: Install UPX and add to PATH, or disable in `build_config.json`

3. **NSIS not found**
   ```
   ⚠ NSIS not found - installer creation will be skipped
   ```
   Solution: Install NSIS or remove "installer" from output_formats

4. **Antivirus false positives**
   - Some antivirus software may flag PyInstaller executables
   - Code signing (future enhancement) will help reduce this
   - Users may need to whitelist the application

### Build Logs

Detailed logs are saved in `build/logs/` with timestamps. Check these for:
- Exact error messages
- Hidden import issues
- File not found errors
- Compression statistics

## Advanced Configuration

### Custom PyInstaller Spec

The build uses `pyinstaller.spec` if present. Key sections:
- `hiddenimports`: Modules not automatically detected
- `excludes`: Modules to exclude for size optimization
- `datas`: Additional files to include
- `exe`: Executable configuration

### Optimizing Build Size

1. Review and update `excludes` in build config
2. Enable UPX compression
3. Remove unnecessary hidden imports
4. Use `--log-level DEBUG` to identify included modules

## Security Considerations

1. **Code Signing** (Future)
   - Reduces antivirus false positives
   - Provides authenticity verification
   - Required for some enterprise deployments

2. **Build Environment**
   - Use clean build environments
   - Verify all dependencies
   - Pin dependency versions

3. **Distribution**
   - Use HTTPS for all downloads
   - Provide checksums for verification
   - Document known issues with antivirus software