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

    response = client.responses.create(
        model=model,
        instructions=(
            "You are a helpful shopping assistant. Answer the customer's question "
            "using only the product catalog data provided. Do not guess or add "
            "outside facts. If the data does not contain the answer, say that the "
            "catalog does not provide that information. Keep the answer concise."
        ),
        input=(
            f"Product catalog data:\n{product.model_dump_json()}\n\n"
            f"Customer question:\n{question}"
        ),
    )

    answer = response.output_text.strip()
    if not answer:
        return "The catalog does not provide that information for this product."

    return answer