import json
import re
from typing import Any

from app.catalog import Product


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
        part.capitalize()
        for part in key.replace("_", " ").replace("-", " ").split()
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
        "a", "an", "the", "and", "or", "for", "with", "of", "in",
        "is", "does", "have", "has", "show", "find", "looking", "under",
        "below", "above", "up", "to", "at", "least", "maximum", "minimum",
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
    category: str | None,
    max_price: float | None,
    product_type: str | None = None,
    condition: str | None = None,
    brand: str | None = None,
    max_weight_kg: float | None = None,
    min_ram_gb: int | None = None,
    min_storage_gb: int | None = None,
    attribute_filters: dict[str, Any] | None = None,
) -> list[str]:
    reasons: list[str] = []
    query_lower = query.casefold()

    if max_price is not None and product.price <= max_price:
        reasons.append(
            f"Within your budget (up to {product.currency} {max_price:,.0f})"
        )

    if category is not None and product.category.casefold() == category:
        reasons.append(f"Category: {product.category}")

    if product_type and (product.product_type or "").casefold() == product_type:
        reasons.append(f"Product type: {product.product_type}")

    if condition and (product.condition or "").casefold() == condition:
        reasons.append(f"Condition: {product.condition}")

    if brand and (product.brand or "").casefold() == brand:
        reasons.append(f"Brand: {product.brand}")

    if max_weight_kg is not None and product.weight_kg is not None:
        if product.weight_kg <= max_weight_kg:
            reasons.append(
                f"Weight: {product.weight_kg:g} kg "
                f"(your limit: {max_weight_kg:g} kg)"
            )

    if min_ram_gb is not None and product.ram_gb is not None:
        if product.ram_gb >= min_ram_gb:
            reasons.append(
                f"RAM: {product.ram_gb} GB "
                f"(minimum requested: {min_ram_gb} GB)"
            )

    if min_storage_gb is not None and product.storage_gb is not None:
        if product.storage_gb >= min_storage_gb:
            reasons.append(
                f"Storage: {product.storage_gb} GB "
                f"(minimum requested: {min_storage_gb} GB)"
            )

    if attribute_filters:
        for name, constraint in attribute_filters.items():
            reason = _attribute_reason(product, name, constraint)
            if reason:
                reasons.append(reason)

    # Generic explanations cite only attributes actually present in the product.
    reasons.extend(_mentioned_attribute_reasons(product, query))

    # Keep existing laptop query explanations until those behaviors are migrated.
    if max_weight_kg is None and any(
        word in query_lower for word in ("lightweight", "light weight", "portable")
    ):
        if product.weight_kg is not None:
            reasons.append(f"Weight: {product.weight_kg:g} kg")

    if any(word in query_lower for word in ("programming", "coding", "developer")):
        if product.processor:
            reasons.append(f"Processor: {product.processor}")
        if min_ram_gb is None and product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if min_ram_gb is None and ("ram" in query_lower or "memory" in query_lower):
        if product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if min_storage_gb is None and (
        "storage" in query_lower or "ssd" in query_lower
    ):
        if product.storage_gb is not None:
            reasons.append(f"Storage: {product.storage_gb} GB")

    return list(dict.fromkeys(reasons))[:6]
