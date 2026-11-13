from pathlib import Path

from fastapi.testclient import TestClient

from spencer.main import create_app

from .conftest import pdf_bytes, receipt_text


def test_import_duplicates_and_persistence(
    client: TestClient, receipt_pdf: bytes, tmp_path: Path
) -> None:
    imported = client.post(
        "/api/receipts", files={"file": ("test.pdf", receipt_pdf, "application/pdf")}
    )
    assert imported.status_code == 201
    assert imported.json()["line_count"] == 4
    assert (
        client.post("/api/receipts", files={"file": ("again.pdf", receipt_pdf)}).json()["status"]
        == "duplicate"
    )
    with TestClient(create_app(tmp_path)) as restarted:
        state = restarted.get("/api/state").json()
        assert len(state["receipts"]) == 1
        assert len(state["purchases"]) == 4
        assert len(state["products"]) == 3
        assert state["receipts"][0]["total_cents"] == 700
        assert restarted.get(f"/api/receipts/{imported.json()['id']}/pdf").content == receipt_pdf


def test_receipt_identity_detects_reexported_pdf(client: TestClient, receipt_pdf: bytes) -> None:
    client.post("/api/receipts", files={"file": ("first.pdf", receipt_pdf)})
    result = client.post(
        "/api/receipts", files={"file": ("second.pdf", receipt_pdf + b"\n%new export")}
    )
    assert result.json()["status"] == "duplicate"
    assert len(client.get("/api/state").json()["purchases"]) == 4


def test_failed_receipt_stays_visible_without_purchases(client: TestClient) -> None:
    result = client.post(
        "/api/receipts",
        files={"file": ("bad.pdf", pdf_bytes(receipt_text("PRODOTTO TEST *a 9,00")))},
    )
    assert result.json()["status"] == "failed"
    state = client.get("/api/state").json()
    assert state["receipts"][0]["error"]
    assert state["purchases"] == []


def test_review_applies_to_history_and_future_imports(
    client: TestClient, receipt_pdf: bytes
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    state = client.get("/api/state").json()
    product_id = state["products"][0]["id"]
    category_id = state["categories"][0]["id"]
    assert (
        client.patch(
            f"/api/products/{product_id}", json={"name": "Latte", "category_id": category_id}
        ).status_code
        == 200
    )
    client.post(
        "/api/receipts",
        files={
            "file": (
                "new.pdf",
                pdf_bytes(receipt_text("LATTE TEST 1L *a 7,00", document="0002-0001")),
            )
        },
    )
    state = client.get("/api/state").json()
    assert len(state["products"]) == 3
    assert state["products"][0] == {
        "id": product_id,
        "name": "Latte",
        "category_id": category_id,
        "reviewed": True,
    }
    assert (
        len([line for line in state["purchases"] if line["alias_id"] == state["aliases"][0]["id"]])
        == 3
    )


def test_alias_match_can_be_undone_without_touching_receipt_lines(
    client: TestClient, receipt_pdf: bytes
) -> None:
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    before = client.get("/api/state").json()
    alias = before["aliases"][0]
    target = before["products"][1]["id"]
    assert (
        client.patch(f"/api/aliases/{alias['id']}", json={"product_id": target}).status_code == 200
    )
    assert client.get("/api/state").json()["aliases"][0]["product_id"] == target
    detached = client.patch(f"/api/aliases/{alias['id']}", json={"product_id": None}).json()
    assert detached["product_id"] != target
    assert client.get("/api/state").json()["purchases"] == before["purchases"]


def test_deletion_removes_purchases_and_pdf(client: TestClient, receipt_pdf: bytes) -> None:
    receipt_id = client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)}).json()[
        "id"
    ]
    assert client.delete(f"/api/receipts/{receipt_id}").status_code == 200
    state = client.get("/api/state").json()
    assert state["purchases"] == state["receipts"] == []
    assert client.get(f"/api/receipts/{receipt_id}/pdf").status_code == 404


def test_category_edits_and_invalid_inputs(client: TestClient, receipt_pdf: bytes) -> None:
    category_id = client.post("/api/categories", json={"name": "Colazione"}).json()["id"]
    assert client.post("/api/categories", json={"name": "Colazione"}).status_code == 409
    assert (
        client.patch(f"/api/categories/{category_id}", json={"name": "La colazione"}).status_code
        == 200
    )
    assert client.post("/api/categories", json={"name": "  "}).status_code == 422
    client.post("/api/receipts", files={"file": ("test.pdf", receipt_pdf)})
    product_id = client.get("/api/state").json()["products"][0]["id"]
    assert (
        client.patch(
            f"/api/products/{product_id}", json={"name": "Latte", "category_id": 9999}
        ).status_code
        == 422
    )


def test_oversized_upload_is_rejected(client: TestClient) -> None:
    assert (
        client.post(
            "/api/receipts", files={"file": ("large.pdf", b"x" * (15 * 1024 * 1024 + 1))}
        ).status_code
        == 413
    )
