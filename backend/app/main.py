from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.catalog import Product, load_products
from app.embeddings import ProductEmbeddingModel
from app.feedback import FeedbackRequest, record_feedback
from app.qa import AskRequest, AskResponse, answer_question
from app.recommendation import (
    RecommendRequest,
    rank_products,
    resolve_filters,
)
from app.reasons import build_reasons


class RecommendationItem(BaseModel):
    product: Product
    score: float
    reasons: list[str]


class RecommendResponse(BaseModel):
    results: list[RecommendationItem]


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest, request: Request):
    filters = resolve_filters(body, request.app.state.products)
    query_embedding = request.app.state.embedding_model.embed_query(body.query)

    ranked = rank_products(
        products=request.app.state.products,
        product_embeddings=request.app.state.product_embeddings,
        query_embedding=query_embedding,
        query=body.query,
        filters=filters,
        limit=10,
    )

    return {
        "results": [
            {
                "product": product,
                "score": score,
                "reasons": build_reasons(
                    product=product,
                    query=body.query,
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
            for product, score in ranked
        ]
    }


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest, request: Request):
    product = next(
        (
            item
            for item in request.app.state.products
            if item.id == body.product_id
        ),
        None,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {body.product_id!r} was not found.",
        )

    return {"answer": answer_question(product, body.question)}


@app.post("/feedback")
def submit_feedback(body: FeedbackRequest, request: Request):
    product_exists = any(
        product.id == body.product_id
        for product in request.app.state.products
    )

    if not product_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Product with id {body.product_id!r} was not found.",
        )

    record_feedback(body)
    return {"status": "recorded"}