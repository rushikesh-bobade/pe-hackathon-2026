"""
Unit tests for the URL Shortener application.
Tests individual functions in isolation (no DB, no HTTP).
"""

import pytest

from app.models.url import generate_short_code
from app.routes.shortener import is_valid_url


# ─── Tests for generate_short_code ──────────────────────────────────────────

class TestGenerateShortCode:
    """Unit tests for the generate_short_code function."""

    def test_default_length_is_six(self):
        code = generate_short_code()
        assert len(code) == 6

    def test_custom_length(self):
        code = generate_short_code(length=10)
        assert len(code) == 10

    def test_returns_alphanumeric_only(self):
        for _ in range(20):
            code = generate_short_code()
            assert code.isalnum(), f"Expected alphanumeric, got: {code}"

    def test_returns_string(self):
        code = generate_short_code()
        assert isinstance(code, str)

    def test_codes_are_random(self):
        """Generate 100 codes — they should not all be identical."""
        codes = {generate_short_code() for _ in range(100)}
        assert len(codes) > 1, "Short codes should not all be the same"

    def test_length_one(self):
        code = generate_short_code(length=1)
        assert len(code) == 1

    def test_length_twenty(self):
        code = generate_short_code(length=20)
        assert len(code) == 20


# ─── Tests for is_valid_url ──────────────────────────────────────────────────

class TestIsValidUrl:
    """Unit tests for the URL validation helper."""

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_http_url(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_url_with_path(self):
        assert is_valid_url("https://example.com/some/path?q=1") is True

    def test_valid_url_with_subdomain(self):
        assert is_valid_url("https://www.google.com") is True

    def test_valid_url_with_port(self):
        assert is_valid_url("http://localhost:5000") is True

    def test_invalid_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_ftp_scheme(self):
        assert is_valid_url("ftp://example.com") is False

    def test_invalid_empty_string(self):
        assert is_valid_url("") is False

    def test_invalid_just_scheme(self):
        assert is_valid_url("https://") is False

    def test_invalid_random_string(self):
        assert is_valid_url("not-a-url-at-all") is False

    def test_invalid_none_like_string(self):
        assert is_valid_url("null") is False

    def test_valid_url_with_fragment(self):
        assert is_valid_url("https://example.com/page#section") is True

    def test_valid_long_url(self):
        long_url = "https://example.com/" + "a" * 2000
        assert is_valid_url(long_url) is True

    def test_invalid_spaces(self):
        assert is_valid_url("https://exam ple.com") is False
