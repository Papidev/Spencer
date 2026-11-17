import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from spencer.database import Product, database_engine
from spencer.enrichment import EnrichmentWorker, ProductPage, ProductResearch, public_url


def research_client(
    *,
    found: bool = True,
    unavailable: bool = False,
    cloud: bool = False,
    pack_size: str = "1 L",
    kind: str = "fixed",
    category_id: int | None = 1,
    image_url: str = "https://93.184.216.34/latte.jpg",
    on_selection: Callable[[], object] | None = None,
) -> ProductResearch:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "name": "qwen3.5:9b",
                            **({"remote_host": "ollama.com"} if cloud else {}),
                        }
                    ]
                },
            )
        if request.url.path == "/api/chat":
            data = json.loads(request.content)
            if "query" in data["format"]["properties"]:
                result = {"query": "Latte test 1L"}
            else:
                if on_selection:
                    on_selection()
                result = {
                    "candidate": 0 if found else None,
                    "name": "Latte intero test",
                    "brand": "Test",
                    "pack_size": pack_size,
                    "kind": kind,
                    "category_id": category_id,
                }
            return httpx.Response(200, json={"message": {"content": json.dumps(result)}})
        if request.url.path == "/search":
            if unavailable:
                return httpx.Response(503)
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "url": "https://93.184.216.34/latte",
                            "title": "Latte intero test 1 L",
                            "content": "Latte marca Test da 1 L",
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            text='''<html><meta property="og:image"
            content="'''
            + image_url
            + """"><script type="application/ld+json">
            {"@type":"Product","name":"Latte intero test 1 L","brand":{"name":"Test"}}
            </script></html>""",
            headers={"content-type": "text/html"},
        )

    return ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(respond)))


