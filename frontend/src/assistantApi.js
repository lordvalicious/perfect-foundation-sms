/*
 * AI Assistant API client.
 *
 * Contract (backend P5 implements `apps/ai` mounted at `/api/ai/`):
 *
 *   GET    /api/ai/status/                     -> { available, provider?, name?, message? }
 *   GET    /api/ai/conversations/              -> { results: [{ id, title, created_at, updated_at }] }
 *   POST   /api/ai/conversations/              -> { id, title, created_at }
 *   GET    /api/ai/conversations/<id>/         -> { id, title, messages: [Message] }
 *   POST   /api/ai/conversations/<id>/messages/
 *          body: { message, school_id, campus_id }
 *          -> Message (assistant reply; user turn is stored server-side)
 *   DELETE /api/ai/conversations/<id>/         -> 204
 *   POST   /api/ai/actions/execute/
 *          body: { action_id, confirmation, params } -> { ok: true, detail?, ... }
 *
 * Message shape (used by GET conversation detail and POST messages):
 *   {
 *     id, role: "user" | "assistant",
 *     content: string,
 *     created_at: ISO string,
 *     sources?: string[],
 *     actions?: [              // assistant-only, PROPOSED actions
 *        { id, label, description?, risk?: "low"|"medium"|"high",
 *          params, requires_confirmation }
 *     ]
 *   }
 *
 * Security rules the client always follows:
 *  - Roles are DERIVED SERVER-SIDE from the session; the client never
 *    sends roles or permissions and never claims authorization.
 *  - The client only ever sends the school/campus the user is currently
 *    scoped to (useSchool context) — never free-form identifiers. The
 *    backend must re-validate ownership of both on every request.
 *  - Proposed actions are only RENDERED and CONFIRMED by the user. The
 *    client never performs the action itself; execution always goes back
 *    through the backend which re-checks authorization + institution scope.
 *  - Assistant text is rendered as plain text (no HTML injection).
 */

import { apiFetch, jsonHeaders } from "./api";

const AI_BASE = "/api/ai";

const LIST_FALLBACK = "Could not load conversations.";

function normalizeMessage(raw) {
  if (!raw || typeof raw !== "object") return null;

  const actions = Array.isArray(raw.actions) ? raw.actions : [];
  const sources = Array.isArray(raw.sources) ? raw.sources : [];

  return {
    id: raw.id ?? null,
    role: raw.role === "user" ? "user" : "assistant",
    content: typeof raw.content === "string" ? raw.content : "",
    createdAt: raw.created_at || null,
    sources: sources.map((s) => (typeof s === "string" ? s : String(s))),
    actions: actions.filter(
      (a) => a && typeof a.label === "string" && a.label.trim()
    ),
  };
}

// `status` never throws for "not available" deployments: 404/405/410 mean the
// endpoint was not implemented yet, and a non-2xx response is reported as an
// unavailable state the page can render (rather than a hard error).
export async function getAssistantStatus() {
  try {
    const response = await fetch(`${AI_BASE}/status/`, {
      credentials: "include",
    });

    if (!response.ok) {
      if ([404, 405, 410].includes(response.status)) {
        return {
          available: false,
          message:
            "The AI assistant is not enabled for this deployment yet.",
        };
      }
      return {
        available: false,
        message: "The AI assistant is temporarily unavailable.",
      };
    }

    const data = await response.json().catch(() => ({}));
    if (data && typeof data === "object" && "available" in data) {
      return {
        available: !!data.available,
        provider: data.provider || "",
        name: data.name || "AI Assistant",
        message: data.message || "",
      };
    }

    return { available: false, message: "The AI assistant is not enabled." };
  } catch {
    return {
      available: false,
      message: "The AI assistant could not be reached.",
    };
  }
}

export async function listConversations() {
  const data = await apiFetch(`${AI_BASE}/conversations/`, {}, LIST_FALLBACK);
  return Array.isArray(data) ? data : data.results || [];
}

export async function createConversation() {
  return apiFetch(
    `${AI_BASE}/conversations/`,
    { method: "POST", headers: jsonHeaders(), body: "{}" },
    "Could not start a new conversation."
  );
}

export async function getConversation(id, schoolId, campusId) {
  const data = await apiFetch(
    `${AI_BASE}/conversations/${id}/?school_id=${encodeURIComponent(
      schoolId
    )}&campus_id=${
      campusId ? encodeURIComponent(campusId) : ""
    }`,
    {},
    "Could not load the conversation."
  );

  const messages = Array.isArray(data.messages)
    ? data.messages
    : Array.isArray(data.results)
    ? data.results
    : [];

  return {
    id: data.id ?? id,
    title: data.title || "Conversation",
    messages: messages.map(normalizeMessage).filter(Boolean),
  };
}

export async function sendMessage(
  conversationId,
  { message, schoolId, campusId }
) {
  const raw = await apiFetch(
    `${AI_BASE}/conversations/${conversationId}/messages/`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        message,
        school_id: schoolId,
        campus_id: campusId || null,
      }),
    },
    "The assistant could not respond."
  );

  // Accept either a single assistant message or a { user_message,
  // assistant_message } envelope.
  const assistantRaw = raw?.assistant_message || raw;
  const normalized = normalizeMessage(assistantRaw);

  if (!normalized) {
    throw new Error("The assistant returned an empty response.");
  }

  return normalized;
}

export async function deleteConversation(id) {
  await apiFetch(
    `${AI_BASE}/conversations/${id}/`,
    { method: "DELETE" },
    "Could not delete the conversation."
  );
}

// Confirms + executes a PROPOSED action. The backend re-validates the
// session role and the school/campus scope before performing anything.
export async function executeAction({ action, schoolId, campusId }) {
  const data = await apiFetch(
    `${AI_BASE}/actions/execute/`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({
        action_id: action.id,
        confirmation: true,
        params: action.params || {},
        school_id: schoolId,
        campus_id: campusId || null,
      }),
    },
    "The action could not be executed."
  );

  return {
    ok: data && data.ok !== false,
    detail: data?.detail || "Action completed.",
  };
}