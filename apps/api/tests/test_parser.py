import json
import os
from pathlib import Path

import pytest

from spencer.parser import ReceiptError, parse_pdf, parse_text

from .conftest import pdf_bytes, receipt_text


def test_digital_pdf_extraction_and_multibuy(receipt_pdf: bytes) -> None:
    result = parse_pdf(receipt_pdf)
    assert result.total == result.paid == 700
    assert len(result.lines) == 4
    assert [line.discount for line in result.lines] == [100, 100, 100, 0]
    assert result.date == "2026-11-08"


def test_vouchers_and_payment_benefits_are_separate() -> None:
    result = parse_text(
        receipt_text(
            "PRODOTTO TEST *a 30,00\nBUONO SPESA FIDATY 20,00-S\nBUONO SCONTO eb 10,00 E.",
            "10,00",
            "PAGAMENTO CARTA DI CREDITO 8,00\nPAGAMENTO +F) SCONTO +FACILE 2,00",
        )
    )
    assert result.lines[0].discount == 0
    assert result.voucher == 2000
    assert result.total == 1000
    assert result.paid == 800


def test_multibuy_rounding_preserves_total() -> None:
    result = parse_text(
        receipt_text("VARIANTE A *d 5,79\nVARIANTE B *d 5,79\nSC. 2X1 5,79-S", "5,79")
    )
    assert [line.discount for line in result.lines] == [289, 290]


def test_points_do_not_break_discount_association() -> None:
    result = parse_text(
        receipt_text(
            "BISCOTTI TEST *c 10,00\nPUNTI FRAGOLA 20\nP)PUNTI FRAGOLA 20\nSCONTO FIDATY 30% 3,00-S"
        )
    )
    assert result.lines[0].discount == 300


@pytest.mark.parametrize(
    "body,total",
    [
        ("PRODOTTO TEST *a 8,00", "7,00"),
        ("PRODOTTO TEST *a 7,00\nMOVIMENTO IGNOTO 1,00", "7,00"),
        ("PRODOTTO TEST *a 2,00\nSCONTO 3,00-S", "7,00"),
        ("PRODOTTO TEST *a 9,00\nSC. 2X1 2,00-S", "7,00"),
    ],
)
def test_ambiguous_or_unreconciled_data_is_rejected(body: str, total: str) -> None:
    with pytest.raises(ReceiptError):
        parse_text(receipt_text(body, total))


def test_payment_mismatch_is_rejected() -> None:
    with pytest.raises(ReceiptError, match="pagamenti"):
        parse_text(
            receipt_text("PRODOTTO TEST *a 7,00", payments="PAGAMENTO CARTA DI CREDITO 6,00")
        )


@pytest.mark.parametrize(
    "content", [b"not a pdf", b"%PDF-broken", pdf_bytes("SCONTRINO SENZA TESTO SUPPORTATO")]
)
def test_invalid_and_unsupported_documents(content: bytes) -> None:
    with pytest.raises(ReceiptError):
        parse_pdf(content)


def test_annotations_are_not_part_of_product_identity() -> None:
    assert parse_text(receipt_text("BANANE * *a 7,00")).lines[0].label == "BANANE"


@pytest.mark.parametrize("fixture_index", [0, 1, 2])
def test_private_receipts_when_available(fixture_index: int) -> None:
    manifest = os.environ.get("SPENCER_TEST_RECEIPTS")
    if not manifest:
        pytest.skip("Optional local receipts are never committed")
    path = Path(manifest)
    fixture = json.loads(path.read_text())[fixture_index]
    result = parse_pdf((path.parent / fixture["file"]).read_bytes())
    assert len(result.lines) == fixture["line_count"]
    assert result.total == fixture["total_cents"]
    assert result.paid == fixture["paid_cents"]
