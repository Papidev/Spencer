"""Queue existing products for receipt-based sales type classification."""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE products
        SET category_status = 'pending', category_attempts = 0, category_after = 0
        WHERE kind = 'unknown' AND manual_fields NOT LIKE '%"kind"%'
          AND id IN (SELECT aliases.product_id FROM aliases
                     JOIN purchases ON purchases.alias_id = aliases.id)
    """)


def downgrade() -> None:
    pass
