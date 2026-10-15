# Three-minute project demo

## Before presenting

- Start the backend and frontend using the project setup instructions. Allow the embedding model to finish loading before searching.
- Open `http://127.0.0.1:5173/`. Confirm `http://127.0.0.1:8000/health` returns `{"status":"ok"}`.
- Use the inputs in [Example searches](example-searches.md).
- If presenting Q&A or the agent, configure `GROQ_API_KEY` in `backend/.env`, restart the backend, and try a question beforehand. Keep credentials off the projector. Without a key, explain that this portion is unavailable.

## 0:00–0:25: Introduce the problem

“A shopper usually describes a need rather than an exact product name. Our assistant combines catalog filters with semantic similarity to recommend products and show the stored details behind each match.”

“This demo uses 600 fictional products across 12 categories. Prices and specifications are synthetic, so this demonstrates the shopping workflow rather than real buying advice.”

## 0:25–1:05: Search and explain

Enter `lightweight laptop for programming under 60000`, choose **Laptop**, set maximum price to **60000**, and submit.

Point to a returned name, price, category, and attributes. Read its reasons and compare them with the same record.

“Budget and category are hard filters. The eligible products are ranked using semantic similarity and keyword overlap. The reasons cite stored details such as weight and RAM. A match score is a ranking signal, not a measured probability that this is the best product.”

## 1:05–1:40: Change the requirements

Use `smartphone with at least 8 GB RAM`, choose **Smartphone**, set the maximum price to **30000**, and submit. Show the price and RAM fields. Lower the budget to **15000** and click **Find recommendations** again.

“The new request runs the filters again. Changing a control takes effect when we submit the form.”

## 1:40–2:10: Ask a catalog question

If Groq is configured, ask a smartphone result `How much RAM does this product have?` and compare the answer with its attributes. Then ask about a warranty when none is recorded.

“The model receives the selected catalog record. It should say the information is unavailable when a fact is missing. We still need broader checks of generated answers.”

If Groq is unavailable, show the stored attributes and state that live Q&A requires the API key. Do not present an invented response as a live answer.

## 2:10–2:35: Show a no-result case

Enter `books`, choose **Books**, set maximum price to **1**, and submit.

“No catalog product meets this budget. The system returns no matches instead of silently exceeding the limit.”

## 2:35–3:00: Explain the pipeline and limits

“The flow is CSV catalog, validation, product text and embeddings, hard filters, ranking, reasons, and display. The interface also offers helpfulness feedback, which is stored locally; it does not currently retrain the ranking.”

“The next steps are local fallbacks for unavailable services, better category wording, clearer no-result explanations, and fuller end-to-end validation.”

## Optional extension

Select two products for the side-by-side comparison. If Groq is configured, demonstrate the assistant with a request to find and compare two products. The agent can call search, comparison, and detail tools, with a six-round tool limit. This is optional and is not needed for the three-minute sequence.
