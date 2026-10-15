# Catalog data notes



## Source and reuse



- Project input file: `data/products.csv`

- Original dataset name and source URL: Not recorded; verify from the original download before citing or redistributing the data.

- License and redistribution permission: Not verified.

- Download or snapshot date: Not recorded.

- Price currency: INR, as confirmed by the project owner.



## Current catalog profile



- Product count: 3,463

- Product category: laptops

- Duplicate product IDs: 0

- Missing required fields: 0

- Missing weight values: 2,160

- Missing product type values: 2,160

- Missing condition values: 1,303



## Transformations



- Category is normalized to `laptop`.

- Product type and condition are stored in separate CSV columns when identified from the source description.

- Unknown optional values remain blank in the CSV and load as null.

- Prices are represented in INR.



## Known limitations



- The original dataset source, license, and download date still need verification.

- The date represented by catalog prices is unknown.

- Many products have no weight value, so weight filters must not treat missing weight as zero.

- Blank product type or condition means that value was not identified for that row.


