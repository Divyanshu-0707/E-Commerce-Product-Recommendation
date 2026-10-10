import re
from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, Field, field_validator

from app.catalog import Product


class RecommendRequest(BaseModel):
    query: str
    category: str | None = None
    product_type: str | None = None
    condition: str | None = None
    brand: str | None = None
    max_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    max_weight_kg: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    min_ram_gb: int | None = Field(default=None, ge=0)
    min_storage_gb: int | None = Field(default=None, ge=0)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

    @field_validator("category", "product_type", "condition", "brand")
    @classmethod
    def normalize_text_filters(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip().casefold()


@dataclass(frozen=True)
class ResolvedFilters:
    category: str | None
    product_type: str | None
    condition: str | None
    brand: str | None
    max_price: float | None
    max_weight_kg: float | None
    min_ram_gb: int | None
    min_storage_gb: int | None


PRICE_PATTERN = re.compile(
    r"\b(?:under|below|less than|up to|upto|max(?:imum)?(?: price)?|"
    r"budget(?: of)?|within)\s*(?:₹|rs\.?|inr)?\s*"
    r"([\d,]+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\b",
    re.IGNORECASE,
)

WEIGHT_PATTERN = re.compile(
    r"\b(?:under|below|less than|at most|up to|lighter than|max(?:imum)?(?: weight)?)"
    r"\s*(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\b",
    re.IGNORECASE,
)

RAM_PATTERN = re.compile(
    r"\b(?:(?:at least|minimum(?: of)?|min(?:imum)?)\s*)?"
    r"(\d+)\s*gb\s*(?:of\s*)?(?:ram|memory)\b",
    re.IGNORECASE,
)

STORAGE_PATTERN = re.compile(
    r"\b(?:(?:at least|minimum(?: of)?|min(?:imum)?)\s*)?"
    r"(\d+(?:\.\d+)?)\s*(gb|tb)\s*(?:of\s*)?"
    r"(?:storage|ssd|hard drive|disk)\b",
    re.IGNORECASE,
)

TYPE_ALIASES = {
    "2 in 1 convertible": ("2 in 1 convertible", "2 in 1", "2-in-1"),
}

LEXICAL_STOP_WORDS = {
    "a", "an", "the", "for", "with", "and", "of", "in",
    "under", "below", "less", "than", "at", "most", "up",
    "to", "within", "budget", "maximum", "max", "laptop",
    "laptops", "kg", "kilogram", "kilograms", "gb", "tb",
    "ram", "memory", "storage", "ssd", "price",
}


def _normalized_phrase(value: str) -> str:
    return re.sub(r"[\s-]+", " ", value.casefold()).strip()


def _find_catalog_match(query: str, values: set[str]) -> str | None:
    normalized_query = _normalized_phrase(query)

    for value in sorted(values, key=len, reverse=True):
        aliases = TYPE_ALIASES.get(value.casefold(), (value,))

        for alias in aliases:
            phrase = _normalized_phrase(alias)
            if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_query):
                return value.casefold()

    return None


def extract_max_price(query: str) -> float | None:
    match = PRICE_PATTERN.search(query)
    if not match:
        return None

    # Avoid treating a weight or storage number as a price.
    remainder = query[match.end():]
    if re.match(r"\s*(?:kg|kilograms?|g|gb|tb)\b", remainder, re.IGNORECASE):
        return None

    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").casefold()

    if unit in {"k", "thousand"}:
        amount *= 1_000
    elif unit in {"lakh", "lac"}:
        amount *= 100_000

    return amount


def extract_max_weight(query: str) -> float | None:
    match = WEIGHT_PATTERN.search(query)
    return float(match.group(1)) if match else None


def extract_min_ram(query: str) -> int | None:
    match = RAM_PATTERN.search(query)
    return int(match.group(1)) if match else None


def extract_min_storage(query: str) -> int | None:
    match = STORAGE_PATTERN.search(query)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2).casefold()

    if unit == "tb":
        amount *= 1024

    return int(amount)


