; --- Définitions des variables globales ---
#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"
; Il est crucial d'incrémenter cette version à chaque build pour la réputation
#define MyAppVersion "1.0.1" 
#define MyURL "https://github.com/zyloscore/bulkpdf"

[Setup]
; ID unique - Ne pas changer pour que Windows reconnaisse l'application au fil des mises à jour
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

; --- CONFIGURATION DE RÉPUTATION (CRITIQUE) ---
; Ces champs remplissent les propriétés "Détails" du .exe que Windows scanne
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="BulkPDF - Outil Open Source de traitement PDF"
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoCopyright="Copyright (C) 2026 {#MyAppPublisher}"
; Manifeste de compatibilité pour prouver à Windows que l'app est moderne
SignTool=none

; Privilèges requis
PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; Source de l'exécutable généré par PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Note : Assurez-vous que le logo.ico est bien présent dans src/assets/

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent