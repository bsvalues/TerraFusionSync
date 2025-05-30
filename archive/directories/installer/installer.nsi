;TerraFusion Platform Installer
;NSIS Script for Windows Deployment
;Creates a complete county-ready GIS platform installation

!define PRODUCT_NAME "TerraFusion Platform"
!define PRODUCT_VERSION "2.1.0"
!define PRODUCT_PUBLISHER "County GIS Solutions"
!define PRODUCT_WEB_SITE "https://terrafusion.gov"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\TerraFusion.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\terrafusion.ico"
!define MUI_UNICON "assets\terrafusion.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\welcome.bmp"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Custom configuration page
Page custom ConfigPageCreate ConfigPageLeave

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\TerraFusion.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; Reserve files
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

; Variables
Var CountyName
Var DatabaseType
Var InstallAI
Var AutoStart
Var SampleData

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "TerraFusion-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES\TerraFusion"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; Version Information
VIProductVersion "2.1.0.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "FileDescription" "TerraFusion Platform Installer"

Section "Core Platform" SecCore
  SectionIn RO ; Required section
  
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Core application files
  File "bin\terrafusion_gateway.exe"
  File "bin\sync_service.exe"
  File "config\default.env"
  File "README.txt"
  File "LICENSE.txt"
  
  ; Python runtime (embedded)
  SetOutPath "$INSTDIR\python"
  File /r "python\*.*"
  
  ; Configuration files
  SetOutPath "$INSTDIR\config"
  File "config\*.json"
  File "config\*.yml"
  
  ; Create data directories
  CreateDirectory "$APPDATA\TerraFusion"
  CreateDirectory "$APPDATA\TerraFusion\exports"
  CreateDirectory "$APPDATA\TerraFusion\logs"
  CreateDirectory "$APPDATA\TerraFusion\backups"
  
  ; Generate county-specific configuration
  Call CreateCountyConfig
  
SectionEnd

Section "GIS Export Engine" SecGIS
  SetOutPath "$INSTDIR\bin"
  File "bin\gis_export_v2.exe"
  
  SetOutPath "$INSTDIR\lib"
  File /r "lib\gis\*.*"
  
  ; GDAL/OGR libraries for GIS processing
  SetOutPath "$INSTDIR\gdal"
  File /r "gdal\*.*"
  
SectionEnd

Section "NarratorAI Assistant" SecAI
  StrCmp $InstallAI "1" 0 SkipAI
  
  SetOutPath "$INSTDIR\bin"
  File "bin\narrator_ai.exe"
  
  ; Check if Ollama is already installed
  Call CheckOllamaInstalled
  Pop $0
  StrCmp $0 "1" OllamaExists InstallOllama
  
  InstallOllama:
    DetailPrint "Installing Ollama AI Runtime..."
    SetOutPath "$INSTDIR\ollama"
    File "ollama\ollama.exe"
    
    ; Install default model
    DetailPrint "Setting up AI model (this may take a few minutes)..."
    ExecWait '"$INSTDIR\ollama\ollama.exe" pull llama3.2:3b' $0
    
  OllamaExists:
    DetailPrint "Ollama detected, configuring TerraFusion AI integration..."
  
  SkipAI:
SectionEnd

Section "Database (PostgreSQL)" SecDB
  StrCmp $DatabaseType "embedded" 0 SkipEmbeddedDB
  
  DetailPrint "Installing embedded PostgreSQL database..."
  SetOutPath "$INSTDIR\postgresql"
  File /r "postgresql\*.*"
  
  ; Initialize database
  DetailPrint "Initializing database..."
  ExecWait '"$INSTDIR\postgresql\bin\initdb.exe" -D "$APPDATA\TerraFusion\data" -U postgres' $0
  
  ; Create TerraFusion database
  DetailPrint "Creating TerraFusion database..."
  ExecWait '"$INSTDIR\postgresql\bin\createdb.exe" -U postgres terrafusion' $0
  
  SkipEmbeddedDB:
SectionEnd

Section "Sample County Data" SecSample
  StrCmp $SampleData "1" 0 SkipSample
  
  DetailPrint "Installing sample county data..."
  SetOutPath "$APPDATA\TerraFusion\sample_data"
  File /r "sample_data\*.*"
  
  ; Import sample data to database
  DetailPrint "Importing sample parcel and zoning data..."
  ExecWait '"$INSTDIR\python\python.exe" "$INSTDIR\scripts\import_sample_data.py"' $0
  
  SkipSample:
SectionEnd

Section "Windows Services" SecServices
  StrCmp $AutoStart "1" 0 SkipServices
  
  DetailPrint "Installing Windows services..."
  
  ; Install NSSM (Non-Sucking Service Manager)
  SetOutPath "$INSTDIR\nssm"
  File "nssm\nssm.exe"
  
  ; Create TerraFusion API Gateway service
  ExecWait '"$INSTDIR\nssm\nssm.exe" install "TerraFusion Gateway" "$INSTDIR\terrafusion_gateway.exe"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Gateway" DisplayName "TerraFusion API Gateway"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Gateway" Description "TerraFusion Platform API Gateway Service"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Gateway" Start SERVICE_AUTO_START"' $0
  
  ; Create TerraFusion Sync Service
  ExecWait '"$INSTDIR\nssm\nssm.exe" install "TerraFusion Sync" "$INSTDIR\python\python.exe"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Sync" AppParameters "$INSTDIR\sync_service.py"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Sync" DisplayName "TerraFusion Sync Service"' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" set "TerraFusion Sync" Start SERVICE_AUTO_START"' $0
  
  ; Start services
  DetailPrint "Starting TerraFusion services..."
  ExecWait 'net start "TerraFusion Gateway"' $0
  ExecWait 'net start "TerraFusion Sync"' $0
  
  SkipServices:
SectionEnd

Section "Desktop Integration" SecDesktop
  ; Create desktop shortcut
  CreateShortCut "$DESKTOP\TerraFusion Platform.lnk" "$INSTDIR\TerraFusion.exe" "" "$INSTDIR\terrafusion.ico"
  
  ; Create start menu folder
  CreateDirectory "$SMPROGRAMS\TerraFusion Platform"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\TerraFusion Platform.lnk" "$INSTDIR\TerraFusion.exe"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\Configuration.lnk" "$INSTDIR\config\county_setup.bat"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\Logs.lnk" "$APPDATA\TerraFusion\logs"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\User Guide.lnk" "$INSTDIR\README.txt"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\Uninstall.lnk" "$INSTDIR\uninst.exe"
  
  ; Create system tray launcher
  SetOutPath "$INSTDIR"
  File "bin\terrafusion_tray.exe"
  
  ; Add to startup (optional)
  StrCmp $AutoStart "1" 0 SkipStartup
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TerraFusion" "$INSTDIR\terrafusion_tray.exe"
  SkipStartup:
  
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\TerraFusion Platform\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\TerraFusion.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\TerraFusion.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  
  ; Create validation script
  Call CreateValidationScript
  
  ; Show completion message
  MessageBox MB_ICONINFORMATION "TerraFusion Platform has been successfully installed!$\r$\n$\r$\nThe system is configured for: $CountyName$\r$\n$\r$\nAccess the platform at: http://localhost:5000"
  
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core TerraFusion platform components (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecGIS} "Advanced GIS export engine with multiple format support"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecAI} "AI-powered analysis and insights (requires internet for initial setup)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDB} "Embedded PostgreSQL database (choose if no existing database)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecSample} "Sample county data for testing and training"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecServices} "Automatic startup and Windows service integration"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Desktop shortcuts and system tray integration"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Custom configuration page
Function ConfigPageCreate
  !insertmacro MUI_HEADER_TEXT "County Configuration" "Configure TerraFusion for your county"
  
  nsDialogs::Create 1018
  Pop $0
  
  ; County name input
  ${NSD_CreateLabel} 0 10u 100% 12u "County Name:"
  ${NSD_CreateText} 0 25u 200u 12u ""
  Pop $1
  
  ; Database type selection
  ${NSD_CreateLabel} 0 50u 100% 12u "Database Configuration:"
  ${NSD_CreateRadioButton} 10u 65u 180u 12u "Install embedded PostgreSQL (recommended)"
  Pop $2
  ${NSD_CreateRadioButton} 10u 80u 180u 12u "Connect to existing PostgreSQL server"
  Pop $3
  
  ; AI features checkbox
  ${NSD_CreateCheckBox} 0 105u 200u 12u "Enable AI-powered analysis features"
  Pop $4
  
  ; Auto-start checkbox
  ${NSD_CreateCheckBox} 0 125u 200u 12u "Start services automatically with Windows"
  Pop $5
  
  ; Sample data checkbox
  ${NSD_CreateCheckBox} 0 145u 200u 12u "Install sample county data for testing"
  Pop $6
  
  ; Set defaults
  ${NSD_SetText} $1 "Your County"
  ${NSD_Check} $2
  ${NSD_Check} $4
  ${NSD_Check} $5
  
  nsDialogs::Show
