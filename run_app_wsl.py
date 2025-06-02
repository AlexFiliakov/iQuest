#!/usr/bin/env python3
"""
WSL launcher for Apple Health Monitor Dashboard.

This script handles the Qt platform plugin issues in WSL by using the offscreen
platform for headless operation. For GUI operation, ensure you have an X server
running (like VcXsrv or WSLg).
"""

import os
import sys
import subprocess

def main():
    # Check if we have a display
    if os.environ.get('DISPLAY'):
        print(f"X11 display found: {os.environ['DISPLAY']}")
        # Try to run with GUI
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
    else:
        print("No X11 display found. Running in headless mode.")
        print("To run with GUI, ensure X server is running and DISPLAY is set.")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Run the main application
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'src', 'main.py')
    
    # Execute the main script
    result = subprocess.run([sys.executable, main_script] + sys.argv[1:])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()