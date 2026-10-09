import csv
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError


EXPECTED_COLUMNS = [
    "id",
    "title",
    "category",
    "brand",
    "price",
    "description",
    "weight_kg",
    "processor",
    "ram_gb",
    "storage_gb",
]

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "products.csv"


class Product(BaseModel):
    id: str
    title: str
    category: str
    brand: str | None
    price: float = Field(ge=0, allow_inf_nan=False)
    description: str
    weight_kg: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    processor: str | None
    ram_gb: int | None = Field(default=None, ge=0)
    storage_gb: int | None = Field(default=None, ge=0)


def _optional_text(value: str) -> str | None:
    value = value.strip()
    return value or None


def _optional_float(value: str, column: str, row_number: int) -> float | None:
    value = value.strip()
    if not value:
        return None

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {column} must be a number; got {value!r}"
        ) from exc


def _optional_int(value: str, column: str, row_number: int) -> int | None:
    value = value.strip()
    if not value:
        return None

    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {column} must be a whole number; got {value!r}"
        ) from exc

    if not number.is_integer():
        raise ValueError(
            f"Row {row_number}: {column} must be a whole number; got {value!r}"
        )

    return int(number)


def load_products(path: Path = CATALOG_PATH) -> list[Product]:
    if not path.exists():
        raise FileNotFoundError(f"Product catalog not found: {path}")

    products: list[Product] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "CSV headers must match the contract exactly and in order. "
                f"Expected: {EXPECTED_COLUMNS}; found: {reader.fieldnames}"
            )

        for row in reader:
            row_number = reader.line_num

            if None in row:
                raise ValueError(f"Row {row_number}: unexpected extra CSV values")

            if not any((value or "").strip() for value in row.values()):
                continue

            item = {key: (row.get(key) or "").strip() for key in EXPECTED_COLUMNS}

            for required in ("id", "title", "category"):
                if not item[required]:
                    raise ValueError(
                        f"Row {row_number}: required field {required!r} is blank"
                    )

            if not item["description"]:
                item["description"] = ""

            if not item["price"]:
                raise ValueError(f"Row {row_number}: required field 'price' is blank")

            try:
                item["price"] = float(item["price"])
                item["brand"] = _optional_text(item["brand"])
                item["processor"] = _optional_text(item["processor"])
                item["weight_kg"] = _optional_float(
                    item["weight_kg"], "weight_kg", row_number
                )
                item["ram_gb"] = _optional_int(
                    item["ram_gb"], "ram_gb", row_number
                )
                item["storage_gb"] = _optional_int(
                    item["storage_gb"], "storage_gb", row_number
                )

                product = Product.model_validate(item)
            except (ValueError, ValidationError) as exc:
                raise ValueError(f"Invalid product on row {row_number}: {exc}") from exc

            if product.id in seen_ids:
                raise ValueError(
                    f"Row {row_number}: duplicate product id {product.id!r}"
                )

            seen_ids.add(product.id)
            products.append(product)

    return products