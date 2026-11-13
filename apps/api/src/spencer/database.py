import os
from pathlib import Path

from sqlalchemy import ForeignKey, UniqueConstraint, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    reviewed: Mapped[bool] = mapped_column(default=False)


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = (UniqueConstraint("retailer", "label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    retailer: Mapped[str]
    label: Mapped[str]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (UniqueConstraint("identity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    file_hash: Mapped[str] = mapped_column(unique=True)
    filename: Mapped[str]
    identity: Mapped[str | None]
    retailer: Mapped[str] = mapped_column(default="Esselunga")
    store: Mapped[str] = mapped_column(default="")
    date: Mapped[str | None]
    document: Mapped[str | None]
    status: Mapped[str]
    error: Mapped[str | None]
    total_cents: Mapped[int] = mapped_column(default=0)
    voucher_cents: Mapped[int] = mapped_column(default=0)
    paid_cents: Mapped[int] = mapped_column(default=0)
    payments: Mapped[str] = mapped_column(default="[]")
    lines: Mapped[list["Purchase"]] = relationship(cascade="all, delete-orphan")


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"))
    alias_id: Mapped[int] = mapped_column(ForeignKey("aliases.id"))
    position: Mapped[int]
    gross_cents: Mapped[int]
    discount_cents: Mapped[int]
    price_verified: Mapped[bool] = mapped_column(default=True)
    discount_label: Mapped[str] = mapped_column(default="")


CATEGORIES = [
    "Frutta e verdura",
    "Carne",
    "Pesce",
    "Salumi",
    "Latticini e uova",
    "Pasta, riso e cereali",
    "Pane e prodotti da forno",
    "Dolci e snack",
    "Surgelati",
    "Dispensa e condimenti",
    "Bevande",
    "Alcolici",
    "Casa",
    "Cura della persona",
]


def data_directory() -> Path:
    return Path(os.environ.get("SPENCER_DATA_DIR", Path(__file__).resolve().parents[4] / "data"))


def database_engine(directory: Path) -> Engine:
    directory.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{directory / 'spencer.sqlite3'}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection: object, _: object) -> None:
        # SQLAlchemy exposes the underlying DBAPI connection in this event.
        connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]

    return engine
