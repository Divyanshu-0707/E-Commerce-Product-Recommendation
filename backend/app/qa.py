from pydantic import BaseModel, field_validator

from app.catalog import Product


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


def _description_matches(product: Product, keywords: tuple[str, ...]) -> str | None:
    parts = [
        part.strip()
        for part in product.description.split(";")
        if part.strip()
    ]
    matches = [
        part
        for part in parts
        if any(keyword in part.casefold() for keyword in keywords)
    ]
    return "; ".join(matches) if matches else None


def answer_question(product: Product, question: str) -> str:
    q = question.casefold()

    if "ram" in q or "memory" in q:
        if product.ram_gb is not None:
            return f"It has {product.ram_gb} GB of RAM."
        return "The catalog does not provide the RAM for this product."

    if "storage" in q or "ssd" in q or "hard drive" in q:
        if "ssd" in q:
            detail = _description_matches(product, ("ssd", "storage type"))
            if detail:
                return detail
            return "The catalog does not specify whether this product has an SSD."

        if product.storage_gb is not None:
            return f"It has {product.storage_gb} GB of storage."
        return "The catalog does not provide the storage capacity for this product."

    if "price" in q or "cost" in q or "how much" in q:
        return f"The listed price is ₹{product.price:,.2f}."

    if "brand" in q or "manufacturer" in q:
        if product.brand:
            return f"The brand is {product.brand}."
        return "The catalog does not provide the brand for this product."

    if "processor" in q or "cpu" in q:
        if product.processor:
            return f"The processor is {product.processor}."
        return "The catalog does not provide the processor for this product."

    if "weight" in q or "heavy" in q or "lightweight" in q or "portable" in q:
        if product.weight_kg is not None:
            return f"It weighs {product.weight_kg:g} kg."
        return "The catalog does not provide the weight for this product."

    if "screen" in q or "display" in q or "resolution" in q:
        detail = _description_matches(product, ("screen", "display", "resolution"))
        if detail:
            return detail
        return "The catalog does not provide display details for this product."

    if "gpu" in q or "graphics" in q:
        detail = _description_matches(product, ("gpu", "graphics"))
        if detail:
            return detail
        return "The catalog does not provide graphics details for this product."

    if "operating system" in q or " os " in f" {q} ":
        detail = _description_matches(product, ("operating system", "os:"))
        if detail:
            return detail
        return "The catalog does not provide the operating system for this product."

    if "category" in q or "type" in q:
        return f"The catalog lists it as a {product.category}."

    if "title" in q or "name" in q or "model" in q:
        return f"The product is {product.title}."

    if "battery" in q:
        return "The catalog does not provide battery information for this product."

    return "The catalog does not provide that information for this product."