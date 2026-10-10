from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.catalog import load_products
from app.embeddings import ProductEmbeddingModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the catalog and create product embeddings once at startup.
    app.state.products = load_products()
    app.state.embedding_model = ProductEmbeddingModel()
    app.state.product_embeddings = app.state.embedding_model.embed_products(
        app.state.products
    )

    print(f"Loaded {len(app.state.products)} products and their embeddings.")
    yield


app = FastAPI(
    title="AI E-Commerce Product Recommendation Assistant",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}