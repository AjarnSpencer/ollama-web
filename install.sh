#!/usr/bin/env bash
# ollama-web turnkey installer for Linux and macOS
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

# Install dependencies and package
if [ -f "pyproject.toml" ]; then
    echo "→ Installing from local repository..."
    $PY_BIN -m pip install --upgrade .
else
    echo "→ Installing from GitHub..."
    $PY_BIN -m pip install --upgrade git+https://github.com/AjarnSpencer/ollama-web.git
fi

# Check for companion voice engine
if ! command -v ollama-speak >/dev/null 2>&1 && ! command -v ospeak >/dev/null 2>&1; then
    echo "→ Installing local companion voice engine (ollama-speak)..."
    $PY_BIN -m pip install --upgrade git+https://github.com/AjarnSpencer/ollama-speak.git || true
fi

echo "=================================================="
echo " ✓ Installation complete!"
echo " Run: 'ollama-web \"your search query\"'"
echo " Or install terminal hook for native 'ollama run':"
echo "      ollama-web --install-hook"
echo "=================================================="
