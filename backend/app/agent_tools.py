from typing import Any

from app.catalog import Product
from app.embeddings import ProductEmbeddingModel
from app.reasons import build_reasons
from app.recommendation import (
    RecommendRequest,
    rank_products,
    resolve_filters,
)


def search_products_tool(
    query: str,
    products: list[Product],
    embedding_model: ProductEmbeddingModel,
    product_embeddings,
    *,
    category: str | None = None,
    max_price: float | None = None,
    attribute_filters: dict[str, Any] | None = None,
) -> dict:
    """Search the catalog with validated hard filters and hybrid ranking."""
    query = query.strip()
    if not query:
        return {"error": "Search query must not be blank."}

    request = RecommendRequest.model_validate(
        {
            "query": query,
            "category": category,
            "max_price": max_price,
            "attribute_filters": attribute_filters or {},
        }
    )
    filters = resolve_filters(request, products)
    query_embedding = embedding_model.embed_query(query)

    ranked = rank_products(
        products=products,
        product_embeddings=product_embeddings,
        query_embedding=query_embedding,
        query=query,
        filters=filters,
        limit=5,
    )

    results = []
    for product, score in ranked:
        results.append(
            {
                "product": product.model_dump(mode="json"),
                "score": float(score),
                "reasons": build_reasons(
                    product=product,
                    query=query,
                    category=filters.category,
                    max_price=filters.max_price,
                    product_type=filters.product_type,
                    condition=filters.condition,
                    brand=filters.brand,
                    max_weight_kg=filters.max_weight_kg,
                    min_ram_gb=filters.min_ram_gb,
                    min_storage_gb=filters.min_storage_gb,
                    attribute_filters=filters.attribute_filters,
                ),
            }
        )

    return {"results": results, "count": len(results)}


def compare_products_tool(
    product_ids: list[str],
    products: list[Product],
) -> dict:
    """Return catalog data for exactly two products to compare."""
    if len(product_ids) != 2:
        return {"error": "Provide exactly two product IDs to compare."}

    if product_ids[0] == product_ids[1]:
        return {"error": "Choose two different product IDs."}

    products_by_id = {product.id: product for product in products}
    missing_ids = [
        product_id
        for product_id in product_ids
        if product_id not in products_by_id
    ]

    if missing_ids:
        return {
            "error": "Product ID not found.",
            "missing_product_ids": missing_ids,
        }

    selected_products = [products_by_id[product_id] for product_id in product_ids]
    product_records = [
        product.model_dump(mode="json") for product in selected_products
    ]

    common_fields = ("title", "category", "brand", "price", "currency")
    comparison_rows = [
        {
            "field": field,
            "values": [getattr(product, field) for product in selected_products],
        }
        for field in common_fields
    ]

    attribute_names: dict[str, str] = {}
    for product in selected_products:
        for name in product.attributes:
            normalized_name = str(name).casefold()
            attribute_names.setdefault(normalized_name, str(name))

    for normalized_name, display_name in sorted(attribute_names.items()):
        values = []
        for product in selected_products:
            values_by_name = {
                str(name).casefold(): value
                for name, value in product.attributes.items()
            }
            values.append(values_by_name.get(normalized_name))
        comparison_rows.append(
            {
                "field": f"attributes.{display_name}",
                "values": values,
            }
        )

    return {"products": product_records, "comparison_rows": comparison_rows}


def get_product_details_tool(
    product_id: str,
    products: list[Product],
) -> dict:
    """Look up one product's catalog data for a grounded answer."""
    product = next(
        (item for item in products if item.id == product_id),
        None,
    )

    if product is None:
        return {"error": f"Product ID {product_id!r} was not found."}

    return {"product": product.model_dump(mode="json")}
