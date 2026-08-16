import { useState } from "react";
import {
  Inbox,
  Mail,
  Plus,
  Search,
  Send,
  Trash2,
  X,
} from "lucide-react";
import { useAuth } from "../auth";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  Pagination,
} from "./ui";
import { apiFetch, jsonHeaders } from "../api";

const MESSAGES_URL = "/api/communication/messages/";

function roleLabel(role) {
  if (!role) return "";
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatSent(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function initials(name) {
  return (name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export default function MessagesPage() {
  const { user } = useAuth();
  const me = user ? user.id : null;

  const [box, setBox] = useState("inbox");
  const [rows, setRows] = useState(null);
  const [count, setCount] = useState(0);
  const [next, setNext] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [unread, setUnread] = useState(0);

  const [composing, setComposing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ subject: "", body: "" });
  const [recipient, setRecipient] = useState(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const [threadOpen, setThreadOpen] = useState(false);
  const [thread, setThread] = useState(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [replyBody, setReplyBody] = useState("");
  const [sending, setSending] = useState(false);

  const load = (targetBox = box, targetPage = 1) => {
    setLoading(true);
    setError("");

    const params = new URLSearchParams({
      box: targetBox,
      page: String(targetPage),
    });

    fetch(`${MESSAGES_URL}?${params.toString()}`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => {
        setRows(json.results || []);
        setCount(json.count || 0);
        setNext(json.next);
        setPrevious(json.previous);
        setPage(targetPage);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const loadUnread = () => {
    fetch(`${MESSAGES_URL}unread-count/`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { count: 0 }))
      .then((json) => setUnread(json.count || 0))
      .catch(() => {});
  };

  if (rows === null && !loading) {
    load();
    loadUnread();
  }

  const switchBox = (nextBox) => {
    if (nextBox === box) return;
    setBox(nextBox);
    setRows(null);
    setThreadOpen(false);
    setThread(null);
  };

  const searchRecipients = (value) => {
    setQuery(value);
    const term = value.trim();

    if (term.length < 2) {
      setResults([]);
      return;
    }

    setSearching(true);

    fetch(
      `${MESSAGES_URL}recipients/?q=${encodeURIComponent(term)}`,
      { credentials: "include" }
    )
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => setResults(json.results || []))
      .catch(() => setResults([]))
      .finally(() => setSearching(false));
  };

  const openCompose = () => {
    setComposing(true);
    setMessage("");
    setError("");
    setForm({ subject: "", body: "" });
    setRecipient(null);
    setQuery("");
    setResults([]);
  };

  const handleSend = async (event) => {
    event.preventDefault();

    if (!recipient) return;

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiFetch(
        MESSAGES_URL,
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify({
            recipient_id: recipient.id,
            subject: form.subject,
            body: form.body,
          }),
        },
        "Could not send the message."
      );

      setComposing(false);
      setMessage("Message sent.");
      setRows(null);
      load(box, 1);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const openThread = (item) => {
    setThreadOpen(true);
    setThreadLoading(true);
    setReplyBody("");

    fetch(`${MESSAGES_URL}${item.id}/thread/`, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : { results: [] }))
      .then((json) => {
        setThread(json.results || []);
        setThreadLoading(false);
        loadUnread();
        setRows(null);
        load(box, page);
      })
      .catch(() => {
        setThread([]);
        setThreadLoading(false);
      });
  };

  const closeThread = () => {
    setThreadOpen(false);
    setThread(null);
  };

  const handleReply = async (event) => {
    event.preventDefault();

    const root = thread && thread[0];
    if (!root || !replyBody.trim()) return;

    setSending(true);
    setError("");
    setMessage("");

    const other = root.sender && root.sender.id === me ? root.recipient : root.sender;

    try {
      await apiFetch(
        MESSAGES_URL,
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify({
            recipient: other ? other.id : null,
            subject: root.subject && root.subject.startsWith("Re:") ? root.subject : `Re: ${root.subject}`,
            body: replyBody,
            parent: root.id,
          }),
        },
        "Could not send the reply."
      );

      setReplyBody("");
      setMessage("Reply sent.");
      openThread(root);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm("Delete this message?")) return;

    try {
      await apiFetch(
        `${MESSAGES_URL}${item.id}/`,
        { method: "DELETE" },
        "Could not delete the message."
      );

      setMessage("Message deleted.");
      setThreadOpen(false);
      setThread(null);
      setRows(null);
      load(box, page);
      loadUnread();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Messages"
        title="Messages"
        subtitle="Send private messages to staff, teachers, students, and parents."
      />

      {message && (
        <div className="state-card success">
          <strong>{message}</strong>
        </div>
      )}

      <div className="filter-row">
        <div className="msg-tabs">
          <button
            type="button"
            className={`msg-tab${box === "inbox" ? " active" : ""}`}
            onClick={() => switchBox("inbox")}
          >
            <Inbox size={15} />
            Inbox
            {unread > 0 && <span className="msg-tab-count">{unread}</span>}
          </button>

          <button
            type="button"
            className={`msg-tab${box === "sent" ? " active" : ""}`}
            onClick={() => switchBox("sent")}
          >
            <Send size={15} />
            Sent
          </button>
        </div>

        <button type="button" className="primary-button" onClick={openCompose}>
          <Plus size={15} />
          New Message
        </button>
      </div>

      <div className="panel">
        <PanelHeader
          title={box === "inbox" ? "Inbox" : "Sent Messages"}
          subtitle="messages"
          count={count}
        />

        <StateArea loading={loading} error={error} onRetry={() => load(box, page)}>
          {!rows || rows.length === 0 ? (
            <EmptyState
              icon={Mail}
              title="No messages here"
              message={
                box === "inbox"
                  ? "Your inbox is empty. Compose a new message to get started."
                  : "You have not sent any messages yet."
              }
            />
          ) : (
            <>
              <div className="msg-list">
                {rows.map((item) => {
                  const isSent = item.direction === "sent";
                  const participant = isSent ? item.recipient : item.sender;
                  const unreadRow = !isSent && !item.is_read;

                  return (
                    <div
                      key={item.id}
                      className={`msg-row${unreadRow ? " unread" : ""}`}
                      onClick={() => openThread(item)}
                    >
                      <div className="msg-avatar">
                        {participant && participant.photo_url ? (
                          <img src={participant.photo_url} alt="" />
                        ) : (
                          <span>{initials(participant && participant.name)}</span>
                        )}
                      </div>

                      <div className="msg-main">
                        <div className="msg-top">
                          <strong>{participant ? participant.name : "Unknown"}</strong>
                          <span className="msg-time">{formatSent(item.sent_at)}</span>
                        </div>

                        <div className="msg-subject">
                          {unreadRow && <span className="msg-dot" />}
                          {item.subject}
                        </div>

                        <div className="msg-snippet">{item.body}</div>
                      </div>

                      <button
                        type="button"
                        className="msg-delete"
                        title="Delete message"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleDelete(item);
                        }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  );
                })}
              </div>

              <Pagination
                count={count}
                page={page}
                next={next}
                previous={previous}
                onPage={(targetPage) => load(box, targetPage)}
              />
            </>
          )}
        </StateArea>
      </div>

      {composing && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setComposing(false);
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <h3>New Message</h3>

              <button
                type="button"
                className="modal-close"
                onClick={() => setComposing(false)}
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSend}>
              <div className="modal-body">
                <label>
                  To
                  <div className="recipient-search">
                    <Search size={14} />
                    <input
                      type="text"
                      value={query}
                      onChange={(event) => searchRecipients(event.target.value)}
                      placeholder="Search staff, teachers, students..."
                    />
                  </div>

                  {recipient && (
                    <div className="recipient-chip">
                      {recipient.name}
                      <button
                        type="button"
                        onClick={() => {
                          setRecipient(null);
                          setQuery("");
                          setResults([]);
                        }}
                      >
                        <X size={12} />
                      </button>
                    </div>
                  )}

                  {!recipient && results.length > 0 && (
                    <div className="recipient-results">
                      {results.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => {
                            setRecipient(item);
                            setQuery("");
                            setResults([]);
                          }}
                        >
                          <span>{item.name}</span>
                          <span className="recipient-role">{roleLabel(item.role)}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {searching && <span className="field-hint">Searching...</span>}
                </label>

                <label>
                  Subject
                  <input
                    type="text"
                    required
                    value={form.subject}
                    onChange={(event) =>
                      setForm({ ...form, subject: event.target.value })
                    }
                    placeholder="Message subject"
                  />
                </label>

                <label>
                  Message
                  <textarea
                    required
                    rows={6}
                    value={form.body}
                    onChange={(event) =>
                      setForm({ ...form, body: event.target.value })
                    }
                    placeholder="Write your message..."
                  />
                </label>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setComposing(false)}
                >
                  <X size={15} />
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving || !recipient}
                >
                  <Send size={15} />
                  {saving ? "Sending..." : "Send Message"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {threadOpen && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeThread();
          }}
        >
          <div className="modal large">
            <div className="modal-header">
              <h3>{thread && thread[0] ? thread[0].subject : "Conversation"}</h3>

              <button type="button" className="modal-close" onClick={closeThread}>
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              {threadLoading ? (
                <div className="state-card">Loading conversation...</div>
              ) : (
                thread &&
                thread.length > 0 && (
                  <>
                    <div className="thread-list">
                      {thread.map((item) => {
                        const mine =
                          item.sender && me && item.sender.id === me;

                        return (
                          <div
                            key={item.id}
                            className={`thread-bubble${mine ? " out" : " in"}`}
                          >
                            <div className="thread-bubble-meta">
                              <strong>
                                {mine ? "You" : item.sender ? item.sender.name : "Unknown"}
                              </strong>
                              <span>{formatSent(item.sent_at)}</span>
                            </div>

                            <p>{item.body}</p>
                          </div>
                        );
                      })}
                    </div>

                    <form onSubmit={handleReply} className="thread-reply">
                      <textarea
                        required
                        rows={3}
                        value={replyBody}
                        onChange={(event) => setReplyBody(event.target.value)}
                        placeholder="Write a reply..."
                      />

                      <div className="thread-reply-actions">
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => handleDelete(thread[0])}
                        >
                          <Trash2 size={15} />
                          Delete
                        </button>

                        <button
                          type="submit"
                          className="primary-button"
                          disabled={sending || !replyBody.trim()}
                        >
                          <Send size={15} />
                          {sending ? "Sending..." : "Reply"}
                        </button>
                      </div>
                    </form>
                  </>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
