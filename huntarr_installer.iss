#define MyAppName "Huntarr"
#define ReadVersionFile(str fileName) \
   Local[0] = FileOpen(fileName), \
   Local[1] = FileRead(Local[0]), \
   FileClose(Local[0]), \
   Local[1]

#define MyAppVersion ReadVersionFile("version.txt")
#define MyAppPublisher "Huntarr"
#define MyAppURL "https://github.com/plexguide/Huntarr.io"
#define MyAppExeName "Huntarr.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{22AE2CDB-5F87-4E42-B5C3-28E121D4BDFF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=.\installer
OutputBaseFilename=Huntarr_Setup
SetupIconFile=frontend\static\logo\huntarr.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
CloseApplications=no
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1
Name: "installservice"; Description: "Install as Windows Service"; GroupDescription: "Windows Service"; Flags: checkedonce

[Files]
Source: "dist\Huntarr\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Create empty config directories to ensure they exist with proper permissions
Source: "LICENSE"; DestDir: "{app}\config"; Flags: ignoreversion; AfterInstall: CreateConfigDirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; First, remove any existing service
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-service"; Flags: runhidden
; Wait a moment for the service to be properly removed
Filename: "{sys}\cmd.exe"; Parameters: "/c timeout /t 3"; Flags: runhidden
; Install the service
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-service"; Description: "Install Huntarr as a Windows Service"; Tasks: installservice; Flags: runhidden
; Grant permissions to the config directory 
Filename: "{sys}\cmd.exe"; Parameters: '/c icacls "{app}\config" /grant Everyone:(OI)(CI)F'; Flags: runhidden shellexec
; Start the service
Filename: "{sys}\net.exe"; Parameters: "start Huntarr"; Flags: runhidden; Tasks: installservice
; Launch Huntarr
Filename: "http://localhost:9705"; Description: "Open Huntarr Web Interface"; Flags: postinstall shellexec nowait
; Launch Huntarr
Filename: "{app}\{#MyAppExeName}"; Description: "Run Huntarr Application"; Flags: nowait postinstall skipifsilent; Check: not IsTaskSelected('installservice')

[UninstallRun]
; Stop the service first
Filename: "{sys}\net.exe"; Parameters: "stop Huntarr"; Flags: runhidden
; Wait a moment for the service to stop
Filename: "{sys}\cmd.exe"; Parameters: "/c timeout /t 3"; Flags: runhidden
; Then remove it
Filename: "{app}\{#MyAppExeName}"; Parameters: "--remove-service"; Flags: runhidden

[Code]
procedure CreateConfigDirs;
begin
  // Create necessary directories with explicit permissions
  ForceDirectories(ExpandConstant('{app}\config\logs'));
  ForceDirectories(ExpandConstant('{app}\config\stateful'));
  ForceDirectories(ExpandConstant('{app}\config\user'));
end;

// Check for running services and processes before install
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to stop the service if it's already running
  Exec(ExpandConstant('{sys}\net.exe'), 'stop Huntarr', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  // Give it a moment to stop
  Sleep(2000);
  Result := True;
end;

// Handle cleaning up before uninstall
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to stop the service before uninstalling
  Exec(ExpandConstant('{sys}\net.exe'), 'stop Huntarr', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(2000);
  Result := True;
end; 