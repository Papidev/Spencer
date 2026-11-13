"""Initial receipt, product, and category storage."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id")),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("retailer", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.UniqueConstraint("retailer", "label"),
    )
    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_hash", sa.String(), nullable=False, unique=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("identity", sa.String(), unique=True),
        sa.Column("retailer", sa.String(), nullable=False),
        sa.Column("store", sa.String(), nullable=False),
        sa.Column("date", sa.String()),
        sa.Column("document", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.String()),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("voucher_cents", sa.Integer(), nullable=False),
        sa.Column("paid_cents", sa.Integer(), nullable=False),
        sa.Column("payments", sa.String(), nullable=False),
    )
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("receipt_id", sa.Integer(), sa.ForeignKey("receipts.id"), nullable=False),
        sa.Column("alias_id", sa.Integer(), sa.ForeignKey("aliases.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("gross_cents", sa.Integer(), nullable=False),
        sa.Column("discount_cents", sa.Integer(), nullable=False),
        sa.Column("price_verified", sa.Boolean(), nullable=False),
        sa.Column("discount_label", sa.String(), nullable=False),
    )


def downgrade() -> None:
    for table in ("purchases", "receipts", "aliases", "products", "categories"):
        op.drop_table(table)
