"""
Search package initialization and unified query orchestration.
"""

import re
import sys
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

    # Strip CLI command wrappers and trailing pipe commands
    q = re.sub(r"^(?:ollama-web|oweb|ollama)\s+", "", q, flags=re.IGNORECASE).strip()
    q = re.sub(r"\|\s*(?:ollama-speak|ospeak|speak|cat|less|head|tail)?\s*$", "", q, flags=re.IGNORECASE).strip()

    # Extract readable keywords from embedded URLs
    urls = re.findall(r"https?://[^\s)>\]\"']+", q)
    url_keywords = []
    for u in urls:
        parsed = urllib.parse.urlparse(u)
        host_parts = [p for p in parsed.netloc.split(".") if p not in ("www", "com", "org", "net", "io", "co", "uk")]
        path_parts = [p for p in re.split(r"[/\-_]", parsed.path) if len(p) > 2 and not re.match(r"^[0-9a-f]{4,}$", p)]
        url_keywords.extend(host_parts[:1] + path_parts[:3])
    q = re.sub(r"https?://[^\s)>\]\"']+", " ", q)

    # Strip markdown, box-drawing characters, quotes, and conversational wrappers
    q = re.sub(r"[\*`#>\[\]\u2500-\u257f\u2580-\u259f\u25a0-\u25ff┃│║━─┌┐└┘├┤┬┴┼|\"']+", " ", q)
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
    """Executes live web search using Google News RSS and DuckDuckGo and deep-scrapes top hits."""
    clean_q = distill_search_query(query)
    if verbose:
        print(f"{C_CYAN}🌐 Searching live web for:{C_RESET} {C_BOLD}{clean_q}{C_RESET} ...", file=sys.stderr, flush=True)

    is_news = bool(re.search(r"\b(news|latest|breaking|today|yesterday|this week|update|recent|crackdown|arrest|raid)\b", query, re.IGNORECASE))

    raw_hits = []
    seen = set()

    # 1. If it's a news/current events query, prioritize Google News RSS for fresh timestamps
    if is_news:
        gnews = GoogleNewsRSSProvider()
        news_hits = gnews.search(clean_q, max_results=max_results)
        for nh in news_hits:
            if nh.url not in seen:
                raw_hits.append(nh)
                seen.add(nh.url)

    # 2. Query DuckDuckGo
    ddg = DuckDuckGoProvider()
    ddg_hits = ddg.search(clean_q, max_results=max_results + 3)
    for dh in ddg_hits:
        # If it's a news query, discard generic country overview / encyclopedia landing pages
        if is_news and any(domain in dh.url for domain in ("wikipedia.org/wiki/", "britannica.com/place/", "thailand.go.th/home")):
            continue
        if dh.url not in seen:
            raw_hits.append(dh)
            seen.add(dh.url)

    # 3. Fallback to Google News RSS if DDG yielded fewer than 3 hits
    if not is_news and len(raw_hits) < 3:
        gnews = GoogleNewsRSSProvider()
        fallback_hits = gnews.search(clean_q, max_results=4)
        for fh in fallback_hits:
            if fh.url not in seen:
                raw_hits.append(fh)
                seen.add(fh.url)

    results = [h.to_dict() for h in raw_hits[:max_results]]

    if verbose:
        for idx, r in enumerate(results, 1):
            date_info = f" [{r['date']}]" if r.get("date") else ""
            print(f"  {C_GREEN}[{idx}]{C_RESET} {r['title']}{date_info} {C_DIM}({r['href']}){C_RESET}", file=sys.stderr, flush=True)

    scraped_pages = []
    for idx, r in enumerate(results, 1):
        if len(scraped_pages) >= deep_scrape_top:
            break
        href = r.get("href", "")
        if href.startswith("http") and "news.google.com/rss" not in href:
            if verbose:
                print(f"  {C_DIM}↳ Reading live content from [{idx}]...{C_RESET}", file=sys.stderr, flush=True)
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
        date_str = f" [Published: {r.get('date')}]" if r.get("date") else ""
        lines.append(f"[{i}] Title: {r.get('title')}{date_str}")
        lines.append(f"    URL: {r.get('href')}")
        lines.append(f"    Summary: {r.get('body')}")
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
        "2. Prioritize recent dates and developments (e.g. 2024–2026) over outdated historical events.\n"
        "3. NEVER tell the user to 'visit their website'—deliver the requested details directly.\n"
        "4. If the user asks for a 'resume' of events, they mean a summary or synopsis."
    )
    return "\n".join(lines)
