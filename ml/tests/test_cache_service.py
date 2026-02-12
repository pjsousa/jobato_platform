from datetime import datetime, timezone

from app.services.cache import CachePolicy, CacheService, load_cache_policy


def test_load_cache_policy_reads_ttl_and_revisit_values(tmp_path):
    cache_config = tmp_path / "cache.yaml"
    cache_config.write_text(
        "\n".join(
            [
                "cache:",
                "  ttlHours: 12",
                "  revisitThrottleDays: 7",
                "",
            ]
        ),
        encoding="utf-8",
    )

    policy = load_cache_policy(path=cache_config)

    assert policy.ttl_hours == 12
    assert policy.revisit_throttle_days == 7


def test_cache_ttl_boundary_uses_strict_expiry(tmp_path):
    service = CacheService(data_dir=tmp_path, policy=CachePolicy(ttl_hours=12, revisit_throttle_days=7))
    now = datetime(2026, 2, 12, 12, 0, 0, tzinfo=timezone.utc)

    still_fresh = service.is_cache_fresh(
        cached_at="2026-02-12T00:00:00Z",
        cache_expires_at="2026-02-12T12:00:01Z",
        now=now,
    )
    expired_on_boundary = service.is_cache_fresh(
        cached_at="2026-02-12T00:00:00Z",
        cache_expires_at="2026-02-12T12:00:00Z",
        now=now,
    )

    assert still_fresh is True
    assert expired_on_boundary is False


def test_revisit_throttle_boundary_allows_at_7_day_cutoff(tmp_path):
    service = CacheService(data_dir=tmp_path, policy=CachePolicy(ttl_hours=12, revisit_throttle_days=7))
    now = datetime(2026, 2, 12, 12, 0, 0, tzinfo=timezone.utc)

    throttled_before_cutoff = service.is_revisit_throttled(
        last_seen_at="2026-02-05T12:00:01Z",
        now=now,
    )
    allowed_on_cutoff = service.is_revisit_throttled(
        last_seen_at="2026-02-05T12:00:00Z",
        now=now,
    )

    assert throttled_before_cutoff is True
    assert allowed_on_cutoff is False
