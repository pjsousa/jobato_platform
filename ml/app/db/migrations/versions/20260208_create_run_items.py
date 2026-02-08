from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260208_create_run_items"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("query_text", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("raw_url", sa.String(), nullable=False),
        sa.Column("final_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
    )
    op.create_index("idx_run_items__run_id", "run_items", ["run_id"])


def downgrade() -> None:
    op.drop_index("idx_run_items__run_id", table_name="run_items")
    op.drop_table("run_items")
