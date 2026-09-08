import React from "react";

/**
 * EmptyState - Reusable empty state component.
 * Shows when a list/data set has no items.
 * 
 * Usage:
 * <EmptyState
 *   icon={Settings}
 *   title="No settings found"
 *   description="Your settings will appear here once configured."
 *   actionLabel="Add First Setting"
 *   onAction={() => navigate("/settings")}
 * />
 */
export function EmptyState({
  icon,
  title = "No items found",
  description = "There are no items to display.",
  actionLabel = null,
  onAction = null,
  className = "",
}) {
  return (
    <div className={`content ${className} text-center py-16`}
      style={{
        color: "var(--text-muted)",
        maxWidth: "400px",
        margin: "0 auto",
      }}
    >
      <div className="mb-6">
        {icon && <icon className="h-12 w-12 text-text-muted mx-auto opacity-50 mb-4" />}
        <div className="inline-flex items-center justify-center h-16 w-16 rounded-full border border-border-2 bg-surface-3">
          <svg
            className="h-8 w-8 opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 8v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l7 7v3m-9 3v4a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3m-9-3v-4a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v3m-9 3a2 2 0 0 0 2 2h3a2 2 0 0 0 2-2h-3v-2zm8.5-4.5a1 1 0 0 1 1 1H14a1 1 0 0 1-1-1h-1a1 1 0 0 1-1-1H8a1 1 0 0 1-1-1H5a1 1 0 0 1-1-1a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2z" />
          </svg>
        </div>
      </div>
      <h3 className="text-text mb-2">{title}</h3>
      <p className="text-text-muted mb-6">{description}</p>
      {actionLabel && (
        <button
          className="primary-button"
          onClick={onAction}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

/**
 * RetryButton - Reusable retry button component.
 * Shows when an API call fails, allows user to retry.
 * 
 * Usage:
 * <RetryButton
 *   onRetry={loadData}
 *   loading={isLoading}
 *   error={errorMessage}
 *   fallback="Loading data..."
 * />
 */
export function RetryButton({
  onRetry,
  loading = false,
  error = "Failed to load data.",
  fallback = "Try again",
  className = "",
  disabled = false,
}) {
  return (
    <div className={`state-card error ${className} text-center py-6`}>
      <p className="text-text-muted mb-3">{error}</p>
      <button
        className={`primary-button ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={onRetry}
        disabled={loading || disabled}
      >
        {loading ? "Loading..." : fallback}
      </button>
    </div>
  );
}

/**
 * UseApiWithRetry - Hook that adds retry logic to useApiList.
 * 
 * Usage:
 * const { rows, loading, error, refresh } = useApiListWithRetry('/api/students/');
 */
export function useApiListWithRetry(url) {
  const { rows, count, loading, error, page, next, previous, refresh } = useApiList(url);
  
  const retry = useCallback(() => {
    refresh(new URLSearchParams({ page: 1 }));
  }, [refresh]);
  
  return { rows, count, loading, error, page, next, previous, retry };
}