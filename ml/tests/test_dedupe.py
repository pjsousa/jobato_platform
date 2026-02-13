"""Tests for deduplication pipeline."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, RunResult
from app.pipelines.dedupe import (
    dedupe_run_results,
    DedupeOutcome,
    _compute_jaccard_similarity,
    _compute_ngram_signature,
    _extract_comparable_text,
    _group_by_normalized_url,
    _process_url_groups,
    _find_similar_duplicates,
    DEFAULT_SIMILARITY_THRESHOLD,
)


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
def sample_results():
    """Create sample RunResult objects for testing."""
    base_time = datetime.now(timezone.utc).isoformat()
    
    return [
        RunResult(
            id=1,
            run_id="test-run-1",
            query_id="q1",
            query_text="python developer",
            search_query="site:example.com python developer",
            domain="example.com",
            title="Python Developer Job",
            snippet="Looking for a Python developer",
            raw_url="https://example.com/job/123",
            final_url="https://example.com/job/123",
            created_at=base_time,
            updated_at=base_time,
            normalized_url="abc123hash",
            visible_text="We are looking for a Python developer with 3+ years experience.",
        ),
        RunResult(
            id=2,
            run_id="test-run-1",
            query_id="q1",
            query_text="python developer",
            search_query="site:example.com python developer",
            domain="example.com",
            title="Python Developer Position",
            snippet="Python developer position available",
            raw_url="https://example.com/job/123?utm_source=google",
            final_url="https://example.com/job/123",
            created_at=base_time,
            updated_at=base_time,
            normalized_url="abc123hash",  # Same as first result
            visible_text="We are looking for a Python developer with 3+ years experience.",
        ),
        RunResult(
            id=3,
            run_id="test-run-1",
            query_id="q2",
            query_text="senior python",
            search_query="site:example.com senior python",
            domain="example.com",
            title="Senior Python Engineer",
            snippet="Senior Python engineer needed",
            raw_url="https://example.com/job/456",
            final_url="https://example.com/job/456",
            created_at=base_time,
            updated_at=base_time,
            normalized_url="def456hash",  # Different URL
            visible_text="Senior Python engineer with 5+ years experience required.",
        ),
    ]


class TestDedupeRunResults:
    """Test cases for the main dedupe_run_results function."""

    def test_no_results_returns_zero_counts(self, db_session):
        """Test that dedupe with no results returns zero counts."""
        outcome = dedupe_run_results(db_session, "non-existent-run")
        
        assert outcome.duplicates_found == 0
        assert outcome.canonical_count == 0
        assert outcome.exact_duplicates == 0
        assert outcome.similar_duplicates == 0

    def test_exact_url_duplicates_detected(self, db_session, sample_results):
        """Test that exact URL duplicates are detected and linked."""
        # Add results to database
        db_session.add_all(sample_results[:2])  # First two have same normalized_url
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run-1")
        
        # Refresh results from database
        results = db_session.query(RunResult).all()
        
        # First result (lowest id) should be canonical
        canonical = next(r for r in results if r.id == 1)
        assert canonical.is_duplicate == False
        assert canonical.is_hidden == False
        assert canonical.canonical_id is None
        assert canonical.duplicate_count == 1
        
        # Second result should be marked as duplicate
        duplicate = next(r for r in results if r.id == 2)
        assert duplicate.is_duplicate == True
        assert duplicate.is_hidden == True
        assert duplicate.canonical_id == 1
        
        assert outcome.duplicates_found == 1
        assert outcome.exact_duplicates == 1
        assert outcome.similar_duplicates == 0
        assert outcome.canonical_count == 1

    def test_different_urls_not_marked_duplicates(self, db_session, sample_results):
        """Test that results with different URLs are not marked as duplicates."""
        db_session.add_all([sample_results[0], sample_results[2]])
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run-1")
        
        results = db_session.query(RunResult).all()
        
        for result in results:
            assert result.is_duplicate == False
            assert result.is_hidden == False
            assert result.canonical_id is None
        
        assert outcome.duplicates_found == 0
        assert outcome.canonical_count == 2

    def test_text_similarity_detects_near_duplicates(self, db_session):
        """Test that text similarity detects near-duplicate content."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            RunResult(
                id=1,
                run_id="test-run-1",
                query_id="q1",
                query_text="python developer",
                search_query="site:example.com python developer",
                domain="example.com",
                title="Python Developer",
                snippet="We are hiring a Python developer. Must have 3+ years experience with Django and Flask.",
                raw_url="https://example.com/job/1",
                final_url="https://example.com/job/1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                visible_text="We are hiring a Python developer. Must have 3+ years experience with Django and Flask.",
            ),
            RunResult(
                id=2,
                run_id="test-run-1",
                query_id="q1",
                query_text="python developer",
                search_query="site:example.com python developer",
                domain="example.com",
                title="Python Developer",
                snippet="We are hiring a Python developer. Must have 3+ years experience with Django and Flask.",
                raw_url="https://example.com/job/2",
                final_url="https://example.com/job/2",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash2",  # Different URL
                visible_text="We are hiring a Python developer. Must have 3+ years experience with Django and Flask.",
            ),
        ]
        
        db_session.add_all(results)
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run-1")
        
        # Refresh results
        db_results = db_session.query(RunResult).all()
        
        # One should be canonical, one should be duplicate
        canonical = next(r for r in db_results if r.is_duplicate == False)
        duplicate = next(r for r in db_results if r.is_duplicate == True)
        
        assert duplicate.canonical_id == canonical.id
        assert duplicate.is_hidden == True
        assert outcome.similar_duplicates == 1

    def test_already_duplicate_results_excluded(self, db_session):
        """Test that already marked duplicates are excluded from reprocessing."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            RunResult(
                id=1,
                run_id="test-run-1",
                query_id="q1",
                query_text="test",
                search_query="site:example.com test",
                domain="example.com",
                title="Test Job 1",
                snippet="Test snippet",
                raw_url="https://example.com/job/1",
                final_url="https://example.com/job/1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                is_duplicate=False,
            ),
            RunResult(
                id=2,
                run_id="test-run-1",
                query_id="q1",
                query_text="test",
                search_query="site:example.com test",
                domain="example.com",
                title="Test Job 2",
                snippet="Test snippet 2",
                raw_url="https://example.com/job/2",
                final_url="https://example.com/job/2",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                is_duplicate=True,  # Already marked
                canonical_id=1,
                is_hidden=True,
            ),
        ]
        
        db_session.add_all(results)
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run-1")
        
        # Should not find any new duplicates
        assert outcome.duplicates_found == 0

    def test_empty_normalized_url_skipped(self, db_session):
        """Test that results without normalized_url are handled gracefully."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        result = RunResult(
            id=1,
            run_id="test-run-1",
            query_id="q1",
            query_text="test",
            search_query="site:example.com test",
            domain="example.com",
            title="Test Job",
            snippet="Test snippet",
            raw_url="https://example.com/job/1",
            final_url="https://example.com/job/1",
            created_at=base_time,
            updated_at=base_time,
            normalized_url=None,
            visible_text="Some job description text here.",
        )
        
        db_session.add(result)
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run-1")
        
        # Should complete without errors
        assert outcome.duplicates_found == 0
        assert outcome.canonical_count == 1  # Single result with no duplicates


class TestGroupByNormalizedUrl:
    """Test cases for _group_by_normalized_url function."""

    def test_groups_by_normalized_url(self, sample_results):
        """Test that results are correctly grouped by normalized_url."""
        groups = _group_by_normalized_url(sample_results)
        
        assert "abc123hash" in groups
        assert "def456hash" in groups
        assert len(groups["abc123hash"]) == 2
        assert len(groups["def456hash"]) == 1

    def test_empty_normalized_url_excluded(self, sample_results):
        """Test that results without normalized_url are excluded."""
        sample_results[0].normalized_url = None
        
        groups = _group_by_normalized_url(sample_results)
        
        assert len(groups) == 2  # Only 2 unique normalized_urls remain

    def test_empty_list_returns_empty_dict(self):
        """Test that empty list returns empty dict."""
        groups = _group_by_normalized_url([])
        
        assert groups == {}


class TestProcessUrlGroups:
    """Test cases for _process_url_groups function."""

    def test_single_result_per_url_not_duplicate(self, db_session, sample_results):
        """Test that single results per URL are not marked duplicates."""
        groups = {"hash1": [sample_results[2]]}  # Only one result
        
        duplicates = _process_url_groups(db_session, groups)
        
        assert len(duplicates) == 0
        # When single result in group, is_duplicate is not set (remains None or 0)
        assert sample_results[2].is_duplicate == False or sample_results[2].is_duplicate is None

    def test_multiple_results_mark_duplicates(self, db_session, sample_results):
        """Test that multiple results per URL mark duplicates correctly."""
        # Create two results with same URL but different IDs
        r1 = sample_results[0]  # id=1
        r2 = sample_results[1]  # id=2
        r1.normalized_url = "samehash"
        r2.normalized_url = "samehash"
        
        groups = {"samehash": [r1, r2]}
        
        duplicates = _process_url_groups(db_session, groups)
        
        assert len(duplicates) == 1
        assert r1.is_duplicate is False  # First (lowest id) is canonical
        assert r2.is_duplicate is True
        assert r2.canonical_id == r1.id
        assert r1.duplicate_count == 1