FunctionEnd

Function ConfigPageLeave
  ; Get values from configuration page
  ${NSD_GetText} $1 $CountyName
  
  ${NSD_GetState} $2 $0
  StrCmp $0 ${BST_CHECKED} 0 +3
  StrCpy $DatabaseType "embedded"
  Goto +2
  StrCpy $DatabaseType "external"
  
  ${NSD_GetState} $4 $InstallAI
  ${NSD_GetState} $5 $AutoStart
  ${NSD_GetState} $6 $SampleData
FunctionEnd

Function CreateCountyConfig
  ; Create county-specific .env file
  FileOpen $0 "$INSTDIR\config\county.env" w
  FileWrite $0 "# TerraFusion Configuration for $CountyName$\r$\n"
  FileWrite $0 "COUNTY_NAME=$CountyName$\r$\n"
  FileWrite $0 "SESSION_SECRET=terrafusion-$CountyName-${PRODUCT_VERSION}$\r$\n"
  
  StrCmp $DatabaseType "embedded" 0 ExternalDB
  FileWrite $0 "DATABASE_URL=postgresql://postgres@localhost:5432/terrafusion$\r$\n"
  Goto DBDone
  
  ExternalDB:
  FileWrite $0 "# DATABASE_URL=postgresql://user:password@server:5432/database$\r$\n"
  
  DBDone:
  StrCmp $InstallAI "1" 0 NoAI
  FileWrite $0 "NARRATOR_AI_URL=http://localhost:11434$\r$\n"
  FileWrite $0 "NARRATOR_AI_MODEL=llama3.2:3b$\r$\n"
  Goto AIDone
  
  NoAI:
  FileWrite $0 "# AI features disabled$\r$\n"
  
  AIDone:
  FileWrite $0 "LOG_LEVEL=INFO$\r$\n"
  FileWrite $0 "BACKUP_ENABLED=true$\r$\n"
  FileClose $0
FunctionEnd

Function CheckOllamaInstalled
  ; Check if Ollama is already installed
  ReadRegStr $0 HKLM "SOFTWARE\Ollama" "InstallLocation"
  StrCmp $0 "" NotInstalled Installed
  
  NotInstalled:
  Push "0"
  Return
  
  Installed:
  Push "1"
  Return
FunctionEnd

Function CreateValidationScript
  ; Create post-install validation script
  FileOpen $0 "$INSTDIR\scripts\validate_install.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 "echo TerraFusion Platform Installation Validation$\r$\n"
  FileWrite $0 "echo ============================================$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "echo Checking service status...$\r$\n"
  FileWrite $0 'curl -s http://localhost:5000/api/status | findstr "success" >nul$\r$\n'
  FileWrite $0 "if %errorlevel%==0 ($\r$\n"
  FileWrite $0 "    echo [OK] TerraFusion API Gateway is running$\r$\n"
  FileWrite $0 ") else ($\r$\n"
  FileWrite $0 "    echo [ERROR] TerraFusion API Gateway is not responding$\r$\n"
  FileWrite $0 ")$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "echo Installation validation complete.$\r$\n"
  FileWrite $0 "echo Access TerraFusion at: http://localhost:5000$\r$\n"
  FileWrite $0 "pause$\r$\n"
  FileClose $0
FunctionEnd

Section Uninstall
  ; Stop services first
  ExecWait 'net stop "TerraFusion Gateway"' $0
  ExecWait 'net stop "TerraFusion Sync"' $0
  
  ; Remove services
  ExecWait '"$INSTDIR\nssm\nssm.exe" remove "TerraFusion Gateway" confirm' $0
  ExecWait '"$INSTDIR\nssm\nssm.exe" remove "TerraFusion Sync" confirm' $0
  
  ; Remove files
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\*.*"
  
  ; Remove directories
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\TerraFusion Platform"
  
  ; Remove desktop shortcut
  Delete "$DESKTOP\TerraFusion Platform.lnk"
  
  ; Remove from startup
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TerraFusion"
  
  ; Remove registry entries
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  SetAutoClose true
SectionEnd