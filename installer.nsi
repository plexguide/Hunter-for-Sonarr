; Huntarr Windows Installer Script
; Created by Cascade for Huntarr.io

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Define application information
!define PRODUCT_NAME "Huntarr.io"
!define PRODUCT_VERSION "1.7.0"
!define PRODUCT_PUBLISHER "PlexGuide"
!define PRODUCT_WEB_SITE "https://github.com/plexguide/Huntarr.io"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\Huntarr.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; Request application privileges for Windows Vista/7/8/10
RequestExecutionLevel admin

; Use modern UI
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "Huntarr-Windows-README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set language
!insertmacro MUI_LANGUAGE "English"

; Main installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Huntarr-Setup-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\Huntarr"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; Set branding with MUI
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\win.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\win.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Installer sections
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite on
  
  ; Add the main executable and all necessary files
  File "dist\Huntarr.exe"
  
  ; Extract all contents of ZIP package
  ; File /r "dist\*.*"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\Huntarr"
  CreateShortCut "$SMPROGRAMS\Huntarr\Huntarr.lnk" "$INSTDIR\Huntarr.exe"
  CreateShortCut "$DESKTOP\Huntarr.lnk" "$INSTDIR\Huntarr.exe"
  
  ; Register application
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\Huntarr.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\Huntarr.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

; Uninstaller section
Section Uninstall
  ; Remove shortcuts
  Delete "$SMPROGRAMS\Huntarr\Huntarr.lnk"
  Delete "$DESKTOP\Huntarr.lnk"
  RMDir "$SMPROGRAMS\Huntarr"
  
  ; Remove files and uninstaller
  Delete "$INSTDIR\Huntarr.exe"
  Delete "$INSTDIR\uninst.exe"

  ; Remove directories used
  RMDir "$INSTDIR"

  ; Remove registry keys
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
SectionEnd
