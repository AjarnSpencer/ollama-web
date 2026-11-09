#!/usr/bin/env bash
# ollama-web turnkey isolated installer for Linux and macOS
# Universal live web search, deep scraper, desktop GUI proxy daemon, and MCP server
set -e

APP_NAME="ollama-web"
INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
REPO_URL="https://github.com/AjarnSpencer/ollama-web.git"

echo "=================================================="
echo " 🌐 Installing ${APP_NAME} (Universal Ollama Search)"
echo "=================================================="

# 1. Detect Python 3.9+
if command -v python3 >/dev/null 2>&1; then
    PY_SYSTEM="python3"
elif command -v python >/dev/null 2>&1; then
    PY_SYSTEM="python"
else
    echo "❌ Error: Python 3.9+ is required but not installed." >&2
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip" >&2
    echo "   Fedora/RHEL:   sudo dnf install -y python3" >&2
    echo "   macOS:         brew install python" >&2
    exit 1
fi

# Verify Python version >= 3.9
PY_VER=$($PY_SYSTEM -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PY_SYSTEM -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PY_SYSTEM -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    echo "❌ Error: Python 3.9+ required. Found Python ${PY_VER}." >&2
    exit 1
fi
echo "✓ Detected Python ${PY_VER} (${PY_SYSTEM})"

# 2. Check for python3-venv support
if ! $PY_SYSTEM -m venv --help >/dev/null 2>&1; then
    echo "❌ Error: The 'venv' module is missing from your Python installation." >&2
    echo "   On Ubuntu/Debian, run: sudo apt install -y python3-venv" >&2
    exit 1
fi

# 3. Create dedicated isolated virtual environment (bypasses PEP 668 cleanly)
echo "→ Setting up isolated virtual environment in ${INSTALL_DIR}/venv..."
mkdir -p "${INSTALL_DIR}"
$PY_SYSTEM -m venv "${INSTALL_DIR}/venv"
VENV_PY="${INSTALL_DIR}/venv/bin/python"
VENV_PIP="${INSTALL_DIR}/venv/bin/pip"

# Upgrade pip and wheel in isolated venv
"${VENV_PIP}" install --quiet --upgrade pip wheel setuptools

# 4. Install the package
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if [ -f "${SCRIPT_DIR}/pyproject.toml" ]; then
    echo "→ Installing from local source (${SCRIPT_DIR})..."
    "${VENV_PIP}" install --upgrade "${SCRIPT_DIR}"
else
    echo "→ Installing latest release from GitHub (${REPO_URL})..."
    "${VENV_PIP}" install --upgrade "git+${REPO_URL}"
fi

# 5. Create symlinks in ~/.local/bin
mkdir -p "${BIN_DIR}"
ln -sf "${INSTALL_DIR}/venv/bin/ollama-web" "${BIN_DIR}/ollama-web"
ln -sf "${INSTALL_DIR}/venv/bin/oweb" "${BIN_DIR}/oweb"
echo "✓ Created launcher symlinks in ${BIN_DIR}"

# 6. Ensure ~/.local/bin is on PATH
PATH_CONFIGURED=false
case ":$PATH:" in
    *":${BIN_DIR}:"*) PATH_CONFIGURED=true ;;
esac

if [ "$PATH_CONFIGURED" = false ]; then
    echo "→ Adding ${BIN_DIR} to your shell profile..."
    SHELL_NAME=$(basename "${SHELL:-bash}")
    RC_FILE=""
    if [ "$SHELL_NAME" = "zsh" ]; then
        RC_FILE="${HOME}/.zshrc"
    elif [ "$SHELL_NAME" = "bash" ]; then
        if [ -f "${HOME}/.bashrc" ]; then
            RC_FILE="${HOME}/.bashrc"
        elif [ -f "${HOME}/.bash_profile" ]; then
            RC_FILE="${HOME}/.bash_profile"
        fi
    fi
    if [ -n "$RC_FILE" ] && [ -w "$RC_FILE" ]; then
        if ! grep -q ".local/bin" "$RC_FILE"; then
            echo '' >> "$RC_FILE"
            echo '# Added by ollama-web installer' >> "$RC_FILE"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
            echo "✓ Added PATH export to ${RC_FILE}"
        fi
    fi
fi

# 7. Check for companion voice engine (ollama-speak)
if ! command -v ollama-speak >/dev/null 2>&1 && ! command -v ospeak >/dev/null 2>&1; then
    echo "→ Companion voice engine (ollama-speak) not found."
    echo "  To add 100% local voice narration, install it anytime with:"
    echo "    curl -fsSL https://raw.githubusercontent.com/AjarnSpencer/ollama-speak/main/install.sh | bash"
fi

echo "=================================================="
echo " 🎉 Installation Complete!"
echo "=================================================="
echo " You can now run:"
echo "   ollama-web \"your search query\""
echo "   oweb \"fast shortcut\""
echo " Or attach transparent web search to native 'ollama run':"
echo "   ollama-web --install-hook"
if [ "$PATH_CONFIGURED" = false ]; then
    echo ""
    echo " ⚠️  Note: If 'ollama-web' is not recognized immediately in your current terminal,"
    echo "     run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "     or restart your terminal."
fi
echo "=================================================="
