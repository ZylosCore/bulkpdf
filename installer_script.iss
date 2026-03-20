; --- Définitions globales ---
#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"
#define MyAppVersion "1.0.0" 
#define MyURL "https://github.com/zyloscore/bulkpdf"

[Setup]
; ID unique pour l'application
AppId={{9F5D3B2C-1A4E-4F3D-BD6A-2C1E4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyURL}
AppSupportURL={#MyURL}
AppUpdatesURL={#MyURL}

; Configuration de l'installation
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BulkPDF_Setup
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; --- IMPORTANT POUR LA RÉPUTATION ---
; Indiquer clairement le nom de l'éditeur dans les propriétés du fichier généré
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="Outil de gestion et traitement de fichiers PDF en lot"
VersionInfoVersion={#MyAppVersion}
VersionInfoCopyright="Copyright (C) 2024 {#MyAppPublisher}"

; Privilèges requis (admin permet d'écrire dans Program Files)
PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; Source de l'exécutable généré par PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Si vous avez d'autres dépendances non incluses dans l'EXE, ajoutez-les ici

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent