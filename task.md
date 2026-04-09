# Groq LLM Integration — Task Tracker

## Ship 1: Groq Client + Config
- [ ] Add GROQ_* settings to config.py
- [ ] Add httpx to pyproject.toml main deps
- [ ] Create backend/engine/llm.py (client singleton, prompt dispatcher, failure handling)

## Ship 2: Schema Migration
- [ ] Add narrative_summary + groq_enriched to Audit model
- [ ] Add mitigation_strategy_enriched to Recommendation model
- [ ] Create Alembic migration
- [ ] Add new fields to Pydantic response schemas

## Ship 3: Worker Integration
- [ ] Add enrich_recommendations_with_llm() to recommendations.py
- [ ] Add LLM enrichment block to worker.py (intermediate flush, Groq calls, fallback)

## Ship 4: API + Frontend
- [ ] Update api/audits.py mappers to include new fields
- [ ] Update AuditDetail page (narrative panel, enriched recs, AI badge)
- [ ] Update Dashboard (groq_enriched badge)

## Ship 5: Metric Wizard
- [ ] Create rule-based metric recommendation function
- [ ] Add POST /api/v1/metrics/recommend endpoint with Groq augmentation
- [ ] Create MetricWizard frontend page
