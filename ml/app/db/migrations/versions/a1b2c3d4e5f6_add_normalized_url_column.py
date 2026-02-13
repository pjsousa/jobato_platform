"""Add normalized_url column to run_items

Revision ID: a1b2c3d4e5f6
Revises: 6f1aa0f9d8c2
Create Date: 2026-02-13 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6f1aa0f9d8c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("run_items", sa.Column("normalized_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("run_items", "normalized_url")
