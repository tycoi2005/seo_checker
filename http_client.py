"""HTTP client utilities for fetching web pages."""

import requests
from urllib.parse import urlparse


class HttpClient:
    """Handles HTTP requests with proper error handling and headers."""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; SEO-Checker/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.timeout = timeout

    def fetch(self, url: str) -> requests.Response:
        """Fetch a URL and return the response."""
        response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        response.raise_for_status()
        return response

    def fetch_text(self, url: str) -> str:
        """Fetch a URL and return the text content."""
        response = self.fetch(url)
        return response.text

    def check_url_exists(self, url: str) -> tuple[bool, int]:
        """Check if a URL exists and return (exists, status_code)."""
        try:
            response = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )
            if response.status_code == 405:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
            return response.status_code < 400, response.status_code
        except requests.RequestException:
            return False, 0

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a URL by ensuring it has a scheme."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url.rstrip("/")

    @staticmethod
    def get_base_url(url: str) -> str:
        """Extract the base URL (scheme + netloc) from a full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
