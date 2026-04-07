# ML Fairness Audit Platform — MVP Specification

## 1. Product Scope

FairLens is a web application that lets ML engineers, model risk managers, and compliance officers upload model prediction data, run automated statistical fairness tests against protected demographic attributes, and receive a structured PASS / CONDITIONAL_PASS / FAIL verdict alongside an audit-ready report. It targets financial services teams subject to EU AI Act, US ECOA, UK FCA, and Singapore MAS FEAT fairness requirements. PASS / CONDITIONAL_PASS / FAIL in FairLens is a statistical audit classification for configured metrics and thresholds, not a legal compliance determination. It does not train, retrain, or deploy models. It does not provide legal compliance certification. It does not perform real-time inference monitoring. The single workflow it makes dramatically easier: a compliance officer today spends two to four weeks coordinating between data scientists, risk managers, and legal to manually compute fairness metrics, interpret results, and assemble regulatory documentation. FairLens compresses that into a single upload-and-review session that produces examiner-ready output in under five minutes.

## 2. Architecture Decision Record

| Component | Decision | Rationale | Tradeoff |
|---|---|---|---|
| Runtime | Python 3.12 | NumPy, pandas, scipy, and fairlearn are all Python-native; no viable alternative for statistical computation at this complexity. | Front-end developers need a separate mental model; mitigated by clear API boundary. |
| Back-end Framework | FastAPI | Async-native, automatic OpenAPI docs, Pydantic validation, and first-class support for background tasks. Lean enough for single-deploy. | Smaller ecosystem than Django; no built-in admin panel. |
| Front-end | React 18 + Vite | Fast build times, large component ecosystem, strong TypeScript support. Vite's build output drops into FastAPI's static directory for single-deploy. | Heavier than a server-rendered approach; justified by the dense interactive dashboard requirement. |
| Database | SQLite (Phase 1–2) with a migration path to PostgreSQL (Phase 3) | Zero-config for prototype; SQLAlchemy ORM abstracts the switch. Alembic manages schema migrations identically for both engines. | SQLite has limited concurrent write throughput; acceptable for ≤10 concurrent users in Phase 1–2. |
| Job Queue | ARQ (async Redis queue) | Lightweight, Python-native, async-first. Single `redis` dependency. Avoids the Celery + RabbitMQ operational weight for a prototype. | Less battle-tested than Celery at high scale; sufficient for ≤50 concurrent jobs. |
| File Storage | Local filesystem (Phase 1–2), S3-compatible (Phase 3) | Uploaded CSVs are ephemeral — processed and deleted. Results are stored in DB. Local disk is simplest for single-deploy. | Not horizontally scalable; Phase 3 migration to S3/MinIO is pre-planned. |
| Auth | API key auth (Phase 1), session-based auth with bcrypt (Phase 2), RBAC (Phase 3) | API keys are the lowest-friction auth for a prototype used by technical users. Session auth adds UI login. RBAC adds enterprise role separation. | No SSO/OIDC until Phase 3+; acceptable for an internal tool during early adoption. |
| Deployment | Single app service URL on Render.com or Railway, with Redis as required backing service | `Dockerfile` builds the React app, copies the bundle into FastAPI's `/static` directory, and runs `uvicorn`; ARQ requires Redis but users still access one app URL. | No CDN for static assets; acceptable for internal/pilot use. |

## 3. Core Data Model

