"""Add dedupe fields to run_items

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-13 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add dedupe columns
    op.add_column("run_items", sa.Column("canonical_id", sa.Integer(), nullable=True))
    op.add_column("run_items", sa.Column("is_duplicate", sa.Integer(), default=0))
    op.add_column("run_items", sa.Column("is_hidden", sa.Integer(), default=0))
    op.add_column("run_items", sa.Column("duplicate_count", sa.Integer(), default=0))
    
    # Add indexes for dedupe queries (SQLite supports these)
    op.create_index("idx_run_items__normalized_url", "run_items", ["normalized_url"])
    op.create_index("idx_run_items__canonical_id", "run_items", ["canonical_id"])
    op.create_index("idx_run_items__is_duplicate", "run_items", ["is_duplicate"])
    op.create_index("idx_run_items__is_hidden", "run_items", ["is_hidden"])
    
    # Note: Foreign key constraints are not added via Alembic for SQLite
    # because SQLite doesn't support ALTER TABLE ADD CONSTRAINT.
    # The foreign key relationship is enforced at the application level
    # and documented in the model. SQLite foreign keys are enabled via
    # PRAGMA foreign_keys = ON in the session configuration.


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_run_items__is_hidden", table_name="run_items")
    op.drop_index("idx_run_items__is_duplicate", table_name="run_items")
    op.drop_index("idx_run_items__canonical_id", table_name="run_items")
    op.drop_index("idx_run_items__normalized_url", table_name="run_items")
    
    # Drop columns
    op.drop_column("run_items", "duplicate_count")
    op.drop_column("run_items", "is_hidden")
    op.drop_column("run_items", "is_duplicate")
    op.drop_column("run_items", "canonical_id")
