from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from spencer.database import database_engine


def test_existing_products_migrate_to_unknown_without_changing_purchases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPENCER_DATA_DIR", str(tmp_path))
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "0002")
    engine = database_engine(tmp_path)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO products (id, name, reviewed) VALUES (1, 'Pollo', 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO aliases (id, retailer, label, product_id) VALUES (1, 'Test', 'POLLO', 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO receipts (id, file_hash, filename, retailer, store, status, total_cents, voucher_cents, paid_cents, payments) "
            "VALUES (1, 'test', 'test.pdf', 'Test', 'Test store', 'imported', 500, 0, 500, '[]')"
        )
        connection.exec_driver_sql(
            "INSERT INTO purchases (id, receipt_id, alias_id, position, gross_cents, discount_cents, price_verified, discount_label) "
            "VALUES (1, 1, 1, 0, 500, 0, 1, '')"
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT name, kind FROM products").all() == [
            ("Pollo", "unknown")
        ]
        assert connection.exec_driver_sql(
            "SELECT category_status, category_attempts, category_after FROM products"
        ).all() == [("pending", 0, 0)]
        assert connection.exec_driver_sql("SELECT gross_cents FROM purchases").scalar() == 500
    engine.dispose()
