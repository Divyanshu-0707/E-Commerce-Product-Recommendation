from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import APIError

from app.agent import AgentRequest, AgentResponse, run_agent
from app.catalog import Product, load_products
from app.embeddings import ProductEmbeddingModel
from app.feedback import FeedbackRequest, record_feedback
from app.qa import AskRequest, AskResponse, answer_question
from app.recommendation import (
    RecommendRequest,
    no_results_message,
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
    message: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.products = load_products()
    app.state.embedding_model = None
    app.state.product_embeddings = None

    try:
        embedding_model = ProductEmbeddingModel()
        product_embeddings = embedding_model.embed_products(app.state.products)
    except Exception as exc:
        print(
            "Embedding model unavailable "
            f"({type(exc).__name__}); using keyword-only search."
        )
    else:
        app.state.embedding_model = embedding_model
        app.state.product_embeddings = product_embeddings
        print(f"Loaded {len(app.state.products)} products and their embeddings.")

    yield


app = FastAPI(
    title="AI E-Commerce Product Recommendation Assistant",
    lifespan=lifespan,
)

CATALOG_METADATA_PATH = Path(__file__).resolve().parents[2] / "data" / "catalog_metadata.json"

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


@app.get("/categories")
def categories(request: Request):
    values = {product.category for product in request.app.state.products}
    return {"categories": sorted(values, key=str.casefold)}


@app.get("/catalog-info")
def catalog_info():
    if not CATALOG_METADATA_PATH.exists():
        return {"synthetic": False}
    return json.loads(CATALOG_METADATA_PATH.read_text(encoding="utf-8"))


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest, request: Request):
    filters = resolve_filters(body, request.app.state.products)
    embedding_model = request.app.state.embedding_model
    query_embedding = None
    if embedding_model is not None:
        try:
            query_embedding = embedding_model.embed_query(body.query)
        except Exception as exc:
            print(
                "Query embedding unavailable "
                f"({type(exc).__name__}); using keyword-only search."
            )

    ranked = rank_products(
        products=request.app.state.products,
        product_embeddings=request.app.state.product_embeddings,
        query_embedding=query_embedding,
        query=body.query,
        filters=filters,
        limit=10,
    )

    return {
        "message": (
            no_results_message(filters, request.app.state.products)
            if not ranked
            else None
        ),
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
                    attribute_filters=filters.attribute_filters,
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

    try:
        answer = answer_question(product, body.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service could not complete the request. Please try again.",
        ) from exc
    return {"answer": answer}


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


@app.post("/assistant", response_model=AgentResponse)
def assistant(body: AgentRequest, request: Request):
    try:
        answer = run_agent(
            message=body.message,
            products=request.app.state.products,
            embedding_model=request.app.state.embedding_model,
            product_embeddings=request.app.state.product_embeddings,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service could not complete the request. Please try again.",
        ) from exc
    return AgentResponse(answer=answer)
