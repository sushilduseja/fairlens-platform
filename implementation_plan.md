# Groq LLM Integration — Refactoring Plan

## 1. Groq Client: Location, Structure, Failure Handling

### Location

New file: `backend/engine/llm.py`

Lives in `engine/` — not `core/`, not `api/`. The LLM is a computation layer that operates on `MetricResult` data structures, same as `recommendations.py` and `metrics.py`. It imports from `engine/`, it's consumed by `jobs/worker.py`. Putting it in `core/` would imply it's infrastructure; it's not. It's domain logic.

### Structure

One module, three concerns:

1. **Client singleton.** A thin async wrapper around Groq's REST API using `httpx.AsyncClient`. Not the Groq Python SDK — that adds a dependency with its own retry/timeout opinions that conflict with ours. Raw `httpx` gives us control over timeouts, retries, and response parsing. The client is instantiated once at module level with a connection pool, reused across calls.

2. **Prompt dispatcher.** Two async functions exposed to the rest of the codebase:
   - `generate_narrative_summary(results, model_context, use_case)` → returns a string (the audit narrative) or `None` on failure.
   - `generate_enriched_recommendations(results, rule_based_recs, model_context, use_case)` → returns a list of enriched recommendation dicts or `None` on failure.
   
   Each function constructs its own system prompt, serializes the structured input, calls Groq, parses the response, and validates the output shape.

3. **Configuration.** Three new fields on `Settings` in `config.py`:
   - `GROQ_API_KEY: str = ""` — empty string means Groq is disabled. Not `None`, because `None` requires sentinel logic; empty string is falsy and trivial to check.
   - `GROQ_MODEL: str = "llama-3.3-70b-versatile"` — the specific model. Pinned, not "latest." Llama 3.3 70B is the right tradeoff: fast inference on Groq, large enough context for full audit payloads, structured output compliance better than Mixtral. 
   - `GROQ_TIMEOUT_SECONDS: int = 30` — hard timeout per call.

### Failure Handling

**Iron rule: Groq is always optional. The statistical result is the product. The LLM enriches it.**

Implementation:
- Every LLM function returns `T | None`. `None` means the call failed, timed out, or Groq is disabled.
- The worker checks if the return is `None`. If so, it persists the rule-based output unchanged. The user sees the same result they see today. No degradation.
- No retries inside the LLM module. If Groq is slow or down, one attempt with a 30-second timeout, then `None`. Rationale: the worker is already inside an async job. Adding retries doubles the audit completion time for a cosmetic enrichment. Not worth it.
- All Groq failures are logged with the audit ID, status code, and response body (truncated to 500 chars). No silent swallowing.
- A `groq_enriched: bool` flag on the Audit record tells the API consumer whether LLM enrichment succeeded. The frontend can show a subtle indicator ("AI-enhanced analysis" vs. "statistical analysis"), but both paths are complete.

---

## 2. Prompt Engineering Strategy

### Input: What Goes to the LLM

The LLM receives a JSON object constructed from `MetricResult` dataclasses. The serialization is explicit — not `dataclasses.asdict()` dumped wholesale. Each field is named and annotated:

```
{
  "model_name": "Credit Scoring v3.1",
  "use_case": "credit_approval",
  "overall_verdict": "CONDITIONAL_PASS",
  "dataset_row_count": 45000,
  "results": [
    {
      "metric": "demographic_parity",
      "display_name": "Demographic Parity",
      "protected_attribute": "gender",
      "privileged_group": "male",
      "unprivileged_group": "female",
      "privileged_rate": 0.72,
      "unprivileged_rate": 0.61,
      "disparity": 0.11,
      "threshold": 0.10,
      "status": "FAIL",
      "confidence_interval": [0.08, 0.14],
      "p_value": 0.003,
      "sample_size_privileged": 28000,
      "sample_size_unprivileged": 17000
    }
  ],
  "rule_based_recommendations": [
    {
      "priority": "high",
      "issue": "Demographic parity violation...",
      "mitigation_strategy": "Resample training data..."
    }
  ]
}
```

Key design choices:
- **Numeric values are already computed.** The LLM's job is interpretation, not calculation.
- **Field names are human-readable** (not `ci_lower`/`ci_upper`, but `confidence_interval` as an array). Reduces prompt confusion.
- **Rule-based recommendations are included** so the LLM can reference, rephrase, and contextualize them — not invent from scratch.

### System Prompt: What It Establishes

Two system prompts, one per function.

**Narrative summary system prompt:**

