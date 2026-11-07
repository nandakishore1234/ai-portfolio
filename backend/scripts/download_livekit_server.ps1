$ErrorActionPreference = "Stop"
$binDir = Join-Path $PSScriptRoot "..\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$zip = Join-Path $binDir "livekit-server.zip"
$exe = Join-Path $binDir "livekit-server.exe"
# Prefer a server new enough for current livekit-client (v1 RTC path).
$url = "https://github.com/livekit/livekit/releases/download/v1.13.11/livekit_1.13.11_windows_amd64.zip"
if (Test-Path $exe) {
  $ver = & $exe --version 2>&1 | Out-String
  if ($ver -match "1\.13\.") {
    Write-Host "Already present: $exe ($ver.Trim())"
    exit 0
  }
  Write-Host "Upgrading LiveKit server from: $ver"
}
Write-Host "Downloading LiveKit server..."
Invoke-WebRequest -Uri $url -OutFile $zip
$tmp = Join-Path $binDir "lk_tmp"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $tmp -Force
Remove-Item $zip -Force
$found = Get-ChildItem $tmp -Recurse -Filter "livekit-server.exe" | Select-Object -First 1
if (-not $found) { throw "livekit-server.exe missing from archive" }
Copy-Item $found.FullName $exe -Force
Remove-Item $tmp -Recurse -Force
Write-Host "LiveKit server ready: $exe"
& $exe --version
