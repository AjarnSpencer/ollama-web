# ollama-web one-line installer for Windows PowerShell
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🌐 Installing ollama-web for Windows" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check for Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[!] Error: Python 3.9+ was not found on your system PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/ or the Microsoft Store." -ForegroundColor Yellow
    exit 1
}

Write-Host "→ Installing ollama-web package via pip..." -ForegroundColor Green
python -m pip install --upgrade --user git+https://github.com/AjarnSpencer/ollama-web.git

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " ✓ Installation complete!" -ForegroundColor Green
Write-Host " Run: 'ollama-web ""your question""'" -ForegroundColor White
Write-Host " Or start proxy daemon for Desktop GUI: 'ollama-web --proxy'" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
