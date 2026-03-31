"""Tests for report generator."""

import json
from seo_checker.meta_checker import MetaTagAnalysis, MetaTagIssue
from seo_checker.robots_sitemap_checker import RobotsAnalysis, SitemapAnalysis
from seo_checker.link_checker import LinkAnalysis
from seo_checker.report_generator import ReportGenerator, _normalize_issue


class TestNormalizeIssue:
    def test_converts_dataclass_to_dict(self):
        issue = MetaTagIssue(
            severity="HIGH", issue="Test issue", recommendation="Fix it"
        )
        result = _normalize_issue(issue)
        assert result == {
            "severity": "HIGH",
            "issue": "Test issue",
            "recommendation": "Fix it",
        }

    def test_passes_through_dict(self):
        issue = {
            "severity": "LOW",
            "issue": "Dict issue",
            "recommendation": "Do something",
        }
        result = _normalize_issue(issue)
        assert result == issue


class TestGenerateMarkdownReport:
    def test_contains_all_sections(self):
        reporter = ReportGenerator()
        meta = MetaTagAnalysis(
            title="Test",
            meta_description="Desc",
            canonical="https://example.com/",
            viewport="width=device-width",
            charset="UTF-8",
            lang="en",
            og_tags={"og:title": "Test"},
            twitter_cards={"twitter:card": "summary"},
            structured_data=["{}"],
            favicon=True,
        )
        robots = RobotsAnalysis(exists=True)
        sitemap = SitemapAnalysis(exists=True, total_urls=10)
        links = LinkAnalysis(total_links=5)

        md = reporter.generate_markdown_report(
            "https://example.com", meta, robots, sitemap, links
        )
        assert "# SEO Audit Report" in md
        assert "## Meta Tags Analysis" in md
        assert "## Robots.txt Analysis" in md
        assert "## Sitemap Analysis" in md
        assert "## Link Analysis" in md
        assert "## Issues Summary" in md


class TestGenerateJsonReport:
    def test_valid_json(self):
        reporter = ReportGenerator()
        meta = MetaTagAnalysis(title="Test")
        robots = RobotsAnalysis(exists=True)
        sitemap = SitemapAnalysis(exists=True, total_urls=5)
        links = LinkAnalysis(total_links=3)

        json_str = reporter.generate_json_report(
            "https://example.com", meta, robots, sitemap, links
        )
        data = json.loads(json_str)
        assert data["url"] == "https://example.com"
        assert "meta_tags" in data
        assert "robots_txt" in data
        assert "sitemap" in data
        assert "links" in data

    def test_meta_issues_serialized(self):
        reporter = ReportGenerator()
        meta = MetaTagAnalysis()
        meta.issues.append(
            MetaTagIssue(
                severity="CRITICAL", issue="Missing title", recommendation="Add title"
            )
        )
        robots = RobotsAnalysis(exists=True)
        sitemap = SitemapAnalysis(exists=True)
        links = LinkAnalysis()

        json_str = reporter.generate_json_report(
            "https://example.com", meta, robots, sitemap, links
        )
        data = json.loads(json_str)
        assert len(data["meta_tags"]["issues"]) == 1
        assert data["meta_tags"]["issues"][0]["severity"] == "CRITICAL"
