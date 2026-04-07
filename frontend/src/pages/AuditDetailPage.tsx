import { useParams } from "react-router-dom";

import { StatusBadge } from "../components/StatusBadge";
import { usePollAudit } from "../hooks/usePollAudit";
import { formatDate, formatNumber } from "../utils/format";

export function AuditDetailPage() {
  const { id } = useParams();
  const { audit, error } = usePollAudit(id);

  if (error) {
    return <p className="error">{error}</p>;
  }
  if (!audit) {
    return <p>Loading audit...</p>;
  }

  return (
    <section>
      <div className="header-row">
        <h2>Audit Results</h2>
        <StatusBadge value={audit.overall_verdict ?? audit.status} />
      </div>

      <div className="card">
        <p><strong>Status:</strong> <StatusBadge value={audit.status} /></p>
        <p><strong>Rows:</strong> {audit.dataset_row_count ?? "-"}</p>
        <p><strong>Started:</strong> {formatDate(audit.started_at)}</p>
        <p><strong>Completed:</strong> {formatDate(audit.completed_at)}</p>
        {audit.error_message ? <p className="error">{audit.error_message}</p> : null}
      </div>

      <div className="card table-wrap">
        <h3>Metric Results</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Attribute</th>
              <th>Disparity</th>
              <th>CI</th>
              <th>p-value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {audit.results.map((result, index) => (
              <tr key={`${result.metric_name}-${result.protected_attribute}-${index}`}>
                <td>{result.metric_name}</td>
                <td>{result.protected_attribute}</td>
                <td>{formatNumber(result.disparity)}</td>
                <td>{formatNumber(result.confidence_interval_lower)} - {formatNumber(result.confidence_interval_upper)}</td>
                <td>{formatNumber(result.p_value)}</td>
                <td><StatusBadge value={result.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Recommendations</h3>
        <ul className="recommendations">
          {audit.recommendations.map((item, index) => (
            <li key={`${item.issue}-${index}`}>
              <StatusBadge value={item.priority} />
              <p><strong>{item.issue}</strong></p>
              <p>{item.mitigation_strategy}</p>
              <small>Effort: {item.implementation_effort}</small>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
