export function normalizeTicker(value: string) {
  return value.trim().toUpperCase();
}

export function formatPrice(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `$${Number(value).toFixed(2)}`;
}

export function formatPercent(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `${Number(value).toFixed(2)}%`;
}

export function formatAccuracy(value?: string | null) {
  if (!value) {
    return "None";
  }
  return `${(Number(value) * 100).toFixed(0)}%`;
}

export function formatScore(value?: string | null) {
  if (!value) {
    return "None";
  }
  return Number(value).toFixed(2);
}

export function formatNumber(value?: number | null) {
  if (value === null || value === undefined) {
    return "None";
  }
  return Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "No timestamp";
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

export function directionClass(direction: string) {
  if (direction === "up") {
    return "positive";
  }
  if (direction === "down") {
    return "negative";
  }
  return "neutral";
}
