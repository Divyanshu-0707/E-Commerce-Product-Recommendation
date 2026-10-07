# AI E-Commerce Product Recommendation & Assistant

## Project goal

Build an end-to-end shopping assistant for a product catalog. A shopper should be able to write a request such as “a lightweight laptop for programming under ₹60,000” and receive relevant catalog products, reasons for the recommendations, and answers to product questions. The workshop focus is recommendation, embeddings, semantic search, and an optional large language model (LLM).

The assistant must use trusted catalog records. It must not invent products, prices, specifications, ratings, availability, or policies. If the catalog lacks an answer, it should say so. Checkout, payments, live inventory, and store scraping are outside the initial workshop scope.

## Required user experiences

1. Accept a natural-language product request and return relevant matches.
2. Show each result's name, price, category, important attributes, and a concise reason for its ranking.
3. Apply explicit budget and category requirements as hard filters.
4. Update recommendations when the shopper changes a budget or preferred category.
5. Explain why a particular product was recommended using its actual attributes.
6. Answer a factual question about a product from stored catalog information, or state that the information is unavailable.
7. Handle no-result requests without presenting an item that breaks the user's stated constraints.

## Suggested pipeline

`catalog → validate and clean → structured records and embeddings → index → understand query → hard filters → semantic retrieval → rank → explain/display → collect interactions`

Keep the components separate. The team may choose its language, framework, model, and interface. A local demo should still work with keyword or TF-IDF retrieval if an embedding or LLM service is unavailable. An external model should be optional, and credentials must come from environment variables.

### Catalog and data preparation

- Use a sample catalog the team is allowed to redistribute. Document its source and license in the README.
- Give every product a stable unique ID. Required fields: name, category, numeric price, currency, description, and relevant attributes. Add brand, rating, image, and availability only when the source provides them.
- Normalize categories, price formats, units, and empty values. Preserve unknown values as unknown.
- Validate duplicate IDs, missing names, invalid prices, and missing required fields before indexing.
- Keep original data separate from cleaned data and generated indexes. Document how to rebuild generated files.

### Search and ranking

- Parse explicit constraints such as maximum price and category. Apply them before ranking.
- Search descriptive needs against product names, descriptions, and attributes using text similarity or embeddings.
- Rank eligible products by relevance using a documented method. Do not allow a high similarity score to override a hard budget limit.
- When nothing matches, explain which constraints produced no results. Alternatives may be shown only if clearly labeled as outside the constraints.

### Explanations and questions

- Generate recommendation reasons from the returned product's stored attributes. Include limitations when relevant.
- For product questions, identify the product and answer using its stored fields. State “not available in our catalog” when a fact is absent.
- If using an LLM, give it only retrieved product records as factual context and check that its answer does not add unsupported claims.
- Treat product descriptions and user text as data, not instructions to change program behavior or expose secrets.

## Minimum demo checks

| Scenario | Expected result |
| --- | --- |
| Natural-language request | Relevant catalog products appear in a useful order. |
| Maximum budget | No result exceeds the stated limit. |
| Category change | Results update to the chosen category. |
| Recommendation explanation | The reason cites real product attributes. |
| Product question | The answer comes from a stored field, or states that it is unknown. |
| No matches | The system explains the result without fabricating a product. |

Include example queries and expected behavior in the README so the demo can be repeated on another machine.

## Implementation stages

### Stage 1: Foundation

Choose and document the catalog. Define the product schema. Add a README with prerequisites, installation, run commands, and example queries. Add `.gitignore` entries for virtual environments, caches, generated indexes, local configuration, and secrets.

### Stage 2: Recommendation engine

Implement catalog validation and cleaning, exact price/category filters, semantic or text retrieval, and ranking. Return structured results with product IDs, attributes, and reasons.

### Stage 3: Assistant and interface

Build a simple UI or CLI. Let users enter requests and adjust filters. Add catalog-grounded explanations and product Q&A. Keep any hosted model integration optional.

### Stage 4: Verification and presentation

Run the minimum demo checks. Also test malformed queries, missing fields, an empty catalog, and no-result cases. Document known limitations and prepare a short presentation script.

## Team workflow

- `main` is the final reviewed branch. Divyanshu manages its updates.
- `development` is the shared integration branch and the source of teammates' updates.
- Personal branches are `aditi`, `devansh`, `divyanshu`, and `krish`. Use them for isolated work and pull requests when coordinating parallel changes. The team may work directly on `development` if Divyanshu chooses that simpler process.
- Get the latest `development` before starting and again before pushing. Resolve conflicts carefully. Never force-push a shared branch.
- Use descriptive commit messages. For each change, explain how to run or check it.
- Agree on file or feature ownership before two people edit the same area. Record actual assignments in issues or the README; do not assume them from branch names.

## Code and repository quality

- Prefer clear functions and a small, understandable dependency set.
- Add tests or reproducible manual checks for filtering, ranking, and grounded answers.
- Never commit passwords, API keys, tokens, private customer data, or large generated files.
- Keep setup instructions current whenever dependencies, commands, data, or configuration change.
- Do not claim a feature works until it has been run on representative catalog records.

## Definition of done

A feature is done when a teammate can run it from a fresh checkout using the README, its relevant edge cases have been checked, and its outputs are traceable to catalog records. The project is ready for presentation when every minimum demo scenario passes.