```
Entity: User
  id: uuid                   — Primary key; avoids sequential enumeration.
  email: string, unique      — Login identifier; also used for audit attribution.
  name: string               — Display name in the UI and on generated reports.
  hashed_password: string    — bcrypt hash; null in Phase 1 (API-key-only auth).
  api_key: string, unique    — Bearer token for API access; generated on account creation.
  role: enum [admin, analyst, viewer]  — Controls access level; enforced from Phase 3.
  created_at: datetime       — Account creation timestamp for audit trail.
  is_active: boolean         — Soft-delete flag; deactivated users cannot authenticate.

Entity: Model
  id: uuid                   — Primary key.
  user_id: uuid → User.id    — Owner; scopes visibility in multi-tenant queries.
  name: string               — Human-readable model identifier (e.g., "Credit Scoring v3.1").
  use_case: enum [credit_approval, fraud_detection, underwriting, insurance, other]
                             — Drives metric recommendation logic and report template selection.
  description: string, nullable  — Optional context for the report's model summary section.
  created_at: datetime       — Tracks when the model was registered.

Entity: Audit
  id: uuid                   — Primary key; also serves as the job reference for the queue.
  model_id: uuid → Model.id  — The model being audited.
  user_id: uuid → User.id    — The user who initiated the audit; logged for attribution.
  status: enum [queued, processing, completed, failed]
                             — Job lifecycle state; polled by the front-end and returned by the API.
  overall_verdict: enum [PASS, CONDITIONAL_PASS, FAIL], nullable
                             — Set when status transitions to "completed." Null while processing.
                             — Deterministic policy: PASS if zero metric results fail; CONDITIONAL_PASS if failed results are >0 and <=25% of computed metric-by-attribute results; FAIL otherwise.
  verdict_metadata: json, nullable
                             — Structured verdict traceability payload:
                               `{ failed_result_count: integer, total_result_count: integer, policy_version: string, computed_at: datetime }`.
                               Required when `overall_verdict` is non-null.
  dataset_row_count: integer, nullable
                             — Total rows in the uploaded dataset; shown in results summary.
  protected_attributes: json — Array of objects: [{name, type, privileged_group, unprivileged_group}].
                               Stored as JSON because the shape varies per audit and is read-only after creation.
  selected_metrics: json     — Array of metric identifiers the user chose (e.g., ["demographic_parity", "equalized_odds"]).
  file_path: string          — Temporary path to the uploaded CSV. Deleted after processing completes.
  ground_truth_column: string, nullable  — Column name for labels; null if not provided (some metrics skipped).
  prediction_column: string  — Column name containing model predictions or scores.
  error_message: string, nullable  — Human-readable failure reason if status is "failed."
  started_at: datetime, nullable    — When the job worker began processing.
  completed_at: datetime, nullable  — When processing finished (success or failure).
  created_at: datetime       — When the audit was submitted.

Entity: FairnessResult
  id: uuid                   — Primary key.
  audit_id: uuid → Audit.id  — Parent audit; one audit produces multiple results (one per metric × attribute pair).
  metric_name: string        — e.g., "demographic_parity." Matches the metric catalog identifiers.
  protected_attribute: string — The attribute this result pertains to (e.g., "gender").
  privileged_value: float    — Metric value for the privileged group.
  unprivileged_value: float  — Metric value for the unprivileged group.
  disparity: float           — Absolute difference or ratio between groups (metric-dependent).
  threshold: float           — The pass/fail boundary for this metric. Configurable; defaults from regulatory guidance.
  status: enum [PASS, FAIL]  — Whether disparity exceeds threshold.
  confidence_interval_lower: float  — Lower bound of the 95% bootstrap CI.
  confidence_interval_upper: float  — Upper bound of the 95% bootstrap CI.
  p_value: float             — Permutation test p-value for statistical significance.
  sample_size_privileged: integer   — Row count for the privileged group; flags small-sample warnings.
  sample_size_unprivileged: integer — Row count for the unprivileged group.
  interpretation: string     — One-sentence plain-language explanation (generated, not LLM).

Entity: Recommendation
  id: uuid                   — Primary key.
  audit_id: uuid → Audit.id  — Parent audit.
  priority: enum [high, medium, low]  — Triage level shown in the report.
  issue: string              — What the problem is, in plain language.
  mitigation_strategy: string — Specific remediation action (e.g., "Resample training data to equalize base rates").
  implementation_effort: enum [low, medium, high]  — Rough sizing for the model team.
  created_at: datetime       — Timestamp for audit trail ordering.

Entity: AuditLog
  id: uuid                   — Primary key.
  user_id: uuid → User.id, nullable  — Who performed the action; null for system-initiated events.
  action: string             — Machine-readable action code (e.g., "audit.created", "report.downloaded", "user.login").
  resource_type: string      — Entity type affected (e.g., "Audit", "Model").
  resource_id: uuid          — ID of the affected entity.
  details: json, nullable    — Additional context (e.g., changed fields, request IP, user agent).
  created_at: datetime       — Immutable timestamp; AuditLog rows are append-only and never updated or deleted.
```

**Relationships summary:** A User owns many Models. A Model has many Audits. An Audit has many FairnessResults and many Recommendations. Every state-changing action across all entities writes an AuditLog entry.

## 4. Project Scaffolding

