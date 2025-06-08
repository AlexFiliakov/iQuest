# Force clean build artifacts on Windows
# Run as Administrator if needed

Write-Host "Force cleaning build artifacts..." -ForegroundColor Yellow
Write-Host ""

function Force-Remove {
    param($Path)
    
    if (Test-Path $Path) {
        Write-Host "Removing $Path..." -ForegroundColor Cyan
        
        # First try normal removal
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "  Success!" -ForegroundColor Green
            return
        }
        catch {
            Write-Host "  Normal removal failed, trying advanced methods..." -ForegroundColor Yellow
        }
        
        # Take ownership and remove attributes
        try {
            # Remove read-only attributes
            Get-ChildItem -Path $Path -Recurse -Force | ForEach-Object {
                $_.Attributes = 'Normal'
            }
            
            # Try again
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "  Success after attribute reset!" -ForegroundColor Green
            return
        }
        catch {
            Write-Host "  Still failed, trying with delay..." -ForegroundColor Yellow
        }
        
        # Wait and try again (for OneDrive/antivirus)
        Start-Sleep -Seconds 2
        
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "  Success after delay!" -ForegroundColor Green
        }
        catch {
            Write-Host "  Failed to remove $Path" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }
}

# Clean directories
Force-Remove "build\work"
Force-Remove "build\dist"
Force-Remove "dist"
Force-Remove "__pycache__"

# Clean spec files
Get-ChildItem -Filter "*.spec" | Where-Object { 
    $_.Name -ne "pyinstaller.spec" -and $_.Name -ne "pyinstaller_onefile.spec" 
} | ForEach-Object {
    Write-Host "Removing $($_.Name)..." -ForegroundColor Cyan
    Remove-Item $_.FullName -Force
}

Write-Host ""
Write-Host "Cleanup attempt complete!" -ForegroundColor Green
Write-Host ""
Write-Host "If you still have issues:" -ForegroundColor Yellow
Write-Host "1. Close all programs using the build files"
Write-Host "2. Pause OneDrive sync"
Write-Host "3. Run PowerShell as Administrator"
Write-Host "4. Use Task Manager to end any Python processes"
Write-Host "5. Try: python build.py --incremental"
Write-Host ""