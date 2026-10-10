from app.catalog import Product


def build_reasons(
    product: Product,
    query: str,
    category: str | None,
    max_price: float | None,
) -> list[str]:
    reasons: list[str] = []
    query_lower = query.casefold()

    if max_price is not None and product.price <= max_price:
        reasons.append(f"Within your budget (up to ₹{max_price:,.0f})")

    if category is not None and product.category.casefold() == category:
        reasons.append(f"Category: {product.category}")

    if any(word in query_lower for word in ("lightweight", "light weight", "portable")):
        if product.weight_kg is not None:
            reasons.append(f"Weight: {product.weight_kg:g} kg")

    if any(word in query_lower for word in ("programming", "coding", "developer")):
        if product.processor:
            reasons.append(f"Processor: {product.processor}")
        if product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if "ram" in query_lower or "memory" in query_lower:
        if product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if "storage" in query_lower or "ssd" in query_lower:
        if product.storage_gb is not None:
            reasons.append(f"Storage: {product.storage_gb} GB")

    # Keep the card reasons short and avoid repeating the same fact.
    return list(dict.fromkeys(reasons))[:3]