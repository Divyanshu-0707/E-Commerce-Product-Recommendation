import json
import re
from typing import Any

from app.catalog import Product
from app.recommendation import ResolvedFilters


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _attribute_label(key: str) -> str:
    return " ".join(
        part.capitalize() for part in key.replace("_", " ").replace("-", " ").split()
    )


def _attribute_reason(
    product: Product,
    name: str,
    constraint: Any,
) -> str | None:
    matching_values = [
        value
        for key, value in product.attributes.items()
        if str(key).casefold() == name.casefold()
    ]
    if len(matching_values) != 1 or matching_values[0] is None:
        return None

    actual = matching_values[0]
    label = _attribute_label(name)
    details: list[str] = []
    if constraint.eq is not None:
        details.append(f"requested {_format_value(constraint.eq)}")
    if constraint.gte is not None and constraint.lte is not None:
        details.append(
            f"requested range {_format_value(constraint.gte)}–"
            f"{_format_value(constraint.lte)}"
        )
    elif constraint.gte is not None:
        details.append(f"minimum {_format_value(constraint.gte)}")
    elif constraint.lte is not None:
        details.append(f"maximum {_format_value(constraint.lte)}")

    suffix = f" ({'; '.join(details)})" if details else ""
    return f"{label}: {_format_value(actual)}{suffix}"


def _mentioned_attribute_reasons(product: Product, query: str) -> list[str]:
    query_terms = set(re.findall(r"[a-z0-9]+", query.casefold()))
    stop_words = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "for",
        "with",
        "of",
        "in",
        "is",
        "does",
        "have",
        "has",
        "show",
        "find",
        "looking",
        "under",
        "below",
        "above",
        "up",
        "to",
        "at",
        "least",
        "maximum",
        "minimum",
    }
    query_terms -= stop_words

    reasons = []
    for key in sorted(product.attributes, key=str):
        value = product.attributes[key]
        if value is None:
            continue
        searchable = f"{key} {_format_value(value)}".replace("_", "-")
        attribute_terms = set(re.findall(r"[a-z0-9]+", searchable.casefold()))
        if query_terms & attribute_terms:
            reasons.append(f"{_attribute_label(str(key))}: {_format_value(value)}")
    return reasons


def build_reasons(
    product: Product,
    query: str,
    filters: ResolvedFilters,
) -> list[str]:
    reasons: list[str] = []
    query_lower = query.casefold()

    if filters.max_price is not None and product.price <= filters.max_price:
        reasons.append(
            f"Within your budget (up to {product.currency} {filters.max_price:,.0f})"
        )

    if filters.category is not None and product.category.casefold() == filters.category:
        reasons.append(f"Category: {product.category}")

    if (
        filters.product_type
        and (product.product_type or "").casefold() == filters.product_type
    ):
        reasons.append(f"Product type: {product.product_type}")

    if filters.condition and (product.condition or "").casefold() == filters.condition:
        reasons.append(f"Condition: {product.condition}")

    if filters.brand and (product.brand or "").casefold() == filters.brand:
        reasons.append(f"Brand: {product.brand}")

    if filters.max_weight_kg is not None and product.weight_kg is not None:
        if product.weight_kg <= filters.max_weight_kg:
            reasons.append(
                f"Weight: {product.weight_kg:g} kg "
                f"(your limit: {filters.max_weight_kg:g} kg)"
            )

    if filters.min_ram_gb is not None and product.ram_gb is not None:
        if product.ram_gb >= filters.min_ram_gb:
            reasons.append(
                f"RAM: {product.ram_gb} GB "
                f"(minimum requested: {filters.min_ram_gb} GB)"
            )

    if filters.min_storage_gb is not None and product.storage_gb is not None:
        if product.storage_gb >= filters.min_storage_gb:
            reasons.append(
                f"Storage: {product.storage_gb} GB "
                f"(minimum requested: {filters.min_storage_gb} GB)"
            )

    for name, constraint in filters.attribute_filters.items():
        reason = _attribute_reason(product, name, constraint)
        if reason:
            reasons.append(reason)

    reasons.extend(_mentioned_attribute_reasons(product, query))

    # Include stored specs for common laptop requests.
    if filters.max_weight_kg is None and any(
        word in query_lower for word in ("lightweight", "light weight", "portable")
    ):
        if product.weight_kg is not None:
            reasons.append(f"Weight: {product.weight_kg:g} kg")

    if any(word in query_lower for word in ("programming", "coding", "developer")):
        if product.processor:
            reasons.append(f"Processor: {product.processor}")
        if filters.min_ram_gb is None and product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if filters.min_ram_gb is None and ("ram" in query_lower or "memory" in query_lower):
        if product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if filters.min_storage_gb is None and (
        "storage" in query_lower or "ssd" in query_lower
    ):
        if product.storage_gb is not None:
            reasons.append(f"Storage: {product.storage_gb} GB")

    return list(dict.fromkeys(reasons))[:6]
