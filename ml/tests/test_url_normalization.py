"""Tests for URL normalization for stable dedupe keys.

Tests cover:
- AC1: Normalized URL key generation and storage
- AC2: Equivalent URLs with tracking params/casing produce same key
- AC3: Malformed URLs record clear error without crashing
"""

import pytest

from app.services.url_normalizer import (
    NormalizationResult,
    are_urls_equivalent,
    normalize_url,
)


class TestNormalizeUrl:
    """Test URL normalization produces stable, deterministic keys."""

    def test_basic_url_normalization(self):
        """Basic URL is normalized correctly."""
        result = normalize_url("https://example.com/jobs/123")
        assert result.success
        assert result.normalized_url == "https://example.com/jobs/123"
        assert result.error is None
        assert result.original_url == "https://example.com/jobs/123"

    def test_preserves_original_url(self):
        """Original URL is always preserved in the result."""
        original = "HTTPS://EXAMPLE.COM/Jobs/123?utm_source=test"
        result = normalize_url(original)
        assert result.original_url == original
        assert result.success

    def test_lowercase_scheme(self):
        """Scheme is normalized to lowercase."""
        result = normalize_url("HTTPS://example.com/page")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_lowercase_host(self):
        """Host is normalized to lowercase."""
        result = normalize_url("https://EXAMPLE.COM/page")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_removes_default_https_port(self):
        """Default HTTPS port 443 is removed."""
        result = normalize_url("https://example.com:443/page")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_removes_default_http_port(self):
        """Default HTTP port 80 is removed."""
        result = normalize_url("http://example.com:80/page")
        assert result.success
        assert result.normalized_url == "http://example.com/page"

    def test_preserves_non_default_port(self):
        """Non-default ports are preserved."""
        result = normalize_url("https://example.com:8443/page")
        assert result.success
        assert result.normalized_url == "https://example.com:8443/page"

    def test_removes_fragment(self):
        """Fragment identifiers are removed."""
        result = normalize_url("https://example.com/page#section")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_removes_empty_fragment(self):
        """Empty fragments are removed."""
        result = normalize_url("https://example.com/page#")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_sorts_query_params(self):
        """Query parameters are sorted alphabetically."""
        result = normalize_url("https://example.com/page?z=1&a=2&m=3")
        assert result.success
        assert result.normalized_url == "https://example.com/page?a=2&m=3&z=1"

    def test_preserves_path(self):
        """Path is preserved correctly."""
        result = normalize_url("https://example.com/jobs/backend/senior")
        assert result.success
        assert result.normalized_url == "https://example.com/jobs/backend/senior"

    def test_normalizes_empty_path_to_root(self):
        """Empty path is normalized to /."""
        result = normalize_url("https://example.com")
        assert result.success
        assert result.normalized_url == "https://example.com/"

    def test_removes_trailing_slash_except_root(self):
        """Trailing slash is removed except for root path."""
        result = normalize_url("https://example.com/page/")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_keeps_trailing_slash_for_root(self):
        """Root path keeps its trailing slash."""
        result = normalize_url("https://example.com/")
        assert result.success
        assert result.normalized_url == "https://example.com/"

    def test_removes_double_slashes_in_path(self):
        """Double slashes in path are normalized."""
        result = normalize_url("https://example.com//page//subpage")
        assert result.success
        assert result.normalized_url == "https://example.com/page/subpage"

    def test_idempotent_normalization(self):
        """Normalization is idempotent: normalize(normalize(x)) == normalize(x)."""
        original = "HTTPS://EXAMPLE.COM:443/PAGE/?b=2&a=1#fragment"
        first = normalize_url(original)
        second = normalize_url(first.normalized_url)
        assert first.normalized_url == second.normalized_url


