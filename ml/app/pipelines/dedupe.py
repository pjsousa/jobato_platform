"""Deduplication pipeline for detecting and linking duplicate results."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models import RunResult
from app.services.url_normalizer import normalize_url

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Default similarity threshold for text-based deduplication
DEFAULT_SIMILARITY_THRESHOLD = 0.90


def dedupe_run_results(
    session: Session,
    run_id: str,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> DedupeOutcome:
    """Run deduplication on all results for a given run.
    
    Two-phase approach:
    1. Exact URL matching using normalized_url
    2. Text similarity matching for near-duplicates
    
    First occurrence is always the canonical record.
    
    Args:
        session: Database session
        run_id: The run ID to dedupe
        similarity_threshold: Threshold for text similarity (0.0 to 1.0)
        
    Returns:
        DedupeOutcome with statistics about deduplication
    """
    # Fetch all non-duplicate results for this run
    # Include both False (0) and NULL values since new records have is_duplicate=NULL
    results = session.execute(
        select(RunResult).where(
            RunResult.run_id == run_id,
            (RunResult.is_duplicate == False) | (RunResult.is_duplicate.is_(None)),
        )
    ).scalars().all()
    
    if not results:
        logger.info("dedupe.no_results run_id=%s", run_id)
        return DedupeOutcome(duplicates_found=0, canonical_count=0)
    
    logger.info("dedupe.start run_id=%s count=%d", run_id, len(results))
    
    # Phase 1: Exact URL matching by normalized_url
    url_groups = _group_by_normalized_url(results)
    exact_duplicates = _process_url_groups(session, url_groups)
    
    # Refresh results list to exclude already-marked duplicates
    remaining_results = [
        r for r in results 
        if r.id not in {d.id for d in exact_duplicates}
    ]
    
    # Phase 2: Text similarity matching
    similar_duplicates = _find_similar_duplicates(
        session, remaining_results, similarity_threshold
    )
    
    # Commit all changes
    session.commit()
    
    total_duplicates = len(exact_duplicates) + len(similar_duplicates)
    canonical_count = len(results) - total_duplicates
    
    logger.info(
        "dedupe.complete run_id=%s exact=%d similar=%d canonical=%d",
        run_id, len(exact_duplicates), len(similar_duplicates), canonical_count
    )
    
    return DedupeOutcome(
        duplicates_found=total_duplicates,
        canonical_count=canonical_count,
        exact_duplicates=len(exact_duplicates),
        similar_duplicates=len(similar_duplicates),
    )


def _group_by_normalized_url(results: list[RunResult]) -> dict[str, list[RunResult]]:
    """Group results by their normalized URL."""
    groups: dict[str, list[RunResult]] = defaultdict(list)
    for result in results:
        if result.normalized_url:
            groups[result.normalized_url].append(result)
    return groups


def _process_url_groups(
    session: Session,
    url_groups: dict[str, list[RunResult]],
) -> list[RunResult]:
    """Process URL groups and mark duplicates."""
    duplicates: list[RunResult] = []
    
    for normalized_url, group in url_groups.items():
        if len(group) <= 1:
            continue
        
        # First occurrence is canonical
        canonical = min(group, key=lambda r: r.id)
        group_duplicates = [r for r in group if r.id != canonical.id]
        
        # Update canonical record
        canonical.duplicate_count = len(group_duplicates)
        canonical.is_duplicate = False
        canonical.is_hidden = False
        
        # Mark duplicates
        for dup in group_duplicates:
            dup.canonical_id = canonical.id
            dup.is_duplicate = True
            dup.is_hidden = True
            duplicates.append(dup)
        
        logger.debug(
            "dedupe.url_match normalized_url=%s canonical_id=%d duplicates=%d",
            normalized_url, canonical.id, len(group_duplicates)
        )
    
    return duplicates


def _find_similar_duplicates(
    session: Session,
    results: list[RunResult],
    threshold: float,
) -> list[RunResult]:
    """Find duplicates based on text similarity.
    
    Uses Jaccard similarity on n-grams for efficient comparison.
    """
    if len(results) < 2:
        return []
    
    duplicates: list[RunResult] = []
    processed: set[int] = set()
    
    # Pre-compute text signatures for all results
    signatures = {}
    for result in results:
        text = _extract_comparable_text(result)
        if text:
            signatures[result.id] = _compute_ngram_signature(text)
    
    # Compare each result with others
    for i, result1 in enumerate(results):
        if result1.id in processed:
            continue
        
        sig1 = signatures.get(result1.id)
        if not sig1:
            continue
        
        similar_results: list[RunResult] = []
        
        for result2 in results[i + 1:]:
            if result2.id in processed:
                continue
            
            sig2 = signatures.get(result2.id)
            if not sig2:
                continue
            
            similarity = _compute_jaccard_similarity(sig1, sig2)
            
            if similarity >= threshold:
                similar_results.append(result2)
                processed.add(result2.id)
        
        if similar_results:
            # result1 is the canonical record (first seen)
            result1.duplicate_count = len(similar_results)
            result1.is_duplicate = False
            result1.is_hidden = False
            
            # Mark similar results as duplicates
            for dup in similar_results:
                dup.canonical_id = result1.id
                dup.is_duplicate = True
                dup.is_hidden = True
                duplicates.append(dup)
            
            logger.debug(
                "dedupe.similar_match canonical_id=%d duplicates=%d",
                result1.id, len(similar_results)
            )
    
    return duplicates


def _extract_comparable_text(result: RunResult) -> str:
    """Extract text for similarity comparison."""
    parts = []
    if result.title:
        parts.append(result.title)
    if result.snippet:
        parts.append(result.snippet)
    if result.visible_text:
        parts.append(result.visible_text)
    return " ".join(parts)


def _compute_ngram_signature(text: str, n: int = 3) -> set[str]:
    """Compute n-gram signature for text."""
    # Normalize text: lowercase, remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    
    # Generate n-grams
    ngrams = set()
    words = normalized.split()
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i + n])
        ngrams.add(ngram)
    
    return ngrams


def _compute_jaccard_similarity(set1: set, set2: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


@dataclass(frozen=True)
class DedupeOutcome:
    """Outcome of deduplication process."""
    duplicates_found: int
    canonical_count: int
    exact_duplicates: int = 0
    similar_duplicates: int = 0
