import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from app.catalog import Product
from app.search_text import build_product_text


class AttributeConstraint(BaseModel):
    """Hard conditions that may be applied to any product attribute."""

    model_config = ConfigDict(extra="forbid")

    eq: StrictStr | StrictInt | StrictFloat | StrictBool | None = None
    gte: float | None = Field(default=None, allow_inf_nan=False)
    lte: float | None = Field(default=None, allow_inf_nan=False)

    @field_validator("gte", "lte", mode="before")
    @classmethod
    def numeric_constraints_must_be_numbers(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("gte and lte attribute constraints must be numeric")
        return value

    @model_validator(mode="after")
    def constraint_must_be_satisfiable(self) -> "AttributeConstraint":
        if self.eq is None and self.gte is None and self.lte is None:
            raise ValueError("Provide at least one of eq, gte, or lte")
        if self.gte is not None and self.lte is not None and self.gte > self.lte:
            raise ValueError("gte cannot be greater than lte")
        return self


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
    attribute_filters: dict[str, AttributeConstraint] = Field(default_factory=dict)

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

    @field_validator("attribute_filters")
    @classmethod
    def normalize_attribute_filter_names(
        cls,
        value: dict[str, AttributeConstraint],
    ) -> dict[str, AttributeConstraint]:
        normalized: dict[str, AttributeConstraint] = {}
        for name, constraint in value.items():
            key = name.strip().casefold()
            if not key:
                raise ValueError("Attribute filter names must not be blank")
            if key in normalized:
                raise ValueError(f"Duplicate attribute filter name: {name!r}")
            normalized[key] = constraint
        return normalized


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
    attribute_filters: dict[str, AttributeConstraint]


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

CATEGORY_ALIASES = {
    "laptop": ("laptops",),
    "smartphone": ("smartphones", "phone", "phones", "mobile phone", "mobile phones"),
    "headphones": ("headphone",),
    "tablet": ("tablets",),
    "clothing": ("clothes",),
    "shoes": ("shoe",),
    "home_kitchen": ("home kitchen", "home and kitchen", "home & kitchen"),
    "books": ("book",),
    "sports_fitness": ("sports fitness", "sports and fitness", "sports & fitness"),
    "beauty": ("beauty products",),
    "toys_games": ("toys games", "toys and games", "toys & games", "toy", "toys"),
}

LEXICAL_STOP_WORDS = {
    "a",
    "an",
    "the",
    "for",
    "with",
    "and",
    "of",
    "in",
    "under",
    "below",
    "less",
    "than",
    "at",
    "most",
    "up",
    "to",
    "within",
    "budget",
    "maximum",
    "max",
    "laptop",
    "laptops",
    "kg",
    "kilogram",
    "kilograms",
    "gb",
    "tb",
    "ram",
    "memory",
    "storage",
    "ssd",
    "price",
}

# Ignore shopping phrases when checking product names.
SEARCH_FILLER_WORDS = {
    "a",
    "an",
    "the",
    "for",
    "with",
    "and",
    "of",
    "in",
    "to",
    "at",
    "i",
    "me",
    "my",
    "you",
    "your",
    "please",
    "want",
    "need",
    "buy",
    "find",
    "show",
    "recommend",
    "looking",
    "search",
    "get",
    "some",
    "any",
    "can",
    "could",
    "would",
    "like",
    "is",
    "are",
    "there",
    "do",
    "have",
    "good",
    "best",
    "product",
    "products",
    "item",
    "items",
    "available",
    "catalog",
    "all",
    "few",
    "list",
    "suggest",
    "give",
    "options",
}


def search_terms(text: str) -> set[str]:
    """Normalize search words and common plurals."""
    terms = set()
    for word in re.findall(r"[^\W_]+", text.casefold()):
        if word in SEARCH_FILLER_WORDS:
            continue
        if word.isdecimal():
            word = word.lstrip("0") or "0"
        elif len(word) > 4 and word.endswith("ies"):
            word = word[:-3] + "y"
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        terms.add(word)
    return terms


def query_product_terms(query: str) -> set[str]:
    """Remove parsed limits and soft preferences from the product request."""
    for pattern in (WEIGHT_PATTERN, RAM_PATTERN, STORAGE_PATTERN):
        query = pattern.sub(" ", query)
    if extract_max_price(query) is not None:
        query = PRICE_PATTERN.sub(" ", query)

    # Use cases affect ranking, not which product was requested.
    query = re.sub(
        r"\b(?:for\s+)?(?:programming|coding|music|work|daily use)\b",
        " ",
        query,
        flags=re.IGNORECASE,
    )
    query = re.sub(r"\blightweight\b", "weight", query, flags=re.IGNORECASE)
    for category, aliases in CATEGORY_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            query = re.sub(
                rf"(?<!\w){re.escape(alias)}(?!\w)",
                category,
                query,
                flags=re.IGNORECASE,
            )
    return search_terms(query)


def product_matches_query(
    product: Product,
    query_terms: set[str],
    filters: ResolvedFilters,
) -> bool:
    """Check product words before applying similarity scores."""
    if not query_terms:
        return any((filters.category, filters.product_type, filters.brand))
    # Generated descriptions contain boilerplate that is not product evidence.
    fields = [product.title, product.category, product.brand or ""]
    identity_fields = list(fields)
    for name, value in product.attributes.items():
        if value is None or value is False:
            continue
        fields.extend((str(name), str(value)))
        # Color and care text alone can match unrelated products.
        if name not in {"color", "shade", "care"}:
            identity_fields.extend((str(name), str(value)))
    product_terms = search_terms(" ".join(fields))
    identity_terms = search_terms(" ".join(identity_fields))
    return query_terms <= product_terms and bool(query_terms & identity_terms)


def _normalized_phrase(value: str) -> str:
    return re.sub(r"[\s-]+", " ", value.casefold()).strip()


def _find_catalog_match(
    query: str,
    values: set[str],
    aliases_by_value: dict[str, tuple[str, ...]] = TYPE_ALIASES,
) -> str | None:
    normalized_query = _normalized_phrase(query)

    for value in sorted(values, key=len, reverse=True):
        aliases = (value,) + aliases_by_value.get(value.casefold(), ())

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
    remainder = query[match.end() :]
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
    conditions = {product.condition for product in products if product.condition}
    brands = {product.brand for product in products if product.brand}

    category = request.category
    if category is not None:
        normalized_category = _normalized_phrase(category)
        for value in categories:
            names = (value,) + CATEGORY_ALIASES.get(value.casefold(), ())
            normalized_names = [_normalized_phrase(name) for name in names]
            if normalized_category in normalized_names:
                category = value.casefold()
                break
    if category is None and re.search(r"\blaptops?\b", query_lower):
        category = "laptop"
    if category is None:
        category = _find_catalog_match(query, categories, CATEGORY_ALIASES)

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
    # An explicit null clears the budget; an omitted field uses the query.
    if "max_price" not in request.model_fields_set:
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
        attribute_filters=request.attribute_filters,
    )


