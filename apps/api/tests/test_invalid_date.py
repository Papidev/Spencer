import pytest

from spencer.parser import ReceiptError, parse_text

from .conftest import receipt_text


def test_invalid_dates_fail_with_a_readable_error() -> None:
    with pytest.raises(ReceiptError, match="Data"):
        parse_text(receipt_text("PRODOTTO TEST *a 7,00").replace("08-11-2026", "99-99-2026"))
