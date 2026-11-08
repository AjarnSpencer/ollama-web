# 🌐 ollama-web (`oweb`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange.svg)](https://ollama.ai/)
[![Zero API Keys](https://img.shields.io/badge/API%20Keys-Zero%20Required-green.svg)](#zero-key-architecture)

> **Universal live web search, deep HTML table scraper, desktop GUI proxy daemon, and MCP server for Ollama on Linux, macOS, and Windows.**

`ollama-web` bridges the gap between local AI and the live internet. It works universally across **any model** you have downloaded locally (`llama3.1`, `dolphin-llama3`, `gemma2`, `qwen2.5`, `mistral`, etc.), requires **zero API keys**, converts sports scores and fixture lists into structured markdown tables, and provides a **transparent proxy daemon** so desktop GUI apps (like Chatbox, LibreChat, and Open WebUI) get real-time internet search out of the box.

---

## ✨ Features

- **Universal Model Agnostic:** Automatically queries your local Ollama daemon (`/api/tags`). Never assumes specific models are installed; dynamically resolves and fuzzy-matches whatever you have on disk.
- **Interactive First-Run Setup:** If you don't specify a model, an interactive numbered menu shows your local models and lets you select a default with one keystroke, remembered across sessions.
- **Zero API Key Requirement:** Combines DuckDuckGo and Google News RSS out of the box. Zero accounts, zero credit cards, zero rate-limit blocks.
- **Deep HTML Table & JavaScript Scraper:** Automatically converts HTML tables into clean Markdown tables, and falls back to Jina Reader (`r.jina.ai`) for JavaScript-rendered scoreboards.
- **Zero Bloat for Pure Search Users:** Core package requires only lightweight HTTP and parsing libraries (`requests`, `beautifulsoup4`, `lxml`, `ddgs`). Fast installs with zero heavy multimedia dependencies.
- **Unix Composable Voice:** Seamlessly pairs with companion [`ollama-speak`](https://github.com/AjarnSpencer/ollama-speak) for multilingual spoken readout via pipes or `--speak`.
- **Syntax Guardrails:** Proactively detects common CLI slip-ups like unclosed quotes (`"`) or accidental `-m web` flags without crashing.
- **Transparent Desktop GUI Proxy (`--proxy`):** Runs a lightweight local proxy on `127.0.0.1:11435`. Point any Ollama GUI client (Ollama Desktop, Chatbox, LibreChat, Open WebUI) to port 11435 for instant live web search.
- **Native MCP Server (`--mcp`):** Plugs directly into Claude Desktop, Cursor, and Antigravity as a Model Context Protocol tool provider.

---

## 🚀 Quickstart and Installation

### Option 1: Via PyPI (Recommended for Python users)
```bash
pip install --upgrade ollama-web
```
*(Or use `pipx install ollama-web` for isolated environment installation).*

To install with the companion voice engine:
```bash
pip install --upgrade "ollama-web[speak]"
```

### Option 2: One-Line Installer Script
**Linux & macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/AjarnSpencer/ollama-web/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/AjarnSpencer/ollama-web/main/install.ps1 | iex
```

### Option 3: Standalone Single-File Binaries (Zero Python Required)
Download the standalone executable for your operating system from the [Latest Releases](https://github.com/AjarnSpencer/ollama-web/releases):
- **Windows:** `ollama-web-windows-x64.exe`
- **macOS:** `ollama-web-macos-universal`
- **Linux:** `ollama-web-linux-x86_64` / `ollama-web-linux-arm64`

---

## 🖥️ CLI Usage Examples

### 1. Simple Search Query (Uses Your Default Model)
```bash
ollama-web "What are the latest developments in quantum computing this week?"
```

### 2. Targeting a Specific Local Model
You can use either `-m <model>` or positional syntax:
```bash
ollama-web -m dolphin-llama3:70b "Latest UEFA Champions League standings and scores"
```
Or simply:
```bash
ollama-web gemma4:31b "Explain today's top tech news"
```

### 3. Sports Scores & HTML Tables
Ask for tables directly—`ollama-web` extracts live web data into markdown tables:
```bash
ollama-web -m llama3.1 "Latest 5 La Liga results and next weekend fixtures displayed as a table"
```

### 4. Interactive Terminal REPL
Run without arguments to enter an interactive conversation session with history memory:
```bash
ollama-web
```
Inside the interactive prompt:
- `/model <name>` — Switch the active local model on the fly
- `/models` — List all local Ollama models and their parameters
- `/speak` — Toggle companion spoken voice readout on/off
- `/clear` — Clear conversational context
- `/exit` — Quit

---

## 🗣️ Companion Voice Integration (ollama-speak)

To maintain a clean separation of concerns and zero dependency bloat for pure search users, spoken voice capabilities are packaged separately in [`ollama-speak`](https://github.com/AjarnSpencer/ollama-speak).

### Using with ollama-speak
1. **Unix Pipe (Recommended):**
   ```bash
   ollama-web "Latest news on James Webb Space Telescope" | ollama-speak
   ```
2. **Command Line Flag:**
   ```bash
   ollama-web --speak "What is quantum computing?"
   ```
3. **Piping Any Ollama Model to Speech:**
   ```bash
   ollama run llama3 "Tell me a short bedtime story" | ollama-speak
   ```

---

## 🪟 Desktop GUI App Integration (Transparent Proxy)

Want live web search inside your favorite Ollama desktop GUI or web interface?

1. **Start the Proxy Daemon:**
   ```bash
   ollama-web --proxy
   ```
   *(Running on `http://127.0.0.1:11435`)*

2. **Configure Your GUI Client:**
   In your client application's settings, change the Ollama Base URL:
   - **Default:** `http://127.0.0.1:11434`
   - **Change to:** `http://127.0.0.1:11435`

3. **Enjoy Live Internet Search:**
   Any prompt you submit through the GUI (Chatbox, LibreChat, Open WebUI, Jan.ai) will now automatically be augmented with real-time web search and scraped markdown tables before reaching your local model!

---

## 🔌 Model Context Protocol (MCP) Server

To use `ollama-web` as a web-search tool provider in **Claude Desktop**, add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ollama-web": {
      "command": "ollama-web",
      "args": ["--mcp"]
    }
  }
}
```

---

## ⚙️ Configuration

Configuration is stored in `~/.config/ollama-web/config.json` (or `%APPDATA%\ollama-web\config.json` on Windows):

```json
{
  "default_model": "llama3.1:70b",
  "search_mode": "auto",
  "num_ctx": 16384,
  "max_search_results": 5,
  "speak_enabled": false
}
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [Issues page](https://github.com/AjarnSpencer/ollama-web/issues).

## 📄 License

This project is licensed under the [MIT License](LICENSE).
