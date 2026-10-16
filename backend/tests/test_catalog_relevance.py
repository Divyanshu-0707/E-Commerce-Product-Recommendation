import unittest
from types import SimpleNamespace

import numpy as np

from app.agent_tools import search_products_tool
from app.catalog import load_products
from app.main import recommend
from app.recommendation import RecommendRequest, rank_products, resolve_filters


class CatalogRelevanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = load_products()

    def search(self, query, category=None, semantic=False, **constraints):
        request = RecommendRequest(query=query, category=category, **constraints)
        filters = resolve_filters(request, self.products)
        # Even an erroneously high semantic score must not invent a match.
        vectors = np.ones((len(self.products), 1)) if semantic else None
        query_vector = np.ones(1) if semantic else None
        return rank_products(
            self.products,
            vectors,
            query_vector,
            query,
            filters,
        )

    def test_absent_products_and_unrelated_requests_return_no_results(self):
        queries = [
            "perfume",
            "Perfumes",
            "please recommend perfumes under 2000",
            "fresh milk",
            "bananas",
            "pet food",
            "buy a car",
            "refrigerator",
            "phone case",
            "laptop stand",
            "face cream",
            "wooden dining table",
            "gaming chair",
            "books for cooking",
            "hello",
            "tell me a joke",
            "zzzxxyy",
            "!!!",
            "产品不存在",
            "show me products",
            "Notebook Air 999",
        ]
        for semantic in (False, True):
            for query in queries:
                with self.subTest(query=query, semantic=semantic):
                    self.assertEqual(self.search(query, semantic=semantic), [])

    def test_reported_beauty_searches_only_return_the_requested_items(self):
        for semantic in (False, True):
            for query, title in [
                ("Hair Oil", "Hair Oil"),
                ("hair oils", "Hair Oil"),
                ("Lotion", "Lotion"),
                ("lotions", "Lotion"),
                ("hand cream", "Hand Cream"),
                ("cream", "Hand Cream"),
            ]:
                with self.subTest(query=query, semantic=semantic):
                    ranked = self.search(query, semantic=semantic)
                    self.assertEqual(len(ranked), 5)
                    for product, _ in ranked:
                        self.assertEqual(product.category, "beauty")
                        self.assertIn(title, product.title)

    def test_every_catalog_category_and_non_tech_product_searches_still_work(self):
        cases = [
            ("laptop", "laptop"),
            ("phones", "smartphone"),
            ("headphones for music", "headphones"),
            ("tablet", "tablet"),
            ("shirts", "clothing"),
            ("running shoes", "shoes"),
            ("desk lamp", "home_kitchen"),
            ("writing desk", "furniture"),
            ("fiction books", "books"),
            ("yoga mat", "sports_fitness"),
            ("shampoo", "beauty"),
            ("wooden blocks", "toys_games"),
            ("lightweight laptop for programming", "laptop"),
            ("programming laptop under 60000", "laptop"),
            ("coding laptop", "laptop"),
            ("music headphones", "headphones"),
        ]
        for semantic in (False, True):
            for query, category in cases:
                with self.subTest(query=query, semantic=semantic):
                    ranked = self.search(query, semantic=semantic)
                    self.assertTrue(ranked)
                    self.assertEqual({p.category for p, _ in ranked}, {category})

    def test_category_control_cannot_substitute_for_an_absent_item(self):
        for category in ("beauty", "laptop"):
            with self.subTest(category=category):
                self.assertEqual(self.search("perfumes", category=category), [])
        self.assertEqual(self.search("lotion", category="laptop"), [])

    def test_valid_matches_keep_budget_and_attribute_constraints(self):
        self.assertEqual(self.search("hair oil", max_price=1), [])
        ranked = self.search("lotion", max_price=2800)
        self.assertTrue(ranked)
        self.assertTrue(all(p.price <= 2800 for p, _ in ranked))
        ranked = self.search("smartphone with at least 8 GB RAM", max_price=30000)
        self.assertTrue(ranked)
        self.assertTrue(all(p.price <= 30000 and p.ram_gb >= 8 for p, _ in ranked))
        ranked = self.search("fragrance free lotion")
        self.assertTrue(ranked)
        self.assertTrue(all(p.attributes["fragrance_free"] is True for p, _ in ranked))

    def test_recommend_endpoint_reports_relevance_failure_without_filter_lie(self):
        state = SimpleNamespace(
            products=self.products,
            embedding_model=None,
            product_embeddings=None,
        )
        request = SimpleNamespace(app=SimpleNamespace(state=state))
        response = recommend(RecommendRequest(query="perfumes"), request)
        self.assertEqual(response["results"], [])
        self.assertIn("requested product details", response["message"])
        self.assertNotIn("match all of these filters", response["message"])

    def test_assistant_search_uses_the_same_relevance_gate(self):
        for query in ("perfumes", "fresh milk", "phone case"):
            with self.subTest(query=query):
                response = search_products_tool(query, self.products, None, None)
                self.assertEqual(response["results"], [])
                self.assertEqual(response["count"], 0)
                self.assertIn("requested product details", response["message"])
        response = search_products_tool("hair oil", self.products, None, None)
        self.assertEqual(response["count"], 5)
        self.assertTrue(
            all("Hair Oil" in r["product"]["title"] for r in response["results"])
        )


if __name__ == "__main__":
    unittest.main()
