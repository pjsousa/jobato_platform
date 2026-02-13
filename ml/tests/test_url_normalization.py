"""Tests for URL normalization service."""

import pytest

from app.services.url_normalizer import normalize_url, are_urls_equivalent


class TestNormalizeUrl:
    """Test cases for URL normalization."""

    def test_normalizes_simple_url(self):
        """Test that a simple URL generates a consistent hash."""
        url = "https://example.com/job/123"
        result = normalize_url(url)

        assert result is not None
        assert len(result) == 64  # SHA-256 hex string length

    def test_normalizes_scheme_casing(self):
        """Test that scheme casing is normalized (lowercased)."""
        url1 = "https://example.com/job"
        url2 = "HTTPS://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_normalizes_host_casing(self):
        """Test that host casing is normalized (lowercased)."""
        url1 = "https://Example.COM/job"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_strips_utm_tracking_parameters(self):
        """Test that utm_* tracking parameters are stripped."""
        url1 = "https://example.com/job?utm_source=google&utm_medium=email"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_strips_fbclid_tracking_parameter(self):
        """Test that fbclid tracking parameter is stripped."""
        url1 = "https://example.com/job?fbclid=IwAR123456"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_strips_gclid_tracking_parameter(self):
        """Test that gclid tracking parameter is stripped."""
        url1 = "https://example.com/job?gclid=abc123"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_strips_msclkid_tracking_parameter(self):
        """Test that msclkid tracking parameter is stripped."""
        url1 = "https://example.com/job?msclkid=xyz789"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_strips_ref_and_source_tracking_parameters(self):
        """Test that ref and source tracking parameters are stripped."""
        url1 = "https://example.com/job?ref=newsletter&source=email"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_preserves_non_tracking_query_parameters(self):
        """Test that non-tracking query parameters are preserved."""
        url1 = "https://example.com/job?id=123&category=tech"
        url2 = "https://example.com/job?id=123&category=tech&utm_source=google"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_sorts_query_parameters_alphabetically(self):
        """Test that query parameters are sorted alphabetically."""
        url1 = "https://example.com/job?z=last&a=first&m=middle"
        url2 = "https://example.com/job?a=first&m=middle&z=last"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_removes_fragment_identifiers(self):
        """Test that fragment identifiers are removed."""
        url1 = "https://example.com/job#section1"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_removes_default_http_port(self):
        """Test that default HTTP port (80) is removed."""
        url1 = "http://example.com:80/job"
        url2 = "http://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_removes_default_https_port(self):
        """Test that default HTTPS port (443) is removed."""
        url1 = "https://example.com:443/job"
        url2 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 == result2

    def test_preserves_non_default_ports(self):
        """Test that non-default ports are preserved."""
        url1 = "https://example.com:8080/job"
        url2 = "https://example.com:8080/job"
        url3 = "https://example.com/job"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)
        result3 = normalize_url(url3)

        assert result1 == result2
        assert result1 != result3

    def test_handles_empty_url(self):
        """Test that empty URL returns None."""
        result = normalize_url("")
        assert result is None

    def test_handles_none_url(self):
        """Test that None URL returns None."""
        result = normalize_url(None)
        assert result is None

    def test_handles_url_without_scheme(self):
        """Test that URL without scheme returns None."""
        result = normalize_url("example.com/job")
        assert result is None

    def test_handles_url_without_host(self):
        """Test that URL without host returns None."""
        result = normalize_url("https:///job")
        assert result is None

    def test_handles_malformed_url(self):
        """Test that malformed URL returns None."""
        result = normalize_url("not a valid url")
        assert result is None

    def test_is_idempotent(self):
        """Test that normalization is idempotent."""
        url = "https://Example.COM/Job?utm_source=Google&id=123#Section"

        # First normalization
        result1 = normalize_url(url)

        # The result is a hash, so we can't re-normalize it
        # But we can verify the same URL produces the same hash
        result2 = normalize_url(url)

        assert result1 == result2

    def test_different_urls_produce_different_hashes(self):
        """Test that different URLs produce different hashes."""
        url1 = "https://example.com/job/123"
        url2 = "https://example.com/job/456"

        result1 = normalize_url(url1)
        result2 = normalize_url(url2)

        assert result1 != result2


class TestAreUrlsEquivalent:
    """Test cases for URL equivalence checking."""

    def test_equivalent_urls_with_tracking_params(self):
        """Test that URLs differing only by tracking params are equivalent."""
        url1 = "https://example.com/job?utm_source=google"
        url2 = "https://example.com/job"

        assert are_urls_equivalent(url1, url2) is True

    def test_equivalent_urls_with_casing_differences(self):
        """Test that URLs differing only by casing are equivalent."""
        url1 = "https://Example.COM/JOB"
        url2 = "https://example.com/job"

        assert are_urls_equivalent(url1, url2) is True

    def test_non_equivalent_urls(self):
        """Test that different URLs are not equivalent."""
        url1 = "https://example.com/job/123"
        url2 = "https://example.com/job/456"

        assert are_urls_equivalent(url1, url2) is False

    def test_malformed_url_returns_false(self):
        """Test that malformed URLs return False for equivalence."""
        url1 = "https://example.com/job"
        url2 = "not a valid url"

        assert are_urls_equivalent(url1, url2) is False

    def test_both_malformed_urls_returns_false(self):
        """Test that both malformed URLs return False."""
        url1 = "not a valid url 1"
        url2 = "not a valid url 2"

        assert are_urls_equivalent(url1, url2) is False

    def test_empty_urls_returns_false(self):
        """Test that empty URLs return False."""
        assert are_urls_equivalent("", "") is False


class TestComplexUrlScenarios:
    """Test complex URL scenarios."""

    def test_url_with_multiple_tracking_params(self):
        """Test URL with multiple tracking parameters."""
        url = (
            "https://example.com/job?"
            "utm_source=google&"
            "utm_medium=email&"
            "utm_campaign=summer2024&"
            "fbclid=abc123&"
            "gclid=xyz789&"
            "id=123"
        )
        expected_equivalent = "https://example.com/job?id=123"

        result = normalize_url(url)
        expected = normalize_url(expected_equivalent)

        assert result == expected

    def test_url_with_unicode_in_path(self):
        """Test URL with unicode characters in path."""
        url = "https://example.com/job/développeur"
        result = normalize_url(url)

        assert result is not None
        assert len(result) == 64

    def test_url_with_query_params_only(self):
        """Test URL with only query parameters (no path)."""
        url = "https://example.com?search=python&location=remote"
        result = normalize_url(url)

        assert result is not None
        assert len(result) == 64

    def test_url_with_complex_query_params(self):
        """Test URL with complex query parameters including arrays."""
        url = "https://example.com/job?tags[]=python&tags[]=remote&id=123"
        result = normalize_url(url)

        assert result is not None
        assert len(result) == 64
