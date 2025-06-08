# PyInstaller 6.14.0 Migration Summary

This document summarizes the changes made to update the Apple Health Monitor Dashboard build scripts for compatibility with PyInstaller 6.14.0.

## Changes Made

### 1. Updated `pyinstaller.spec`

The following deprecated parameters were removed or updated:

- **Removed from `Analysis` class:**
  - `win_no_prefer_redirects` - Removed in PyInstaller 6.x
  - `win_private_assemblies` - Removed in PyInstaller 6.x

- **Updated in `EXE` class:**
  - Commented out `argv_emulation` - This parameter was removed in PyInstaller 6.x (was only relevant for macOS)
  - Replaced `uac_admin` with `uac_uiaccess` - The parameter name changed in PyInstaller 6.x

### 2. Created `pyinstaller_onefile.spec`

A new spec file was created for single-file builds with the same PyInstaller 6.x compatibility updates:
- Uses the same parameter updates as the main spec file
- Configured for single-file output (includes all binaries and data in the EXE)

### 3. Updated `build.py`

- Added compatibility note in the module docstring indicating PyInstaller 6.14.0+ support
- Updated `create_version_info_file` function documentation to note PyInstaller 6.x compatibility

## Key PyInstaller 6.x Changes

1. **Removed Windows-specific parameters**: The `win_no_prefer_redirects` and `win_private_assemblies` parameters are no longer needed or supported.

2. **UAC parameter rename**: The `uac_admin` parameter has been replaced with `uac_uiaccess` for better clarity about what it controls.

3. **macOS-specific parameter removal**: The `argv_emulation` parameter was removed as it was only relevant for macOS builds.

4. **Block cipher handling**: While `block_cipher` is still supported, PyInstaller 6.x recommends using the `cipher` parameter directly in Analysis and PYZ classes.

## Testing Recommendations

After these updates, test the build process with:

```bash
# Test directory bundle build
python build.py --format exe

# Test single-file build
python build.py --format onefile

# Test all distribution formats
python build.py --all-formats
```

## Compatibility

These changes maintain backward compatibility with the existing build process while ensuring forward compatibility with PyInstaller 6.14.0 and future 6.x releases.

The `requirements.txt` file already specifies `PyInstaller>=6.14.0`, ensuring users will get a compatible version.