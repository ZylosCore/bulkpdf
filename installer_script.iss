; --- DÉFINITIONS DE L'APPLICATION ---
#define MyAppName "BulkPDF"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkPDF.exe"
#ifndef MyAppVersion
  #define MyAppVersion "1.2.0"
#endif
#define MyURL "https://github.com/zyloscore/bulkpdf"

[Setup]
; Identifiant unique de l'application (ne pas changer pour les mises à jour)
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

; --- CONFIGURATION DE LA SIGNATURE NUMÉRIQUE ---
; Définit l'outil de signature (MsSign est configuré via la ligne de commande ISCC dans GitHub Actions)
SignTool=MsSign $f
; Active la signature du programme de désinstallation généré par Inno Setup
SignedUninstaller=yes

; --- MÉTADONNÉES POUR WINDOWS SMARTSCREEN ---
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="BulkPDF - Outil de gestion PDF"
VersionInfoVersion={#MyAppVersion}
VersionInfoCopyright="Copyright (C) 2024 {#MyAppPublisher}"

; Requis pour l'installation dans Program Files
PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
; L'exécutable principal généré par PyInstaller (doit être signé AVANT cette étape dans le workflow)
Source: "dist\{#MyAppName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; TOUS les autres fichiers et sous-dossiers générés par le mode --onedir (DLLs, assets, etc.)
Source: "dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
; Option pour lancer l'application immédiatement après l'installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
