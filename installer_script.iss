#define MyAppName "BulkFolder"
#define MyAppPublisher "Zyloscore"
#define MyAppExeName "BulkFolder.exe"
; L'ID ci-dessous est crucial pour la réputation de l'app sous Windows
#define MyAppId "{{A1B2C3D4-E5F6-4789-9ABC-DEF123456789}}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Paramètres pour réduire les alertes SmartScreen
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=BulkFolder_Setup_v{#MyAppVersion}
SetupIconFile=src\assets\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; On récupère tout le contenu du dossier généré par PyInstaller
Source: "dist\BulkFolder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; On inclut le fichier de version pour l'UI
Source: "project_info.xml"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent