@echo off
REM Clean build artifacts for Windows with OneDrive handling
REM Run this if you get permission errors during build

echo Cleaning build artifacts...
echo.

REM Try to stop any processes that might be using the files
echo Attempting to clean build directories...

REM Force remove build directories
if exist "build\work" (
    echo Removing build\work...
    rmdir /s /q "build\work" 2>nul
    if exist "build\work" (
        echo Failed to remove build\work - trying with timeout...
        timeout /t 2 /nobreak >nul
        rmdir /s /q "build\work" 2>nul
    )
)

if exist "build\dist" (
    echo Removing build\dist...
    rmdir /s /q "build\dist" 2>nul
)

if exist "dist" (
    echo Removing dist...
    rmdir /s /q "dist" 2>nul
)

if exist "__pycache__" (
    echo Removing __pycache__...
    rmdir /s /q "__pycache__" 2>nul
)

REM Remove any .spec files except our custom ones
for %%f in (*.spec) do (
    if not "%%f"=="pyinstaller.spec" if not "%%f"=="pyinstaller_onefile.spec" (
        echo Removing %%f...
        del "%%f" 2>nul
    )
)

echo.
echo Cleanup complete!
echo.
echo If you still get permission errors:
echo 1. Close any programs that might be using the build files
echo 2. Pause OneDrive sync temporarily
echo 3. Run this script as Administrator
echo 4. Try running: build.py --incremental (to skip cleaning)
echo.
pause