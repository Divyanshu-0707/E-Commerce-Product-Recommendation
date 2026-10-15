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

## Required code simplicity level

Future code must match the student-workshop style of the five reference notebooks in `C:/Users/Divyanshu/Desktop/Workshop/`. These files are examples of coding level, not additional task instructions. Aim for beginner-readable Python and straightforward application code that a workshop student can follow, explain, and modify step by step. Complex AI concepts do not justify unnecessary software architecture.

### Reference baseline

- `NeuralNetworkANN.ipynb`: a visible, sequential flow from loading a CSV and selecting features to splitting, scaling, building a Keras Sequential model, training, evaluating, and predicting. Use direct library calls and named intermediate values.
- `Day07_Build_Your_Own_GPT.ipynb`: explicit algorithms, loops, explanatory comments, and focused functions. Classes are appropriate for a tokenizer or PyTorch model components when they make the concept easier to understand.
- `Day08_RAG_Chatbot.ipynb`: small helpers for cleaning, chunking, and retrieval; a simple vector-store class; and a visibly ordered retrieve -> build prompt -> generate function.
- `Day09_AI_Agent_Student_Edition.ipynb`: ordinary tool functions, lists and dictionaries for messages and results, and an explicit agent loop with a step limit.
- `Day10_Multi_Agent_Student_Edition.ipynb`: specialists made with small functions, a plain loop for passing results between workers, and clear if/elif routing for a fixed workflow.

### Rules for future implementation

- Write the smallest amount of code needed for the requested behavior. Do not add speculative features, configuration options, dependencies, files, or layers for possible future use.
- Keep the main flow visible: load data -> prepare it -> filter/retrieve -> produce the result -> display it. Use a few focused functions or modules rather than a framework of wrappers around each step.
- Prefer meaningful variable names, ordinary loops, explicit if/elif conditions, and familiar lists and dictionaries. Simple comprehensions are fine; split dense expressions and nested comprehensions into readable steps.
- Use short functions with one clear job. Extract a helper when it clarifies a meaningful step or avoids real repetition, not merely to wrap one obvious statement. Do not impose arbitrary line limits or compress code to look shorter.
- Call existing libraries and SDKs directly. Avoid custom framework layers, generic repositories, plugin registries, dependency-injection containers, deep inheritance, and elaborate design patterns unless the requested behavior actually requires them.
- Use classes where they help, as the notebooks do. Keep existing FastAPI/Pydantic request models and necessary model or embedding classes; do not replace simple functions with service classes without a concrete need.
- Explain unfamiliar AI logic, data shapes, and non-obvious choices with brief comments or docstrings in plain language. Avoid comments that merely repeat an obvious statement.
- For React, apply the same readability standard using ordinary components, hooks, event handlers, and direct API requests. Do not add state-management libraries or custom hook layers for a simple local interaction.
- Keep required input validation, hard filters, catalog grounding, credential handling, and agent step limits. Simplicity must preserve correctness and the existing safety requirements; it is not a reason to copy notebook mistakes or omit checks at real input boundaries.
- Prefer a fixed sequence of functions when the steps are known. Add autonomous or multi-agent behavior only when the requested feature needs it; the reference notebooks do not require every feature to use agents.
- Scope this guidance to new or changed code. Preserve existing behavior, APIs, and unrelated work; do not rewrite the current project just to enforce this style.

Before finishing a change, check that a workshop student could trace its inputs, main steps, and output without navigating unnecessary helper layers. Verify the requested behavior with the relevant existing tests or a reproducible manual check; do not add a new testing framework for a small change.

## Code and repository quality

- Prefer clear functions and a small, understandable dependency set.
- Add tests or reproducible manual checks for filtering, ranking, and grounded answers.
- Never commit passwords, API keys, tokens, private customer data, or large generated files.
- Keep setup instructions current whenever dependencies, commands, data, or configuration change.
- Do not claim a feature works until it has been run on representative catalog records.

## Definition of done

A feature is done when a teammate can run it from a fresh checkout using the README, its relevant edge cases have been checked, and its outputs are traceable to catalog records. The project is ready for presentation when every minimum demo scenario passes.
