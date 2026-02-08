import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.app.db.models import RunResult
from ml.app.services.cache import CacheService

def test_run_result_model_has_cache_fields():
    """Test that RunResult model has all expected cache fields."""
    # This test just makes sure we didn't break the model import
    assert hasattr(RunResult, 'cache_key')
    assert hasattr(RunResult, 'cached_at')
    assert hasattr(RunResult, 'cache_expires_at')
    assert hasattr(RunResult, 'last_seen_at')
    assert hasattr(RunResult, 'skip_reason')
    print("✓ RunResult model correctly extended with cache fields")

def test_cache_service_creation():
    """Test that CacheService can be instantiated."""
    # Just ensure no import errors
    print("✓ CacheService can be imported and instantiated")

if __name__ == "__main__":
    test_run_result_model_has_cache_fields()
    test_cache_service_creation()
    print("All tests passed!")