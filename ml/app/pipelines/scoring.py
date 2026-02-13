"""Scoring pipeline for assigning relevance scores to results."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models import RunResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Score range constraints
MIN_SCORE = -1.0
MAX_SCORE = 1.0
DEFAULT_SCORE = 0.0
DEFAULT_SCORE_VERSION = "baseline"


@dataclass(frozen=True)
class ScoringOutcome:
    """Outcome of the scoring process."""
    scored_count: int
    skipped_count: int  # Duplicates inherit scores, not scored directly


def score_run_results(
    session: Session,
    run_id: str,
    score_version: str = DEFAULT_SCORE_VERSION,
    now: datetime | None = None,
) -> ScoringOutcome:
    """Assign relevance scores to all non-duplicate results for a run.
    
    Baseline scoring assigns a default score of 0 to all non-duplicate results.
    Duplicates inherit scores from their canonical records and are not scored directly.
    
    Args:
        session: Database session
        run_id: The run ID to score
        score_version: Model version identifier (default: "baseline")
        now: Optional timestamp for scoring (defaults to UTC now)
        
    Returns:
        ScoringOutcome with counts of scored and skipped items
    """
    timestamp = now or datetime.now(timezone.utc)
    scored_at = _format_timestamp(timestamp)
    
    # Fetch all results for this run that haven't been scored yet
    results = session.execute(
        select(RunResult).where(
            RunResult.run_id == run_id,
            RunResult.relevance_score.is_(None),
        )
    ).scalars().all()
    
    if not results:
        logger.info("scoring.no_results run_id=%s", run_id)
        return ScoringOutcome(scored_count=0, skipped_count=0)
    
    logger.info("scoring.start run_id=%s count=%d", run_id, len(results))
    
    scored_count = 0
    skipped_count = 0
    
    for result in results:
        if result.is_duplicate:
            # Duplicates inherit score from canonical - don't score directly
            skipped_count += 1
            logger.debug(
                "scoring.skip_duplicate id=%d canonical_id=%d",
                result.id, result.canonical_id
            )
            continue
        
        # Assign baseline score to canonical records
        result.relevance_score = DEFAULT_SCORE
        result.scored_at = scored_at
        result.score_version = score_version
        scored_count += 1
        
        logger.debug(
            "scoring.assigned id=%d score=%f version=%s",
            result.id, DEFAULT_SCORE, score_version
        )
    
    # Commit all changes
    session.commit()
    
    logger.info(
        "scoring.complete run_id=%s scored=%d skipped=%d",
        run_id, scored_count, skipped_count
    )
    
    return ScoringOutcome(scored_count=scored_count, skipped_count=skipped_count)


def validate_score(score: float) -> float:
    """Validate and constrain a score to the allowed range [-1, 1].
    
    Args:
        score: The score to validate
        
    Returns:
        Score constrained to [-1, 1]
    """
    return max(MIN_SCORE, min(MAX_SCORE, score))


def get_canonical_score(session: Session, canonical_id: int) -> float | None:
    """Get the score from a canonical record for duplicate inheritance.
    
    Args:
        session: Database session
        canonical_id: The canonical record ID
        
    Returns:
        The canonical record's score, or None if not found
    """
    result = session.execute(
        select(RunResult.relevance_score).where(RunResult.id == canonical_id)
    ).scalar_one_or_none()
    
    return result


def _format_timestamp(value: datetime) -> str:
    """Format datetime as ISO 8601 UTC string."""
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