```
fairlens-platform/
├── backend/                    # All Python server code
│   ├── api/                    # FastAPI route handlers, grouped by domain (audits, models, auth)
│   ├── core/                   # App config, security utilities, error handlers, dependency injection
│   ├── db/                     # SQLAlchemy models, Alembic migrations, session management
│   ├── engine/                 # Fairness metric computation, statistical tests, result interpretation
│   ├── jobs/                   # ARQ worker definitions and task functions for async audit processing
│   ├── reports/                # PDF and JSON report generation logic and templates
│   └── schemas/                # Pydantic request/response models shared between API and engine
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── components/         # Reusable UI components (tables, status badges, file uploader)
│   │   ├── pages/              # Route-level page components (Dashboard, AuditDetail, NewAudit)
│   │   ├── hooks/              # Custom React hooks for API calls and polling
│   │   ├── styles/             # Global CSS, design tokens, component-specific stylesheets
│   │   └── utils/              # Formatters, constants, type definitions
│   └── public/                 # Static assets (favicon, fonts)
├── tests/                      # Pytest suites mirroring backend structure
├── sample-data/                # Bundled demo CSVs for first-run experience
├── Dockerfile                  # Multi-stage: build frontend, install backend deps, serve with uvicorn
├── docker-compose.yml          # Local dev: app + Redis
├── alembic.ini                 # Database migration configuration
├── pyproject.toml              # Python dependency management (uv/pip)
└── README.md                   # Setup, local dev, and deployment instructions
```

## 5. Phase 1 — Runnable Audit Core

### Goal

A single user can upload a CSV of model predictions, configure an audit, and receive a PASS/FAIL verdict with per-metric disparity scores and confidence intervals, all through a working web interface.

### Included Features

1. User can register an account and receive an API key for programmatic access (Phase 1 auth baseline).
2. User can register a model by providing its name, use case category, and optional description.
3. User can upload a CSV file, select protected attributes and metrics, and submit a fairness audit that runs asynchronously.
4. User can view a live-updating status indicator while the audit processes, then see the full results — overall verdict, per-metric disparity scores, confidence intervals, p-values, and plain-language interpretations — on a single results page.
5. User can view a dashboard listing all their past audits with status, verdict, model name, and date, sorted most-recent-first.
6. User can view a built-in reference of available fairness metrics with definitions, use-case guidance, and limitations.

### Excluded (with reason)

| Feature | Why Excluded |
|---|---|
| PDF report generation | High implementation cost (templating, layout, fonts). JSON results are sufficient for Phase 1; PDF added in Phase 3 when compliance officers are onboarded. |
| LLM-powered explanations | Adds an external API dependency, prompt engineering burden, and hallucination risk. Rule-based interpretations cover Phase 1 needs. |
| Metric selection wizard | Interactive questionnaire is a UX luxury; a static reference page with clear guidance achieves 80% of the value at 10% of the cost. |
| Webhook callbacks on audit completion | No known Phase 1 user has a system to receive webhooks. Front-end polling covers the use case. |
| Auto-detection of protected attributes | Requires heuristic column-name matching that produces false positives. Explicit user selection is more trustworthy and simpler. |

### API Surface

**1. POST /api/v1/auth/register**
- Request: `{ email: string, name: string, password: string }`
- Response: `{ user_id: uuid, api_key: string }`
- Registers a new user account and returns the API key.

**2. POST /api/v1/models**
- Request: `{ name: string, use_case: string, description: string | null }`
- Response: `{ model_id: uuid, name: string, use_case: string, created_at: datetime }`
- Registers a model for auditing.

**3. POST /api/v1/audits**
- Request: `multipart/form-data` with fields: `{ model_id: uuid, file: binary (CSV), prediction_column: string, ground_truth_column: string | null, protected_attributes: json, selected_metrics: json }`
- Response: `{ audit_id: uuid, status: "queued", created_at: datetime }`
- Uploads the dataset, validates the schema, enqueues the audit job.

**4. GET /api/v1/audits/{audit_id}**
- Request: path parameter `audit_id: uuid`
- Response: `{ audit_id: uuid, status: string, overall_verdict: string | null, dataset_row_count: integer | null, results: [FairnessResult], recommendations: [Recommendation], error_message: string | null, started_at: datetime | null, completed_at: datetime | null }`
- Returns current audit status and results if completed.

**5. GET /api/v1/audits**
- Request: query parameters `{ page: integer, per_page: integer }`
- Response: `{ audits: [{ audit_id, model_name, status, overall_verdict, created_at }], total: integer, page: integer }`
- Lists all audits for the authenticated user, paginated.

**6. GET /api/v1/metrics**
- Request: none
- Response: `{ metrics: [{ name: string, display_name: string, category: string, description: string, use_cases: [string], limitations: [string], requires_ground_truth: boolean }] }`
- Returns the catalog of available fairness metrics.

### Metric Reproducibility Contract (Phase 1)

