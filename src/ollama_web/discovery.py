"""
Dynamic model discovery, capability inspection, and interactive selection.
"""

import os
import re
import sys
import difflib
import requests
from typing import List, Dict, Optional, Tuple

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_MAGENTA = "\033[95m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def sanitize_terminal_input(text: str) -> str:
    """Removes terminal escape sequences, box characters, and glob expansion artifacts."""
    if not text:
        return ""
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z~]", " ", text)
    text = re.sub(r"\^\[\[[0-9;]*[a-zA-Z~]", " ", text)
    # Strip terminal border/box-drawing glyphs
    text = re.sub(r"[\u2500-\u257f\u2580-\u259f\u25a0-\u25ff┃│║━─┌┐└┘├┤┬┴┼]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def check_syntax_guardrails(raw_prompt: str) -> List[str]:
    """Inspects raw user CLI input for common errors like unclosed quotes."""
    warnings = []
    # Check for unmatched double quotes
    double_quotes = raw_prompt.count('"')
    if double_quotes % 2 != 0:
        warnings.append("Detected an unclosed double quote (\") in your prompt. Ensure your query string is closed.")
    single_quotes = raw_prompt.count("'")
    if single_quotes % 2 != 0:
        warnings.append("Detected an unclosed single quote (') in your prompt.")
    return warnings


def get_local_models() -> List[Dict]:
    """Queries Ollama /api/tags to list all locally installed models."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        r.raise_for_status()
        models = r.json().get("models", [])
        # Separate local non-zero-byte models from cloud stubs
        local = [m for m in models if m.get("size", 0) > 10_000_000 and "embed" not in m.get("name", "")]
        cloud = [m for m in models if m.get("size", 0) <= 10_000_000]
        return local + cloud
    except Exception as e:
        return []


def get_model_capabilities(model_name: str) -> List[str]:
    """Inspects Ollama /api/show for model capabilities (tools, thinking, completion)."""
    try:
        r = requests.post(f"{OLLAMA_HOST}/api/show", json={"name": model_name}, timeout=5)
        if r.status_code == 200:
            return r.json().get("capabilities", ["completion"])
    except Exception:
        pass
    return ["completion"]


def is_known_model_token(token: str) -> Optional[str]:
    """Returns resolved model name if token matches any local model; returns None if it's a command/query keyword."""
    if not token:
        return None
    tok = sanitize_terminal_input(token).strip()
    if not tok or " " in tok:
        return None
    if tok.lower() in ("web", "search", "online", "auto", "default", "none"):
        return None

    models = get_local_models()
    names = [m["name"] for m in models]
    if tok in names:
        return tok
    # Exact base match before ':'
    for n in names:
        base = n.split(":")[0]
        if tok.lower() == n.lower() or tok.lower() == base.lower():
            return n
        if (":" in tok or "/" in tok) and tok.lower() in n.lower():
            return n
    # Prefix match (e.g. 'dolphin-llama3' -> 'dolphin-llama3:70b', 'llama3.1' -> 'llama3.1:70b')
    for n in names:
        if n.lower().startswith(tok.lower()):
            return n
    # Substring match
    for n in names:
        if tok.lower() in n.lower():
            return n
    return None


def resolve_model_name(requested_name: Optional[str]) -> Optional[str]:
    """Resolves an explicitly requested model name, handling fuzzy matching."""
    if not requested_name:
        return None
    req = sanitize_terminal_input(requested_name).strip()
    if not req or req.lower() in ("web", "search", "online", "auto", "default"):
        return None
    return is_known_model_token(req)


def prompt_interactive_model_selection(installed_models: List[Dict]) -> Optional[str]:
    """
    Presents an interactive numbered menu of installed models when no default is set,
    with clear guidance on how to switch models later.
    """
    if not installed_models:
        print(f"{C_YELLOW}[!] No local Ollama models found at {OLLAMA_HOST}.{C_RESET}")
        print(f"{C_CYAN}Please download a model first using:{C_RESET} ollama run llama3.1 (or gemma2, qwen2.5)")
        return None

    print(f"\n{C_BOLD}{C_CYAN}=================================================================={C_RESET}")
    print(f"{C_BOLD} 🌐 ollama-web — First-Time Model Setup{C_RESET}")
    print(f" Please select a default local model to use for live web queries:")
    print(f"{C_BOLD}{C_CYAN}=================================================================={C_RESET}")

    for idx, m in enumerate(installed_models, 1):
        sz = m.get("size", 0) / (1024 ** 3)
        sz_str = f"{sz:.1f} GB" if sz > 0.05 else "Cloud"
        caps = ", ".join(get_model_capabilities(m["name"]))
        print(f"  {C_GREEN}[{idx}]{C_RESET} {m['name']:<42} {C_DIM}({sz_str}, {caps}){C_RESET}")

    print(f"\n{C_DIM}Tip: You can switch models anytime with:{C_RESET} {C_YELLOW}ollama-web -m <model> \"prompt\"{C_RESET}")
    print(f"{C_DIM}Or inside interactive mode using:{C_RESET} {C_YELLOW}/model <name>{C_RESET}\n")

    while True:
        try:
            choice = input(f"{C_BOLD}Enter number [1-{len(installed_models)}] (default: 1): {C_RESET}").strip()
            if not choice:
                return installed_models[0]["name"]
            if choice.isdigit() and 1 <= int(choice) <= len(installed_models):
                return installed_models[int(choice) - 1]["name"]
            print(f"{C_YELLOW}Invalid choice. Enter a number between 1 and {len(installed_models)}.{C_RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return None
