# 🌐 ollama-web (`oweb`)

[![PyPI version](https://img.shields.io/pypi/v/ollama-web.svg?color=blue)](https://pypi.org/project/ollama-web/)
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
- **Explicit URL Deep Reader:** Pass any URL in your prompt to scrape full page text (up to 7,500 chars) directly into your model context.
- **Real-Time Terminal Streaming (Never Stare at a Blank Screen):** Live search queries and page-reading progress appear immediately so you always know what the tool is doing. Model tokens stream live token-by-token directly to your terminal—fully visible, readable, and copy-pasteable.
- **Zero-Flag Spoken Audio:** Answers are automatically spoken aloud as soon as generation completes when the lightweight companion `ollama-speak` is installed. No complex pipes or extra flags needed! If you prefer silence, simply pass `-q` or `--mute`.
- **Unix Composable Voice:** Seamlessly pairs with companion [`ollama-speak`](https://github.com/AjarnSpencer/ollama-speak) for multilingual spoken readout via pipes (`| ollama-speak`) or automatic background narration. Pipes never swallow text!
- **Syntax Guardrails:** Proactively detects common CLI slip-ups like unclosed quotes (`"`) or accidental `-m web` flags without crashing.
- **Transparent Desktop GUI Proxy (`--proxy`):** Runs a lightweight local proxy on `127.0.0.1:11435`. Point any Ollama GUI client (Ollama Desktop, Chatbox, LibreChat, Open WebUI) to port 11435 for instant live web search.
- **Native MCP Server (`--mcp`):** Plugs directly into Claude Desktop, Cursor, and Antigravity as a Model Context Protocol tool provider.

---

## 🚀 Quickstart and Installation

### Option 1 — Install via PyPI (Recommended for Python users)
`ollama-web` is published to the official Python Package Index (PyPI). You can install it directly into any active Python environment:

```bash
pip install --upgrade ollama-web
```

Or install in an isolated global CLI environment using `pipx` (recommended by the Python Packaging Authority for standalone command line utilities):
```bash
pipx install ollama-web
```

To install with the companion voice engine (`ollama-speak`):
```bash
pip install --upgrade "ollama-web[speak]"
```

---

### Option 2 — One-Line Turnkey Installer (Zero Configuration)
Works cleanly on fresh Linux, macOS, and WSL systems without requiring manual virtual environments or tripping PEP 668 system python locks.

**Linux and macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/AjarnSpencer/ollama-web/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/AjarnSpencer/ollama-web/main/install.ps1 | iex
```

What the turnkey installer does:
- Sets up an isolated virtual environment in `~/.local/share/ollama-web/venv` (zero system conflicts).
- Symlinks `ollama-web` and `oweb` launchers into `~/.local/bin/`.
- Configures user `PATH` if not already set.

---

### Option 3 — Standalone Single-File Binaries (Zero Python Required)
Download the standalone executable for your operating system from the [Latest Releases](https://github.com/AjarnSpencer/ollama-web/releases):
- **Windows:** `ollama-web-windows-x64.exe`
- **macOS:** `ollama-web-macos-universal`
- **Linux:** `ollama-web-linux-x86_64` / `ollama-web-linux-arm64`

---

### Option 4 — Install from GitHub
```bash
pip install git+https://github.com/AjarnSpencer/ollama-web.git
```

---

### 📦 PyPI Package Information (For Maintainers)
- **PyPI Release:** [https://pypi.org/project/ollama-web/](https://pypi.org/project/ollama-web/)
- **Release Automation:** Pushing a version tag (e.g. `git tag v1.0.1 && git push origin v1.0.1`) automatically triggers GitHub Actions (`.github/workflows/release.yml`) to build and publish updates to PyPI.

---

## 📖 Complete Command Line Reference and Flags

`ollama-web` accepts flexible argument ordering. You can pass flags anywhere or use positional tokens.

### Flags Table

| Flag | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--model MODEL` | `-m` | `config.default_model` | Specify target Ollama model (fuzzy-matched against local models) |
| `--install-hook` | | | Seamlessly add live search and voice to native `ollama run` in your terminal |
| `--remove-hook` | | | Remove terminal shell hook from `.bashrc` / `.zshrc` |
| `--mute` | `-q`, `--quiet` | `False` | Mute spoken audio output (silent text-only terminal mode) |
| `--speak` | `-s` | `True` (auto) | Force spoken voice output (voice is already ON by default if companion is installed) |
| `--proxy` | | `False` | Launch transparent desktop GUI proxy daemon |
| `--port PORT` | | `11435` | Custom TCP port for the proxy daemon |
| `--mcp` | | `False` | Run as standard Model Context Protocol (stdio MCP) server |
| `--list-models` | `-l` | | Print table of all locally installed Ollama models and exit |
| `--no-search` | | `False` | Query model directly without live web search |
| `--think` | | `False` | Enable reasoning thinking stream (DeepSeek-R1, QwQ, etc.) |
| `-h`, `--help` | | | Show full help manual and flag descriptions |

---

## 💡 Practical Tutorials and Workflows

### Tutorial 1 — Quick Real-Time Web Search (Text + Automatic Voice)
Run a live web search using your configured default model:
```bash
ollama-web "What are the latest breakthroughs in fusion energy this week?"
```
`ollama-web` will:
1. Search live web sources and Google News RSS.
2. Scrape top resulting pages with live status updates on stderr so you know what is happening.
3. Stream tokens directly to your terminal in real time (fully readable and copy-pasteable).
4. Automatically speak the summary aloud when finished if companion `ollama-speak` is installed.

---

### Tutorial 2 — Silent Terminal Mode (`-q` / `--mute`)
If you want to read in silence without audio playback:
```bash
ollama-web -q "Latest developments in quantum computing"
```
Or use `--mute` anytime.

---

### Tutorial 3 — Native Terminal Integration (`ollama-web --install-hook`)
If you want your standard `ollama` terminal command to automatically gain live web search and voice without changing your habits:
```bash
ollama-web --install-hook
source ~/.bashrc   # or source ~/.zshrc
```
Now, whenever you use `ollama` in the terminal:
- **One-shot prompt with live search + voice:**
  ```bash
  ollama run llama3.1 "What are today's top tech headlines?"
  ```
- **Direct web search shortcut:**
  ```bash
  ollama web "Champions League fixtures this week"
  ```
- **Standard Ollama commands:**
  `ollama list`, `ollama pull`, and interactive sessions continue to pass through directly to the native `ollama` binary without modification.

To remove the hook at any time:
```bash
ollama-web --remove-hook
```

---

### Tutorial 4 — Targeting a Specific Local Model
You can specify the model either with `-m` or by typing the model name directly as the first argument:
```bash
# Using the -m flag:
ollama-web -m dolphin-llama3:70b "Latest UEFA Champions League results and standings"

# Or using natural positional syntax:
ollama-web qwen2.5:32b "Summarize today's top artificial intelligence headlines"
```

---

### Tutorial 5 — Extracting HTML Tables into Markdown
Ask for tables directly—`ollama-web` automatically converts complex HTML tables from web pages into clean Markdown tables:
```bash
ollama-web -m llama3.1 "Latest 5 English Premier League results and table standings"
```

---

### Tutorial 6 — Deep Scraping Explicit URLs
If you want your local LLM to read and analyze an exact web article or blog post, simply include the URL in your prompt:
```bash
ollama-web "https://arstechnica.com/science/ Summarize the lead space exploration article"
```
`ollama-web` will detect the URL, fetch its full clean text (up to 7,500 characters), and feed it directly into the prompt context alongside any web search results.

---

### Tutorial 7 — Reasoning Models with Thinking Mode (`--think`)
For reasoning models (like `deepseek-r1`, `qwq`, or thinking-enabled checkpoints), pass `--think` to stream internal reasoning tokens before the final answer:
```bash
ollama-web -m deepseek-r1:14b --think "Analyze the current economic trends from today's market news"
```

---

### Tutorial 8 — Pure Local Inference Without Web Search (`--no-search`)
Need to ask your model a general programming or logic question without scraping the web? Pass `--no-search`:
```bash
ollama-web --no-search -m llama3.1 "Write a Python script to sort a dictionary by values"
```

---

### Tutorial 9 — Interactive REPL Session
Running `ollama-web` without arguments launches an interactive shell with conversation memory:
```bash
ollama-web
```
Inside the interactive prompt:
- `/model <name>` — Switch the active local model on the fly
- `/models` — List all local Ollama models and their parameters
- `/mute` or `/speak` — Toggle companion voice audio on or off
- `/clear` — Reset conversational memory
- `/exit` — Quit the session

---

### Tutorial 10 — Spoken Voice with Companion `ollama-speak`
`ollama-web` pairs natively with [`ollama-speak`](https://github.com/AjarnSpencer/ollama-speak):

**Method A — Zero-Flag Automatic Voice:**
Just run `ollama-web "..."`. The terminal prints text live while you listen to the spoken answer.

**Method B — Unix Pipe (Zero-Swallow Output):**
```bash
ollama-web "Who won yesterday's basketball matches?" | ollama-speak
```
`ollama-speak` mirrors the text directly to `stdout` so pipes never swallow your screen output.

---

### Tutorial 11 — Transparent Desktop GUI Proxy (`--proxy`)
Enable live web search inside your favorite Ollama desktop apps (Chatbox, LibreChat, Open WebUI, Jan.ai):

1. **Start the proxy in a background terminal:**
   ```bash
   ollama-web --proxy --port 11435
   ```
2. **Point your desktop app's Ollama Base URL to port 11435:**
   - Change `http://127.0.0.1:11434` to `http://127.0.0.1:11435`
3. **Submit any question from your GUI:**
   The proxy automatically searches the web, deep-scrapes tables, injects context, and streams tokens back into your graphical desktop app!

---

### Tutorial 12 — Model Context Protocol (MCP) in Claude Desktop
To expose web search tools directly to Claude Desktop, Cursor, or Antigravity, add this to your `claude_desktop_config.json`:
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

## ⚙️ Persistent Configuration

Your defaults are saved in `~/.config/ollama-web/config.json` (or `%APPDATA%\ollama-web\config.json` on Windows):

```json
{
  "default_model": "llama3.1:70b",
  "search_mode": "auto",
  "num_ctx": 16384,
  "max_search_results": 5,
  "voice_enabled": true
}
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [Issues page](https://github.com/AjarnSpencer/ollama-web/issues).

## 📄 License

This project is licensed under the [MIT License](LICENSE).
