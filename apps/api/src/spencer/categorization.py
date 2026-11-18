"""Independent, durable category classification using the local model."""

import json
import logging
import time
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from spencer.database import Alias, Category, Product, Purchase

logger = logging.getLogger(__name__)


class CategoryResearch(Protocol):
    async def classify_category(
        self, labels: list[str], categories: dict[int, str]
    ) -> int | None: ...


class CategoryWorker:
    def __init__(self, engine: Engine, research: CategoryResearch) -> None:
        self.engine = engine
        self.research = research

    def resume(self) -> None:
        with Session(self.engine) as session:
            for product in session.scalars(select(Product)):
                if product.category_id is not None or "category_id" in json.loads(product.manual_fields):
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
                    Product.category_id.is_(None),
                    ~Product.manual_fields.contains('"category_id"'),
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
        failed = False
        try:
            category_id = await self.research.classify_category(labels, categories)
        except Exception:
            logger.warning("Category classification failed for product %s", product_id, exc_info=False)
            failed = True
        with Session(self.engine) as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            product = session.get(Product, product_id)
            if product is None or product.search_revision != revision:
                return True
            if product.category_id is not None or "category_id" in json.loads(product.manual_fields):
                product.category_status = "done"
            elif failed:
                product.category_status = "retry" if product.category_attempts < 3 else "failed"
                product.category_after = time.time() + 60 * product.category_attempts
            else:
                # Categories can be deleted or edited while the model is running.
                if category_id is not None and session.get(Category, category_id) is None:
                    category_id = None
                product.category_id = category_id
                product.category_status = "done" if category_id is not None else "not_found"
            session.commit()
        return True
