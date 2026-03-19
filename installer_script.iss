#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"

[Setup]
AppId={{9F5D3B2C-1A4E-4F3D-BD6A-2C1E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BulkPDF_Setup
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Droits admin pour éviter l'erreur 4551 de Windows
PrivilegesRequired=admin

[Files]
; On récupère le fichier unique généré par PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent