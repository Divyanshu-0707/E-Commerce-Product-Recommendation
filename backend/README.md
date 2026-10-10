\# Backend Setup



\## Requirements



\- Python

\- A Groq API key for the `/ask` endpoint



\## Install on Windows



Run these commands from the repository root:



```powershell

python -m venv backend\\.venv

.\\backend\\.venv\\Scripts\\Activate.ps1

python -m pip install -r backend\\requirements.txt

```



\## Configure the Groq API



Create `backend/.env` with:



```env

GROQ\_API\_KEY=your-groq-api-key

GROQ\_MODEL=openai/gpt-oss-20b

```



Replace `your-groq-api-key` with your own key. Keep the real key private; never commit or share it. `.env` files are ignored by Git.



The `/ask` endpoint sends the selected product's catalog data and the question to Groq. Free-tier usage is subject to provider limits.



\## Run the backend



From the repository root:



```powershell

cd backend

.\\.venv\\Scripts\\Activate.ps1

python -m uvicorn app.main:app --reload

```



Leave this terminal open while using the app. The backend runs at `http://127.0.0.1:8000`.



\- Health check: `http://127.0.0.1:8000/health`

\- Interactive API docs: `http://127.0.0.1:8000/docs`

