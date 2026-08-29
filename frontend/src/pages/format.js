export function formatCurrency(value) {
  const number = Number(value || 0);

  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(number);
}

export function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function getMonthLabel(monthKey) {
  const [year, month] = String(monthKey).split("-").map(Number);
  const date = new Date(year, month - 1, 1);
  return date.toLocaleDateString("en-GB", { month: "short" });
}
