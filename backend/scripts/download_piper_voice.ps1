$ErrorActionPreference = "Stop"
$out = Join-Path $PSScriptRoot "..\data\piper"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
@(
  "en_US-ryan-high.onnx",
  "en_US-ryan-high.onnx.json"
) | ForEach-Object {
  $target = Join-Path $out $_
  if (-not (Test-Path $target)) {
    Write-Host "Downloading $_ ..."
    Invoke-WebRequest -Uri "$base/$_" -OutFile $target
  } else {
    Write-Host "Already present: $_"
  }
}
Write-Host "Piper voice ready in $out"
