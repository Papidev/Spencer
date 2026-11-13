import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from io import BytesIO

import pdfplumber


class ReceiptError(ValueError):
    pass


@dataclass
class Line:
    label: str
    gross: int
    discount: int = 0
    verified: bool = True
    discount_label: str = ""


@dataclass
class ParsedReceipt:
    date: str
    store: str
    document: str
    terminal: str
    total: int
    voucher: int
    paid: int
    payments: list[dict[str, str | int]]
    lines: list[Line] = field(default_factory=list)

    @property
    def identity(self) -> str:
        return f"Esselunga|{self.store}|{self.terminal}|{self.date}|{self.document}"


def cents(value: str) -> int:
    return int(Decimal(value.replace(".", "").replace(",", ".")) * 100)


def parse_pdf(content: bytes) -> ParsedReceipt:
    if not content.startswith(b"%PDF-"):
        raise ReceiptError("Il file non è un PDF valido.")
    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            if len(pdf.pages) > 10:
                raise ReceiptError("Lo scontrino supera il limite di 10 pagine.")
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ReceiptError:
        raise
    except Exception as error:
        raise ReceiptError(
            "Impossibile leggere il PDF. Verifica che non sia protetto o danneggiato."
        ) from error
    return parse_text(text)


def parse_text(text: str) -> ParsedReceipt:
    if "ESSELUNGA" not in text.upper():
        raise ReceiptError("Formato non supportato: importa uno scontrino digitale Esselunga.")
    start = re.search(r"IVA\s+EURO", text)
    end = re.search(r"TOTALE EURO\s+([\d.]+,\d{2})", text)
    date = re.search(r"(\d{2}-\d{2}-\d{4})\s+\d{2}:\d{2}", text)
    document = re.search(r"DOCUMENTO N\.\s*(\S+)", text)
    terminal = re.search(r"MATRICOLA CASSA N\.\s*(\S+)", text)
    store = re.search(r"\* ESSELUNGA[^\n]*\n([^\n]+)", text)
    if not all((start, end, date, document, terminal, store)):
        raise ReceiptError(
            "Dati dello scontrino mancanti. Il PDF deve contenere testo selezionabile."
        )
    assert start and end and date and document and terminal and store
    if end.start() <= start.end():
        raise ReceiptError("Struttura dello scontrino non riconosciuta.")

    lines: list[Line] = []
    voucher = 0
    for raw in text[start.end() : end.start()].splitlines():
        raw = raw.strip()
        if not raw:
            continue
        item = re.fullmatch(r"(.+?)\s+\*[a-z]\s+([\d.]+,\d{2})", raw)
        discount = re.fullmatch(r"(.+?)\s+([\d.]+,\d{2})-S", raw)
        if item:
            # Asterisks used as receipt annotations are not part of the product label.
            lines.append(Line(re.sub(r"\s+\*$", "", item[1]).strip(), cents(item[2])))
        elif discount:
            label, amount = discount[1], cents(discount[2])
            if label.startswith("BUONO SPESA"):
                voucher += amount
            elif label == "SC. 2X1":
                # This format identifies a pair of immediately preceding product rows.
                if (
                    len(lines) < 2
                    or any(line.discount for line in lines[-2:])
                    or amount != min(line.gross for line in lines[-2:])
                ):
                    raise ReceiptError("Offerta 2x1 non riconciliabile: controlla lo scontrino.")
                gross = sum(line.gross for line in lines[-2:])
                allocated = amount * lines[-2].gross // gross
                for line, reduction in zip(
                    lines[-2:], (allocated, amount - allocated), strict=True
                ):
                    line.discount += reduction
                    line.discount_label = label
            elif label.upper().startswith(("SCONTO", "SC.")) and lines:
                lines[-1].discount += amount
                lines[-1].discount_label = "; ".join(
                    filter(None, (lines[-1].discount_label, label))
                )
            else:
                raise ReceiptError(f"Sconto non riconosciuto: {label}.")
        elif re.fullmatch(r"(?:P\))?PUNTI FRAGOLA.*", raw):
            continue
        elif re.fullmatch(r"BUONO SCONTO eb\s+[\d.]+,\d{2}\s+E\.", raw):
            # An issued voucher for a future purchase, not a discount on this receipt.
            continue
        else:
            raise ReceiptError(f"Riga non riconosciuta: {raw}")

    total = cents(end[1])
    if not lines or any(line.discount > line.gross for line in lines):
        raise ReceiptError("Importi dei prodotti non validi.")
    if sum(line.gross - line.discount for line in lines) - voucher != total:
        raise ReceiptError(
            "Il totale estratto non corrisponde allo scontrino. Nessun acquisto incluso nelle analisi."
        )
    payments: list[dict[str, str | int]] = [
        {"label": match[1], "cents": cents(match[2])}
        for match in re.finditer(r"^PAGAMENTO\s+(.+?)\s+([\d.]+,\d{2})\s*$", text, re.MULTILINE)
    ]
    if not payments or sum(int(payment["cents"]) for payment in payments) != total:
        raise ReceiptError("Il dettaglio dei pagamenti non corrisponde al totale.")
    paid = sum(
        int(payment["cents"])
        for payment in payments
        if not re.search(r"SCONTO|BUONO|VOUCHER", str(payment["label"]), re.I)
    )
    try:
        parsed_date = datetime.strptime(date[1], "%d-%m-%Y").date().isoformat()
    except ValueError as error:
        raise ReceiptError("Data dello scontrino non valida.") from error
    return ParsedReceipt(
        date=parsed_date,
        store=store[1].strip(),
        document=document[1],
        terminal=terminal[1],
        total=total,
        voucher=voucher,
        paid=paid,
        payments=payments,
        lines=lines,
    )
