\# AI E-Commerce Product Recommendation Assistant



Phase 1 shopping assistant that recommends laptops from a product catalog using natural-language search, exact filters, semantic similarity, and catalog-grounded answers.



\## Features



\- Natural-language laptop search

\- Category and maximum-price filters

\- Embedding-based semantic ranking

\- Catalog-backed recommendation reasons

\- Product questions through the `/ask` API



\## Technology



\- Frontend: React with Vite

\- Backend: Python and FastAPI

\- Embeddings: Sentence Transformers (`all-MiniLM-L6-v2`)

\- Catalog: `data/products.csv`



\## Setup on Windows



Run from the repository root:



&#x20;   python -m venv backend\\.venv

&#x20;   .\\backend\\.venv\\Scripts\\Activate.ps1

&#x20;   python -m pip install -r backend\\requirements.txt



Start the backend in one PowerShell window:



&#x20;   cd backend

&#x20;   python -m uvicorn app.main:app --reload



Start the frontend in a second PowerShell window:



&#x20;   cd frontend

&#x20;   npm install

&#x20;   npm run dev



Open the local URL printed by Vite. The first backend startup may download the embedding model.



\## API



\- `GET /health` — checks that the API is running

\- `POST /recommend` — returns filtered and ranked laptop recommendations

\- `POST /ask` — answers a product question from its catalog record



Interactive API docs: `http://127.0.0.1:8000/docs`



\## Catalog



The catalog is `data/products.csv`; prices are in INR. Unknown optional specifications are left blank.



Before redistributing this catalog in the public repository, document its source and confirm the license allows redistribution.



\## Known limitations



\- The catalog currently covers laptops.

\- Search parsing and recommendation explanations use basic rules.

\- Product answers use catalog fields; they do not use an LLM.

\- Product embeddings are generated when the backend starts.

