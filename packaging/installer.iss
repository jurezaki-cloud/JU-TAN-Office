; Inno Setup 6 — JU-TAN Office Enterprise 64-bit
#define MyAppName "JU-TAN Office Enterprise"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "JU-TAN Studio"
#define MyAppExeName "JU-TAN-Office.exe"

[Setup]
AppId={{A7C3E9F1-4B12-4D90-9E21-A1B2C3D4E5F6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
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
VersionInfoVersion=1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
UsePreviousAppDir=yes
DisableDirPage=no
ExtraDiskSpaceRequired=52428800

[Files]
Source: "..\dist\JU-TAN-Office\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "Version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
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

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Src, Dst: String;
begin
  Result := '';
  Src := ExpandConstant('{commonappdata}\JU-TAN Office\Data\ju_tan.db');
  Dst := ExpandConstant('{commonappdata}\JU-TAN Office\Backup\pre-upgrade.db');
  if FileExists(Src) then begin
    ForceDirectories(ExtractFilePath(Dst));
    CopyFile(Src, Dst, False);
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
