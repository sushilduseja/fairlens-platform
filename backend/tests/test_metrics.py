"""Tests for backend/engine/metrics.py fairness metrics."""

import numpy as np
import pytest

from backend.engine.metrics import (
    demographic_parity,
    equalized_odds,
    calibration,
    predictive_equality,
    MetricResult,
    METRIC_CATALOG,
    METRIC_FUNCTIONS,
)


class TestDemographicParity:
    """Test demographic parity metric."""

    def test_demographic_parity_returns_metric_result(self):
        """Test that demographic_parity returns a MetricResult."""
        predictions = np.array([1, 1, 0, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert isinstance(result, MetricResult)
        assert result.metric_name == "demographic_parity"

    def test_demographic_parity_equal_groups_passes(self):
        """Test that equal prediction rates result in PASS."""
        predictions = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert result.status == "PASS"
        assert result.disparity == 0.0

    def test_demographic_parity_unequal_groups_may_fail(self):
        """Test that unequal prediction rates are detected."""
        predictions = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert result.disparity > 0

    def test_demographic_parity_has_interpretation(self):
        """Test that result includes interpretation."""
        predictions = np.array([1, 0, 1, 0])
        groups = np.array(["A", "A", "B", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 0


class TestEqualizedOdds:
    """Test equalized odds metric."""

    def test_equalized_odds_returns_metric_result(self):
        """Test that equalized_odds returns a MetricResult."""
        predictions = np.array([1, 1, 0, 0, 1, 0, 1, 0])
        labels = np.array([1, 1, 0, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = equalized_odds(predictions, labels, groups, "A", "B")

        assert isinstance(result, MetricResult)
        assert result.metric_name == "equalized_odds"

    def test_equalized_odds_equal_tpr_and_fpr_passes(self):
        """Test that equal TPR and FPR results in PASS."""
        predictions = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        labels = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = equalized_odds(predictions, labels, groups, "A", "B")

        assert result.status == "PASS"

    def test_equalized_odds_requires_ground_truth(self):
        """Test that equalized odds requires ground truth labels."""
        predictions = np.array([1, 0, 1, 0])
        labels = np.array([1, 0, 1, 0])
        groups = np.array(["A", "A", "B", "B"])

        result = equalized_odds(predictions, labels, groups, "A", "B")

        assert result.sample_size_privileged > 0
        assert result.sample_size_unprivileged > 0


class TestCalibration:
    """Test calibration metric."""

    def test_calibration_returns_metric_result(self):
        """Test that calibration returns a MetricResult."""
        predictions = np.array([0.9, 0.8, 0.2, 0.1, 0.9, 0.8, 0.2, 0.1])
        labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = calibration(predictions, labels, groups, "A", "B")

        assert isinstance(result, MetricResult)
        assert result.metric_name == "calibration"

    def test_calibration_includes_p_value(self):
        """Test that calibration includes p-value."""
        predictions = np.array([0.9, 0.8, 0.2, 0.1, 0.9, 0.8, 0.2, 0.1])
        labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = calibration(predictions, labels, groups, "A", "B")

        assert 0.0 <= result.p_value <= 1.0


class TestPredictiveEquality:
    """Test predictive equality metric."""

    def test_predictive_equality_returns_metric_result(self):
        """Test that predictive_equality returns a MetricResult."""
        predictions = np.array([1, 1, 0, 0, 1, 0, 1, 0])
        labels = np.array([1, 1, 0, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = predictive_equality(predictions, labels, groups, "A", "B")

        assert isinstance(result, MetricResult)
        assert result.metric_name == "predictive_equality"

    def test_predictive_equality_equal_fpr_passes(self):
        """Test that equal FPR results in PASS."""
        predictions = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        labels = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = predictive_equality(predictions, labels, groups, "A", "B")

        assert result.status == "PASS"


class TestMetricCatalog:
    """Test metric catalog and registry."""

    def test_all_metrics_in_catalog(self):
        """Test that all metrics are in the catalog."""
        expected = {"demographic_parity", "equalized_odds", "calibration", "predictive_equality"}

        assert set(METRIC_CATALOG.keys()) == expected

    def test_all_metrics_in_functions(self):
        """Test that all metrics have compute functions."""
        expected = {"demographic_parity", "equalized_odds", "calibration", "predictive_equality"}

        assert set(METRIC_FUNCTIONS.keys()) == expected

    def test_metric_catalog_has_required_fields(self):
        """Test that each metric has required fields."""
        for metric_name, metric_info in METRIC_CATALOG.items():
            assert "name" in metric_info
            assert "display_name" in metric_info
            assert "category" in metric_info
            assert "description" in metric_info
            assert "use_cases" in metric_info
            assert "limitations" in metric_info
            assert "requires_ground_truth" in metric_info

    def test_demographic_parity_does_not_require_ground_truth(self):
        """Test that demographic parity doesn't require ground truth."""
        assert METRIC_CATALOG["demographic_parity"]["requires_ground_truth"] == False

    def test_equalized_odds_requires_ground_truth(self):
        """Test that equalized odds requires ground truth."""
        assert METRIC_CATALOG["equalized_odds"]["requires_ground_truth"] == True


class TestMetricResult:
    """Test MetricResult dataclass."""

    def test_metric_result_has_all_fields(self):
        """Test that MetricResult has all required fields."""
        result = MetricResult(
            metric_name="test",
            privileged_value=0.5,
            unprivileged_value=0.4,
            disparity=0.1,
            threshold=0.1,
            status="PASS",
            ci_lower=0.05,
            ci_upper=0.15,
            p_value=0.3,
            sample_size_privileged=100,
            sample_size_unprivileged=100,
            interpretation="Test interpretation",
        )

        assert result.metric_name == "test"
        assert result.privileged_value == 0.5
        assert result.status == "PASS"


class TestEdgeCases:
    """Test edge cases for metrics."""

    def test_empty_group_raises_or_handles(self):
        """Test that empty groups are handled gracefully."""
        predictions = np.array([1, 0, 1, 0])
        groups = np.array(["A", "A", "B", "B"])

        # With empty predictions for one group
        result = demographic_parity(predictions, groups, "A", "C")

        assert isinstance(result, MetricResult)

    def test_single_element_groups(self):
        """Test metrics work with single element groups."""
        predictions = np.array([1, 0])
        groups = np.array(["A", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert isinstance(result, MetricResult)

    def test_binary_predictions(self):
        """Test with binary predictions."""
        predictions = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = demographic_parity(predictions, groups, "A", "B")

        assert 0.0 <= result.privileged_value <= 1.0
        assert 0.0 <= result.unprivileged_value <= 1.0

    def test_probability_predictions(self):
        """Test with probability predictions."""
        predictions = np.array([0.9, 0.8, 0.2, 0.1, 0.85, 0.75, 0.25, 0.15])
        labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        groups = np.array(["A", "A", "A", "A", "B", "B", "B", "B"])

        result = predictive_equality(predictions, labels, groups, "A", "B")

        assert isinstance(result, MetricResult)
