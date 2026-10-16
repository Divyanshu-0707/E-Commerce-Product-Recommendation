"""Convert the preserved laptop CSV to the shared product catalog format."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "source" / "products.csv"
OUTPUT_PATH = ROOT / "data" / "products.csv"

LEGACY_COLUMNS = [
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
OUTPUT_COLUMNS = [
    "id",
    "title",
    "category",
    "brand",
    "price",
    "currency",
    "description",
    "attributes",
]


def optional_text(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None


def optional_number(value: str, field: str, row_number: int) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        number = float(cleaned)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {field} must be numeric; got {cleaned!r}"
        ) from exc
    if number < 0:
        raise ValueError(f"Row {row_number}: {field} must not be negative")
    return number


def optional_integer(value: str, field: str, row_number: int) -> int | None:
    number = optional_number(value, field, row_number)
    if number is None:
        return None
    if not number.is_integer():
        raise ValueError(
            f"Row {row_number}: {field} must be a whole number; got {value!r}"
        )
    return int(number)


def migrate_catalog() -> int:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Preserved source catalog not found: {SOURCE_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[str] = set()
    count = 0

    with SOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != LEGACY_COLUMNS:
            raise ValueError(
                f"Unexpected source CSV headers: {reader.fieldnames}; "
                f"expected {LEGACY_COLUMNS}"
            )

        with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()

            for row in reader:
                row_number = reader.line_num
                if None in row:
                    raise ValueError(f"Row {row_number}: unexpected extra CSV values")
                if not any((value or "").strip() for value in row.values()):
                    continue

                item = {key: (row.get(key) or "").strip() for key in LEGACY_COLUMNS}
                for required in ("id", "title", "category", "price", "description"):
                    if not item[required]:
                        raise ValueError(
                            f"Row {row_number}: required field {required!r} is blank"
                        )
                if item["id"] in seen_ids:
                    raise ValueError(
                        f"Row {row_number}: duplicate product id {item['id']!r}"
                    )
                seen_ids.add(item["id"])

                attributes = {
                    "product_type": optional_text(item["product_type"]),
                    "condition": optional_text(item["condition"]),
                    "weight_kg": optional_number(
                        item["weight_kg"], "weight_kg", row_number
                    ),
                    "processor": optional_text(item["processor"]),
                    "ram_gb": optional_integer(item["ram_gb"], "ram_gb", row_number),
                    "storage_gb": optional_integer(
                        item["storage_gb"], "storage_gb", row_number
                    ),
                }
                attributes = {
                    key: value for key, value in attributes.items() if value is not None
                }

                price = float(item["price"])
                if price < 0:
                    raise ValueError(f"Row {row_number}: price must not be negative")

                writer.writerow(
                    {
                        "id": item["id"],
                        "title": item["title"],
                        "category": item["category"].casefold(),
                        "brand": optional_text(item["brand"]) or "",
                        "price": price,
                        "currency": "INR",
                        "description": item["description"],
                        "attributes": json.dumps(
                            attributes, ensure_ascii=False, separators=(",", ":")
                        ),
                    }
                )
                count += 1

    return count


if __name__ == "__main__":
    print(f"Migrated {migrate_catalog()} products to {OUTPUT_PATH}")