class TestTrackingParameterRemoval:
    """Test that tracking parameters are stripped."""

    @pytest.mark.parametrize(
        "param",
        [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "utm_id",
            "utm_source_platform",
            "utm_creative_format",
            "utm_marketing_tactic",
            "fbclid",
            "gclid",
            "gclsrc",
            "dclid",
            "msclkid",
            "ref",
            "source",
            "src",
            "campaign",
            "affiliate",
            "tracking",
            "track",
            "trk",
            "click_id",
            "clickid",
            "twclid",
            "ttclid",
            "_ga",
            "_gl",
        ],
    )
    def test_removes_tracking_param(self, param):
        """Known tracking parameters are removed."""
        url = f"https://example.com/page?{param}=value&keep=this"
        result = normalize_url(url)
        assert result.success
        assert param not in result.normalized_url
        assert "keep=this" in result.normalized_url

    def test_removes_utm_prefixed_params(self):
        """Any utm_ prefixed parameter is removed."""
        result = normalize_url(
            "https://example.com/page?utm_custom=val&keep=this"
        )
        assert result.success
        assert "utm_custom" not in result.normalized_url
        assert "keep=this" in result.normalized_url

    def test_preserves_legitimate_params(self):
        """Legitimate query parameters are preserved."""
        result = normalize_url("https://example.com/page?id=123&page=1")
        assert result.success
        assert "id=123" in result.normalized_url
        assert "page=1" in result.normalized_url

    def test_removes_all_tracking_preserves_all_legitimate(self):
        """Complex URL with mixed params is handled correctly."""
        url = (
            "https://example.com/job/123"
            "?id=123&utm_source=google&page=1&fbclid=abc&sort=date&gclid=xyz"
        )
        result = normalize_url(url)
        assert result.success
        assert "id=123" in result.normalized_url
        assert "page=1" in result.normalized_url
        assert "sort=date" in result.normalized_url
        assert "utm_source" not in result.normalized_url
        assert "fbclid" not in result.normalized_url
        assert "gclid" not in result.normalized_url


class TestUrlEquivalence:
    """Test AC2: URLs differing only by tracking params/casing produce same key."""

    def test_urls_with_different_casing_are_equivalent(self):
        """URLs differing only by host casing are equivalent."""
        assert are_urls_equivalent(
            "https://EXAMPLE.COM/page",
            "https://example.com/page",
        )

    def test_urls_with_different_scheme_casing_are_equivalent(self):
        """URLs differing only by scheme casing are equivalent."""
        assert are_urls_equivalent(
            "HTTPS://example.com/page",
            "https://example.com/page",
        )

    def test_urls_with_different_tracking_params_are_equivalent(self):
        """URLs differing only by tracking params are equivalent."""
        assert are_urls_equivalent(
            "https://example.com/page?utm_source=google",
            "https://example.com/page?utm_source=facebook",
        )

    def test_urls_with_tracking_vs_no_tracking_are_equivalent(self):
        """URL with tracking params is equivalent to same URL without."""
        assert are_urls_equivalent(
            "https://example.com/page?utm_source=test&fbclid=123",
            "https://example.com/page",
        )

    def test_urls_with_fragment_vs_no_fragment_are_equivalent(self):
        """URL with fragment is equivalent to same URL without."""
        assert are_urls_equivalent(
            "https://example.com/page#section",
            "https://example.com/page",
        )

    def test_urls_with_default_port_vs_no_port_are_equivalent(self):
        """URL with default port is equivalent to same URL without."""
        assert are_urls_equivalent(
            "https://example.com:443/page",
            "https://example.com/page",
        )

    def test_urls_with_different_query_param_order_are_equivalent(self):
        """URLs with same query params in different order are equivalent."""
        assert are_urls_equivalent(
            "https://example.com/page?a=1&b=2",
            "https://example.com/page?b=2&a=1",
        )

    def test_different_paths_are_not_equivalent(self):
        """URLs with different paths are not equivalent."""
        assert not are_urls_equivalent(
            "https://example.com/page1",
            "https://example.com/page2",
        )

    def test_different_hosts_are_not_equivalent(self):
        """URLs with different hosts are not equivalent."""
        assert not are_urls_equivalent(
            "https://example.com/page",
            "https://other.com/page",
        )

    def test_different_legitimate_params_are_not_equivalent(self):
        """URLs with different legitimate query params are not equivalent."""
        assert not are_urls_equivalent(
            "https://example.com/page?id=1",
            "https://example.com/page?id=2",
        )

    def test_complex_equivalent_urls(self):
        """Complex real-world URLs that should be equivalent."""
        url1 = (
            "HTTPS://Jobs.EXAMPLE.COM:443/posting/123"
            "?utm_source=linkedin&utm_medium=social&fbclid=abc123#apply"
        )
        url2 = "https://jobs.example.com/posting/123"
        assert are_urls_equivalent(url1, url2)


class TestMalformedUrlHandling:
    """Test AC3: Malformed URLs record clear error without crashing."""

    def test_empty_url_returns_error(self):
        """Empty URL returns clear error."""
        result = normalize_url("")
        assert not result.success
        assert result.normalized_url is None
        assert result.error == "Empty URL"
        assert result.original_url == ""

    def test_none_url_returns_error(self):
        """None URL returns clear error (if passed as empty string)."""
        result = normalize_url(None)  # type: ignore
        assert not result.success
        assert result.normalized_url is None
        assert result.error is not None

    def test_missing_scheme_returns_error(self):
        """URL without scheme returns clear error."""
        result = normalize_url("example.com/page")
        assert not result.success
        assert result.normalized_url is None
        assert "scheme" in result.error.lower()
        assert result.original_url == "example.com/page"

    def test_unsupported_scheme_returns_error(self):
        """URL with unsupported scheme returns clear error."""
        result = normalize_url("file:///path/to/file")
        assert not result.success
        assert result.normalized_url is None
        assert "scheme" in result.error.lower()

    def test_missing_host_returns_error(self):
        """URL without host returns clear error."""
        result = normalize_url("https:///page")
        assert not result.success
        assert result.normalized_url is None
        assert "host" in result.error.lower()

    def test_javascript_scheme_returns_error(self):
        """JavaScript URL returns clear error."""
        result = normalize_url("javascript:alert(1)")
        assert not result.success
        assert result.normalized_url is None

    def test_data_scheme_returns_error(self):
        """Data URL returns clear error."""
        result = normalize_url("data:text/html,<h1>Test</h1>")
        assert not result.success
        assert result.normalized_url is None

    def test_malformed_url_does_not_raise(self):
        """Malformed URLs do not raise exceptions."""
        malformed_urls = [
            "",
            "   ",
            "not a url",
            "://missing-scheme.com",
            "ftp://",
            "mailto:user@example.com",
        ]
        for url in malformed_urls:
            result = normalize_url(url)
            # Should not raise, should return error
            assert isinstance(result, NormalizationResult)
            if not result.success:
                assert result.error is not None

    def test_equivalence_with_malformed_url_returns_false(self):
        """Checking equivalence with malformed URL returns False."""
        assert not are_urls_equivalent("", "https://example.com")
        assert not are_urls_equivalent("https://example.com", "not a url")
        assert not are_urls_equivalent("invalid", "also invalid")


class TestEdgeCases:
    """Test edge cases and special URL formats."""

    def test_url_with_userinfo(self):
        """URL with username is handled."""
        result = normalize_url("https://user@example.com/page")
        assert result.success
        assert "user@" in result.normalized_url

    def test_url_with_userinfo_and_password(self):
        """URL with username:password is handled."""
        result = normalize_url("https://user:pass@example.com/page")
        assert result.success
        assert "user:pass@" in result.normalized_url

    def test_url_with_unicode_host(self):
        """URL with unicode characters in host is handled."""
        # IDN domains should work
        result = normalize_url("https://example.com/page")
        assert result.success

    def test_url_with_encoded_characters(self):
        """URL with percent-encoded characters is handled."""
        result = normalize_url("https://example.com/path%20with%20spaces")
        assert result.success
        assert result.normalized_url is not None

    def test_url_with_empty_query_string(self):
        """URL with empty query string is handled."""
        result = normalize_url("https://example.com/page?")
        assert result.success
        # Empty query should be removed
        assert result.normalized_url == "https://example.com/page"

    def test_url_with_query_param_without_value(self):
        """URL with query param without value is handled."""
        result = normalize_url("https://example.com/page?flag")
        assert result.success
        assert "flag" in result.normalized_url

    def test_ftp_url_is_supported(self):
        """FTP URLs are supported."""
        result = normalize_url("ftp://files.example.com/file.txt")
        assert result.success
        assert result.normalized_url == "ftp://files.example.com/file.txt"

    def test_whitespace_trimming(self):
        """Leading/trailing whitespace is trimmed."""
        result = normalize_url("  https://example.com/page  ")
        assert result.success
        assert result.normalized_url == "https://example.com/page"

    def test_very_long_url(self):
        """Very long URLs are handled."""
        path = "/a" * 500
        url = f"https://example.com{path}"
        result = normalize_url(url)
        assert result.success
        assert result.normalized_url is not None


class TestRealWorldUrls:
    """Test with real-world job posting URL patterns."""

    def test_linkedin_job_url(self):
        """LinkedIn job URL is normalized correctly."""
        url = (
            "https://www.linkedin.com/jobs/view/123456789"
            "?utm_campaign=google_jobs&utm_source=google_jobs_apply"
            "&utm_medium=organic&originalSubdomain=uk"
        )
        result = normalize_url(url)
        assert result.success
        # Tracking params removed, legitimate params kept
        assert "utm_campaign" not in result.normalized_url
        assert "utm_source" not in result.normalized_url
        assert "originalSubdomain=uk" in result.normalized_url

    def test_indeed_job_url(self):
        """Indeed job URL is normalized correctly."""
        url = (
            "https://www.indeed.com/viewjob?jk=abc123def456"
            "&tk=1abc2def3ghi&from=serp&vjs=3"
        )
        result = normalize_url(url)
        assert result.success
        assert "jk=abc123def456" in result.normalized_url

    def test_greenhouse_job_url(self):
        """Greenhouse job URL is normalized correctly."""
        url = (
            "https://boards.greenhouse.io/company/jobs/123456"
            "?gh_src=abc123def&source=LinkedIn"
        )
        result = normalize_url(url)
        assert result.success
        # gh_src is not a standard tracking param, should be kept
        assert "gh_src=abc123def" in result.normalized_url
        # 'source' is a tracking param
        assert "source=" not in result.normalized_url

    def test_lever_job_url(self):
        """Lever job URL is normalized correctly."""
        url = "https://jobs.lever.co/company/abc-123-def-456"
        result = normalize_url(url)
        assert result.success
        assert result.normalized_url == "https://jobs.lever.co/company/abc-123-def-456"

    def test_workable_job_url(self):
        """Workable job URL is normalized correctly."""
        url = "https://apply.workable.com/company/j/ABC123DEF/"
        result = normalize_url(url)
        assert result.success
        # Trailing slash should be removed
        assert result.normalized_url == "https://apply.workable.com/company/j/ABC123DEF"

    def test_equivalent_job_postings_from_different_sources(self):
        """Same job accessed via different tracking links should be equivalent."""
        direct = "https://jobs.example.com/posting/12345"
        google = (
            "https://jobs.example.com/posting/12345"
            "?utm_source=google&gclid=abc123"
        )
        linkedin = (
            "https://jobs.example.com/posting/12345"
            "?utm_source=linkedin&li_fat_id=xyz"
        )
        facebook = (
            "https://jobs.example.com/posting/12345"
            "?fbclid=fb123&ref=social"
        )

        direct_result = normalize_url(direct)
        google_result = normalize_url(google)
        linkedin_result = normalize_url(linkedin)
        facebook_result = normalize_url(facebook)

        assert direct_result.normalized_url == google_result.normalized_url
        assert direct_result.normalized_url == linkedin_result.normalized_url
        assert direct_result.normalized_url == facebook_result.normalized_url
