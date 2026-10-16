import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from app.catalog import Product, load_products
from app.qa import UNKNOWN_ANSWER, answer_question
from app.recommendation import (
    RecommendRequest,
    no_results_message,
    rank_products,
    resolve_filters,
)


def make_product(
    product_id: str,
    title: str,
    price: float,
    category: str = "laptop",
    attributes: dict | None = None,
) -> Product:
    return Product(
        id=product_id,
        title=title,
        category=category,
        price=price,
        currency="INR",
        description=f"Demo product: {title}",
        attributes=attributes or {},
    )


class KeywordFallbackTests(unittest.TestCase):
    def test_null_budget_removes_price_cap_but_keeps_category(self):
        products = [
            make_product("laptop-1", "Programming Laptop", 50000),
            make_product("laptop-2", "Programming Laptop Plus", 70000),
            make_product("phone-1", "Programming Phone", 20000, "smartphone"),
        ]
        request = RecommendRequest.model_validate(
            {
                "query": "programming laptop under 60000",
                "category": "laptop",
                "max_price": None,
            }
        )
        filters = resolve_filters(request, products)
        ranked = rank_products(
            products=products,
            product_embeddings=None,
            query_embedding=None,
            query=request.query,
            filters=filters,
        )
        self.assertIsNone(filters.max_price)
        self.assertEqual(
            {product.id for product, _ in ranked}, {"laptop-1", "laptop-2"}
        )

    def test_numeric_budget_including_zero_remains_a_hard_limit(self):
        products = [
            make_product("book-free", "Programming Book", 0, "books"),
            make_product("book-paid", "Programming Book Plus", 500, "books"),
        ]
        for budget, expected in [(0, {"book-free"}), (500, {"book-free", "book-paid"})]:
            with self.subTest(budget=budget):
                request = RecommendRequest(query="books", max_price=budget)
                filters = resolve_filters(request, products)
                ranked = rank_products(
                    products=products,
                    product_embeddings=None,
                    query_embedding=None,
                    query=request.query,
                    filters=filters,
                )
                self.assertEqual({product.id for product, _ in ranked}, expected)

    def test_keyword_search_keeps_budget_and_category_filters(self):
        products = [
            make_product("laptop-1", "Programming Laptop", 50000),
            make_product("laptop-2", "Programming Laptop Plus", 70000),
            make_product("phone-1", "Programming Phone", 20000, "smartphone"),
        ]
        request = RecommendRequest(
            query="programming laptop under 60000",
            category="laptop",
        )
        filters = resolve_filters(request, products)

        ranked = rank_products(
            products=products,
            product_embeddings=None,
            query_embedding=None,
            query=request.query,
            filters=filters,
        )

        self.assertEqual([product.id for product, _ in ranked], ["laptop-1"])

    def test_no_results_explains_filter_counts(self):
        products = [
            make_product("book-1", "Demo Book", 250, "books"),
            make_product("book-2", "Demo Book Two", 500, "books"),
        ]
        request = RecommendRequest(
            query="books",
            category="books",
            max_price=1,
        )
        filters = resolve_filters(request, products)

        message = no_results_message(filters, products)

        self.assertIn("2 total", message)
        self.assertIn("category 'books': 2", message)
        self.assertIn("maximum price INR 1: 0", message)
        self.assertIn("Change one or more filters", message)

    def test_empty_catalog_has_clear_no_results_message(self):
        request = RecommendRequest(query="books", category="books")
        filters = resolve_filters(request, [])

        self.assertEqual(
            no_results_message(filters, []),
            "No catalog products are available for this search.",
        )

    def test_blank_query_is_rejected(self):
        with self.assertRaises(ValidationError):
            RecommendRequest(query="  ")


class CatalogGroundedAnswerTests(unittest.TestCase):
    def setUp(self):
        self.product = make_product(
            "laptop-1",
            "Programming Laptop",
            50000,
            attributes={"ram_gb": 16},
        )

    def test_direct_question_uses_stored_value_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            answer = answer_question(
                self.product, "How much RAM does this product have?"
            )
        self.assertIn("16", answer)

    def test_missing_product_fact_is_reported_as_unknown(self):
        with patch.dict("os.environ", {}, clear=True):
            answer = answer_question(self.product, "What is the warranty period?")
        self.assertEqual(answer, UNKNOWN_ANSWER)

    def test_unrecognized_question_does_not_invent_an_answer_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            answer = answer_question(self.product, "Is it suitable for a long commute?")
        self.assertEqual(answer, UNKNOWN_ANSWER)

    def test_model_selected_field_is_checked_against_product_record(self):
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=True),
            patch("app.qa.OpenAI") as openai,
        ):
            openai.return_value.responses.create.return_value.output_text = (
                '{"fields":["ram_gb"]}'
            )
            answer = answer_question(
                self.product, "Can you share a performance capacity detail?"
            )

        self.assertEqual(answer, "RAM (GB): 16.")

    def test_model_cannot_return_a_field_outside_the_product_record(self):
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=True),
            patch("app.qa.OpenAI") as openai,
        ):
            openai.return_value.responses.create.return_value.output_text = (
                '{"fields":["warranty"]}'
            )
            answer = answer_question(
                self.product, "What commitment period applies to this product?"
            )

        self.assertEqual(answer, UNKNOWN_ANSWER)


class CatalogValidationTests(unittest.TestCase):
    COLUMNS = [
        "id",
        "title",
        "category",
        "brand",
        "price",
        "currency",
        "description",
        "attributes",
    ]

    def write_catalog(self, rows: list[dict[str, str]]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        catalog_path = Path(temp_dir.name) / "products.csv"
        with catalog_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return catalog_path

    def test_empty_catalog_loads_as_empty_list(self):
        catalog_path = self.write_catalog([])
        self.assertEqual(load_products(catalog_path), [])

    def test_missing_required_name_is_rejected(self):
        catalog_path = self.write_catalog(
            [
                {
                    "id": "item-1",
                    "title": "",
                    "category": "books",
                    "brand": "",
                    "price": "10",
                    "currency": "INR",
                    "description": "demo",
                    "attributes": "{}",
                }
            ]
        )
        with self.assertRaisesRegex(ValueError, "title.*blank"):
            load_products(catalog_path)

    def test_malformed_attributes_are_rejected(self):
        catalog_path = self.write_catalog(
            [
                {
                    "id": "item-1",
                    "title": "Demo Book",
                    "category": "books",
                    "brand": "",
                    "price": "10",
                    "currency": "INR",
                    "description": "demo",
                    "attributes": "not-json",
                }
            ]
        )
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            load_products(catalog_path)


if __name__ == "__main__":
    unittest.main()
