type Verdict = "PASS" | "CONDITIONAL_PASS" | "FAIL" | "queued" | "processing" | "completed" | "failed";

export function StatusBadge({ value }: { value: Verdict | string | null | undefined }) {
  const normalized = String(value ?? "unknown");
  return <span className={`badge badge-${normalized.toLowerCase()}`}>{normalized}</span>;
}
