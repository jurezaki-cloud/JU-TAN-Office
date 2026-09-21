; Inno Setup 6 — JU-TAN Office Enterprise 64-bit
; Version / publisher defines: packaging/version.iss (generated from app.core.release_meta)
#include "version.iss"

[Setup]
AppId={{A7C3E9F1-4B12-4D90-9E21-A1B2C3D4E5F6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppPublisherURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
AppContact={#MyAppSupportEmail}
AppCopyright={#MyAppCopyright}
DefaultDirName={autopf}\JU-TAN Office
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=JU-TAN-Office-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=LICENSE.txt
SetupIconFile=..\resources\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
UsePreviousAppDir=yes
DisableDirPage=no
ExtraDiskSpaceRequired=52428800
; Close running app before file replace / DB backup (Restart Manager).
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
; Must match app.core.app_mutex.APP_MUTEX_NAME
AppMutex=JU-TANOfficeMutex

[Files]
Source: "..\dist\JU-TAN-Office\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "Version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\PRIVACY.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\INSTALL.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\USER_GUIDE.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\ADMIN_GUIDE.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\RELEASE_NOTES.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\SECURITY.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\SIGNING.md"; DestDir: "{app}\docs"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\updates\latest.json"; DestDir: "{app}\updates"; Flags: ignoreversion

[Dirs]
Name: "{commonappdata}\JU-TAN Office\Data"; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Logs"; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Backup"; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Temp"; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Reports"; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Data\documents"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Odstrani {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{group}\Dokumentacija\Politika zasebnosti"; Filename: "{app}\docs\PRIVACY.md"
Name: "{group}\Dokumentacija\Namestitev"; Filename: "{app}\docs\INSTALL.md"
Name: "{group}\Dokumentacija\Uporabniški vodič"; Filename: "{app}\docs\USER_GUIDE.md"
Name: "{group}\Dokumentacija\Skrbniški vodič"; Filename: "{app}\docs\ADMIN_GUIDE.md"
Name: "{group}\Dokumentacija\Opombe ob izdaji"; Filename: "{app}\docs\RELEASE_NOTES.md"
Name: "{group}\Dokumentacija\Varnost"; Filename: "{app}\docs\SECURITY.md"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Ikona na namizju"; GroupDescription: "Bližnjice:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Zaženi {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\install.json"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CopyIfExists(const Src, Dst: String);
begin
  if FileExists(Src) then
    CopyFile(Src, Dst, False);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
{ WAL-safe cold backup after CloseApplications: copy main DB + WAL/SHM sidecars. }
var
  DataDir, BackupDir: String;
begin
  Result := '';
  DataDir := ExpandConstant('{commonappdata}\JU-TAN Office\Data');
  BackupDir := ExpandConstant('{commonappdata}\JU-TAN Office\Backup');
  if FileExists(DataDir + '\ju_tan.db') then begin
    ForceDirectories(BackupDir);
    CopyIfExists(DataDir + '\ju_tan.db', BackupDir + '\pre-upgrade.db');
    CopyIfExists(DataDir + '\ju_tan.db-wal', BackupDir + '\pre-upgrade.db-wal');
    CopyIfExists(DataDir + '\ju_tan.db-shm', BackupDir + '\pre-upgrade.db-shm');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Json, Root: String;
begin
  if CurStep = ssPostInstall then begin
    Root := ExpandConstant('{commonappdata}\JU-TAN Office');
    StringChangeEx(Root, '\', '/', True);
    Json := '{"mode":"installed","data_root":"' + Root + '"}';
    SaveStringToFile(ExpandConstant('{app}\install.json'), Json, False);
  end;
end;
