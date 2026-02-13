"""URL normalization service for generating stable dedupe keys."""

from __future__ import annotations

import hashlib
import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


logger = logging.getLogger(__name__)

# Tracking parameters to strip from URLs
_TRACKING_PARAMS = {
    # Google Analytics
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
    # Google Ads
    "gclid",
    "gclsrc",
    "dclid",
    # Microsoft Ads
    "msclkid",
    # General tracking
    "ref",
    "source",
    "medium",
    "campaign",
    "term",
    "content",
    # Other common tracking params
    "cid",
    "mcid",
    "sourceid",
}

# Default ports to remove
_DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize_url(url: str) -> str | None:
    """Normalize a URL for stable dedupe key generation.

    Performs the following normalizations:
    - Lowercases scheme and host
    - Removes default ports (80 for http, 443 for https)
    - Strips tracking parameters (utm_*, fbclid, gclid, etc.)
    - Sorts query parameters alphabetically
    - Removes fragment identifiers
    - Generates SHA-256 hash of normalized URL

    Args:
        url: The URL to normalize

    Returns:
        A SHA-256 hash string of the normalized URL, or None if URL is malformed.
        The original URL is preserved elsewhere; this hash is for dedupe only.

    """
    if not url or not isinstance(url, str):
        logger.warning("url_normalization.empty_or_invalid url=%s", url)
        return None

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        logger.warning("url_normalization.parse_failed url=%s error=%s", url, e)
        return None

    # Validate scheme and host
    if not parsed.scheme or not parsed.netloc:
        logger.warning("url_normalization.missing_scheme_or_host url=%s", url)
        return None

    # Normalize scheme (lowercase)
    scheme = parsed.scheme.lower()

    # Normalize host (lowercase)
    host = parsed.netloc.lower()

    # Remove default port if present
    if ":" in host:
        host_parts = host.rsplit(":", 1)
        if len(host_parts) == 2:
            hostname, port_str = host_parts
            try:
                port = int(port_str)
                default_port = _DEFAULT_PORTS.get(scheme)
                if default_port and port == default_port:
                    host = hostname
            except ValueError:
                # Port is not a valid number, keep as-is
                pass

    # Normalize path (lowercase and ensure it starts with / if not empty)
    path = parsed.path.lower() if parsed.path else parsed.path
    if path and not path.startswith("/"):
        path = "/" + path

    # Strip tracking parameters and sort remaining
    query = _normalize_query(parsed.query)

    # Remove fragment entirely
    fragment = ""

    # Reconstruct normalized URL
    normalized = urlunparse((scheme, host, path, parsed.params, query, fragment))

    # Generate SHA-256 hash
    hash_value = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    return hash_value


def _normalize_query(query: str) -> str:
    """Normalize query string by removing tracking params and sorting.

    Args:
        query: Raw query string

    Returns:
        Normalized query string with tracking params removed and sorted alphabetically.

    """
    if not query:
        return ""

    try:
        params = parse_qs(query, keep_blank_values=True)
    except Exception:
        # If parsing fails, return empty query
        return ""

    # Filter out tracking parameters
    filtered_params = {
        k: v for k, v in params.items() if k.lower() not in _TRACKING_PARAMS
    }

    if not filtered_params:
        return ""

    # Sort parameters alphabetically and encode
    # Use doseq=True to handle multiple values for same key
    return urlencode(sorted(filtered_params.items()), doseq=True)


def are_urls_equivalent(url1: str, url2: str) -> bool:
    """Check if two URLs are equivalent after normalization.

    Args:
        url1: First URL
        url2: Second URL

    Returns:
        True if both URLs normalize to the same key, False otherwise.
        Returns False if either URL is malformed.

    """
    key1 = normalize_url(url1)
    key2 = normalize_url(url2)

    if key1 is None or key2 is None:
        return False

    return key1 == key2
