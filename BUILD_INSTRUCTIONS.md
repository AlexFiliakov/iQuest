# Build Instructions for Apple Health Monitor Dashboard

This document provides instructions for building all three distribution formats of the Apple Health Monitor Dashboard.

## Prerequisites

1. **Python 3.10+** installed
2. **All dependencies installed**: `pip install -r requirements.txt`
3. **PyInstaller**: Included in requirements.txt
4. **Optional tools**:
   - **UPX**: For executable compression (download from https://upx.github.io/)
   - **NSIS**: For creating Windows installer (download from https://nsis.sourceforge.io/)

## Quick Start

To create all three distribution formats at once:

```bash
python build.py --all-formats
```

This will create:
1. **Directory bundle**: For the NSIS installer (`build/dist/HealthMonitor/`)
2. **NSIS installer**: Professional Windows installer (`build/dist/HealthMonitor-1.0.0-installer.exe`)
3. **Portable ZIP**: Self-contained portable version (`build/dist/HealthMonitor-1.0.0-portable.zip`)
4. **Single executable**: Standalone EXE file (`build/dist/AppleHealthMonitor.exe`)

## Individual Build Commands

### 1. Direct Executable (Single File)

Creates a single executable file that can be run without installation:

```bash
python build.py --format onefile
```

Output: `build/dist/AppleHealthMonitor.exe`

**Characteristics**:
- Single file, easy to distribute
- Slower startup (extracts to temp directory)
- Stores data in `%LOCALAPPDATA%\AppleHealthMonitor`

### 2. Directory Bundle

Creates a directory with all required files:

```bash
python build.py
```

Output: `build/dist/HealthMonitor/`

**Characteristics**:
- Faster startup
- Required for creating the installer
- Can be run directly from the directory

### 3. NSIS Installer

Creates a professional Windows installer:

```bash
python build.py --package --format installer
```

Output: `build/dist/HealthMonitor-1.0.0-installer.exe`

**Characteristics**:
- Professional installation experience
- Creates Start Menu shortcuts
- Optional desktop shortcut
- Uninstaller included
- No admin rights required

### 4. Portable ZIP

Creates a portable version that stores data alongside the executable:

```bash
python build.py --package --format zip
```

Output: `build/dist/HealthMonitor-1.0.0-portable.zip`

**Characteristics**:
- Self-contained, no installation needed
- Data stored in `data/` folder next to executable
- Can run from USB drive
- Perfect for users who can't install software

## Build Options

### Debug Build

Include console window for debugging:

```bash
python build.py --build-type debug
```

### Skip Cleaning

Don't clean previous build artifacts:

```bash
python build.py --no-clean
```

### Test Executable

Run basic tests on the built executable:

```bash
python build.py --test
```

### Custom Version

Override the version number:

```bash
python build.py --version 2.0.0 --all-formats
```

## Configuration

Edit `build_config.json` to customize:
- Application name and display name
- Icon file path
- UPX compression settings
- Hidden imports and exclusions
- Output formats

## Distribution Format Comparison

| Format | File Size | Startup Speed | Installation | Data Location | Best For |
|--------|-----------|---------------|--------------|---------------|----------|
| Single EXE | ~150MB | Slower | None | %LOCALAPPDATA% | Quick distribution |
| Installer | ~80MB | Fast | Required | %LOCALAPPDATA% | Professional deployment |
| Portable ZIP | ~85MB | Fast | Extract only | ./data folder | USB/portable use |

## Troubleshooting

### Missing Dependencies

If build fails with import errors:
```bash
pip install -r requirements.txt
```

### UPX Not Found

Download UPX and add to PATH, or disable in `build_config.json`:
```json
{
  "upx_enabled": false
}
```

### NSIS Not Found

Install NSIS or skip installer creation:
```bash
python build.py --package --format zip
```

### Antivirus Warnings

Some antivirus software may flag PyInstaller executables. This is a false positive. You can:
1. Add an exception for the executable
2. Submit the file to your AV vendor for analysis
3. Code-sign the executable (see T04_S07)

## Testing Distributions

After building, test each format:

1. **Single EXE**: Run directly, verify data saves to AppData
2. **Installer**: Install, run, uninstall, verify cleanup
3. **Portable**: Extract to USB, run, verify data portability

## Next Steps

- Code signing: See task T04_S07
- Auto-update system: See task T05_S07
- User documentation: See task T06_S07