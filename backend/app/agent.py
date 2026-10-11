import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, field_validator

from app.agent_tools import (
    compare_products_tool,
    get_product_details_tool,
    search_products_tool,
)
from app.catalog import Product
from app.embeddings import ProductEmbeddingModel


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)

MAX_TOOL_ROUNDS = 3


class AgentRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank.")
        return value


class AgentResponse(BaseModel):
    answer: str


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the laptop catalog for products matching the user's "
                "requirements. Use this when the user asks to find or recommend "
                "products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The user's laptop requirements in natural language."
                        ),
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": (
                "Compare exactly two products that were found in the catalog. "
                "Use their product IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "The two catalog product IDs to compare.",
                    }
                },
                "required": ["product_ids"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": (
                "Look up the catalog data for one product. Use this to answer "
                "questions about a specific product."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product's catalog ID.",
                    }
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
]


def _run_tool(
    tool_name: str,
    arguments: dict,
    products: list[Product],
    embedding_model: ProductEmbeddingModel,
    product_embeddings,
) -> dict:
    """Run only the catalog tools explicitly allowed by this application."""
    if tool_name == "search_products":
        query = arguments.get("query")
        if not isinstance(query, str):
            return {"error": "The search query must be text."}

        return search_products_tool(
            query=query,
            products=products,
            embedding_model=embedding_model,
            product_embeddings=product_embeddings,
        )

    if tool_name == "compare_products":
        product_ids = arguments.get("product_ids")
        if not isinstance(product_ids, list) or not all(
            isinstance(product_id, str) for product_id in product_ids
        ):
            return {"error": "Product IDs must be a list of text values."}

        return compare_products_tool(
            product_ids=product_ids,
            products=products,
        )

    if tool_name == "get_product_details":
        product_id = arguments.get("product_id")
        if not isinstance(product_id, str):
            return {"error": "Product ID must be text."}

        return get_product_details_tool(
            product_id=product_id,
            products=products,
        )

    return {"error": f"Tool {tool_name!r} is not available."}


def run_agent(
    message: str,
    products: list[Product],
    embedding_model: ProductEmbeddingModel,
    product_embeddings,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to backend/.env."
        )

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI shopping assistant for a laptop catalog. "
                "Use the available catalog tools to search, compare, or look up "
                "products. Base product claims only on tool results. If the "
                "catalog does not contain an answer, say so. Do not invent "
                "products, specifications, or prices. Keep the final answer "
                "clear and concise."
            ),
        },
        {"role": "user", "content": message},
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            answer = assistant_message.content
            return answer.strip() if answer else (
                "I couldn't create an answer from the catalog results."
            )

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )

        for tool_call in tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")

                result = _run_tool(
                    tool_name=tool_call.function.name,
                    arguments=arguments,
                    products=products,
                    embedding_model=embedding_model,
                    product_embeddings=product_embeddings,
                )
            except (json.JSONDecodeError, ValueError):
                result = {"error": "The model supplied invalid tool arguments."}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return (
        "I couldn't finish that request in the allowed number of steps. "
        "Try asking for a product search, a two-product comparison, or "
        "details about one catalog product."
    )