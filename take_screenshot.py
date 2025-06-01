#!/usr/bin/env python3
"""Screenshot utility for capturing monitors on Windows via WSL with DPI scaling support."""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def take_screenshot():
    """Capture screenshot of primary monitor and save to ad hoc directory."""
    # Create ad hoc directory if it doesn't exist
    ad_hoc_dir = Path("ad hoc")
    ad_hoc_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = ad_hoc_dir / filename
    
    # PowerShell command to capture primary monitor with DPI awareness
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    # Enable DPI awareness
    Add-Type @'
    using System;
    using System.Runtime.InteropServices;
    public class User32 {{
        [DllImport("user32.dll")]
        public static extern bool SetProcessDPIAware();
        
        [DllImport("shcore.dll")]
        public static extern int GetDpiForMonitor(IntPtr hmonitor, int dpiType, out uint dpiX, out uint dpiY);
        
        [DllImport("user32.dll")]
        public static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint dwFlags);
    }}
'@

    # Set process DPI aware
    [User32]::SetProcessDPIAware()
    
    # Hardcoded scaling factor (150% = 1.5)
    # Note: Automatic detection is complex in PowerShell, using hardcoded value
    $scalingFactor = 1.5
    Write-Host "Using scaling factor: 150%"
    
    # Get primary screen bounds
    $primaryScreen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $primaryScreen.Bounds
    
    # For high DPI, the bounds are already in physical pixels when DPI aware
    Write-Host "Screen bounds: $($bounds.Width)x$($bounds.Height)"
    
    # Create bitmap with screen dimensions
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Set high quality rendering
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    
    # Copy from screen
    $graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bounds.Size)
    
    # Save the image
    $bitmap.Save('{filepath}', [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    Write-Host "Screenshot saved to: {filepath}"
    """
    
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)
        else:
            print(result.stdout.strip())
            return str(filepath)
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        sys.exit(1)

def take_screenshot_all_monitors():
    """Capture screenshot of all monitors combined and save to ad hoc directory."""
    # Create ad hoc directory if it doesn't exist
    ad_hoc_dir = Path("ad hoc")
    ad_hoc_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_all_monitors_{timestamp}.png"
    filepath = ad_hoc_dir / filename
    
    # PowerShell command to capture all monitors with DPI awareness
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    # Enable DPI awareness
    Add-Type @'
    using System;
    using System.Runtime.InteropServices;
    public class User32 {{
        [DllImport("user32.dll")]
        public static extern bool SetProcessDPIAware();
    }}
'@

    # Set process DPI aware
    [User32]::SetProcessDPIAware()
    
    # Hardcoded scaling factor (150% = 1.5)
    $scalingFactor = 1.5
    Write-Host "Using scaling factor: 150%"
    
    # Get virtual screen (all monitors combined)
    $virtualScreen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    
    Write-Host "Virtual screen bounds: $($virtualScreen.Width)x$($virtualScreen.Height) at ($($virtualScreen.X),$($virtualScreen.Y))"
    
    # Create bitmap for entire virtual screen
    $bitmap = New-Object System.Drawing.Bitmap $virtualScreen.Width, $virtualScreen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Set high quality rendering
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    
    # Copy from entire virtual screen
    $graphics.CopyFromScreen($virtualScreen.X, $virtualScreen.Y, 0, 0, $virtualScreen.Size)
    
    # Save the image
    $bitmap.Save('{filepath}', [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    
    # Get monitor info for display
    $screens = [System.Windows.Forms.Screen]::AllScreens
    Write-Host "Captured $($screens.Count) monitor(s) at 150% scaling:"
    foreach ($screen in $screens) {{
        $bounds = $screen.Bounds
        Write-Host "  - $($screen.DeviceName): $($bounds.Width)x$($bounds.Height) at ($($bounds.X), $($bounds.Y))"
    }}
    Write-Host "Screenshot saved to: {filepath}"
    """
    
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)
        else:
            print(result.stdout.strip())
            return str(filepath)
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture screenshots on Windows via WSL with DPI scaling support")
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Capture all monitors instead of just primary"
    )
    
    args = parser.parse_args()
    
    if args.all:
        take_screenshot_all_monitors()
    else:
        take_screenshot()