To make the "match Fairlearn within +/-0.01" acceptance criterion testable and stable:

1. **Prediction input semantics**
   - `prediction_column` is treated as a score/probability in `[0,1]` for calibration.
   - For classification-style metrics (demographic parity, equalized odds, predictive equality), scores are binarized at threshold `>= 0.5`.

2. **Ground truth semantics**
   - `ground_truth_column` must be binary (`0`/`1`) for metrics requiring labels.
   - Non-binary labels are rejected with actionable validation error.

3. **Metric definitions**
   - **Demographic parity:** absolute difference in positive prediction rates between privileged and unprivileged groups.
   - **Equalized odds:** `max(|TPR_diff|, |FPR_diff|)`.
   - **Calibration:** maximum bucket-level absolute difference in observed positive rate across groups.
   - **Predictive equality:** absolute difference in false positive rates.

4. **Statistical test defaults**
   - Bootstrap CI confidence level: `95%`.
   - Bootstrap iterations: `1000` (default).
   - Permutation iterations: `1000` (default).
   - Default RNG seed for deterministic reproducibility: `42`.

5. **Bucket policy (calibration)**
   - `10` equal-width buckets over `[0,1]`.
   - Buckets with fewer than `5` samples in either group are skipped.
   - If all buckets are skipped, calibration disparity defaults to `0.0` and result is flagged in interpretation text as low-sample limitation.

6. **Overall verdict aggregation**
   - PASS: `0` failed metric-by-attribute results.
   - CONDITIONAL_PASS: failed results are `>0` and `<=25%` of computed metric-by-attribute results.
   - FAIL: failed results `>25%` of computed metric-by-attribute results.
   - The audit record stores `failed_result_count` and `total_result_count` in `Audit.verdict_metadata` for traceability.

### Job Execution Contract (Phase 1)

To make async runtime targets and queue behavior deterministic:

1. **Queue and worker settings**
   - Queue backend: Redis.
   - Worker max concurrent jobs per worker process: `10` (Phase 1 default).
   - Deployment baseline for performance targets: one worker on `8 vCPU` class compute.

2. **Timeout and retries**
   - Hard job timeout: `180` seconds.
   - Retry policy: `0` automatic retries for deterministic audit output; failures return actionable error and require user resubmission.

3. **Resource and payload constraints**
   - Maximum upload size: `500 MB`.
   - CSV must include all declared required columns before enqueue finalization.
   - Files are deleted after processing completes (success or failure).

4. **State transitions**
   - Required lifecycle: `queued -> processing -> completed|failed`.
   - `started_at` set at transition to `processing`.
   - `completed_at` set on both `completed` and `failed`.
   - `error_message` required when status is `failed`.

5. **Polling and UX contract**
   - Frontend polling interval: `<= 5` seconds while status is `queued` or `processing`.
   - Result endpoint must remain idempotent and return latest persisted state.

6. **Queue outage behavior (submission path)**
   - If Redis is unavailable at audit submission time, `POST /api/v1/audits` returns `503 Service Unavailable` with machine-readable code `queue_unavailable` and actionable remediation text.
   - In this `503` path, no queued audit record is created; partial state is rolled back.
   - The failure is still recorded in `AuditLog` with action `audit.enqueue_failed`.

### Database Migration and Runtime Contract (Phase 1)

1. **Schema authority**
   - Database schema changes are applied through Alembic revisions only.
   - Every model/schema change requires a corresponding Alembic revision.

2. **Runtime behavior**
   - Production startup must not use runtime auto-create (`create_all`) for schema management.
   - Production startup sequence is: `alembic upgrade head` before app boot.
   - If DB revision is behind expected head, app startup fails fast with explicit migration-required error.

3. **Environment split**
   - Local dev may use a one-time bootstrap path, but CI/staging/prod must always run Alembic migrations.
   - Migration parity is validated in CI by asserting revision head matches application expectation.

### Front-End Views

**1. Registration (Phase 1)**
- URL: `/register`
- Primary action: Create account and issue API key.
- Key UI elements:
  - Email and password form fields
  - API key display on successful registration (copy-to-clipboard)
  - Optional link to login view marked "Phase 2 session auth"

**2. Dashboard**
- URL: `/`
- Primary action: See all audits at a glance and navigate to details.
- Key UI elements:
  - Table of audits with columns: Model, Status (color-coded badge), Verdict (PASS green / CONDITIONAL_PASS amber / FAIL red), Date
  - "New Audit" button
  - Pagination controls

