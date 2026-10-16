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

MAX_TOOL_ROUNDS = 6


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
                "Search the product catalog for products matching the user's "
                "requirements. Use this when the user asks to find or recommend "
                "products. Pass explicit category, budget, and attribute "
                "requirements as filters so they are enforced before ranking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The product requirements in natural language."
                        ),
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Exact product category when requested.",
                    },
                    "max_price": {
                        "type": ["number", "null"],
                        "description": "Inclusive maximum price when requested.",
                    },
                    "attribute_filters": {
                        "type": ["object", "null"],
                        "description": (
                            "Hard product-attribute constraints keyed by catalog "
                            "attribute name. Each constraint may use eq, gte, "
                            "and/or lte. Missing attributes do not satisfy a filter."
                        ),
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "eq": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "number"},
                                        {"type": "boolean"},
                                    ]
                                },
                                "gte": {"type": "number"},
                                "lte": {"type": "number"},
                            },
                            "additionalProperties": False,
                        },
                    },
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
                "Compare exactly two products found in the catalog by product "
                "ID. Use the returned comparison rows for common fields and "
                "category-specific attributes; null means a value is not "
                "available in that product's catalog record."
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
    embedding_model: ProductEmbeddingModel | None,
    product_embeddings,
) -> dict:
    """Run only the catalog tools explicitly allowed by this application."""
    if tool_name == "search_products":
        allowed_arguments = {"query", "category", "max_price", "attribute_filters"}
        if set(arguments) - allowed_arguments:
            return {"error": "The search tool received unsupported filters."}

        query = arguments.get("query")
        if not isinstance(query, str):
            return {"error": "The search query must be text."}
        category = arguments.get("category")
        if category is not None and not isinstance(category, str):
            return {"error": "The category filter must be text."}
        max_price = arguments.get("max_price")
        if max_price is not None and (
            isinstance(max_price, bool) or not isinstance(max_price, (int, float))
        ):
            return {"error": "The maximum price filter must be numeric."}
        attribute_filters = arguments.get("attribute_filters")
        if attribute_filters is None:
            attribute_filters = {}
        if not isinstance(attribute_filters, dict):
            return {"error": "Attribute filters must be an object."}

        return search_products_tool(
            query=query,
            category=category,
            max_price=max_price,
            attribute_filters=attribute_filters,
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
    embedding_model: ProductEmbeddingModel | None,
    product_embeddings,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to backend/.env.")

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI shopping assistant for a product catalog that "
                "may contain many categories. "
                "Use the available catalog tools to search, compare, or look up "
                "products. Apply requested category, budget, and attribute "
                "constraints through search filters. Base product claims only "
                "on tool results. Search and comparison results already contain "
                "the catalog data needed to answer; use those results directly "
                "instead of looking up each returned product again. Call "
                "get_product_details only when the user asks about one specific "
                "product and its record is not already in the conversation. "
                "Treat null or missing attributes as unknown. "
                "If the catalog does not contain an answer, say so. Do not "
                "invent products, specifications, prices, or policies. Keep "
                "the final answer clear and concise."
            ),
        },
        {"role": "user", "content": message},
    ]

    tool_rounds = 0
    while True:
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
            return (
                answer.strip()
                if answer
                else ("I couldn't create an answer from the catalog results.")
            )

        if tool_rounds >= MAX_TOOL_ROUNDS:
            return (
                "I couldn't finish that request in the allowed number of steps. "
                "Try asking for a product search, a two-product comparison, or "
                "details about one catalog product."
            )

        tool_rounds += 1

        messages.append(assistant_message.model_dump(exclude_none=True))

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
            except ValueError:
                result = {"error": "The model supplied invalid tool arguments."}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
