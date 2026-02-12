from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

class HtmlFetcher:
    def __init__(self, data_dir: Path | str | None = None, timeout: int = 30) -> None:
        self.data_dir = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self.timeout = timeout

    def fetch_html(self, url: str, *, run_id: str) -> tuple[str | None, str | None]:
        if not url:
            return None, "url is required"
        if not run_id:
            return None, "run_id is required"

        destination = self._build_destination_path(url, run_id)
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            html = self._read_html(url)
            destination.write_text(html, encoding="utf-8")
            return str(destination), None
        except Exception as error:
            return None, str(error)

    def _build_destination_path(self, url: str, run_id: str) -> Path:
        run_key = _sanitize_segment(run_id)
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.data_dir / "html" / "raw" / run_key / f"{url_hash}.html"

    def _read_html(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme == "mock":
            domain = parsed.netloc or "example.com"
            path = parsed.path or "/"
            return (
                "<html><head><title>Mock page</title></head><body>"
                f"<h1>Mock result for {domain}</h1>"
                f"<p>Path: {path}</p>"
                "<p>This deterministic content is for ingestion tests.</p>"
                "</body></html>"
            )

        request = Request(url, headers={"User-Agent": "jobato/1.0"}, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
        except HTTPError as error:
            raise RuntimeError(f"HTTP {error.code} while fetching {url}") from error
        except (TimeoutError, URLError, OSError) as error:
            raise RuntimeError(f"Failed to fetch HTML for {url}: {error}") from error

        return content.decode(charset, errors="replace")


def _sanitize_segment(value: str) -> str:
    cleaned = [ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value]
    normalized = "".join(cleaned).strip("_")
    return normalized or "unknown"
