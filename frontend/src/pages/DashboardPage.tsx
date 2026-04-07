import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../hooks/useApi";
import { formatDate } from "../utils/format";
import type { AuditListResponse } from "../utils/types";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const [data, setData] = useState<AuditListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    let active = true;
    apiFetch<AuditListResponse>(`/audits?page=${page}&per_page=10`)
      .then((response) => {
        if (!active) {
          return;
        }
        setData(response);
        setError(null);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load audits");
      });
    return () => {
      active = false;
    };
  }, [page]);

  const audits = data?.audits ?? [];

  return (
    <section>
      <div className="header-row">
        <h2>Audit Dashboard</h2>
        <Link className="button-link" to="/audits/new">
          New Audit
        </Link>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Status</th>
              <th>Verdict</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {audits.map((audit) => (
              <tr key={audit.audit_id}>
                <td>{audit.model_name}</td>
                <td>
                  <StatusBadge value={audit.status} />
                </td>
                <td>
                  <StatusBadge value={audit.overall_verdict} />
                </td>
                <td>{formatDate(audit.created_at)}</td>
                <td>
                  <Link to={`/audits/${audit.audit_id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
          Prev
        </button>
        <span>Page {page}</span>
        <button onClick={() => setPage((p) => p + 1)} disabled={!!data && data.audits.length < 10}>
          Next
        </button>
      </div>
    </section>
  );
}
