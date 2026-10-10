import re

from pydantic import BaseModel, Field, field_validator

from app.catalog import Product


class RecommendRequest(BaseModel):
    query: str
    category: str | None = None
    max_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip().casefold()


PRICE_PATTERN = re.compile(
    r"\b(?:under|below|less than|up to|upto|max(?:imum)?(?: price)?|"
    r"budget(?: of)?|within)\s*(?:₹|rs\.?|inr)?\s*"
    r"([\d,]+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\b",
    re.IGNORECASE,
)


def extract_max_price(query: str) -> float | None:
    match = PRICE_PATTERN.search(query)
    if not match:
        return None

    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").casefold()

    if unit == "k":
        amount *= 1_000
    elif unit == "thousand":
        amount *= 1_000
    elif unit in {"lakh", "lac"}:
        amount *= 100_000

    return amount


def resolve_filters(
    request: RecommendRequest,
) -> tuple[str | None, float | None]:
    query_lower = request.query.casefold()

    # An explicitly supplied category takes priority over query extraction.
    category = request.category
    if category is None and re.search(r"\blaptops?\b", query_lower):
        category = "laptop"

    # An explicitly supplied maximum price takes priority over query extraction.
    max_price = request.max_price
    if max_price is None:
        max_price = extract_max_price(request.query)

    return category, max_price


def filter_products(
    products: list[Product],
    category: str | None,
    max_price: float | None,
) -> list[Product]:
    eligible = products

    if category is not None:
        eligible = [
            product
            for product in eligible
            if product.category.casefold() == category
        ]

    if max_price is not None:
        eligible = [
            product for product in eligible if product.price <= max_price
        ]

    return eligible