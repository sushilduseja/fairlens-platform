"""
Recommendation generator — produces actionable remediation advice
based on which metrics failed and their disparity magnitudes.

Rule-based, not LLM. Each failure mode has specific remediation strategies
documented in the source regulatory material.
"""

from backend.engine.metrics import MetricResult


def generate_recommendations(results: list[MetricResult]) -> list[dict]:
    """
    Given a list of MetricResults, generate prioritized recommendations
    for any that have FAIL status.
    """
    recommendations = []
    failed = [r for r in results if r.status == "FAIL"]

    if not failed:
        return []

    for result in failed:
        recs = _recommendations_for_metric(result)
        recommendations.extend(recs)

    # Deduplicate and sort by priority
    seen = set()
    unique = []
    for rec in recommendations:
        key = rec["issue"]
        if key not in seen:
            seen.add(key)
            unique.append(rec)

    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique.sort(key=lambda r: priority_order.get(r["priority"], 3))

    return unique


def _recommendations_for_metric(result: MetricResult) -> list[dict]:
    """Generate metric-specific remediation recommendations."""
    recs = []
    severity = "high" if result.disparity > result.threshold * 2 else "medium"

    if result.metric_name == "demographic_parity":
        recs.append({
            "priority": severity,
            "issue": (
                f"Demographic parity violation on '{result.metric_name}': "
                f"the privileged group has a positive prediction rate of "
                f"{result.privileged_value:.1%} vs {result.unprivileged_value:.1%} "
                f"for the unprivileged group."
            ),
            "mitigation_strategy": (
                "Resample training data to equalize base rates across groups, or apply "
                "post-processing threshold adjustments to balance approval rates. "
                "If using a scorecard model, review feature weights for proxy variables "
                "correlated with the protected attribute (e.g., ZIP code, occupation)."
            ),
            "implementation_effort": "medium",
        })
        recs.append({
            "priority": "medium",
            "issue": (
                "Potential proxy variable influence contributing to demographic parity gap."
            ),
            "mitigation_strategy": (
                "Run feature importance analysis to identify features correlated with the "
                "protected attribute. Consider removing or decorrelating proxy features. "
                "Common proxies in lending: ZIP code, employer, education level."
            ),
            "implementation_effort": "medium",
        })

    elif result.metric_name == "equalized_odds":
        recs.append({
            "priority": severity,
            "issue": (
                f"Equalized odds violation: error rates differ across groups. "
                f"Maximum disparity: {result.disparity:.4f}."
            ),
            "mitigation_strategy": (
                "Adjust classification thresholds per group to equalize TPR and FPR. "
                "This is a post-processing approach that does not require model retraining. "
                "Alternatively, apply in-processing fairness constraints during training "
                "(e.g., adversarial debiasing or fairness-constrained optimization)."
            ),
            "implementation_effort": "medium",
        })

    elif result.metric_name == "calibration":
        recs.append({
            "priority": severity,
            "issue": (
                f"Calibration disparity detected: predicted probabilities are not equally "
                f"reliable across groups. Max bucket disparity: {result.disparity:.4f}."
            ),
            "mitigation_strategy": (
                "Apply group-specific calibration (e.g., Platt scaling or isotonic regression "
                "separately per group) to ensure predicted probabilities reflect true outcome "
                "rates. Verify sufficient sample sizes per calibration bucket."
            ),
            "implementation_effort": "high",
        })

    elif result.metric_name == "predictive_equality":
        recs.append({
            "priority": severity,
            "issue": (
                f"False positive rate disparity: one group experiences false alarms at "
                f"a higher rate. FPR gap: {result.disparity:.4f}."
            ),
            "mitigation_strategy": (
                "Raise the classification threshold for the group with higher FPR to reduce "
                "false positives. Review whether features used for negative predictions "
                "correlate with the protected attribute. In fraud detection, ensure "
                "investigation resources are not disproportionately targeting one group."
            ),
            "implementation_effort": "low",
        })

    # Add universal recommendation for any failure
    if result.p_value < 0.05:
        recs.append({
            "priority": "low",
            "issue": (
                f"The disparity on {result.metric_name} is statistically significant "
                f"(p={result.p_value:.4f}), suggesting it is unlikely due to chance."
            ),
            "mitigation_strategy": (
                "Document this finding for regulatory review. If deployment proceeds, "
                "establish a monitoring schedule (quarterly recommended) to track "
                "whether the disparity widens over time."
            ),
            "implementation_effort": "low",
        })

    # Small sample warning
    min_samples = min(result.sample_size_privileged, result.sample_size_unprivileged)
    if min_samples < 100:
        recs.append({
            "priority": "medium",
            "issue": (
                f"Small sample size ({min_samples}) for one group may produce unreliable "
                f"metric estimates with wide confidence intervals."
            ),
            "mitigation_strategy": (
                "Collect more data for the underrepresented group before making deployment "
                "decisions based on this metric. Consider combining related subgroups "
                "if meaningful. Report the sample size limitation in audit documentation."
            ),
            "implementation_effort": "low",
        })

    return recs