**3. New Audit**
- URL: `/audits/new`
- Primary action: Configure and submit a fairness audit.
- Key UI elements:
  - Model selector (dropdown of registered models, or inline "create new" form)
  - CSV file upload zone (drag-and-drop, with file size and format validation feedback)
  - Column mapper: dropdowns for prediction column and optional ground truth column, populated from CSV headers after upload
  - Protected attribute configurator: add rows specifying attribute column, type, privileged group, unprivileged group
  - Metric selector: checkbox list with inline descriptions

**4. Audit Detail / Results**
- URL: `/audits/:id`
- Primary action: Review audit verdict and per-metric results.
- Key UI elements:
  - Overall verdict badge (large, prominent, color-coded)
  - Status progress indicator (queued → processing → completed, with auto-refresh)
  - Results table: one row per metric × attribute, showing disparity value, CI range, p-value, status badge
  - Recommendations panel: prioritized list with issue, mitigation, and effort level
  - Dataset summary: row count, attribute distributions

**5. Metric Reference**
- URL: `/metrics`
- Primary action: Learn which metrics to select for a given use case.
- Key UI elements:
  - Card per metric: name, definition, when to use, limitations, academic reference
  - Use-case filter tabs (credit, fraud, underwriting)

### Acceptance Criteria

- A user can register, create a model, upload a CSV, submit an audit, and see a PASS/FAIL verdict — the full Phase 1 happy path — in under 3 minutes of wall-clock time for a 10,000-row dataset.
- Demographic parity, equalized odds, calibration, and predictive equality metrics produce results that match Fairlearn's output within a ±0.01 tolerance on the bundled sample datasets.
- A 100,000-row CSV audit completes end-to-end (upload through verdict) in under 90 seconds.
- The results page displays confidence intervals and p-values for every metric × attribute combination.
- An upload of a malformed CSV (wrong columns, non-numeric predictions, missing required fields) returns a specific, actionable error message within 2 seconds — not a stack trace.
- The dashboard correctly reflects audit status transitions in near real-time (polling interval ≤ 5 seconds).
- All state-changing API calls (register, create model, submit audit) write an entry to the AuditLog table.
- The application is accessible at one URL on Render.com, with Redis configured as a required backing service for the async queue.

## 6. Phase 2 — Audit Intelligence

### Goal

Users can compare fairness results across model versions, receive guided metric recommendations, and view historical trends, turning FairLens from a one-shot tool into a continuous model governance workflow.

### Added Features

1. User can compare two audits of the same model side-by-side, with metric deltas highlighted as improvements or regressions.
2. User can answer a three-question wizard (use case, regulatory jurisdiction, whether ground truth is available) and receive a recommended set of metrics with rationale.
3. User can view a trend chart showing how a model's fairness metrics have changed across audits over time.
4. User can receive rule-based remediation recommendations that are specific to the detected failure mode (e.g., resampling for demographic parity failure vs. threshold adjustment for equalized odds failure).
5. User can log in with email and password through a session-based auth flow, with the API key auth preserved for programmatic access.

### API Surface Changes

**1. GET /api/v1/audits/{audit_id_a}/compare/{audit_id_b}**
- Request: two audit ID path parameters
- Response: `{ model_name: string, audit_a_summary: { verdict, date, metrics: [{name, disparity, status}] }, audit_b_summary: { same shape }, deltas: [{ metric_name, attribute, disparity_change: float, direction: "improved" | "regressed" | "unchanged" }] }`
- Returns a structured comparison of two audits.

**2. POST /api/v1/metrics/recommend**
- Request: `{ use_case: string, jurisdiction: string, has_ground_truth: boolean }`
- Response: `{ recommended_metrics: [{ name: string, rationale: string }], warnings: [string] }`
- Returns recommended metrics based on user context.

**3. GET /api/v1/models/{model_id}/trends**
- Request: query parameters `{ metric_name: string, attribute: string }`
- Response: `{ model_name: string, data_points: [{ audit_id: uuid, date: datetime, disparity: float, verdict: string }] }`
- Returns time-series data for a specific metric and attribute across all audits of a model.

**4. POST /api/v1/auth/login**
- Request: `{ email: string, password: string }`
- Response: `{ session_token: string, user: { id, email, name } }`
- Creates a session for browser-based authentication.

### Front-End View Changes

**1. Comparison View (new)**
- URL: `/audits/:id_a/compare/:id_b`
- Primary action: Identify which metrics improved or regressed between two model versions.
- Key UI elements:
  - Two-column layout: Audit A on left, Audit B on right
  - Delta column between them with green (improved) / red (regressed) arrows and magnitude
  - Model name and audit dates in the header
  - Link back to individual audit detail pages

