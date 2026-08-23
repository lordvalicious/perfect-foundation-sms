export function PageHeader({ crumb, title, subtitle, action }) {
  return (
    <div className="page-header">
      <div>
        <div className="breadcrumb">{crumb}</div>
        <h2>{title}</h2>
        <p className="subtitle">{subtitle}</p>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function PanelHeader({ title, subtitle, count, action }) {
  return (
    <div className="teacher-list-header">
      <div>
        <h3>{title}</h3>
        <p>
          {count !== null && count !== undefined
            ? `${count.toLocaleString()} ${subtitle}`
            : subtitle}
        </p>
      </div>
      {action}
    </div>
  );
}

export function StateArea({
  loading,
  error,
  loadingText = "Loading data...",
  errorTitle = "Unable to load data.",
  errorText = "Make sure Django is running at 127.0.0.1:8000.",
  onRetry,
  children,
}) {
  if (loading) {
    return <div className="state-card">{loadingText}</div>;
  }

  if (error) {
    return (
      <div className="state-card error">
        <strong>{errorTitle}</strong>
        <span>{errorText}</span>
        <code>{error}</code>
        {onRetry && (
          <button className="secondary-button" onClick={onRetry}>
            Try Again
          </button>
        )}
      </div>
    );
  }

  return children;
}

export function EmptyState({ icon: Icon, title, message, action }) {
  return (
    <div className="empty-state">
      {Icon && <Icon size={42} strokeWidth={1.5} />}
      <h3>{title}</h3>
      <p>{message}</p>
      {action}
    </div>
  );
}

export function Pagination({
  count,
  page,
  next,
  previous,
  onPage,
  pageSize = 20,
}) {
  if (!count) {
    return null;
  }

  const totalPages = Math.max(1, Math.ceil(count / pageSize));

  return (
    <div className="pagination">
      <button disabled={!previous} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span>
        Page {page} of {totalPages}
      </span>
      <button disabled={!next} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </div>
  );
}

export function StatusBadge({ status, label }) {
  const safe = (status || "").toLowerCase();

  const tone = [
    "active", "present", "paid", "completed", "pass", "scheduled", "cancelled",
  ].includes(safe)
    ? safe === "cancelled"
      ? "inactive"
      : "active"
    : ["inactive", "absent", "fail", "overdue"].includes(safe)
    ? "inactive"
    : ["late", "pending", "partial"].includes(safe)
    ? "warn"
    : "info";

  return (
    <span className={`status-badge ${tone}`}>
      {label || (status ? status.charAt(0).toUpperCase() + status.slice(1) : "\u2014")}
    </span>
  );
}
