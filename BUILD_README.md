# Building Apple Health Monitor Dashboard

This document describes how to build the Apple Health Monitor Dashboard as a Windows executable using PyInstaller.

## Prerequisites

1. **Python 3.10+** installed
2. **All dependencies installed**: `pip install -r requirements.txt`
3. **Windows OS** (or Windows in a VM for cross-platform builds)

## Quick Build

To build the executable with default settings:

```bash
python build.py
```

The executable will be created in `dist/HealthMonitor/HealthMonitor.exe`

## Build Options

### Debug Build
```bash
python build.py --debug
```
Enables verbose logging during the build process.

### Skip Cleaning
```bash
python build.py --no-clean
```
Preserves previous build artifacts (useful for debugging).

### Test Executable
```bash
python build.py --test
```
Runs basic tests on the built executable.

### Create Distribution Package
```bash
python build.py --package
```
Creates a ZIP file for distribution.

### Full Build with Testing and Packaging
```bash
python build.py --test --package
```

## Build Configuration

The build is configured through `pyinstaller.spec` which includes:

- **Application metadata** and version information
- **Icon** (heart on fire emoji ❤️‍🔥)
- **Hidden imports** for all dependencies
- **Asset bundling** (fonts, images, configs)
- **Optimizations** for size reduction

## Troubleshooting

### Missing Dependencies
If the build fails due to missing imports:
1. Check `pyinstaller.spec` for hidden imports
2. Add missing modules to the `hiddenimports` list
3. Rebuild with `python build.py`

### Large Executable Size
The executable includes all dependencies. To reduce size:
1. Ensure UPX is installed for compression
2. Review exclusions in `pyinstaller.spec`
3. Consider using `--onefile` mode (slower startup)

### Antivirus False Positives
Some antivirus software may flag PyInstaller executables:
1. Code signing is implemented in later sprint tasks
2. Submit to antivirus vendors for whitelisting
3. Document known false positives

## Build Output

After a successful build:
```
dist/
└── HealthMonitor/
    ├── HealthMonitor.exe      # Main executable
    ├── assets/                # Bundled assets
    │   ├── fonts/            # Application fonts
    │   └── icon.ico          # Application icon
    └── [various .dll files]   # Required libraries
```

## Distribution

The built application can be distributed as:
1. **Folder** - Copy the entire `dist/HealthMonitor/` directory
2. **ZIP** - Use `python build.py --package`
3. **Installer** - Will be created in Task T03_S07

## Version Management

Version information is managed in `src/version.py` and embedded in:
- Executable metadata
- Application UI
- Distribution packages

## Next Steps

After building the executable:
1. Test on a clean Windows system
2. Check for missing dependencies
3. Verify all features work correctly
4. Document any issues found

For automated builds and CI/CD integration, see Task T02_S07.