from app.catalog import Product


def build_product_text(product: Product) -> str:
    """Create descriptive text for semantic search from a product record."""
    parts = [
        f"Product: {product.title}",
        f"Category: {product.category}",
    ]

    if product.product_type:
        parts.append(f"Product type: {product.product_type}")

    if product.condition:
        parts.append(f"Condition: {product.condition}")

    if product.brand:
        parts.append(f"Brand: {product.brand}")

    parts.append(f"Price: ₹{product.price:g}")

    if product.description:
        parts.append(f"Description: {product.description}")

    if product.weight_kg is not None:
        parts.append(f"Weight: {product.weight_kg:g} kg")

    if product.processor:
        parts.append(f"Processor: {product.processor}")

    if product.ram_gb is not None:
        parts.append(f"RAM: {product.ram_gb} GB")

    if product.storage_gb is not None:
        parts.append(f"Storage: {product.storage_gb} GB")

    return "\n".join(parts)