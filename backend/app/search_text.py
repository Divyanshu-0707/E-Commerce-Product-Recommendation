from typing import Any

from app.catalog import Product


def _display_attribute_value(value: Any) -> str | None:
    """Flatten nested attributes for search, skipping missing values."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value, key=str):
            display_value = _display_attribute_value(value[key])
            if display_value:
                parts.append(f"{key}: {display_value}")
        return ", ".join(parts) or None
    if isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            display_value = _display_attribute_value(item)
            if display_value:
                parts.append(display_value)
        return ", ".join(parts) or None

    text = str(value).strip()
    return text or None


def _attribute_label(key: str) -> str:
    return " ".join(key.replace("_", " ").replace("-", " ").split())


def build_product_text(product: Product) -> str:
    """Keep field order stable so embedding caches can be reused."""
    parts = [
        f"Product: {product.title}",
        f"Category: {product.category}",
    ]

    if product.brand:
        parts.append(f"Brand: {product.brand}")

    parts.append(f"Price: {product.price:g} {product.currency}")

    if product.description:
        parts.append(f"Description: {product.description}")

    for key in sorted(product.attributes, key=str):
        display_value = _display_attribute_value(product.attributes[key])
        if display_value:
            parts.append(f"{_attribute_label(str(key))}: {display_value}")

    return "\n".join(parts)
