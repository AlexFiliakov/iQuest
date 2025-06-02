# WSL Setup Guide for Apple Health Monitor Dashboard

## Problem Summary

When running the Apple Health Monitor Dashboard in WSL (Windows Subsystem for Linux), you may encounter two main issues:

1. **Database I/O Error**: If your project is in a OneDrive folder, SQLite may fail with "disk I/O error"
2. **Qt Platform Plugin Error**: PyQt6 requires additional system libraries in WSL

## Solutions

### 1. Database I/O Error (OneDrive Issue)

The application automatically detects if it's running from a OneDrive folder and creates a temporary copy of the database outside OneDrive. This is handled in `src/config.py`.

If you still experience issues:
- Close OneDrive temporarily while using the app
- Or move the project folder outside of OneDrive

### 2. Qt Platform Plugin Error

The error message:
```
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
```

To fix this, install the required system libraries:

```bash
# For Ubuntu/Debian-based WSL:
sudo apt update
sudo apt install libxcb-cursor0

# If that doesn't work, try:
sudo apt install libxcb-cursor0 libxcb-cursor-dev

# You may also need:
sudo apt install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0
```

### 3. X Server Setup (if needed)

WSL2 includes WSLg which provides built-in X server support. However, if you're using WSL1 or having display issues:

1. Install an X server on Windows (e.g., VcXsrv, Xming, or MobaXterm)
2. Set the DISPLAY variable in WSL:
   ```bash
   export DISPLAY=:0
   # Or for WSL2 with external X server:
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

### 4. Running the Application

After fixing the dependencies:

```bash
cd "/mnt/c/Users/alexf/OneDrive/Documents/Projects/Apple Health Exports"
python src/main.py
```

## Troubleshooting

If you continue to have issues:

1. **Check Qt plugins are found**:
   ```bash
   python -c "from PyQt6.QtCore import QCoreApplication; print(QCoreApplication.libraryPaths())"
   ```

2. **Enable Qt debugging**:
   ```bash
   export QT_DEBUG_PLUGINS=1
   python src/main.py
   ```

3. **Try minimal platform** (headless mode):
   ```bash
   export QT_QPA_PLATFORM=minimal
   python src/main.py
   ```

## Alternative: Running on Windows

If WSL issues persist, consider running the application directly on Windows:

1. Install Python 3.10+ for Windows
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python src/main.py`

This avoids both the OneDrive database issue and Qt platform plugin issues.