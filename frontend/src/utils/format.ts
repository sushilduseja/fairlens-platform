export function formatDate(iso: string | null | undefined): string {
  if (!iso) {
    return "-";
  }
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString();
}

export function formatNumber(value: number, digits = 4): string {
  return value.toFixed(digits);
}
