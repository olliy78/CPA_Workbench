; Inno Setup script for CPA Workbench (small installer variant)
; Variant B: Python is installed on-demand via winget if missing.

#define MyAppName "CPA Workbench"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "CPA Workbench Project"
#define MyAppURL "https://github.com/olliy78/CPA_Workbench"
#define MyAppExe "start_cpa_workbench.vbs"
#define SourceRoot ".."

[Setup]
AppId={{A1C2332F-8688-4D5F-9E72-7461DD9937F4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\CPA_Workbench
SetupIconFile={#SourceRoot}\tools\cpa_workbench.ico
DefaultGroupName=CPA Workbench
DisableProgramGroupPage=no
LicenseFile={#SourceRoot}\LICENSE
OutputDir=Output
OutputBaseFilename=CPA_Workbench_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop icon erstellen"; GroupDescription: "Zusatzaufgaben:"; Flags: unchecked

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: ".git\*,.github\*,.venv\*,build\*,Disketten\*,installer\*,__pycache__\*,*.pyc,*.pyo"
Source: "{#SourceRoot}\installer\start_cpa_workbench.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\tools\cpa_workbench.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CPA Workbench"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\cpa_workbench.ico"
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CPA Workbench"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\cpa_workbench.ico"

[Run]
Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; Description: "CPA Workbench starten"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}\build"
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\tools\__pycache__"

[Code]
var
  NeedPythonInstall: Boolean;

function CommandExists(const CmdName: string): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec(ExpandConstant('{cmd}'), '/C where ' + CmdName, '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
end;

function PythonReady: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec(ExpandConstant('{cmd}'), '/C python -c "import tkinter"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
end;

function WingetReady: Boolean;
begin
  Result := CommandExists('winget');
end;

function InstallPythonWithWinget: Boolean;
var
  ResultCode: Integer;
  Params: string;
begin
  Params := '/C winget install --id Python.Python.3.12 -e --scope user --accept-source-agreements --accept-package-agreements';
  Log('Installing Python via winget: ' + Params);
  Result := Exec(ExpandConstant('{cmd}'), Params, '', SW_SHOW, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
var
  Choice: Integer;
begin
  NeedPythonInstall := not PythonReady;

  if NeedPythonInstall then begin
    if not WingetReady then begin
      MsgBox(
        'Python wurde nicht gefunden und winget ist auf diesem System nicht verfugbar.' + #13#10 +
        'Bitte Python 3.12 (oder neuer) manuell installieren und das Setup erneut starten.',
        mbError, MB_OK
      );
      Result := False;
      exit;
    end;

    Choice := MsgBox(
      'Python wurde nicht gefunden.' + #13#10 +
      'Soll Python jetzt automatisch per winget fur den aktuellen Benutzer installiert werden?',
      mbConfirmation, MB_YESNO
    );

    if Choice <> IDYES then begin
      MsgBox('Setup wird beendet, da Python fur CPA Workbench erforderlich ist.', mbInformation, MB_OK);
      Result := False;
      exit;
    end;
  end;

  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssInstall) and NeedPythonInstall then begin
    WizardForm.StatusLabel.Caption := 'Installiere Python 3.12 uber winget...';
    WizardForm.Update;

    if not InstallPythonWithWinget then begin
      MsgBox(
        'Die automatische Python-Installation ist fehlgeschlagen.' + #13#10 +
        'Bitte Python manuell installieren und Setup erneut starten.',
        mbError, MB_OK
      );
      Abort;
    end;
  end;
end;
