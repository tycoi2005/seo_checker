"""Link analysis module for finding broken and orphaned links."""

try:
    from seo_checker.http_client import HttpClient
except ModuleNotFoundError:
    from http_client import HttpClient

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class LinkInfo:
    """Information about a single link."""

    href: str
    text: str
    source_url: str
    is_internal: bool = False
    status_code: int = 0
    is_broken: bool = False
    link_type: str = "internal"


@dataclass
class LinkAnalysis:
    """Results of link analysis."""

    total_links: int = 0
    internal_links: list = field(default_factory=list)
    external_links: list = field(default_factory=list)
    broken_links: list = field(default_factory=list)
    orphaned_pages: list = field(default_factory=list)
    url_mismatches: list = field(default_factory=list)
    issues: list = field(default_factory=list)


class LinkChecker:
    """Analyzes links for broken URLs and orphaned pages."""

    def __init__(self, client: HttpClient):
        self.client = client

    def analyze_links(
        self, soup: BeautifulSoup, url: str, sitemap_urls: set = None
    ) -> LinkAnalysis:
        """Analyze all links on a page."""
        result = LinkAnalysis()
        parsed_base = urlparse(url)

        links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href", "").strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urljoin(url, href)
            parsed_link = urlparse(full_url)

            is_internal = parsed_link.netloc == parsed_base.netloc
            link_text = link.get_text(strip=True)

            link_info = LinkInfo(
                href=href,
                text=link_text,
                source_url=url,
                is_internal=is_internal,
            )

            if is_internal:
                result.internal_links.append(link_info)
                result.url_mismatches.append(
                    {
                        "link": href,
                        "full_url": full_url,
                        "text": link_text,
                    }
                )
            else:
                result.external_links.append(link_info)

        result.total_links = len(result.internal_links) + len(result.external_links)

        if sitemap_urls:
            self._find_orphaned_pages(sitemap_urls, result.internal_links, result)

        return result

    def check_link_status(self, links: list, max_checks: int = 50) -> list:
        """Check HTTP status codes for internal links."""
        broken = []
        checked = 0

        for link in links:
            if checked >= max_checks:
                break

            full_url = (
                link.href
                if link.href.startswith("http")
                else link.source_url.rsplit("/", 1)[0] + "/" + link.href
            )

            try:
                exists, status_code = self.client.check_url_exists(full_url)
                link.status_code = status_code

                if not exists:
                    link.is_broken = True
                    broken.append(link)
            except Exception:
                pass

            checked += 1

        return broken

    def _find_orphaned_pages(
        self, sitemap_urls: set, internal_links: list, result: LinkAnalysis
    ):
        """Find pages in sitemap that have no internal links pointing to them."""
        linked_paths = set()
        for link in internal_links:
            full_url = (
                link.href
                if link.href.startswith("http")
                else urljoin(link.source_url, link.href)
            )
            parsed = urlparse(full_url)
            linked_paths.add(parsed.path.rstrip("/"))

        for sitemap_url in sitemap_urls:
            parsed = urlparse(sitemap_url)
            path = parsed.path.rstrip("/")

            if path and path not in linked_paths and path != "/":
                result.orphaned_pages.append(
                    {
                        "url": sitemap_url,
                        "path": path,
                        "recommendation": f"Add internal links to {path} from your navigation or content",
                    }
                )

        if result.orphaned_pages:
            result.issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": f"Found {len(result.orphaned_pages)} orphaned pages",
                    "recommendation": "Add internal links to orphaned pages to improve crawlability",
                }
            )
