"""
Four core fairness metrics for financial services ML models.

Each metric function accepts predictions, ground truth, and group labels,
then returns a structured result dict with disparity value, CI, p-value,
and a plain-language interpretation.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from backend.engine.statistics import (
    bootstrap_confidence_interval,
    bootstrap_confidence_interval_from_arrays,
    permutation_test,
    permutation_test_from_arrays,
)


@dataclass
class MetricResult:
    metric_name: str
    privileged_value: float
    unprivileged_value: float
    disparity: float
    threshold: float
    status: str  # PASS or FAIL
    ci_lower: float
    ci_upper: float
    p_value: float
    sample_size_privileged: int
    sample_size_unprivileged: int
    interpretation: str


# ── Default thresholds ──────────────────────────────────────────────────────
# Based on the 80% rule (four-fifths rule) for disparate impact
# and common regulatory guidance.

THRESHOLDS = {
    "demographic_parity": 0.10,
    "equalized_odds": 0.10,
    "calibration": 0.10,
    "predictive_equality": 0.10,
}


# ── Helper: split groups ───────────────────────────────────────────────────

def _split_groups(
    values: NDArray, groups: NDArray, privileged: str, unprivileged: str
) -> tuple[NDArray, NDArray]:
    """Split a values array into privileged and unprivileged subsets."""
    priv_mask = groups == privileged
    unpriv_mask = groups == unprivileged
    return values[priv_mask], values[unpriv_mask]


# ── 1. Demographic Parity ──────────────────────────────────────────────────

def _dp_disparity(group_a: NDArray, group_b: NDArray) -> float:
    """Absolute difference in positive prediction rates."""
    return float(np.mean(group_a) - np.mean(group_b))


def demographic_parity(
    predictions: NDArray,
    groups: NDArray,
    privileged: str,
    unprivileged: str,
    threshold: float | None = None,
) -> MetricResult:
    """
    Demographic Parity: measures whether positive prediction rates are equal
    across groups. A disparity above the threshold indicates the model
    approves one group at a meaningfully different rate.
    """
    thr = threshold or THRESHOLDS["demographic_parity"]
    priv_preds, unpriv_preds = _split_groups(predictions, groups, privileged, unprivileged)

    priv_rate = float(np.mean(priv_preds))
    unpriv_rate = float(np.mean(unpriv_preds))

    point, ci_lo, ci_hi = bootstrap_confidence_interval(priv_preds, unpriv_preds, _dp_disparity)
    p_val = permutation_test(priv_preds, unpriv_preds, _dp_disparity)

    disparity = abs(point)
    status = "FAIL" if disparity > thr else "PASS"

    direction = "higher" if point > 0 else "lower"
    interpretation = (
        f"The privileged group has a {direction} positive prediction rate "
        f"({priv_rate:.1%} vs {unpriv_rate:.1%}), "
        f"with an absolute disparity of {disparity:.4f}. "
        f"{'This exceeds' if status == 'FAIL' else 'This is within'} "
        f"the threshold of {thr:.2f}."
    )

    return MetricResult(
        metric_name="demographic_parity",
        privileged_value=priv_rate,
        unprivileged_value=unpriv_rate,
        disparity=disparity,
        threshold=thr,
        status=status,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        p_value=p_val,
        sample_size_privileged=len(priv_preds),
        sample_size_unprivileged=len(unpriv_preds),
        interpretation=interpretation,
    )


# ── 2. Equalized Odds ──────────────────────────────────────────────────────

def _tpr(predictions: NDArray, labels: NDArray) -> float:
    positives = labels == 1
    if positives.sum() == 0:
        return 0.0
    return float(predictions[positives].mean())


def _fpr(predictions: NDArray, labels: NDArray) -> float:
    negatives = labels == 0
    if negatives.sum() == 0:
        return 0.0
    return float(predictions[negatives].mean())


def equalized_odds(
    predictions: NDArray,
    labels: NDArray,
    groups: NDArray,
    privileged: str,
    unprivileged: str,
    threshold: float | None = None,
) -> MetricResult:
    """
    Equalized Odds: measures whether true positive rates and false positive rates
    are equal across groups. Requires ground truth labels. The disparity reported
    is the maximum of |TPR_diff| and |FPR_diff|.
    """
    thr = threshold or THRESHOLDS["equalized_odds"]

    priv_mask = groups == privileged
    unpriv_mask = groups == unprivileged

    priv_tpr = _tpr(predictions[priv_mask], labels[priv_mask])
    unpriv_tpr = _tpr(predictions[unpriv_mask], labels[unpriv_mask])
    priv_fpr = _fpr(predictions[priv_mask], labels[priv_mask])
    unpriv_fpr = _fpr(predictions[unpriv_mask], labels[unpriv_mask])

    tpr_diff = abs(priv_tpr - unpriv_tpr)
    fpr_diff = abs(priv_fpr - unpriv_fpr)

    def _eo_stat(preds: NDArray, y: NDArray, g: NDArray) -> float:
        pm = g == privileged
        um = g == unprivileged
        if pm.sum() == 0 or um.sum() == 0:
            return 0.0
        _priv_tpr = _tpr(preds[pm], y[pm])
        _unpriv_tpr = _tpr(preds[um], y[um])
        _priv_fpr = _fpr(preds[pm], y[pm])
        _unpriv_fpr = _fpr(preds[um], y[um])
        return max(abs(_priv_tpr - _unpriv_tpr), abs(_priv_fpr - _unpriv_fpr))

    point, ci_lo, ci_hi = bootstrap_confidence_interval_from_arrays(
        [predictions, labels, groups],
        _eo_stat,
    )
    p_val = permutation_test_from_arrays(
        [predictions, labels, groups],
        group_array_index=2,
        statistic_fn=_eo_stat,
    )

    disparity = max(tpr_diff, fpr_diff)
    priv_val = max(priv_tpr, priv_fpr)
    unpriv_val = max(unpriv_tpr, unpriv_fpr)
    status = "FAIL" if disparity > thr else "PASS"

    interpretation = (
        f"TPR disparity: {tpr_diff:.4f}, FPR disparity: {fpr_diff:.4f}. "
        f"The maximum disparity is {disparity:.4f}. "
        f"{'This exceeds' if status == 'FAIL' else 'This is within'} "
        f"the threshold of {thr:.2f}."
    )

    return MetricResult(
        metric_name="equalized_odds",
        privileged_value=priv_val,
        unprivileged_value=unpriv_val,
        disparity=disparity,
        threshold=thr,
        status=status,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        p_value=p_val,
        sample_size_privileged=int(priv_mask.sum()),
        sample_size_unprivileged=int(unpriv_mask.sum()),
        interpretation=interpretation,
    )


# ── 3. Calibration ─────────────────────────────────────────────────────────

def calibration(
    predictions: NDArray,
    labels: NDArray,
    groups: NDArray,
    privileged: str,
    unprivileged: str,
    n_buckets: int = 10,
    threshold: float | None = None,
) -> MetricResult:
    """
    Calibration: measures whether predicted probabilities are equally reliable
    across groups. Splits predictions into buckets and compares actual outcome
    rates per group. Reports the maximum bucket-level disparity.
    """
    thr = threshold or THRESHOLDS["calibration"]

    priv_mask = groups == privileged
    unpriv_mask = groups == unprivileged

    bucket_edges = np.linspace(0, 1, n_buckets + 1)
    max_bucket_disparity = 0.0

    for i in range(n_buckets):
        lo, hi = bucket_edges[i], bucket_edges[i + 1]

        priv_in_bucket = (predictions[priv_mask] >= lo) & (predictions[priv_mask] < hi)
        unpriv_in_bucket = (predictions[unpriv_mask] >= lo) & (predictions[unpriv_mask] < hi)

        if priv_in_bucket.sum() < 5 or unpriv_in_bucket.sum() < 5:
            continue  # Skip buckets with too few samples

        priv_actual = labels[priv_mask][priv_in_bucket].mean()
        unpriv_actual = labels[unpriv_mask][unpriv_in_bucket].mean()
        bucket_disp = abs(priv_actual - unpriv_actual)
        max_bucket_disparity = max(max_bucket_disparity, bucket_disp)

    # Overall calibration rates
    priv_cal = float(labels[priv_mask].mean()) if priv_mask.sum() > 0 else 0.0
    unpriv_cal = float(labels[unpriv_mask].mean()) if unpriv_mask.sum() > 0 else 0.0

    def _calibration_gap(preds: NDArray, y: NDArray, g: NDArray) -> float:
        pm = g == privileged
        um = g == unprivileged
        if pm.sum() == 0 or um.sum() == 0:
            return 0.0
        max_gap = 0.0
        edges = np.linspace(0, 1, n_buckets + 1)
        for idx in range(n_buckets):
            lo, hi = edges[idx], edges[idx + 1]
            p_bucket = (preds[pm] >= lo) & (preds[pm] < hi)
            u_bucket = (preds[um] >= lo) & (preds[um] < hi)
            if p_bucket.sum() < 5 or u_bucket.sum() < 5:
                continue
            p_actual = float(y[pm][p_bucket].mean())
            u_actual = float(y[um][u_bucket].mean())
            max_gap = max(max_gap, abs(p_actual - u_actual))
        return max_gap

    _, ci_lo, ci_hi = bootstrap_confidence_interval_from_arrays(
        [predictions, labels, groups],
        _calibration_gap,
    )
    p_val = permutation_test_from_arrays(
        [predictions, labels, groups],
        group_array_index=2,
        statistic_fn=_calibration_gap,
    )

    status = "FAIL" if max_bucket_disparity > thr else "PASS"

    interpretation = (
        f"Maximum calibration disparity across {n_buckets} probability buckets: "
        f"{max_bucket_disparity:.4f}. "
        f"{'This exceeds' if status == 'FAIL' else 'This is within'} "
        f"the threshold of {thr:.2f}."
    )

    return MetricResult(
        metric_name="calibration",
        privileged_value=priv_cal,
        unprivileged_value=unpriv_cal,
        disparity=max_bucket_disparity,
        threshold=thr,
        status=status,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        p_value=p_val,
        sample_size_privileged=int(priv_mask.sum()),
        sample_size_unprivileged=int(unpriv_mask.sum()),
        interpretation=interpretation,
    )


# ── 4. Predictive Equality ─────────────────────────────────────────────────

def predictive_equality(
    predictions: NDArray,
    labels: NDArray,
    groups: NDArray,
    privileged: str,
    unprivileged: str,
    threshold: float | None = None,
) -> MetricResult:
    """
    Predictive Equality: measures whether false positive rates are equal
    across groups. Unlike Equalized Odds, this only considers FPR disparity.
    Useful when the cost of false positives is high (e.g., fraud false alarms).
    """
    thr = threshold or THRESHOLDS["predictive_equality"]

    priv_mask = groups == privileged
    unpriv_mask = groups == unprivileged

    priv_fpr_val = _fpr(predictions[priv_mask], labels[priv_mask])
    unpriv_fpr_val = _fpr(predictions[unpriv_mask], labels[unpriv_mask])

    disparity = abs(priv_fpr_val - unpriv_fpr_val)

    def _pe_stat(preds: NDArray, y: NDArray, g: NDArray) -> float:
        pm = g == privileged
        um = g == unprivileged
        if pm.sum() == 0 or um.sum() == 0:
            return 0.0
        return abs(_fpr(preds[pm], y[pm]) - _fpr(preds[um], y[um]))

    _, ci_lo, ci_hi = bootstrap_confidence_interval_from_arrays(
        [predictions, labels, groups],
        _pe_stat,
    )
    p_val = permutation_test_from_arrays(
        [predictions, labels, groups],
        group_array_index=2,
        statistic_fn=_pe_stat,
    )

    status = "FAIL" if disparity > thr else "PASS"

    interpretation = (
        f"False positive rate disparity: {disparity:.4f} "
        f"(privileged FPR: {priv_fpr_val:.4f}, unprivileged FPR: {unpriv_fpr_val:.4f}). "
        f"{'This exceeds' if status == 'FAIL' else 'This is within'} "
        f"the threshold of {thr:.2f}."
    )

    return MetricResult(
        metric_name="predictive_equality",
        privileged_value=priv_fpr_val,
        unprivileged_value=unpriv_fpr_val,
        disparity=disparity,
        threshold=thr,
        status=status,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        p_value=p_val,
        sample_size_privileged=int(priv_mask.sum()),
        sample_size_unprivileged=int(unpriv_mask.sum()),
        interpretation=interpretation,
    )


# ── Metric registry ────────────────────────────────────────────────────────

METRIC_CATALOG = {
    "demographic_parity": {
        "name": "demographic_parity",
        "display_name": "Demographic Parity",
        "category": "group_fairness",
        "description": (
            "Measures whether positive prediction rates are equal across groups. "
            "Also known as statistical parity or disparate impact testing."
        ),
        "use_cases": [
            "ECOA disparate impact compliance",
            "Equal opportunity lending goals",
            "Outcomes should be proportional to group sizes",
        ],
        "limitations": [
            "Ignores ground truth differences between groups",
            "May conflict with accuracy optimization",
            "Can incentivize demographic balancing over merit-based decisions",
        ],
        "requires_ground_truth": False,
    },
    "equalized_odds": {
        "name": "equalized_odds",
        "display_name": "Equalized Odds",
        "category": "group_fairness",
        "description": (
            "Measures whether true positive rates and false positive rates are "
            "equal across groups. Ensures accuracy is equally distributed."
        ),
        "use_cases": [
            "Accuracy-critical decisions (credit scoring)",
            "When ground truth labels are reliable",
            "Error consequences should be similar for all groups",
        ],
        "limitations": [
            "Requires labeled ground truth data",
            "Mathematically incompatible with demographic parity when base rates differ",
            "Stricter than other group fairness metrics",
        ],
        "requires_ground_truth": True,
    },
    "calibration": {
        "name": "calibration",
        "display_name": "Calibration",
        "category": "group_fairness",
        "description": (
            "Measures whether predicted probabilities are equally reliable across groups. "
            "A well-calibrated model means a 70% prediction is actually correct 70% of the time "
            "for all groups."
        ),
        "use_cases": [
            "Risk-based pricing models",
            "When probability estimates directly drive decisions",
            "Stakeholders rely on confidence scores",
        ],
        "limitations": [
            "Incompatible with equalized odds when base rates differ (Chouldechova 2017)",
            "Requires sufficient samples per probability bucket",
            "Can mask TPR/FPR disparities",
        ],
        "requires_ground_truth": True,
    },
    "predictive_equality": {
        "name": "predictive_equality",
        "display_name": "Predictive Equality",
        "category": "group_fairness",
        "description": (
            "Measures whether false positive rates are equal across groups. "
            "Focuses specifically on FPR disparity, unlike Equalized Odds which "
            "also considers TPR."
        ),
        "use_cases": [
            "High false-positive-cost scenarios (fraud detection alerts)",
            "When FPR matters more than TPR",
            "Reducing disproportionate false accusations across groups",
        ],
        "limitations": [
            "Ignores true positive rate differences",
            "Requires labeled ground truth data",
            "Narrower view of fairness than equalized odds",
        ],
        "requires_ground_truth": True,
    },
}

# Map metric names to their compute functions
METRIC_FUNCTIONS = {
    "demographic_parity": demographic_parity,
    "equalized_odds": equalized_odds,
    "calibration": calibration,
    "predictive_equality": predictive_equality,
}
