param([int]$Port = 8880)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
  if (-not (Test-Path node_modules)) { throw 'Сначала выполните pnpm install в этой папке.' }
  pnpm exec vite --host 127.0.0.1 --port $Port --strictPort
} finally { Pop-Location }
