import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from spencer.database import Product, database_engine
from spencer.enrichment import ProductResearch
from spencer.illustrations import IllustrationWorker


@pytest.mark.parametrize("selection", ["milk", "invalid", None])
def test_illustrations_are_independent_and_failures_are_bounded(
    client: TestClient,
    receipt_pdf: bytes,
    tmp_path: Path,
    selection: str | None,
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:9b"}]})
        assert request.url.path == "/api/chat"
        assert "LATTE TEST 1L" in json.loads(request.content)["messages"][1]["content"]
        if selection is None:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {"illustrations": [{"product_id": 1, "illustration": selection}]}
                    )
                }
            },
        )

    engine = database_engine(tmp_path)
    with Session(engine) as session:
        for product in session.query(Product):
            product.search_status = "not_found"
            if product.id != 1:
                product.illustration = "groceries"
        session.commit()
    worker = IllustrationWorker(
        engine, ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    )
    for attempt in range(1 if selection == "milk" else 3):
        assert asyncio.run(worker.run_once())
        with Session(engine) as session:
            product = session.get(Product, 1)
            assert product is not None
            assert product.illustration_attempts == attempt + 1
            product.illustration_after = 0
            session.commit()
    assert not asyncio.run(worker.run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["illustration"] == ("milk" if selection == "milk" else "")
    assert product["search_status"] == "not_found"
    assert not product["reviewed"] and not product["image_url"]
    worker.resume()
    if selection != "milk":
        with Session(engine) as session:
            assert session.get(Product, 1).illustration_attempts == 0
    engine.dispose()


def test_batch_respects_product_ids_and_name_corrections_during_inference(
    client: TestClient,
    receipt_pdf: bytes,
    tmp_path: Path,
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:9b"}]})
        client.patch("/api/products/1", json={"name": "Succo di mela"})
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {
                            "illustrations": [
                                {"product_id": 3, "illustration": "bread"},
                                {"product_id": 1, "illustration": "milk"},
                                {"product_id": 2, "illustration": "pasta"},
                            ]
                        }
                    )
                }
            },
        )

    engine = database_engine(tmp_path)
    research = ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    assert asyncio.run(IllustrationWorker(engine, research).run_once())
    products = client.get("/api/state").json()["products"]
    assert [product["illustration"] for product in products] == ["", "pasta", "bread"]
    assert products[0]["name"] == "Succo di mela"
    engine.dispose()
