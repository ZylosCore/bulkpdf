; --- Définitions des variables globales ---
#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"
; MyAppVersion est passé dynamiquement via la ligne de commande dans GitHub Actions
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyURL "https://github.com/zyloscore/bulkpdf"

[Setup]
; ID unique - Ne pas changer pour conserver la continuité des versions
AppId={{9F5D3B2C-1A4E-4F3D-BD6A-2C1E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyURL}
AppSupportURL={#MyURL}
AppUpdatesURL={#MyURL}

; Configuration de l'installeur
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BulkPDF_Setup_{#MyAppVersion}
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; --- CONFIGURATION DE RÉPUTATION ---
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="BulkPDF - Outil Open Source de traitement PDF"
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoCopyright="Copyright (C) 2024 {#MyAppPublisher}"

; Privilèges requis pour installer dans Program Files
PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; Source de l'exécutable généré par PyInstaller (dossier dist)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent