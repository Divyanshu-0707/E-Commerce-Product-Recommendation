import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const ATTRIBUTE_FORMATS = {
  ram_gb: { label: "RAM", unit: "GB" },
  storage_gb: { label: "Storage", unit: "GB" },
  screen_inches: { label: "Display", unit: "in" },
  battery_mah: { label: "Battery", unit: "mAh" },
  battery_hours: { label: "Battery Life", unit: "hours" },
  weight_kg: { label: "Weight", unit: "kg" },
  weight_g: { label: "Weight", unit: "g" },
  volume_ml: { label: "Volume", unit: "ml" },
  capacity_l: { label: "Capacity", unit: "L" },
  width_cm: { label: "Width", unit: "cm" },
  height_cm: { label: "Height", unit: "cm" },
  play_time_minutes: { label: "Play Time", unit: "min" },
};

function formatPrice(price, currency = "INR") {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 0,
    }).format(price);
  } catch {
    return `${currency || "INR"} ${new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 0,
    }).format(price)}`;
  }
}

function formatAttributeLabel(value) {
  const format = ATTRIBUTE_FORMATS[String(value).toLowerCase()];
  if (format) return format.label;
  return String(value)
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatAttributeValue(value, name = "") {
  if (value == null) return "Not available";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    const number = new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 10,
    }).format(value);
    const unit = ATTRIBUTE_FORMATS[name.toLowerCase()]?.unit;
    return unit ? `${number} ${unit}` : number;
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function getAttributeValue(product, name) {
  const entry = Object.entries(product.attributes || {}).find(
    ([key]) => key.toLocaleLowerCase() === name.toLocaleLowerCase(),
  );
  return entry?.[1];
}

export default function App() {
  const [query, setQuery] = useState("");
  const [searchedQuery, setSearchedQuery] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [catalogInfo, setCatalogInfo] = useState(null);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [results, setResults] = useState([]);
  const [sortOrder, setSortOrder] = useState("recommended");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [noResultsMessage, setNoResultsMessage] = useState("");

  const [questions, setQuestions] = useState({});
  const [answers, setAnswers] = useState({});
  const [askErrors, setAskErrors] = useState({});
  const [askingId, setAskingId] = useState(null);
  const [feedbackStates, setFeedbackStates] = useState({});
  const [selectedForCompare, setSelectedForCompare] = useState([]);

  const [agentMessage, setAgentMessage] = useState("");
  const [agentAnswer, setAgentAnswer] = useState("");
  const [agentError, setAgentError] = useState("");
  const [agentLoading, setAgentLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCategories() {
      try {
        const response = await fetch(`${API_BASE}/categories`, {
          signal: controller.signal,
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Could not load product categories.");
        }
        setCategories(data.categories || []);
      } catch (err) {
        if (err.name !== "AbortError") {
          setCategoriesError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) setCategoriesLoading(false);
      }
    }

    async function loadCatalogInfo() {
      try {
        const response = await fetch(`${API_BASE}/catalog-info`, {
          signal: controller.signal,
        });
        if (response.ok) setCatalogInfo(await response.json());
      } catch {
        // A missing demo banner should not block search.
      }
    }

    loadCategories();
    loadCatalogInfo();
    return () => controller.abort();
  }, []);

  const sortedResults = [...results];
  if (sortOrder === "price-asc") {
    sortedResults.sort(
      (left, right) => left.product.price - right.product.price,
    );
  } else if (sortOrder === "price-desc") {
    sortedResults.sort(
      (left, right) => right.product.price - left.product.price,
    );
  }

  const comparisonAttributes = new Set();
  for (const product of selectedForCompare) {
    for (const name of Object.keys(product.attributes || {})) {
      comparisonAttributes.add(name);
    }
  }

  const comparisonRows = [
    {
      label: "Category",
      getValue: (product) => formatAttributeValue(product.category),
    },
    {
      label: "Brand",
      getValue: (product) => formatAttributeValue(product.brand),
    },
    {
      label: "Price",
      getValue: (product) => formatPrice(product.price, product.currency),
    },
  ];

  const sortedAttributes = [...comparisonAttributes].sort((left, right) =>
    left.localeCompare(right),
  );
  for (const name of sortedAttributes) {
    comparisonRows.push({
      key: name,
      label: formatAttributeLabel(name),
      getValue: (product) =>
        formatAttributeValue(getAttributeValue(product, name), name),
    });
  }

  async function searchProducts(event) {
    event.preventDefault();
    setError("");
    setResults([]);
    setNoResultsMessage("");
    setFeedbackStates({});
    setSelectedForCompare([]);
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
      setNoResultsMessage(data.message || "");
    } catch (err) {
      setError(
        `${err.message} Check that the backend is running at ${API_BASE}.`,
      );
    } finally {
      setLoading(false);
    }
  }

  async function sendToAgent(event) {
    event.preventDefault();

    const message = agentMessage.trim();
    if (!message) return;

    setAgentError("");
    setAgentAnswer("");
    setAgentLoading(true);

    try {
      const response = await fetch(`${API_BASE}/assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Assistant request failed.");
      }

      setAgentAnswer(data.answer);
    } catch (err) {
      setAgentError(
        err instanceof TypeError
          ? `${err.message} Check that the backend is running at ${API_BASE}.`
          : err.message,
      );
    } finally {
      setAgentLoading(false);
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

  function toggleCompare(product) {
    const alreadySelected = selectedForCompare.some(
      (item) => item.id === product.id,
    );

    if (alreadySelected) {
      setSelectedForCompare((current) =>
        current.filter((item) => item.id !== product.id),
      );
      return;
    }

    if (selectedForCompare.length < 2) {
      setSelectedForCompare((current) => [...current, product]);
    }
  }

  function explainComparison() {
    const productNames = selectedForCompare
      .map((product) => `${product.title} (ID: ${product.id})`)
      .join(" and ");
    setAgentMessage(
      `Compare ${productNames}. Explain the differences and trade-offs using their catalog attributes. State any missing information.`,
    );
    document.getElementById("agentMessage").focus();
  }

  return (
    <main className="page">
      <div className="app-bar">
        <span className="app-brand">
          AI Shopping Assistant
          <span className="brand-dot" aria-hidden="true" />
        </span>
        <span className="app-context">Your catalog workspace</span>
      </div>
      <header className="hero">
        <p className="eyebrow">LESS SEARCHING. BETTER CHOICES.</p>
        <h1>Find products that fit your needs.</h1>
        <p className="intro">
          Describe what you need. Recommendations follow your budget and use
          product details from the catalog.
        </p>
        {catalogInfo?.synthetic && (
          <p className="demo-notice" role="note">
            Demo catalog: {catalogInfo.product_count} fictional products across{" "}
            {catalogInfo.category_count} categories. Prices and product details
            are synthetic and for demonstration only.
          </p>
        )}
      </header>

      <div className="shopping-layout">
        <section
          className="search-panel catalog-panel"
          aria-labelledby="catalog-title"
        >
          <p className="section-kicker">CATALOG SEARCH</p>
          <h2 id="catalog-title">Find matching products.</h2>
          <p className="panel-description">
            Search the catalog, filter by category and budget, then browse and
            sort the matching products.
          </p>
          <form onSubmit={searchProducts} aria-busy={loading}>
            <label htmlFor="query">What are you looking for?</label>
            <textarea
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: a lightweight laptop for programming, or a waterproof phone"
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
                  disabled={categoriesLoading}
                >
                  <option value="">Any category</option>
                  {categories.map((item) => (
                    <option value={item} key={item}>
                      {formatAttributeLabel(item)}
                    </option>
                  ))}
                </select>
                {categoriesError && (
                  <p className="error-message">{categoriesError}</p>
                )}
              </div>

              <div>
                <label className="budget-label" htmlFor="maxPrice">
                  Budget (INR) <span className="optional-label">Optional</span>
                </label>
                <input
                  id="maxPrice"
                  type="number"
                  min="0"
                  step="any"
                  aria-describedby="budget-hint"
                  value={maxPrice}
                  onChange={(event) => setMaxPrice(event.target.value)}
                  placeholder="No limit"
                />
                <p className="field-hint budget-hint" id="budget-hint">
                  Leave blank for no price cap. Set your maximum here to apply a
                  budget.
                </p>
              </div>
            </div>

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Searching…" : "Find recommendations"}
            </button>
          </form>
        </section>

        <div className="results-area" aria-busy={loading}>
          {error && <p className="error-message">{error}</p>}

          {loading && (
            <div className="empty-state" role="status">
              <h2>Finding your matches…</h2>
              <p>Checking the catalog for products that fit.</p>
            </div>
          )}

          {hasSearched && !loading && results.length === 0 && !error && (
            <div className="empty-state">
              <h2>No matching products.</h2>
              <p className="empty-message">
                {noResultsMessage ||
                  "No products matched your request. Try changing your search or budget."}
              </p>
            </div>
          )}

          {results.length > 0 && (
            <section className="results-section">
              <div className="results-heading">
                <div>
                  <p className="eyebrow">YOUR MATCHES</p>
                  <h2>{results.length} recommendations</h2>
                </div>
                <div className="sort-control">
                  <label htmlFor="sortOrder">Sort recommendations</label>
                  <select
                    id="sortOrder"
                    value={sortOrder}
                    onChange={(event) => setSortOrder(event.target.value)}
                  >
                    <option value="recommended">Best match</option>
                    <option value="price-asc">Price: low to high</option>
                    <option value="price-desc">Price: high to low</option>
                  </select>
                </div>
              </div>

              {selectedForCompare.length > 0 && (
                <section className="compare-panel">
                  <div className="compare-heading">
                    <h3>Compare selected products</h3>
                    <button
                      className="compare-clear-button"
                      type="button"
                      onClick={() => setSelectedForCompare([])}
                    >
                      Clear comparison
                    </button>
                  </div>

                  <p className="compare-prompt">
                    {selectedForCompare.length === 1
                      ? "Select one more product to compare side by side."
                      : "Comparing 2 products."}
                  </p>

                  {selectedForCompare.length === 2 && (
                    <button
                      className="comparison-explain"
                      type="button"
                      onClick={explainComparison}
                    >
                      Explain this comparison with AI
                    </button>
                  )}

                  <div className="compare-table-wrapper">
                    <table className="compare-table">
                      <thead>
                        <tr>
                          <th scope="col">Field</th>
                          {selectedForCompare.map((product) => (
                            <th scope="col" key={product.id}>
                              {product.title}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonRows.map(({ key, label, getValue }) => (
                          <tr key={key || label}>
                            <th scope="row">{label}</th>
                            {selectedForCompare.map((product) => (
                              <td key={`${product.id}-${label}`}>
                                {getValue(product)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              <div className="product-list">
                {sortedResults.map(({ product, score, reasons }) => {
                  const feedback = feedbackStates[product.id];
                  const isSelected = selectedForCompare.some(
                    (item) => item.id === product.id,
                  );

                  return (
                    <article className="product-card" key={product.id}>
                      <div className="product-topline">
                        <div>
                          <p className="product-brand">
                            {formatAttributeLabel(product.category)}
                            {product.brand ? ` · ${product.brand}` : ""}
                          </p>
                          <h3>{product.title}</h3>
                        </div>
                        <p className="price">
                          {formatPrice(product.price, product.currency)}
                        </p>
                      </div>

                      <p className="description">{product.description}</p>

                      <div className="specs">
                        {Object.entries(product.attributes || {})
                          .filter(([, value]) => value != null && value !== "")
                          .map(([name, value]) => (
                            <span key={`${product.id}-${name}`}>
                              {formatAttributeLabel(name)}:{" "}
                              <strong>
                                {formatAttributeValue(value, name)}
                              </strong>
                            </span>
                          ))}
                      </div>

                      <div className="match-row">
                        <span className="score">
                          Match score: {Number(score).toFixed(2)}
                        </span>
                      </div>

                      <label className="compare-option">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          disabled={
                            !isSelected && selectedForCompare.length >= 2
                          }
                          onChange={() => toggleCompare(product)}
                        />
                        Compare this product
                      </label>

                      {reasons?.length > 0 && (
                        <ul className="reasons">
                          {reasons.map((reason, index) => (
                            <li key={`${product.id}-reason-${index}`}>
                              {reason}
                            </li>
                          ))}
                        </ul>
                      )}

                      <div className="feedback-controls">
                        <p>Was this recommendation helpful?</p>
                        <button
                          type="button"
                          disabled={feedback?.loading || feedback?.submitted}
                          onClick={() => submitFeedback(product.id, true)}
                        >
                          Helpful
                        </button>
                        <button
                          type="button"
                          disabled={feedback?.loading || feedback?.submitted}
                          onClick={() => submitFeedback(product.id, false)}
                        >
                          Not helpful
                        </button>

                        {feedback?.message && (
                          <p
                            className={
                              feedback.isError
                                ? "error-message"
                                : "feedback-message"
                            }
                          >
                            {feedback.message}
                          </p>
                        )}
                      </div>

                      <form
                        className="ask-form"
                        onSubmit={(event) => askAboutProduct(event, product.id)}
                      >
                        <label htmlFor={`question-${product.id}`}>
                          Ask about this product
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
                            placeholder="Ask about a product detail"
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
                          <p className="error-message">
                            {askErrors[product.id]}
                          </p>
                        )}
                      </form>
                    </article>
                  );
                })}
              </div>
            </section>
          )}
        </div>

        <section
          className="search-panel assistant-panel"
          aria-labelledby="assistant-title"
        >
          <p className="section-kicker">AI ASSISTANT</p>
          <h2 id="assistant-title">Need help deciding?</h2>
          <p className="panel-description">
            Unsure which product fits? Ask the AI assistant to compare your
            options, explain the trade-offs, or check a detail in the catalog.
          </p>
          <ul className="assistant-purpose">
            <li>
              <strong>Compare options</strong>
              <span>
                Get a written breakdown of differences between products.
              </span>
            </li>
            <li>
              <strong>Explain the fit</strong>
              <span>
                See how stored specifications relate to what you need.
              </span>
            </li>
            <li>
              <strong>Check a detail</strong>
              <span>
                Ask about a product. Missing catalog facts stay unknown.
              </span>
            </li>
          </ul>

          <form onSubmit={sendToAgent} aria-busy={agentLoading}>
            <label htmlFor="agentMessage">What would help you decide?</label>
            <textarea
              id="agentMessage"
              value={agentMessage}
              onChange={(event) => setAgentMessage(event.target.value)}
              placeholder="Example: Compare [product A] and [product B] for programming. Explain their RAM, storage and weight differences."
              rows={3}
              required
            />

            <button
              className="primary-button"
              type="submit"
              disabled={agentLoading}
            >
              {agentLoading ? "Assistant is working…" : "Ask assistant"}
            </button>
            <p className="field-hint">
              AI answers can make mistakes. Check the catalog details.
            </p>
          </form>

          {agentAnswer && (
            <div className="agent-response" aria-live="polite">
              <h3>Assistant response</h3>
              <div className="answer agent-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
                  {agentAnswer}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {agentError && <p className="error-message">{agentError}</p>}
        </section>
      </div>
    </main>
  );
}
