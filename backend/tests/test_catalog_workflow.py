"""Regression checks for the category-agnostic catalog workflow."""

import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np
from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent_tools import (  # noqa: E402
    compare_products_tool,
    get_product_details_tool,
    search_products_tool,
)
from app.catalog import CATALOG_PATH, Product, load_products  # noqa: E402
from app.reasons import build_reasons  # noqa: E402
from app.recommendation import (  # noqa: E402
    AttributeConstraint,
    RecommendRequest,
    rank_products,
    resolve_filters,
)
from app.search_text import build_product_text  # noqa: E402


class CatalogWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.products = load_products(CATALOG_PATH)

    def test_synthetic_catalog_has_twelve_balanced_categories(self) -> None:
        counts = Counter(product.category for product in self.products)
        self.assertEqual(len(self.products), 600)
        self.assertEqual(len(counts), 12)
        self.assertEqual(set(counts.values()), {50})

    def test_all_products_have_shared_fields_and_unique_ids(self) -> None:
        self.assertEqual(len({product.id for product in self.products}), 600)
        for product in self.products:
            with self.subTest(product=product.id):
                self.assertTrue(product.id.startswith("synthetic-"))
                self.assertTrue(product.title)
                self.assertTrue(product.category)
                self.assertGreaterEqual(product.price, 0)
                self.assertEqual(product.currency, "INR")
                self.assertIn("Synthetic demo listing", product.description)
                self.assertIsInstance(product.attributes, dict)

    def test_category_attributes_are_not_laptop_specific(self) -> None:
        by_category = {
            category: next(p for p in self.products if p.category == category)
            for category in {product.category for product in self.products}
        }
        self.assertIn("battery_mah", by_category["smartphone"].attributes)
        self.assertIn("material", by_category["clothing"].attributes)
        self.assertIn("dimensions_cm", by_category["home_kitchen"].attributes)
        self.assertIn("genre", by_category["books"].attributes)
        self.assertIn("age_range", by_category["toys_games"].attributes)

    def test_preserved_legacy_laptop_csv_still_loads(self) -> None:
        legacy_products = load_products(ROOT / "data" / "source" / "products.csv")
        self.assertEqual(len(legacy_products), 3463)
        self.assertEqual({product.category for product in legacy_products}, {"laptop"})
        self.assertTrue(any(product.processor for product in legacy_products))

    def test_search_text_includes_dynamic_nested_attributes(self) -> None:
        product = next(p for p in self.products if p.category == "home_kitchen")
        first = build_product_text(product)
        second = build_product_text(product)
        self.assertEqual(first, second)
        self.assertIn("Category: home_kitchen", first)
        self.assertIn("dimensions cm:", first.casefold())
        self.assertIn("width:", first)

    def test_category_budget_and_generic_attribute_filters_are_hard(self) -> None:
        request = RecommendRequest.model_validate(
            {
                "query": "smartphone with at least 8 GB RAM",
                "category": "SMARTPHONE",
                "max_price": 30000,
                "attribute_filters": {"RAM_GB": {"gte": 8}},
            }
        )
        filters = resolve_filters(request, self.products)
        ranked = rank_products(
            products=self.products,
            product_embeddings=np.zeros((len(self.products), 384), dtype=np.float32),
            query_embedding=np.zeros(384, dtype=np.float32),
            query=request.query,
            filters=filters,
        )
        self.assertTrue(ranked)
        for product, _ in ranked:
            self.assertEqual(product.category, "smartphone")
            self.assertLessEqual(product.price, 30000)
            self.assertGreaterEqual(product.attributes["ram_gb"], 8)

    def test_missing_attributes_do_not_satisfy_hard_filter(self) -> None:
        product = self.products[0].model_copy(update={"attributes": {}})
        filters = resolve_filters(
            RecommendRequest(
                query="product",
                attribute_filters={"ram_gb": AttributeConstraint(gte=8)},
            ),
            [product],
        )
        ranked = rank_products(
            products=[product],
            product_embeddings=np.zeros((1, 384), dtype=np.float32),
            query_embedding=np.zeros(384, dtype=np.float32),
            query="product",
            filters=filters,
        )
        self.assertEqual(ranked, [])

    def test_budget_with_no_eligible_products_returns_empty(self) -> None:
        request = RecommendRequest(query="books", category="books", max_price=1)
        filters = resolve_filters(request, self.products)
        ranked = rank_products(
            products=self.products,
            product_embeddings=np.zeros((len(self.products), 384), dtype=np.float32),
            query_embedding=np.zeros(384, dtype=np.float32),
            query=request.query,
            filters=filters,
        )
        self.assertEqual(ranked, [])

    def test_reasons_reference_stored_values(self) -> None:
        product = next(p for p in self.products if p.category == "smartphone")
        ram = product.attributes["ram_gb"]
        reasons = build_reasons(
            product=product,
            query="smartphone with RAM",
            category="smartphone",
            max_price=product.price,
        )
        self.assertTrue(any(str(ram) in reason and "Ram" in reason for reason in reasons))

    def test_empty_attribute_constraint_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AttributeConstraint.model_validate({})

    def test_agent_search_tool_enforces_generic_category_filters(self) -> None:
        class StubEmbeddingModel:
            @staticmethod
            def embed_query(_query: str) -> np.ndarray:
                return np.zeros(384, dtype=np.float32)

        result = search_products_tool(
            query="books for reading under 1000",
            category="books",
            max_price=1000,
            attribute_filters={"language": {"eq": "English"}},
            products=self.products,
            embedding_model=StubEmbeddingModel(),
            product_embeddings=np.zeros(
                (len(self.products), 384), dtype=np.float32
            ),
        )
        self.assertGreater(result["count"], 0)
        for item in result["results"]:
            product = item["product"]
            self.assertEqual(product["category"], "books")
            self.assertLessEqual(product["price"], 1000)
            self.assertEqual(product["attributes"]["language"], "English")

    def test_agent_compare_and_details_tools_are_category_agnostic(self) -> None:
        book = next(p for p in self.products if p.category == "books")
        shoe = next(p for p in self.products if p.category == "shoes")
        comparison = compare_products_tool(
            [book.id, shoe.id],
            self.products,
        )
        self.assertEqual(len(comparison["products"]), 2)
        rows = {row["field"]: row["values"] for row in comparison["comparison_rows"]}
        self.assertEqual(rows["category"], ["books", "shoes"])
        self.assertIn("attributes.genre", rows)
        self.assertIn("attributes.upper_material", rows)
        self.assertIsNone(rows["attributes.genre"][1])

        details = get_product_details_tool(book.id, self.products)
        self.assertEqual(details["product"]["id"], book.id)


if __name__ == "__main__":
    unittest.main()
