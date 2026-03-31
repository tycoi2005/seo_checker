"""Robots.txt and sitemap analysis module."""

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

import xml.etree.ElementTree as ET

from seo_checker.http_client import HttpClient


@dataclass
class RobotsAnalysis:
    """Results of robots.txt analysis."""

    exists: bool = False
    content: str = ""
    disallowed_paths: list = field(default_factory=list)
    allowed_paths: list = field(default_factory=list)
    sitemap_urls: list = field(default_factory=list)
    crawl_delay: Optional[int] = None
    issues: list = field(default_factory=list)


@dataclass
class SitemapEntry:
    """A single URL entry in a sitemap."""

    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class SitemapAnalysis:
    """Results of sitemap analysis."""

    exists: bool = False
    sitemap_urls: list = field(default_factory=list)
    all_entries: list = field(default_factory=list)
    total_urls: int = 0
    oldest_lastmod: Optional[str] = None
    newest_lastmod: Optional[str] = None
    issues: list = field(default_factory=list)


class RobotsAndSitemapChecker:
    """Analyzes robots.txt and sitemaps."""

    def __init__(self, client: HttpClient):
        self.client = client

    def check_robots(self, base_url: str) -> RobotsAnalysis:
        """Analyze robots.txt file."""
        result = RobotsAnalysis()
        robots_url = urljoin(base_url, "/robots.txt")

        try:
            result.content = self.client.fetch_text(robots_url)
            result.exists = True
        except Exception:
            result.issues.append(
                {
                    "severity": "HIGH",
                    "issue": "Missing robots.txt file",
                    "recommendation": "Create a robots.txt file to guide search engine crawlers",
                }
            )
            return result

        lines = result.content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    result.disallowed_paths.append(path)
            elif line.lower().startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    result.allowed_paths.append(path)
            elif line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                result.sitemap_urls.append(sitemap_url)
            elif line.lower().startswith("crawl-delay:"):
                try:
                    result.crawl_delay = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

        if result.crawl_delay and result.crawl_delay > 5:
            result.issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": f"Crawl-delay is set to {result.crawl_delay} seconds",
                    "recommendation": "Consider reducing crawl-delay to 1-5 seconds or removing it. Google ignores crawl-delay, but Bing respects it.",
                }
            )

        if not result.sitemap_urls:
            result.issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": "No sitemap URL declared in robots.txt",
                    "recommendation": "Add 'Sitemap: https://yoursite.com/sitemap.xml' to robots.txt",
                }
            )

        return result

    def check_sitemaps(self, sitemap_urls: list) -> SitemapAnalysis:
        """Analyze sitemap(s) for completeness and issues."""
        result = SitemapAnalysis()

        if not sitemap_urls:
            result.issues.append(
                {
                    "severity": "HIGH",
                    "issue": "No sitemap URLs to analyze",
                    "recommendation": "Ensure sitemaps are declared in robots.txt or provide them directly",
                }
            )
            return result

        result.exists = True
        result.sitemap_urls = sitemap_urls

        for sitemap_url in sitemap_urls:
            try:
                content = self.client.fetch_text(sitemap_url)
                self._parse_sitemap(content, sitemap_url, result)
            except Exception as e:
                result.issues.append(
                    {
                        "severity": "HIGH",
                        "issue": f"Failed to fetch sitemap: {sitemap_url}",
                        "recommendation": f"Ensure the sitemap is accessible. Error: {str(e)}",
                    }
                )

        self._analyze_sitemap_issues(result)
        return result

    def _parse_sitemap(self, content: str, url: str, result: SitemapAnalysis):
        """Parse sitemap XML content."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            result.issues.append(
                {
                    "severity": "HIGH",
                    "issue": f"Invalid XML in sitemap: {url}",
                    "recommendation": "Fix XML syntax errors in the sitemap",
                }
            )
            return

        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        if root.tag.endswith("sitemapindex"):
            for sitemap in root.findall("ns:sitemap", namespace):
                loc = sitemap.find("ns:loc", namespace)
                if loc is not None and loc.text:
                    result.sitemap_urls.append(loc.text)
        else:
            for url_elem in root.findall("ns:url", namespace):
                entry = SitemapEntry(loc="")
                loc = url_elem.find("ns:loc", namespace)
                if loc is not None and loc.text:
                    entry.loc = loc.text.strip()

                lastmod = url_elem.find("ns:lastmod", namespace)
                if lastmod is not None and lastmod.text:
                    entry.lastmod = lastmod.text.strip()

                changefreq = url_elem.find("ns:changefreq", namespace)
                if changefreq is not None and changefreq.text:
                    entry.changefreq = changefreq.text.strip()

                priority = url_elem.find("ns:priority", namespace)
                if priority is not None and priority.text:
                    entry.priority = priority.text.strip()

                if entry.loc:
                    result.all_entries.append(entry)

    def _analyze_sitemap_issues(self, result: SitemapAnalysis):
        """Analyze sitemap for common issues."""
        if not result.all_entries:
            result.issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": "No URL entries found in sitemap",
                    "recommendation": "Ensure your sitemap contains URLs to your important pages",
                }
            )
            return

        result.total_urls = len(result.all_entries)

        lastmods = [e.lastmod for e in result.all_entries if e.lastmod]
        if lastmods:
            result.oldest_lastmod = min(lastmods)
            result.newest_lastmod = max(lastmods)

            if result.oldest_lastmod and result.oldest_lastmod < "2024":
                result.issues.append(
                    {
                        "severity": "HIGH",
                        "issue": f"Sitemap contains outdated entries (oldest: {result.oldest_lastmod})",
                        "recommendation": "Regenerate your sitemap to ensure all URLs are current",
                    }
                )

        if result.total_urls > 50000:
            result.issues.append(
                {
                    "severity": "MEDIUM",
                    "issue": f"Sitemap has {result.total_urls} URLs (limit is 50,000)",
                    "recommendation": "Split into multiple sitemaps and use a sitemap index file",
                }
            )
