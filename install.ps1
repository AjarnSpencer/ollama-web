# ollama-web turnkey isolated installer for Windows PowerShell
# Universal live web search, deep scraper, desktop GUI proxy daemon, and MCP server
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " 🌐 Installing ollama-web for Windows (Isolated)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Detect Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[!] Error: Python 3.9+ was not found on your system PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/ (ensure 'Add Python to PATH' is checked)." -ForegroundColor Yellow
    exit 1
}

$InstallDir = Join-Path $env:LOCALAPPDATA "ollama-web"
$VenvDir = Join-Path $InstallDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvScripts = Join-Path $VenvDir "Scripts"

# 2. Create isolated venv
Write-Host "→ Creating isolated virtual environment in $VenvDir..." -ForegroundColor Green
if (-not (Test-Path $VenvDir)) {
    & $pythonCmd.Source -m venv $VenvDir
}

# 3. Upgrade pip and install package
Write-Host "→ Installing dependencies in isolated environment..." -ForegroundColor Green
& $VenvPip install --quiet --upgrade pip wheel setuptools

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $ScriptDir "pyproject.toml")) {
    Write-Host "→ Installing from local directory ($ScriptDir)..." -ForegroundColor Green
    & $VenvPip install --upgrade $ScriptDir
} else {
    Write-Host "→ Installing from GitHub..." -ForegroundColor Green
    & $VenvPip install --upgrade "git+https://github.com/AjarnSpencer/ollama-web.git"
}

# 4. Add Scripts to User PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$VenvScripts*") {
    Write-Host "→ Adding $VenvScripts to User PATH..." -ForegroundColor Green
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$VenvScripts", [EnvironmentVariableTarget]::User)
    $env:Path = "$env:Path;$VenvScripts"
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " ✓ Installation complete!" -ForegroundColor Green
Write-Host " Run: 'ollama-web ""your search query""'" -ForegroundColor White
Write-Host " Or shortcut: 'oweb ""fast shortcut""'" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
