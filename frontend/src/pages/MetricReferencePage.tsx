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
  { label: "Insurance", value: "insurance" },
];

export function MetricReferencePage() {
  const [metrics, setMetrics] = useState<MetricInfo[]>([]);
  const [filter, setFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    apiFetch<MetricsResponse>("/metrics")
      .then((response) => setMetrics(response.metrics))
      .catch(() => setMetrics([]))
      .finally(() => setIsLoading(false));
  }, []);

  const filtered = useMemo(
    () =>
      metrics.filter((metric) =>
        filter === "all" ? true : metric.use_cases.some((item) => item.toLowerCase().includes(filter))
      ),
    [filter, metrics]
  );

    return (
      <section className="metric-reference">
        <div className="ref-page-header">
          <h2>Metric Reference</h2>
          <p>Learn which fairness metrics to use for your specific use case.</p>
        </div>

        <div className="ref-filter-tabs">
          {useCaseFilters.map((item) => (
            <button 
              key={item.value} 
              onClick={() => setFilter(item.value)} 
              className={`ref-filter-tab ${filter === item.value ? "active" : ""}`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="ref-metrics-grid">
          {isLoading
            ? Array.from({ length: 6 }).map((_, i) => (
                <article key={i} className="ref-metric-card skeleton-card">
                  <div className="ref-metric-card-header">
                    <div className="skeleton-title"></div>
                    <div className="skeleton-badge"></div>
                  </div>
                  <div className="skeleton-description"></div>
                  <div className="ref-metric-card-details">
                    <div className="ref-detail-section">
                      <div className="skeleton-subtitle"></div>
                      <div className="skeleton-tags"></div>
                    </div>
                    <div className="ref-detail-section">
                      <div className="skeleton-subtitle"></div>
                      <div className="skeleton-list"></div>
                    </div>
                  </div>
                </article>
              ))
            : filtered.map((metric) => (
              <article key={metric.name} className="ref-metric-card">
                <div className="ref-metric-card-header">
                  <h3>{metric.display_name}</h3>
                  {metric.requires_ground_truth && (
                    <span className="ref-metric-badge">Requires Labels</span>
                  )}
                </div>
                <p className="ref-metric-description">{metric.description}</p>
                
                <div className="ref-metric-card-details">
                  <div className="ref-detail-section">
                    <h4>Use Cases</h4>
                    <div className="ref-use-case-tags">
                      {metric.use_cases.map((useCase) => (
                        <span key={useCase} className="ref-use-case-tag">{useCase}</span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="ref-detail-section">
                    <h4>Limitations</h4>
                    <ul className="ref-limitations-list">
                      {metric.limitations.map((limitation, index) => (
                        <li key={index}>{limitation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </article>
            ))}
        </div>

        {filtered.length === 0 && (
          <div className="empty-state">
            <p>No metrics found for this filter.</p>
          </div>
        )}
      </section>
    );
}
