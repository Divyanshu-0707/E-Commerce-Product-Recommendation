# Backend setup

FastAPI loads the catalog, builds or loads cached MiniLM embeddings, and serves recommendation, question, feedback, and agent endpoints.

## Install and run

Python 3.13 was used for local verification. From the repository root:

```powershell
py -3.13 -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for application startup to complete. First use may download `sentence-transformers/all-MiniLM-L6-v2`. Product vectors are cached in `backend/.cache/`. If the embedding model or a query embedding cannot load, recommendations use keyword-only ranking over the catalog text and attributes.

- [Health](http://127.0.0.1:8000/health)
- [Interactive API docs](http://127.0.0.1:8000/docs)

The frontend calls port 8000. Browser origins allowed by the backend are `http://localhost:5173` and `http://127.0.0.1:5173`.

## Groq for Q&A and the agent

Create `backend/.env` with your own credentials:

```env
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-20b
```

`GROQ_MODEL` is optional; the value shown is the code's default. Restart the backend after configuration changes. `/ask` sends the selected product record and question to Groq. `/assistant` uses catalog tools through Groq. Search and rule-based recommendation reasons do not need a Groq key.

Without a valid key/service, Q&A and the agent currently fail rather than providing a local answer. AI answers still need factual verification against catalog records.

Never commit a real key. The current `.gitignore` entries are commented out and do not protect `backend/.env`; check files explicitly before staging changes.

## Catalog, embeddings, and feedback

`data/products.csv` holds 600 synthetic products in 12 categories. Restart the backend after changing the catalog. Product text and model name determine the embedding cache filename; changed text selects a new cache. To force rebuilding, stop the backend, remove the generated `product-embeddings-*.npy` files under `backend/.cache/`, and restart.

`POST /recommend` returns `results` and `message`. `message` is null for nonempty results; an empty result includes the applied filter combination or an empty-catalog explanation. Hard constraints are never automatically relaxed.

Feedback appends to `data/feedback.jsonl` and does not change ranking. [Catalog details and rebuild instructions](../docs/synthetic-catalog.md) describe which generated files are overwritten.

See [pipeline details](../docs/recommendation-pipeline.md) for behavior and limitations.
