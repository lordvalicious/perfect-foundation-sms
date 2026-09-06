/**
 * sessionWatch — global 401/403 (session-expiry) detection.
 *
 * Wraps window.fetch once and dispatches a `pf:unauthorized` event whenever an
 * authenticated API request returns HTTP 401, or returns HTTP 403 while the
 * session is actually gone. The 403 case is verified against /api/auth/me/ so
 * that legitimate "authenticated but forbidden" responses do not force a
 * logout. The AuthProvider subscribes to this event and clears the in-memory
 * user so the Shell redirects to login.
 *
 * This is a UX convenience (session expiry). It is NOT a security mechanism —
 * the backend remains the sole authority on authorization.
 */

const INIT_EVENT = "pf:unauthorized";

// Endpoints that legitimately return 401 (bad credentials, pre-auth) must not
// trigger a forced "session expired" redirect.
const EXCLUDED_PATHS = [
  "/api/auth/login/",
  "/api/auth/logout/",
  "/api/auth/csrf/",
  "/api/auth/me/",
  "/api/schools/tenant-config/",
];

const SESSION_PROBE = "/api/auth/me/";

let installed = false;

export function installSessionWatch() {
  if (installed || typeof window === "undefined") return;
  installed = true;

  const originalFetch = window.fetch.bind(window);
  let probing = false;

  const fireExpired = () => {
    window.dispatchEvent(new CustomEvent(INIT_EVENT));
  };

  const probeSession = () => {
    if (probing) return;
    probing = true;
    originalFetch(SESSION_PROBE, { credentials: "include" })
      .then((response) => {
        if (!response.ok) fireExpired();
      })
      .catch(() => {})
      .finally(() => {
        probing = false;
      });
  };

  window.fetch = function (input, init) {
    const url =
      typeof input === "string"
        ? input
        : input && typeof input.url === "string"
        ? input.url
        : "";

    const shouldWatch =
      url.startsWith("/api/") &&
      !EXCLUDED_PATHS.some((p) => url.startsWith(p));

    const promise = originalFetch(input, init);

    if (shouldWatch) {
      promise.then((response) => {
        if (response.status === 401) {
          fireExpired();
        } else if (response.status === 403) {
          probeSession();
        }
      });
    }

    return promise;
  };
}

export function onSessionExpired(handler) {
  window.addEventListener(INIT_EVENT, handler);
  return () => window.removeEventListener(INIT_EVENT, handler);
}
