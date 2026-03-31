"""Tests for robots.txt and sitemap checker."""

from unittest.mock import MagicMock
from seo_checker.robots_sitemap_checker import (
    RobotsAndSitemapChecker,
    SitemapAnalysis,
)


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


class TestCheckRobots:
    def test_missing_robots_txt(self):
        client = MagicMock()
        client.fetch.side_effect = Exception("404 Client Error: Not Found")
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert result.exists is False
        assert any(i["severity"] == "HIGH" for i in result.issues)

    def test_valid_robots_txt(self):
        client = MagicMock()
        client.fetch.return_value = _mock_response(
            "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml"
        )
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert result.exists is True
        assert "https://example.com/sitemap.xml" in result.sitemap_urls

    def test_crawl_delay_warning(self):
        client = MagicMock()
        client.fetch.return_value = _mock_response(
            "User-agent: *\nDisallow: /admin/\nCrawl-delay: 10"
        )
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert result.crawl_delay == 10
        assert any(
            i["severity"] == "MEDIUM" and "Crawl-delay" in i["issue"]
            for i in result.issues
        )

    def test_no_sitemap_declaration(self):
        client = MagicMock()
        client.fetch.return_value = _mock_response("User-agent: *\nDisallow: /admin/")
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert any(
            i["severity"] == "MEDIUM" and "No sitemap" in i["issue"]
            for i in result.issues
        )

    def test_disallowed_paths(self):
        client = MagicMock()
        client.fetch.return_value = _mock_response(
            "User-agent: *\nDisallow: /admin/\nDisallow: /private/"
        )
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert "/admin/" in result.disallowed_paths
        assert "/private/" in result.disallowed_paths

    def test_blocked_robots_txt(self):
        client = MagicMock()
        client.fetch.side_effect = Exception("403 Client Error: Forbidden")
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_robots("https://example.com")
        assert result.exists is False
        assert any("blocked" in i["issue"] for i in result.issues)


class TestCheckSitemaps:
    def test_no_sitemap_urls(self):
        client = MagicMock()
        checker = RobotsAndSitemapChecker(client)
        result = checker.check_sitemaps([])
        assert result.exists is False
        assert any(i["severity"] == "HIGH" for i in result.issues)

    def test_parse_sitemap_index(self):
        client = MagicMock()
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap><loc>https://example.com/sitemap1.xml</loc></sitemap>
            <sitemap><loc>https://example.com/sitemap2.xml</loc></sitemap>
        </sitemapindex>"""
        checker = RobotsAndSitemapChecker(client)
        result = SitemapAnalysis()
        checker._parse_sitemap(
            sitemap_xml, "https://example.com/sitemap_index.xml", result
        )
        assert "https://example.com/sitemap1.xml" in result.sitemap_urls
        assert "https://example.com/sitemap2.xml" in result.sitemap_urls

    def test_parse_url_sitemap(self):
        client = MagicMock()
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2026-01-01</lastmod>
            </url>
            <url>
                <loc>https://example.com/page2</loc>
                <lastmod>2025-06-15</lastmod>
            </url>
        </urlset>"""
        checker = RobotsAndSitemapChecker(client)
        result = SitemapAnalysis()
        checker._parse_sitemap(sitemap_xml, "https://example.com/sitemap.xml", result)
        assert len(result.all_entries) == 2
        assert result.all_entries[0].loc == "https://example.com/page1"
        assert result.all_entries[0].lastmod == "2026-01-01"

    def test_outdated_sitemap_warning(self):
        client = MagicMock()
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/old</loc>
                <lastmod>2022-01-01</lastmod>
            </url>
        </urlset>"""
        checker = RobotsAndSitemapChecker(client)
        result = SitemapAnalysis()
        checker._parse_sitemap(sitemap_xml, "https://example.com/sitemap.xml", result)
        checker._analyze_sitemap_issues(result)
        assert any(
            i["severity"] == "HIGH" and "outdated" in i["issue"] for i in result.issues
        )

    def test_invalid_xml(self):
        client = MagicMock()
        checker = RobotsAndSitemapChecker(client)
        result = SitemapAnalysis()
        checker._parse_sitemap(
            "not valid xml", "https://example.com/sitemap.xml", result
        )
        assert any(
            i["severity"] == "HIGH" and "Invalid XML" in i["issue"]
            for i in result.issues
        )
