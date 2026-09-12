import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Bot,
  Send,
  Sparkles,
  Building2,
  MapPin,
  ShieldCheck,
  RefreshCw,
  Search,
  AlertTriangle,
  FileText,
} from "lucide-react";
import { PageHeader, EmptyState, SkeletonBlock } from "./ui";
import { useSchool } from "../schoolContext";
import { useToast } from "../toast";
import {
  fetchAssistantOverview,
  askQuestion,
  searchEntities,
  getAnomalies,
  createCommunicationDraft,
} from "../assistantApi";

const ASK_PROMPTS = [
  {
    id: "attendance",
    label: "Attendance",
    capability: "attendance_insights",
    query: "How is attendance going?",
  },
  {
    id: "finance",
    label: "Fees & overdue",
    capability: "finance_insights",
    query: "Show me overdue fees",
  },
  {
    id: "academic",
    label: "Latest exam",
    capability: "academic_insights",
    query: "How did the latest exam go?",
  },
  {
    id: "counts",
    label: "Student count",
    capability: null,
    query: "How many students are in my scope?",
  },
];

const TOOL_ACTIONS = [
  { id: "anomalies", label: "Anomaly scan", capability: "anomalies", kind: "anomalies" },
  { id: "search", label: "Find student / class", capability: "search", kind: "search" },
];

const DRAFT_ACTIONS = [
  { id: "fee_reminder", label: "Draft fee reminder", capability: "communication_drafts", type: "fee_reminder" },
  { id: "attendance_warning", label: "Draft attendance notice", capability: "communication_drafts", type: "attendance_warning" },
  { id: "exam_notice", label: "Draft exam notice", capability: "communication_drafts", type: "exam_notice" },
];

const SUGGESTIONS = [
  "How is attendance going?",
  "Show me overdue fees",
  "How did the latest exam go?",
];

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function severityLabel(severity) {
  if (severity === "high") return "High";
  if (severity === "medium") return "Medium";
  return "Low";
}

function DigestCard({ digest }) {
  if (!digest || Object.keys(digest).length === 0) return null;

  const rows = [];
  if ("overall_rate" in digest) {
    rows.push(
      ["Overall attendance", `${digest.overall_rate}%`],
      ["Records in scope", String(digest.records ?? "—")],
      ["Present", String(digest.present ?? "—")],
      ["Days", String(digest.days ?? "—")],
      [
        "Below 75%",
        Array.isArray(digest.students_below_75)
          ? String(digest.students_below_75.length)
          : "—",
      ]
    );
  }
  if ("total_outstanding" in digest) {
    rows.push(
      ["Total outstanding", String(digest.total_outstanding ?? "—")],
      ["Open invoices", String(digest.invoice_count ?? "—")],
      ["Overdue", String(digest.overdue_count ?? "—")],
      ["Overdue amount", String(digest.overdue_amount ?? "—")]
    );
  }
  if ("exam" in digest || "overall_pass_rate" in digest) {
    rows.push(
      ["Exam", digest.exam || "—"],
      ["Overall pass rate", `${digest.overall_pass_rate}%`],
      ["Subjects", String(digest.subjects?.length ?? "—")]
    );
  }
  if ("students" in digest || "teachers" in digest) {
    rows.push(
      ["Students", String(digest.students ?? "—")],
      ["Teachers", String(digest.teachers ?? "—")]
    );
  }

  return (
    <div className="assistant-digest">
      <div className="assistant-digest-title">Figures</div>
      {rows.map(([key, value]) => (
        <div className="assistant-digest-row" key={key}>
          <span className="assistant-digest-key">{key}</span>
          <span className="assistant-digest-value">{value}</span>
        </div>
      ))}
      {Array.isArray(digest.students_below_75) &&
        digest.students_below_75.length > 0 && (
          <ul className="assistant-digest-list">
            {digest.students_below_75.map((entry) => (
              <li key={entry.student_id}>
                Student #{entry.student_id} — {entry.rate}% ({entry.absent}{" "}
                absent)
              </li>
            ))}
          </ul>
        )}
      {Array.isArray(digest.subjects) && digest.subjects.length > 0 && (
        <ul className="assistant-digest-list">
          {digest.subjects.map((entry) => (
            <li key={entry.subject}>
              {entry.subject}: {entry.pass_rate}% pass rate
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EntityCard({ entity }) {
  const kind = (entity.kind || "record").toUpperCase();
  const meta =
    entity.kind === "invoice"
      ? `${entity.invoice_number || ""}${entity.status ? ` · ${entity.status}` : ""}${entity.balance ? ` · balance ${entity.balance}` : ""}`
      : entity.kind === "student"
      ? `${entity.admission_number || ""}${entity.status ? ` · ${entity.status}` : ""}`
      : entity.kind === "teacher"
      ? `${entity.employee_number || ""}`
      : "";
  return (
    <div className="assistant-item-card">
      <span className="assistant-item-kind">{kind}</span>
      <strong>{entity.name || entity.invoice_number || `#${entity.id}`}</strong>
      {meta && <span className="assistant-item-meta">{meta}</span>}
    </div>
  );
}

function AnomalyCard({ item }) {
  return (
    <div className={`assistant-item-card sev-${item.severity}`}>
      <span className="assistant-item-kind">{severityLabel(item.severity)} impact</span>
      <strong>{item.title}</strong>
      <span className="assistant-item-meta">{item.detail}</span>
    </div>
  );
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

      {!mine && message.digest && <DigestCard digest={message.digest} />}

      {!mine && Array.isArray(message.items) && message.items.length > 0 && (
        <div className="assistant-items">
          {message.kind === "anomalies"
            ? message.items.map((item, i) => (
                <AnomalyCard key={i} item={item} />
              ))
            : message.items.map((entity, i) => (
                <EntityCard key={`${entity.id}-${i}`} entity={entity} />
              ))}
        </div>
      )}

      {!mine && message.draft && (
        <div className="assistant-draft-card">
          <span className="assistant-draft-note">
            <ShieldCheck size={12} /> DRAFT ONLY — nothing is sent
          </span>
          <strong>{message.draft.subject}</strong>
          <p>{message.draft.body}</p>
          <span className="assistant-item-meta">
            {message.draft.recipientCount} recipient(s) generated in your scope
          </span>
        </div>
      )}
    </div>
  );
}

export default function AIAssistantPage() {
  const toast = useToast();
  const { currentSchool, activeCampus, campusList } = useSchool();

  const [status, setStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusReloadKey, setStatusReloadKey] = useState(0);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pendingText, setPendingText] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");

  const [pendingDraft, setPendingDraft] = useState(null);
  const [drafting, setDrafting] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const sendingRef = useRef(false);
  const threadForRef = useRef(null);
  const bottomRef = useRef(null);
  const tmpIdRef = useRef(0);

  const campusLabel =
    activeCampus?.name ||
    (campusList.length > 1 ? "All campuses" : currentSchool?.name || "—");

  const capabilities = useMemo(
    () => (status?.available ? status.capabilities : []),
    [status]
  );
  const hasCapability = useCallback(
    (capability) => !capability || capabilities.includes(capability),
    [capabilities]
  );

  const busy = sending || drafting || searching;

  const loadStatus = useCallback(() => {
    setStatusLoading(true);
    fetchAssistantOverview()
      .then(setStatus)
      .finally(() => setStatusLoading(false));
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus, statusReloadKey]);

  // Client-session history resets with every school/campus scope change so
  // earlier questions are never (mis)read against the new scope.
  useEffect(() => {
    setMessages([]);
    setInput("");
    setSendError("");
    setPendingDraft(null);
    setSearchOpen(false);
    setSearchQuery("");
  }, [currentSchool?.id, activeCampus?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  const appendMessage = useCallback((message) => {
    setMessages((current) => [...current, message]);
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
      appendMessage({
        id: tmpId,
        role: "user",
        kind: "ask",
        content: text,
        createdAt: new Date().toISOString(),
      });
      setInput("");

      threadForRef.current = "ask";
      try {
        const answer = await askQuestion(text);
        if (threadForRef.current === "ask") {
          appendMessage({
            id: `ask-${Date.now()}`,
            role: "assistant",
            kind: "ask",
            content: answer.answer || "No answer returned.",
            digest: answer.digest,
            createdAt: new Date().toISOString(),
          });
        }
      } catch (err) {
        setMessages((current) => current.filter((m) => m.id !== tmpId));
        setInput(text);
        setPendingText(text);
        setSendError(err.message);
      } finally {
        threadForRef.current = null;
        sendingRef.current = false;
        setSending(false);
      }
    },
    [status, appendMessage]
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

  const runAnomalies = useCallback(async () => {
    if (busy) return;
    setSearching(false);
    try {
      const items = await getAnomalies();
      appendMessage({
        id: `anom-${Date.now()}`,
        role: "assistant",
        kind: "anomalies",
        content:
          items.length > 0
            ? "Anomaly scan for your scope:"
            : "No anomalies found in your scope.",
        items,
        createdAt: new Date().toISOString(),
      });
    } catch (err) {
      toast.error(err.message);
    }
  }, [busy, appendMessage, toast]);

  const runSearch = useCallback(async () => {
    const query = searchQuery.trim();
    if (!query || searching) return;
    try {
      const entities = await searchEntities(query);
      appendMessage({
        id: `search-${Date.now()}`,
        role: "assistant",
        kind: "search",
        content:
          entities.length > 0
            ? `Found ${entities.length} matching record(s) in your scope:`
            : `No matching records in your scope.`,
        items: entities,
        createdAt: new Date().toISOString(),
      });
      setSearchOpen(false);
      setSearchQuery("");
    } catch (err) {
      toast.error(err.message);
    }
  }, [searchQuery, searching, appendMessage, toast]);

  const confirmDraft = useCallback(async () => {
    if (!pendingDraft || drafting) return;
    setDrafting(true);
    const type = pendingDraft.type;
    try {
      const draft = await createCommunicationDraft({ type });
      appendMessage({
        id: `draft-${Date.now()}`,
        role: "assistant",
        kind: "draft",
        content: "Generated a draft for review:",
        draft,
        createdAt: new Date().toISOString(),
      });
      setPendingDraft(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setDrafting(false);
    }
  }, [pendingDraft, drafting, appendMessage, toast]);

  const cancelDraft = useCallback(() => setPendingDraft(null), []);

  const promptChips = ASK_PROMPTS.filter((item) =>
    hasCapability(item.capability)
  );
  const toolChips = TOOL_ACTIONS.filter((item) =>
    hasCapability(item.capability)
  );
  const draftChips = DRAFT_ACTIONS.filter((item) =>
    hasCapability(item.capability)
  );

  return (
    <section className="content">
      <PageHeader
        crumb="Home / AI Assistant"
        title="AI Assistant"
        subtitle="Ask plain-language questions about the active school. Answers are scoped to your role, school and campus — on the server."
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
          <div className="assistant-context-bar">
            <span className="assistant-context-badge">
              <Building2 size={13} />
              {currentSchool?.name || status.school}
            </span>
            <span className="assistant-context-badge">
              <MapPin size={13} />
              {campusLabel}
            </span>
            <span className="assistant-context-badge">
              <ShieldCheck size={13} />
              {status.role}
            </span>
            <span className="assistant-context-note">
              <ShieldCheck size={13} />
              Scoped to your access in the active school.
            </span>
          </div>

          <div className="assistant-capbar">
            {promptChips.map((chip) => (
              <button
                type="button"
                key={chip.id}
                className="assistant-chip"
                onClick={() => send(chip.query)}
                disabled={busy}
              >
                {chip.label}
              </button>
            ))}
            {toolChips.map((chip) => (
              <button
                type="button"
                key={chip.id}
                className="assistant-chip"
                onClick={() =>
                  chip.kind === "anomalies"
                    ? runAnomalies()
                    : setSearchOpen((open) => !open)
                }
                disabled={busy}
              >
                {chip.kind === "anomalies" ? (
                  <AlertTriangle size={13} />
                ) : (
                  <Search size={13} />
                )}
                {chip.label}
              </button>
            ))}
            {draftChips.map((chip) => (
              <button
                type="button"
                key={chip.id}
                className="assistant-chip"
                onClick={() =>
                  setPendingDraft({ type: chip.type, label: chip.label })
                }
                disabled={busy}
              >
                <FileText size={13} />
                {chip.label}
              </button>
            ))}
          </div>

          <div className="assistant-scroll">
            {messages.length === 0 ? (
              <EmptyState
                icon={Sparkles}
                title="Ask the assistant anything"
                message="Ask about attendance, fees, exam results, or student counts for the active school, or use the shortcuts above."
              />
            ) : (
              <div className="thread-list">
                {messages.map((message) => (
                  <div key={message.id} className="assistant-message">
                    <MessageBubble message={message} />
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
                    <span className="assistant-thinking-label">Thinking…</span>
                  </div>
                )}
                <div ref={bottomRef} />
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

            {pendingDraft && (
              <div className="assistant-confirm-bar">
                <span>
                  Generate a <strong>{pendingDraft.label.toLowerCase()}</strong>{" "}
                  draft for students in your scope? Nothing is sent.
                </span>
                <button
                  type="button"
                  className="primary-button"
                  onClick={confirmDraft}
                  disabled={drafting}
                >
                  {drafting ? "Generating…" : "Confirm"}
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={cancelDraft}
                  disabled={drafting}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {searchOpen && (
            <div className="assistant-search-box">
              <input
                className="assistant-input"
                value={searchQuery}
                placeholder="Search students, classes, teachers or invoices in your scope…"
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") runSearch();
                }}
                aria-label="Search within your scope"
              />
              <button
                type="button"
                className="primary-button"
                onClick={runSearch}
                disabled={searching || !searchQuery.trim()}
              >
                <Search size={14} /> {searching ? "Searching…" : "Search"}
              </button>
            </div>
          )}

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
              placeholder="Ask about attendance, fees, exam results, and student counts…"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={busy}
              aria-label="Ask the AI assistant"
            />
            <div className="assistant-composer-foot">
              <span>Enter to send · Shift+Enter for a new line</span>
              <button
                type="button"
                className="primary-button"
                onClick={() => send(input)}
                disabled={busy || !input.trim()}
              >
                <Send size={14} /> {sending ? "Asking…" : "Ask"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}