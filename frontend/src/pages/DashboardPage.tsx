import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../hooks/useApi";
import { formatDate } from "../utils/format";
import type { AuditListResponse } from "../utils/types";
import { StatusBadge } from "../components/StatusBadge";

interface DashboardStats {
  totalAudits: number;
  passRate: number;
  pendingCount: number;
  failCount: number;
}

export function DashboardPage() {
  const [data, setData] = useState<AuditListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState<DashboardStats>({
    totalAudits: 0,
    passRate: 0,
    pendingCount: 0,
    failCount: 0,
  });

  useEffect(() => {
    let active = true;
    apiFetch<AuditListResponse>(`/audits?page=${page}&per_page=10`)
      .then((response) => {
        if (!active) return;
        setData(response);
        setError(null);
        
        // Calculate stats from loaded audits
        const audits = response.audits;
        const completed = audits.filter(a => a.status === "completed");
        const passed = completed.filter(a => a.overall_verdict === "PASS");
        const pending = audits.filter(a => a.status === "queued" || a.status === "processing");
        const failed = audits.filter(a => a.overall_verdict === "FAIL");
        
        setStats({
          totalAudits: response.total,
          passRate: completed.length > 0 ? Math.round((passed.length / completed.length) * 100) : 0,
          pendingCount: pending.length,
          failCount: failed.length,
        });
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load audits");
      });
    return () => { active = false; };
  }, [page]);

  const audits = data?.audits ?? [];

  return (
    <section className="dashboard">
      {/* Header with prominent CTA */}
      <div className="dashboard-header">
        <div>
          <h2>Dashboard</h2>
          <p className="dashboard-subtitle">Monitor your fairness audits</p>
        </div>
        <Link to="/audits/new" className="btn-primary-large">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          New Audit
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon total">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-value">{stats.totalAudits}</span>
            <span className="kpi-label">Total Audits</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon pass">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <path d="M22 4L12 14.01l-3-3"/>
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-value">{stats.passRate}%</span>
            <span className="kpi-label">Pass Rate</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon pending">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-value">{stats.pendingCount}</span>
            <span className="kpi-label">Pending</span>
          </div>
        </div>
        
        <div className="kpi-card">
          <div className="kpi-icon fail">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M15 9l-6 6M9 9l6 6"/>
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-value">{stats.failCount}</span>
            <span className="kpi-label">Failed</span>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error ? <div className="error-banner">{error}</div> : null}

      {/* Audit Cards List */}
      <div className="audits-section">
        <div className="section-header">
          <h3>Recent Audits</h3>
          {data && data.total > 10 && (
            <div className="pagination pagination-compact">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                Previous
              </button>
              <span>Page {page}</span>
              <button onClick={() => setPage((p) => p + 1)} disabled={!data || data.audits.length < 10}>
                Next
              </button>
            </div>
          )}
        </div>

        {audits.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                <path d="M12 11v6M9 14h6"/>
              </svg>
            </div>
            <h4>No audits yet</h4>
            <p>Run your first fairness check to see results here.</p>
            <Link to="/audits/new" className="btn-primary">
              Create Your First Audit
            </Link>
          </div>
        ) : (
            <div className="audit-cards">
            {audits.map((audit) => (
              <Link key={audit.audit_id} to={`/audits/${audit.audit_id}`} className="audit-card">
                <div className="audit-card-main">
                  <span className="audit-model">{audit.model_name}</span>
                  <div className="audit-card-badges">
                    {audit.groq_enriched && <span className="ai-badge-small">AI</span>}
                    <StatusBadge value={audit.overall_verdict} large />
                  </div>
                </div>
                <div className="audit-card-meta">
                  <StatusBadge value={audit.status} />
                  <span className="audit-date">{formatDate(audit.created_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