class TestComputeJaccardSimilarity:
    """Test cases for Jaccard similarity computation."""

    def test_identical_sets_have_similarity_one(self):
        """Test that identical sets have similarity of 1.0."""
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        
        similarity = _compute_jaccard_similarity(set1, set2)
        
        assert similarity == 1.0

    def test_disjoint_sets_have_similarity_zero(self):
        """Test that disjoint sets have similarity of 0.0."""
        set1 = {"a", "b", "c"}
        set2 = {"x", "y", "z"}
        
        similarity = _compute_jaccard_similarity(set1, set2)
        
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Test partial overlap between sets."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # Intersection: {b, c} = 2
        # Union: {a, b, c, d} = 4
        # Similarity: 2/4 = 0.5
        
        similarity = _compute_jaccard_similarity(set1, set2)
        
        assert similarity == 0.5

    def test_empty_sets(self):
        """Test handling of empty sets."""
        assert _compute_jaccard_similarity(set(), set()) == 1.0
        assert _compute_jaccard_similarity(set(), {"a"}) == 0.0
        assert _compute_jaccard_similarity({"a"}, set()) == 0.0


class TestComputeNgramSignature:
    """Test cases for n-gram signature computation."""

    def test_basic_ngrams(self):
        """Test basic n-gram generation."""
        text = "the quick brown fox"
        signature = _compute_ngram_signature(text, n=2)
        
        expected = {"the quick", "quick brown", "brown fox"}
        assert signature == expected

    def test_text_normalization(self):
        """Test that text is normalized (lowercased, whitespace)."""
        text = "  The   QUICK   Brown  Fox  "
        signature = _compute_ngram_signature(text, n=2)
        
        expected = {"the quick", "quick brown", "brown fox"}
        assert signature == expected

    def test_single_word(self):
        """Test handling of single word text."""
        text = "hello"
        signature = _compute_ngram_signature(text, n=2)
        
        assert signature == set()  # Not enough words for bigrams

    def test_empty_text(self):
        """Test handling of empty text."""
        assert _compute_ngram_signature("") == set()
        assert _compute_ngram_signature("   ") == set()


class TestExtractComparableText:
    """Test cases for text extraction."""

    def test_extracts_all_fields(self, sample_results):
        """Test that all text fields are extracted."""
        result = sample_results[0]
        text = _extract_comparable_text(result)
        
        assert result.title in text
        assert result.snippet in text
        assert result.visible_text in text

    def test_handles_missing_fields(self):
        """Test handling of missing fields."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        result = RunResult(
            id=1,
            run_id="test",
            query_id="q1",
            query_text="test",
            search_query="test",
            domain="example.com",
            title="Title Only",
            snippet="",
            raw_url="url",
            final_url="url",
            created_at=base_time,
            updated_at=base_time,
            visible_text=None,
        )
        
        text = _extract_comparable_text(result)
        
        assert "Title Only" in text
        assert "  " not in text  # No double spaces from empty fields


class TestFindSimilarDuplicates:
    """Test cases for text similarity duplicate detection."""

    def test_identical_text_detected(self, db_session):
        """Test that identical text is detected as duplicate."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            RunResult(
                id=1,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Same Title",
                snippet="Same snippet",
                raw_url="url1",
                final_url="url1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                visible_text="This is exactly the same job description.",
            ),
            RunResult(
                id=2,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Same Title",
                snippet="Same snippet",
                raw_url="url2",
                final_url="url2",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash2",
                visible_text="This is exactly the same job description.",
            ),
        ]
        
        duplicates = _find_similar_duplicates(db_session, results, 0.90)
        
        assert len(duplicates) == 1
        assert duplicates[0].id == 2  # Second result is duplicate

    def test_different_text_not_duplicate(self, db_session):
        """Test that different text is not marked as duplicate."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            RunResult(
                id=1,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Python Developer",
                snippet="Python job",
                raw_url="url1",
                final_url="url1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                visible_text="Python developer with Django experience needed.",
            ),
            RunResult(
                id=2,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Java Developer",
                snippet="Java job",
                raw_url="url2",
                final_url="url2",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash2",
                visible_text="Java developer with Spring experience needed.",
            ),
        ]
        
        duplicates = _find_similar_duplicates(db_session, results, 0.90)
        
        assert len(duplicates) == 0

    def test_threshold_affects_detection(self, db_session):
        """Test that similarity threshold affects duplicate detection."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            RunResult(
                id=1,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Developer",
                snippet="Job",
                raw_url="url1",
                final_url="url1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                visible_text="Python developer job requirements experience skills",
            ),
            RunResult(
                id=2,
                run_id="test",
                query_id="q1",
                query_text="test",
                search_query="test",
                domain="example.com",
                title="Developer",
                snippet="Position",
                raw_url="url2",
                final_url="url2",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash2",
                visible_text="Python developer position requirements experience skills",
            ),
        ]
        
        # With high threshold, might not be detected
        duplicates_high = _find_similar_duplicates(db_session, results, 0.95)
        
        # With lower threshold, should be detected
        duplicates_low = _find_similar_duplicates(db_session, results, 0.70)
        
        # The exact counts depend on the similarity score
        assert len(duplicates_high) <= len(duplicates_low)


