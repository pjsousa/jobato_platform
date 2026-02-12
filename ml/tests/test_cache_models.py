from app.db.models import RunResult
from app.services.cache import CachePolicy, CacheService


def test_run_result_model_has_cache_fields():
    assert hasattr(RunResult, "cache_key")
    assert hasattr(RunResult, "cached_at")
    assert hasattr(RunResult, "cache_expires_at")
    assert hasattr(RunResult, "last_seen_at")
    assert hasattr(RunResult, "skip_reason")


def test_cache_service_can_generate_stable_keys(tmp_path):
    service = CacheService(data_dir=tmp_path, policy=CachePolicy(ttl_hours=12, revisit_throttle_days=7))

    first = service.generate_cache_key(query_text="Senior Backend Remote", domain="Workable.com")
    second = service.generate_cache_key(query_text="  senior   backend remote ", domain="workable.com")

    assert first == second
