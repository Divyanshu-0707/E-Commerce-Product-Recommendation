import { useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function formatPrice(price) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(price);
}

export default function App() {
  const [query, setQuery] = useState("");
  const [searchedQuery, setSearchedQuery] = useState("");
  const [category, setCategory] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const [questions, setQuestions] = useState({});
  const [answers, setAnswers] = useState({});
  const [askErrors, setAskErrors] = useState({});
  const [askingId, setAskingId] = useState(null);
  const [feedbackStates, setFeedbackStates] = useState({});

  async function searchProducts(event) {
    event.preventDefault();
    setError("");
    setResults([]);
    setFeedbackStates({});
    setHasSearched(true);
    setSearchedQuery(query.trim());
    setLoading(true);

    const body = {
      query: query.trim(),
      category: category || null,
      max_price: maxPrice ? Number(maxPrice) : null,
    };

    try {
      const response = await fetch(`${API_BASE}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Search request failed.");
      }

      setResults(data.results);
    } catch (err) {
      setError(
        `${err.message} Check that the backend is running at ${API_BASE}.`
      );
    } finally {
      setLoading(false);
    }
  }

  async function askAboutProduct(event, productId) {
    event.preventDefault();
    setAskErrors((current) => ({ ...current, [productId]: "" }));
    setAnswers((current) => ({ ...current, [productId]: "" }));

    const question = (questions[productId] || "").trim();
    if (!question) {
      setAskErrors((current) => ({
        ...current,
        [productId]: "Enter a question first.",
      }));
      return;
    }

    setAskingId(productId);

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId, question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Question request failed.");
      }

      setAnswers((current) => ({ ...current, [productId]: data.answer }));
    } catch (err) {
      setAskErrors((current) => ({
        ...current,
        [productId]: err.message,
      }));
    } finally {
      setAskingId(null);
    }
  }

  async function submitFeedback(productId, helpful) {
    setFeedbackStates((current) => ({
      ...current,
      [productId]: {
        loading: true,
        submitted: false,
        message: "",
        isError: false,
      },
    }));

    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: productId,
          query: searchedQuery,
          helpful,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Feedback submission failed.");
      }

      setFeedbackStates((current) => ({
        ...current,
        [productId]: {
          loading: false,
          submitted: true,
          message: "Thanks for your feedback.",
          isError: false,
        },
      }));
    } catch (err) {
      setFeedbackStates((current) => ({
        ...current,
        [productId]: {
          loading: false,
          submitted: false,
          message: err.message,
          isError: true,
        },
      }));
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <p className="eyebrow">AI SHOPPING ASSISTANT</p>
        <h1>Find a laptop that fits your needs.</h1>
        <p className="intro">
          Describe what you need. Recommendations follow your budget and use
          product details from the catalog.
        </p>
      </header>

      <section className="search-panel">
        <form onSubmit={searchProducts}>
          <label htmlFor="query">What are you looking for?</label>
          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Example: lightweight laptop for programming under 80000"
            required
            rows={3}
          />

          <div className="filters">
            <div>
              <label htmlFor="category">Category</label>
              <select
                id="category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                <option value="">Any category</option>
                <option value="laptop">Laptop</option>
              </select>
            </div>

            <div>
              <label htmlFor="maxPrice">Maximum price (₹)</label>
              <input
                id="maxPrice"
                type="number"
                min="0"
                value={maxPrice}
                onChange={(event) => setMaxPrice(event.target.value)}
                placeholder="e.g. 80000"
              />
            </div>
          </div>

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Searching…" : "Find recommendations"}
          </button>
        </form>
      </section>

      {error && <p className="error-message">{error}</p>}

      {!loading && results.length === 0 && !error && (
        <p className="empty-message">
          {hasSearched
            ? "No products matched your request. Try changing your search or budget."
            : "Enter a search above to see laptop recommendations."}
        </p>
      )}

      {results.length > 0 && (
        <section className="results-section">
          <div className="results-heading">
            <div>
              <p className="eyebrow">YOUR MATCHES</p>
              <h2>{results.length} recommendations</h2>
            </div>
          </div>

          <div className="product-list">
            {results.map(({ product, score, reasons }) => (
              <article className="product-card" key={product.id}>
                <div className="product-topline">
                  <div>
                    <p className="product-brand">{product.brand || "Laptop"}</p>
                    <h3>{product.title}</h3>
                  </div>
                  <p className="price">{formatPrice(product.price)}</p>
                </div>

                <p className="description">{product.description}</p>

                <div className="specs">
                  {product.processor && <span>{product.processor}</span>}
                  {product.ram_gb != null && (
                    <span>{product.ram_gb} GB RAM</span>
                  )}
                  {product.storage_gb != null && (
                    <span>{product.storage_gb} GB storage</span>
                  )}
                  {product.weight_kg != null && (
                    <span>{product.weight_kg} kg</span>
                  )}
                </div>

                <div className="match-row">
                  <span className="score">
                    Match score: {Number(score).toFixed(2)}
                  </span>
                </div>

                {reasons?.length > 0 && (
                  <ul className="reasons">
                    {reasons.map((reason, index) => (
                      <li key={`${product.id}-reason-${index}`}>{reason}</li>
                    ))}
                  </ul>
                )}

                <div className="feedback-controls">
                  <p>Was this recommendation helpful?</p>
                  <button
                    type="button"
                    disabled={
                      feedbackStates[product.id]?.loading ||
                      feedbackStates[product.id]?.submitted
                    }
                    onClick={() => submitFeedback(product.id, true)}
                  >
                    Helpful
                  </button>
                  <button
                    type="button"
                    disabled={
                      feedbackStates[product.id]?.loading ||
                      feedbackStates[product.id]?.submitted
                    }
                    onClick={() => submitFeedback(product.id, false)}
                  >
                    Not helpful
                  </button>

                  {feedbackStates[product.id]?.message && (
                    <p
                      className={
                        feedbackStates[product.id].isError
                          ? "error-message"
                          : "feedback-message"
                      }
                    >
                      {feedbackStates[product.id].message}
                    </p>
                  )}
                </div>

                <form
                  className="ask-form"
                  onSubmit={(event) => askAboutProduct(event, product.id)}
                >
                  <label htmlFor={`question-${product.id}`}>
                    Ask about this laptop
                  </label>
                  <div className="ask-row">
                    <input
                      id={`question-${product.id}`}
                      value={questions[product.id] || ""}
                      onChange={(event) =>
                        setQuestions((current) => ({
                          ...current,
                          [product.id]: event.target.value,
                        }))
                      }
                      placeholder="How much RAM does it have?"
                    />
                    <button
                      type="submit"
                      disabled={askingId === product.id}
                    >
                      {askingId === product.id ? "Asking…" : "Ask"}
                    </button>
                  </div>

                  {answers[product.id] && (
                    <p className="answer">{answers[product.id]}</p>
                  )}
                  {askErrors[product.id] && (
                    <p className="error-message">{askErrors[product.id]}</p>
                  )}
                </form>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}