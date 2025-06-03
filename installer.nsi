; Apple Health Monitor Installer Script
; Based on ADR-003: Packaging and Distribution Strategy

!define PRODUCT_NAME "Apple Health Monitor"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Apple Health Monitor Team"
!define PRODUCT_WEB_SITE "https://github.com/yourusername/apple-health-monitor"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\HealthMonitor.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; Include Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\installer_welcome.bmp"  ; 164x314 pixels
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\installer_welcome.bmp"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!define MUI_LICENSEPAGE_CHECKBOX
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\HealthMonitor.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Apple Health Monitor"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View Readme"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_LINK "Visit our website"
!define MUI_FINISHPAGE_LINK_LOCATION "${PRODUCT_WEB_SITE}"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language files
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2025 ${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileDescription" "Apple Health Monitor Dashboard Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"

; Installer attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "build\dist\AppleHealthMonitor-${PRODUCT_VERSION}-installer.exe"
InstallDir "$LOCALAPPDATA\AppleHealthMonitor"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
SetCompressor /SOLID lzma
RequestExecutionLevel user  ; No admin rights required

; Function to check if already running
Function CheckRunning
  FindWindow $0 "" "Apple Health Monitor Dashboard"
  StrCmp $0 0 notRunning
    MessageBox MB_OK|MB_ICONEXCLAMATION "${PRODUCT_NAME} is currently running. Please close it before continuing." /SD IDOK
    Abort
  notRunning:
FunctionEnd

; Installer sections
Section "!Apple Health Monitor (required)" SEC01
  SectionIn RO
  
  ; Check if already running
  Call CheckRunning
  
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Copy all files from the distribution
  File /r "build\dist\HealthMonitor\*.*"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\HealthMonitor.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
  
  ; Store installation folder
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\HealthMonitor.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\HealthMonitor.exe"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKCU "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  
  ; Get size of installation
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
  
  ; Create README.txt for installation
  FileOpen $0 "$INSTDIR\README.txt" w
  FileWrite $0 "Apple Health Monitor Dashboard v${PRODUCT_VERSION}$\r$\n"
  FileWrite $0 "================================================$\r$\n$\r$\n"
  FileWrite $0 "Thank you for installing Apple Health Monitor!$\r$\n$\r$\n"
  FileWrite $0 "Getting Started:$\r$\n"
  FileWrite $0 "1. Launch the application from the Start Menu$\r$\n"
  FileWrite $0 "2. Click 'Select File' to import your Apple Health export$\r$\n"
  FileWrite $0 "3. Choose date range and metrics to analyze$\r$\n"
  FileWrite $0 "4. Explore your health data through various dashboards$\r$\n$\r$\n"
  FileWrite $0 "Data Location:$\r$\n"
  FileWrite $0 "Your data is stored locally at: %LOCALAPPDATA%\AppleHealthMonitor\data$\r$\n$\r$\n"
  FileWrite $0 "Support:$\r$\n"
  FileWrite $0 "Visit: ${PRODUCT_WEB_SITE}$\r$\n"
  FileClose $0
SectionEnd

Section "Desktop Shortcut" SEC02
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\HealthMonitor.exe"
SectionEnd

Section "File Association" SEC03
  ; Associate .health files with our application (future feature)
  ; WriteRegStr HKCU "Software\Classes\.health" "" "AppleHealthMonitor.Document"
  ; WriteRegStr HKCU "Software\Classes\AppleHealthMonitor.Document" "" "Apple Health Monitor Document"
  ; WriteRegStr HKCU "Software\Classes\AppleHealthMonitor.Document\DefaultIcon" "" "$INSTDIR\HealthMonitor.exe,0"
  ; WriteRegStr HKCU "Software\Classes\AppleHealthMonitor.Document\shell\open\command" "" '"$INSTDIR\HealthMonitor.exe" "%1"'
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "The core application files (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "Create a shortcut on your desktop for easy access"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} "Associate .health files with Apple Health Monitor (future feature)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section Uninstall
  ; Check if running
  FindWindow $0 "" "Apple Health Monitor Dashboard"
  StrCmp $0 0 notRunning
    MessageBox MB_OK|MB_ICONEXCLAMATION "${PRODUCT_NAME} is currently running. Please close it before uninstalling." /SD IDOK
    Abort
  notRunning:
  
  ; Ask about user data
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to keep your health data and settings?$\r$\n$\r$\nSelect 'Yes' to keep your data for future use.$\r$\nSelect 'No' to remove all data." /SD IDYES IDYES keepData
  
  ; Remove data directory if user chose to
  RMDir /r "$LOCALAPPDATA\AppleHealthMonitor\data"
  RMDir "$LOCALAPPDATA\AppleHealthMonitor"  ; Only removes if empty
  
  keepData:
  ; Remove installation files
  Delete "$INSTDIR\HealthMonitor.exe"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\LICENSE.txt"
  
  ; Remove all other files
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\assets"
  
  ; Remove shortcuts
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\*.*"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  
  ; Remove installation directory (only if empty)
  RMDir "$INSTDIR"
  
  ; Remove registry entries
  DeleteRegKey HKCU "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"
  
  SetAutoClose true
SectionEnd

; Installer initialization
Function .onInit
  ; Check if already installed
  ReadRegStr $0 HKCU "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $0 "" done
  
  MessageBox MB_YESNO|MB_ICONQUESTION "${PRODUCT_NAME} is already installed.$\r$\n$\r$\nDo you want to upgrade/reinstall?" /SD IDYES IDYES done
  Abort
  
  done:
FunctionEnd