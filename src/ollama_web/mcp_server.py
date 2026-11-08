"""
Model Context Protocol (MCP) Server for ollama-web.
Exposes web_search and fetch_page tools via standard JSON-RPC over stdio.
"""

import sys
import json
from .search import perform_search, fetch_url_text, distill_search_query

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the live internet for recent facts, news, sports scores, and articles without an API key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search keywords"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_page",
        "description": "Fetch and extract text and markdown tables from a specific webpage URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to scrape"}
            },
            "required": ["url"]
        }
    }
]

def run_mcp_server():
    """Runs a standard stdio JSON-RPC MCP server."""
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "web_search":
                    q = args.get("query", "")
                    results, pages = perform_search(q, max_results=5, deep_scrape_top=2, verbose=False)
                    content_text = json.dumps({"results": results, "scraped_pages": pages}, indent=2)
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": content_text}]}}
                elif name == "fetch_page":
                    u = args.get("url", "")
                    p = fetch_url_text(u, max_chars=8000)
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": p.get("content", "")}]}}
                else:
                    resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool '{name}' not found"}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
