/*
 * AI Assistant API client — matches backend `apps/ai` (mounted at `/api/ai/`).
 *
 * Endpoints:
 *   GET  /api/ai/overview/              -> { role, institution, institution_name,
 *                                            capabilities[], students_in_scope,
 *                                            attendance{...}, finance?{...} }
 *   POST /api/ai/ask/  body {query}     -> { ok, query, intent, answer, digest }
 *   GET  /api/ai/search/?q=             -> { query, entities[] }
 *   GET  /api/ai/insights/students/     -> { insights[] }  (role-gated)
 *   GET  /api/ai/insights/attendance/   -> attendance dict  (role-gated)
 *   GET  /api/ai/insights/academic/     -> academic dict  (role-gated)
 *   GET  /api/ai/insights/finance/      -> finance dict  (role-gated)
 *   GET  /api/ai/anomalies/             -> { anomalies[] }  (role-gated)
 *   POST /api/ai/communication/draft/   -> draft dict (role-gated, NEVER sends)
 *
 * Security rules the client always follows:
 *  - All authorization, role checks, institution scope and campus scope are
 *    DERIVED SERVER-SIDE from the session. The client sends NO roles,
 *    permissions, school ids or campus ids — it only asks questions.
 *  - The "overview" endpoint doubles as the availability probe: 403 means the
 *    account is not authorized (not an outage), 404/405/410 mean the module
 *    is not deployed. Both map to a friendly, non-throwing `available:false`.
 *  - Communication drafts are generated server-side and are `draft_only` —
 *    nothing is ever sent by this client.
 *  - Assistant text is rendered as plain text (no HTML injection).
 */

import { apiFetch, jsonHeaders } from "./api";

const AI_BASE = "/api/ai";

function normalizeOverview(data) {
  if (!data || typeof data !== "object" || !("capabilities" in data)) {
    return null;
  }
  return {
    role: data.role || "member",
    school: data.institution_name || "Active school",
    capabilities: Array.isArray(data.capabilities) ? data.capabilities : [],
    studentsInScope: data.students_in_scope ?? null,
    attendance: data.attendance || null,
    finance: data.finance || null,
  };
}

// Never throws for "not available/not authorized" deployments — the page can
// render an honest state instead of a hard error.
export async function fetchAssistantOverview() {
  try {
    const response = await fetch(`${AI_BASE}/overview/`, {
      credentials: "include",
    });

    if (!response.ok) {
      if ([404, 405, 410].includes(response.status)) {
        return {
          available: false,
          message: "The AI assistant is not enabled for this deployment yet.",
        };
      }
      if (response.status === 403) {
        return {
          available: false,
          message:
            "The AI assistant is not available to your account. Ask an administrator for access.",
        };
      }
      return {
        available: false,
        message: "The AI assistant is temporarily unavailable.",
      };
    }

    const data = await response.json().catch(() => ({}));
    const overview = normalizeOverview(data);
    return overview
      ? { available: true, ...overview }
      : { available: false, message: "The AI assistant returned an invalid response." };
  } catch {
    return { available: false, message: "The AI assistant could not be reached." };
  }
}

export async function askQuestion(query) {
  const data = await apiFetch(
    `${AI_BASE}/ask/`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ query }),
    },
    "The assistant could not answer."
  );

  return {
    intent: data?.intent || "general",
    answer: typeof data?.answer === "string" ? data.answer : "",
    digest: data?.digest && typeof data.digest === "object" ? data.digest : {},
  };
}

export async function searchEntities(query) {
  const data = await apiFetch(
    `${AI_BASE}/search/?q=${encodeURIComponent(query)}`,
    {},
    "Could not search."
  );
  return Array.isArray(data?.entities) ? data.entities : [];
}

export async function getAnomalies() {
  const data = await apiFetch(`${AI_BASE}/anomalies/`, {}, "Could not scan.");
  return Array.isArray(data?.anomalies) ? data.anomalies : [];
}

// Generates (never sends) a scoped communication draft. The backend refuses
// if recipients fall outside the caller's access scope.
export async function createCommunicationDraft({ type, subject = "", body = "" }) {
  const data = await apiFetch(
    `${AI_BASE}/communication/draft/`,
    {
      method: "POST",
      headers: jsonHeaders(),
      body: JSON.stringify({ type, subject, body }),
    },
    "Could not generate the draft."
  );
  return {
    type: data?.type || type,
    subject: data?.subject || "",
    body: data?.body || "",
    recipientCount: data?.recipient_count ?? 0,
    draftOnly: data?.draft_only !== false,
  };
}