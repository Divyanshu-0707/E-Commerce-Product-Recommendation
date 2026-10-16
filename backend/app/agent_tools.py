from typing import Any

from app.catalog import Product
from app.embeddings import ProductEmbeddingModel
from app.reasons import build_reasons
from app.recommendation import (
    RecommendRequest,
    no_results_message,
    rank_products,
    resolve_filters,
)


def search_products_tool(
    query: str,
    products: list[Product],
    embedding_model: ProductEmbeddingModel | None,
    product_embeddings,
    *,
    category: str | None = None,
    max_price: float | None = None,
    attribute_filters: dict[str, Any] | None = None,
) -> dict:
    """Search the catalog with the same filters as the web form."""
    query = query.strip()
    if not query:
        return {"error": "Search query must not be blank."}

    request_data = {
        "query": query,
        "category": category,
        "attribute_filters": attribute_filters or {},
    }
    # Omit an unspecified budget so the query can supply it.
    if max_price is not None:
        request_data["max_price"] = max_price
    request = RecommendRequest.model_validate(request_data)
    filters = resolve_filters(request, products)
    query_embedding = None
    if embedding_model is not None:
        try:
            query_embedding = embedding_model.embed_query(query)
        except Exception:
            # Fall back to keyword search.
            query_embedding = None

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
                "reasons": build_reasons(product, query, filters),
            }
        )

    response = {"results": results, "count": len(results)}
    if not results:
        response["message"] = no_results_message(filters, products, query)
    return response


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
        product_id for product_id in product_ids if product_id not in products_by_id
    ]

    if missing_ids:
        return {
            "error": "Product ID not found.",
            "missing_product_ids": missing_ids,
        }

    selected_products = [products_by_id[product_id] for product_id in product_ids]
    product_records = [product.model_dump(mode="json") for product in selected_products]

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

    attributes_by_product = []
    for product in selected_products:
        attributes_by_product.append(
            {str(name).casefold(): value for name, value in product.attributes.items()}
        )

    for normalized_name, display_name in sorted(attribute_names.items()):
        values = [
            attributes.get(normalized_name) for attributes in attributes_by_product
        ]
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
    """Look up a product by its catalog ID."""
    product = next(
        (item for item in products if item.id == product_id),
        None,
    )

    if product is None:
        return {"error": f"Product ID {product_id!r} was not found."}

    return {"product": product.model_dump(mode="json")}
