"""
Deep HTML table and article extractor with Jina Reader fallback.
"""

import re
import urllib.parse
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

def clean_jina_markdown(md_text: str, max_chars: int = 9000) -> str:
    """Cleans Jina Reader markdown output by removing cookie banners and image tags."""
    if not md_text:
        return ""
    # Jump to first main H1 heading if preceded by cookie wall
    h1_match = re.search(r"\n#\s+[^\n]+", md_text)
    if h1_match and ("cookie" in md_text[:h1_match.start()].lower() or h1_match.start() < 3500):
        header_lines = [l for l in md_text[:400].splitlines() if l.startswith("Title:") or l.startswith("URL Source:")]
        md_text = "\n".join(header_lines) + "\n" + md_text[h1_match.start():]

    # Remove markdown images
    md_text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", md_text)
    # Compact markdown links [Label](url) -> Label
    md_text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", md_text)
    # Strip cookie/consent noise
    noisy = [
        r"(?i)^.*consent to cookies.*$",
        r"(?i)^.*manage preferences.*$",
        r"(?i)^.*skip to main content.*$",
    ]
    for p in noisy:
        md_text = re.sub(p, "", md_text, flags=re.M)

    md_text = re.sub(r"\n{3,}", "\n\n", md_text).strip()
    return md_text[:max_chars]


def fetch_url_via_jina(url: str, max_chars: int = 9000) -> Optional[Dict]:
    """Fetches JS-heavy or Akamai/Cloudflare protected pages via Jina Reader."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        r = requests.get(jina_url, headers={"X-Return-Format": "markdown"}, timeout=12)
        if r.status_code == 200 and len(r.text) > 100:
            cleaned = clean_jina_markdown(r.text, max_chars=max_chars)
            title_m = re.search(r"^Title:\s*(.+)$", r.text, flags=re.M)
            title = title_m.group(1).strip() if title_m else url
            return {"url": url, "title": title, "content": cleaned}
    except Exception:
        pass
    return None


def fetch_url_text(url: str, max_chars: int = 8000) -> Dict:
    """Extracts readable article text AND HTML tables, with automatic Jina Reader fallback."""
    title = url
    direct_content = ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg"]):
            tag.decompose()
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        blocks = []
        # Extract HTML tables as Markdown tables
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr")[:45]:
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                if any(cells):
                    rows.append("| " + " | ".join(cells) + " |")
            if len(rows) >= 2:
                blocks.append("\n".join(rows))

        # Extract headings, paragraphs, and list items
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "article"]):
            t = el.get_text(" ", strip=True)
            if len(t) > 25 and "cookie" not in t.lower():
                blocks.append(t)

        direct_content = "\n".join(blocks)
        direct_content = re.sub(r"[ \t]+", " ", direct_content).strip()
    except Exception:
        direct_content = ""

    # If direct scrape returned little content (JS-rendered client app), use Jina Reader
    if len(direct_content) < 700 or "enable javascript" in direct_content.lower():
        jina_res = fetch_url_via_jina(url, max_chars=max_chars)
        if jina_res and len(jina_res["content"]) > len(direct_content):
            return jina_res

    if not direct_content:
        return {"url": url, "title": title, "content": "[Page content requires dynamic rendering or is unavailable]"}

    return {"url": url, "title": title, "content": direct_content[:max_chars]}
