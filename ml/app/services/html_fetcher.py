from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.fetcher import FetchResponse


class HtmlFetcher:
    def __init__(self, data_dir: Path | str | None = None, timeout: int = 30):
        self.data_dir = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self.timeout = timeout
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_html(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Fetch HTML content from a URL and save it to file storage.
        
        Returns:
            tuple of (file_path, error_message) where:
            - file_path: path to saved HTML file or None if failed
            - error_message: error description or None if successful
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Create HTML storage directory if it doesn't exist
            html_dir = self.data_dir / "html" / "raw"
            html_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate deterministic filename based on URL
            filename = self._generate_filename(url)
            file_path = html_dir / filename
            
            # Save HTML content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            return str(file_path), None
            
        except Exception as e:
            return None, str(e)

    def _generate_filename(self, url: str) -> str:
        """
        Generate a deterministic, filesystem-safe filename for HTML content.
        
        Uses URL hash for collision safety and traceability.
        """
        parsed_url = urlparse(url)
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return f"{url_hash}.html"