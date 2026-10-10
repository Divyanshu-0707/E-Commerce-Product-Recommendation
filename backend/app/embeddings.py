import numpy as np
from sentence_transformers import SentenceTransformer

from app.catalog import Product
from app.search_text import build_product_text


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class ProductEmbeddingModel:
    def __init__(self) -> None:
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_products(self, products: list[Product]) -> np.ndarray:
        """Create one normalized embedding for each product, in list order."""
        texts = [build_product_text(product) for product in products]

        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        return self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

    def embed_query(self, query: str) -> np.ndarray:
        """Create a normalized embedding for a customer's query."""
        return self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
