# MOJ Laws Scraper

Grabs statute data from the Saudi MOJ legal portal (`laws.moj.gov.sa`) via its
internal API and saves it as clean JSON files.

## Why API instead of HTML?

The site is a JS SPA (content loads via JavaScript after page load), so plain
HTML scraping just gets you an empty "Loading..." page. This tool talks
directly to the API the site itself uses:

```
GET https://laws-gateway.moj.gov.sa/apis/legislations/v1/statute/get-Statute-gateway-Detail?Serial={SERIAL}
```

## Requirements

```bash
pip install requests --break-system-packages
```

## How to get a statute's Serial

1. Open the statute page on `laws.moj.gov.sa`
2. F12 -> Network tab -> filter Fetch/XHR -> refresh the page
3. Look for a request called `get-Statute-gateway-Detail`
4. The value after `Serial=` in that request URL is what you need

Or just grab it straight from the page URL:
`https://laws.moj.gov.sa/ar/legislation/{SERIAL}`

## Usage

```bash
# one statute
python3 scraper.py sSe-gyvwrajdndY5P08WZg

# multiple statutes in one go (same code, zero changes needed)
python3 scraper.py sSe-gyvwrajdndY5P08WZg YKWucFk-FcY_A84_-dpluA --output output

# add a delay between requests (be nice to the server, avoid rate limits)
python3 scraper.py sSe-gyvwrajdndY5P08WZg --delay 2
```

Each statute gets saved as its own JSON file in `output/`.

## Validating the output

```bash
python3 validate.py output/*.json
```

Checks:
- all required top-level fields exist (title, url, articles...)
- `article_count` matches the actual number of articles
- no leftover HTML tags in article text
- no duplicate article numbers

## Output shape

```json
{
  "document_title": "نظام المرافعات الشرعية",
  "summary": "...",
  "status": "ساري",
  "serial": "sSe-gyvwrajdndY5P08WZg",
  "source_url": "https://laws.moj.gov.sa/ar/legislation/sSe-gyvwrajdndY5P08WZg",
  "article_count": 187,
  "articles": [
    {
      "article_number": "المادة الأولى",
      "part": "الباب الأول",
      "chapter": null,
      "article_text": "تطبق المحاكم على القضايا المعروضة أمامها...",
      "is_cancelled": false,
      "legal_status": "اصلية"
    }
  ],
  "scraped_at": "2026-07-02T10:00:00Z"
}
```
