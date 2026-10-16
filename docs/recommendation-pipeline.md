# How recommendations work

The current application combines exact filters with semantic and keyword similarity. It searches the stored catalog; it does not browse stores or verify market prices. See [Synthetic catalog](synthetic-catalog.md) for the data's origin and limits.

## Request flow

```text
CSV -> validate records -> build product text -> normalized embeddings/cache
User query + controls -> resolve hard filters -> eligible products
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

Hard filters run before ranking. A highly similar item above the budget is excluded. If no products qualify, the result list is empty. The current code has no minimum relevance threshold, so a weakly relevant eligible product can still appear.

## Answers and agent tools

Recommendation reasons use ordinary Python rules and do not call an LLM. Product Q&A sends one selected product record to Groq with instructions to use only that record. The assistant can call catalog search, two-product comparison, and product-detail tools, with a six-round tool limit. Q&A and the agent require credentials; generated answers have no independent factual validator.

## Current limits

- Explicit request fields override corresponding values inferred from text; conflicting inputs are not reconciled automatically.
- Category aliases cover common phrases such as phone, smartphones, and home kitchen; arbitrary wording is still limited. Explicit category controls take precedence.
- Filters update results after form submission, not immediately on control changes.
- If model setup or query embedding fails, recommendations use keyword-only ranking. This keeps search available offline but reduces matching to words found in the catalog record.
- Empty results include the resolved filter combination. The message does not claim which individual filter independently caused the failure or relax constraints automatically.
- Correct filtering does not establish semantic ranking quality or the accuracy of generated answers.

Use [Example searches](example-searches.md) to repeat a search.
