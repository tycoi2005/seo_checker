"""Tests for HTTP client."""

from unittest.mock import MagicMock, patch
from seo_checker.http_client import HttpClient


class TestNormalizeUrl:
    def test_adds_https(self):
        assert HttpClient.normalize_url("example.com") == "https://example.com"

    def test_keeps_existing_scheme(self):
        assert HttpClient.normalize_url("http://example.com") == "http://example.com"

    def test_strips_trailing_slash(self):
        assert HttpClient.normalize_url("https://example.com/") == "https://example.com"


class TestGetBaseUrl:
    def test_extracts_base(self):
        assert (
            HttpClient.get_base_url("https://example.com/page?a=1")
            == "https://example.com"
        )

    def test_with_port(self):
        assert (
            HttpClient.get_base_url("https://example.com:8080/path")
            == "https://example.com:8080"
        )


class TestCheckUrlExists:
    def test_existing_url(self):
        client = HttpClient()
        with patch.object(client.session, "head") as mock_head:
            mock_head.return_value = MagicMock(status_code=200)
            exists, status = client.check_url_exists("https://example.com")
            assert exists is True
            assert status == 200

    def test_nonexistent_url(self):
        client = HttpClient()
        with patch.object(client.session, "head") as mock_head:
            mock_head.return_value = MagicMock(status_code=404)
            exists, status = client.check_url_exists("https://example.com/missing")
            assert exists is False
            assert status == 404

    def test_fallback_to_get_on_405(self):
        client = HttpClient()
        with (
            patch.object(client.session, "head") as mock_head,
            patch.object(client.session, "get") as mock_get,
        ):
            mock_head.return_value = MagicMock(status_code=405)
            mock_get.return_value = MagicMock(status_code=200)
            exists, status = client.check_url_exists("https://example.com")
            assert exists is True
            assert mock_get.called

    def test_exception_returns_false(self):
        client = HttpClient()
        with patch.object(client.session, "head") as mock_head:
            import requests

            mock_head.side_effect = requests.RequestException("Connection error")
            exists, status = client.check_url_exists("https://example.com")
            assert exists is False
            assert status == 0
