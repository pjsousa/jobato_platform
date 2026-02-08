from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import RunResult


class CacheService:
    def __init__(self, session: Session, logger: logging.Logger | None = None) -> None:
        self._session = session
        self._logger = logger or logging.getLogger(__name__)
        self._cache_ttl_hours = 12
        self._revisit_throttle_days = 7

    def generate_cache_key(self, query_text: str, domain: str) -> str:
        """Generate a stable cache key from query text and domain."""
        key_string = f"{query_text}+{domain}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def is_cache_fresh(self, cached_at: str, cache_expires_at: str) -> bool:
        """Check if a cached result is still valid."""
        if not cached_at or not cache_expires_at:
            return False
            
        try:
            cached_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
            expiry_time = datetime.fromisoformat(cache_expires_at.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) < expiry_time
        except ValueError:
            return False

    def get_cached_results(self, run_id: str, cache_key: str) -> List[RunResult] | None:
        """Retrieve cached results if they exist and are fresh."""
        try:
            results = self._session.query(RunResult).filter(
                RunResult.run_id == run_id,
                RunResult.cache_key == cache_key
            ).all()
            
            # Check if any results are cached and not expired
            if results:
                # We check if the first result is still valid (assuming all results are from same cache)
                if self.is_cache_fresh(results[0].cached_at, results[0].cache_expires_at):
                    self._logger.info(
                        "cache.hit run_id=%s cache_key=%s", run_id, cache_key
                    )
                    return results
                else:
                    self._logger.info(
                        "cache.expired run_id=%s cache_key=%s", run_id, cache_key
                    )
            else:
                self._logger.info(
                    "cache.miss run_id=%s cache_key=%s", run_id, cache_key
                )
        except Exception as e:
            self._logger.error(
                "cache.error run_id=%s cache_key=%s error=%s", run_id, cache_key, str(e)
            )
            
        return None

    def store_cached_results(self, run_id: str, cache_key: str, results: List[RunResult]) -> None:
        """Store results in cache with expiration metadata."""
        try:
            # Set cache expiration to 12 hours from now
            now = datetime.now(timezone.utc)
            expiry_time = now + timedelta(hours=self._cache_ttl_hours)
            
            # Format timestamps consistently
            now_str = now.isoformat().replace('+00:00', 'Z')
            expiry_str = expiry_time.isoformat().replace('+00:00', 'Z')
            
            # Update existing results with cache metadata or add it to new results
            for result in results:
                result.cache_key = cache_key
                result.cached_at = now_str
                result.cache_expires_at = expiry_str
                
            self._logger.info(
                "cache.stored run_id=%s cache_key=%s results=%s", 
                run_id, cache_key, len(results)
            )
        except Exception as e:
            self._logger.error(
                "cache.store.error run_id=%s cache_key=%s error=%s", 
                run_id, cache_key, str(e)
            )

    def is_url_revisit_allowed(self, last_seen_at: str | None) -> bool:
        """Check if a URL can be revisited based on throttle (7 days)."""
        if not last_seen_at:
            return True  # No previous visit, allowed
            
        try:
            seen_time = datetime.fromisoformat(last_seen_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            time_diff = now - seen_time
            
            # Allow revisit if older than 7 days
            return time_diff.days >= self._revisit_throttle_days
        except ValueError:
            # If timestamp is invalid, allow revisit
            return True

    def mark_url_seen(self, run_id: str, url: str) -> None:
        """Mark a URL as seen for revisit throttling."""
        try:
            now = datetime.now(timezone.utc)
            now_str = now.isoformat().replace('+00:00', 'Z')
            
            # Update the last_seen_at for URLs matching this URL
            # This is a simplified approach - more complex might need a separate table
            self._session.query(RunResult).filter(
                RunResult.run_id == run_id,
                RunResult.raw_url == url
            ).update({
                RunResult.last_seen_at: now_str
            })
            self._session.commit()
        except Exception as e:
            self._logger.error(
                "revisit.throttle.error run_id=%s url=%s error=%s", 
                run_id, url, str(e)
            )