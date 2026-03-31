"""Tests for link checker."""

from bs4 import BeautifulSoup
from unittest.mock import MagicMock
from seo_checker.link_checker import LinkChecker, LinkInfo


def _make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestAnalyzeLinks:
    def test_internal_links(self):
        html = """<html><body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </body></html>"""
        soup = _make_soup(html)
        checker = LinkChecker(MagicMock())
        result = checker.analyze_links(soup, "https://example.com/")
        assert len(result.internal_links) == 2
        assert result.total_links == 2

    def test_external_links(self):
        html = """<html><body>
            <a href="https://other.com/page">External</a>
        </body></html>"""
        soup = _make_soup(html)
        checker = LinkChecker(MagicMock())
        result = checker.analyze_links(soup, "https://example.com/")
        assert len(result.external_links) == 1
        assert result.internal_links == []

    def test_skip_special_links(self):
        html = """<html><body>
            <a href="#section">Anchor</a>
            <a href="javascript:void(0)">JS</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="tel:+1234567890">Phone</a>
            <a href="/valid">Valid</a>
        </body></html>"""
        soup = _make_soup(html)
        checker = LinkChecker(MagicMock())
        result = checker.analyze_links(soup, "https://example.com/")
        assert result.total_links == 1

    def test_orphaned_pages(self):
        sitemap_urls = {
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/orphaned-page",
        }
        html = """<html><body>
            <a href="/about">About</a>
        </body></html>"""
        soup = _make_soup(html)
        checker = LinkChecker(MagicMock())
        result = checker.analyze_links(soup, "https://example.com/", sitemap_urls)
        assert any("orphaned-page" in p["path"] for p in result.orphaned_pages)

    def test_no_orphaned_pages(self):
        sitemap_urls = {
            "https://example.com/",
        }
        html = """<html><body>
        </body></html>"""
        soup = _make_soup(html)
        checker = LinkChecker(MagicMock())
        result = checker.analyze_links(soup, "https://example.com/", sitemap_urls)
        assert result.orphaned_pages == []


class TestCheckLinkStatus:
    def test_broken_link_detected(self):
        client = MagicMock()
        client.check_url_exists.return_value = (False, 404)
        checker = LinkChecker(client)
        link = LinkInfo(
            href="https://example.com/broken",
            text="Broken",
            source_url="https://example.com/",
        )
        broken = checker.check_link_status([link])
        assert len(broken) == 1
        assert broken[0].is_broken is True

    def test_valid_link(self):
        client = MagicMock()
        client.check_url_exists.return_value = (True, 200)
        checker = LinkChecker(client)
        link = LinkInfo(
            href="https://example.com/valid",
            text="Valid",
            source_url="https://example.com/",
        )
        broken = checker.check_link_status([link])
        assert len(broken) == 0

    def test_max_checks_limit(self):
        client = MagicMock()
        client.check_url_exists.return_value = (False, 404)
        checker = LinkChecker(client)
        links = [
            LinkInfo(
                href=f"https://example.com/page{i}",
                text=f"Page {i}",
                source_url="https://example.com/",
            )
            for i in range(10)
        ]
        checker.check_link_status(links, max_checks=3)
        assert client.check_url_exists.call_count == 3
