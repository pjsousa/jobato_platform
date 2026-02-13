"""Add scoring fields to run_items

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-13 02:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scoring columns
    op.add_column("run_items", sa.Column("relevance_score", sa.Float(), nullable=True))
    op.add_column("run_items", sa.Column("scored_at", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("score_version", sa.String(), nullable=True))
    
    # Add indexes for scoring queries
    op.create_index("idx_run_items__relevance_score", "run_items", ["relevance_score"])
    op.create_index("idx_run_items__scored_at", "run_items", ["scored_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_run_items__scored_at", table_name="run_items")
    op.drop_index("idx_run_items__relevance_score", table_name="run_items")
    
    # Drop columns
    op.drop_column("run_items", "score_version")
    op.drop_column("run_items", "scored_at")
    op.drop_column("run_items", "relevance_score")