> You are a fairness audit analyst at a financial services regulator. You write clear, precise executive summaries of ML model fairness audit results. You are given the computed statistical results — you must not invent, modify, or round any numeric values. Your role is to explain what the numbers mean in plain language, highlight which findings require attention, and connect results to regulatory context. Write for a compliance officer who understands risk but not statistics. Do not use hedging language like "might" or "could potentially." State findings directly. Maximum 4 paragraphs.

**Enriched recommendations system prompt:**

> You are an ML fairness remediation advisor for financial services. You are given statistical audit results and preliminary rule-based recommendations. Your job is to contextualize each recommendation for the specific use case and model type given. Add regulatory references where relevant (EU AI Act, ECOA, FCA, MAS FEAT). Rewrite generic advice into specific, actionable steps. Do not change the priority or structure — return the same number of recommendations in the same JSON format. Do not invent metrics, values, or statistics not present in the input.

### Output Constraints: Preventing Hallucination

1. **Structured output via Groq's JSON mode.** Both calls set `response_format: { type: "json_object" }`. The response is parsed as JSON; if parsing fails, the call returns `None` and the rule-based output is used.

2. **Post-generation validation.** For the recommendations function, the output JSON is validated: same number of items as input, priority values match the input, no new numeric claims. If validation fails → `None` → fall back to rule-based.

3. **The system prompt explicitly forbids numeric invention.** All numbers the LLM references must appear in the input payload. This is enforceable because the input payload is a closed set of values — any number in the output not in the input is detectable.

4. **No "explain" endpoint.** The original source material had a `POST /api/v1/fairness/explain` endpoint that accepted arbitrary metric results and generated explanations on-demand. This is the wrong architecture. It creates a code path where the LLM is called synchronously on every API request, with no caching, no persistence, and no fallback. Instead, LLM output is generated once during audit processing and stored. The explain endpoint is not built.

---

## 3. What Gets Replaced, Augmented, or Stays Untouched

### Untouched (read-only)

| File | Reason |
|---|---|
| `engine/statistics.py` | Core statistical computation. No LLM involvement. |
| `engine/metrics.py` | Metric functions and `MetricResult` dataclass. The `interpretation` field stays as-is — it's the deterministic fallback when Groq is unavailable. |
| `jobs/queue.py` | Enqueue logic is unchanged. |
| `api/auth.py` | No LLM involvement. |
| `api/models.py` | No LLM involvement. |
| `api/audit_log.py` | No LLM involvement. |
| `api/audit_log_middleware.py` | No LLM involvement. |
| `db/session.py` | No changes. |

### Augmented (logic added, existing behavior preserved)

| File | Change |
|---|---|
| `engine/recommendations.py` | `generate_recommendations()` stays as-is. A new function `enrich_recommendations_with_llm()` is added alongside it. It takes the rule-based output and the MetricResults, calls Groq, and returns either the enriched version or the original unchanged. The existing function is still the fallback and always runs first. |
| `jobs/worker.py` | After line 106 (where rule-based recommendations are persisted), a new block calls `generate_narrative_summary()` and `enrich_recommendations_with_llm()`. If enrichment succeeds, it updates the stored recommendations and writes the narrative summary. If it fails, nothing changes — the audit completes with rule-based output. |
| `core/config.py` | Three new `GROQ_*` settings added. |
| `db/models.py` | Two new columns on `Audit`, one new column on `Recommendation`. See §5. |
| `schemas/schemas.py` | Two new fields on `AuditDetailResponse`, one new field on `RecommendationResponse`. See §6. |
| `api/audits.py` | `_map_result()` and `_map_recommendation()` updated to include new fields. `get_audit()` now returns the new fields. No new logic — just wider response shape. |

### Replaced (nothing)

No existing function is deleted or replaced. Every LLM function is additive. The rule-based path is always there.

---

## 4. Async Execution Strategy in worker.py

### Decision: LLM Enrichment Runs Inline, After Stat Completion, Before Final Commit

The audit job pipeline becomes:

```
1. Load CSV, compute metrics         (existing, unchanged)
2. Generate rule-based recommendations (existing, unchanged)
3. Persist stat results + rule-based recs (existing, unchanged)  
4. Flush to DB                        (new: intermediate flush)
5. Call Groq for narrative summary     (new)
6. Call Groq for enriched recs         (new)
7. If Groq succeeded: update recs + write narrative (new)
8. Set status = "completed"           (existing)
9. Final commit                       (existing)
```

### Why Inline, Not a Separate Follow-up Job

Three reasons:

1. **User experience.** If LLM enrichment is a separate job, the audit status goes to "completed" before enrichment finishes. The user sees incomplete results, then they change. That's worse than waiting 10–15 extra seconds for a single completed state.

