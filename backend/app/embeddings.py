import hashlib
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from app.catalog import Product
from app.search_text import build_product_text


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"


class ProductEmbeddingModel:
    def __init__(self) -> None:
        self.model = SentenceTransformer(MODEL_NAME)

    def _cache_path(self, texts: list[str]) -> Path:
        cache_input = json.dumps(
            {"model": MODEL_NAME, "texts": texts},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        fingerprint = hashlib.sha256(cache_input).hexdigest()
        return CACHE_DIR / f"product-embeddings-{fingerprint}.npy"

    def embed_products(self, products: list[Product]) -> np.ndarray:
        """Load cached product embeddings or create and cache them."""
        texts = [build_product_text(product) for product in products]

        if not texts:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)

        cache_path = self._cache_path(texts)

        if cache_path.exists():
            try:
                cached = np.load(cache_path, allow_pickle=False)
                if cached.shape == (len(texts), EMBEDDING_DIMENSION):
                    print("Loaded cached product embeddings.")
                    return cached.astype(np.float32, copy=False)
            except (OSError, ValueError):
                # Rebuild the cache if the file is damaged or unreadable.
                pass

        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        embeddings = np.asarray(embeddings, dtype=np.float32)

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_suffix(".tmp")
        with temporary_path.open("wb") as file:
            np.save(file, embeddings, allow_pickle=False)
        temporary_path.replace(cache_path)

        print("Created and cached product embeddings.")
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """Create a normalized embedding for a customer's query."""
        return self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]