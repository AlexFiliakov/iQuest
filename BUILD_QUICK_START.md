# Apple Health Monitor Dashboard - Build Instructions

## Quick Start - Incremental Builds

For fast development builds that only rebuild changed files:

```bash
# Unix/Linux/macOS/WSL
python build_incremental.py

# Windows
build_incremental.bat
```

## Icon

The application now uses a heart emoji icon (💖) as specified. The icon files are:
- `assets/heart_icon.ico` - Multi-resolution Windows icon
- `assets/heart_icon_*.png` - Individual PNG files for each size

## Build Options

### Incremental Build (Fastest - Recommended for Development)
Only rebuilds if source files have changed:
```bash
python build.py --incremental
```

### Full Rebuild
Cleans all artifacts and rebuilds from scratch:
```bash
python build.py
```

### Build All Distribution Formats
Creates executable, installer, and portable ZIP:
```bash
python build.py --all-formats

# Or with incremental build:
python build.py --all-formats --incremental
```

### Debug Build
Includes console window for debugging:
```bash
python build.py --build-type debug
```

## Build Artifacts

After building, you'll find:
- **Executable**: `build/dist/HealthMonitor/HealthMonitor.exe`
- **Installer**: `build/dist/HealthMonitor-{version}-installer.exe` (if NSIS is installed)
- **Portable ZIP**: `build/dist/HealthMonitor-{version}-portable.zip`
- **Single File EXE**: `build/dist/AppleHealthMonitor.exe` (when using --format onefile)

## Incremental Build Benefits

The incremental build mode:
1. **Skips cleaning** build artifacts
2. **Checks timestamps** to see if rebuild is needed
3. **Reuses PyInstaller cache** for unchanged modules
4. **Typically 5-10x faster** than full rebuild

Perfect for development when you're making frequent changes!

## Troubleshooting

### Permission Errors (Windows/OneDrive)

If you get "Access is denied" errors:

1. **Use incremental builds** (recommended):
   ```bash
   python build.py --incremental
   ```

2. **Clean manually** before building:
   ```bash
   # Windows Command Prompt
   clean_build_windows.bat
   
   # Or PowerShell (run as Administrator)
   powershell -ExecutionPolicy Bypass -File clean_build_force.ps1
   ```

3. **Pause OneDrive sync** temporarily during builds

4. **Alternative**: Copy project to a non-OneDrive location

### Other Issues

If incremental builds fail:
1. Run a full clean build: `python build.py`
2. Check for PyQt5 conflicts: `pip uninstall PyQt5`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## Custom Icon

To change the icon:
1. Replace `assets/heart_icon.ico` with your icon
2. Update `build_config.json` to point to the new icon
3. Rebuild the application