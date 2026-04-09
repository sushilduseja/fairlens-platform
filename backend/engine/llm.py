"""Groq LLM integration for FairLens audit enrichment.

This module provides:
1. Client singleton - async httpx wrapper around Groq REST API
2. Prompt dispatcher - generate_narrative_summary, generate_enriched_recommendations
3. Failure handling - returns None on any failure, logs errors, never blocks

All LLM functions are optional. The statistical result is the product.
The LLM enriches it when available.
"""

import logging
from typing import Any

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
    return _client


async def _close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _is_groq_available() -> bool:
    return bool(settings.GROQ_API_KEY)


def _serialize_audit_for_llm(
    audit_id: str,
    model_name: str,
    use_case: str,
    overall_verdict: str | None,
    dataset_row_count: int | None,
    results: list[dict[str, Any]],
    rule_based_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Serialize audit data into LLM-friendly JSON structure."""
    serialized_results = []
    for r in results:
        result_dict = {
            "metric": r.get("metric_name", ""),
            "display_name": r.get("metric_name", "").replace("_", " ").title(),
            "protected_attribute": r.get("protected_attribute", ""),
            "privileged_group": r.get("privileged_value", 0),
            "unprivileged_group": r.get("unprivileged_value", 0),
            "disparity": r.get("disparity", 0),
            "threshold": r.get("threshold", 0),
            "status": r.get("status", ""),
            "confidence_interval": [
                r.get("confidence_interval_lower", 0),
                r.get("confidence_interval_upper", 0),
            ],
            "p_value": r.get("p_value", 1.0),
            "sample_size_privileged": r.get("sample_size_privileged", 0),
            "sample_size_unprivileged": r.get("sample_size_unprivileged", 0),
        }
        serialized_results.append(result_dict)

    return {
        "audit_id": audit_id,
        "model_name": model_name,
        "use_case": use_case,
        "overall_verdict": overall_verdict or "UNKNOWN",
        "dataset_row_count": dataset_row_count or 0,
        "results": serialized_results,
        "rule_based_recommendations": rule_based_recommendations,
    }


async def generate_narrative_summary(
    audit_id: str,
    model_name: str,
    use_case: str,
    overall_verdict: str | None,
    dataset_row_count: int | None,
    results: list[dict[str, Any]],
    rule_based_recommendations: list[dict[str, Any]],
) -> str | None:
    """Generate executive summary narrative from audit results.

    Returns the narrative string or None on failure.
    When None, the caller falls back to rule-based output.
    """
    if not _is_groq_available():
        logger.info(f"Groq disabled, skipping narrative for audit {audit_id}")
        return None

    client = _get_client()
    payload = _serialize_audit_for_llm(
        audit_id,
        model_name,
        use_case,
        overall_verdict,
        dataset_row_count,
        results,
        rule_based_recommendations,
    )

    system_prompt = """You are a fairness audit analyst at a financial services regulator. You write clear, precise executive summaries of ML model fairness audit results. You are given the computed statistical results — you must not invent, modify, or round any numeric values. Your role is to explain what the numbers mean in plain language, highlight which findings require attention, and connect results to regulatory context. Write for a compliance officer who understands risk but not statistics. Do not use hedging language like "might" or "could potentially." State findings directly. Maximum 4 paragraphs."""

    try:
        response = await client.post(
            "/chat/completions",
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Here is the audit data:\n\n```json\n{payload}\n```\n\nWrite the executive summary.",
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 800,
            },
        )

        if response.status_code != 200:
            logger.error(
                f"Groq narrative failed for audit {audit_id}: status={response.status_code}, body={response.text[:500]}"
            )
            return None

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            logger.error(f"Groq narrative empty for audit {audit_id}")
            return None

        logger.info(f"Generated narrative for audit {audit_id}")
        return content

    except httpx.TimeoutException:
        logger.error(f"Groq timeout for audit {audit_id}")
        return None
    except Exception as e:
        logger.error(f"Groq narrative error for audit {audit_id}: {e}")
        return None


async def generate_enriched_recommendations(
    audit_id: str,
    model_name: str,
    use_case: str,
    overall_verdict: str | None,
    dataset_row_count: int | None,
    results: list[dict[str, Any]],
    rule_based_recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    """Enrich recommendations with LLM context.

    Returns enriched recommendations list or None on failure.
    When None, the caller falls back to rule-based output.
    Validation ensures same count and structure as input.
    """
    if not _is_groq_available():
        logger.info(f"Groq disabled, skipping enrichment for audit {audit_id}")
        return None

    if not rule_based_recommendations:
        return None

    client = _get_client()
    payload = _serialize_audit_for_llm(
        audit_id,
        model_name,
        use_case,
        overall_verdict,
        dataset_row_count,
        results,
        rule_based_recommendations,
    )

    system_prompt = """You are an ML fairness remediation advisor for financial services. You are given statistical audit results and preliminary rule-based recommendations. Your job is to contextualize each recommendation for the specific use case and model type given. Add regulatory references where relevant (EU AI Act, ECOA, FCA, MAS FEAT). Rewrite generic advice into specific, actionable steps. Do not change the priority or structure — return the same number of recommendations in the same JSON format. Do not invent metrics, values, or statistics not present in the input."""

    try:
        response = await client.post(
            "/chat/completions",
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Here is the audit data:\n\n```json\n{payload}\n```\n\nEnrich the recommendations.",
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
            },
        )

        if response.status_code != 200:
            logger.error(
                f"Groq enrichment failed for audit {audit_id}: status={response.status_code}, body={response.text[:500]}"
            )
            return None

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            logger.error(f"Groq enrichment empty for audit {audit_id}")
            return None

        import json

        enriched = json.loads(content)
        if not isinstance(enriched, list):
            logger.error(f"Groq enrichment not a list for audit {audit_id}")
            return None

        if len(enriched) != len(rule_based_recommendations):
            logger.error(
                f"Groq enrichment count mismatch for audit {audit_id}: got {len(enriched)}, expected {len(rule_based_recommendations)}"
            )
            return None

        for i, item in enumerate(enriched):
            if "priority" not in item or "mitigation_strategy" not in item:
                logger.error(f"Groq enrichment missing required fields for audit {audit_id}")
                return None

        logger.info(f"Enriched {len(enriched)} recommendations for audit {audit_id}")
        return enriched

    except json.JSONDecodeError:
        logger.error(f"Groq enrichment JSON parse failed for audit {audit_id}")
        return None
    except httpx.TimeoutException:
        logger.error(f"Groq enrichment timeout for audit {audit_id}")
        return None
    except Exception as e:
        logger.error(f"Groq enrichment error for audit {audit_id}: {e}")
        return None