def _filter_checks(product: Product, filters: ResolvedFilters) -> dict[str, bool]:
    """Check active filters in the order shown in no-match messages."""
    checks = {}
    if filters.category:
        checks[f"category '{filters.category}'"] = (
            product.category.casefold() == filters.category
        )
    if filters.product_type:
        checks[f"product type '{filters.product_type}'"] = (
            product.product_type or ""
        ).casefold() == filters.product_type
    if filters.condition:
        checks[f"condition '{filters.condition}'"] = (
            product.condition or ""
        ).casefold() == filters.condition
    if filters.brand:
        checks[f"brand '{filters.brand}'"] = (
            product.brand or ""
        ).casefold() == filters.brand
    if filters.max_price is not None:
        checks[f"maximum price INR {filters.max_price:g}"] = (
            product.price <= filters.max_price
        )
    if filters.max_weight_kg is not None:
        checks[f"maximum weight {filters.max_weight_kg:g} kg"] = (
            product.weight_kg is not None and product.weight_kg <= filters.max_weight_kg
        )
    if filters.min_ram_gb is not None:
        checks[f"minimum RAM {filters.min_ram_gb} GB"] = (
            product.ram_gb is not None and product.ram_gb >= filters.min_ram_gb
        )
    if filters.min_storage_gb is not None:
        checks[f"minimum storage {filters.min_storage_gb} GB"] = (
            product.storage_gb is not None
            and product.storage_gb >= filters.min_storage_gb
        )
    for name, constraint in filters.attribute_filters.items():
        checks[f"attribute '{name}'"] = _attribute_constraint_matches(
            product, name, constraint
        )
    return checks


def no_results_message(
    filters: ResolvedFilters,
    products: list[Product] | None = None,
    query: str | None = None,
) -> str:
    """Explain no matches without relaxing the filters."""
    details = []
    for label, value in (
        ("category", filters.category),
        ("product type", filters.product_type),
        ("condition", filters.condition),
        ("brand", filters.brand),
        ("maximum price", filters.max_price),
        ("maximum weight (kg)", filters.max_weight_kg),
        ("minimum RAM (GB)", filters.min_ram_gb),
        ("minimum storage (GB)", filters.min_storage_gb),
    ):
        if value is not None:
            display = f"{value:g}" if isinstance(value, (int, float)) else value
            details.append(f"{label}: {display}")

    for name, constraint in filters.attribute_filters.items():
        for operator, value in (
            ("=", constraint.eq),
            (">=", constraint.gte),
            ("<=", constraint.lte),
        ):
            if value is not None:
                details.append(f"{name} {operator} {value}")

    if products is not None and not products:
        return "No catalog products are available for this search."

    filter_results = []
    if products is not None:
        filter_results = [_filter_checks(product, filters) for product in products]
    if query is not None and any(all(checks.values()) for checks in filter_results):
        return (
            "No catalog products match the requested product details. "
            "Try a product name or category from the catalog. "
            "Unrelated products have not been substituted."
        )

    message = (
        "No catalog products match all of these filters: "
        + ("; ".join(details) if details else "no explicit filters")
        + "."
    )

    if products is not None:
        remaining = filter_results
        counts = [f"{len(products)} total"]
        for label in filter_results[0]:
            remaining = [checks for checks in remaining if checks[label]]
            counts.append(f"{label}: {len(remaining)}")
            if not remaining:
                break
        message += " Filtering in order: " + " -> ".join(counts) + "."

    return message + " Change one or more filters and search again."


_MISSING_ATTRIBUTE = object()


def _get_product_attribute(product: Product, name: str) -> Any:
    normalized_name = name.casefold()
    matches = [
        value
        for key, value in product.attributes.items()
        if str(key).casefold() == normalized_name
    ]
    if len(matches) != 1:
        return _MISSING_ATTRIBUTE
    return matches[0]


def _attribute_constraint_matches(
    product: Product,
    name: str,
    constraint: AttributeConstraint,
) -> bool:
    actual = _get_product_attribute(product, name)
    if actual is _MISSING_ATTRIBUTE:
        return False

    if constraint.eq is not None:
        expected = constraint.eq
        if isinstance(expected, bool):
            if not isinstance(actual, bool) or actual is not expected:
                return False
        elif isinstance(expected, str):
            if not isinstance(actual, str) or actual.casefold() != expected.casefold():
                return False
        elif (
            isinstance(actual, bool)
            or not isinstance(actual, (int, float))
            or actual != expected
        ):
            return False

    if constraint.gte is not None:
        if (
            isinstance(actual, bool)
            or not isinstance(actual, (int, float))
            or actual < constraint.gte
        ):
            return False

    if constraint.lte is not None:
        if (
            isinstance(actual, bool)
            or not isinstance(actual, (int, float))
            or actual > constraint.lte
        ):
            return False

    return True


def _text_match_score(query: str, product_text: str) -> float:
    query_terms = {
        token
        for token in re.findall(r"[a-z]+", query.casefold())
        if token not in LEXICAL_STOP_WORDS
    }
    if not query_terms:
        return 0.0
    product_terms = set(re.findall(r"[a-z]+", product_text.casefold()))
    return len(query_terms & product_terms) / len(query_terms)


def lexical_match_score(query: str, product: Product) -> float:
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

    return _text_match_score(query, product_text)


def keyword_match_score(query: str, product: Product) -> float:
    """Score text overlap across the product record for fallback search."""
    return _text_match_score(query, build_product_text(product))


def rank_products(
    products: list[Product],
    product_embeddings: np.ndarray | None,
    query_embedding: np.ndarray | None,
    query: str,
    filters: ResolvedFilters,
    limit: int = 10,
) -> list[tuple[Product, float]]:
    # Apply exact filters before ranking eligible products.
    query_terms = query_product_terms(query)
    eligible_indices = []

    for index, product in enumerate(products):
        if not all(_filter_checks(product, filters).values()):
            continue

        if not product_matches_query(product, query_terms, filters):
            continue

        eligible_indices.append(index)

    if not eligible_indices:
        return []

    if product_embeddings is None or query_embedding is None:
        # Use keyword scores when embeddings are unavailable.
        scores = np.array(
            [keyword_match_score(query, products[index]) for index in eligible_indices]
        )
    else:
        eligible_vectors = product_embeddings[eligible_indices]
        semantic_scores = eligible_vectors @ query_embedding

        lexical_scores = np.array(
            [lexical_match_score(query, products[index]) for index in eligible_indices]
        )

        # Blend semantic similarity with keyword overlap.
        scores = 0.8 * np.clip(semantic_scores, 0.0, 1.0) + 0.2 * lexical_scores

    ranked_positions = np.argsort(-scores)[:limit]

    results = []
    for position in ranked_positions:
        product_index = eligible_indices[position]
        product = products[product_index]
        score = float(scores[position])
        results.append((product, score))
    return results
