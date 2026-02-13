"""Integration tests for scoring in the ingestion pipeline."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, RunResult
from app.pipelines.ingestion import ingest_run, IngestionOutcome, RunInput
from app.pipelines.dedupe import DedupeOutcome
from app.pipelines.scoring import ScoringOutcome
from app.schemas.results import SearchResultItem


class MockSearchClient:
    """Mock search client for testing."""
    
    def __init__(self, results: list[SearchResultItem]):
        self._results = results
    
    def search(self, *, run_id: str, search_query: str) -> list[SearchResultItem]:
        return self._results


class MockUrlResolver:
    """Mock URL resolver for testing."""
    
    def __init__(self, status_code: int = 200, final_url: str | None = None):
        self._status_code = status_code
        self._final_url = final_url
    
    def resolve(self, url: str):
        class Resolved:
            def __init__(self, status_code, final_url):
                self.status_code = status_code
                self.final_url = final_url
        return Resolved(self._status_code, self._final_url or url)


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test.db"


@pytest.fixture
def data_dir(tmp_path):
    """Create a temporary data directory."""
    return tmp_path


@pytest.fixture
def session(temp_db_path):
    """Create a database session for testing."""
    engine = create_engine(f"sqlite:///{temp_db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def get_run_db_path(data_dir: Path, run_id: str) -> Path:
    """Get the path to a run's database file."""
    return data_dir / "db" / "runs" / f"{run_id}.db"


@pytest.fixture
def run_inputs():
    """Create sample run inputs."""
    return [
        RunInput(
            query_id="q1",
            query_text="python developer",
            domain="example.com",
            search_query="site:example.com python developer",
        ),
        RunInput(
            query_id="q2",
            query_text="java engineer",
            domain="example.com",
            search_query="site:example.com java engineer",
        ),
    ]


class TestIngestionWithScoring:
    """Tests for ingestion pipeline with scoring integration."""

    def test_scoring_runs_after_dedupe(self, data_dir, run_inputs):
        """Scoring runs after deduplication in the ingestion pipeline."""
        search_results = [
            SearchResultItem(
                title="Python Developer",
                snippet="Great Python job",
                link="https://example.com/job1",
                display_link="example.com",
            ),
            SearchResultItem(
                title="Java Engineer",
                snippet="Great Java job",
                link="https://example.com/job2",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-run-1",
            run_inputs=run_inputs[:1],  # Just one input for simplicity
            search_client=MockSearchClient(search_results[:1]),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify both dedupe and scoring ran
        assert outcome.dedupe_outcome is not None
        assert outcome.scoring_outcome is not None
        assert outcome.scoring_outcome.scored_count > 0

    def test_scoring_can_be_disabled(self, data_dir, run_inputs):
        """Scoring can be disabled via parameter."""
        search_results = [
            SearchResultItem(
                title="Python Developer",
                snippet="Great Python job",
                link="https://example.com/job1",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-run-2",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=False,  # Disable scoring
        )
        
        # Verify scoring did not run
        assert outcome.scoring_outcome is None

    def test_scores_stored_in_database(self, data_dir, run_inputs):
        """Scores are stored in the database after ingestion."""
        search_results = [
            SearchResultItem(
                title="Python Developer",
                snippet="Great Python job",
                link="https://example.com/job1",
                display_link="example.com",
            ),
        ]
        
        ingest_run(
            run_id="test-run-3",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify scores in database (ingestion creates db at data_dir/db/runs/{run_id}.db)
        db_path = get_run_db_path(data_dir, "test-run-3")
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            results = session.query(RunResult).filter_by(run_id="test-run-3").all()
            assert len(results) > 0
            
            for result in results:
                if not result.is_duplicate:
                    assert result.relevance_score is not None
                    assert result.scored_at is not None
                    assert result.score_version is not None
        finally:
            session.close()

    def test_duplicate_inheritance_behavior(self, data_dir, run_inputs):
        """Duplicates do not receive separate scores but inherit from canonical."""
        # Create two identical search results that will be deduplicated
        search_results = [
            SearchResultItem(
                title="Same Job",
                snippet="Same description",
                link="https://example.com/same-job",
                display_link="example.com",
            ),
            SearchResultItem(
                title="Same Job",
                snippet="Same description",
                link="https://example.com/same-job-dup",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-run-4",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify scoring outcome reflects duplicate skipping
        assert outcome.scoring_outcome is not None
        assert outcome.scoring_outcome.skipped_count > 0

    def test_scoring_outcome_structure(self, data_dir, run_inputs):
        """Scoring outcome contains expected fields."""
        search_results = [
            SearchResultItem(
                title="Python Developer",
                snippet="Great Python job",
                link="https://example.com/job1",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-run-5",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify outcome structure
        assert isinstance(outcome, IngestionOutcome)
        assert hasattr(outcome, 'scoring_outcome')
        assert outcome.scoring_outcome is not None
        assert hasattr(outcome.scoring_outcome, 'scored_count')
        assert hasattr(outcome.scoring_outcome, 'skipped_count')
        assert outcome.scoring_outcome.scored_count >= 0
        assert outcome.scoring_outcome.skipped_count >= 0

    def test_score_range_in_integration(self, data_dir, run_inputs):
        """All scores stored are within the valid range [-1, 1]."""
        search_results = [
            SearchResultItem(
                title=f"Job {i}",
                snippet=f"Description {i}",
                link=f"https://example.com/job{i}",
                display_link="example.com",
            )
            for i in range(5)
        ]
        
        ingest_run(
            run_id="test-run-6",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify score range in database
        db_path = get_run_db_path(data_dir, "test-run-6")
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            results = session.query(RunResult).filter_by(run_id="test-run-6").all()
            
            for result in results:
                if result.relevance_score is not None:
                    assert -1.0 <= result.relevance_score <= 1.0
        finally:
            session.close()

    def test_baseline_score_in_integration(self, data_dir, run_inputs):
        """Baseline scoring assigns default score of 0."""
        search_results = [
            SearchResultItem(
                title="Python Developer",
                snippet="Great Python job",
                link="https://example.com/job1",
                display_link="example.com",
            ),
        ]
        
        ingest_run(
            run_id="test-run-7",
            run_inputs=run_inputs[:1],
            search_client=MockSearchClient(search_results),
            url_resolver=MockUrlResolver(),
            data_dir=data_dir,
            dedupe_enabled=True,
            scoring_enabled=True,
        )
        
        # Verify baseline scores in database
        db_path = get_run_db_path(data_dir, "test-run-7")
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            results = session.query(RunResult).filter_by(run_id="test-run-7").all()
            
            for result in results:
                if not result.is_duplicate and result.relevance_score is not None:
                    assert result.relevance_score == 0.0
                    assert result.score_version == "baseline"
        finally:
            session.close()
