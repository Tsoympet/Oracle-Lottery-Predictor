
#define MyAppName "Oracle Lottery Predictor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Oracle Lottery Predictor Team"
#define MyAppExeName "OracleLotteryPredictor.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
LicenseFile=EULA.txt
OutputDir=Output
OutputBaseFilename=OracleLotteryPredictorSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=assets\icon.png
WizardImageFile=assets\banner.bmp

[Files]
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "EULA.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\OracleLotteryPredictor\OracleLotteryPredictor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"


[Files]
Source: "installer\config_template.json"; DestDir: "{commonappdata}\OracleLotteryPredictor"; Flags: ignoreversion

