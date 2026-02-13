"""Tests for the scoring pipeline."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, RunResult
from app.pipelines.scoring import (
    score_run_results,
    validate_score,
    get_canonical_score,
    MIN_SCORE,
    MAX_SCORE,
    DEFAULT_SCORE,
    DEFAULT_SCORE_VERSION,
)


@pytest.fixture
def session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_results(session):
    """Create sample results for testing."""
    results = [
        RunResult(
            run_id="test-run-1",
            query_id="q1",
            query_text="test query",
            search_query="site:example.com test",
            domain="example.com",
            title="Job 1",
            snippet="Snippet 1",
            raw_url="https://example.com/job1",
            final_url="https://example.com/job1",
            created_at="2026-02-13T10:00:00Z",
            updated_at="2026-02-13T10:00:00Z",
            is_duplicate=False,
            is_hidden=False,
            duplicate_count=0,
        ),
        RunResult(
            run_id="test-run-1",
            query_id="q2",
            query_text="test query 2",
            search_query="site:example.com test2",
            domain="example.com",
            title="Job 2",
            snippet="Snippet 2",
            raw_url="https://example.com/job2",
            final_url="https://example.com/job2",
            created_at="2026-02-13T10:01:00Z",
            updated_at="2026-02-13T10:01:00Z",
            is_duplicate=False,
            is_hidden=False,
            duplicate_count=0,
        ),
    ]
    session.add_all(results)
    session.commit()
    return results


@pytest.fixture
def duplicate_result(session, sample_results):
    """Create a duplicate result linked to the first sample result."""
    canonical = sample_results[0]
    duplicate = RunResult(
        run_id="test-run-1",
        query_id="q1",
        query_text="test query",
        search_query="site:example.com test",
        domain="example.com",
        title="Job 1 Duplicate",
        snippet="Snippet 1 Duplicate",
        raw_url="https://example.com/job1-dup",
        final_url="https://example.com/job1-dup",
        created_at="2026-02-13T10:02:00Z",
        updated_at="2026-02-13T10:02:00Z",
        canonical_id=canonical.id,
        is_duplicate=True,
        is_hidden=True,
        duplicate_count=0,
    )
    session.add(duplicate)
    session.commit()
    return duplicate


class TestScoreRunResults:
    """Tests for the score_run_results function."""

    def test_scores_non_duplicate_results(self, session, sample_results):
        """AC1: Non-duplicate results receive a score in range [-1, 1]."""
        outcome = score_run_results(session, "test-run-1")
        
        assert outcome.scored_count == 2
        assert outcome.skipped_count == 0
        
        # Verify scores were assigned
        for result in sample_results:
            session.refresh(result)
            assert result.relevance_score is not None
            assert MIN_SCORE <= result.relevance_score <= MAX_SCORE

    def test_default_score_is_zero(self, session, sample_results):
        """AC2: Default score is 0 when no model exists."""
        score_run_results(session, "test-run-1")
        
        for result in sample_results:
            session.refresh(result)
            assert result.relevance_score == DEFAULT_SCORE

    def test_score_metadata_stored(self, session, sample_results):
        """Score metadata (scored_at, score_version) is stored."""
        now = datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
        outcome = score_run_results(session, "test-run-1", now=now)
        
        for result in sample_results:
            session.refresh(result)
            assert result.scored_at is not None
            assert result.score_version == DEFAULT_SCORE_VERSION
            assert result.scored_at == "2026-02-13T12:00:00Z"

    def test_skips_duplicate_results(self, session, sample_results, duplicate_result):
        """Duplicates are skipped and do not receive separate scores."""
        outcome = score_run_results(session, "test-run-1")
        
        assert outcome.scored_count == 2  # Only canonical records
        assert outcome.skipped_count == 1  # Duplicate skipped
        
        # Verify duplicate was not scored
        session.refresh(duplicate_result)
        assert duplicate_result.relevance_score is None

    def test_no_results_returns_zero_counts(self, session):
        """Returns zero counts when no unscored results exist."""
        outcome = score_run_results(session, "non-existent-run")
        
        assert outcome.scored_count == 0
        assert outcome.skipped_count == 0

    def test_only_processes_unscored_results(self, session, sample_results):
        """Only processes results without existing scores."""
        # Score once
        score_run_results(session, "test-run-1")
        
        # Score again - should find no unscored results
        outcome = score_run_results(session, "test-run-1")
        
        assert outcome.scored_count == 0
        assert outcome.skipped_count == 0

    def test_custom_score_version(self, session, sample_results):
        """Custom score version is stored."""
        custom_version = "v1.0.0"
        score_run_results(session, "test-run-1", score_version=custom_version)
        
        for result in sample_results:
            session.refresh(result)
            assert result.score_version == custom_version


class TestValidateScore:
    """Tests for the validate_score function."""

    def test_valid_scores_preserved(self):
        """Valid scores within range are preserved."""
        assert validate_score(0.0) == 0.0
        assert validate_score(0.5) == 0.5
        assert validate_score(-0.5) == -0.5
        assert validate_score(1.0) == 1.0
        assert validate_score(-1.0) == -1.0

    def test_high_scores_clamped(self):
        """Scores above 1.0 are clamped to 1.0."""
        assert validate_score(1.5) == 1.0
        assert validate_score(2.0) == 1.0
        assert validate_score(100.0) == 1.0

    def test_low_scores_clamped(self):
        """Scores below -1.0 are clamped to -1.0."""
        assert validate_score(-1.5) == -1.0
        assert validate_score(-2.0) == -1.0
        assert validate_score(-100.0) == -1.0


class TestGetCanonicalScore:
    """Tests for the get_canonical_score function."""

    def test_returns_canonical_score(self, session, sample_results):
        """Returns the score from the canonical record."""
        canonical = sample_results[0]
        canonical.relevance_score = 0.75
        session.commit()
        
        score = get_canonical_score(session, canonical.id)
        assert score == 0.75

    def test_returns_none_for_missing_record(self, session):
        """Returns None when canonical record not found."""
        score = get_canonical_score(session, 99999)
        assert score is None

    def test_returns_none_for_unscored_record(self, session, sample_results):
        """Returns None when canonical record has no score."""
        canonical = sample_results[0]
        score = get_canonical_score(session, canonical.id)
        assert score is None


class TestScoreRange:
    """Tests for score range constraints."""

    def test_min_score_constant(self):
        """MIN_SCORE is -1.0."""
        assert MIN_SCORE == -1.0

    def test_max_score_constant(self):
        """MAX_SCORE is 1.0."""
        assert MAX_SCORE == 1.0

    def test_default_score_constant(self):
        """DEFAULT_SCORE is 0.0."""
        assert DEFAULT_SCORE == 0.0

    def test_default_score_version_constant(self):
        """DEFAULT_SCORE_VERSION is 'baseline'."""
        assert DEFAULT_SCORE_VERSION == "baseline"
