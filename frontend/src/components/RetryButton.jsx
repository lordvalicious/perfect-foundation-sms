import React, { useState } from "react";

/**
 * RetryButton - Reusable retry button component.
 * Shows when an API call fails, allows user to retry.
 * 
 * Usage:
 * <RetryButton
 *   onRetry={loadData}
 *   loading={isLoading}
 *   error={errorMessage}
 *   fallback="Try again"
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