**2. Model Detail with Trends (new)**
- URL: `/models/:id`
- Primary action: Monitor fairness trajectory over time.
- Key UI elements:
  - Line chart: X-axis is audit date, Y-axis is disparity value, one line per metric
  - Threshold reference line for visual pass/fail boundary
  - Table of all audits for this model below the chart
  - "Compare" button that lets user select two audits from the table

**3. Metric Wizard (new)**
- URL: `/metrics/wizard`
- Primary action: Get a recommended metric set based on context.
- Key UI elements:
  - Three-step form: use case (dropdown), jurisdiction (dropdown), ground truth available (yes/no toggle)
  - Results card showing recommended metrics with one-line rationale each
  - Warning callout if selected metrics have known incompatibilities
  - "Use these metrics" button that pre-fills the New Audit form

**4. Dashboard (modified)**
- Added: model name filter dropdown. Added: "Compare" action on row selection (select two rows, click compare).

### Acceptance Criteria

- A user can select two audits of the same model and view a comparison page showing per-metric deltas within 2 seconds.
- The metric wizard produces correct recommendations for all three jurisdiction × use-case combinations tested against the regulatory compliance mapping in the source material.
- The trend chart renders correctly for a model with 10+ historical audits and updates immediately when a new audit completes.
- Recommendations for a demographic parity failure differ substantively from recommendations for an equalized odds failure — they are not generic.
- Session-based login works end-to-end: a user can log in via the UI, navigate all authenticated pages, and log out, with the session expiring after 24 hours of inactivity.
- All new state-changing actions (login, compare, wizard use) are captured in the AuditLog.

## 7. Phase 3 — Enterprise Readiness

### Goal

FairLens meets the compliance, security, and reporting requirements of an enterprise pilot, including role-based access control, PDF report export, and regulatory alignment documentation.

### Added Features

1. User with the admin role can assign roles (admin, analyst, viewer) to other users, controlling who can submit audits versus who can only view results.
2. User can download a PDF fairness audit report for any completed audit, formatted to the EU AI Act Annex IV technical documentation template, including executive summary, metric tables, limitations, recommendations, and methodology appendix.
3. User can view a regulatory coverage panel on each audit result that maps each tested metric to the specific regulatory requirement it satisfies (EU AI Act Article 9, ECOA Regulation B, FCA Fairness Principles, MAS FEAT).
4. User can configure the system to store uploaded files in an S3-compatible object store instead of local disk, enabling horizontal scaling.

### Regulatory Coverage

| Feature | Regulation | Specific Requirement |
|---|---|---|
| PDF report with Annex IV template sections | EU AI Act | Annex IV: Technical documentation for high-risk AI systems, including bias risk assessment, testing protocols, and limitations disclosure. |
| Demographic parity metric with disparate impact ratio | US ECOA / Regulation B | Demonstrate absence of disparate impact on protected classes (gender, age, race, marital status, national origin) in lending decisions. |
| Regulatory coverage panel mapping metrics to requirements | UK FCA | Demonstrate fairness, transparency, and accountability in consumer-facing model decisions. |
| Audit trail (AuditLog entity, immutable, append-only) | MAS FEAT / EU AI Act Article 9.5 | Accountability pillar: maintain records of testing decisions, methodology, and results for regulatory examination. |

### Acceptance Criteria

- A viewer-role user cannot submit audits or create models; the API returns 403 and the UI hides the relevant controls.
- The generated PDF report contains all six sections specified in the EU AI Act Annex IV template: model description, protected attributes tested, metrics with statistical significance, limitations, recommendations, and methodology appendix.
- The PDF generates in under 30 seconds for an audit with 100,000 rows and 4 protected attributes.
- The regulatory coverage panel correctly maps each metric to at least one regulation, and the mapping is consistent with the regulatory compliance documentation in the source material.
- Switching file storage from local to S3-compatible requires changing only environment variables, not code.

## 8. Non-Functional Requirements

