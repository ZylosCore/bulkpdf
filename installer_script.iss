; Script Inno Setup pour BulkFolder
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
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=BulkFolder_Setup
; Correction ici : utilisation du bon nom de fichier icône
SetupIconFile=src\assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; On prend l'exécutable généré par PyInstaller dans le dossier dist
Source: "dist\BulkFolder\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\BulkFolder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent