"""URL normalization for stable dedupe keys.

This module provides deterministic URL normalization for deduplication purposes.
The normalized URL is used as a stable key for detecting duplicate job postings.

Normalization rules:
- Lowercase scheme and host
- Remove default ports (80 for http, 443 for https)
- Strip tracking parameters (utm_*, fbclid, gclid, msclkid, ref, source, etc.)
- Remove fragment identifiers
- Sort query parameters alphabetically
- Normalize percent-encoding

The normalization is idempotent: normalize(normalize(url)) == normalize(url)
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

logger = logging.getLogger(__name__)

# Tracking parameters to strip from URLs
TRACKING_PARAMS = frozenset(
    {
        # Google Analytics / UTM
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "utm_source_platform",
        "utm_creative_format",
        "utm_marketing_tactic",
        # Facebook
        "fbclid",
        "fb_action_ids",
        "fb_action_types",
        "fb_source",
        "fb_ref",
        # Google Ads
        "gclid",
        "gclsrc",
        "dclid",
        # Microsoft Ads
        "msclkid",
        # General tracking
        "ref",
        "source",
        "src",
        "campaign",
        "affiliate",
        "affiliate_id",
        "partner",
        "partner_id",
        "tracking",
        "track",
        "trk",
        "click_id",
        "clickid",
        # LinkedIn
        "li_fat_id",
        "li_fat_idinfo",
        # Twitter
        "twclid",
        # TikTok
        "ttclid",
        # Session/analytics
        "sessionid",
        "session_id",
        "_ga",
        "_gl",
        "_hsenc",
        "_hsmi",
        # Email tracking
        "mc_cid",
        "mc_eid",
        # Other common tracking
        "igshid",
        "s_kwcid",
        "zanpid",
    }
)

# Default ports by scheme
DEFAULT_PORTS = {
    "http": 80,
    "https": 443,
    "ftp": 21,
}


@dataclass(frozen=True)
class NormalizationResult:
    """Result of URL normalization attempt."""

    normalized_url: str | None
    error: str | None
    original_url: str

    @property
    def success(self) -> bool:
        return self.normalized_url is not None and self.error is None


def normalize_url(url: str) -> NormalizationResult:
    """Normalize a URL for stable dedupe key generation.

    Args:
        url: The URL to normalize.

    Returns:
        NormalizationResult with normalized_url on success or error on failure.
        The original_url is always preserved.

    The normalization is deterministic and idempotent. Two URLs that represent
    the same resource will produce the same normalized key.
    """
    if not url:
        return NormalizationResult(
            normalized_url=None,
            error="Empty URL",
            original_url=url or "",
        )

    try:
        return _normalize_url_impl(url)
    except Exception as exc:
        logger.warning("url_normalizer.error url=%s error=%s", url, str(exc))
        return NormalizationResult(
            normalized_url=None,
            error=str(exc),
            original_url=url,
        )


def _normalize_url_impl(url: str) -> NormalizationResult:
    """Internal implementation of URL normalization."""
    original_url = url.strip()

    # Parse the URL
    parsed = urlparse(original_url)

    # Validate scheme
    scheme = parsed.scheme.lower()
    if not scheme:
        return NormalizationResult(
            normalized_url=None,
            error="Missing URL scheme",
            original_url=original_url,
        )

    if scheme not in ("http", "https", "ftp"):
        return NormalizationResult(
            normalized_url=None,
            error=f"Unsupported URL scheme: {scheme}",
            original_url=original_url,
        )

    # Validate netloc (host)
    if not parsed.netloc:
        return NormalizationResult(
            normalized_url=None,
            error="Missing URL host",
            original_url=original_url,
        )

    # Normalize host (lowercase)
    host = parsed.hostname
    if not host:
        return NormalizationResult(
            normalized_url=None,
            error="Invalid URL host",
            original_url=original_url,
        )
    host = host.lower()

    # Handle port - remove default ports
    port = parsed.port
    if port and port == DEFAULT_PORTS.get(scheme):
        port = None

    # Build netloc with optional port
    netloc = host
    if port:
        netloc = f"{host}:{port}"

    # Preserve userinfo if present (rare but valid)
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo = f"{userinfo}:{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    # Normalize path
    path = parsed.path or "/"
    # Normalize empty path to /
    if not path:
        path = "/"
    # Remove trailing slash except for root
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    # Normalize double slashes
    while "//" in path:
        path = path.replace("//", "/")

    # Filter and sort query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = [
        (key, value)
        for key, value in query_params
        if key.lower() not in TRACKING_PARAMS
        and not key.lower().startswith("utm_")
    ]
    # Sort alphabetically by key, then by value for stability
    sorted_params = sorted(filtered_params, key=lambda x: (x[0].lower(), x[1]))
    query = urlencode(sorted_params)

    # Remove fragment (anchor)
    fragment = ""

    # Reconstruct the URL
    normalized = urlunparse((scheme, netloc, path, "", query, fragment))

    return NormalizationResult(
        normalized_url=normalized,
        error=None,
        original_url=original_url,
    )


def are_urls_equivalent(url1: str, url2: str) -> bool:
    """Check if two URLs are equivalent after normalization.

    Args:
        url1: First URL to compare.
        url2: Second URL to compare.

    Returns:
        True if both URLs normalize to the same key, False otherwise.
        Returns False if either URL fails normalization.
    """
    result1 = normalize_url(url1)
    result2 = normalize_url(url2)

    if not result1.success or not result2.success:
        return False

    return result1.normalized_url == result2.normalized_url
