import { useParams, Link } from "react-router-dom";

import { StatusBadge } from "../components/StatusBadge";
import { usePollAudit } from "../hooks/usePollAudit";
import { formatDate, formatNumber } from "../utils/format";

export function AuditDetailPage() {
  const { id } = useParams();
  const { audit, error } = usePollAudit(id);

  if (error) {
    return (
      <div className="error-container">
        <div className="error-card">
          <div className="error-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 8v4M12 16h.01"/>
            </svg>
          </div>
          <h3>Error Loading Audit</h3>
          <p>{error}</p>
          <Link to="/" className="btn-primary">Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  if (!audit) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading audit...</p>
      </div>
    );
  }

  const isProcessing = audit.status === "queued" || audit.status === "processing";
  const showNarrative = audit.narrative_summary && !isProcessing;

  return (
    <section className="audit-detail">
      {/* Header with status first */}
      <div className="audit-header">
        <div className="audit-header-left">
          <Link to="/" className="back-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back
          </Link>
          <h2>Audit Results</h2>
        </div>
        <div className="audit-header-right">
          <StatusBadge value={audit.status} large />
          {audit.overall_verdict && !isProcessing && (
            <StatusBadge value={audit.overall_verdict} large />
          )}
          {audit.groq_enriched && (
            <span className="ai-badge">AI-Enhanced</span>
          )}
        </div>
      </div>

      {/* Narrative Summary */}
      {showNarrative && (
        <div className="narrative-card animate-in" style={{animationDelay: "50ms"}}>
          <h3>Executive Summary</h3>
          <div className="narrative-content">
            {audit.narrative_summary?.split('\n\n').map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        </div>
      )}

      {/* Processing State */}
      {isProcessing && (
        <div className="processing-card">
          <div className="processing-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <div className="processing-content">
            <h3>Audit {audit.status === "queued" ? "Queued" : "Processing"}</h3>
            <p>This typically takes 30-90 seconds for a 10,000-row dataset.</p>
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {audit.status === "failed" && audit.error_message && (
        <div className="error-state-card">
          <div className="error-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M15 9l-6 6M9 9l6 6"/>
            </svg>
          </div>
          <div>
            <h4>Audit Failed</h4>
            <p>{audit.error_message}</p>
          </div>
        </div>
      )}

      {/* Audit Metadata Bar */}
      <div className="audit-metadata-bar animate-in" style={{animationDelay: "100ms"}}>
        <div className="metadata-item">
          <span className="metadata-label">Dataset Size</span>
          <span className="metadata-value">{audit.dataset_row_count?.toLocaleString() ?? "-"} rows</span>
        </div>
        <div className="metadata-divider"></div>
        <div className="metadata-item">
          <span className="metadata-label">Started</span>
          <span className="metadata-value">{formatDate(audit.started_at)}</span>
        </div>
        <div className="metadata-divider"></div>
        <div className="metadata-item">
          <span className="metadata-label">Completed</span>
          <span className="metadata-value">{formatDate(audit.completed_at)}</span>
        </div>
        <div className="metadata-divider"></div>
        <div className="metadata-item">
          <span className="metadata-label">Protected Attributes</span>
          <span className="metadata-value">{audit.protected_attributes?.length ?? 0} defined</span>
        </div>
      </div>

      {/* Metric Results Table */}
      {audit.results.length > 0 && (
        <div className="results-section animate-in" style={{animationDelay: "150ms"}}>
          <h3>Metric Results</h3>
          <div className="card table-card">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Attribute</th>
                  <th>Disparity</th>
                  <th>95% CI</th>
                  <th>p-value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody className="animate-in-stagger">
                {audit.results.map((result, index) => (
                  <tr key={`${result.metric_name}-${result.protected_attribute}-${index}`}>
                    <td className="metric-name">{result.metric_name}</td>
                    <td>{result.protected_attribute}</td>
                    <td className="metric-value">{formatNumber(result.disparity)}</td>
                    <td className="metric-ci">
                      [{formatNumber(result.confidence_interval_lower)}, {formatNumber(result.confidence_interval_upper)}]
                    </td>
                    <td className="metric-pvalue">{formatNumber(result.p_value)}</td>
                    <td><StatusBadge value={result.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {audit.recommendations.length > 0 && (
        <div className="recommendations-section animate-in" style={{animationDelay: "200ms"}}>
          <h3>Recommendations</h3>
          <div className="recommendations-list animate-in-stagger">
            {audit.recommendations.map((item, index) => (
              <div key={`${item.issue}-${index}`} className="recommendation-card">
                <div className="recommendation-header">
                  <StatusBadge value={item.priority} />
                  <span className="effort-tag">{item.implementation_effort}</span>
                </div>
                <h4>{item.issue}</h4>
                <p className="mitigation">
                  {item.mitigation_strategy_enriched ?? item.mitigation_strategy}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verified Pass State */}
      {audit.overall_verdict === "PASS" && audit.recommendations.length === 0 && !isProcessing && (
        <div className="verified-pass-state animate-in" style={{animationDelay: "200ms"}}>
          <div className="verified-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
              <path d="M8 12l3 3 5-5"/>
            </svg>
          </div>
          <h3>Audit Verified: PASS</h3>
          <p>The model prediction dataset has been rigorously tested against all specified fairness metrics. No significant disparity was detected across the protected attributes.</p>
          <div className="verification-badge">Certified Compliance Ready</div>
        </div>
      )}
    </section>
  );
}
