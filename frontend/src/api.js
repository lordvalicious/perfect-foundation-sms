// Maps an HTTP status to a safe, user-friendly message. Sensitive backend
// internals are never surfaced; the message comes from the backend's own
// `detail` when present (safe), otherwise a generic tone for the status.
export function statusMessage(status) {
  if (status === 400) {
    return "The information you entered could not be saved. Please check the fields and try again.";
  }

  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested record could not be found.";
  }

  if (status === 409) {
    return "A record already exists with those details. Please use a different value.";
  }

  if (status >= 500) {
    return "Something went wrong on the server. Please try again shortly.";
  }

  return null;
}

// Builds a safe error message from a failed response. Uses the backend's own
// `detail` (authored and intended for display) when present; otherwise a
// status-based generic message. Field-level errors are summarized without
// dumping raw values.
export function buildErrorMessage({
  status,
  detail,
  fieldErrors,
  responseText,
  fallback = "Request failed.",
}) {
  if (detail && typeof detail === "string" && detail.trim()) {
    return detail;
  }

  const generic = statusMessage(status);

  if (generic) {
    return generic;
  }

  if (fieldErrors && typeof fieldErrors === "object") {
    const fields = Object.keys(fieldErrors);
    if (fields.length > 0) {
      const label = fields.length === 1 ? fields[0] : "some fields";
      return `Please check ${label} in the form.`;
    }
  }

  if (responseText && typeof responseText === "string" && responseText.trim()) {
    return fallback;
  }

  return fallback;
}

export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }

  return null;
}

export function authHeaders(extra = {}) {
  const csrfToken = getCookie("csrftoken");

  return {
    ...extra,
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
  };
}

export function jsonHeaders(extra = {}) {
  return authHeaders({
    "Content-Type": "application/json",
    ...extra,
  });
}

export async function readJson(response, fallback) {
  const text = await response.text();

  if (!text) {
    throw new Error(
      `${fallback} The server returned an empty response (HTTP ${response.status}).`
    );
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(
      `${fallback} The server returned a non-JSON response (HTTP ${response.status}).`
    );
  }
}

export async function apiFetch(url, options = {}, fallback = "Request failed.") {
  const csrfToken = getCookie("csrftoken");

  const headers = {
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    credentials: "include",
    ...options,
    headers,
  });

  const data = await readJson(response, fallback).catch(() => ({}));

  if (!response.ok) {
    let message = fallback;

    if (data && typeof data === "object") {
      if (data.detail) {
        message = Array.isArray(data.detail)
          ? data.detail.join(", ")
          : String(data.detail);
      } else {
        const parts = Object.entries(data)
          .map(([field, value]) => {
            const text = Array.isArray(value)
              ? value.join(", ")
              : String(value);

            return `${field}: ${text}`;
          })
          .filter((text) => text && text !== "undefined: undefined");

        if (parts.length) {
          message = parts.join(" | ");
        }
      }
    }

    throw new Error(message);
  }

  return data;
}

export function downloadUrl(path) {
  window.open(path, "_blank");
}

export function apiDownload(path, filename) {
  return fetch(path, { credentials: "include" })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Download failed.");
      }

      return response.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = filename || "download";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
}
