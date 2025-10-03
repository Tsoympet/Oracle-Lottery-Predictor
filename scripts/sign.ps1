
Param(
  [Parameter(Mandatory=$true)] [string]$PfxPath,
  [Parameter(Mandatory=$true)] [string]$PfxPassword,
  [Parameter(Mandatory=$true)] [string]$TargetGlob,
  [string]$TimestampUrl = "http://timestamp.digicert.com"
)
$ErrorActionPreference = "Stop"
$files = Get-ChildItem -Path $TargetGlob -Recurse -File | Where-Object { $_.Extension -match '^(\.exe|\.dll|\.pyd)$' }
if (-not $files) { Write-Host "No signable files"; exit 0 }
$signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\x64\signtool.exe"
if (-not (Test-Path $signtool)) {
  $signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
}
function Sign-OneFile($f) {
  $max = 3
  for ($i=1; $i -le $max; $i++) {
    try {
      & $signtool sign /f $PfxPath /p $PfxPassword /fd sha256 /td sha256 /tr $TimestampUrl "$($f.FullName)"
      Write-Host "Signed: $($f.FullName)"; return
    } catch {
      if ($i -eq $max) { throw "Failed signing $($f.FullName). $_" } else { Start-Sleep -Seconds (2*$i) }
    }
  }
}
foreach ($f in $files) { Sign-OneFile $f }
foreach ($f in $files) { & $signtool verify /pa /v "$($f.FullName)" | Out-Null }
