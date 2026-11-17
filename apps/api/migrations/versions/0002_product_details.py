"""Product details, manual corrections and durable enrichment work."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("brand", "pack_size", "image_url", "source_url", "confirmation", "search_error"):
        op.add_column("products", sa.Column(name, sa.String(), nullable=False, server_default=""))
    op.add_column(
        "products", sa.Column("manual_fields", sa.String(), nullable=False, server_default="[]")
    )
    op.add_column(
        "products", sa.Column("search_status", sa.String(), nullable=False, server_default="idle")
    )
    for name in ("search_attempts", "search_revision"):
        op.add_column("products", sa.Column(name, sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "products", sa.Column("search_after", sa.Float(), nullable=False, server_default="0")
    )
    op.execute("""UPDATE products SET confirmation = 'manual',
        manual_fields = '["name", "category_id"]' WHERE reviewed = 1""")


def downgrade() -> None:
    for name in (
        "brand",
        "pack_size",
        "image_url",
        "source_url",
        "confirmation",
        "manual_fields",
        "search_status",
        "search_attempts",
        "search_error",
        "search_after",
        "search_revision",
    ):
        op.drop_column("products", name)