| Requirement | Target | Measurement Method |
|---|---|---|
| Synchronous API response time (auth, model CRUD, audit list) | < 200ms at p95 | Load test with 20 concurrent users using k6 or locust; measure p95 latency. |
| Async audit job completion (10,000-row dataset, 4 metrics, 2 attributes) | < 30 seconds | Automated test: submit audit via API, poll until completed, measure elapsed time; baseline assumes 8 vCPU class worker and default statistical settings (bootstrap/permutation 1000 iterations each). |
| Async audit job completion (100,000-row dataset, 4 metrics, 4 attributes) | < 90 seconds | Same as above with larger dataset and same hardware/iteration assumptions. |
| Maximum upload file size | 500 MB | Server rejects uploads above limit with a 413 response and a message stating the limit. |
| Concurrent user support (Phase 1–2) | 10 simultaneous authenticated users with no degradation | Load test: 10 users each submitting one audit and polling for results concurrently. |
| Concurrent user support (Phase 3) | 50 simultaneous authenticated users | Same load test scaled to 50 users. |
| Audit log retention | Indefinite; logs are append-only and never deleted or modified | Verify via database constraint: no UPDATE or DELETE operations permitted on the AuditLog table. |
| Uptime (self-hosted, single instance) | 99% monthly | Render.com health check monitoring; alert on downtime > 7 hours/month. |

## 9. Out of Scope (MVP)

1. **Model training and retraining.** FairLens audits outputs; it does not modify models. Building a training pipeline is a different product.
2. **Real-time inference monitoring.** Continuous monitoring requires streaming infrastructure (Kafka, Flink) that exceeds the prototype's operational budget. Batch re-auditing via new CSV uploads covers the periodic monitoring use case.
3. **Custom metric builder.** Fewer than 10% of target users in the first six months will need metrics beyond the four core options. Adding a custom metric DSL is premature.
4. **Multi-language / i18n support.** All target users in the first two enterprise pilots operate in English. Localization adds translation maintenance cost with no near-term demand.
5. **SSO / OIDC integration.** Enterprise SSO requires per-customer identity provider configuration. API key + email/password auth is sufficient for pilot-stage onboarding; SSO is a post-MVP enterprise sales enablement feature.
6. **Automated bias remediation.** The product recommends mitigations; it does not apply them. Automated remediation requires access to the model training pipeline, which is outside the product boundary.
7. **Counterfactual fairness and individual fairness metrics.** These require causal model assumptions that most financial services teams are not prepared to specify. Adding them without adequate UX for causal graph input would produce unreliable results.
8. **Webhook callbacks for audit completion.** No Phase 1–3 user has a downstream system ready to consume webhooks. Front-end polling and email-on-completion (future) cover the notification need.

## Design Decisions Added

### Dashboard Information Hierarchy
Primary: "New Audit" button — prominent CTA, always visible in page header.
Secondary: Audit table — shows model name, status badge (color-coded), verdict (PASS/CONDITIONAL_PASS/FAIL), created date. Sorted most-recent-first.
Tertiary: Model filter dropdown — optional filtering by model.

### New Audit View Hierarchy
Primary: Model selector (dropdown or inline create) — user selects existing model or creates new one first.
Secondary: CSV file upload zone — drag-and-drop with file size/format validation feedback.
Tertiary: Column mapper — after upload, select prediction column and optional ground truth column.
Quaternary: Protected attribute configurator — add rows specifying attribute column, type, privileged/unprivileged groups.
Quinary: Metric selector — checkbox list with inline descriptions.

