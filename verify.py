#!/usr/bin/env python3
"""
Diagnostic & Verification Suite for ollama-web.
Runs automated smoke tests to verify local Ollama connectivity, search backends, and terminal integration.
"""

import sys
import json
import requests

def test_ollama_daemon():
    print("[1/3] Checking Ollama daemon connectivity (http://127.0.0.1:11434)...", end=" ", flush=True)
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"✓ OK ({len(models)} local models found)")
            return True
        else:
            print(f"❌ Failed (HTTP {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_search_backend():
    print("[2/3] Checking live search backend (DuckDuckGo & Google News)...", end=" ", flush=True)
    try:
        from ollama_web.search import perform_search
        res, pages = perform_search("NASA space mission updates", max_results=3, deep_scrape_top=1, verbose=False)
        if res:
            print(f"✓ OK ({len(res)} results retrieved)")
            return True
        else:
            print("❌ Failed (Zero search results)")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def test_voice_companion():
    print("[3/3] Checking local voice companion dispatch...", end=" ", flush=True)
    import shutil
    has_ospeak = bool(shutil.which("ollama-speak") or shutil.which("ospeak"))
    has_ai_say = bool(shutil.which("ai-say"))
    if has_ospeak:
        print("✓ OK (Found standalone ollama-speak)")
        return True
    elif has_ai_say:
        print("✓ OK (Found host local voice daemon ai-say)")
        return True
    else:
        print("⚠️ Warning (ollama-speak not installed; run 'pip install ollama-speak' for voice)")
        return True

def main():
    print("==================================================")
    print(" 🛠️  ollama-web System Diagnostic & Smoke Test")
    print("==================================================")
    t1 = test_ollama_daemon()
    t2 = test_search_backend()
    t3 = test_voice_companion()
    print("==================================================")
    if t1 and t2 and t3:
        print("🎉 All systems verified and operational!")
        sys.exit(0)
    else:
        print("❌ Diagnostic failures detected. Check logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
