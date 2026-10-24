param(
  [string]$Python = "py -3.11",
  [switch]$InstallOptional
)

$ErrorActionPreference = "Stop"
Write-Host "EchoMind Windows setup (local CPU-first)" -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' was not found. Install Python 3.11 from python.org, then rerun."
}

& py -3.11 --version
if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
  & py -3.11 -m venv .venv
}
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
if ($InstallOptional) {
  & $venvPython -m pip install "-e .[asr,ui,science,dev]"
} else {
  & $venvPython -m pip install "-e .[dev]"
}

New-Item -ItemType Directory -Force -Path data\samples, data\evaluation, data\metadata, experiments\reports | Out-Null
& $venvPython scripts\check_environment.py
Write-Host "Setup complete. Model weights are not downloaded automatically." -ForegroundColor Green
Write-Host "Activate with .\.venv\Scripts\Activate.ps1 and launch with python app.py"
