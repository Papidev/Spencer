import hashlib
import json
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from spencer.database import (
    CATEGORIES,
    Alias,
    Category,
    Product,
    Purchase,
    Receipt,
    data_directory,
    database_engine,
)
from spencer.parser import ReceiptError, parse_pdf


class ProductUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category_id: int | None = None
    reviewed: bool = True


class AliasUpdate(BaseModel):
    product_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


def create_app(directory: Path | None = None) -> FastAPI:
    directory = directory or data_directory()
    engine = database_engine(directory)
    pdf_directory = directory / "receipts"
    pdf_directory.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Any:
        with Session(engine) as session:
            if not session.scalar(select(Category.id).limit(1)):
                session.add_all(Category(name=name) for name in CATEGORIES)
                session.commit()
        yield
        engine.dispose()

    app = FastAPI(title="Spencer", lifespan=lifespan)

    def session_dependency() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    Database = Annotated[Session, Depends(session_dependency)]

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/state")
    def state(session: Database) -> dict[str, Any]:
        receipts = session.scalars(
            select(Receipt).order_by(Receipt.date.desc(), Receipt.id.desc())
        ).all()
        return {
            "receipts": [
                {
                    "id": receipt.id,
                    "filename": receipt.filename,
                    "retailer": receipt.retailer,
                    "store": receipt.store,
                    "date": receipt.date,
                    "document": receipt.document,
                    "status": receipt.status,
                    "error": receipt.error,
                    "total_cents": receipt.total_cents,
                    "voucher_cents": receipt.voucher_cents,
                    "paid_cents": receipt.paid_cents,
                    "payments": json.loads(receipt.payments),
                    "line_count": len(receipt.lines),
                }
                for receipt in receipts
            ],
            "categories": [
                {"id": category.id, "name": category.name}
                for category in session.scalars(select(Category).order_by(Category.name)).all()
            ],
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "category_id": product.category_id,
                    "reviewed": product.reviewed,
                }
                for product in session.scalars(select(Product)).all()
            ],
            "aliases": [
                {
                    "id": alias.id,
                    "label": alias.label,
                    "retailer": alias.retailer,
                    "product_id": alias.product_id,
                }
                for alias in session.scalars(select(Alias)).all()
            ],
            "purchases": [
                {
                    "id": purchase.id,
                    "receipt_id": purchase.receipt_id,
                    "alias_id": purchase.alias_id,
                    "position": purchase.position,
                    "gross_cents": purchase.gross_cents,
                    "discount_cents": purchase.discount_cents,
                    "price_verified": purchase.price_verified,
                    "discount_label": purchase.discount_label,
                }
                for purchase in session.scalars(
                    select(Purchase).order_by(Purchase.receipt_id, Purchase.position)
                ).all()
            ],
        }

    @app.post("/api/receipts", status_code=201)
    def import_receipt(file: UploadFile, session: Database) -> dict[str, Any]:
        content = file.file.read(15 * 1024 * 1024 + 1)
        if len(content) > 15 * 1024 * 1024:
            raise HTTPException(413, "Il PDF supera il limite di 15 MB.")
        digest = hashlib.sha256(content).hexdigest()
        existing = session.scalar(select(Receipt).where(Receipt.file_hash == digest))
        if existing and existing.status == "imported":
            return {"status": "duplicate", "id": existing.id}
        receipt = existing or Receipt(
            file_hash=digest, filename=Path(file.filename or "scontrino.pdf").name, status="failed"
        )
        try:
            parsed = parse_pdf(content)
        except ReceiptError as error:
            receipt.status = "failed"
            receipt.error = str(error)
            session.add(receipt)
            session.commit()
            if content.startswith(b"%PDF-"):
                (pdf_directory / f"{digest}.pdf").write_bytes(content)
            return {"status": "failed", "id": receipt.id, "error": str(error)}

        duplicate = session.scalar(select(Receipt).where(Receipt.identity == parsed.identity))
        if duplicate and duplicate.id != receipt.id:
            return {"status": "duplicate", "id": duplicate.id}
        receipt.identity = parsed.identity
        receipt.store = parsed.store
        receipt.date = parsed.date
        receipt.document = parsed.document
        receipt.total_cents = parsed.total
        receipt.voucher_cents = parsed.voucher
        receipt.paid_cents = parsed.paid
        receipt.payments = json.dumps(parsed.payments)
        receipt.status = "imported"
        receipt.error = None
        session.add(receipt)
        session.flush()
        for position, line in enumerate(parsed.lines):
            alias = session.scalar(
                select(Alias).where(Alias.retailer == "Esselunga", Alias.label == line.label)
            )
            if alias is None:
                product = Product(name=line.label, reviewed=False)
                session.add(product)
                session.flush()
                alias = Alias(retailer="Esselunga", label=line.label, product_id=product.id)
                session.add(alias)
                session.flush()
            session.add(
                Purchase(
                    receipt_id=receipt.id,
                    alias_id=alias.id,
                    position=position,
                    gross_cents=line.gross,
                    discount_cents=line.discount,
                    price_verified=line.verified,
                    discount_label=line.discount_label,
                )
            )
        try:
            # Atomic replacement also makes a reimport after a failed commit safe.
            (pdf_directory / f"{digest}.pdf").write_bytes(content)
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(409, "Scontrino già importato. Aggiorna la pagina.") from error
        return {"status": "imported", "id": receipt.id, "line_count": len(parsed.lines)}

    @app.get("/api/receipts/{receipt_id}/pdf")
    def original(receipt_id: int, session: Database) -> FileResponse:
        receipt = session.get(Receipt, receipt_id)
        if receipt is None or not (pdf_directory / f"{receipt.file_hash}.pdf").exists():
            raise HTTPException(404, "PDF non disponibile.")
        return FileResponse(
            pdf_directory / f"{receipt.file_hash}.pdf",
            media_type="application/pdf",
            filename=receipt.filename,
            content_disposition_type="inline",
        )

    @app.delete("/api/receipts/{receipt_id}")
    def delete_receipt(receipt_id: int, session: Database) -> dict[str, bool]:
        receipt = session.get(Receipt, receipt_id)
        if receipt is None:
            raise HTTPException(404, "Scontrino non trovato.")
        path = pdf_directory / f"{receipt.file_hash}.pdf"
        session.delete(receipt)
        session.commit()
        path.unlink(missing_ok=True)
        return {"deleted": True}

    @app.patch("/api/products/{product_id}")
    def update_product(
        product_id: int, update: ProductUpdate, session: Database
    ) -> dict[str, bool]:
        product = session.get(Product, product_id)
        if product is None:
            raise HTTPException(404, "Prodotto non trovato.")
        if update.category_id is not None and session.get(Category, update.category_id) is None:
            raise HTTPException(422, "Categoria non valida.")
        if not update.name.strip():
            raise HTTPException(422, "Inserisci un nome.")
        product.name = update.name.strip()
        product.category_id = update.category_id
        product.reviewed = update.reviewed
        session.commit()
        return {"updated": True}

    @app.patch("/api/aliases/{alias_id}")
    def move_alias(alias_id: int, update: AliasUpdate, session: Database) -> dict[str, int]:
        alias = session.get(Alias, alias_id)
        if alias is None:
            raise HTTPException(404, "Descrizione non trovata.")
        if update.product_id is None:
            product = Product(name=alias.label, reviewed=False)
            session.add(product)
            session.flush()
        else:
            found = session.get(Product, update.product_id)
            if found is None:
                raise HTTPException(404, "Prodotto non trovato.")
            product = found
        alias.product_id = product.id
        session.commit()
        return {"product_id": product.id}

    @app.post("/api/categories", status_code=201)
    def add_category(update: CategoryUpdate, session: Database) -> dict[str, int]:
        if not update.name.strip():
            raise HTTPException(422, "Inserisci un nome.")
        category = Category(name=update.name.strip())
        session.add(category)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(409, "Questa categoria esiste già.") from error
        return {"id": category.id}

    @app.patch("/api/categories/{category_id}")
    def rename_category(
        category_id: int, update: CategoryUpdate, session: Database
    ) -> dict[str, bool]:
        category = session.get(Category, category_id)
        if category is None:
            raise HTTPException(404, "Categoria non trovata.")
        if not update.name.strip():
            raise HTTPException(422, "Inserisci un nome.")
        category.name = update.name.strip()
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(409, "Questa categoria esiste già.") from error
        return {"updated": True}

    return app


app = create_app()
