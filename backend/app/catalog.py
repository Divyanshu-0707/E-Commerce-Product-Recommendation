import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, computed_field

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "products.csv"

# Support both the current catalog and the original laptop CSV.
CATALOG_COLUMNS = [
    "id",
    "title",
    "category",
    "brand",
    "price",
    "currency",
    "description",
    "attributes",
]
LEGACY_LAPTOP_COLUMNS = [
    "id",
    "title",
    "category",
    "product_type",
    "condition",
    "brand",
    "price",
    "description",
    "weight_kg",
    "processor",
    "ram_gb",
    "storage_gb",
]


class Product(BaseModel):
    """A catalog record with category-specific attributes."""

    id: str
    title: str
    category: str
    brand: str | None = None
    price: float = Field(ge=0, allow_inf_nan=False)
    currency: str = "INR"
    description: str
    attributes: dict[str, Any] = Field(default_factory=dict)

    # Existing clients still use these top-level laptop fields.
    @computed_field
    @property
    def product_type(self) -> str | None:
        return self._legacy_text("product_type")

    @computed_field
    @property
    def condition(self) -> str | None:
        return self._legacy_text("condition")

    @computed_field
    @property
    def weight_kg(self) -> float | None:
        return self._legacy_number("weight_kg")

    @computed_field
    @property
    def processor(self) -> str | None:
        return self._legacy_text("processor")

    @computed_field
    @property
    def ram_gb(self) -> int | None:
        return self._legacy_integer("ram_gb")

    @computed_field
    @property
    def storage_gb(self) -> int | None:
        return self._legacy_integer("storage_gb")

    def _legacy_text(self, key: str) -> str | None:
        value = self.attributes.get(key)
        return str(value) if value is not None else None

    def _legacy_number(self, key: str) -> float | None:
        value = self.attributes.get(key)
        return float(value) if isinstance(value, (int, float)) else None

    def _legacy_integer(self, key: str) -> int | None:
        value = self.attributes.get(key)
        return int(value) if isinstance(value, (int, float)) else None


def _optional_text(value: str) -> str | None:
    value = value.strip()
    return value or None


def _optional_number(value: str, column: str, row_number: int) -> float | None:
    value = value.strip()
    if not value:
        return None

    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {column} must be a number; got {value!r}"
        ) from exc
    if number < 0:
        raise ValueError(f"Row {row_number}: {column} must not be negative")
    return number


def _optional_integer(value: str, column: str, row_number: int) -> int | None:
    number = _optional_number(value, column, row_number)
    if number is None:
        return None
    if not number.is_integer():
        raise ValueError(
            f"Row {row_number}: {column} must be a whole number; got {value!r}"
        )
    return int(number)


def _parse_attributes(value: str, row_number: int) -> dict[str, Any]:
    if not value.strip():
        return {}

    try:
        attributes = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Row {row_number}: attributes must contain valid JSON"
        ) from exc

    if not isinstance(attributes, dict):
        raise ValueError(f"Row {row_number}: attributes must be a JSON object")

    normalized = {str(key).strip(): item for key, item in attributes.items()}
    if any(not key for key in normalized):
        raise ValueError(f"Row {row_number}: attribute names must not be blank")
    return normalized


def _read_product_row(
    row: dict[str, str | None],
    columns: list[str],
    row_number: int,
) -> Product:
    item = {key: (row.get(key) or "").strip() for key in columns}

    for required in ("id", "title", "category", "price", "description"):
        if not item[required]:
            raise ValueError(f"Row {row_number}: required field {required!r} is blank")

    brand = _optional_text(item["brand"])
    if columns == LEGACY_LAPTOP_COLUMNS:
        attributes: dict[str, Any] = {
            "product_type": _optional_text(item["product_type"]),
            "condition": _optional_text(item["condition"]),
            "weight_kg": _optional_number(item["weight_kg"], "weight_kg", row_number),
            "processor": _optional_text(item["processor"]),
            "ram_gb": _optional_integer(item["ram_gb"], "ram_gb", row_number),
            "storage_gb": _optional_integer(
                item["storage_gb"], "storage_gb", row_number
            ),
        }
        attributes = {
            key: value for key, value in attributes.items() if value is not None
        }
        currency = "INR"
    else:
        attributes = _parse_attributes(item["attributes"], row_number)
        currency = item["currency"].upper()
        if not currency:
            raise ValueError(f"Row {row_number}: required field 'currency' is blank")

    try:
        return Product.model_validate(
            {
                "id": item["id"],
                "title": item["title"],
                "category": item["category"].casefold(),
                "brand": brand,
                "price": float(item["price"]),
                "currency": currency,
                "description": item["description"],
                "attributes": attributes,
            }
        )
    except ValueError as exc:
        raise ValueError(f"Invalid product on row {row_number}: {exc}") from exc


def load_products(path: Path = CATALOG_PATH) -> list[Product]:
    """Read and validate either catalog format."""
    if not path.exists():
        raise FileNotFoundError(f"Product catalog not found: {path}")

    products: list[Product] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = reader.fieldnames

        if columns not in (CATALOG_COLUMNS, LEGACY_LAPTOP_COLUMNS):
            raise ValueError(
                "CSV headers must match the shared product format or the "
                "legacy laptop format. "
                f"Expected one of: {CATALOG_COLUMNS}; {LEGACY_LAPTOP_COLUMNS}. "
                f"Found: {columns}"
            )

        for row in reader:
            row_number = reader.line_num
            if None in row:
                raise ValueError(f"Row {row_number}: unexpected extra CSV values")
            if not any((value or "").strip() for value in row.values()):
                continue

            product = _read_product_row(row, columns, row_number)
            if product.id in seen_ids:
                raise ValueError(
                    f"Row {row_number}: duplicate product id {product.id!r}"
                )

            seen_ids.add(product.id)
            products.append(product)

    return products
