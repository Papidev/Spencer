"""Generic product illustrations selected by local AI."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("illustration", sa.String(), nullable=False, server_default="")
    )
    op.add_column(
        "products",
        sa.Column("illustration_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "products", sa.Column("illustration_after", sa.Float(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    for name in ("illustration", "illustration_attempts", "illustration_after"):
        op.drop_column("products", name)
