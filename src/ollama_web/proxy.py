"""
Transparent Ollama & OpenAI API Proxy Daemon.
Runs on localhost:11435 and injects live web search into any Ollama GUI client (Ollama Desktop, Chatbox, LibreChat, Open WebUI).
Uses Python's standard library ThreadingHTTPServer for zero-dependency reliability.
"""

import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import requests

from .search import perform_search, build_search_context_block, distill_search_query
from .discovery import OLLAMA_HOST, is_known_model_token, resolve_model_name

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class OllamaProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default noisy access logs

    def do_GET(self):
        """Pass-through for /api/tags, /api/version, etc. so GUIs discover models seamlessly."""
        target_url = f"{OLLAMA_HOST}{self.path}"
        try:
            r = requests.get(target_url, timeout=10)
            self.send_response(r.status_code)
            for k, v in r.headers.items():
                if k.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(r.content)))
            self.end_headers()
            self.wfile.write(r.content)
        except Exception as e:
            self.send_error(502, f"Ollama proxy connection error: {e}")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            payload = {}

        path = self.path.split("?")[0]

        # 1. Handle Ollama /api/chat
        if path == "/api/chat":
            self.handle_chat_proxy(payload)
        # 2. Handle Ollama /api/generate
        elif path == "/api/generate":
            self.handle_generate_proxy(payload)
        # 3. Handle OpenAI /v1/chat/completions
        elif path == "/v1/chat/completions":
            self.handle_openai_proxy(payload)
        # 4. Fallback pass-through for other endpoints
        else:
            self.passthrough_post(self.path, raw_body)

    def handle_chat_proxy(self, payload: dict):
        messages = payload.get("messages", [])
        last_user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        user_prompt = last_user_msg.get("content", "") if last_user_msg else ""

        # Auto web search injection
        if user_prompt and len(user_prompt.strip()) > 3:
            print(f"[Proxy] Searching web for: {user_prompt[:60]}...", flush=True)
            res, pages = perform_search(user_prompt, max_results=4, deep_scrape_top=2, verbose=False)
            if res:
                web_block = build_search_context_block(distill_search_query(user_prompt), res, pages)
                last_user_msg["content"] = f"{web_block}\n\nUser Question: {user_prompt}"

        # Enforce sane context window
        options = payload.get("options", {})
        if "num_ctx" not in options:
            options["num_ctx"] = 16384
            payload["options"] = options

        target_url = f"{OLLAMA_HOST}/api/chat"
        self.stream_ollama_response(target_url, payload)

    def handle_generate_proxy(self, payload: dict):
        prompt = payload.get("prompt", "")
        if prompt and len(prompt.strip()) > 3:
            print(f"[Proxy] Searching web for: {prompt[:60]}...", flush=True)
            res, pages = perform_search(prompt, max_results=4, deep_scrape_top=2, verbose=False)
            if res:
                web_block = build_search_context_block(distill_search_query(prompt), res, pages)
                payload["prompt"] = f"{web_block}\n\nUser Question: {prompt}"

        options = payload.get("options", {})
        if "num_ctx" not in options:
            options["num_ctx"] = 16384
            payload["options"] = options

        target_url = f"{OLLAMA_HOST}/api/generate"
        self.stream_ollama_response(target_url, payload)

    def handle_openai_proxy(self, payload: dict):
        # Translate or proxy OpenAI chat completion requests
        target_url = f"{OLLAMA_HOST}/v1/chat/completions"
        self.passthrough_post(self.path, json.dumps(payload).encode("utf-8"))

    def stream_ollama_response(self, target_url: str, payload: dict):
        try:
            with requests.post(target_url, json=payload, stream=True, timeout=300) as r:
                self.send_response(r.status_code)
                for k, v in r.headers.items():
                    if k.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
                        self.send_header(k, v)
                self.end_headers()
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        self.wfile.write(chunk)
                        self.wfile.flush()
        except Exception as e:
            self.send_error(502, f"Proxy stream error: {e}")

    def passthrough_post(self, path: str, raw_body: bytes):
        target_url = f"{OLLAMA_HOST}{path}"
        try:
            r = requests.post(target_url, data=raw_body, headers={"Content-Type": "application/json"}, timeout=300)
            self.send_response(r.status_code)
            for k, v in r.headers.items():
                if k.lower() not in ("content-length", "transfer-encoding", "content-encoding"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(r.content)))
            self.end_headers()
            self.wfile.write(r.content)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

def run_proxy(port: int = 11435, host: str = "127.0.0.1"):
    server = ThreadedHTTPServer((host, port), OllamaProxyHandler)
    print(f"==================================================================")
    print(f" 🌐 ollama-web Transparent Proxy Daemon running on {host}:{port}")
    print(f" Point any Ollama GUI app (Desktop GUI, Chatbox, LibreChat) to:")
    print(f"   http://{host}:{port}")
    print(f" Target Ollama backend: {OLLAMA_HOST}")
    print(f" Press Ctrl+C to stop.")
    print(f"==================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping proxy daemon.")
        server.server_close()
