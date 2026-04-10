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
  completedCount: number;
}

export function DashboardPage() {
  const [data, setData] = useState<AuditListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState<DashboardStats>({
    totalAudits: 0,
    passRate: 0,
    pendingCount: 0,
    failCount: 0,
    completedCount: 0,
  });

  useEffect(() => {
    let active = true;
    apiFetch<AuditListResponse>(`/audits?page=${page}&per_page=10`)
      .then((response) => {
        if (!active) return;
        setData(response);
        setError(null);
        setLoading(false);
        
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
          completedCount: completed.length,
        });
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load audits");
        setLoading(false);
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

      {/* Summary Metrics */}
      {loading ? (
        <div className="summary-metrics">
          <div className="metric-main shimmer" style={{ width: '100%', height: 120, borderRadius: 8 }} />
          <div className="metric-sub-grid">
            {[1, 2, 3].map((i) => (
              <div key={i} className="metric-sub-card shimmer" style={{ width: '100%', height: 80, borderRadius: 8 }} />
            ))}
          </div>
        </div>
      ) : (
        <div className="summary-metrics">
          <div className="metric-main">
            <div className="metric-header">
              <span className="metric-label">Overall Pass Rate</span>
              <div className="metric-status-pill" style={{ color: 'var(--color-pass)', backgroundColor: 'var(--color-pass-bg)' }}>
                Healthy
              </div>
            </div>
            <div className="metric-value-large">{stats.passRate}%</div>
            <div className="metric-footer">
              Based on {stats.completedCount} completed audits
            </div>
          </div>
          <div className="metric-sub-grid">
            <div className="metric-sub-card">
              <span className="metric-label">Total Audits</span>
              <span className="metric-value">{stats.totalAudits}</span>
            </div>
            <div className="metric-sub-card">
              <span className="metric-label">Pending</span>
              <span className="metric-value">{stats.pendingCount}</span>
            </div>
            <div className="metric-sub-card">
              <span className="metric-label">Failed</span>
              <span className="metric-value" style={{ color: 'var(--color-fail)' }}>{stats.failCount}</span>
            </div>
          </div>
        </div>
      )}

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

        {loading ? (
          <div className="audit-cards">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="audit-card">
                <div className="audit-card-main">
                  <span className="audit-model shimmer" style={{ width: 150, height: 20, borderRadius: 4 }} />
                  <div className="audit-card-badges">
                    <span className="shimmer" style={{ width: 40, height: 24, borderRadius: 12 }} />
                    <span className="shimmer" style={{ width: 50, height: 24, borderRadius: 12 }} />
                  </div>
                </div>
                <div className="audit-card-meta">
                  <span className="shimmer" style={{ width: 70, height: 20, borderRadius: 4 }} />
                  <span className="shimmer" style={{ width: 100, height: 16, borderRadius: 4 }} />
                </div>
              </div>
            ))}
          </div>
        ) : audits.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
                <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2"/>
              </svg>
            </div>
            <h4>No Fairness Audits Detected</h4>
            <p>Your dashboard is empty. Start by uploading a model prediction dataset to analyze fairness and compliance across your protected attributes.</p>
            <Link to="/audits/new" className="btn-primary">
              Run Your First Audit
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
