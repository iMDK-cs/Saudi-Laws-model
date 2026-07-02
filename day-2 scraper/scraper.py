"""
scraper.py
Grabs statute data from the Saudi MOJ legal portal (laws.moj.gov.sa).

Just pass any statute's Serial (grabbed from browser DevTools) and it works -
same code handles every statute, no per-statute tweaking needed.
"""

import json
import time
import argparse
from pathlib import Path

import requests

API_URL = "https://laws-gateway.moj.gov.sa/apis/legislations/v1/statute/get-Statute-gateway-Detail"

HEADERS = {
    "Accept": "*/*",
    "Origin": "https://laws.moj.gov.sa",
    "Referer": "https://laws.moj.gov.sa/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    ),
}

TYPE_PART, TYPE_CHAPTER, TYPE_ARTICLE = 3, 2, 1


def fetch_statute(serial: str, timeout: int = 20) -> dict:
    """Hit the API for one statute by its Serial, return the raw model dict."""
    params = {"Serial": serial, "identityNumber": ""}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API returned success=False for serial={serial}: {data.get('message')}")
    return data["model"]


def _strip_html(html_text: str) -> str:
    """Strip basic HTML tags (p, br, span...) from article text, keep line breaks."""
    if not html_text:
        return ""
    import re
    text = re.sub(r"<br\s*/?>", "\n", html_text)
    text = re.sub(r"</p>\s*<p[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ")
    return text.strip()


def _walk(nodes, part=None, chapter=None, articles=None):
    """Recursively walk the statuteStructure tree and flatten every article out."""
    if articles is None:
        articles = []
    for node in nodes or []:
        node_type = node.get("type")
        if node_type == TYPE_PART:
            _walk(node.get("items"), part=node.get("sequence"), chapter=None, articles=articles)
        elif node_type == TYPE_CHAPTER:
            _walk(node.get("items"), part=part, chapter=node.get("sequence"), articles=articles)
        elif node_type == TYPE_ARTICLE:
            articles.append({
                "article_number": node.get("sequence"),
                "part": part,
                "chapter": chapter,
                "article_text": _strip_html(node.get("text")),
                "is_cancelled": node.get("isCancelled", False),
                "legal_status": node.get("legalStatusName"),
            })
            # some articles have sub-items too, just in case, walk those too
            if node.get("items"):
                _walk(node.get("items"), part=part, chapter=chapter, articles=articles)
    return articles


def parse_statute(model: dict, source_url: str) -> dict:
    """Turn the raw API response into the clean JSON shape we want to save."""
    articles = _walk(model.get("statuteStructure"))
    hard_copy = model.get("hardCopy") or {}

    return {
        "document_title": model.get("name"),
        "summary": model.get("summary"),
        "legal_type": model.get("legalType"),
        "status": model.get("legalStatueName"),
        "classification": model.get("classificationName"),
        "workflow_status": model.get("workflowStatueName"),
        "issuance_date_hijri": model.get("issuanceDate"),
        "publish_date_hijri": model.get("publishDate"),
        "serial": model.get("serial"),
        "source_url": source_url,
        "pdf_document_name": hard_copy.get("documentName"),
        "article_count": len(articles),
        "articles": articles,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def slugify(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")


def scrape_and_save(serial: str, output_dir: str = "output") -> Path:
    source_url = f"https://laws.moj.gov.sa/ar/legislation/{serial}"
    model = fetch_statute(serial)
    parsed = parse_statute(model, source_url)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slugify(parsed['document_title'] or serial)}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MOJ Laws Portal scraper")
    ap.add_argument("serials", nargs="+", help="one or more statute Serial values")
    ap.add_argument("--output", default="output", help="folder to save JSON files in")
    ap.add_argument("--delay", type=float, default=1.0, help="delay between requests (seconds)")
    args = ap.parse_args()

    for i, serial in enumerate(args.serials):
        print(f"[{i+1}/{len(args.serials)}] Scraping serial={serial} ...")
        try:
            path = scrape_and_save(serial, args.output)
            print(f"  -> saved to {path}")
        except Exception as e:
            print(f"  !! failed: {e}")
        if i < len(args.serials) - 1:
            time.sleep(args.delay)
