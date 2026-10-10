import re

import numpy as np
from pydantic import BaseModel, Field, field_validator

from app.catalog import Product


class RecommendRequest(BaseModel):
    query: str
    category: str | None = None
    max_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip().casefold()


PRICE_PATTERN = re.compile(
    r"\b(?:under|below|less than|up to|upto|max(?:imum)?(?: price)?|"
    r"budget(?: of)?|within)\s*(?:₹|rs\.?|inr)?\s*"
    r"([\d,]+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\b",
    re.IGNORECASE,
)


def extract_max_price(query: str) -> float | None:
    match = PRICE_PATTERN.search(query)
    if not match:
        return None

    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").casefold()

    if unit in {"k", "thousand"}:
        amount *= 1_000
    elif unit in {"lakh", "lac"}:
        amount *= 100_000

    return amount


def resolve_filters(
    request: RecommendRequest,
) -> tuple[str | None, float | None]:
    category = request.category
    if category is None and re.search(r"\blaptops?\b", request.query, re.IGNORECASE):
        category = "laptop"

    max_price = request.max_price
    if max_price is None:
        max_price = extract_max_price(request.query)

    return category, max_price


def rank_products(
    products: list[Product],
    product_embeddings: np.ndarray,
    query_embedding: np.ndarray,
    category: str | None,
    max_price: float | None,
    limit: int = 10,
) -> list[tuple[Product, float]]:
    # Apply exact filters first. Only eligible products are semantically ranked.
    eligible_indices = [
        index
        for index, product in enumerate(products)
        if (category is None or product.category.casefold() == category)
        and (max_price is None or product.price <= max_price)
    ]

    if not eligible_indices:
        return []

    eligible_vectors = product_embeddings[eligible_indices]
    similarities = eligible_vectors @ query_embedding

    ranked_positions = np.argsort(-similarities)[:limit]

    return [
        (
            products[eligible_indices[position]],
            max(0.0, min(1.0, float(similarities[position]))),
        )
        for position in ranked_positions
    ]