2. **Atomicity.** Keeping it inline means one transaction, one status transition. A separate job means managing a second status (`completed_basic` vs `completed_enriched`) or re-opening a "completed" audit to update it. Both are worse.

3. **Failure isolation.** The intermediate flush at step 4 means that if Groq times out or errors, the statistical results are already in the DB. The worker catches the Groq exception, sets `groq_enriched = False`, and proceeds to step 8. The audit completes with rule-based output. No data loss.

### Why Not Parallel Groq Calls

The two Groq calls (narrative + recommendations) run sequentially, not concurrently. Rationale: they share the same Groq rate limit bucket. Running them in parallel doubles the chance of a 429 rate-limit error. Sequential calls with a total budget of 60 seconds (30s each) are safer.

---

## 5. Schema Changes

### Audit Table: Two New Columns

| Column | Type | Default | Purpose |
|---|---|---|---|
| `narrative_summary` | `Text`, nullable | `None` | Stores the LLM-generated executive summary. Null means no LLM enrichment occurred. |
| `groq_enriched` | `Boolean`, not null | `False` | Flag indicating whether Groq enrichment succeeded. Drives frontend display logic. |

### Recommendation Table: One New Column

| Column | Type | Default | Purpose |
|---|---|---|---|
| `mitigation_strategy_enriched` | `Text`, nullable | `None` | LLM-enriched version of the mitigation strategy. When present, the frontend displays this. When null, falls back to `mitigation_strategy` (the rule-based version). |

### Why Not Replace `mitigation_strategy` In-Place

The rule-based version is the ground truth. It's deterministic, auditable, and regulatory-defensible. The enriched version is an LLM's interpretation. Storing both means:
- Audit trail preserves both the original and the enriched text.
- If a compliance officer questions the recommendation, the original logic is recoverable.
- If Groq outputs something unusable in prod, the fallback is already in the DB without a re-run.

### Alembic Migration Sequence

One migration file. Three `add_column` operations. All columns are nullable or have defaults, so the migration is backwards-compatible with existing data. No data backfill needed — existing audits will have `groq_enriched = False` and null LLM fields, which is correct.

Migration order:
1. `ALTER TABLE audits ADD COLUMN narrative_summary TEXT`
2. `ALTER TABLE audits ADD COLUMN groq_enriched BOOLEAN NOT NULL DEFAULT 0`
3. `ALTER TABLE recommendations ADD COLUMN mitigation_strategy_enriched TEXT`

SQLite handles all three. No type conflicts.

---

## 6. API Surface Changes

### No New Endpoints

The prompt's §4 notes a planned `POST /api/v1/metrics/recommend` for Phase 2. That endpoint gets the Groq treatment in §7 below. No other new endpoints are needed.

The `POST /api/v1/fairness/explain` endpoint from the original source material is **not built**. Reasoning: it would call Groq synchronously on every request, which means no caching, unbounded latency on the API, and no fallback when Groq is down. The correct architecture is to generate LLM content once during audit processing and serve it from the database. That's what this plan does.

### Modified Response Schemas

**`AuditDetailResponse`** — two new fields:

| Field | Type | Description |
|---|---|---|
| `narrative_summary` | `string \| null` | LLM-generated executive summary. Null when Groq was unavailable or disabled. |
| `groq_enriched` | `boolean` | Whether this audit has LLM-enhanced content. |

**`RecommendationResponse`** — one new field:

| Field | Type | Description |
|---|---|---|
| `mitigation_strategy_enriched` | `string \| null` | LLM-enhanced version of the mitigation strategy. Frontend should prefer this over `mitigation_strategy` when present. |

**`AuditSummary`** (list view) — one new field:

| Field | Type | Description |
|---|---|---|
| `groq_enriched` | `boolean` | Lets the dashboard show an "AI-enhanced" badge without loading the full audit. |

### Frontend Implications

The frontend changes are display-only:
- Audit detail page: render `narrative_summary` in a dedicated panel above the results table when non-null. Show an "AI-Enhanced Analysis" indicator when `groq_enriched` is true.
- Recommendations: display `mitigation_strategy_enriched` when present, fall back to `mitigation_strategy` when null.
- Dashboard: small badge on audit rows where `groq_enriched` is true.

---

## 7. Metric Recommendation Wizard Refactor

### Current State

`POST /api/v1/metrics/recommend` is planned for Phase 2 as a rule-based wizard: user provides `use_case`, `jurisdiction`, `has_ground_truth` → system returns hardcoded metric recommendations.

### Refactored Architecture

The endpoint keeps its exact request/response contract:

