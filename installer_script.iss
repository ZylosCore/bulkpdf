#define MyAppName "BulkFolder"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkFolder.exe"

[Setup]
AppId={{8E4C2A15-3B1A-4D2E-9C1F-7B8A9C0D1E2F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BulkFolder_Setup
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Demander les droits admin pour bypasser la politique 4551
PrivilegesRequired=admin

[Files]
; On ne prend que le fichier EXE unique généré dans 'dist'
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent