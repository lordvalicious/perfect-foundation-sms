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
  const response = await fetch(url, {
    credentials: "include",
    ...options,
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
