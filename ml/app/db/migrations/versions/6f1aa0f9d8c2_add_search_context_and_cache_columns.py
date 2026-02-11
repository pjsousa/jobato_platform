"""Add search context and cache columns to run_items

Revision ID: 6f1aa0f9d8c2
Revises: 357d21170b4c
Create Date: 2026-02-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f1aa0f9d8c2"
down_revision: Union[str, None] = "357d21170b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("run_items", sa.Column("query_id", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("search_query", sa.String(), nullable=False, server_default=""))
    op.add_column("run_items", sa.Column("cache_key", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("cached_at", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("cache_expires_at", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("last_seen_at", sa.String(), nullable=True))
    op.add_column("run_items", sa.Column("skip_reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("run_items", "skip_reason")
    op.drop_column("run_items", "last_seen_at")
    op.drop_column("run_items", "cache_expires_at")
    op.drop_column("run_items", "cached_at")
    op.drop_column("run_items", "cache_key")
    op.drop_column("run_items", "search_query")
    op.drop_column("run_items", "query_id")
