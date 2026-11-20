import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from spencer.categorization import CategoryWorker
from spencer.database import Product, database_engine
from spencer.enrichment import ProductResearch


def classification_client(
    category_id: int | None,
    *,
    unavailable: bool = False,
    on_selection: Callable[[], object] | None = None,
) -> ProductResearch:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:9b"}]})
        # Category classification must not call a search engine or retrieve product pages.
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert list(payload["format"]["properties"]) == ["category_id", "kind"]
        assert "LATTE TEST 1L" in payload["messages"][1]["content"]
        if on_selection:
            on_selection()
        if unavailable:
            return httpx.Response(503)
        return httpx.Response(
            200, json={"message": {"content": json.dumps({"category_id": category_id, "kind": "fixed"})}}
        )

    return ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(respond)))


@pytest.mark.parametrize("category_name", ["Latticini e uova", "Bevande", None])
def test_ai_category_is_independent_of_exact_identification(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path, category_name: str | None
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    state = client.get("/api/state").json()
    category_id = next((c["id"] for c in state["categories"] if c["name"] == category_name), None)
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        product = session.get(Product, 1)
        assert product is not None
        product.search_status = "not_found"
        session.commit()
    worker = CategoryWorker(engine, classification_client(category_id))
    assert asyncio.run(worker.run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["category_id"] == category_id
    assert product["category_status"] == ("done" if category_id is not None else "not_found")
    assert product["kind"] == "fixed"
    assert product["name"] == "LATTE TEST 1L"
    assert product["search_status"] == "not_found"
    assert not product["reviewed"] and not product["confirmation"]
    assert not product["source_url"] and not product["image_url"]
    engine.dispose()


def test_manual_category_during_inference_wins(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    research = classification_client(
        1, on_selection=lambda: client.patch("/api/products/1", json={"category_id": None})
    )
    assert asyncio.run(CategoryWorker(engine, research).run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["category_id"] is None
    assert product["category_status"] == "done"
    assert "category_id" in product["manual_fields"]
    engine.dispose()


def test_existing_categories_and_manual_empty_category_are_not_processed(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        products = session.query(Product).order_by(Product.id).all()
        products[0].category_id = 1
        products[0].kind = "fixed"
        products[1].manual_fields = '["category_id", "kind"]'
        products[2].category_status = "not_found"
        session.commit()
    worker = CategoryWorker(engine, classification_client(2))
    worker.resume()
    assert asyncio.run(worker.run_once()) is False
    products = client.get("/api/state").json()["products"]
    assert products[0]["category_id"] == 1
    assert products[1]["category_id"] is None
    engine.dispose()


@pytest.mark.parametrize("unavailable,category_id", [(True, 1), (False, 99999)])
def test_invalid_or_unavailable_ai_retries_with_a_persistent_limit(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path,
    unavailable: bool, category_id: int,
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        for product in session.query(Product).filter(Product.id != 1):
            product.category_status = "done"
        session.commit()
    worker = CategoryWorker(engine, classification_client(category_id, unavailable=unavailable))
    for attempt in range(3):
        assert asyncio.run(worker.run_once())
        with Session(engine) as session:
            product = session.get(Product, 1)
            assert product is not None
            assert product.category_attempts == attempt + 1
            assert product.category_id is None
            assert product.category_status == ("retry" if attempt < 2 else "failed")
            product.category_after = 0
            session.commit()
    assert asyncio.run(worker.run_once()) is False
    worker.resume()
    with Session(engine) as session:
        product = session.get(Product, 1)
        assert product is not None
        assert product.category_status == "pending"
        assert product.category_attempts == 0
    assert asyncio.run(CategoryWorker(engine, classification_client(1)).run_once())
    assert client.get("/api/state").json()["products"][0]["category_id"] == 1
    engine.dispose()


def test_uncertain_ai_result_is_not_repeated_on_restart(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        for product in session.query(Product).filter(Product.id != 1):
            product.category_status = "done"
        session.commit()
    assert asyncio.run(CategoryWorker(engine, classification_client(None)).run_once())
    restarted = CategoryWorker(engine, classification_client(1))
    restarted.resume()
    assert asyncio.run(restarted.run_once()) is False
    assert client.get("/api/state").json()["products"][0]["category_id"] is None
    engine.dispose()


@pytest.mark.parametrize("manual_edit", [False, True])
def test_classifies_sales_type_with_existing_category(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path, manual_edit: bool
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    with Session(engine) as session:
        product = session.get(Product, 1)
        assert product is not None
        product.category_id = 1
        session.commit()
    research = classification_client(
        2,
        on_selection=(
            lambda: client.patch("/api/products/1", json={"kind": "variable_weight"})
        ) if manual_edit else None,
    )
    worker = CategoryWorker(engine, research)
    worker.resume()
    assert asyncio.run(worker.run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["category_id"] == 1
    assert product["kind"] == ("variable_weight" if manual_edit else "fixed")
    assert ("kind" in product["manual_fields"]) == manual_edit
    engine.dispose()
