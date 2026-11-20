"""Durable classification of category and sales type using the local model."""

import json
import logging
import time
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from spencer.database import Alias, Category, Product, ProductKind, Purchase

logger = logging.getLogger(__name__)


class CategoryResearch(Protocol):
    async def classify_product(
        self, labels: list[str], categories: dict[int, str]
    ) -> tuple[int | None, ProductKind]: ...


class CategoryWorker:
    def __init__(self, engine: Engine, research: CategoryResearch) -> None:
        self.engine = engine
        self.research = research

    def resume(self) -> None:
        with Session(self.engine) as session:
            for product in session.scalars(select(Product)):
                protected = json.loads(product.manual_fields)
                if (product.category_id is not None or "category_id" in protected) and (
                    product.kind != "unknown" or "kind" in protected
                ):
                    product.category_status = "done"
                elif product.category_status in ("running", "retry", "failed"):
                    product.category_status = "pending"
                    product.category_attempts = 0
                    product.category_after = 0
            session.commit()

    async def run_once(self) -> bool:
        with Session(self.engine) as session:
            product = session.scalar(
                select(Product)
                .where(
                    (Product.category_id.is_(None) & ~Product.manual_fields.contains('"category_id"'))
                    | ((Product.kind == "unknown") & ~Product.manual_fields.contains('"kind"')),
                    Product.category_status.in_(("pending", "retry")),
                    Product.category_after <= time.time(),
                    Product.id.in_(
                        select(Alias.product_id).join(Purchase, Purchase.alias_id == Alias.id)
                    ),
                )
                .order_by(Product.id)
                .limit(1)
            )
            if product is None:
                return False
            product.category_status = "running"
            product.category_attempts += 1
            product_id, revision = product.id, product.search_revision
            labels = list(session.scalars(select(Alias.label).where(Alias.product_id == product.id)))
            categories = {c.id: c.name for c in session.scalars(select(Category))}
            session.commit()
        category_id = None
        kind: ProductKind = "unknown"
        failed = False
        try:
            category_id, kind = await self.research.classify_product(labels, categories)
        except Exception:
            logger.warning("Category classification failed for product %s", product_id, exc_info=False)
            failed = True
        with Session(self.engine) as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            product = session.get(Product, product_id)
            if product is None or product.search_revision != revision:
                return True
            protected = json.loads(product.manual_fields)
            needs_category = product.category_id is None and "category_id" not in protected
            needs_kind = product.kind == "unknown" and "kind" not in protected
            if not needs_category and not needs_kind:
                product.category_status = "done"
            elif failed:
                product.category_status = "retry" if product.category_attempts < 3 else "failed"
                product.category_after = time.time() + 60 * product.category_attempts
            else:
                # Categories can be deleted or edited while the model is running.
                if category_id is not None and session.get(Category, category_id) is None:
                    category_id = None
                if needs_category:
                    product.category_id = category_id
                if needs_kind:
                    product.kind = kind
                product.category_status = (
                    "not_found" if needs_category and category_id is None else "done"
                )
            session.commit()
        return True
