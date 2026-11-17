"""Distinguish repeatable formats from variable-weight purchases."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("kind", sa.String(), nullable=False, server_default="unknown")
    )


def downgrade() -> None:
    op.drop_column("products", "kind")
