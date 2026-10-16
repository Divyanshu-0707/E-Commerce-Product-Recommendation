# How recommendations work

The current application combines exact filters with semantic and keyword similarity. It searches the stored catalog; it does not browse stores or verify market prices. See [Synthetic catalog](synthetic-catalog.md) for the data's origin and limits.

## Request flow

```text
CSV -> validate records -> build product text -> normalized embeddings/cache
User query + controls -> resolve hard filters -> verify product words -> eligible products
Eligible products + query embedding -> hybrid ranking -> reasons -> React results
Product feedback -> local JSONL file
```

| Step | Current implementation | Source |
| --- | --- | --- |
| Load and validate | Read the CSV, reject invalid required fields/prices/IDs, and parse category attributes. | `backend/app/catalog.py` |
| Build text | Combine title, category, optional brand, price, description, and readable attributes. | `backend/app/search_text.py` |
| Embed and cache | Use `all-MiniLM-L6-v2` to create normalized 384-dimensional vectors. Cache product vectors in a NumPy file keyed by model name and product text. If model setup or query embedding fails, use keyword-only ranking instead. | `backend/app/embeddings.py`, `backend/app/main.py` |
| Resolve constraints | Use explicit request fields first, otherwise infer supported constraints from the query. | `backend/app/recommendation.py` |
| Filter | Exclude products that violate category, budget, brand, supported numeric constraints, or generic attribute filters. Missing required measurements cannot satisfy numeric filters. | `backend/app/recommendation.py` |
| Verify relevance | Require meaningful requested product words in catalog titles, categories, brands, or attributes. Normalize common plurals and category aliases; remove shopping filler and supported numeric constraint phrases. Color and care text alone cannot establish product identity, and false/missing boolean attributes do not establish a requested feature. | `backend/app/recommendation.py` |
| Rank | Combine semantic similarity and keyword overlap, then sort eligible products by descending score. | `backend/app/recommendation.py` |
| Explain | Build reasons from stored fields and matched constraints; return up to six distinct reasons. | `backend/app/reasons.py` |
| Display | Show results, stored attributes, scores, reasons, product questions, and comparison controls. | `frontend/src/App.jsx` |
| Collect feedback | Append product ID, query, helpfulness, and UTC timestamp to `data/feedback.jsonl`. Feedback does not currently train the ranking. | `backend/app/feedback.py` |

There is no separate vector database. The runtime index is the product list paired with an embedding matrix. `/recommend` returns at most 10 results; the agent's search tool returns at most 5.

## Ranking formula

When embeddings are available, the application uses this hybrid score:

```text
semantic = dot(normalized_product_vector, normalized_query_vector)
keyword = matching_query_terms / total_query_terms
score = 0.8 * clip(semantic, 0, 1) + 0.2 * keyword
```

The dot product of normalized vectors is cosine similarity. Negative semantic similarity is clipped to zero. Keyword overlap uses unique English letter tokens after removing a fixed set of stop words. It searches the title, category, legacy product type/condition, brand, description, and legacy processor field. If no query terms remain, the keyword score is zero. Other attributes appear directly in embedding text; the hybrid keyword step does not independently traverse the generic attribute object.

When embeddings are unavailable, the fallback ranks eligible products by the fraction of query terms found in their catalog text, including stored attributes. Its score is a simple keyword overlap, so it will not match synonyms or related concepts as semantic search can. Hard filters still run before either ranking method.

For example, semantic similarity `0.75` and keyword overlap `0.50` give `0.8 * 0.75 + 0.2 * 0.50 = 0.70`. This is a sorting score, not a calibrated 70% probability of suitability.

Hard filters and the product-word relevance check run before ranking. A highly similar item above the budget or without evidence for the requested product words is excluded. There is no score-only cutoff: even a high semantic score cannot establish that a requested item exists. If only five items match, return five, rather than filling ten slots. For example, the catalog contains five hair oils and five lotions, but no perfumes.

The relevance check is intentionally conservative and does not use generated description boilerplate as evidence. Supported demo use cases (`programming`, `coding`, `music`, `work`, `daily use`, including phrases beginning with `for`) remain soft ranking preferences; `lightweight` requires a stored weight field. This is not a guarantee of suitability for those uses.

## Answers and agent tools

Recommendation reasons use ordinary Python rules and do not call an LLM. Direct product questions are resolved from stored fields locally. For less direct wording, optional Groq assistance may select candidate field names, but the backend validates those names and constructs the final answer from the product record. Missing or unrecognized facts are reported as unavailable. The shopping agent uses catalog search, two-product comparison, and product-detail tools through Groq, with a six-round tool limit.

## Current limits

- Explicit request fields override corresponding values inferred from text; conflicting inputs are not reconciled automatically.
- Category aliases cover common phrases such as phone, smartphones, and home kitchen; arbitrary wording is still limited. Explicit category controls take precedence.
- Filters update results after form submission, not immediately on control changes.
- If model setup or query embedding fails, recommendations use keyword-only ranking. This keeps search available offline but reduces matching to words found in the catalog record.
- Empty-result messages show filter counts when hard filters exclude all products, or explain that the requested product details could not be matched when otherwise eligible records exist. The assistant search tool uses the same relevance check and no-match explanation. The system does not relax constraints automatically.
- Correct filtering does not establish semantic ranking quality, and optional model-assisted field selection can still misunderstand less direct wording.
- Matching is based on normalized whole words, not unrestricted language understanding. Unknown synonyms, spelling errors, unsupported languages, and descriptions without corresponding names/attributes can produce conservative no-match results. Negations and arbitrary natural-language attribute constraints are not fully parsed; use structured attribute filters for exact conditions.

Use [Example searches](example-searches.md) to repeat a search.
