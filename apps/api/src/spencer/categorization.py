"""Conservative category hints from the original receipt descriptions."""

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from spencer.database import Alias, Category, Product

# Match whole product words (including common receipt abbreviations), not brand names.
CATEGORY_PATTERNS = (
    ("Latticini e uova", r"latte|yogurt|burro|mozzarella|ricotta|gorgonzola|uova|formaggio"),
    ("Pane e prodotti da forno", r"pane|focaccia|focaccine|focacc|pizza|pizzette|grissini|taralli"),
    ("Pasta, riso e cereali", r"pasta|riso|tortelloni|tortellini|gnocchi|spaghetti|penne"),
    ("Carne", r"pollo|tacchino|suino|manzo|vitello"),
    ("Pesce", r"platessa|salmone|merluzzo|sgombro|tonno|orata|branzino"),
    ("Salumi", r"prosciutto|salame|mortadella|speck|pancetta|bresaola"),
    ("Frutta e verdura", r"banane|arance|mele|pere|limoni|cetrioli|cipolline|melanzane|patate|pomodoro|pomodorino|pomodorini|lattuga|radicchio|uva|susine|carote"),
    ("Dolci e snack", r"biscotti|cioccolato|ghiaccioli|croissant"),
    ("Bevande", r"acqua|aranciata|succo"),
    ("Alcolici", r"birra|vino|gin|vodka|whisky"),
)


def receipt_category(labels: list[str], categories: dict[int, str]) -> int | None:
    matches = set()
    for label in labels:
        # These uses of "latte" do not establish a dairy product.
        if re.search(r"\blatte\b", label, re.IGNORECASE) and re.search(
            r"\b(mandorla|soia|avena|riso|cocco|vegetale|corpo|doccia|detergente)\b",
            label,
            re.IGNORECASE,
        ):
            return None
        candidates = [
            (match.start(), category)
            for category, words in CATEGORY_PATTERNS
            if (match := re.search(rf"\b(?:{words})\b", label, re.IGNORECASE))
        ]
        if candidates:
            # The main product usually precedes its ingredients: focaccia con pomodorini.
            position, category = min(candidates)
            if re.search(
                r"\b(burger|contorno|crocchette|sugo|ragù|ragu|torta|latte|crema)\b",
                label[:position],
                re.IGNORECASE,
            ):
                return None
            matches.add(category)
    if len(matches) != 1:
        return None
    return next((key for key, name in categories.items() if name in matches), None)


def categorize_missing_products(session: Session) -> None:
    categories = {category.id: category.name for category in session.scalars(select(Category))}
    for product in session.scalars(select(Product).where(Product.category_id.is_(None))):
        if "category_id" in json.loads(product.manual_fields):
            continue
        product.category_id = receipt_category(
            list(session.scalars(select(Alias.label).where(Alias.product_id == product.id))),
            categories,
        )
