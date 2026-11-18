"""Durable independent AI category classification."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("category_status", sa.String(), nullable=False, server_default="pending")
    )
    op.add_column(
        "products", sa.Column("category_attempts", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "products", sa.Column("category_after", sa.Float(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    for name in ("category_status", "category_attempts", "category_after"):
        op.drop_column("products", name)
