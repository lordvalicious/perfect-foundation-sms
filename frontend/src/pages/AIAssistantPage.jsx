import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Bot,
  Plus,
  Send,
  Trash2,
  Sparkles,
  Building2,
  MapPin,
  ShieldCheck,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import { PageHeader, EmptyState, SkeletonBlock } from "./ui";
import { formatDate } from "./format";
import { useSchool } from "../schoolContext";
import { useToast } from "../toast";
import {
  getAssistantStatus,
  listConversations,
  createConversation,
  getConversation,
  sendMessage,
  deleteConversation,
  executeAction,
} from "../assistantApi";

const SUGGESTIONS = [
  "What can you help me with?",
  "Give me a quick summary of the active school.",
  "What needs my attention right now?",
];

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function riskLabel(risk) {
  if (risk === "high") return "High impact";
  if (risk === "medium") return "Medium impact";
  return "Low impact";
}

function MessageBubble({ message }) {
  const mine = message.role === "user";

  return (
    <div className={`assistant-bubble ${mine ? "out" : "in"}`}>
      {!mine && (
        <div className="assistant-bubble-meta">
          <Bot size={13} />
          <strong>Assistant</strong>
          <span>{formatTime(message.createdAt)}</span>
        </div>
      )}
      {mine && (
        <div className="assistant-bubble-meta">
          <span>You</span>
          <span>{formatTime(message.createdAt)}</span>
        </div>
      )}
      <p>{message.content}</p>

      {!mine && message.sources.length > 0 && (
        <div className="assistant-sources">
          <span className="assistant-sources-label">
            <ShieldCheck size={12} /> Sources
          </span>
          {message.sources.map((source, i) => (
            <span className="status-badge info" key={`${source}-${i}`}>
              {source}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ActionCard({ action, executing, onConfirm, onCancel }) {
  return (
    <div className={`assistant-action-card risk-${action.risk || "low"}`}>
      <div className="assistant-action-head">
        <span className="assistant-action-badge">{riskLabel(action.risk)}</span>
        <button
          type="button"
          className="assistant-action-cancel"
          onClick={onCancel}
          title="Dismiss action"
          aria-label="Dismiss proposed action"
          disabled={executing}
        >
          ×
        </button>
      </div>
      <strong>{action.label}</strong>
      {action.description && <p>{action.description}</p>}
      <button
        type="button"
        className="primary-button assistant-action-confirm"
        onClick={onConfirm}
        disabled={executing}
      >
        <ShieldCheck size={14} />
        {executing ? "Confirming…" : "Confirm action"}
      </button>
      <p className="assistant-action-note">
        Nothing runs until you confirm, and the system applies your existing
        permissions.
      </p>
    </div>
  );
}

export default function AIAssistantPage() {
  const toast = useToast();
  const { currentSchool, activeCampus, campusList, schoolScopeVersion } =
    useSchool();

  const [status, setStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusReloadKey, setStatusReloadKey] = useState(0);

  const [conversations, setConversations] = useState([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [conversationsError, setConversationsError] = useState("");

  const [activeId, setActiveId] = useState(null);
  const [activeTitle, setActiveTitle] = useState("New conversation");
  const [messages, setMessages] = useState([]);
  const [convLoading, setConvLoading] = useState(false);
  const [convError, setConvError] = useState("");

  const [input, setInput] = useState("");
  const [pendingText, setPendingText] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [executingIds, setExecutingIds] = useState(() => new Set());
  const [deletePending, setDeletePending] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const tmpIdRef = useRef(0);
  const sendingRef = useRef(false);
  const threadForRef = useRef(null);
  const bottomRef = useRef(null);

  const schoolId = currentSchool?.id != null ? currentSchool.id : null;
  const campusId = activeCampus?.id != null ? activeCampus.id : null;
  const scopeKey = `${currentSchool?.id ?? "none"}-${activeCampus?.id ?? "all"}`;

  const loadStatus = useCallback(() => {
    setStatusLoading(true);
    getAssistantStatus()
      .then((next) => {
        setStatus(next);
        setStatusLoading(false);
      })
      .finally(() => setStatusLoading(false));
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus, statusReloadKey]);

  const loadConversations = useCallback(async () => {
    if (!status?.available) return;
    setConversationsLoading(true);
    setConversationsError("");
    try {
      const list = await listConversations();
      setConversations(list);
    } catch (err) {
      setConversationsError(err.message);
    } finally {
      setConversationsLoading(false);
    }
  }, [status]);

  // Reset + reload with every school/campus scope change so conversation
  // history is never carried across institutions or campuses.
  useEffect(() => {
    setActiveId(null);
    setActiveTitle("New conversation");
    setMessages([]);
    setConvError("");
    setSendError("");
    setConversations([]);
    setDeletePending(null);
    loadConversations();
  }, [loadConversations, schoolScopeVersion, scopeKey]);

  const loadMessages = useCallback(
    async (id) => {
      if (!id) return;
      setConvLoading(true);
      setConvError("");
      try {
        const conversation = await getConversation(id, schoolId, campusId);
        setActiveTitle(conversation.title);
        setMessages(conversation.messages);
      } catch (err) {
        setConvError(err.message);
      } finally {
        setConvLoading(false);
      }
    },
    [schoolId, campusId]
  );

  useEffect(() => {
    if (activeId) {
      loadMessages(activeId);
    }
  }, [activeId, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  const selectConversation = useCallback((id) => {
    setDeletePending(null);
    setSidebarOpen(false);
    if (id !== activeId) {
      setActiveId(id);
    }
  }, [activeId]);

  const startNewChat = useCallback(async () => {
    setDeletePending(null);
    setInput("");
    setSendError("");
    if (!activeId) {
      setSidebarOpen(false);
      setActiveTitle("New conversation");
      setMessages([]);
      return;
    }
    // Create eagerly so an empty thread has a persistable home.
    setSending(true);
    try {
      const conversation = await createConversation();
      setConversations((current) => [conversation, ...current]);
      setActiveId(conversation.id);
      setActiveTitle(conversation.title || "New conversation");
      setMessages([]);
      setSidebarOpen(false);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSending(false);
    }
  }, [activeId, toast]);

  const handleDeleteConversation = useCallback(
    async (id) => {
      try {
        await deleteConversation(id);
        setConversations((current) =>
          current.filter((c) => c.id !== id)
        );
        if (activeId === id) {
          setActiveId(null);
          setActiveTitle("New conversation");
          setMessages([]);
        }
        setDeletePending(null);
        toast.info("Conversation deleted.");
      } catch (err) {
        toast.error(err.message);
      }
    },
    [activeId, toast]
  );

  const runAction = useCallback(
    async (messageId, action) => {
      const id = action.id;
      setExecutingIds((prev) => new Set(prev).add(id));
      try {
        const result = await executeAction({
          action,
          schoolId,
          campusId,
        });
        toast.success(result.detail);
        setMessages((current) =>
          current.map((m) =>
            m.id === messageId
              ? { ...m, actions: m.actions.filter((a) => a.id !== id) }
              : m
          )
        );
      } catch (err) {
        toast.error(err.message);
      } finally {
        setExecutingIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }
    },
    [schoolId, campusId, toast]
  );

  const dismissAction = useCallback((messageId, actionId) => {
    setMessages((current) =>
      current.map((m) =>
        m.id === messageId
          ? { ...m, actions: m.actions.filter((a) => a.id !== actionId) }
          : m
      )
    );
  }, []);

  const send = useCallback(
    async (rawText) => {
      const text = (rawText || "").trim();
      if (!text || sendingRef.current || !status?.available) return;

      sendingRef.current = true;
      setSending(true);
      setSendError("");
      setPendingText("");

      const tmpId = `tmp-${++tmpIdRef.current}`;
      const createdAt = new Date().toISOString();
      setMessages((current) => [
        ...current,
        {
          id: tmpId,
          role: "user",
          content: text,
          createdAt,
          sources: [],
          actions: [],
        },
      ]);
      setInput("");

      let convId = activeId ? activeId : null;
      try {
        if (!convId) {
          const conversation = await createConversation();
          convId = conversation.id;
          setActiveId(convId);
          setActiveTitle(conversation.title || "New conversation");
          setConversations((current) => [conversation, ...current]);
        }

        // Remember which thread this send belongs to so a late response can
        // never bleed into a different conversation the user switched to.
        threadForRef.current = convId;

        const reply = await sendMessage(convId, {
          message: text,
          schoolId,
          campusId,
        });

        if (threadForRef.current === convId) {
          setMessages((current) => [
            ...current,
            { ...reply, id: reply.id || `assistant-${Date.now()}` },
          ]);
        }
      } catch (err) {
        threadForRef.current = null;
        setMessages((current) =>
          current.filter((m) => m.id !== tmpId)
        );
        setInput(text);
        setPendingText(text);
        setSendError(err.message);
      } finally {
        threadForRef.current = null;
        sendingRef.current = false;
        setSending(false);
      }
    },
    [activeId, schoolId, campusId, status]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send(input);
      }
    },
    [input, send]
  );

  const retrySend = useCallback(() => {
    if (pendingText) send(pendingText);
  }, [pendingText, send]);

  const scopeInfo = useMemo(() => {
    return {
      school: currentSchool?.name || "—",
      campus: activeCampus?.name || (campusList.length > 1 ? "All campuses" : currentSchool?.name || "—"),
    };
  }, [currentSchool, activeCampus, campusList]);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / AI Assistant"
        title="AI Assistant"
        subtitle="Ask questions about your school in plain language. Answers respect your role and the active school."
        action={
          status?.available ? (
            <button
              type="button"
              className="secondary-button"
              onClick={() => setStatusReloadKey((k) => k + 1)}
            >
              <RefreshCw size={14} /> Check status
            </button>
          ) : null
        }
      />

      {statusLoading ? (
        <SkeletonBlock rows={5} text="Checking assistant availability..." />
      ) : !status?.available ? (
        <div className="state-card">
          <Sparkles size={30} strokeWidth={1.5} />
          <strong>AI assistant unavailable</strong>
          <span>
            {status?.message ||
              "The AI assistant is not enabled for this deployment yet."}
          </span>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setStatusReloadKey((k) => k + 1)}
          >
            Try Again
          </button>
        </div>
      ) : (
        <div className="assistant-layout">
          {/* Context banner: the assistant only ever sees the active scope. */}
          <div className="assistant-context-bar">
            <span className="assistant-context-badge">
              <Building2 size={13} />
              {scopeInfo.school}
            </span>
            <span className="assistant-context-badge">
              <MapPin size={13} />
              {scopeInfo.campus}
            </span>
            <span className="assistant-context-note">
              <ShieldCheck size={13} />
              Scoped to your role in the active school.
            </span>
          </div>

          <div className="assistant-body">
            <aside
              className={`assistant-sidebar ${
                sidebarOpen ? "open" : ""
              }`.trim()}
            >
              <button
                type="button"
                className="primary-button assistant-new-chat"
                onClick={startNewChat}
                disabled={sending}
              >
                <Plus size={15} /> New conversation
              </button>

              {conversationsLoading ? (
                <div className="assistant-sidebar-loading">Loading…</div>
              ) : conversationsError ? (
                <div className="state-card error">
                  <span>{conversationsError}</span>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={loadConversations}
                  >
                    Try Again
                  </button>
                </div>
              ) : conversations.length === 0 ? (
                <div className="assistant-sidebar-empty">
                  <MessageSquare size={20} strokeWidth={1.5} />
                  <span>No conversations yet.</span>
                </div>
              ) : (
                <div className="assistant-conv-list">
                  {conversations.map((conversation) => {
                    const isActive = conversation.id === activeId;
                    const confirming =
                      deletePending === conversation.id;
                    return (
                      <div
                        key={conversation.id}
                        className={`assistant-conv ${
                          isActive ? "active" : ""
                        }`.trim()}
                      >
                        <button
                          type="button"
                          className="assistant-conv-main"
                          onClick={() => selectConversation(conversation.id)}
                        >
                          <span className="assistant-conv-title">
                            {conversation.title || "Conversation"}
                          </span>
                          <span className="assistant-conv-meta">
                            {formatDate(
                              conversation.updated_at ||
                                conversation.created_at
                            )}
                          </span>
                        </button>
                        <button
                          type="button"
                          className={`assistant-conv-delete ${
                            confirming ? "confirm" : ""
                          }`.trim()}
                          onClick={() =>
                            confirming
                              ? handleDeleteConversation(conversation.id)
                              : setDeletePending(conversation.id)
                          }
                          title={
                            confirming
                              ? "Click again to delete"
                              : "Delete conversation"
                          }
                          aria-label={
                            confirming
                              ? `Confirm deleting ${conversation.title || "conversation"}`
                              : `Delete ${conversation.title || "conversation"}`
                          }
                        >
                          {confirming ? "Sure?" : <Trash2 size={14} />}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </aside>

            <div className="assistant-thread">
              <div className="assistant-thread-head">
                <button
                  type="button"
                  className="secondary-button assistant-sidebar-toggle"
                  onClick={() => setSidebarOpen((v) => !v)}
                  aria-expanded={sidebarOpen}
                >
                  <MessageSquare size={14} /> Conversations
                </button>
                <strong>{activeTitle}</strong>
              </div>

              <div className="assistant-scroll">
                {convLoading && messages.length === 0 ? (
                  <SkeletonBlock rows={4} text="Loading conversation..." />
                ) : messages.length === 0 ? (
                  <EmptyState
                    icon={Sparkles}
                    title="Ask the assistant anything"
                    message="Try one of these, or write your own question about the active school."
                  />
                ) : (
                  <div className="thread-list">
                    {messages.map((message) => (
                      <div key={message.id} className="assistant-message">
                        <MessageBubble message={message} />
                        {message.role === "assistant" &&
                          message.actions.length > 0 && (
                            <div className="assistant-actions">
                              {message.actions.map((action) => (
                                <ActionCard
                                  key={action.id}
                                  action={action}
                                  executing={executingIds.has(action.id)}
                                  onConfirm={() =>
                                    runAction(message.id, action)
                                  }
                                  onCancel={() =>
                                    dismissAction(message.id, action.id)
                                  }
                                />
                              ))}
                            </div>
                          )}
                      </div>
                    ))}

                    {sending && (
                      <div className="assistant-bubble in assistant-thinking">
                        <div className="assistant-bubble-meta">
                          <Bot size={13} />
                          <strong>Assistant</strong>
                        </div>
                        <span className="thinking-dots">
                          <span />
                          <span />
                          <span />
                        </span>
                        <span className="assistant-thinking-label">
                          Thinking…
                        </span>
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </div>
                )}

                {convError && (
                  <div className="state-card error" style={{ marginTop: 12 }}>
                    <strong>Could not load this conversation</strong>
                    <span>{convError}</span>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => loadMessages(activeId)}
                    >
                      Try Again
                    </button>
                  </div>
                )}

                {sendError && (
                  <div className="state-card error" style={{ marginTop: 12 }}>
                    <strong>No reply received</strong>
                    <span>{sendError}</span>
                    {pendingText && (
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={retrySend}
                        disabled={sending}
                      >
                        <RefreshCw size={13} /> Retry
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div className="assistant-composer">
                {messages.length === 0 && (
                  <div className="assistant-suggestions">
                    {SUGGESTIONS.map((suggestion) => (
                      <button
                        type="button"
                        key={suggestion}
                        className="assistant-suggestion"
                        onClick={() => send(suggestion)}
                        disabled={sending}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
                <textarea
                  className="assistant-input"
                  rows={2}
                  value={input}
                  placeholder="Ask about students, fees, attendance, staff, and more…"
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={sending}
                  aria-label="Message the AI assistant"
                />
                <div className="assistant-composer-foot">
                  <span>Enter to send · Shift+Enter for a new line</span>
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => send(input)}
                    disabled={sending || !input.trim()}
                  >
                    <Send size={14} /> {sending ? "Sending…" : "Send"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}