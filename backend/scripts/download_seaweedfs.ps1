$ErrorActionPreference = "Stop"
$binDir = Join-Path $PSScriptRoot "..\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$exe = Join-Path $binDir "weed.exe"
if (Test-Path $exe) {
  Write-Host "Already present: $exe"
  & $exe version
  exit 0
}
$zip = Join-Path $binDir "seaweedfs.zip"
$url = "https://github.com/seaweedfs/seaweedfs/releases/download/3.97/windows_amd64.zip"
Write-Host "Downloading SeaweedFS..."
Invoke-WebRequest -Uri $url -OutFile $zip
$tmp = Join-Path $binDir "sw_tmp"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $tmp -Force
Remove-Item $zip -Force
$found = Get-ChildItem $tmp -Recurse -Filter "weed.exe" | Select-Object -First 1
if (-not $found) { throw "weed.exe missing from archive" }
Copy-Item $found.FullName $exe -Force
Remove-Item $tmp -Recurse -Force
Write-Host "SeaweedFS ready: $exe"
& $exe version
