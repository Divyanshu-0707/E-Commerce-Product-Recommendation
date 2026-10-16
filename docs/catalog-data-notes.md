# Preserved legacy laptop catalog notes

This file describes the older laptop-only dataset at `data/source/products.csv`. It is preserved for reference and is not the active catalog. The active 600-product catalog is documented in [synthetic-catalog.md](synthetic-catalog.md).

## Source and reuse

- Original dataset name and source URL: not recorded; verify from the original download before citing or redistributing.
- License and redistribution permission: not verified. Do not redistribute this legacy file until its source and rights are confirmed.
- Download or snapshot date: not recorded.
- Currency recorded by the project: INR.

## Preserved catalog profile

- Product count: 3,463.
- Product category: laptops.
- Duplicate product IDs: 0.
- Missing required fields: 0.
- Missing weight values: 2,160.
- Missing product type values: 2,160.
- Missing condition values: 1,303.

## Transformations in the preserved source

- Category is normalized to `laptop` when the migration script reads the file.
- Product type and condition remain optional values.
- Unknown optional values remain blank and load as unknown.
- Prices are treated as INR by the migration script; the original source currency has not been verified.

## Known limitations

- The original source, license, redistribution permission, download date, and price date are unknown.
- Many products have no weight, so a weight filter must not treat missing weight as zero.
- Blank product type or condition means the value was not identified for that row.
