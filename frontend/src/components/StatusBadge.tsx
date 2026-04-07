type Verdict = "PASS" | "CONDITIONAL_PASS" | "FAIL" | "queued" | "processing" | "completed" | "failed";

interface StatusBadgeProps {
  value: Verdict | string | null | undefined;
  large?: boolean;
}

export function StatusBadge({ value, large }: StatusBadgeProps) {
  const normalized = String(value ?? "unknown");
  const label = normalized === "conditional_pass" ? "CONDITIONAL" : normalized;
  return (
    <span className={`badge badge-${normalized.toLowerCase()}${large ? " badge-large" : ""}`}>
      {label}
    </span>
  );
}