class TestDedupeOutcome:
    """Test cases for DedupeOutcome dataclass."""

    def test_basic_outcome(self):
        """Test basic outcome creation."""
        outcome = DedupeOutcome(
            duplicates_found=5,
            canonical_count=10,
            exact_duplicates=3,
            similar_duplicates=2,
        )
        
        assert outcome.duplicates_found == 5
        assert outcome.canonical_count == 10
        assert outcome.exact_duplicates == 3
        assert outcome.similar_duplicates == 2

    def test_default_values(self):
        """Test default values for optional fields."""
        outcome = DedupeOutcome(
            duplicates_found=0,
            canonical_count=5,
        )
        
        assert outcome.exact_duplicates == 0
        assert outcome.similar_duplicates == 0


class TestIntegrationScenarios:
    """Integration test scenarios."""

    def test_complex_dedupe_scenario(self, db_session):
        """Test a complex scenario with both exact and similar duplicates."""
        base_time = datetime.now(timezone.utc).isoformat()
        
        results = [
            # Exact duplicates (same URL)
            RunResult(
                id=1,
                run_id="test-run",
                query_id="q1",
                query_text="python",
                search_query="site:example.com python",
                domain="example.com",
                title="Python Job",
                snippet="Python developer",
                raw_url="https://example.com/job/1",
                final_url="https://example.com/job/1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",
                visible_text="Python developer job.",
            ),
            RunResult(
                id=2,
                run_id="test-run",
                query_id="q1",
                query_text="python",
                search_query="site:example.com python",
                domain="example.com",
                title="Python Job Duplicate",
                snippet="Python developer duplicate",
                raw_url="https://example.com/job/1?source=google",
                final_url="https://example.com/job/1",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash1",  # Same as id=1
                visible_text="Python developer job.",
            ),
            # Similar content (different URL)
            RunResult(
                id=3,
                run_id="test-run",
                query_id="q1",
                query_text="python",
                search_query="site:example.com python",
                domain="example.com",
                title="Python Developer Hiring",
                snippet="We are hiring a Python developer for our team.",
                raw_url="https://example.com/job/3",
                final_url="https://example.com/job/3",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash3",
                visible_text="We are hiring a Python developer for our team.",
            ),
            RunResult(
                id=4,
                run_id="test-run",
                query_id="q1",
                query_text="python",
                search_query="site:example.com python",
                domain="example.com",
                title="Python Developer Hiring",
                snippet="We are hiring a Python developer for our team.",
                raw_url="https://example.com/job/4",
                final_url="https://example.com/job/4",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash4",
                visible_text="We are hiring a Python developer for our team.",
            ),
            # Unique result
            RunResult(
                id=5,
                run_id="test-run",
                query_id="q2",
                query_text="java",
                search_query="site:example.com java",
                domain="example.com",
                title="Java Developer",
                snippet="Java position",
                raw_url="https://example.com/job/5",
                final_url="https://example.com/job/5",
                created_at=base_time,
                updated_at=base_time,
                normalized_url="hash5",
                visible_text="Java developer with Spring experience.",
            ),
        ]
        
        db_session.add_all(results)
        db_session.commit()
        
        outcome = dedupe_run_results(db_session, "test-run")
        
        # Refresh all results
        db_results = {r.id: r for r in db_session.query(RunResult).all()}
        
        # Check exact duplicates
        assert db_results[1].is_duplicate == False  # Canonical
        assert db_results[1].duplicate_count == 1
        assert db_results[2].is_duplicate == True
        assert db_results[2].canonical_id == 1
        
        # Check similar duplicates
        # One of id=3 or id=4 should be canonical, other duplicate
        similar_results = [db_results[3], db_results[4]]
        canonical_similar = next(r for r in similar_results if r.is_duplicate == False)
        duplicate_similar = next(r for r in similar_results if r.is_duplicate == True)
        assert duplicate_similar.canonical_id == canonical_similar.id
        
        # Check unique result
        assert db_results[5].is_duplicate == False
        assert db_results[5].canonical_id is None
        
        # Verify counts
        assert outcome.duplicates_found == 2  # 1 exact + 1 similar
        assert outcome.exact_duplicates == 1
        assert outcome.similar_duplicates == 1
        assert outcome.canonical_count == 3  # 5 total - 2 duplicates
