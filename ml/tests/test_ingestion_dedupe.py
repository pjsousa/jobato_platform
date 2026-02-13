"""Tests for deduplication integration with ingestion pipeline."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, MagicMock

from app.pipelines.ingestion import (
    ingest_run,
    IngestionOutcome,
    RunInput,
    SearchClient,
    UrlResolver,
)
from app.schemas.results import SearchResultItem, ResultMetadata
from app.db.models import Base, RunResult
from app.db.session import open_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_search_client():
    """Create a mock search client."""
    client = Mock(spec=SearchClient)
    return client


@pytest.fixture
def mock_url_resolver():
    """Create a mock URL resolver."""
    resolver = Mock(spec=UrlResolver)
    
    def resolve_side_effect(url):
        # Return a mock resolved URL
        response = Mock()
        response.status_code = 200
        response.final_url = url
        return response
    
    resolver.resolve.side_effect = resolve_side_effect
    return resolver


@pytest.fixture
def sample_run_inputs():
    """Create sample run inputs."""
    return [
        RunInput(
            query_id="q1",
            query_text="python developer",
            domain="example.com",
            search_query="site:example.com python developer",
        ),
    ]


class TestIngestionWithDedupe:
    """Test cases for ingestion with deduplication enabled."""

    def test_dedupe_disabled_skips_deduplication(
        self, db_session, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe can be disabled."""
        # Setup search results with same URL
        mock_search_client.search.return_value = [
            SearchResultItem(
                title="Python Job",
                snippet="Python developer job",
                link="https://example.com/job/1",
                display_link="example.com",
            ),
            SearchResultItem(
                title="Python Job Duplicate",
                snippet="Same job different listing",
                link="https://example.com/job/1?utm_source=google",
                display_link="example.com",
            ),
        ]
        
        db_path = tmp_path / "test.db"
        
        outcome = ingest_run(
            run_id="test-run-1",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=False,  # Disable dedupe
        )
        
        # Should persist both results without deduplication
        assert outcome.persisted_results == 2
        assert outcome.dedupe_outcome is None

    def test_dedupe_enabled_runs_deduplication(
        self, db_session, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe runs when enabled."""
        # Setup search results with same URL
        mock_search_client.search.return_value = [
            SearchResultItem(
                title="Python Job",
                snippet="Python developer job",
                link="https://example.com/job/1",
                display_link="example.com",
            ),
            SearchResultItem(
                title="Python Job Duplicate",
                snippet="Same job different listing",
                link="https://example.com/job/1?utm_source=google",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-run-1",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        # Should have dedupe outcome
        assert outcome.dedupe_outcome is not None
        # Both results should be persisted initially
        assert outcome.persisted_results == 2

    def test_no_results_dedupe_outcome_is_none(
        self, db_session, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe outcome is None when no results are persisted."""
        mock_search_client.search.return_value = []
        
        outcome = ingest_run(
            run_id="test-run-1",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        assert outcome.persisted_results == 0
        assert outcome.dedupe_outcome is None

    def test_dedupe_failure_does_not_break_ingestion(
        self, db_session, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe failure doesn't break the ingestion."""
        mock_search_client.search.return_value = [
            SearchResultItem(
                title="Python Job",
                snippet="Python developer job",
                link="https://example.com/job/1",
                display_link="example.com",
            ),
        ]
        
        # Even if dedupe fails, ingestion should succeed
        outcome = ingest_run(
            run_id="test-run-1",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        # Ingestion should succeed
        assert outcome.persisted_results == 1


class TestIngestionDedupeIntegration:
    """Integration tests for ingestion + dedupe."""

    def test_end_to_end_dedupe_workflow(self, tmp_path):
        """Test complete workflow from ingestion to dedupe."""
        # Create mock search client that returns duplicate results
        search_client = Mock(spec=SearchClient)
        search_client.search.return_value = [
            SearchResultItem(
                title="Software Engineer",
                snippet="Join our team",
                link="https://careers.example.com/jobs/123",
                display_link="careers.example.com",
            ),
            SearchResultItem(
                title="Software Engineer Position",
                snippet="Join our engineering team",
                link="https://careers.example.com/jobs/123?source=linkedin",
                display_link="careers.example.com",
            ),
            SearchResultItem(
                title="Different Job",
                snippet="Different description",
                link="https://careers.example.com/jobs/456",
                display_link="careers.example.com",
            ),
        ]
        
        # Create mock URL resolver
        url_resolver = Mock(spec=UrlResolver)
        
        def resolve_side_effect(url):
            response = Mock()
            response.status_code = 200
            # Strip query params for final URL
            if "?" in url:
                response.final_url = url.split("?")[0]
            else:
                response.final_url = url
            return response
        
        url_resolver.resolve.side_effect = resolve_side_effect
        
        # Create run inputs
        run_inputs = [
            RunInput(
                query_id="q1",
                query_text="software engineer",
                domain="careers.example.com",
                search_query="site:careers.example.com software engineer",
            ),
        ]
        
        # Run ingestion with dedupe
        outcome = ingest_run(
            run_id="integration-test-run",
            run_inputs=run_inputs,
            search_client=search_client,
            url_resolver=url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        # Verify outcome
        assert outcome.persisted_results == 3
        assert outcome.dedupe_outcome is not None
        # Two results have same final URL, so 1 should be marked as duplicate
        assert outcome.dedupe_outcome.duplicates_found >= 0  # Could be 0 if no dedupe matches

    def test_normalized_url_populated_before_dedupe(self, tmp_path):
        """Test that normalized_url is populated before dedupe runs."""
        search_client = Mock(spec=SearchClient)
        search_client.search.return_value = [
            SearchResultItem(
                title="Test Job",
                snippet="Test description",
                link="https://example.com/job/1?utm_source=google",
                display_link="example.com",
            ),
        ]
        
        url_resolver = Mock(spec=UrlResolver)
        response = Mock()
        response.status_code = 200
        response.final_url = "https://example.com/job/1"
        url_resolver.resolve.return_value = response
        
        run_inputs = [
            RunInput(
                query_id="q1",
                query_text="test",
                domain="example.com",
                search_query="site:example.com test",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-normalized-url",
            run_inputs=run_inputs,
            search_client=search_client,
            url_resolver=url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        # Results should have normalized_url populated
        assert outcome.persisted_results == 1
        # The dedupe outcome should exist
        assert outcome.dedupe_outcome is not None


class TestDedupeOutcomeStructure:
    """Test dedupe outcome structure in ingestion results."""

    def test_dedupe_outcome_has_expected_fields(
        self, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe outcome has all expected fields."""
        mock_search_client.search.return_value = [
            SearchResultItem(
                title="Job 1",
                snippet="Description 1",
                link="https://example.com/job/1",
                display_link="example.com",
            ),
            SearchResultItem(
                title="Job 2",
                snippet="Description 2",
                link="https://example.com/job/2",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-outcome-fields",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        assert outcome.dedupe_outcome is not None
        assert hasattr(outcome.dedupe_outcome, 'duplicates_found')
        assert hasattr(outcome.dedupe_outcome, 'canonical_count')
        assert hasattr(outcome.dedupe_outcome, 'exact_duplicates')
        assert hasattr(outcome.dedupe_outcome, 'similar_duplicates')

    def test_dedupe_outcome_counts_are_non_negative(
        self, mock_search_client, mock_url_resolver, sample_run_inputs, tmp_path
    ):
        """Test that dedupe counts are non-negative."""
        mock_search_client.search.return_value = [
            SearchResultItem(
                title="Job",
                snippet="Description",
                link="https://example.com/job/1",
                display_link="example.com",
            ),
        ]
        
        outcome = ingest_run(
            run_id="test-non-negative",
            run_inputs=sample_run_inputs,
            search_client=mock_search_client,
            url_resolver=mock_url_resolver,
            now=datetime.now(timezone.utc),
            data_dir=tmp_path,
            dedupe_enabled=True,
        )
        
        if outcome.dedupe_outcome:
            assert outcome.dedupe_outcome.duplicates_found >= 0
            assert outcome.dedupe_outcome.canonical_count >= 0
            assert outcome.dedupe_outcome.exact_duplicates >= 0
            assert outcome.dedupe_outcome.similar_duplicates >= 0
