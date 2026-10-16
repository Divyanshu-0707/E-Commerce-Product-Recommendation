"""Generate the fictional demo catalog."""

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "products.csv"
METADATA_PATH = ROOT / "data" / "catalog_metadata.json"
PRODUCTS_PER_CATEGORY = 50
SEED = 20261013


# All generated products and details are fictional.
CATEGORY_SPECS = {
    "laptop": {
        "brand": [
            "Demo Aster",
            "Demo Northstar",
            "Demo Pixelworks",
            "Demo Cedar",
            "Demo Orbit",
        ],
        "models": [
            "Notebook",
            "Creator Book",
            "Travel Mate",
            "Workstation",
            "Everyday PC",
            "Studio Slate",
            "Compact Pro",
            "Flex Book",
            "Learning PC",
            "Field Laptop",
        ],
        "variants": ["Air", "Core", "Plus", "Edge", "Nova"],
        "price": (28999, 169999),
        "attributes": lambda rng: {
            "processor": rng.choice(
                ["Demo Core 5", "Demo Core 7", "Demo Ryzen 5", "Demo Ryzen 7"]
            ),
            "ram_gb": rng.choice([8, 16, 16, 32]),
            "storage_gb": rng.choice([256, 512, 512, 1024]),
            "screen_inches": rng.choice([13.3, 14.0, 15.6, 16.0]),
            "weight_kg": round(rng.uniform(1.1, 2.4), 2),
        },
    },
    "smartphone": {
        "brand": [
            "Demo Aster",
            "Demo Northstar",
            "Demo Pixelworks",
            "Demo Cedar",
            "Demo Orbit",
        ],
        "models": [
            "Smartphone",
            "Camera Phone",
            "Pocket Phone",
            "Everyday Phone",
            "Travel Phone",
            "Studio Phone",
            "Compact Phone",
            "Power Phone",
            "Flex Phone",
            "Field Phone",
        ],
        "variants": ["Air", "Core", "Plus", "Edge", "Nova"],
        "price": (6999, 89999),
        "attributes": lambda rng: {
            "ram_gb": rng.choice([4, 6, 8, 12]),
            "storage_gb": rng.choice([64, 128, 256, 512]),
            "screen_inches": rng.choice([6.1, 6.4, 6.7, 6.9]),
            "battery_mah": rng.choice([4000, 4500, 5000, 5500]),
            "water_resistant": rng.choice([True, False]),
        },
    },
    "headphones": {
        "brand": [
            "Demo Sound",
            "Demo Northstar Audio",
            "Demo Cedar Audio",
            "Demo Orbit Sound",
            "Demo Aster Audio",
        ],
        "models": [
            "Over-Ear Headphones",
            "Studio Headphones",
            "Travel Headphones",
            "Wireless Earbuds",
            "Sport Earbuds",
            "On-Ear Headphones",
            "Quiet Headphones",
            "Daily Earbuds",
            "Foldable Headphones",
            "Open-Ear Set",
        ],
        "variants": ["Air", "Core", "Plus", "Edge", "Nova"],
        "price": (999, 32999),
        "attributes": lambda rng: {
            "connectivity": rng.choice(["Bluetooth", "Wired", "Bluetooth and wired"]),
            "noise_cancelling": rng.choice([True, False]),
            "battery_hours": rng.choice([0, 18, 24, 30, 40]),
            "microphone": rng.choice([True, False]),
            "weight_g": rng.choice([180, 220, 260, 310]),
        },
    },
    "tablet": {
        "brand": [
            "Demo Aster",
            "Demo Northstar",
            "Demo Pixelworks",
            "Demo Cedar",
            "Demo Orbit",
        ],
        "models": [
            "Reading Tablet",
            "Creative Tablet",
            "Travel Tablet",
            "Study Tablet",
            "Media Tablet",
            "Compact Tablet",
            "Flex Tablet",
            "Work Tablet",
            "Family Tablet",
            "Field Tablet",
        ],
        "variants": ["Air", "Core", "Plus", "Edge", "Nova"],
        "price": (8999, 99999),
        "attributes": lambda rng: {
            "screen_inches": rng.choice([8.0, 10.1, 11.0, 12.4]),
            "ram_gb": rng.choice([4, 6, 8, 12]),
            "storage_gb": rng.choice([64, 128, 256, 512]),
            "stylus_support": rng.choice([True, False]),
            "battery_hours": rng.choice([8, 10, 12, 14]),
        },
    },
    "clothing": {
        "brand": [
            "Demo Loom",
            "Demo Cedar Wear",
            "Demo Northstar Cloth",
            "Demo Aster Thread",
            "Demo Fieldwear",
        ],
        "models": [
            "Everyday Shirt",
            "Weekend T-Shirt",
            "Light Jacket",
            "Travel Hoodie",
            "Classic Trousers",
            "Relaxed Kurta",
            "Daily Dress",
            "Layering Sweater",
            "Utility Overshirt",
            "Casual Shorts",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (399, 8999),
        "attributes": lambda rng: {
            "size": rng.choice(["XS", "S", "M", "L", "XL", "XXL"]),
            "color": rng.choice(["navy", "olive", "sand", "charcoal", "rust", "cream"]),
            "material": rng.choice(
                ["cotton blend", "linen blend", "recycled polyester", "wool blend"]
            ),
            "fit": rng.choice(["regular", "relaxed", "slim"]),
            "care": rng.choice(["machine wash cold", "hand wash", "dry clean"]),
        },
    },
    "shoes": {
        "brand": [
            "Demo Pace",
            "Demo Cedar Steps",
            "Demo Northstar Trail",
            "Demo Aster Move",
            "Demo Fieldfoot",
        ],
        "models": [
            "Walking Shoes",
            "Trail Shoes",
            "Daily Sneakers",
            "Court Shoes",
            "Running Shoes",
            "Slip-On Shoes",
            "Hiking Boots",
            "Training Shoes",
            "Canvas Shoes",
            "City Sandals",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (799, 12999),
        "attributes": lambda rng: {
            "size_in": rng.choice([6, 7, 8, 9, 10, 11]),
            "color": rng.choice(["navy", "olive", "sand", "charcoal", "rust", "cream"]),
            "upper_material": rng.choice(
                ["mesh", "canvas", "synthetic knit", "vegan leather"]
            ),
            "sole": rng.choice(["rubber", "foam", "EVA blend"]),
            "water_resistant": rng.choice([True, False]),
        },
    },
    "home_kitchen": {
        "brand": [
            "Demo Hearth",
            "Demo Cedar Home",
            "Demo Northstar Living",
            "Demo Aster House",
            "Demo Daywell",
        ],
        "models": [
            "Storage Set",
            "Pour-Over Kettle",
            "Serving Bowl",
            "Desk Lamp",
            "Pantry Jar",
            "Prep Board",
            "Table Fan",
            "Water Bottle",
            "Mixing Set",
            "Reading Light",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (249, 14999),
        "attributes": lambda rng: {
            "material": rng.choice(
                [
                    "stainless steel",
                    "ceramic",
                    "bamboo",
                    "borosilicate glass",
                    "recycled plastic",
                ]
            ),
            "color": rng.choice(["navy", "olive", "sand", "charcoal", "rust", "cream"]),
            "capacity_l": rng.choice([0.5, 0.75, 1.0, 1.5, 2.0]),
            "dishwasher_safe": rng.choice([True, False]),
            "dimensions_cm": {
                "width": rng.choice([10, 15, 20, 25]),
                "height": rng.choice([8, 12, 18, 24]),
            },
        },
    },
    "furniture": {
        "brand": [
            "Demo Hearth",
            "Demo Cedar Home",
            "Demo Northstar Living",
            "Demo Aster House",
            "Demo Daywell",
        ],
        "models": [
            "Reading Chair",
            "Writing Desk",
            "Storage Bench",
            "Side Table",
            "Book Shelf",
            "Dining Chair",
            "Bedside Table",
            "Lounge Stool",
            "Wall Shelf",
            "Compact Cabinet",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (1499, 34999),
        "attributes": lambda rng: {
            "material": rng.choice(
                [
                    "engineered wood",
                    "bamboo",
                    "steel and wood",
                    "solid pine",
                    "recycled board",
                ]
            ),
            "color": rng.choice(["natural", "walnut", "white", "charcoal", "sage"]),
            "width_cm": rng.choice([40, 60, 80, 100, 120]),
            "height_cm": rng.choice([45, 60, 75, 90, 120]),
            "assembly_required": rng.choice([True, False]),
        },
    },
    "books": {
        "brand": [
            "Demo Leaf Press",
            "Demo Northstar Books",
            "Demo Cedar House",
            "Demo Aster Pages",
            "Demo Daywell Reads",
        ],
        "models": [
            "The Quiet Observatory",
            "A Map of Small Ideas",
            "The River Notebook",
            "Gardens After Rain",
            "The Curious Workshop",
            "Letters from Elsewhere",
            "A Practical Sky",
            "The Midnight Library Cart",
            "Patterns of Everyday Life",
            "The Long Weekend Guide",
        ],
        "variants": [
            "Reader Edition",
            "Illustrated Edition",
            "Pocket Edition",
            "Study Edition",
            "Collector Edition",
        ],
        "price": (199, 2499),
        "attributes": lambda rng: {
            "format": rng.choice(["paperback", "hardcover", "ebook"]),
            "genre": rng.choice(
                ["fiction", "science", "history", "self-help", "travel", "craft"]
            ),
            "pages": rng.randint(120, 480),
            "language": rng.choice(["English", "Hindi"]),
            "age_group": rng.choice(["adult", "teen", "children"]),
        },
    },
    "sports_fitness": {
        "brand": [
            "Demo Pace",
            "Demo Cedar Active",
            "Demo Northstar Sport",
            "Demo Aster Move",
            "Demo Fieldfit",
        ],
        "models": [
            "Yoga Mat",
            "Training Bands",
            "Trail Bottle",
            "Balance Board",
            "Skipping Rope",
            "Strength Set",
            "Cycling Gloves",
            "Fitness Roller",
            "Practice Ball",
            "Hiking Pack",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (299, 15999),
        "attributes": lambda rng: {
            "sport": rng.choice(
                ["yoga", "running", "cycling", "strength", "hiking", "team sports"]
            ),
            "material": rng.choice(
                [
                    "natural rubber",
                    "foam",
                    "polyester blend",
                    "steel",
                    "recycled polymer",
                ]
            ),
            "weight_kg": round(rng.uniform(0.2, 4.0), 2),
            "skill_level": rng.choice(["beginner", "intermediate", "all levels"]),
            "color": rng.choice(["navy", "olive", "sand", "charcoal", "rust", "cream"]),
        },
    },
    "beauty": {
        "brand": [
            "Demo Dew",
            "Demo Cedar Care",
            "Demo Northstar Glow",
            "Demo Aster Ritual",
            "Demo Daywell Skin",
        ],
        "models": [
            "Daily Cleanser",
            "Soft Hand Cream",
            "Tinted Balm",
            "Calm Face Mist",
            "Gentle Body Wash",
            "Everyday Lotion",
            "Light Hair Oil",
            "Simple Lip Color",
            "Fresh Shampoo",
            "Evening Moisturizer",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (149, 4999),
        "attributes": lambda rng: {
            "product_type": rng.choice(
                ["cleanser", "moisturizer", "balm", "mist", "wash", "hair care"]
            ),
            "skin_type": rng.choice(
                ["dry", "oily", "combination", "all types", "not specified"]
            ),
            "volume_ml": rng.choice([30, 50, 100, 150, 200]),
            "fragrance_free": rng.choice([True, False]),
            "shade": rng.choice(["clear", "warm beige", "soft rose", "not applicable"]),
        },
    },
    "toys_games": {
        "brand": [
            "Demo Playfield",
            "Demo Cedar Toys",
            "Demo Northstar Play",
            "Demo Aster Games",
            "Demo Daywell Kids",
        ],
        "models": [
            "Puzzle Set",
            "Building Tiles",
            "Story Cards",
            "Strategy Board Game",
            "Wooden Blocks",
            "Pattern Kit",
            "Adventure Game",
            "Creative Craft Box",
            "Memory Match",
            "Mini Science Set",
        ],
        "variants": ["Stone", "River", "Meadow", "Dawn", "Cloud"],
        "price": (199, 5999),
        "attributes": lambda rng: {
            "toy_type": rng.choice(
                [
                    "puzzle",
                    "building",
                    "card game",
                    "board game",
                    "craft",
                    "learning toy",
                ]
            ),
            "age_range": rng.choice(["3+", "5+", "8+", "12+"]),
            "material": rng.choice(["wood", "cardboard", "recycled polymer", "fabric"]),
            "player_count": rng.choice([1, 1, 2, 2, 4]),
            "play_time_minutes": rng.choice([10, 20, 30, 45, 60]),
        },
    },
}


def make_description(category: str, title: str, attributes: dict) -> str:
    details = "; ".join(
        f"{key.replace('_', ' ')}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in attributes.items()
    )
    return (
        f"Synthetic demo listing for {title} in the {category.replace('_', ' ')} "
        f"category. Catalog attributes: {details}. All catalog details are fictional demo data."
    )


def generate_products() -> list[dict[str, str]]:
    rng = random.Random(SEED)
    products = []
    for category, spec in CATEGORY_SPECS.items():
        low, high = spec["price"]
        for index in range(PRODUCTS_PER_CATEGORY):
            model = spec["models"][index // len(spec["variants"])]
            variant = spec["variants"][index % len(spec["variants"])]
            title = f"{model} {variant} {index + 1:02d}"
            brand = spec["brand"][index % len(spec["brand"])]
            attributes = spec["attributes"](rng)

            # Leave some details missing to test unknown answers.
            attr_keys = list(attributes)
            if index % 10 == 9:
                attributes.pop(attr_keys[(index // 10) % len(attr_keys)])

            price_offset = (high - low) * index / (PRODUCTS_PER_CATEGORY - 1)
            price = round(low + price_offset, 2)
            product_id = f"synthetic-{category}-{index + 1:03d}"
            products.append(
                {
                    "id": product_id,
                    "title": title,
                    "category": category,
                    "brand": brand,
                    "price": f"{price:.2f}",
                    "currency": "INR",
                    "description": make_description(category, title, attributes),
                    "attributes": json.dumps(
                        attributes, ensure_ascii=False, separators=(",", ":")
                    ),
                }
            )
    return products


def main() -> None:
    products = generate_products()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "id",
                "title",
                "category",
                "brand",
                "price",
                "currency",
                "description",
                "attributes",
            ],
        )
        writer.writeheader()
        writer.writerows(products)

    metadata = {
        "dataset_type": "synthetic_demo",
        "synthetic": True,
        "notice": "All products, brands, prices, descriptions, and attributes are fictional demo data.",
        "product_count": len(products),
        "products_per_category": PRODUCTS_PER_CATEGORY,
        "category_count": len(CATEGORY_SPECS),
        "categories": list(CATEGORY_SPECS),
        "currency": "INR",
        "generation_seed": SEED,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(
        f"Generated {len(products)} synthetic products across {len(CATEGORY_SPECS)} categories."
    )


if __name__ == "__main__":
    main()
