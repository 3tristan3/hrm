$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendDir = Join-Path $root "backend_django"
$adminDir = Join-Path $root "frontend_admin"
$frontendDir = Join-Path $root "frontend_vue"

$backendCmd = @"
cd "$backendDir"
if (!(Test-Path ".venv\Scripts\Activate.ps1")) {
  python -m venv .venv
  . .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
} else {
  . .venv\Scripts\Activate.ps1
}
python manage.py runserver
"@

$frontendCmd = @"
cd "$frontendDir"
if (!(Test-Path "node_modules")) {
  npm install
}
npm run dev
"@

$adminCmd = @"
cd "$adminDir"
if (!(Test-Path "node_modules")) {
  npm install
}
npm run dev
"@

Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", $frontendCmd
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", $adminCmd
