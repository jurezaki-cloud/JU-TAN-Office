#define MyAppName "JU-TAN Office"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "JU-TAN Studio"
#define MyAppExeName "JU-TAN-Office.exe"

[Setup]
AppId={{9E765F29-77CD-4A35-98B4-6ED6A6F32BA2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\JU-TAN Office
DefaultGroupName=JU-TAN Office
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=JU-TAN-Office-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Ustvari bližnjico na namizju"; GroupDescription: "Dodatne možnosti:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Zaženi {#MyAppName}"; Flags: nowait postinstall skipifsilent
