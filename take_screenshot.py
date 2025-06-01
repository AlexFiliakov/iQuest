#!/usr/bin/env python3
"""Screenshot utility for capturing monitors on Windows via WSL."""

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
    
    # PowerShell command to capture primary monitor with full height
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    # Get primary screen
    $primaryScreen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $primaryScreen.Bounds
    
    # Create bitmap with exact screen dimensions
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Copy from screen using exact bounds
    $graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bitmap.Size)
    
    # Save the image
    $bitmap.Save('{filepath}')
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
    
    # PowerShell command to capture all monitors
    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    # Get virtual screen (all monitors combined)
    $virtualScreen = [System.Windows.Forms.SystemInformation]::VirtualScreen
    
    # Create bitmap for entire virtual screen
    $bitmap = New-Object System.Drawing.Bitmap $virtualScreen.Width, $virtualScreen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Copy from entire virtual screen
    $graphics.CopyFromScreen($virtualScreen.Left, $virtualScreen.Top, 0, 0, $bitmap.Size)
    
    # Save the image
    $bitmap.Save('{filepath}')
    $graphics.Dispose()
    $bitmap.Dispose()
    
    # Get monitor info for display
    $screens = [System.Windows.Forms.Screen]::AllScreens
    Write-Host "Captured $($screens.Count) monitor(s):"
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
    
    parser = argparse.ArgumentParser(description="Capture screenshots on Windows via WSL")
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