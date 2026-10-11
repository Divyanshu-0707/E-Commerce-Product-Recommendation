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
) -> dict:
    """Search the catalog using existing filters and hybrid ranking."""
    query = query.strip()
    if not query:
        return {"error": "Search query must not be blank."}

    request = RecommendRequest(query=query)
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

    return {
        "products": [
            products_by_id[product_id].model_dump(mode="json")
            for product_id in product_ids
        ]
    }


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