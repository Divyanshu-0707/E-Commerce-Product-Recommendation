# Example searches and expected results

Use these examples with the current synthetic catalog. Open the frontend at `http://127.0.0.1:5173/` while the backend is running at `http://127.0.0.1:8000`.

Set the query, category, and maximum price, then click **Find recommendations**. Changing a filter alone does not refresh results; submit the form again. Exact ranking can vary with the embedding model, so judge the returned fields and constraints rather than expecting a fixed first product.

| Example | Query | Category | Maximum price (INR) | Expected behavior |
| --- | --- | --- | --- | --- |
| Natural-language need | `lightweight laptop for programming under 60000` | Laptop | 60000 | Up to 10 laptops costing at most 60,000; inspect stored weight, processor, and RAM in the reasons. “Lightweight” is a relevance preference, not a numeric weight limit. |
| Numeric requirement | `smartphone with at least 8 GB RAM` | Smartphone | 30000 | Only smartphones costing at most 30,000 with at least 8 GB RAM. |
| Different category | `headphones for music` | Headphones | 5000 | Only headphones costing at most 5,000. |
| Budget change | Repeat the smartphone search above | Smartphone | 15000 | Resubmitted results obey the lower price limit; fewer products may qualify. |
| No matches | `books` | Books | 1 | Empty results and a no-match message showing the candidate count after category and budget filters; no over-budget alternatives. |

To demonstrate a category change, replace the laptop query and filters with the headphones example, then submit again. Update the query too: leaving an explicit category in the query can conflict with a different dropdown choice.

## Why was a product recommended?

Read the reasons beneath a returned product. Compare each claim with its displayed price, category, and attributes. For the laptop example, the live API returned `Notebook Core 02` (`synthetic-laptop-002`) with a price of INR 31,876.55, weight of 1.39 kg, and 16 GB RAM on 15 October 2026. Those are fictional catalog values, not verified market specifications or a guarantee of programming performance.

## Product questions

Direct questions about stored fields work without a Groq key. If a question does not name a field clearly, optional Groq assistance selects candidate fields and the backend checks them against the product record before composing an answer. The shopping agent still requires a valid `GROQ_API_KEY` in `backend/.env`.

1. Find a product and ask `How much RAM does this product have?` in its product question box. The answer should match that product's stored `ram_gb` when present.
2. Ask `What is the warranty period?` for a record with no warranty field. The expected answer is that the catalog does not provide that information.
3. Do not accept a plausible answer as proof: compare it with the stored record. These are expected Q&A outcomes, not live-verified results.

## Verification snapshot

On 15 October 2026, live `POST /recommend` checks returned 10 results for the laptop example, 7 for the smartphone example, 7 for the headphones example, and 0 for books under INR 1. The three nonempty requests were checked for category and budget compliance, and the smartphone request was checked for its RAM minimum. These API checks do not establish browser behavior, overall ranking quality, or LLM answer accuracy.

For catalog details, see [Synthetic catalog](synthetic-catalog.md). For the presentation sequence, see [Demo script](demo-script.md).
