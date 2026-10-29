param([int]$Port = 8879)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Не найден .venv/Scripts/python.exe. Подготовьте окружение проекта.'
}
Push-Location -LiteralPath $projectRoot
try { & $pythonPath -B -m game_ui_lab.app --port $Port }
finally { Pop-Location }