def resolve_filters(
    request: RecommendRequest,
    products: list[Product],
) -> ResolvedFilters:
    query = request.query
    query_lower = query.casefold()

    categories = {product.category for product in products}
    product_types = {
        product.product_type for product in products if product.product_type
    }
    conditions = {
        product.condition for product in products if product.condition
    }
    brands = {product.brand for product in products if product.brand}

    category = request.category
    if category is None and re.search(r"\blaptops?\b", query_lower):
        category = "laptop"
    if category is None:
        category = _find_catalog_match(query, categories)

    product_type = request.product_type
    if product_type is None:
        product_type = _find_catalog_match(query, product_types)

    condition = request.condition
    if condition is None:
        condition = _find_catalog_match(query, conditions)

    brand = request.brand
    if brand is None:
        brand = _find_catalog_match(query, brands)

    max_price = request.max_price
    if max_price is None:
        max_price = extract_max_price(query)

    max_weight_kg = request.max_weight_kg
    if max_weight_kg is None:
        max_weight_kg = extract_max_weight(query)

    min_ram_gb = request.min_ram_gb
    if min_ram_gb is None:
        min_ram_gb = extract_min_ram(query)

    min_storage_gb = request.min_storage_gb
    if min_storage_gb is None:
        min_storage_gb = extract_min_storage(query)

    return ResolvedFilters(
        category=category,
        product_type=product_type,
        condition=condition,
        brand=brand,
        max_price=max_price,
        max_weight_kg=max_weight_kg,
        min_ram_gb=min_ram_gb,
        min_storage_gb=min_storage_gb,
    )


def lexical_match_score(query: str, product: Product) -> float:
    query_terms = {
        token
        for token in re.findall(r"[a-z]+", query.casefold())
        if token not in LEXICAL_STOP_WORDS
    }
    if not query_terms:
        return 0.0

    product_text = " ".join(
        str(value or "")
        for value in (
            product.title,
            product.category,
            product.product_type,
            product.condition,
            product.brand,
            product.description,
            product.processor,
        )
    ).casefold()

    product_terms = set(re.findall(r"[a-z]+", product_text))
    return len(query_terms & product_terms) / len(query_terms)


def rank_products(
    products: list[Product],
    product_embeddings: np.ndarray,
    query_embedding: np.ndarray,
    query: str,
    filters: ResolvedFilters,
    limit: int = 10,
) -> list[tuple[Product, float]]:
    # Apply exact filters before ranking eligible products.
    eligible_indices = []

    for index, product in enumerate(products):
        if filters.category and product.category.casefold() != filters.category:
            continue
        if (
            filters.product_type
            and (product.product_type or "").casefold() != filters.product_type
        ):
            continue
        if (
            filters.condition
            and (product.condition or "").casefold() != filters.condition
        ):
            continue
        if filters.brand and (product.brand or "").casefold() != filters.brand:
            continue
        if filters.max_price is not None and product.price > filters.max_price:
            continue

        # Unknown measurements cannot satisfy a numeric filter.
        if filters.max_weight_kg is not None:
            if product.weight_kg is None or product.weight_kg > filters.max_weight_kg:
                continue
        if filters.min_ram_gb is not None:
            if product.ram_gb is None or product.ram_gb < filters.min_ram_gb:
                continue
        if filters.min_storage_gb is not None:
            if product.storage_gb is None or product.storage_gb < filters.min_storage_gb:
                continue

        eligible_indices.append(index)

    if not eligible_indices:
        return []

    eligible_vectors = product_embeddings[eligible_indices]
    semantic_scores = eligible_vectors @ query_embedding

    lexical_scores = np.array(
        [
            lexical_match_score(query, products[index])
            for index in eligible_indices
        ]
    )

    # Blend semantic meaning with exact keyword overlap.
    hybrid_scores = (
        0.8 * np.clip(semantic_scores, 0.0, 1.0)
        + 0.2 * lexical_scores
    )
    ranked_positions = np.argsort(-hybrid_scores)[:limit]

    return [
        (
            products[eligible_indices[position]],
            float(hybrid_scores[position]),
        )
        for position in ranked_positions
    ]