from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from spencer.main import create_app


def receipt_text(
    body: str, total: str = "7,00", payments: str | None = None, document: str = "0001-0001"
) -> str:
    return f"""* ESSELUNGA S.p.A. *
VIA ESEMPIO - NEGOZIO TEST
DOCUMENTO COMMERCIALE
IVA EURO
{body}
TOTALE EURO {total} *
{payments or f"PAGAMENTO CARTA DI CREDITO {total}"}
08-11-2026 12:29
DOCUMENTO N. {document}
MATRICOLA CASSA N. 10000001
"""


def pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    document = canvas.Canvas(buffer, pagesize=(400, max(600, len(text.splitlines()) * 14 + 50)))
    block = document.beginText(20, max(600, len(text.splitlines()) * 14 + 50) - 30)
    block.setFont("Courier", 10)
    for line in text.splitlines():
        block.textLine(line)
    document.drawText(block)
    document.save()
    return buffer.getvalue()


@pytest.fixture
def receipt_pdf() -> bytes:
    return pdf_bytes(
        receipt_text(
            "LATTE TEST 1L *a 2,00\nLATTE TEST 1L *a 2,00\nSC. 2X1 2,00-S\nPASTA TEST 500G *a 4,00\nSCONTO FIDATY 25% 1,00-S\nPANE TEST *a 2,00"
        )
    )


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("SPENCER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SPENCER_ENRICHMENT_ENABLED", "false")
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    with TestClient(create_app(tmp_path)) as client:
        yield client
