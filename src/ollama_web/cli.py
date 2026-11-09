"""
Main CLI entrypoint for ollama-web (oweb).
"""

import os
import re
import sys
import json
import argparse
import requests
from typing import List, Dict

from .config import load_config, save_config
from .discovery import (
    OLLAMA_HOST,
    get_local_models,
    get_model_capabilities,
    is_known_model_token,
    resolve_model_name,
    prompt_interactive_model_selection,
    sanitize_terminal_input,
    check_syntax_guardrails,
    C_CYAN, C_GREEN, C_YELLOW, C_MAGENTA, C_DIM, C_BOLD, C_RESET
)
from .search import (
    perform_search,
    build_search_context_block,
    distill_search_query,
    fetch_url_text
)
from .voice import speak_text
from .proxy import run_proxy
from .mcp_server import run_mcp_server

SYSTEM_PROMPT = (
    "You are an intelligent AI assistant running locally via Ollama with live internet search "
    "and webpage scraping capabilities. Always extract and present concrete facts, dates, headlines, "
    "match fixtures, scores, and markdown tables directly from the retrieved web content. "
    "Prioritize current, recent developments (2024-2026) over outdated historical events when responding to news queries. "
    "Never tell the user to 'visit the website' instead of answering. "
    "If the user asks for a 'resume' of articles or data, they mean a summary or synopsis."
)


def query_ollama(
    model: str,
    user_prompt: str,
    history: List[Dict],
    search_mode: str = "auto",
    enable_thinking: bool = False,
    max_results: int = 5,
    speak_enabled: bool = False
) -> str:
    user_prompt = sanitize_terminal_input(user_prompt)
    is_piped = not sys.stdout.isatty()

    # 1. Scrape any explicit URLs in the prompt
    explicit_urls = re.findall(r"https?://[^\s)>\]\"']+", user_prompt)
    scraped_explicit = []
    for u in explicit_urls[:4]:
        if not is_piped:
            print(f"{C_CYAN}📄 Fetching URL:{C_RESET} {u} ...", file=sys.stderr, flush=True)
        else:
            print(f"📄 Fetching URL: {u} ...", file=sys.stderr, flush=True)
        scraped_explicit.append(fetch_url_text(u, max_chars=7500))

    augmented_sections = []
    if scraped_explicit:
        url_block = "=== SCRAPED EXPLICIT URL CONTENT ===\n" + "\n\n".join(
            f"URL: {p['url']}\nTitle: {p['title']}\nContent:\n{p['content']}" for p in scraped_explicit
        )
        augmented_sections.append(url_block)

    # 2. Perform live web search
    if search_mode != "off":
        results, scraped_pages = perform_search(user_prompt, max_results=max_results, deep_scrape_top=3, verbose=True)
        if results:
            web_block = build_search_context_block(distill_search_query(user_prompt), results, scraped_pages)
            augmented_sections.append(web_block)

    if augmented_sections:
        augmented_user_content = "\n\n".join(augmented_sections) + f"\n\nUser Request: {user_prompt}"
    else:
        augmented_user_content = user_prompt

    messages = list(history) + [{"role": "user", "content": augmented_user_content}]

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": 16384
        }
    }
    caps = get_model_capabilities(model)
    if "thinking" in caps:
        payload["think"] = bool(enable_thinking)

    if not is_piped:
        sys.stderr.write(f"\n{C_MAGENTA}{C_BOLD}[{model}]{C_RESET} {C_DIM}(evaluating context & generating...){C_RESET}")
        sys.stderr.flush()

    status_cleared = False
    full_reply = []

    try:
        with requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True, timeout=300) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("message", {}).get("content", "")
                if token:
                    if not status_cleared:
                        if not is_piped:
                            sys.stderr.write("\r\033[K" + f"{C_MAGENTA}{C_BOLD}[{model}]{C_RESET} ")
                            sys.stderr.flush()
                        status_cleared = True
                    sys.stdout.write(token)
                    sys.stdout.flush()
                    full_reply.append(token)
                if chunk.get("done"):
                    break
    except KeyboardInterrupt:
        if not status_cleared and not is_piped:
            sys.stderr.write("\r\033[K" + f"{C_MAGENTA}{C_BOLD}[{model}]{C_RESET} ")
            sys.stderr.flush()
        print(f"\n{C_YELLOW}[Generation interrupted]{C_RESET}", file=sys.stderr)
    except Exception as e:
        if not status_cleared and not is_piped:
            sys.stderr.write("\r\033[K" + f"{C_MAGENTA}{C_BOLD}[{model}]{C_RESET} ")
            sys.stderr.flush()
        err_msg = f"Ollama error: {e}"
        print(f"\n{C_YELLOW}[!] {err_msg}{C_RESET}", file=sys.stderr)
        if speak_enabled:
            speak_text(f"Ollama error on model {model}. {e}")

    sys.stdout.write("\n")
    sys.stdout.flush()
    reply_str = "".join(full_reply).strip()

    if reply_str:
        history.append({"role": "user", "content": user_prompt})
        history.append({"role": "assistant", "content": reply_str})
        if speak_enabled:
            speak_text(reply_str)

    return reply_str