### Audit Detail View Hierarchy
Primary: Status progress indicator — queued → processing → completed, with auto-refresh (tell user what's happening first).
Secondary: Overall verdict badge — large, prominent, color-coded (green/amber/red), shown only when status is "completed".
Tertiary: Results table — per metric × attribute: disparity value, CI range, p-value, status badge.
Quaternary: Recommendations panel — prioritized list with issue, mitigation strategy, effort level.
Quinary: Dataset summary — row count, attribute distributions.

### Interaction State Specifications
| View | State | User Sees | Behavior |
|------|-------|-----------|----------|
| Dashboard | Empty | "No audits yet" warm message + "New Audit" CTA + 1-line FairLens explanation | — |
| Dashboard | Loading | Spinner in table body | Show after 200ms delay |
| Dashboard | Error | Error banner with retry button | Retry fetches latest list |
| New Audit | File Selected | Show column mapper, hide upload zone | Auto-populate column dropdowns |
| New Audit | Config Incomplete | Inline validation message | Disable Submit until valid |
| New Audit | Submitting | "Submitting..." disabled button + spinner | — |
| New Audit | Error | "Invalid CSV format" with specific error message | Highlight problematic field |
| Audit Detail | Processing | Status: "Processing..." + spinner + "This typically takes 30-90 seconds" | Auto-poll every 5s |
| Audit Detail | Failed | Error message + "Retry" button | Re-submit same config |
| Results | Partial | Show available results with "Processing remaining metrics..." banner | — |

### User Journey Storyboard — First-Time User

| Step | User Does | User Feels | UI Response |
|------|-----------|------------|--------------|
| 1 | Lands on `/register` | Curiosity, "another tool?" | Clean form, minimal distractions |
| 2 | Enters email/password, clicks Register | Anticipation | Immediate redirect |
| 3 | Sees API key displayed | Relief + need to copy | Copy button prominent, "Save this key" message |
| 4 | Auto-redirects to `/` dashboard | Slight confusion — "now what?" | Empty state with warm message + "New Audit" CTA + 1-line: "Upload model predictions to check for bias" |
| 5 | Clicks "New Audit" button | Ready to test | Model selector prominent, or "Create your first model" if none |
| 6 | Selects model, uploads CSV | Nervous — "did I do this right?" | Validation feedback: "Valid CSV, 10,000 rows detected" |
| 7 | Maps columns, selects attributes/metrics | Focused but uncertain | "3 metrics selected, ready to run" confirmation |
| 8 | Clicks Submit | Hope mixed with patience | Status: "Queued" + estimated time |
| 9 | Polling sees "processing" | Waiting | Progress: "Processing... typically 30-90 seconds" |
| 10 | Verdict appears | Relief (PASS) or concern (FAIL) | Verdict badge: large, color-coded |
| 11 | Reads results + recommendations | "What do I do now?" | Recommendations sorted by priority with effort estimate |

### Returning User Journey

| Step | User Does | User Feels | UI Response |
|------|-----------|------------|--------------|
| 1 | Lands on `/` dashboard | Purposeful — checking results | Table of audits, most recent first |
| 2 | Sees audit status "processing" | Waiting, checking progress | Status badge + auto-refresh |
| 3 | Clicks completed audit | Ready to review | Full results + recommendations |
| 4 | Clicks "New Audit" | Efficiency — knows flow | Pre-selected last-used model if exists |

### Design System Recommendation

**Run /design-consultation to create DESIGN.md before implementation.**

This would define:
- Color system: PASS/FAIL verdict colors, status badges, brand accent
- Typography scale: Font families, sizes for headings/body/captions
- Component library: Button styles, form inputs, table designs
- Spacing/grid: Base unit, component gaps, section margins
- Interaction patterns: Hover states, transitions, loading animations

Without DESIGN.md, implementers make ad-hoc decisions that won't be consistent.

### Responsive Specification (Required)

| View | Desktop (1200px+) | Tablet (768-1199px) | Mobile (320-767px) |
|------|-------------------|---------------------|---------------------|
| Dashboard | Table: full columns | Table: horizontal scroll or collapse date column | Card list: one audit per row |
| New Audit | Two-column: model left, upload right | Stacked: model above upload | Single column, full-width |
| Audit Detail | Full results table | Horizontal scroll table | Stacked: verdict → status → results cards |
| Navigation | Top nav bar | Hamburger menu | Hamburger menu |

### Responsive Breakpoints
- Mobile: 320px - 767px
- Tablet: 768px - 1199px  
- Desktop: 1200px+

### Touch Targets
- All buttons and interactive elements: minimum 44px height
- Table rows: minimum 48px height for tap target

### Color Contrast (Desktop-focused)
- PASS badge: verify contrast ratio ≥ 4.5:1
- FAIL badge: verify contrast ratio ≥ 4.5:1
- If not accessible, add text label alongside color

### Accessibility (Deferred / Not in Scope)
- Screen reader optimization: not required for MVP
- Keyboard navigation: basic support (Tab through forms)
- ARIA landmarks: skip for MVP

### Unresolved Design Decisions — Resolved

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| Empty state messaging | "No audits yet. Run your first fairness check to see results here." + "New Audit" CTA | Warm, actionable, explains value |
| Mobile navigation pattern | Hamburger icon in header, slide-out menu from right | Standard pattern, familiar to users |
| Verdict badge colors | PASS: Emerald 600 (#059669), FAIL: Rose 600 (#e11d48), CONDITIONAL_PASS: Amber 600 (#d97706) | High contrast, accessible with text labels |
| Table sorting defaults | Sort by created_at descending (most recent first) | Users want to see latest results |
| File upload progress | Percentage text + progress bar + "Uploading..." status | Clear feedback for large files |
| Results table pagination | 20 rows per page, sortable columns | Standard data table pattern |
| Error message style | Inline validation for forms, toast for async actions | Context-appropriate feedback |
| Status badge style | Pill-shaped, with icon + text (e.g., "✓ Completed") | Clear without relying on color alone |
