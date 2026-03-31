"""Report generation module for SEO analysis results."""

import json
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from seo_checker.meta_checker import MetaTagAnalysis, MetaTagIssue
from seo_checker.robots_sitemap_checker import RobotsAnalysis, SitemapAnalysis
from seo_checker.link_checker import LinkAnalysis


def _normalize_issue(issue) -> dict:
    """Convert MetaTagIssue objects or dicts to a uniform dict."""
    if isinstance(issue, MetaTagIssue):
        return {
            "severity": issue.severity,
            "issue": issue.issue,
            "recommendation": issue.recommendation,
        }
    return issue


class ReportGenerator:
    """Generates formatted reports from SEO analysis results."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def print_console_report(
        self,
        url: str,
        meta: MetaTagAnalysis,
        robots: RobotsAnalysis,
        sitemap: SitemapAnalysis,
        links: LinkAnalysis,
    ):
        """Print a comprehensive console report."""
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold cyan]SEO Audit Report[/bold cyan]\n[dim]{url} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
                border_style="cyan",
            )
        )
        self.console.print()

        self._print_meta_section(meta)
        self._print_robots_section(robots)
        self._print_sitemap_section(sitemap)
        self._print_links_section(links)
        self._print_summary(meta, robots, sitemap, links)

    def _print_meta_section(self, meta: MetaTagAnalysis):
        """Print meta tag analysis section."""
        self.console.print(
            Panel("[bold blue]Meta Tags Analysis[/bold blue]", border_style="blue")
        )

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Title", meta.title or "[red]Missing[/red]")
        table.add_row("Title Length", str(len(meta.title) if meta.title else 0))
        table.add_row(
            "Meta Description",
            (meta.meta_description[:80] + "...")
            if meta.meta_description
            else "[red]Missing[/red]",
        )
        table.add_row("Description Length", str(meta.meta_description_length))
        table.add_row("Canonical", meta.canonical or "[red]Missing[/red]")
        table.add_row(
            "Viewport",
            "[green]Present[/green]" if meta.viewport else "[red]Missing[/red]",
        )
        table.add_row("Charset", meta.charset or "[red]Missing[/red]")
        table.add_row("Language", meta.lang or "[red]Missing[/red]")
        table.add_row("Robots Meta", meta.robots or "[dim]Not set[/dim]")
        table.add_row("Open Graph Tags", f"{len(meta.og_tags)} tags found")
        table.add_row("Twitter Cards", f"{len(meta.twitter_cards)} tags found")
        table.add_row("Structured Data", f"{len(meta.structured_data)} blocks found")
        table.add_row(
            "Favicon",
            "[green]Present[/green]" if meta.favicon else "[red]Missing[/red]",
        )

        self.console.print(table)

        if meta.og_tags:
            self.console.print("\n[dim]Open Graph tags present:[/dim]")
            for tag, value in meta.og_tags.items():
                self.console.print(f"  [green]✓[/green] {tag}")

        if meta.twitter_cards:
            self.console.print("\n[dim]Twitter Card tags present:[/dim]")
            for tag, value in meta.twitter_cards.items():
                self.console.print(f"  [green]✓[/green] {tag}")

        self.console.print()

    def _print_robots_section(self, robots: RobotsAnalysis):
        """Print robots.txt analysis section."""
        self.console.print(
            Panel("[bold blue]Robots.txt Analysis[/bold blue]", border_style="blue")
        )

        if robots.exists:
            self.console.print("[green]✓[/green] robots.txt found")

            if robots.disallowed_paths:
                self.console.print(
                    f"\n[dim]Disallowed paths ({len(robots.disallowed_paths)}):[/dim]"
                )
                for path in robots.disallowed_paths:
                    self.console.print(f"  [yellow]✗[/yellow] {path}")

            if robots.sitemap_urls:
                self.console.print("\n[dim]Sitemap URLs declared:[/dim]")
                for url in robots.sitemap_urls:
                    self.console.print(f"  [green]✓[/green] {url}")

            if robots.crawl_delay:
                self.console.print(
                    f"\n[dim]Crawl-delay:[/dim] {robots.crawl_delay} seconds"
                )
        else:
            self.console.print("[red]✗[/red] robots.txt not found")

        self.console.print()

    def _print_sitemap_section(self, sitemap: SitemapAnalysis):
        """Print sitemap analysis section."""
        self.console.print(
            Panel("[bold blue]Sitemap Analysis[/bold blue]", border_style="blue")
        )

        if sitemap.exists:
            self.console.print("[green]✓[/green] Sitemap found")
            self.console.print(f"\n[dim]Total URLs:[/dim] {sitemap.total_urls}")

            if sitemap.oldest_lastmod:
                self.console.print(
                    f"[dim]Oldest update:[/dim] {sitemap.oldest_lastmod}"
                )
            if sitemap.newest_lastmod:
                self.console.print(
                    f"[dim]Newest update:[/dim] {sitemap.newest_lastmod}"
                )

            if sitemap.sitemap_urls:
                self.console.print(
                    f"\n[dim]Sitemap files ({len(sitemap.sitemap_urls)}):[/dim]"
                )
                for url in sitemap.sitemap_urls[:10]:
                    self.console.print(f"  • {url}")
        else:
            self.console.print("[red]✗[/red] Sitemap not found")

        self.console.print()

    def _print_links_section(self, links: LinkAnalysis):
        """Print link analysis section."""
        self.console.print(
            Panel("[bold blue]Link Analysis[/bold blue]", border_style="blue")
        )

        self.console.print(f"[dim]Total links found:[/dim] {links.total_links}")
        self.console.print(f"[dim]Internal links:[/dim] {len(links.internal_links)}")
        self.console.print(f"[dim]External links:[/dim] {len(links.external_links)}")

        if links.broken_links:
            self.console.print(
                f"\n[red]✗ Broken links ({len(links.broken_links)}):[/red]"
            )
            for link in links.broken_links[:10]:
                self.console.print(
                    f"  [red]✗[/red] {link.href} (Status: {link.status_code})"
                )

        if links.orphaned_pages:
            self.console.print(
                f"\n[yellow]⚠ Orphaned pages ({len(links.orphaned_pages)}):[/yellow]"
            )
            for page in links.orphaned_pages[:10]:
                self.console.print(f"  [yellow]⚠[/yellow] {page['path']}")

        self.console.print()

    def _print_summary(
        self,
        meta: MetaTagAnalysis,
        robots: RobotsAnalysis,
        sitemap: SitemapAnalysis,
        links: LinkAnalysis,
    ):
        """Print summary of all issues."""
        all_issues = []
        all_issues.extend([_normalize_issue(i) for i in meta.issues])
        all_issues.extend(robots.issues)
        all_issues.extend(sitemap.issues)
        all_issues.extend(links.issues)

        critical = [i for i in all_issues if i.get("severity") == "CRITICAL"]
        high = [i for i in all_issues if i.get("severity") == "HIGH"]
        medium = [i for i in all_issues if i.get("severity") == "MEDIUM"]
        low = [i for i in all_issues if i.get("severity") == "LOW"]

        self.console.print(
            Panel("[bold blue]Issues Summary[/bold blue]", border_style="blue")
        )

        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("Severity", style="bold")
        table.add_column("Count")

        if critical:
            table.add_row("[red]CRITICAL[/red]", str(len(critical)))
        if high:
            table.add_row("[yellow]HIGH[/yellow]", str(len(high)))
        if medium:
            table.add_row("[cyan]MEDIUM[/cyan]", str(len(medium)))
        if low:
            table.add_row("[dim]LOW[/dim]", str(len(low)))

        if not all_issues:
            table.add_row("[green]No issues found![/green]", "")

        self.console.print(table)

        if all_issues:
            self.console.print("\n[bold]Detailed Issues:[/bold]\n")
            for issue in sorted(
                all_issues,
                key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(
                    x.get("severity", "LOW"), 4
                ),
            ):
                severity = issue.get("severity", "LOW")
                color = {
                    "CRITICAL": "red",
                    "HIGH": "yellow",
                    "MEDIUM": "cyan",
                    "LOW": "dim",
                }.get(severity, "white")
                self.console.print(
                    f"[{color}][{severity}][/{color}] {issue.get('issue', '')}"
                )
                self.console.print(
                    f"  [dim]→ {issue.get('recommendation', '')}[/dim]\n"
                )

    def generate_markdown_report(
        self,
        url: str,
        meta: MetaTagAnalysis,
        robots: RobotsAnalysis,
        sitemap: SitemapAnalysis,
        links: LinkAnalysis,
    ) -> str:
        """Generate a markdown report."""
        all_issues = []
        all_issues.extend([_normalize_issue(i) for i in meta.issues])
        all_issues.extend(robots.issues)
        all_issues.extend(sitemap.issues)
        all_issues.extend(links.issues)

        md = []
        md.append("# SEO Audit Report")
        md.append(f"**URL:** {url}")
        md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        md.append("## Meta Tags Analysis")
        md.append(f"- **Title:** {meta.title or 'Missing'}")
        md.append(f"- **Title Length:** {len(meta.title) if meta.title else 0}")
        md.append(f"- **Meta Description:** {meta.meta_description or 'Missing'}")
        md.append(f"- **Description Length:** {meta.meta_description_length}")
        md.append(f"- **Canonical:** {meta.canonical or 'Missing'}")
        md.append(f"- **Viewport:** {'Present' if meta.viewport else 'Missing'}")
        md.append(f"- **Charset:** {meta.charset or 'Missing'}")
        md.append(f"- **Language:** {meta.lang or 'Missing'}")
        md.append(f"- **Open Graph Tags:** {len(meta.og_tags)} found")
        md.append(f"- **Twitter Cards:** {len(meta.twitter_cards)} found")
        md.append(f"- **Structured Data:** {len(meta.structured_data)} blocks")
        md.append(f"- **Favicon:** {'Present' if meta.favicon else 'Missing'}")
        md.append("")

        md.append("## Robots.txt Analysis")
        md.append(f"- **Status:** {'Found' if robots.exists else 'Not found'}")
        if robots.disallowed_paths:
            md.append(f"- **Disallowed Paths:** {len(robots.disallowed_paths)}")
        if robots.sitemap_urls:
            md.append(f"- **Sitemap URLs:** {', '.join(robots.sitemap_urls)}")
        if robots.crawl_delay:
            md.append(f"- **Crawl Delay:** {robots.crawl_delay} seconds")
        md.append("")

        md.append("## Sitemap Analysis")
        md.append(f"- **Status:** {'Found' if sitemap.exists else 'Not found'}")
        md.append(f"- **Total URLs:** {sitemap.total_urls}")
        if sitemap.oldest_lastmod:
            md.append(f"- **Oldest Update:** {sitemap.oldest_lastmod}")
        if sitemap.newest_lastmod:
            md.append(f"- **Newest Update:** {sitemap.newest_lastmod}")
        md.append("")

        md.append("## Link Analysis")
        md.append(f"- **Total Links:** {links.total_links}")
        md.append(f"- **Internal Links:** {len(links.internal_links)}")
        md.append(f"- **External Links:** {len(links.external_links)}")
        md.append(f"- **Broken Links:** {len(links.broken_links)}")
        md.append(f"- **Orphaned Pages:** {len(links.orphaned_pages)}")
        md.append("")

        md.append("## Issues Summary")
        critical = [i for i in all_issues if i.get("severity") == "CRITICAL"]
        high = [i for i in all_issues if i.get("severity") == "HIGH"]
        medium = [i for i in all_issues if i.get("severity") == "MEDIUM"]
        low = [i for i in all_issues if i.get("severity") == "LOW"]

        md.append(f"- **CRITICAL:** {len(critical)}")
        md.append(f"- **HIGH:** {len(high)}")
        md.append(f"- **MEDIUM:** {len(medium)}")
        md.append(f"- **LOW:** {len(low)}")
        md.append("")

        if all_issues:
            md.append("### Detailed Issues")
            for issue in sorted(
                all_issues,
                key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(
                    x.get("severity", "LOW"), 4
                ),
            ):
                md.append(
                    f"- **[{issue.get('severity', 'LOW')}]** {issue.get('issue', '')}"
                )
                md.append(f"  - *Recommendation:* {issue.get('recommendation', '')}")
            md.append("")

        return "\n".join(md)

    def generate_json_report(
        self,
        url: str,
        meta: MetaTagAnalysis,
        robots: RobotsAnalysis,
        sitemap: SitemapAnalysis,
        links: LinkAnalysis,
    ) -> str:
        """Generate a JSON report."""
        report = {
            "url": url,
            "date": datetime.now().isoformat(),
            "meta_tags": {
                "title": meta.title,
                "title_length": len(meta.title) if meta.title else 0,
                "meta_description": meta.meta_description,
                "description_length": meta.meta_description_length,
                "canonical": meta.canonical,
                "viewport": meta.viewport,
                "charset": meta.charset,
                "language": meta.lang,
                "og_tags": meta.og_tags,
                "twitter_cards": meta.twitter_cards,
                "structured_data_count": len(meta.structured_data),
                "favicon": meta.favicon,
                "issues": [_normalize_issue(i) for i in meta.issues],
            },
            "robots_txt": {
                "exists": robots.exists,
                "disallowed_paths": robots.disallowed_paths,
                "sitemap_urls": robots.sitemap_urls,
                "crawl_delay": robots.crawl_delay,
                "issues": robots.issues,
            },
            "sitemap": {
                "exists": sitemap.exists,
                "total_urls": sitemap.total_urls,
                "oldest_lastmod": sitemap.oldest_lastmod,
                "newest_lastmod": sitemap.newest_lastmod,
                "issues": sitemap.issues,
            },
            "links": {
                "total_links": links.total_links,
                "internal_links": len(links.internal_links),
                "external_links": len(links.external_links),
                "broken_links": len(links.broken_links),
                "orphaned_pages": len(links.orphaned_pages),
                "issues": links.issues,
            },
        }

        return json.dumps(report, indent=2)