def test_worker_saves_grounded_details_and_confirms_automatically(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    worker = EnrichmentWorker(engine, research_client())
    assert asyncio.run(worker.run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["kind"] == "fixed"
    assert product["name"] == "Latte intero test"
    assert product["reviewed"] is True
    assert product["confirmation"] == "automatic"
    assert product["image_url"] == "https://93.184.216.34/latte.jpg"
    assert product["source_url"] == "https://93.184.216.34/latte"
    assert product["search_status"] == "matched"
    assert len(client.get("/api/state").json()["purchases"]) == 4
    engine.dispose()


def test_manual_correction_during_research_wins_without_losing_other_details(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    research = research_client(
        on_selection=lambda: client.patch(
            "/api/products/1", json={"name": "Il mio latte", "image_url": "", "kind": "variable_weight"}
        )
    )
    assert asyncio.run(EnrichmentWorker(engine, research).run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["name"] == "Il mio latte"
    assert product["image_url"] == ""
    assert product["brand"] == "Test"
    assert product["pack_size"] == "1 L"
    assert product["confirmation"] == "manual"
    assert product["kind"] == "variable_weight"
    assert product["manual_fields"] == ["image_url", "kind", "name"]
    engine.dispose()


def test_failures_are_bounded_persistent_and_resume_on_restart(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    worker = EnrichmentWorker(engine, research_client(unavailable=True))
    # Leave just one queued product for a deterministic run through the retry budget.
    with Session(engine) as session:
        for product in session.query(Product).filter(Product.id != 1):
            product.search_status = "idle"
        session.commit()
    for attempt in range(3):
        assert asyncio.run(worker.run_once())
        with Session(engine) as session:
            product = session.get(Product, 1)
            assert product is not None
            assert product.search_attempts == attempt + 1
            product.search_after = 0
            session.commit()
    assert asyncio.run(worker.run_once()) is False
    assert client.get("/api/state").json()["products"][0]["search_status"] == "failed"
    worker.resume()
    assert client.get("/api/state").json()["products"][0]["search_status"] == "pending"
    engine.dispose()


def test_no_match_preserves_original_and_does_not_confirm(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    assert asyncio.run(EnrichmentWorker(engine, research_client(found=False)).run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["name"] == "LATTE TEST 1L"
    assert product["image_url"] == ""
    assert product["reviewed"] is False
    assert product["search_status"] == "not_found"
    assert client.post("/api/products/search").json() == {"queued": 0}
    assert client.get("/api/state").json()["products"][0]["search_status"] == "not_found"
    assert client.post(
        f"/api/products/{product['id']}/search", json={"replace_manual": False}
    ).json() == {"queued": True}
    assert client.get("/api/state").json()["products"][0]["search_status"] == "pending"
    engine.dispose()


def test_requeue_invalidates_in_flight_result(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    engine = database_engine(tmp_path)
    research = research_client(
        on_selection=lambda: client.post("/api/products/1/search", json={"replace_manual": False})
    )
    asyncio.run(EnrichmentWorker(engine, research).run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["search_status"] == "pending"
    assert product["name"] == "LATTE TEST 1L"
    engine.dispose()


def test_partial_manual_update_and_explicit_replacement(
    client: TestClient, receipt_pdf: bytes
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    client.patch("/api/products/1", json={"category_id": 1})
    assert client.patch("/api/products/1", json={"brand": "Mia marca"}).status_code == 200
    product = client.get("/api/state").json()["products"][0]
    assert product["name"] == "LATTE TEST 1L"
    assert product["category_id"] == 1
    assert product["manual_fields"] == ["brand", "category_id"]
    client.post("/api/products/1/search", json={"replace_manual": False})
    assert client.get("/api/state").json()["products"][0]["manual_fields"] == [
        "brand",
        "category_id",
    ]
    client.post("/api/products/1/search", json={"replace_manual": True})
    assert client.get("/api/state").json()["products"][0]["manual_fields"] == []
    assert (
        client.patch("/api/products/1", json={"image_url": "http://127.0.0.1/private"}).status_code
        == 422
    )


def test_cloud_model_is_rejected() -> None:
    from spencer.enrichment import SearchUnavailable

    with pytest.raises(SearchUnavailable):
        asyncio.run(research_client(cloud=True).research(["LATTE"], {1: "Latticini"}))


def test_unsupported_pack_size_and_generic_sharing_image_are_discarded() -> None:
    result = asyncio.run(
        research_client(
            pack_size="6 L", image_url="https://93.184.216.34/share/social.jpg"
        ).research(["LATTE TEST"], {1: "Latticini"})
    )
    assert result is not None
    assert result["pack_size"] == ""
    assert result["kind"] == "unknown"
    assert result["image_url"] == ""


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/x",
        "https://[::1]/",
        "https://host.local/x",
        "https://user:pass@example.com",
        "http://169.254.169.254/x",
    ],
)
def test_private_or_non_http_images_are_rejected(url: str) -> None:
    assert not public_url(url)


def test_page_without_image_does_not_use_page_url_as_photo() -> None:
    page = ProductPage()
    page.feed(
        '<script type="application/ld+json">{"@graph":[{"@type":"Product","name":"Latte"}]}</script>'
    )
    assert page.product_data()["name"] == "Latte"
    assert page.image == ""


@pytest.mark.parametrize("packaged", [True, False])
def test_images_are_checked_for_packaging_and_verdicts_cached(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path, packaged: bool
) -> None:
    from spencer.main import create_app

    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    client.patch("/api/products/1", json={"image_url": "https://93.184.216.34/photo.png"})
    requested = []
    classifications = []

    def image_response(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:9b"}]})
        if request.url.path == "/api/chat":
            classifications.append(json.loads(request.content))
            return httpx.Response(
                200, json={"message": {"content": json.dumps({"packaged": packaged})}}
            )
        requested.append(str(request.url))
        return httpx.Response(
            200, content=b"\x89PNG\r\n\x1a\nimage fixture", headers={"content-type": "image/png"}
        )

    research = ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(image_response)))
    with TestClient(create_app(tmp_path, research)) as app:
        first = app.get("/api/products/1/image")
        second = app.get("/api/products/1/image")
        assert first.status_code == second.status_code == (200 if packaged else 404)
        if packaged:
            assert first.headers["content-type"] == "image/png"
        assert first.content == second.content
        assert len(requested) == 1
        assert len(classifications) == 1
        assert classifications[0]["messages"][-1]["images"]
        assert len(list((tmp_path / "product-images").iterdir())) == 2


def test_executable_content_cannot_be_served_as_a_product_image(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    from spencer.main import create_app

    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    client.patch("/api/products/1", json={"image_url": "https://93.184.216.34/photo.png"})
    research = ProductResearch(
        httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    content=b"<svg><script>bad()</script></svg>",
                    headers={"content-type": "image/png"},
                )
            )
        )
    )
    with TestClient(create_app(tmp_path, research)) as app:
        assert app.get("/api/products/1/image").status_code == 404
    assert not (tmp_path / "product-images").exists()


def test_image_redirects_cannot_access_local_services() -> None:
    requested = []

    def redirect(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})

    research = ProductResearch(httpx.AsyncClient(transport=httpx.MockTransport(redirect)))
    assert asyncio.run(research.image("https://93.184.216.34/photo.png")) is None
    assert requested == ["https://93.184.216.34/photo.png"]


@pytest.mark.parametrize("kind", ["unknown", "variable_weight"])
def test_research_preserves_non_comparable_classification(kind: str) -> None:
    result = asyncio.run(
        research_client(kind=kind).research(["LATTE TEST"], {1: "Latticini"})
    )
    assert result is not None
    assert result["kind"] == kind


def test_match_without_category_preserves_receipt_category(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    state = client.get("/api/state").json()
    dairy = next(c["id"] for c in state["categories"] if c["name"] == "Latticini e uova")
    assert state["products"][0]["category_id"] == dairy
    engine = database_engine(tmp_path)
    assert asyncio.run(EnrichmentWorker(engine, research_client(category_id=None)).run_once())
    product = client.get("/api/state").json()["products"][0]
    assert product["category_id"] == dairy
    assert product["search_status"] == "matched"
    engine.dispose()
