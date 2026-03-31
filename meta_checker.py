"""Meta tag analysis module for SEO checking."""

from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class MetaTagIssue:
    """Represents a meta tag issue found during analysis."""

    severity: str
    issue: str
    recommendation: str


@dataclass
class MetaTagAnalysis:
    """Results of meta tag analysis."""

    title: Optional[str] = None
    title_count: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    canonical: Optional[str] = None
    viewport: Optional[str] = None
    charset: Optional[str] = None
    robots: Optional[str] = None
    lang: Optional[str] = None
    og_tags: dict = field(default_factory=dict)
    twitter_cards: dict = field(default_factory=dict)
    structured_data: list = field(default_factory=list)
    favicon: bool = False
    issues: list = field(default_factory=list)


class MetaTagChecker:
    """Analyzes meta tags for SEO best practices."""

    MIN_TITLE_LENGTH = 30
    MAX_TITLE_LENGTH = 60
    MIN_DESC_LENGTH = 120
    MAX_DESC_LENGTH = 160

    def analyze(self, soup: BeautifulSoup, url: str) -> MetaTagAnalysis:
        """Analyze all meta tags in the HTML."""
        result = MetaTagAnalysis()

        self._check_title(soup, result)
        self._check_meta_description(soup, result)
        self._check_canonical(soup, result)
        self._check_viewport(soup, result)
        self._check_charset(soup, result)
        self._check_robots(soup, result)
        self._check_lang(soup, result)
        self._check_og_tags(soup, result)
        self._check_twitter_cards(soup, result)
        self._check_structured_data(soup, result)
        self._check_favicon(soup, result)

        return result

    def _check_title(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check title tag presence and quality."""
        titles = soup.find_all("title")
        result.title_count = len(titles)

        if result.title_count == 0:
            result.issues.append(
                MetaTagIssue(
                    severity="CRITICAL",
                    issue="Missing <title> tag",
                    recommendation="Add a unique, descriptive <title> tag (30-60 characters)",
                )
            )
        elif result.title_count > 1:
            result.issues.append(
                MetaTagIssue(
                    severity="CRITICAL",
                    issue=f"Duplicate <title> tags found ({result.title_count} instances)",
                    recommendation="Ensure only one <title> tag exists in the <head> section",
                )
            )
        else:
            result.title = titles[0].get_text(strip=True)
            title_len = len(result.title)

            if title_len == 0:
                result.issues.append(
                    MetaTagIssue(
                        severity="HIGH",
                        issue="Empty <title> tag",
                        recommendation="Add meaningful content to the <title> tag",
                    )
                )
            elif title_len < self.MIN_TITLE_LENGTH:
                result.issues.append(
                    MetaTagIssue(
                        severity="MEDIUM",
                        issue=f"Title too short ({title_len} chars)",
                        recommendation=f"Increase title length to {self.MIN_TITLE_LENGTH}-{self.MAX_TITLE_LENGTH} characters",
                    )
                )
            elif title_len > self.MAX_TITLE_LENGTH:
                result.issues.append(
                    MetaTagIssue(
                        severity="MEDIUM",
                        issue=f"Title too long ({title_len} chars)",
                        recommendation=f"Reduce title length to {self.MIN_TITLE_LENGTH}-{self.MAX_TITLE_LENGTH} characters",
                    )
                )

    def _check_meta_description(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check meta description presence and quality."""
        meta_desc = soup.find("meta", attrs={"name": "description"})

        if not meta_desc:
            meta_desc = soup.find("meta", attrs={"property": "og:description"})

        if not meta_desc or not meta_desc.get("content"):
            result.issues.append(
                MetaTagIssue(
                    severity="HIGH",
                    issue="Missing meta description",
                    recommendation="Add a unique meta description (120-160 characters)",
                )
            )
        else:
            result.meta_description = meta_desc.get("content", "")
            result.meta_description_length = len(result.meta_description)

            if result.meta_description_length < self.MIN_DESC_LENGTH:
                result.issues.append(
                    MetaTagIssue(
                        severity="MEDIUM",
                        issue=f"Meta description too short ({result.meta_description_length} chars)",
                        recommendation=f"Increase to {self.MIN_DESC_LENGTH}-{self.MAX_DESC_LENGTH} characters",
                    )
                )
            elif result.meta_description_length > self.MAX_DESC_LENGTH:
                result.issues.append(
                    MetaTagIssue(
                        severity="LOW",
                        issue=f"Meta description too long ({result.meta_description_length} chars)",
                        recommendation=f"Consider reducing to {self.MIN_DESC_LENGTH}-{self.MAX_DESC_LENGTH} characters",
                    )
                )

    def _check_canonical(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check canonical URL tag."""
        canonical = soup.find("link", attrs={"rel": "canonical"})

        if not canonical:
            result.issues.append(
                MetaTagIssue(
                    severity="HIGH",
                    issue="Missing canonical URL",
                    recommendation="Add a <link rel='canonical'> tag to prevent duplicate content issues",
                )
            )
        else:
            result.canonical = canonical.get("href", "")

    def _check_viewport(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check viewport meta tag for mobile-friendliness."""
        viewport = soup.find("meta", attrs={"name": "viewport"})

        if not viewport:
            result.issues.append(
                MetaTagIssue(
                    severity="HIGH",
                    issue="Missing viewport meta tag",
                    recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
                )
            )
        else:
            result.viewport = viewport.get("content", "")

    def _check_charset(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check charset declaration."""
        charset = soup.find("meta", attrs={"charset": True})
        if charset:
            result.charset = charset.get("charset", "")
        else:
            charset = soup.find("meta", attrs={"http-equiv": "Content-Type"})
            if charset:
                result.charset = charset.get("content", "")

        if not result.charset:
            result.issues.append(
                MetaTagIssue(
                    severity="MEDIUM",
                    issue="Missing charset declaration",
                    recommendation="Add <meta charset='UTF-8'> as the first element in <head>",
                )
            )

    def _check_robots(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check robots meta tag."""
        robots = soup.find("meta", attrs={"name": "robots"})
        if robots:
            result.robots = robots.get("content", "")
            if "noindex" in result.robots.lower():
                result.issues.append(
                    MetaTagIssue(
                        severity="CRITICAL",
                        issue="Page set to 'noindex'",
                        recommendation="Remove 'noindex' from robots meta tag if you want this page indexed",
                    )
                )

    def _check_lang(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check HTML lang attribute."""
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            result.lang = html_tag.get("lang")
        else:
            result.issues.append(
                MetaTagIssue(
                    severity="MEDIUM",
                    issue="Missing HTML lang attribute",
                    recommendation="Add lang attribute to <html> tag (e.g., <html lang='en-US'>)",
                )
            )

    def _check_og_tags(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check Open Graph tags."""
        og_properties = [
            "og:title",
            "og:description",
            "og:url",
            "og:type",
            "og:image",
            "og:site_name",
            "og:locale",
        ]

        for prop in og_properties:
            tag = soup.find("meta", attrs={"property": prop})
            if tag:
                result.og_tags[prop] = tag.get("content", "")

        missing_og = []
        for prop in ["og:title", "og:description", "og:type", "og:image"]:
            if prop not in result.og_tags:
                missing_og.append(prop)

        if missing_og:
            result.issues.append(
                MetaTagIssue(
                    severity="MEDIUM",
                    issue=f"Missing Open Graph tags: {', '.join(missing_og)}",
                    recommendation="Add missing OG tags for better social media sharing",
                )
            )

        if "og:image" in result.og_tags:
            width_tag = soup.find("meta", attrs={"property": "og:image:width"})
            height_tag = soup.find("meta", attrs={"property": "og:image:height"})
            if not width_tag or not height_tag:
                result.issues.append(
                    MetaTagIssue(
                        severity="LOW",
                        issue="Missing og:image dimensions",
                        recommendation="Add og:image:width and og:image:height meta tags",
                    )
                )

    def _check_twitter_cards(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check Twitter Card meta tags."""
        twitter_tags = [
            "twitter:card",
            "twitter:title",
            "twitter:description",
            "twitter:site",
        ]

        for tag_name in twitter_tags:
            tag = soup.find("meta", attrs={"name": tag_name})
            if tag:
                result.twitter_cards[tag_name] = tag.get("content", "")

        if not result.twitter_cards:
            result.issues.append(
                MetaTagIssue(
                    severity="LOW",
                    issue="Missing Twitter Card meta tags",
                    recommendation="Add Twitter Card meta tags for better sharing on X/Twitter",
                )
            )

    def _check_structured_data(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check for JSON-LD structured data."""
        scripts = soup.find_all("script", type="application/ld+json")
        result.structured_data = [
            s.get_text(strip=True) for s in scripts if s.get_text(strip=True)
        ]

        if not result.structured_data:
            result.issues.append(
                MetaTagIssue(
                    severity="MEDIUM",
                    issue="No structured data (JSON-LD) found",
                    recommendation="Add JSON-LD structured data to help search engines understand your content",
                )
            )

    def _check_favicon(self, soup: BeautifulSoup, result: MetaTagAnalysis):
        """Check for favicon declaration."""
        favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        result.favicon = favicon is not None

        if not result.favicon:
            result.issues.append(
                MetaTagIssue(
                    severity="LOW",
                    issue="Missing favicon",
                    recommendation="Add a favicon with <link rel='icon' href='/favicon.ico'>",
                )
            )
