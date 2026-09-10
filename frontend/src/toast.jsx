/* eslint-disable react-refresh/only-export-components */
/* Lite, dependency-free toast system.
   - ToastProvider renders an aria-live viewport (polite for info/success,
     assertive for errors) so screen readers announce feedback.
   - useToast() exposes push({ type, text, duration }) plus typed helpers
     success(), error(), info().
   - Stacking, auto-dismiss, click-to-dismiss, keyboard focusable close. */

import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

const ToastContext = createContext({
  success: () => {},
  error: () => {},
  info: () => {},
  push: () => {},
});

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((items) => items.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    ({ type = "info", text, duration = 4000 }) => {
      const id = ++idRef.current;
      setToasts((items) => [...items.slice(-3), { id, type, text }]);
      if (duration) {
        window.setTimeout(() => dismiss(id), duration);
      }
    },
    [dismiss]
  );

  const api = useMemo(
    () => ({
      success: (text) => push({ type: "success", text }),
      error: (text) => push({ type: "error", text, duration: 6000 }),
      info: (text) => push({ type: "info", text }),
      push,
    }),
    [push]
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-viewport" aria-live="polite" aria-atomic="false">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast-card toast-${toast.type}`}
            role={toast.type === "error" ? "alert" : "status"}
          >
            <span className="toast-text">{toast.text}</span>
            <button
              type="button"
              className="toast-close"
              aria-label="Dismiss notification"
              onClick={() => dismiss(toast.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}