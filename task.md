# FairLens MVP - Phase 1 Build Tasks

## Backend Foundation
- [x] Initialize Python project (pyproject.toml, dependencies)
- [x] FastAPI app entry point with CORS, static file serving
- [x] Core config (settings, database URL, Redis URL)
- [x] SQLAlchemy models for all 6 entities
- [x] Alembic migration setup
- [x] Pydantic schemas (request/response models)
- [x] Auth utilities (API key generation, password hashing, dependency injection)
- [x] Structured error handling middleware

## Fairness Engine
- [x] Statistical testing framework (bootstrap CI, permutation test)
- [x] Demographic parity metric
- [x] Equalized odds metric
- [x] Calibration metric
- [x] Predictive equality metric
- [x] Result interpretation (rule-based plain-language)
- [x] Recommendation generator (rule-based per failure mode)

## API Routes
- [x] POST /api/v1/auth/register
- [x] POST /api/v1/auth/login (cookie/session)
- [x] POST /api/v1/models
- [x] POST /api/v1/audits (multipart file upload)
- [x] GET /api/v1/audits/{audit_id}
- [x] GET /api/v1/audits (list, paginated)
- [x] GET /api/v1/metrics (catalog)
- [x] AuditLog middleware for state-changing endpoints

## Job Queue
- [x] ARQ worker setup with Redis
- [x] Audit processing task (validate -> compute -> store)
- [x] File cleanup after processing

## Frontend
- [x] Vite + React + TypeScript project init
- [x] Design system (tokens, global CSS, fonts)
- [x] Auth pages (Register, Login)
- [x] Dashboard page (audit list table)
- [x] New Audit page (model selector, file upload, column mapper, attribute config, metric selector)
- [x] Audit Detail / Results page (verdict, results table, recommendations, status polling)
- [x] Metric Reference page
- [x] API client hooks (fetch wrapper, polling)
- [x] Layout shell (nav, sidebar)

## Integration
- [x] Dockerfile (multi-stage: build frontend, serve with uvicorn)
- [x] docker-compose.yml (app + Redis)
- [x] Sample datasets (bundled CSVs)
- [x] README with setup instructions
