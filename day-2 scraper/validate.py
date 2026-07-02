"""
validate.py
Checks the JSON files scraper.py produces and prints a pass/fail report.
Run: python3 validate.py output/*.json
"""

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = [
    "document_title", "source_url", "serial", "articles", "article_count",
]
REQUIRED_ARTICLE_FIELDS = ["article_number", "article_text"]


def validate_file(path: Path) -> list[str]:
    problems = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    # 1) required top-level fields exist and aren't empty
    for field in REQUIRED_TOP_LEVEL:
        if field not in data or data[field] in (None, ""):
            problems.append(f"missing/empty required field: '{field}'")

    articles = data.get("articles", [])

    # 2) declared count matches actual count
    if data.get("article_count") != len(articles):
        problems.append(
            f"count mismatch: article_count={data.get('article_count')} but actual={len(articles)}"
        )

    if not articles:
        problems.append("no articles extracted at all")

    seen_numbers = set()
    for i, art in enumerate(articles):
        for field in REQUIRED_ARTICLE_FIELDS:
            if not art.get(field):
                problems.append(f"article #{i}: '{field}' is empty")

        text = art.get("article_text", "")
        if "<" in text and ">" in text:
            problems.append(f"article #{i} ({art.get('article_number')}): leftover HTML tags in text")

        num = art.get("article_number")
        if num in seen_numbers:
            problems.append(f"duplicate article number: {num}")
        seen_numbers.add(num)

    return problems


def main():
    paths = sys.argv[1:]
    if not paths:
        print("usage: python3 validate.py output/*.json")
        sys.exit(1)

    total_problems = 0
    for p in paths:
        path = Path(p)
        problems = validate_file(path)
        status = "OK" if not problems else f"FAIL ({len(problems)} issues)"
        print(f"\n{path.name}: {status}")
        for pr in problems:
            print(f"   - {pr}")
        total_problems += len(problems)

    print(f"\n{'='*40}\nTotal: {len(paths)} file(s), {total_problems} issue(s)")
    sys.exit(1 if total_problems else 0)


if __name__ == "__main__":
    main()