def interactive_repl(model: str, search_mode: str = "auto", speak_enabled: bool = True):
    caps = get_model_capabilities(model)
    print(f"{C_BOLD}{C_CYAN}=================================================================={C_RESET}")
    print(f"{C_BOLD} 🌐 ollama-web Interactive Terminal ({model}){C_RESET}")
    print(f" Web Search : {C_GREEN}{search_mode.upper()}{C_RESET}")
    print(f" Spoken Audio: {C_GREEN}{'ON (ollama-speak)' if speak_enabled else 'MUTED'}{C_RESET}")
    print(f" Commands   : {C_YELLOW}/model <name>{C_RESET}, {C_YELLOW}/models{C_RESET}, {C_YELLOW}/search <q>{C_RESET}, {C_YELLOW}/mute{C_RESET}, {C_YELLOW}/clear{C_RESET}, {C_YELLOW}/exit{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}=================================================================={C_RESET}\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            prompt = input(f"{C_BOLD}>>> {C_RESET}").strip()
            if not prompt:
                continue
            if prompt in ("/exit", "/quit", ":q"):
                print("Goodbye!")
                break
            if prompt == "/clear":
                history = [{"role": "system", "content": SYSTEM_PROMPT}]
                print(f"{C_GREEN}Chat history cleared.{C_RESET}\n")
                continue
            if prompt == "/models":
                for m in get_local_models():
                    print(f"  - {m['name']}")
                print()
                continue
            if prompt.startswith("/model "):
                req = prompt.split(" ", 1)[1].strip()
                resolved = resolve_model_name(req)
                if resolved:
                    model = resolved
                    print(f"{C_GREEN}Switched model to: {model}{C_RESET}\n")
                else:
                    print(f"{C_YELLOW}Model '{req}' not found.{C_RESET}\n")
                continue
            if prompt in ("/speak", "/voice", "/mute"):
                speak_enabled = not speak_enabled
                print(f"{C_GREEN}Spoken output: {'ENABLED (ollama-speak)' if speak_enabled else 'MUTED'}{C_RESET}\n")
                continue

            # 1. Clean accidental CLI invocations pasted into the REPL
            pipe_speak = bool(re.search(r'\|\s*(?:ollama-speak|ospeak|speak)\s*$', prompt, re.IGNORECASE))
            prompt = re.sub(r'\|\s*(?:ollama-speak|ospeak|speak)\s*$', '', prompt).strip()
            prompt = re.sub(r'^(?:ollama-web|oweb)\s+', '', prompt).strip()

            model_flag_match = re.match(r'^-m\s+(\S+)\s+(.*)$', prompt)
            if model_flag_match:
                req_model = model_flag_match.group(1).strip()
                resolved = resolve_model_name(req_model)
                if resolved:
                    model = resolved
                    print(f"{C_GREEN}Switched model to: {model}{C_RESET}\n")
                prompt = model_flag_match.group(2).strip()

            if (prompt.startswith('"') and prompt.endswith('"')) or (prompt.startswith("'") and prompt.endswith("'")):
                prompt = prompt[1:-1].strip()

            if not prompt:
                continue

            # Check quote guardrails
            warnings = check_syntax_guardrails(prompt)
            for w in warnings:
                print(f"{C_YELLOW}[!] Warning: {w}{C_RESET}")

            current_speak = speak_enabled or pipe_speak

            query_ollama(
                model=model,
                user_prompt=prompt,
                history=history,
                search_mode=search_mode,
                speak_enabled=current_speak
            )
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def main():
    config = load_config()

    parser = argparse.ArgumentParser(
        prog="ollama-web",
        description="Universal live web search, deep table scraping, and desktop GUI proxy daemon for Ollama."
    )
    parser.add_argument("-m", "--model", default=None, help="Ollama model name or substring")
    parser.add_argument("--proxy", action="store_true", help="Run as transparent GUI proxy daemon on localhost:11435")
    parser.add_argument("--port", type=int, default=11435, help="Port for transparent proxy daemon (default: 11435)")
    parser.add_argument("--mcp", action="store_true", help="Run as Model Context Protocol (MCP) stdio server")
    parser.add_argument("--list-models", "-l", action="store_true", help="List available local Ollama models")
    parser.add_argument("--no-search", action="store_true", help="Disable automatic live web search")
    parser.add_argument("--mute", "-q", "--quiet", action="store_true", help="Mute spoken audio output (silent text-only terminal mode)")
    parser.add_argument("--speak", "-s", action="store_true", help="Force spoken voice output (voice is ON by default if companion is present)")
    parser.add_argument("--think", action="store_true", help="Enable reasoning thinking output if supported")
    parser.add_argument("--install-hook", action="store_true", help="Install shell hook to seamlessly add web search and voice to native 'ollama run' in terminal")
    parser.add_argument("--remove-hook", action="store_true", help="Remove terminal shell hook from .bashrc/.zshrc")
    parser.add_argument("prompt", nargs="*", help="Model name and/or search query")

    args, unknown = parser.parse_known_args()
    if unknown:
        args.prompt.extend(unknown)

    # Subcommand: Terminal Hook Management
    if args.install_hook:
        from .hook import install_hook
        install_hook()
        return

    if args.remove_hook:
        from .hook import remove_hook
        remove_hook()
        return

    # Subcommand: MCP Server
    if args.mcp:
        run_mcp_server()
        return

    # Subcommand: Transparent Proxy Daemon
    if args.proxy:
        run_proxy(port=args.port)
        return

    # Subcommand: List Models
    if args.list_models:
        models = get_local_models()
        print(f"{C_BOLD}{'MODEL NAME':<45} {'SIZE':<10} {'CAPABILITIES'}{C_RESET}")
        print("-" * 75)
        for m in models:
            sz = m.get("size", 0) / (1024 ** 3)
            sz_str = f"{sz:.1f} GB" if sz > 0.05 else "Cloud"
            caps = ", ".join(get_model_capabilities(m["name"]))
            print(f"{m['name']:<45} {sz_str:<10} {caps}")
        return

    prompt_parts = [sanitize_terminal_input(p) for p in args.prompt if sanitize_terminal_input(p)]
    model_name = None
    search_mode = "off" if args.no_search else config.get("search_mode", "auto")

    # 1. Parse -m / --model flag
    if args.model:
        m_lower = args.model.lower().strip()
        if m_lower in ("web", "search", "online", "always"):
            search_mode = "always"
        elif m_lower in ("auto", "default"):
            search_mode = "auto"
        else:
            model_name = resolve_model_name(args.model)

    # 2. Check positional prompt tokens for a model identifier
    if prompt_parts:
        matched_model = is_known_model_token(prompt_parts[0])
        if matched_model:
            if not model_name:
                model_name = matched_model
                prompt_parts = prompt_parts[1:]
            elif model_name == matched_model:
                prompt_parts = prompt_parts[1:]

    # 3. Check persistent config for default model
    if not model_name and config.get("default_model"):
        model_name = resolve_model_name(config["default_model"])

    # 4. First-run selection if model is still unspecified
    if not model_name:
        local_models = get_local_models()
        if not local_models:
            print(f"[!] No local Ollama models found at {OLLAMA_HOST}.", file=sys.stderr)
            print("Please download a model first using: ollama run llama3.1 (or gemma2, qwen2.5)", file=sys.stderr)
            sys.exit(1)
        if not sys.stdin.isatty():
            model_name = local_models[0]["name"]
        else:
            chosen = prompt_interactive_model_selection(local_models)
            if not chosen:
                sys.exit(1)
            model_name = chosen
            config["default_model"] = model_name
            config["first_run_completed"] = True
            save_config(config)

    # Voice is enabled by default for zero-flag ease of use
    default_voice = config.get("voice_enabled", config.get("speak_enabled", True))
    if args.mute:
        speak_enabled = False
    elif args.speak:
        speak_enabled = True
    else:
        speak_enabled = default_voice

    # Proactive quote warnings on single-turn prompt
    if prompt_parts:
        raw_combined = " ".join(args.prompt)
        for w in check_syntax_guardrails(raw_combined):
            print(f"{C_YELLOW}[!] Warning: {w}{C_RESET}", file=sys.stderr)

        user_prompt = " ".join(prompt_parts)
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        query_ollama(
            model=model_name,
            user_prompt=user_prompt,
            history=history,
            search_mode=search_mode,
            enable_thinking=args.think,
            speak_enabled=speak_enabled
        )
    else:
        interactive_repl(
            model=model_name,
            search_mode=search_mode,
            speak_enabled=speak_enabled
        )


if __name__ == "__main__":
    main()
