import { useState } from "react";
import { BookMarked, Search, BookCopy, RotateCcw } from "lucide-react";
import { PageHeader, PanelHeader, StateArea, EmptyState } from "./ui";
import { formatDate, formatCurrency } from "./format";
import { apiFetch, jsonHeaders } from "../api";

const BOOKS_URL = "/api/library/books/";
const ISSUES_URL = "/api/library/issues/";

export default function LibraryPage() {
  const [tab, setTab] = useState("books");
  const [books, setBooks] = useState(null);
  const [issues, setIssues] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState("");
  const [returning, setReturning] = useState(null);

  const loadBooks = () => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();

    if (search.trim()) {
      params.append("q", search.trim());
    }

    if (category) {
      params.append("category", category);
    }

    fetch(`${BOOKS_URL}?${params.toString()}`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((data) => {
        setBooks(data.results || data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const loadIssues = () => {
    setLoading(true);
    setError("");

    fetch(ISSUES_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((data) => {
        setIssues(data.results || data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const switchTab = (next) => {
    setTab(next);
    setMessage("");

    if (next === "books" && books === null) {
      loadBooks();
    } else if (next === "issues" && issues === null) {
      loadIssues();
    }
  };

  const handleReturn = async (issueId) => {
    setReturning(issueId);
    setMessage("");

    try {
      await apiFetch(
        `${ISSUES_URL}${issueId}/return/`,
        { method: "POST", headers: jsonHeaders() },
        "Could not return the book."
      );

      setMessage("Book returned successfully.");
      setIssues(null);
      loadIssues();
    } catch (err) {
      setError(err.message);
    } finally {
      setReturning(null);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Library"
        title="Library"
        subtitle="Manage the school library catalog and book issues."
      />

      {message && (
        <div className="state-card success">
          <strong>{message}</strong>
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab-button ${tab === "books" ? "active" : ""}`}
          onClick={() => switchTab("books")}
        >
          Books
        </button>

        <button
          className={`tab-button ${tab === "issues" ? "active" : ""}`}
          onClick={() => switchTab("issues")}
        >
          Issues
        </button>
      </div>

      {tab === "books" && (
        <div className="panel">
          <PanelHeader
            title="Book Catalog"
            subtitle="books found"
            count={books ? books.length : null}
          />

          <div className="filter-row">
            <div className="filter-search">
              <Search size={18} />

              <input
                type="text"
                placeholder="Search by title, author, or ISBN..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="">All categories</option>
              <option value="fiction">Fiction</option>
              <option value="non_fiction">Non-Fiction</option>
              <option value="textbook">Textbook</option>
              <option value="reference">Reference</option>
              <option value="science">Science</option>
              <option value="math">Mathematics</option>
              <option value="literature">Literature</option>
              <option value="history">History</option>
              <option value="geography">Geography</option>
              <option value="other">Other</option>
            </select>

            <button type="button" className="primary-button" onClick={loadBooks}>
              Search
            </button>
          </div>

          <StateArea loading={loading} error={error} onRetry={loadBooks}>
            {!books || books.length === 0 ? (
              <EmptyState
                icon={BookMarked}
                title="No books found"
                message="Add books in the admin panel or adjust your filters."
              />
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>TITLE</th>
                      <th>AUTHOR</th>
                      <th>ISBN</th>
                      <th>CATEGORY</th>
                      <th>COPIES</th>
                      <th>AVAILABLE</th>
                      <th>ISSUED</th>
                    </tr>
                  </thead>

                  <tbody>
                    {books.map((book) => (
                      <tr key={book.id}>
                        <td>
                          <strong>{book.title}</strong>
                        </td>

                        <td>{book.author || "—"}</td>

                        <td>{book.isbn || "—"}</td>

                        <td>{book.category_display || "—"}</td>

                        <td>{book.total_copies ?? 0}</td>

                        <td>
                          <span className="status-badge active">
                            {book.available_copies ?? 0}
                          </span>
                        </td>

                        <td>{book.issued_copies ?? 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </StateArea>
        </div>
      )}

      {tab === "issues" && (
        <div className="panel">
          <PanelHeader
            title="Book Issues"
            subtitle="issue records"
            count={issues ? issues.length : null}
          />

          <StateArea loading={loading} error={error} onRetry={loadIssues}>
            {!issues || issues.length === 0 ? (
              <EmptyState
                icon={BookCopy}
                title="No issues recorded"
                message="Issue records will appear here once books are lent out."
              />
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>BOOK</th>
                      <th>BARCODE</th>
                      <th>BORROWER</th>
                      <th>ISSUE DATE</th>
                      <th>DUE DATE</th>
                      <th>RETURN DATE</th>
                      <th>FINE</th>
                      <th>STATUS</th>
                      <th>ACTION</th>
                    </tr>
                  </thead>

                  <tbody>
                    {issues.map((issue) => (
                      <tr key={issue.id}>
                        <td>
                          <strong>{issue.book_title}</strong>
                        </td>

                        <td>{issue.barcode || "—"}</td>

                        <td>{issue.borrower || "—"}</td>

                        <td>{formatDate(issue.issue_date)}</td>

                        <td>{formatDate(issue.due_date)}</td>

                        <td>{formatDate(issue.return_date)}</td>

                        <td>{formatCurrency(issue.fine)}</td>

                        <td>
                          <span className={`status-badge ${issue.status === "returned" ? "inactive" : "warn"}`}>
                            {issue.status ? issue.status.charAt(0).toUpperCase() + issue.status.slice(1) : "—"}
                          </span>
                        </td>

                        <td>
                          {issue.status !== "returned" ? (
                            <button
                              type="button"
                              className="table-action"
                              disabled={returning === issue.id}
                              onClick={() => handleReturn(issue.id)}
                            >
                              <RotateCcw size={14} />
                              {returning === issue.id ? "Returning..." : "Return"}
                            </button>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </StateArea>
        </div>
      )}
    </section>
  );
}
