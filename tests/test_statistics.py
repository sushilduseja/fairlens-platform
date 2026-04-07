import numpy as np

from backend.engine.statistics import (
    bootstrap_confidence_interval,
    bootstrap_confidence_interval_from_arrays,
    permutation_test,
    permutation_test_from_arrays,
)


def test_bootstrap_confidence_interval_returns_ordered_bounds():
    a = np.array([1, 1, 1, 0, 1], dtype=float)
    b = np.array([0, 0, 0, 1, 0], dtype=float)
    point, lo, hi = bootstrap_confidence_interval(a, b, lambda x, y: float(np.mean(x) - np.mean(y)))
    assert lo <= point <= hi


def test_permutation_test_probability_bounds():
    a = np.array([1, 1, 0, 1], dtype=float)
    b = np.array([0, 0, 1, 0], dtype=float)
    p = permutation_test(a, b, lambda x, y: float(np.mean(x) - np.mean(y)), n_permutations=200)
    assert 0.0 <= p <= 1.0


def test_array_bootstrap_and_permutation_helpers():
    preds = np.array([0.9, 0.8, 0.2, 0.1], dtype=float)
    labels = np.array([1, 1, 0, 0], dtype=int)
    groups = np.array(["A", "A", "B", "B"], dtype=str)

    def stat(p, y, g):
        am = g == "A"
        bm = g == "B"
        return float(abs(y[am].mean() - y[bm].mean()))

    point, lo, hi = bootstrap_confidence_interval_from_arrays([preds, labels, groups], stat, n_iterations=100)
    p = permutation_test_from_arrays([preds, labels, groups], group_array_index=2, statistic_fn=stat, n_permutations=100)

    assert lo <= point <= hi
    assert 0.0 <= p <= 1.0
