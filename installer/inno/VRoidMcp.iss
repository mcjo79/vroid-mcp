; VRoid MCP Bridge - installateur local Inno Setup
; Compilation : ISCC.exe installer\inno\VRoidMcp.iss
; Le payload doit etre extrait dans out\inno_payload avant compilation.

#define MyAppName "VRoid MCP Bridge"
#define MyAppVersion "0.12.0-local"
#define MyAppPublisher "mcjo79"
#define MyAppURL "https://mcjo79.github.io/vroid-mcp/"
#define MyAppExeName "Installer-GUI.cmd"
#define PayloadDir "..\..\out\inno_payload"

[Setup]
AppId={{A7C2E6E4-1D1B-4C0B-9F2A-6D5C4B3A2E10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\VRoidMcp
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=VRoidMcp-Setup-v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=0.12.0.0
VersionInfoDescription={#MyAppName} setup
LicenseFile=..\..\LICENSE

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\{#MyAppName} - README"; Filename: "{app}\README.md"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Configurer VRoid Studio maintenant"; Flags: postinstall nowait skipifsilent shellexec

[Code]
function RunIntegrationUninstall(RemoveBepInEx, RemoveData: Boolean): Integer;
var
  Params: String;
  ResultCode: Integer;
begin
  Result := 0;
  if not FileExists(ExpandConstant('{app}\install.ps1')) then
    exit;

  Params := '-NoProfile -ExecutionPolicy Bypass -File "' +
            ExpandConstant('{app}\install.ps1') + '" -Uninstall';
  if RemoveBepInEx then
    Params := Params + ' -RemoveBepInEx';
  if RemoveData then
    Params := Params + ' -RemoveData';

  if Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
          Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := ResultCode
  else
    Result := -1;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RemoveBepInEx, RemoveData: Boolean;
  Code: Integer;
begin
  if CurUninstallStep <> usUninstall then
    exit;

  if UninstallSilent then
  begin
    RemoveBepInEx := False;
    RemoveData := False;
  end
  else
  begin
    RemoveBepInEx :=
      MsgBox('Supprimer aussi BepInEx et ses sauvegardes ?' + #13#10 + #13#10 +
             'Choisir Non conserve BepInEx et les autres plugins.',
             mbConfirmation, MB_YESNO) = IDYES;

    RemoveData :=
      MsgBox('Supprimer aussi le serveur MCP, le runtime Python et le cache ?' + #13#10 + #13#10 +
             'Choisir Non conserve ces donnees locales.',
             mbConfirmation, MB_YESNO) = IDYES;
  end;

  Code := RunIntegrationUninstall(RemoveBepInEx, RemoveData);
  if Code <> 0 then
    MsgBox('Le nettoyage VRoid a retourne le code ' + IntToStr(Code) +
           '.' + #13#10 + #13#10 +
           'Le dossier de l''application va etre retire ; verifiez les fichiers restants.',
           mbError, MB_OK);
end;

