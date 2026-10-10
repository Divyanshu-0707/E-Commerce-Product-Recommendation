from app.catalog import Product


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
) -> list[str]:
    reasons: list[str] = []
    query_lower = query.casefold()

    if max_price is not None and product.price <= max_price:
        reasons.append(f"Within your budget (up to INR {max_price:,.0f})")

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

    if min_ram_gb is None and (
        "ram" in query_lower or "memory" in query_lower
    ):
        if product.ram_gb is not None:
            reasons.append(f"RAM: {product.ram_gb} GB")

    if min_storage_gb is None and (
        "storage" in query_lower or "ssd" in query_lower
    ):
        if product.storage_gb is not None:
            reasons.append(f"Storage: {product.storage_gb} GB")

    return list(dict.fromkeys(reasons))[:6]