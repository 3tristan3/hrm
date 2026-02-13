$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend_django"
$applyDir = Join-Path $root "frontend_vue"
$adminDir = Join-Path $root "frontend_admin"

function New-RunnerCommand {
  param(
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$WorkDir,
    [Parameter(Mandatory = $true)][string[]]$Steps
  )

  $lines = @(
    "`$ErrorActionPreference = 'Stop'"
    "`$host.UI.RawUI.WindowTitle = '$Title'"
    "Set-Location '$WorkDir'"
  )
  $lines += $Steps
  return ($lines -join "`n")
}

$backendSteps = @(
  "if (!(Test-Path '.venv\Scripts\Activate.ps1')) { python -m venv .venv }",
  ". .\.venv\Scripts\Activate.ps1",
  "python -m pip install -r requirements.txt",
  "python manage.py migrate",
  "python manage.py runserver 0.0.0.0:8000"
)

$applySteps = @(
  "if (!(Test-Path 'node_modules')) { npm install }",
  "npx vite --host 0.0.0.0 --port 8080 --strictPort"
)

$adminSteps = @(
  "if (!(Test-Path 'node_modules')) { npm install }",
  "npx vite --host 0.0.0.0 --port 8090 --strictPort"
)

$backendCmd = New-RunnerCommand -Title "HRM Backend" -WorkDir $backendDir -Steps $backendSteps
$applyCmd = New-RunnerCommand -Title "HRM Apply Frontend" -WorkDir $applyDir -Steps $applySteps
$adminCmd = New-RunnerCommand -Title "HRM Admin Frontend" -WorkDir $adminDir -Steps $adminSteps

Start-Process -FilePath "pwsh" -ArgumentList "-NoLogo", "-NoProfile", "-NoExit", "-Command", $backendCmd
Start-Process -FilePath "pwsh" -ArgumentList "-NoLogo", "-NoProfile", "-NoExit", "-Command", $applyCmd
Start-Process -FilePath "pwsh" -ArgumentList "-NoLogo", "-NoProfile", "-NoExit", "-Command", $adminCmd

Write-Host ""
Write-Host "HRM 启动脚本已执行，已打开 3 个窗口：" -ForegroundColor Green
Write-Host "- Backend:   http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "- Apply UI:  http://127.0.0.1:8080" -ForegroundColor Cyan
Write-Host "- Admin UI:  http://127.0.0.1:8090" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果 8080/8090 被占用，Vite 会直接报错（不会自动跳到 5173/5174）。" -ForegroundColor Yellow
