"""
Search package initialization and unified query orchestration.
"""

import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Tuple

from .base import SearchHit, SearchProvider
from .duckduckgo import DuckDuckGoProvider
from .googlenews import GoogleNewsRSSProvider
from .scraper import fetch_url_text, fetch_url_via_jina

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def distill_search_query(raw_query: str) -> str:
    """Extracts clean topic keywords from natural language prompts, URLs, and markdown."""
    q = raw_query
    # Extract readable keywords from embedded URLs
    urls = re.findall(r"https?://[^\s)>\]\"']+", q)
    url_keywords = []
    for u in urls:
        parsed = urllib.parse.urlparse(u)
        host_parts = [p for p in parsed.netloc.split(".") if p not in ("www", "com", "org", "net", "io", "co", "uk")]
        path_parts = [p for p in re.split(r"[/\-_]", parsed.path) if len(p) > 2 and not re.match(r"^[0-9a-f]{4,}$", p)]
        url_keywords.extend(host_parts[:1] + path_parts[:3])
    q = re.sub(r"https?://[^\s)>\]\"']+", " ", q)

    # Strip markdown, box-drawing characters, and conversational wrappers
    q = re.sub(r"[\*`#>\[\]\u2500-\u257f\u2580-\u259f\u25a0-\u25ff┃│║━─┌┐└┘├┤┬┴┼|]+", " ", q)
    q = re.sub(
        r"(?i)\b(r?etrieve( the)? data from|search( the web)?( for)?|look up|and give( me)? a (resume|summary|synopsis)( of)?|tell me what happened|give me a (resume|summary|synopsis)( of)?)\b",
        " ",
        q
    )
    q = re.sub(r"\s+", " ", q).strip(" :,-.")

    if url_keywords and len(q.split()) < 6:
        q = (" ".join(url_keywords) + " " + q).strip()

    words = q.split()
    if len(words) > 16:
        q = " ".join(words[:16])

    return q if q else raw_query[:100]


def perform_search(query: str, max_results: int = 5, deep_scrape_top: int = 3, verbose: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """Executes live web search using DuckDuckGo with Google News RSS fallback and deep-scrapes top hits."""
    clean_q = distill_search_query(query)
    if verbose:
        print(f"{C_CYAN}🌐 Searching live web for:{C_RESET} {C_BOLD}{clean_q}{C_RESET} ...", flush=True)

    ddg = DuckDuckGoProvider()
    raw_hits = ddg.search(clean_q, max_results=max_results)

    # Fallback to Google News RSS if DDG yielded fewer than 3 hits
    if len(raw_hits) < 3:
        gnews = GoogleNewsRSSProvider()
        fallback_hits = gnews.search(clean_q, max_results=4)
        seen = {h.url for h in raw_hits}
        for fh in fallback_hits:
            if fh.url not in seen:
                raw_hits.append(fh)
                seen.add(fh.url)

    results = [h.to_dict() for h in raw_hits[:max_results]]

    if verbose:
        for idx, r in enumerate(results, 1):
            print(f"  {C_GREEN}[{idx}]{C_RESET} {r['title']} {C_DIM}({r['href']}){C_RESET}", flush=True)

    scraped_pages = []
    for idx, r in enumerate(results, 1):
        if len(scraped_pages) >= deep_scrape_top:
            break
        href = r.get("href", "")
        if href.startswith("http") and "news.google.com/rss" not in href:
            if verbose:
                print(f"  {C_DIM}↳ Reading live content from [{idx}]...{C_RESET}", flush=True)
            page = fetch_url_text(href, max_chars=6500)
            if page["content"] and not page["content"].startswith("[Page content"):
                scraped_pages.append(page)

    return results, scraped_pages


def build_search_context_block(query: str, results: List[Dict], scraped_pages: List[Dict]) -> str:
    """Builds a formatted context injection block containing search snippets and full scraped tables."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"=== LIVE WEB SEARCH RESULTS (Retrieved: {now_str}) ===",
        f"Search Query: {query}",
        ""
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] Title: {r.get('title')}")
        lines.append(f"    URL: {r.get('href')}")
        lines.append(f"    Snippet: {r.get('body')}")
        lines.append("")

    if scraped_pages:
        lines.append("=== EXTRACTED FULL WEBPAGE & TABLE CONTENT ===")
        for p in scraped_pages:
            lines.append(f"\n--- WEBPAGE: {p.get('title')} ({p.get('url')}) ---")
            lines.append(p.get("content", ""))
            lines.append("--- END WEBPAGE ---\n")

    lines.append(
        "CRITICAL INSTRUCTIONS FOR ANSWERING:\n"
        "1. Extract and present ACTUAL facts, dates, match fixtures, scores, and markdown tables directly from the content above.\n"
        "2. NEVER tell the user to 'visit their website'—deliver the requested details directly.\n"
        "3. If the user asks for a 'resume' of events, they mean a summary or synopsis."
    )
    return "\n".join(lines)
