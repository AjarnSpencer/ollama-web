#!/usr/bin/env bash
# ollama-web one-line installer for Linux and macOS
set -e

echo "=================================================="
echo " 🌐 Installing ollama-web (Universal Ollama Search)"
echo "=================================================="

# Check for Python 3.9+
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    echo "[!] Error: Python 3.9+ is required but not found."
    exit 1
fi

# Detect pipx or pip
if command -v pipx >/dev/null 2>&1; then
    echo "→ Installing via pipx..."
    pipx install --upgrade git+https://github.com/AjarnSpencer/ollama-web.git || pipx install --upgrade ollama-web
else
    echo "→ Installing via user pip..."
    $PY_BIN -m pip install --user --upgrade git+https://github.com/AjarnSpencer/ollama-web.git || $PY_BIN -m pip install --user --upgrade ollama-web
fi

echo "=================================================="
echo " ✓ Installation complete!"
echo " Run: 'ollama-web \"your search query\"'"
echo " Or start the GUI proxy: 'ollama-web --proxy'"
echo "=================================================="
