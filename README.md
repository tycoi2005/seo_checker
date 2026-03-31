# SEO Checker

A Python CLI tool that audits any website for SEO issues — meta tags, robots.txt, sitemaps, broken links, and orphaned pages — then gives you actionable recommendations to fix them.

## Quick Start

```bash
pip install -r requirements.txt

# From inside this directory
python main.py https://example.com

# Or from the parent directory
python -m seo_checker.main https://example.com
```

That's it. You get a color-coded report in your terminal.

## What It Checks

### Meta Tags
| Check | Severity | Why It Matters |
|-------|----------|---------------|
| Missing/duplicate `<title>` | CRITICAL | Most important on-page SEO signal |
| Title length (30-60 chars) | MEDIUM | Too short wastes opportunity; too long gets truncated |
| Missing meta description | HIGH | Directly influences click-through rate from search results |
| Description length (120-160 chars) | MEDIUM | Stay within Google's display limits |
| Missing canonical URL | HIGH | Prevents duplicate content penalties |
| Missing viewport tag | HIGH | Required for mobile-friendly ranking |
| Missing charset / lang | MEDIUM | Proper rendering and language targeting |
| Missing Open Graph tags | MEDIUM | Controls how pages look when shared on social media |
| Missing Twitter Cards | LOW | Optimizes link previews on X/Twitter |
| Missing structured data (JSON-LD) | MEDIUM | Enables rich results in search |
| Missing favicon | LOW | Brand recognition in browser tabs |

### Robots.txt
| Check | Severity | Why It Matters |
|-------|----------|---------------|
| Missing file | HIGH | Search engines benefit from crawl guidance |
| Aggressive crawl-delay (>5s) | MEDIUM | Slows down indexing unnecessarily |
| No sitemap declaration | MEDIUM | Helps crawlers discover your sitemap |

### Sitemaps
| Check | Severity | Why It Matters |
|-------|----------|---------------|
| Missing sitemap | HIGH | Critical for large or complex sites |
| Outdated entries (pre-2024) | HIGH | Stale sitemaps may contain dead URLs |
| Over 50,000 URLs | MEDIUM | Exceeds sitemap protocol limits |

### Links
| Check | Severity | Why It Matters |
|-------|----------|---------------|
| Broken internal links | HIGH | Wastes crawl budget, harms user experience |
| Orphaned pages | MEDIUM | Pages in sitemap with no internal links are hard for crawlers to discover |

## Usage

```
python main.py <url> [options]

Positional:
  url                   URL of the website to analyze

Options:
  --format {console,markdown,json}   Output format (default: console)
  -o, --output FILE                  Save report to file (markdown/json)
  --check-links                      Check HTTP status of internal links (slower)
  --max-link-checks N                Max links to check (default: 50)
  --timeout N                        HTTP timeout in seconds (default: 30)
  -h, --help                         Show help
```

### Examples

```bash
# Quick audit with console output
python main.py https://example.com

# Save markdown report
python main.py https://example.com --format markdown -o report.md

# Save JSON for CI/CD or dashboards
python main.py https://example.com --format json -o report.json

# Check for broken links (slower, checks up to 50 by default)
python main.py https://example.com --check-links

# Check more links on a large site
python main.py https://example.com --check-links --max-link-checks 200
```

## Output

### Console

```
╭──────────────────────────────────────────────────╮
│ SEO Audit Report                                 │
│ https://messagewatcher.com - 2026-03-31 12:55:11 │
╰──────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────╮
│ Meta Tags Analysis                                       │
╰──────────────────────────────────────────────────────────╯
  Title                 Missing
  Meta Description      Meet the regulatory requirements...
  Canonical             https://messagewatcher.com/
  Open Graph Tags       7 tags found
  Structured Data       1 blocks found

╭──────────────────────────────────────────────────────────╮
│ Issues Summary                                           │
╰──────────────────────────────────────────────────────────╯
  Severity    Count
  CRITICAL    1
  HIGH        2
  LOW         1

[CRITICAL] Duplicate <title> tags found (2 instances)
  → Ensure only one <title> tag exists in the <head> section

[HIGH] Missing robots.txt file
  → Create a robots.txt file to guide search engine crawlers
```

### JSON

Structured output for automation, CI/CD pipelines, or dashboards:

```json
{
  "url": "https://example.com",
  "date": "2026-03-31T12:55:30",
  "meta_tags": {
    "title": "Example Domain",
    "meta_description": null,
    "canonical": null,
    "og_tags": {},
    "issues": [{"severity": "HIGH", "issue": "Missing meta description", "recommendation": "..."}]
  },
  "robots_txt": { "exists": false, "issues": [] },
  "sitemap": { "exists": false, "total_urls": 0 },
  "links": { "total_links": 1, "broken_links": 0, "orphaned_pages": 0 }
}
```

## Project Structure

```
seo_checker/
├── __init__.py                 # Package init
├── __main__.py                 # Enables `python -m seo_checker`
├── http_client.py              # HTTP client with session management
├── meta_checker.py             # Meta tag analysis (title, OG, Twitter, etc.)
├── robots_sitemap_checker.py   # Robots.txt and sitemap parsing
├── link_checker.py             # Link extraction and orphan detection
├── report_generator.py         # Console, markdown, JSON output
└── main.py                     # CLI entry point (argparse)

tests/
├── test_http_client.py
├── test_meta_checker.py
├── test_robots_sitemap_checker.py
├── test_link_checker.py
└── test_report_generator.py
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Lint
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .

# Run all tests
pytest tests/

# Run a single test
pytest tests/test_meta_checker.py -k test_check_title
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client |
| `beautifulsoup4` + `lxml` | HTML/XML parsing |
| `rich` | Colorized console output |

## License

MIT
