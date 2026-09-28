; Inno Setup 6 — JU-TAN Office Enterprise 64-bit
; Version / publisher defines: packaging/version.iss (generated from app.core.release_meta)
; Safe install / uninstall architecture:
;   - Normal upgrade / reinstall PRESERVES business data by default
;   - Explicit "Nova čista namestitev" resets business data only after confirmation
;   - Standard uninstall removes the program and keeps business data
;   - Complete uninstall removes JU-TAN-owned data only after confirmation
;   - Local backups deleted only when the user explicitly checks that option
;   - Device license activation in LocalAppData is NEVER deleted by Setup/Uninstall
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
; Official Slovenian Inno Setup language pack (compiler:Languages\Slovenian.isl).
; Custom Fresh Install / Complete Uninstall pages remain Slovenian in [Code].
ShowLanguageDialog=no

[Languages]
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"

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
Source: "..\docs\DATA_LOCATIONS.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\updates\latest.json"; DestDir: "{app}\updates"; Flags: ignoreversion

[Dirs]
; ProgramData is machine-wide. JU-TAN Office runs unelevated after setup,
; therefore standard Windows users need modify rights on application data.
; uninsneveruninstall: standard uninstall PRESERVES business data.
; Complete uninstall deletes these folders explicitly in [Code] after confirmation.
Name: "{commonappdata}\JU-TAN Office"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Data"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Logs"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Backup"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Temp"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Reports"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{commonappdata}\JU-TAN Office\Data\documents"; Permissions: users-modify; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Odstrani {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{group}\Dokumentacija\Politika zasebnosti"; Filename: "{app}\docs\PRIVACY.md"
Name: "{group}\Dokumentacija\Namestitev"; Filename: "{app}\docs\INSTALL.md"
Name: "{group}\Dokumentacija\Uporabniški vodič"; Filename: "{app}\docs\USER_GUIDE.md"
Name: "{group}\Dokumentacija\Skrbniški vodič"; Filename: "{app}\docs\ADMIN_GUIDE.md"
Name: "{group}\Dokumentacija\Opombe ob izdaji"; Filename: "{app}\docs\RELEASE_NOTES.md"
Name: "{group}\Dokumentacija\Varnost"; Filename: "{app}\docs\SECURITY.md"
Name: "{group}\Dokumentacija\Lokacije podatkov"; Filename: "{app}\docs\DATA_LOCATIONS.md"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Ikona na namizju"; GroupDescription: "Bližnjice:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Zaženi {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\install.json"

[Code]
var
  InstallModePage: TInputOptionWizardPage;
  PreviousDataExists: Boolean;
  FreshInstallChosen: Boolean;
  CreateFreshBackup: Boolean;
  UninstallComplete: Boolean;
  UninstallDeleteBackups: Boolean;

function AppDataRoot: String;
begin
  Result := ExpandConstant('{commonappdata}\JU-TAN Office');
end;

function AppDataDir: String;
begin
  Result := AppDataRoot + '\Data';
end;

function AppBackupDir: String;
begin
  Result := AppDataRoot + '\Backup';
end;

function AppLogsDir: String;
begin
  Result := AppDataRoot + '\Logs';
end;

function AppTempDir: String;
begin
  Result := AppDataRoot + '\Temp';
end;

function AppReportsDir: String;
begin
  Result := AppDataRoot + '\Reports';
end;

function LicenseStateDir: String;
{ Online activation — NEVER deleted by installer/uninstaller. }
begin
  Result := ExpandConstant('{localappdata}\JU-TAN\Office');
end;

function PreviousInstallDataExists: Boolean;
begin
  Result :=
    FileExists(AppDataDir + '\ju_tan.db') or
    FileExists(AppDataDir + '\ju_tan.db-wal') or
    FileExists(AppDataDir + '\settings.json') or
    FileExists(AppDataDir + '\warehouse.json') or
    FileExists(AppDataDir + '\session.json') or
    DirExists(AppDataDir + '\documents');
end;

procedure CopyIfExists(const Src, Dst: String);
begin
  if FileExists(Src) then
    CopyFile(Src, Dst, False);
end;

function InitializeSetup(): Boolean;
begin
  FreshInstallChosen := False;
  CreateFreshBackup := False;
  PreviousDataExists := PreviousInstallDataExists;
  Result := True;
end;

procedure InitializeWizard;
begin
  if PreviousDataExists and (not WizardSilent) then
  begin
    InstallModePage := CreateInputOptionPage(
      wpWelcome,
      'Namestitev',
      'Na tem računalniku so bili najdeni podatki prejšnje namestitve JU-TAN Office.',
      'Izberite način namestitve:'#13#10#13#10 +
      '• Nadgradnja ohrani podjetja, stranke, artikle, račune in druge poslovne podatke.'#13#10 +
      '• Čista namestitev inicializira JU-TAN Office kot nov program brez obstoječih ' +
      'podjetij, strank, artiklov, računov, ponudb, naročil in drugih poslovnih podatkov.'#13#10#13#10 +
      'Običajna nadgradnja (npr. 1.0.3 → 1.0.4) mora ohraniti podatke — izberite prvo možnost.',
      True, False);
    InstallModePage.Add('Nadgradi / ponovno namesti in ohrani podatke');
    InstallModePage.Add('Nova čista namestitev');
    InstallModePage.Values[0] := True;
  end;
end;

function ConfirmFreshDanger: Boolean;
begin
  Result := MsgBox(
    'POZOR'#13#10#13#10 +
    'Izbrisani bodo vsi lokalni podatki JU-TAN Office:'#13#10 +
    '• podjetja'#13#10 +
    '• stranke'#13#10 +
    '• artikli'#13#10 +
    '• računi'#13#10 +
    '• ponudbe'#13#10 +
    '• naročila'#13#10 +
    '• plačila'#13#10 +
    '• lokalne nastavitve'#13#10 +
    '• lokalna baza podatkov'#13#10 +
    '• predpomnilnik in začasne datoteke'#13#10#13#10 +
    'Lokalne varnostne kopije in aktivacija naprave se privzeto ohranijo.'#13#10 +
    'Tega dejanja ni mogoče razveljaviti.'#13#10#13#10 +
    'Ali želite nadaljevati?',
    mbError, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

function AskFreshBackupChoice: Boolean;
{ Returns False if the user cancels. Sets CreateFreshBackup / FreshInstallChosen. }
var
  Answer: Integer;
begin
  Result := False;
  Answer := MsgBox(
    'Pred izbrisom ustvari varnostno kopijo'#13#10#13#10 +
    'Priporočeno: najprej ustvarite varnostno kopijo, nato nadaljujte s čisto namestitvijo.'#13#10#13#10 +
    'Da = Ustvari varnostno kopijo in nadaljuj'#13#10 +
    'Ne = Izbriši brez varnostne kopije'#13#10 +
    'Prekliči = Prekini čisto namestitev',
    mbConfirmation, MB_YESNOCANCEL or MB_DEFBUTTON1);

  if Answer = IDCANCEL then
    Exit;

  if Answer = IDYES then
  begin
    CreateFreshBackup := True;
    if not ConfirmFreshDanger then
      Exit;
    FreshInstallChosen := True;
    Result := True;
    Exit;
  end;

  { IDNO — delete without backup: require strong confirmation }
  CreateFreshBackup := False;
  if not ConfirmFreshDanger then
    Exit;
  if MsgBox(
       'Potrditev: izbrisati lokalne poslovne podatke BREZ nove varnostne kopije?',
       mbError, MB_YESNO or MB_DEFBUTTON2) <> IDYES then
    Exit;
  FreshInstallChosen := True;
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (InstallModePage <> nil) and (CurPageID = InstallModePage.ID) then
  begin
    FreshInstallChosen := False;
    CreateFreshBackup := False;
    if InstallModePage.Values[1] then
    begin
      if not AskFreshBackupChoice then
      begin
        { Stay on page; re-select preserve-data option for safety. }
        InstallModePage.Values[0] := True;
        InstallModePage.Values[1] := False;
        Result := False;
      end;
    end;
  end;
end;

function CreateTimestampedFreshBackup: Boolean;
{ Copy business data into Backup\FreshInstall\... Return True only if validated. }
var
  Stamp, Target, DataDir, BackupRoot: String;
  ExitCode: Integer;
begin
  Result := False;
  DataDir := AppDataDir;
  BackupRoot := AppBackupDir;
  Stamp := GetDateTimeString('yyyymmdd-hhnnss', '-', '-');
  Target := BackupRoot + '\FreshInstall\JU-TAN-before-fresh-' + Stamp;
  if not ForceDirectories(Target) then
  begin
    MsgBox('Varnostne kopije ni bilo mogoče ustvariti (mapa). Čista namestitev je prekinjena.', mbError, MB_OK);
    Exit;
  end;

  if FileExists(DataDir + '\ju_tan.db') then
  begin
    if not CopyFile(DataDir + '\ju_tan.db', Target + '\ju_tan.db', False) then
    begin
      MsgBox('Varnostne kopije baze ni bilo mogoče ustvariti. Podatki niso bili izbrisani.', mbError, MB_OK);
      Exit;
    end;
    if not FileExists(Target + '\ju_tan.db') then
    begin
      MsgBox('Varnostna kopija ni bila preverjena. Podatki niso bili izbrisani.', mbError, MB_OK);
      Exit;
    end;
    CopyIfExists(DataDir + '\ju_tan.db-wal', Target + '\ju_tan.db-wal');
    CopyIfExists(DataDir + '\ju_tan.db-shm', Target + '\ju_tan.db-shm');
  end;

  CopyIfExists(DataDir + '\settings.json', Target + '\settings.json');
  CopyIfExists(DataDir + '\warehouse.json', Target + '\warehouse.json');
  CopyIfExists(DataDir + '\audit.jsonl', Target + '\audit.jsonl');
  if DirExists(DataDir + '\documents') then
  begin
    ForceDirectories(Target + '\documents');
    Exec('cmd.exe',
      '/C xcopy /E /I /Y /Q "' + DataDir + '\documents\*" "' + Target + '\documents\"',
      '', SW_HIDE, ewWaitUntilTerminated, ExitCode);
  end;

  SaveStringToFile(Target + '\manifest.txt',
    'kind=fresh-install-pre-reset' + #13#10 +
    'created=' + Stamp + #13#10 +
    'data_dir=' + DataDir + #13#10, False);

  Result := True;
end;

procedure DeleteFileIfExists(const Path: String);
{ Rename/move-then-delete with retries. Windows Search/AV can briefly lock ju_tan.db;
  moving removes it from the live data path even if the final delete lags. }
var
  I: Integer;
  Tmp: String;
  ResultCode: Integer;
begin
  if not FileExists(Path) then
    Exit;
  Tmp := Path + '.jutan-delete';
  if FileExists(Tmp) then
    DeleteFile(Tmp);
  if not RenameFile(Path, Tmp) then
  begin
    { cmd move often succeeds when Pascal RenameFile fails under shared locks }
    Exec('cmd.exe', '/C move /Y "' + Path + '" "' + Tmp + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
  if FileExists(Tmp) then
  begin
    for I := 1 to 20 do
    begin
      if DeleteFile(Tmp) then
        Exit;
      if not FileExists(Tmp) then
        Exit;
      Sleep(150);
    end;
    Exit;
  end;
  if FileExists(Path) then
  begin
    for I := 1 to 20 do
    begin
      if DeleteFile(Path) then
        Exit;
      if not FileExists(Path) then
        Exit;
      Sleep(150);
    end;
  end;
end;

procedure WipeBusinessDataKeepBackups;
{ Destructive fresh / complete cleanup of JU-TAN-owned runtime business data.
  Does NOT delete Backup\ (caller decides). Does NOT touch LocalAppData license. }
var
  DataDir: String;
  ResultCode: Integer;
begin
  DataDir := AppDataDir;

  { WAL/SHM first, then main DB — reduces lock races on Windows. }
  DeleteFileIfExists(DataDir + '\ju_tan.db-wal');
  DeleteFileIfExists(DataDir + '\ju_tan.db-shm');
  DeleteFileIfExists(DataDir + '\ju_tan.db');
  { Force-delete any leftovers (including .jutan-delete renames). }
  Exec('cmd.exe',
    '/C del /F /Q "' + DataDir + '\ju_tan.db" "' + DataDir + '\ju_tan.db-wal" "' +
    DataDir + '\ju_tan.db-shm" "' + DataDir + '\ju_tan.db.jutan-delete" "' +
    DataDir + '\ju_tan.db-wal.jutan-delete" "' + DataDir + '\ju_tan.db-shm.jutan-delete"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  DeleteFileIfExists(DataDir + '\settings.json');
  DeleteFileIfExists(DataDir + '\warehouse.json');
  DeleteFileIfExists(DataDir + '\audit.jsonl');
  DeleteFileIfExists(DataDir + '\session.json');
  DeleteFileIfExists(DataDir + '\crash.flag');
  DeleteFileIfExists(DataDir + '\app_version.txt');
  DeleteFileIfExists(DataDir + '\last_vacuum.txt');
  DeleteFileIfExists(DataDir + '\license.json');
  DeleteFileIfExists(DataDir + '\ui_layout.json');
  DeleteFileIfExists(DataDir + '\.machine_key');

  if DirExists(DataDir + '\documents') then
    DelTree(DataDir + '\documents', True, True, True);
  if DirExists(DataDir + '\drafts') then
    DelTree(DataDir + '\drafts', True, True, True);

  { Company logos under Data (not brand assets from install tree) }
  DeleteFileIfExists(DataDir + '\company_logo.png');
  DeleteFileIfExists(DataDir + '\company_logo.jpg');
  DeleteFileIfExists(DataDir + '\company_logo.jpeg');
  DeleteFileIfExists(DataDir + '\company_logo.webp');

  if DirExists(AppLogsDir) then
    DelTree(AppLogsDir, False, True, False);
  if DirExists(AppTempDir) then
    DelTree(AppTempDir, False, True, False);
  if DirExists(AppReportsDir) then
    DelTree(AppReportsDir, False, True, False);

  ForceDirectories(DataDir);
  ForceDirectories(DataDir + '\documents');
  ForceDirectories(AppLogsDir);
  ForceDirectories(AppTempDir);
  ForceDirectories(AppReportsDir);
  ForceDirectories(AppBackupDir);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
{ WAL-safe cold backup after CloseApplications for upgrades.
  Fresh install optionally backs up then wipes business data. }
var
  DataDir, BackupDir: String;
begin
  Result := '';
  NeedsRestart := False;
  DataDir := AppDataDir;
  BackupDir := AppBackupDir;

  { Silent installs never auto-wipe — always preserve. }
  if WizardSilent then
    FreshInstallChosen := False;

  if FreshInstallChosen then
  begin
    if CreateFreshBackup then
    begin
      if not CreateTimestampedFreshBackup then
      begin
        Result := 'Čista namestitev prekinjena — varnostna kopija ni uspela.';
        FreshInstallChosen := False;
        Exit;
      end;
    end;
    WipeBusinessDataKeepBackups;
    Exit;
  end;

  { Normal upgrade / reinstall with data preserved }
  if FileExists(DataDir + '\ju_tan.db') then
  begin
    ForceDirectories(BackupDir);
    CopyIfExists(DataDir + '\ju_tan.db', BackupDir + '\pre-upgrade.db');
    CopyIfExists(DataDir + '\ju_tan.db-wal', BackupDir + '\pre-upgrade.db-wal');
    CopyIfExists(DataDir + '\ju_tan.db-shm', BackupDir + '\pre-upgrade.db-shm');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Json, Root, Mode: String;
begin
  if CurStep = ssPostInstall then
  begin
    Root := AppDataRoot;
    StringChangeEx(Root, '\', '/', True);
    if FreshInstallChosen then
      Mode := 'fresh'
    else if PreviousDataExists then
      Mode := 'upgrade'
    else
      Mode := 'installed';
    Json :=
      '{"mode":"installed","install_kind":"' + Mode +
      '","data_root":"' + Root +
      '","license_preserved":true}';
    SaveStringToFile(ExpandConstant('{app}\install.json'), Json, False);
  end;
end;

{ ========================= UNINSTALL ========================= }

function ConfirmCompleteUninstall: Boolean;
begin
  Result := MsgBox(
    'POZOR'#13#10#13#10 +
    'Izbrisani bodo vsi lokalni podatki JU-TAN Office:'#13#10 +
    '• podjetja'#13#10 +
    '• stranke'#13#10 +
    '• artikli'#13#10 +
    '• računi'#13#10 +
    '• ponudbe'#13#10 +
    '• naročila'#13#10 +
    '• plačila'#13#10 +
    '• lokalne nastavitve'#13#10 +
    '• lokalna baza podatkov'#13#10 +
    '• predpomnilnik in začasne datoteke'#13#10#13#10 +
    'Tega dejanja ni mogoče razveljaviti.'#13#10#13#10 +
    'Ali želite nadaljevati?',
    mbError, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

function InitializeUninstall(): Boolean;
var
  Answer: Integer;
begin
  UninstallComplete := False;
  UninstallDeleteBackups := False;
  Result := True;

  if UninstallSilent then
  begin
    { Silent uninstall = standard (preserve data). Never auto-complete-wipe. }
    Exit;
  end;

  Answer := MsgBox(
    'Odstranitev JU-TAN Office'#13#10#13#10 +
    'Izberite način odstranitve:'#13#10#13#10 +
    'Da = Odstrani program'#13#10 +
    '       Program bo odstranjen, poslovni podatki pa bodo ohranjeni za morebitno ponovno namestitev.'#13#10#13#10 +
    'Ne = Popolnoma odstrani JU-TAN Office in vse podatke'#13#10 +
    '       (zahteva dodatno potrditev)'#13#10#13#10 +
    'Prekliči = Prekini odstranitev',
    mbConfirmation, MB_YESNOCANCEL or MB_DEFBUTTON1);

  if Answer = IDCANCEL then
  begin
    Result := False;
    Exit;
  end;

  if Answer = IDYES then
  begin
    { Standard uninstall — preserve ProgramData / license }
    UninstallComplete := False;
    Exit;
  end;

  { Complete uninstall path }
  if not ConfirmCompleteUninstall then
  begin
    Result := False;
    Exit;
  end;

  UninstallDeleteBackups :=
    MsgBox(
      'Izbriši tudi lokalne varnostne kopije?'#13#10#13#10 +
      'Privzeto: NE — varnostne kopije ostanejo.'#13#10#13#10 +
      'Da = izbriši tudi lokalne varnostne kopije'#13#10 +
      'Ne = ohrani lokalne varnostne kopije',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;

  UninstallComplete := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if UninstallComplete then
    begin
      WipeBusinessDataKeepBackups;
      if UninstallDeleteBackups then
      begin
        if DirExists(AppBackupDir) then
          DelTree(AppBackupDir, True, True, True);
      end;
      { Remove empty runtime folders under ProgramData when safe }
      if DirExists(AppLogsDir) then
        DelTree(AppLogsDir, True, True, True);
      if DirExists(AppTempDir) then
        DelTree(AppTempDir, True, True, True);
      if DirExists(AppReportsDir) then
        DelTree(AppReportsDir, True, True, True);
      if DirExists(AppDataDir) then
        DelTree(AppDataDir, True, True, True);
      { Remove root only if backups were also deleted (otherwise keep Backup). }
      if UninstallDeleteBackups then
      begin
        if DirExists(AppDataRoot) then
          DelTree(AppDataRoot, True, True, True);
      end;
      { License activation intentionally preserved:
        LicenseStateDir = %LocalAppData%\JU-TAN\Office
        so reinstall does not consume another device seat. }
    end;
  end;
end;
