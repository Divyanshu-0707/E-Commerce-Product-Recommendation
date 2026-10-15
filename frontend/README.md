# Shopping assistant frontend

React and Vite provide catalog search, filters, product details and reasons, comparison, helpfulness feedback, product questions, and the agent form.

## Run

Node.js 24 was used for local verification. Start the backend first using [backend setup](../backend/README.md). From the repository root:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open [the app](http://127.0.0.1:5173/). The API address in `src/App.jsx` is `http://127.0.0.1:8000`. Port 5173 is allowed by backend CORS; `--strictPort` prevents Vite silently selecting an unsupported port.

Enter a request, optionally select a category and budget, and click **Find recommendations**. Changing filters requires submitting again. For no matches, the interface shows the explanation from the last submitted response. Unsubmitted edits do not change that explanation.

Q&A and the agent require Groq credentials on the backend. Search itself does not require those credentials.

## Checks and build preview

```powershell
npm run lint
npm run build
npm run preview -- --host 127.0.0.1 --port 5173 --strictPort
```

Stop the dev server before using preview on the same port. The default preview port 4173 is not allowed by the current backend CORS configuration. A successful build does not establish live API or AI-answer correctness.

See [example searches](../docs/example-searches.md) and [demo script](../docs/demo-script.md).
