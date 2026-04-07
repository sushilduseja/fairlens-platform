import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../hooks/useApi";
import type { MetricInfo } from "../utils/types";

type MetricsResponse = {
  metrics: MetricInfo[];
};

const useCaseFilters = [
  { label: "All", value: "all" },
  { label: "Credit", value: "credit" },
  { label: "Fraud", value: "fraud" },
  { label: "Underwriting", value: "underwriting" },
];

export function MetricReferencePage() {
  const [metrics, setMetrics] = useState<MetricInfo[]>([]);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    apiFetch<MetricsResponse>("/metrics")
      .then((response) => setMetrics(response.metrics))
      .catch(() => setMetrics([]));
  }, []);

  const filtered = useMemo(
    () =>
      metrics.filter((metric) =>
        filter === "all" ? true : metric.use_cases.some((item) => item.toLowerCase().includes(filter))
      ),
    [filter, metrics]
  );

  return (
    <section>
      <h2>Metric Reference</h2>
      <div className="tabs">
        {useCaseFilters.map((item) => (
          <button key={item.value} onClick={() => setFilter(item.value)} className={filter === item.value ? "active" : ""}>
            {item.label}
          </button>
        ))}
      </div>

      <div className="metrics-grid">
        {filtered.map((metric) => (
          <article key={metric.name} className="card metric-card">
            <h3>{metric.display_name}</h3>
            <p>{metric.description}</p>
            <p><strong>Use Cases:</strong> {metric.use_cases.join(", ")}</p>
            <p><strong>Limitations:</strong> {metric.limitations.join("; ")}</p>
            <p><strong>Ground Truth:</strong> {metric.requires_ground_truth ? "Required" : "Not required"}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
