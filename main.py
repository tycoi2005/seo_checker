"""SEO Checker CLI - Analyze any website for SEO issues."""

import argparse
import os
from urllib.parse import urlparse
from datetime import datetime

try:
    from seo_checker.http_client import HttpClient
    from seo_checker.meta_checker import MetaTagChecker, MetaTagAnalysis
    from seo_checker.robots_sitemap_checker import RobotsAndSitemapChecker
    from seo_checker.link_checker import LinkChecker, LinkAnalysis
    from seo_checker.report_generator import ReportGenerator
except ModuleNotFoundError:
    from http_client import HttpClient
    from meta_checker import MetaTagChecker, MetaTagAnalysis
    from robots_sitemap_checker import RobotsAndSitemapChecker
    from link_checker import LinkChecker, LinkAnalysis
    from report_generator import ReportGenerator

from bs4 import BeautifulSoup


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SEO Checker - Analyze websites for SEO issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m seo_checker.main https://example.com
  python -m seo_checker.main https://example.com --format json
  python -m seo_checker.main https://example.com --format markdown -o report.md
  python -m seo_checker.main https://example.com --check-links
        """,
    )

    parser.add_argument(
        "url",
        help="URL of the website to analyze",
    )
    parser.add_argument(
        "--format",
        choices=["console", "markdown", "json"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (for markdown/json formats)",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Check HTTP status of internal links (slower)",
    )
    parser.add_argument(
        "--max-link-checks",
        type=int,
        default=50,
        help="Maximum number of links to check (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP request timeout in seconds (default: 30)",
    )

    return parser.parse_args()


def analyze_website(
    url: str, check_links: bool = False, max_link_checks: int = 50, timeout: int = 30
):
    """Run full SEO analysis on a website."""
    client = HttpClient(timeout=timeout)
    url = HttpClient.normalize_url(url)

    print(f"Analyzing: {url}")
    print("Fetching page...")

    try:
        response = client.fetch(url)
        html = response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        # Build empty objects with an error issue so reports still generate
        meta = MetaTagAnalysis()
        meta.issues.append({"severity": "CRITICAL", "issue": f"Failed to fetch {url}", "recommendation": f"Error: {e}"})
        robots = RobotsAndSitemapChecker(client).check_robots(url)
        sitemap = RobotsAndSitemapChecker(client).check_sitemaps([])
        links = LinkAnalysis()
        return url, meta, robots, sitemap, links

    soup = BeautifulSoup(html, "lxml")

    # Meta tag analysis
    print("Checking meta tags...")
    meta_checker = MetaTagChecker()
    meta = meta_checker.analyze(soup, url)

    # Robots.txt and sitemap analysis
    print("Checking robots.txt and sitemaps...")
    robots_checker = RobotsAndSitemapChecker(client)
    robots = robots_checker.check_robots(url)

    sitemap_urls = robots.sitemap_urls if robots.exists else []
    if not sitemap_urls:
        # Fallback to default sitemap.xml if none found in robots.txt
        sitemap_urls = [url.rstrip("/") + "/sitemap.xml"]

    sitemap = robots_checker.check_sitemaps(sitemap_urls)

    # Collect all sitemap URLs for orphaned page detection
    all_sitemap_urls = set()
    for entry in sitemap.all_entries:
        all_sitemap_urls.add(entry.loc)

    # Link analysis
    print("Analyzing links...")
    link_checker = LinkChecker(client)
    links = link_checker.analyze_links(soup, url, all_sitemap_urls)

    if check_links:
        print(f"Checking HTTP status of up to {max_link_checks} internal links...")
        broken = link_checker.check_link_status(links.internal_links, max_link_checks)
        links.broken_links = broken

    return url, meta, robots, sitemap, links


def main():
    """Main entry point."""
    args = parse_args()

    url, meta, robots, sitemap, links = analyze_website(
        args.url,
        check_links=args.check_links,
        max_link_checks=args.max_link_checks,
        timeout=args.timeout,
    )

    reporter = ReportGenerator()

    # Automatically save a markdown report to the results folder
    domain = urlparse(url).netloc.replace("www.", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create results dir in the seo_checker directory
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
    os.makedirs(results_dir, exist_ok=True)

    auto_report_path = os.path.join(results_dir, f"{domain}_{timestamp}.md")
    with open(auto_report_path, "w") as f:
        f.write(reporter.generate_markdown_report(url, meta, robots, sitemap, links))

    auto_json_path = os.path.join(results_dir, f"{domain}_{timestamp}.json")
    with open(auto_json_path, "w") as f:
        f.write(reporter.generate_json_report(url, meta, robots, sitemap, links))

    print(f"\n[+] Full reports automatically saved for review:\n    - {auto_report_path}\n    - {auto_json_path}\n")

    if args.format == "console":
        reporter.print_console_report(url, meta, robots, sitemap, links)
    elif args.format == "markdown":
        report = reporter.generate_markdown_report(url, meta, robots, sitemap, links)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    elif args.format == "json":
        report = reporter.generate_json_report(url, meta, robots, sitemap, links)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
