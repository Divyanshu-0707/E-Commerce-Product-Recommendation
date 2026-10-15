import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, field_validator

from app.catalog import Product


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)


class AskRequest(BaseModel):
    product_id: str
    question: str

    @field_validator("product_id", "question")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be blank")
        return value


class AskResponse(BaseModel):
    answer: str


def answer_question(product: Product, question: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to backend/.env and restart the backend."
        )

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    catalog_record = {
        "id": product.id,
        "title": product.title,
        "category": product.category,
        "brand": product.brand,
        "price": product.price,
        "currency": product.currency,
        "description": product.description,
        "attributes": product.attributes,
    }

    response = client.responses.create(
        model=model,
        instructions=(
            "You are a helpful shopping assistant. Answer the customer's question "
            "using only the product catalog data provided. Do not guess or add "
            "outside facts. If the data does not contain the answer, say that the "
            "catalog does not provide that information. Product-specific "
            "specifications may appear under the attributes object; interpret "
            "those stored key-value pairs as the source of truth. Do not infer "
            "a missing attribute from the product category or typical products. "
            "Keep the answer concise."
        ),
        input=(
            "Product catalog data:\n"
            f"{json.dumps(catalog_record, ensure_ascii=False, indent=2)}\n\n"
            f"Customer question:\n{question}"
        ),
    )

    answer = response.output_text.strip()
    if not answer:
        return "The catalog does not provide that information for this product."

    return answer
