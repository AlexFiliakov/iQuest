@echo off
REM Quick incremental build for Apple Health Monitor Dashboard
REM Uses incremental builds by default for faster development

echo Running incremental build...
echo.

python build.py --incremental %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo Executable: build\dist\HealthMonitor\HealthMonitor.exe
    echo.
    echo To create all distribution formats, run: build_incremental.bat --all-formats
) else (
    echo.
    echo Build failed!
    exit /b %ERRORLEVEL%
)