[Setup]
AppName=TaskHUD
AppVersion=1.5
AppPublisher=Talison Henke
DefaultDirName={localappdata}\TaskHUD
DefaultGroupName=TaskHUD
SetupIconFile=icon\taskhud.ico
OutputDir=dist
OutputBaseFilename=TaskHUDSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ShowLanguageDialog=yes

[CustomMessages]
LanguageName=br
ViewReadme=Ler instruções importantes

[CustomMessages]
LanguageName=pt
ViewReadme=Visualizar instruções após a instalação

[CustomMessages]
LanguageName=es
ViewReadme=Ver archivo de instrucciones

[CustomMessages]
LanguageName=en
ViewReadme=View instructions after installation

[Languages]
Name: "br"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "dist\TaskHUD.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\icon\*"; DestDir: "{app}\icon"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\audio\*"; DestDir: "{app}\audio"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "leia-me.txt"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "{cm:AutoStartProgram,TaskHUD}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{group}\TaskHUD"; Filename: "{app}\TaskHUD.exe"
Name: "{commondesktop}\TaskHUD"; Filename: "{app}\TaskHUD.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TaskHUD.exe"; Description: "{cm:LaunchProgram,TaskHUD}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\leia-me.txt"; Description: "{cm:ViewReadme}"; Flags: postinstall shellexec skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "TaskHUD"; ValueData: """{app}\TaskHUD.exe"""; \
  Flags: uninsdeletevalue; Tasks: autostart

[Code]
var
  DeleteData: Boolean;
  ReadmeDescription: String;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  DeleteData := MsgBox('Você deseja apagar também os dados do TaskHUD (tarefas salvas)?',
                       mbConfirmation, MB_YESNO) = IDYES;
end;

procedure DeinitializeUninstall();
var
  DataPath: string;
begin
  if DeleteData then
  begin
    DataPath := ExpandConstant('{localappdata}\TaskHUD');
    DelTree(DataPath, True, True, True);
  end;
end;

procedure InitializeWizard();
begin
  // Define a descrição do leia-me com base na linguagem selecionada
  case ActiveLanguage of
    'br': ReadmeDescription := 'Ler instruções importantes';
    'pt': ReadmeDescription := 'Visualizar instruções após a instalação';
    'es': ReadmeDescription := 'Ver archivo de instrucciones';
    else ReadmeDescription := 'View instructions after installation';
  end;
end;

function GetCustomSetupExitCodes: Boolean;
begin
  Result := True;
end;

// Substitui os textos padrão de "Executar programa" e "Visualizar leia-me"
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.RunList.Checked[0] := True; // Marcar para executar TaskHUD
    WizardForm.RunList.Checked[1] := True; // Leia-me marcado por padrão

    WizardForm.RunList.ItemCaption[1] := ReadmeDescription;
  end;
end;