**Request (unchanged):**
```
{ use_case: string, jurisdiction: string, has_ground_truth: boolean }
```

**Response (unchanged):**
```
{ recommended_metrics: [{ name: string, rationale: string }], warnings: [string] }
```

**Implementation:**

1. A rule-based function runs first. It maps `jurisdiction` to required metrics (e.g., ECOA → demographic_parity is mandatory) and `has_ground_truth` to available metrics (e.g., no ground truth → only demographic_parity). This produces a baseline recommendation with template rationale strings.

2. If `settings.GROQ_API_KEY` is set, the baseline recommendation + user inputs are sent to Groq with a system prompt:

   > You are an ML fairness metric advisor for financial services. You are given a use case, jurisdiction, and whether ground truth labels are available, along with a preliminary metric recommendation. Rewrite each rationale to be specific to the given use case and jurisdiction. Add relevant regulatory references. If the preliminary recommendation is missing a metric that is strongly advisable for this jurisdiction, add it with rationale. Return the same JSON structure. Do not remove metrics from the preliminary set.

3. The Groq response is validated: all original metric names are present, no unknown metric names added, each rationale is a non-empty string. If validation fails → return the rule-based baseline.

4. This call is synchronous (not a background job) but is acceptable because:
   - It's a lightweight prompt — small input, small output, ~1-2 second Groq latency.
   - The endpoint is called once per wizard interaction, not per page load.
   - The 30-second timeout is the upper bound; typical response is under 3 seconds.
   - On timeout, the rule-based response is returned immediately. The user doesn't wait.

### Why This Is the Right Seam

The wizard is the one place where the LLM is genuinely better than rules. A rule-based engine can say "ECOA requires demographic parity." An LLM can say "For credit approval models under ECOA, demographic parity is required because Regulation B §1002.4 mandates disparate impact testing on approval rates. Given your model also uses probability-based scoring, calibration testing is strongly recommended alongside demographic parity to catch cases where equal approval rates mask unequal risk assessment accuracy across protected classes." That's the difference between a lookup table and an advisor.

---

## 8. Sequencing

### Ship 1: Groq Client + Config (foundation)

**Files:** `backend/engine/llm.py`, `backend/core/config.py` (3 new fields), `pyproject.toml` (`httpx` dependency — already present as a dev dep, promote to main)

**Rationale:** Everything else depends on this. It's also fully testable in isolation — mock Groq responses, verify prompt construction, verify failure → None behavior. Ship and verify before touching the worker.

### Ship 2: Schema Migration (storage layer)

**Files:** `backend/db/models.py` (3 new columns), `alembic/versions/xxx_add_groq_columns.py`, `backend/schemas/schemas.py` (3 new fields)

**Rationale:** The worker can't persist LLM output until columns exist. The API can't return LLM fields until schemas include them. This ships before the worker change so the migration runs before any code tries to write to the new columns. The new columns are all nullable/defaulted, so the migration is safe to run against a live DB with existing data.

### Ship 3: Worker Integration (the actual enrichment)

**Files:** `backend/jobs/worker.py`, `backend/engine/recommendations.py` (new `enrich_recommendations_with_llm()`)

**Rationale:** This is where Groq calls actually happen. It depends on Ship 1 (client exists) and Ship 2 (columns exist). After this ships, new audits get LLM enrichment. Existing audits are unaffected.

### Ship 4: API + Frontend Changes (surface the results)

**Files:** `backend/api/audits.py` (map new fields), `frontend/src/pages/AuditDetail.tsx` (narrative panel, enriched recs), `frontend/src/pages/Dashboard.tsx` (enriched badge)

**Rationale:** Pure display changes. No backend logic risk. Ship last because it's the lowest-risk and most reversible change. If Ships 1–3 are live but Ship 4 isn't, the data is being generated and stored — it's just not visible in the UI yet. That's a safe intermediate state.

### Ship 5: Metric Wizard (Phase 2 feature, with LLM)

**Files:** `backend/api/metrics.py` (new endpoint), `frontend/src/pages/MetricWizard.tsx`

**Rationale:** This is a new feature, not a refactor of existing behavior. It should ship after the core enrichment pipeline (Ships 1–4) is stable and validated. It also serves as a proof point: if Ships 1–4 work, Ship 5 is just a new call site for the same Groq client.

---

## Dependency Graph

```
Ship 1 (client + config)
  ↓
Ship 2 (schema migration)
  ↓
Ship 3 (worker integration)
  ↓
Ship 4 (API + frontend)
  ↓
Ship 5 (wizard endpoint)
```

No parallelism. Each ship depends on the previous. Each is independently deployable and safe to run against a production database.
