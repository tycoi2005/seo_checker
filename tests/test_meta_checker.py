"""Tests for meta tag checker."""

from bs4 import BeautifulSoup
from seo_checker.meta_checker import MetaTagChecker


def _make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class TestCheckTitle:
    def test_missing_title(self):
        soup = _make_soup("<html><head></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.title_count == 0
        assert any(
            i.severity == "CRITICAL" and "Missing" in i.issue for i in result.issues
        )

    def test_duplicate_title(self):
        soup = _make_soup("<html><head><title>A</title><title>B</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.title_count == 2
        assert any(
            i.severity == "CRITICAL" and "Duplicate" in i.issue for i in result.issues
        )

    def test_valid_title(self):
        soup = _make_soup(
            "<html><head><title>This is a valid title for testing</title></head></html>"
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.title == "This is a valid title for testing"
        assert result.title_count == 1
        assert not any(i.severity == "CRITICAL" for i in result.issues)

    def test_title_too_short(self):
        soup = _make_soup("<html><head><title>Hi</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "too short" in i.issue for i in result.issues
        )

    def test_title_too_long(self):
        long_title = "A" * 80
        soup = _make_soup(f"<html><head><title>{long_title}</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "too long" in i.issue for i in result.issues
        )

    def test_empty_title(self):
        soup = _make_soup("<html><head><title></title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(i.severity == "HIGH" and "Empty" in i.issue for i in result.issues)


class TestCheckMetaDescription:
    def test_missing_description(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "HIGH" and "Missing meta description" in i.issue
            for i in result.issues
        )

    def test_valid_description(self):
        desc = "A" * 150
        soup = _make_soup(
            f'<html><head><meta name="description" content="{desc}"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.meta_description == desc
        assert result.meta_description_length == 150

    def test_description_too_short(self):
        soup = _make_soup(
            '<html><head><meta name="description" content="Short"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "too short" in i.issue for i in result.issues
        )

    def test_description_too_long(self):
        desc = "A" * 200
        soup = _make_soup(
            f'<html><head><meta name="description" content="{desc}"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(i.severity == "LOW" and "too long" in i.issue for i in result.issues)


class TestCheckCanonical:
    def test_missing_canonical(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "HIGH" and "Missing canonical" in i.issue
            for i in result.issues
        )

    def test_valid_canonical(self):
        soup = _make_soup(
            '<html><head><link rel="canonical" href="https://example.com/"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.canonical == "https://example.com/"


class TestCheckViewport:
    def test_missing_viewport(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "HIGH" and "Missing viewport" in i.issue
            for i in result.issues
        )

    def test_valid_viewport(self):
        soup = _make_soup(
            '<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.viewport == "width=device-width, initial-scale=1"


class TestCheckLang:
    def test_missing_lang(self):
        soup = _make_soup("<html><head></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "Missing HTML lang" in i.issue
            for i in result.issues
        )

    def test_valid_lang(self):
        soup = _make_soup('<html lang="en-US"><head></head></html>')
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.lang == "en-US"


class TestCheckRobots:
    def test_noindex_detected(self):
        soup = _make_soup(
            '<html><head><meta name="robots" content="noindex, nofollow"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "CRITICAL" and "noindex" in i.issue for i in result.issues
        )

    def test_index_allowed(self):
        soup = _make_soup(
            '<html><head><title>Valid Title Here For Testing</title><meta name="robots" content="index, follow"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.robots == "index, follow"
        assert not any(i.severity == "CRITICAL" for i in result.issues)


class TestCheckOgTags:
    def test_missing_og_tags(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "Missing Open Graph" in i.issue
            for i in result.issues
        )

    def test_complete_og_tags(self):
        html = """
        <html lang="en"><head>
        <title>This is a complete title for testing purposes</title>
        <meta property="og:title" content="Test">
        <meta property="og:description" content="Desc">
        <meta property="og:type" content="website">
        <meta property="og:image" content="https://example.com/img.png">
        <meta property="og:image:width" content="1200">
        <meta property="og:image:height" content="630">
        <link rel="canonical" href="https://example.com/">
        <meta name="viewport" content="width=device-width">
        <meta charset="UTF-8">
        <link rel="icon" href="/favicon.ico">
        <script type="application/ld+json">{"@context":"https://schema.org"}</script>
        <meta name="twitter:card" content="summary">
        </head></html>
        """
        result = MetaTagChecker().analyze(_make_soup(html), "https://example.com")
        assert "og:title" in result.og_tags
        assert not any("Missing Open Graph" in i.issue for i in result.issues)
        assert not any("og:image dimensions" in i.issue for i in result.issues)

    def test_og_image_missing_dimensions(self):
        html = """
        <html><head>
        <meta property="og:title" content="Test">
        <meta property="og:description" content="Desc">
        <meta property="og:type" content="website">
        <meta property="og:image" content="https://example.com/img.png">
        </head></html>
        """
        result = MetaTagChecker().analyze(_make_soup(html), "https://example.com")
        assert any("og:image dimensions" in i.issue for i in result.issues)


class TestCheckTwitterCards:
    def test_missing_twitter_cards(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "LOW" and "Missing Twitter Card" in i.issue
            for i in result.issues
        )

    def test_valid_twitter_cards(self):
        html = """
        <html><head>
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:site" content="@example">
        </head></html>
        """
        result = MetaTagChecker().analyze(_make_soup(html), "https://example.com")
        assert result.twitter_cards["twitter:card"] == "summary_large_image"


class TestCheckStructuredData:
    def test_missing_structured_data(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "MEDIUM" and "structured data" in i.issue.lower()
            for i in result.issues
        )

    def test_valid_structured_data(self):
        html = """
        <html><head>
        <script type="application/ld+json">{"@context": "https://schema.org"}</script>
        </head></html>
        """
        result = MetaTagChecker().analyze(_make_soup(html), "https://example.com")
        assert len(result.structured_data) == 1


class TestCheckFavicon:
    def test_missing_favicon(self):
        soup = _make_soup("<html><head><title>Test</title></head></html>")
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert any(
            i.severity == "LOW" and "Missing favicon" in i.issue for i in result.issues
        )

    def test_valid_favicon(self):
        soup = _make_soup(
            '<html><head><link rel="icon" href="/favicon.ico"></head></html>'
        )
        result = MetaTagChecker().analyze(soup, "https://example.com")
        assert result.favicon is True
