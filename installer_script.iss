#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"
#ifndef MyAppVersion
  #define MyAppVersion "1.2.0"
#endif
#define MyURL "https://github.com/zyloscore/bulkpdf"

[Setup]
AppId={{9F5D3B2C-1A4E-4F3D-BD6A-2C1E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BulkPDF_Setup_{#MyAppVersion}
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; --- CONFIGURATION DE LA SIGNATURE ---
SignTool=MsSign $f
SignedUninstaller=yes

; Métadonnées pour Windows SmartScreen
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="BulkPDF - Outil de gestion PDF"
VersionInfoVersion={#MyAppVersion}
VersionInfoCopyright="Copyright (C) 2024 {#MyAppPublisher}"

PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; L'exécutable principal (sera signé par le workflow avant d'être inclus ici)
Source: "dist\{#MyAppName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Tous les autres fichiers nécessaires
Source: "dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
