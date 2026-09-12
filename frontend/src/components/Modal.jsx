import { useEffect, useRef, useCallback } from "react";
import { X } from "lucide-react";

/**
 * Accessible Modal component with:
 * - Focus trap
 * - ESC key handling
 * - Focus restoration
 * - ARIA attributes
 * - Body scroll lock
 *
 * Uses the app's existing .modal-overlay / .modal / .teacher-modal CSS classes
 * so it stays consistent with the rest of the UI (including dark theme).
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  footer,
  descriptionId,
}) {
  const modalRef = useRef(null);
  const previousActiveElement = useRef(null);

  // Get focusable elements within the modal
  const getFocusableElements = useCallback(() => {
    if (!modalRef.current) return [];
    const selector = [
      'button:not([disabled]):not([aria-hidden="true"])',
      '[href]:not([disabled]):not([aria-hidden="true"])',
      'input:not([disabled]):not([aria-hidden="true"])',
      'select:not([disabled]):not([aria-hidden="true"])',
      'textarea:not([disabled]):not([aria-hidden="true"])',
      '[tabindex]:not([disabled]):not([aria-hidden="true"])',
      '[contenteditable="true"]:not([disabled]):not([aria-hidden="true"])',
    ].join(", ");

    return Array.from(modalRef.current.querySelectorAll(selector));
  }, []);

  // Handle focus trap + ESC key
  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "Tab") {
        const focusableElements = getFocusableElements();
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }

      if (event.key === "Escape" && closeOnEscape) {
        onClose();
      }
    },
    [closeOnEscape, getFocusableElements, onClose]
  );

  // Focus management + scroll lock
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement;
      document.body.classList.add("modal-open");
      document.addEventListener("keydown", handleKeyDown);

      const focusTimer = setTimeout(() => {
        const focusableElements = getFocusableElements();
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        } else if (modalRef.current) {
          modalRef.current.setAttribute("tabIndex", "-1");
          modalRef.current.focus();
        }
      }, 0);

      return () => {
        clearTimeout(focusTimer);
        document.removeEventListener("keydown", handleKeyDown);
        document.body.classList.remove("modal-open");
        if (previousActiveElement.current) {
          previousActiveElement.current.focus();
        }
      };
    }
  }, [isOpen, handleKeyDown, getFocusableElements]);

  if (!isOpen) return null;

  const modalSizeClass =
    size === "large" || size === "xl" || size === "lg" || size === "full" ? "large" : "";

  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        ref={modalRef}
        className={`modal ${modalSizeClass}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : undefined}
        aria-describedby={descriptionId}
      >
        {typeof title === "string" && (
          <div className="modal-header">
            <h3>{title}</h3>
            <button
              type="button"
              className="modal-close"
              onClick={onClose}
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        {typeof title !== "string" && title}
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

export default Modal;