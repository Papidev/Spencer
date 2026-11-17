from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from spencer.categorization import receipt_category
from spencer.database import CATEGORIES, Alias, Category, Product, database_engine
from spencer.main import create_app


@pytest.mark.parametrize(
    ("labels", "expected"),
    [
        (["LATTE PS. UHT ESS."], "Latticini e uova"),
        (["FOCACCIA C/POMODORINI"], "Pane e prodotti da forno"),
        (["FOCACC.CROC.MAIS"], "Pane e prodotti da forno"),
        (["6 FOCACCINE"], "Pane e prodotti da forno"),
        (["STRACC. POLLO PROV PL"], "Carne"),
        (["FILETTI DI PLATESSA"], "Pesce"),
        (["TORTELLONI RIC/SPIN."], "Pasta, riso e cereali"),
        (["BANANE"], "Frutta e verdura"),
        (["LATTE DI MANDORLA"], None),
        (["LATTE CORPO"], None),
        (["CIOCCOLATO AL LATTE"], "Dolci e snack"),
        (["CAPRICE PICC"], None),
        (["PATATESCO"], None),
        (["BURGER FIOCCHI PATATE"], None),
        (["SUGO AL POMODORO"], None),
        (["TORTA CON CIPOLLINE"], None),
        (["LATTE", "PANE"], None),
    ],
)
def test_category_from_receipt_words(labels: list[str], expected: str | None) -> None:
    categories = dict(enumerate(CATEGORIES, start=1))
    category_id = receipt_category(labels, categories)
    assert (categories[category_id] if category_id is not None else None) == expected


def test_does_not_invent_missing_category() -> None:
    assert receipt_category(["LATTE"], {1: "Bevande"}) is None


def test_import_categorizes_without_confirming_products(
    client: TestClient, receipt_pdf: bytes
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    state = client.get("/api/state").json()
    categories = {c["id"]: c["name"] for c in state["categories"]}
    assert [categories[p["category_id"]] for p in state["products"]] == [
        "Latticini e uova", "Pasta, riso e cereali", "Pane e prodotti da forno"
    ]
    assert all(not p["reviewed"] and not p["confirmation"] for p in state["products"])


def test_startup_fills_existing_missing_categories_and_preserves_manual_choices(
    client: TestClient, tmp_path: Path
) -> None:
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        dairy = session.scalar(select(Category.id).where(Category.name == "Latticini e uova"))
        for name, category_id, manual_fields in [
            ("FOCACCIA C/POMODORINI", None, "[]"),
            ("LATTE", None, '["category_id"]'),
            ("PANE", dairy, '["category_id"]'),
            ("PIZZA", dairy, "[]"),
        ]:
            product = Product(
                name=name, category_id=category_id, manual_fields=manual_fields,
                search_status="not_found",
            )
            session.add(product)
            session.flush()
            session.add(Alias(retailer="Esselunga", label=name, product_id=product.id))
        session.commit()
    engine.dispose()
    with TestClient(create_app(tmp_path)) as restarted:
        state = restarted.get("/api/state").json()
    categories = {c["id"]: c["name"] for c in state["categories"]}
    assert [categories.get(p["category_id"]) for p in state["products"]] == [
        "Pane e prodotti da forno", None, "Latticini e uova", "Latticini e uova"
    ]
    assert all(p["search_status"] == "not_found" and not p["reviewed"] for p in state["products"])
    assert state["products"][1]["manual_fields"] == ["category_id"]
