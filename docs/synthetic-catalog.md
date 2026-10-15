# Current synthetic catalog

The active catalog is `data/products.csv`. It contains 600 fictional products: 50 in each of 12 categories. All prices use INR. Product names, brands, descriptions, prices, and attributes are demo fixtures, not real listings, live inventory, or verified product claims.

This document describes the current multi-category catalog. The older `catalog-data-notes.md` describes the preserved laptop dataset and should not be used as the current catalog profile.

## Origin and reuse status

The project includes a local generator at `scripts/generate_synthetic_demo_catalog.py`. Its seed is `20261013`; category specifications and price ranges are defined in that script. `data/catalog_metadata.json` identifies the active data as synthetic and records its count and categories. The generator is the reproducible source for the demo catalog; it does not scrape a store or fetch live prices.

No explicit dataset license is supplied in these files. Synthetic origin does not itself establish a license: the team still needs to record its chosen reuse terms before public redistribution. Do not assign an unverified external dataset source or license to this catalog.

The earlier 3,463-row laptop CSV is preserved separately at `data/source/products.csv`. Its original external source and redistribution permission remain unverified. It is not the active multi-category demo catalog.

## Categories

| Category key | Products |
| --- | ---: |
| laptop | 50 |
| smartphone | 50 |
| headphones | 50 |
| tablet | 50 |
| clothing | 50 |
| shoes | 50 |
| home_kitchen | 50 |
| furniture | 50 |
| books | 50 |
| sports_fitness | 50 |
| beauty | 50 |
| toys_games | 50 |

## CSV structure

| Column | Meaning |
| --- | --- |
| `id` | Stable generated ID, such as `synthetic-smartphone-001`. |
| `title` | Product display name. |
| `category` | Category key from the table above. |
| `brand` | Fictional brand; the loader permits an unknown brand. |
| `price` | Non-negative numeric price. |
| `currency` | `INR` for this catalog. |
| `description` | Text explicitly identifying the record as a synthetic demo listing. |
| `attributes` | JSON object containing category-specific details. |

Examples of attributes include laptop `ram_gb` and `weight_kg`, smartphone `battery_mah`, clothing `material`, and book `genre`. Some generated attributes are deliberately omitted to exercise unknown-information handling. A missing value must not be treated as zero or guessed from the category.

## Loading and validation

`backend/app/catalog.py` checks the CSV header layout, required values, duplicate IDs, invalid prices, and JSON attribute objects. It trims shared text fields, normalizes category casing and currency casing, and loads records into the shared product model. It also supports the preserved legacy laptop CSV format.

Category-specific attribute names and units are defined by the generator. The loader does not establish that a fictional specification is realistic or normalize every possible unit in arbitrary imported attributes.

## Rebuilding the generated data

From the repository root, after creating the backend environment:

```powershell
.\backend\.venv\Scripts\python.exe scripts\generate_synthetic_demo_catalog.py
```

This overwrites `data/products.csv` and `data/catalog_metadata.json`. It leaves `data/source/products.csv` intact. Reusing the unchanged script and seed gives reproducible product rows. Restart the backend afterward so its in-memory catalog is reloaded.

Product embeddings are cached under `backend/.cache/`. The cache key includes the model name and product text. Backend startup creates embeddings when there is no usable matching cache; regenerating unchanged product text can reuse the existing cache. The backend currently requires the embedding model to load even when cached vectors exist.

## Limits

- The balanced sample is useful for exercising categories and filters; it does not represent market demand or real catalog distributions.
- Prices are illustrative, and attribute combinations may be unrealistic.
- Ratings, availability, warranty terms, and policies must not be invented when absent.
- This catalog cannot demonstrate recommendation quality for thousands of real products without further data and evaluation.

See [Example searches](example-searches.md) for repeatable inputs and [Demo script](demo-script.md) for presentation guidance.
