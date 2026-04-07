"""Statistical testing framework — bootstrap CIs and permutation tests."""

import numpy as np
from numpy.typing import NDArray


def bootstrap_confidence_interval(
    group_a: NDArray,
    group_b: NDArray,
    metric_fn: callable,
    n_iterations: int = 5000,
    confidence_level: float = 0.95,
    rng_seed: int = 42,
) -> tuple[float, float, float]:
    """
    Compute a metric's point estimate and bootstrap confidence interval.

    Returns (point_estimate, ci_lower, ci_upper).
    metric_fn(a, b) should return a scalar disparity measure.
    """
    rng = np.random.default_rng(rng_seed)
    point_estimate = metric_fn(group_a, group_b)

    boot_estimates = np.empty(n_iterations)
    for i in range(n_iterations):
        a_sample = rng.choice(group_a, size=len(group_a), replace=True)
        b_sample = rng.choice(group_b, size=len(group_b), replace=True)
        boot_estimates[i] = metric_fn(a_sample, b_sample)

    alpha = 1 - confidence_level
    ci_lower = float(np.percentile(boot_estimates, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_estimates, 100 * (1 - alpha / 2)))

    return float(point_estimate), ci_lower, ci_upper


def permutation_test(
    group_a: NDArray,
    group_b: NDArray,
    metric_fn: callable,
    n_permutations: int = 5000,
    rng_seed: int = 42,
) -> float:
    """
    Two-sided permutation test for disparity significance.

    Returns p-value: probability of observing a disparity as extreme or
    more extreme than the actual disparity under the null hypothesis
    that both groups are drawn from the same distribution.
    """
    rng = np.random.default_rng(rng_seed)
    observed = abs(metric_fn(group_a, group_b))

    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)
    count_extreme = 0

    for _ in range(n_permutations):
        rng.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        perm_stat = abs(metric_fn(perm_a, perm_b))
        if perm_stat >= observed:
            count_extreme += 1

    return (count_extreme + 1) / (n_permutations + 1)


def bootstrap_confidence_interval_from_arrays(
    arrays: list[NDArray],
    statistic_fn: callable,
    n_iterations: int = 2000,
    confidence_level: float = 0.95,
    rng_seed: int = 42,
) -> tuple[float, float, float]:
    """
    Bootstrap CI for statistic_fn over one or more aligned arrays.
    statistic_fn(*arrays) must return scalar statistic.
    """
    if not arrays:
        raise ValueError("arrays cannot be empty")
    lengths = {len(arr) for arr in arrays}
    if len(lengths) != 1:
        raise ValueError("all arrays must have same length")

    n = len(arrays[0])
    if n == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(rng_seed)
    point_estimate = float(statistic_fn(*arrays))
    if not np.isfinite(point_estimate):
        point_estimate = 0.0
    boot_estimates = np.empty(n_iterations)

    for i in range(n_iterations):
        idx = rng.choice(n, size=n, replace=True)
        sampled = [arr[idx] for arr in arrays]
        stat = float(statistic_fn(*sampled))
        boot_estimates[i] = 0.0 if not np.isfinite(stat) else stat

    alpha = 1 - confidence_level
    ci_lower = float(np.percentile(boot_estimates, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_estimates, 100 * (1 - alpha / 2)))
    return point_estimate, ci_lower, ci_upper


def permutation_test_from_arrays(
    arrays: list[NDArray],
    group_array_index: int,
    statistic_fn: callable,
    n_permutations: int = 2000,
    rng_seed: int = 42,
) -> float:
    """
    Permutation test by shuffling a designated group membership array.
    """
    if not arrays:
        raise ValueError("arrays cannot be empty")
    lengths = {len(arr) for arr in arrays}
    if len(lengths) != 1:
        raise ValueError("all arrays must have same length")

    observed = abs(float(statistic_fn(*arrays)))
    if not np.isfinite(observed):
        observed = 0.0
    n = len(arrays[0])
    if n == 0:
        return 1.0

    rng = np.random.default_rng(rng_seed)
    count_extreme = 0
    base_arrays = [arr.copy() for arr in arrays]

    for _ in range(n_permutations):
        perm = rng.permutation(n)
        permuted_arrays = [arr.copy() for arr in base_arrays]
        permuted_arrays[group_array_index] = base_arrays[group_array_index][perm]
        perm_stat = abs(float(statistic_fn(*permuted_arrays)))
        if not np.isfinite(perm_stat):
            perm_stat = 0.0
        if perm_stat >= observed:
            count_extreme += 1

    return (count_extreme + 1) / (n_permutations + 1)
