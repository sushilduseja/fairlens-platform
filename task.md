# Groq LLM Integration — Task Tracker

## Ship 1: Groq Client + Config
- [x] Add GROQ_* settings to config.py
- [x] Add httpx to pyproject.toml main deps
- [x] Create backend/engine/llm.py (client singleton, prompt dispatcher, failure handling)

## Ship 2: Schema Migration
- [x] Add narrative_summary + groq_enriched to Audit model
- [x] Add mitigation_strategy_enriched to Recommendation model
- [x] Create Alembic migration
- [x] Add new fields to Pydantic response schemas

## Ship 3: Worker Integration
- [x] Add enrich_recommendations_with_llm() to recommendations.py
- [x] Add LLM enrichment block to worker.py (intermediate flush, Groq calls, fallback)

## Ship 4: API + Frontend
- [x] Update api/audits.py mappers to include new fields
- [x] Update AuditDetail page (narrative panel, enriched recs, AI badge)
- [x] Update Dashboard (groq_enriched badge)

## Ship 5: Metric Wizard
- [ ] Create rule-based metric recommendation function
- [ ] Add POST /api/v1/metrics/recommend endpoint with Groq augmentation
- [ ] Create MetricWizard frontend page