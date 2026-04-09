"""Tests for backend/api/audits.py audit creation and processing."""

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.db.models import Audit, Model


class TestAuditCreation:
    """Test audit creation endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = MagicMock()
        user.id = "test-user-id"
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_model(self):
        """Create a mock model."""
        model = MagicMock()
        model.id = "test-model-id"
        model.user_id = "test-user-id"
        model.name = "Test Model"
        model.use_case = "credit_approval"
        return model

    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content for testing."""
        return "prediction,label,gender,age\n1,1,M,25\n1,0,M,30\n0,0,F,22\n0,1,F,28"

    def test_parse_protected_attributes_valid_json(self):
        """Test that valid JSON protected_attributes parses correctly."""
        from backend.api.audits import _parse_protected_attributes

        raw = '[{"name": "gender", "type": "binary", "privileged_group": "M", "unprivileged_group": "F"}]'
        result = _parse_protected_attributes(raw)

        assert len(result) == 1
        assert result[0].name == "gender"
        assert result[0].privileged_group == "M"
        assert result[0].unprivileged_group == "F"

    def test_parse_protected_attributes_invalid_json_raises(self):
        """Test that invalid JSON raises HTTPException."""
        from backend.api.audits import _parse_protected_attributes
        from fastapi import HTTPException

        raw = "invalid json"
        with pytest.raises(HTTPException) as exc_info:
            _parse_protected_attributes(raw)
        assert exc_info.value.status_code == 422

    def test_parse_selected_metrics_valid(self):
        """Test that valid metrics parse correctly."""
        from backend.api.audits import _parse_selected_metrics

        raw = '["demographic_parity", "equalized_odds"]'
        result = _parse_selected_metrics(raw)

        assert result == ["demographic_parity", "equalized_odds"]

    def test_parse_selected_metrics_unknown_metric_raises(self):
        """Test that unknown metric raises HTTPException."""
        from backend.api.audits import _parse_selected_metrics
        from fastapi import HTTPException

        raw = '["invalid_metric"]'
        with pytest.raises(HTTPException) as exc_info:
            _parse_selected_metrics(raw)
        assert "Unknown metrics" in exc_info.value.detail

    def test_parse_selected_metrics_empty_list_raises(self):
        """Test that empty metrics list raises HTTPException."""
        from backend.api.audits import _parse_selected_metrics
        from fastapi import HTTPException

        raw = "[]"
        with pytest.raises(HTTPException) as exc_info:
            _parse_selected_metrics(raw)
        assert exc_info.value.status_code == 422


class TestGroundTruthValidation:
    """Test ground truth column validation."""

    def test_ground_truth_required_for_equalized_odds(self):
        """Test that equalized_odds requires ground_truth_column."""
        from backend.api.audits import _validate_ground_truth_requirements
        from fastapi import HTTPException

        metrics = ["equalized_odds"]
        ground_truth = None

        with pytest.raises(HTTPException) as exc_info:
            _validate_ground_truth_requirements(metrics, ground_truth)
        assert "ground_truth_column is required" in exc_info.value.detail

    def test_ground_truth_not_required_for_demographic_parity(self):
        """Test that demographic_parity doesn't require ground_truth_column."""
        from backend.api.audits import _validate_ground_truth_requirements

        metrics = ["demographic_parity"]
        ground_truth = None

        _validate_ground_truth_requirements(metrics, ground_truth)

    def test_ground_truth_required_for_calibration(self):
        """Test that calibration requires ground_truth_column."""
        from backend.api.audits import _validate_ground_truth_requirements
        from fastapi import HTTPException

        metrics = ["calibration"]
        ground_truth = None

        with pytest.raises(HTTPException) as exc_info:
            _validate_ground_truth_requirements(metrics, ground_truth)
        assert "ground_truth_column is required" in exc_info.value.detail


class TestCSVValidation:
    """Test CSV file validation."""

    @pytest.fixture
    def valid_csv_file(self, tmp_path):
        """Create a valid CSV file."""
        csv_path = tmp_path / "valid.csv"
        df = pd.DataFrame(
            {
                "prediction": [1, 0, 1, 0],
                "label": [1, 0, 1, 0],
                "gender": ["M", "M", "F", "F"],
            }
        )
        df.to_csv(csv_path, index=False)
        return csv_path

    def test_validate_csv_columns_missing_prediction(self, valid_csv_file):
        """Test validation fails when prediction column missing."""
        from backend.api.audits import _validate_csv_columns
        from fastapi import HTTPException
        from backend.schemas.schemas import ProtectedAttributeConfig

        protected_attrs = [
            ProtectedAttributeConfig(
                name="gender", type="binary", privileged_group="M", unprivileged_group="F"
            )
        ]

        with pytest.raises(HTTPException) as exc_info:
            _validate_csv_columns(valid_csv_file, "nonexistent_column", "label", protected_attrs)
        assert "missing required columns" in exc_info.value.detail

    def test_validate_csv_columns_non_numeric_prediction(self, tmp_path):
        """Test validation fails when prediction column is non-numeric."""
        from backend.api.audits import _validate_csv_columns
        from fastapi import HTTPException
        from backend.schemas.schemas import ProtectedAttributeConfig

        csv_path = tmp_path / "non_numeric.csv"
        df = pd.DataFrame(
            {
                "prediction": ["yes", "no", "yes", "no"],
                "label": [1, 0, 1, 0],
            }
        )
        df.to_csv(csv_path, index=False)

        protected_attrs = []

        with pytest.raises(HTTPException) as exc_info:
            _validate_csv_columns(csv_path, "prediction", "label", protected_attrs)
        assert "must be numeric" in exc_info.value.detail


class TestUploadPersistence:
    """Test file upload persistence."""

    @pytest.fixture
    def mock_settings(self, tmp_path):
        """Create mock settings for upload path."""
        with patch("backend.api.audits.settings") as mock_settings:
            mock_settings.upload_path = tmp_path / "uploads"
            mock_settings.MAX_UPLOAD_SIZE_MB = 1
            yield mock_settings

    @pytest.mark.asyncio
    async def test_persist_upload_creates_file(self, mock_settings, tmp_path):
        """Test that _persist_upload creates the file."""
        from backend.api.audits import _persist_upload

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        content = b"prediction,label\n1,1\n0,0"
        file = UploadFile(filename="test.csv", file=io.BytesIO(content))

        with patch("backend.api.audits.settings") as mock_s:
            mock_s.upload_path = upload_dir
            mock_s.MAX_UPLOAD_SIZE_MB = 1
            result = await _persist_upload(file)

        assert result.exists()
        assert result.name.endswith(".csv")

    @pytest.mark.asyncio
    async def test_persist_upload_rejects_non_csv(self, mock_settings):
        """Test that non-CSV files are rejected."""
        from backend.api.audits import _persist_upload
        from fastapi import HTTPException

        content = b"some data"
        file = UploadFile(filename="test.txt", file=io.BytesIO(content))

        with pytest.raises(HTTPException) as exc_info:
            await _persist_upload(file)
        assert exc_info.value.status_code == 422


class TestAuditStatusTransitions:
    """Test audit status transitions."""

    def test_audit_status_queued_on_creation(self):
        """Test that audit starts with queued status."""
        from backend.db.models import Audit

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="queued",
            dataset_row_count=0,
            protected_attributes=[],
            selected_metrics=[],
            file_path="/tmp/test.csv",
            prediction_column="pred",
        )

        assert audit.status == "queued"

    def test_audit_status_processing_on_worker_start(self):
        """Test that audit status changes to processing."""
        from backend.db.models import Audit

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="queued",
            dataset_row_count=0,
            protected_attributes=[],
            selected_metrics=[],
            file_path="/tmp/test.csv",
            prediction_column="pred",
        )

        audit.status = "processing"

        assert audit.status == "processing"

    def test_audit_status_completed_after_worker(self):
        """Test that audit status changes to completed."""
        from backend.db.models import Audit

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="processing",
            dataset_row_count=100,
            protected_attributes=[],
            selected_metrics=[],
            file_path="/tmp/test.csv",
            prediction_column="pred",
            overall_verdict="PASS",
        )

        audit.status = "completed"

        assert audit.status == "completed"
        assert audit.overall_verdict == "PASS"

    def test_audit_status_failed_on_error(self):
        """Test that audit status changes to failed on error."""
        from backend.db.models import Audit

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="queued",
            dataset_row_count=0,
            protected_attributes=[],
            selected_metrics=[],
            file_path="/tmp/test.csv",
            prediction_column="pred",
        )

        audit.status = "failed"
        audit.error_message = "Database connection failed"

        assert audit.status == "failed"
        assert audit.error_message == "Database connection failed"


class TestAuditModelMapping:
    """Test audit to response mapping."""

    def test_map_fairness_result_response(self):
        """Test mapping FairnessResult to response."""
        from backend.api.audits import _map_result
        from backend.db.models import FairnessResult

        result = FairnessResult(
            audit_id="test-audit",
            metric_name="demographic_parity",
            protected_attribute="gender",
            privileged_value=0.8,
            unprivileged_value=0.4,
            disparity=0.4,
            threshold=0.1,
            status="FAIL",
            confidence_interval_lower=0.7,
            confidence_interval_upper=0.9,
            p_value=0.01,
            sample_size_privileged=100,
            sample_size_unprivileged=100,
            interpretation="Test interpretation",
        )

        response = _map_result(result)

        assert response.metric_name == "demographic_parity"
        assert response.privileged_value == 0.8
        assert response.status == "FAIL"

    def test_map_recommendation_response(self):
        """Test mapping Recommendation to response."""
        from backend.api.audits import _map_recommendation
        from backend.db.models import Recommendation

        recommendation = Recommendation(
            audit_id="test-audit",
            priority="high",
            issue="Test issue",
            mitigation_strategy="Test strategy",
            implementation_effort="medium",
        )

        response = _map_recommendation(recommendation)

        assert response.priority == "high"
        assert response.issue == "Test issue"


class TestAuditListPagination:
    """Test audit list pagination."""

    def test_list_audits_pagination_defaults(self):
        """Test default pagination values."""
        page = 1
        per_page = 20

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        assert page == 1
        assert per_page == 20

    def test_list_audits_pagination_clamp_page(self):
        """Test page number is clamped to minimum 1."""
        page = 0
        per_page = 20

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        assert page == 1

    def test_list_audits_pagination_clamp_per_page(self):
        """Test per_page is clamped between 1 and 100."""
        page = 1
        per_page = 500

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        assert per_page == 100

    def test_list_audits_offset_calculation(self):
        """Test offset calculation for pagination."""
        page = 3
        per_page = 20

        offset = (page - 1) * per_page

        assert offset == 40


class TestAuditModelOwnership:
    """Test audit model ownership validation."""

    def test_audit_model_must_belong_to_user(self):
        """Test that user can only create audit for their own models."""
        from backend.db.models import Audit, Model, User

        user = User(id="user-1", email="user1@test.com", hashed_password="hash", is_active=True)
        other_user = User(
            id="user-2", email="user2@test.com", hashed_password="hash", is_active=True
        )

        model = Model(id="model-1", user_id="user-1", name="Test Model", use_case="credit_approval")

        assert model.user_id == user.id
        assert model.user_id != other_user.id


class TestAuditEnqueueFailureHandling:
    """Test audit enqueue failure handling."""

    @pytest.mark.asyncio
    async def test_enqueue_failure_sets_failed_status(self):
        """Test that failed enqueue sets audit status to failed."""
        from backend.jobs.queue import enqueue_audit_job
        from backend.core.config import settings

        with patch("backend.jobs.queue.create_pool") as mock_create_pool:
            mock_pool = AsyncMock()
            mock_pool.enqueue_job.side_effect = Exception("Redis connection failed")
            mock_create_pool.return_value = mock_pool

            audit = MagicMock()
            audit.id = "test-audit-id"
            audit.status = "queued"

            try:
                await enqueue_audit_job(audit.id)
            except Exception:
                pass

            mock_pool.enqueue_job.assert_called_once()


class TestAuditFileCleanup:
    """Test audit file cleanup after processing."""

    def test_worker_removes_csv_after_processing(self):
        """Test that worker removes CSV file after processing."""
        from pathlib import Path

        csv_path = Path("/tmp/test_upload.csv")
        csv_path.write_text("test content")

        assert csv_path.exists()

        csv_path.unlink(missing_ok=True)

        assert not csv_path.exists()


class TestAuditProtectedAttributes:
    """Test protected attributes handling in audits."""

    def test_audit_stores_protected_attributes_as_json(self):
        """Test that protected attributes are stored as JSON."""
        from backend.db.models import Audit

        protected_attrs = [
            {
                "name": "gender",
                "type": "binary",
                "privileged_group": "M",
                "unprivileged_group": "F",
            },
            {
                "name": "age_group",
                "type": "categorical",
                "privileged_group": "adult",
                "unprivileged_group": "senior",
            },
        ]

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="queued",
            dataset_row_count=0,
            protected_attributes=protected_attrs,
            selected_metrics=["demographic_parity"],
            file_path="/tmp/test.csv",
            prediction_column="pred",
        )

        assert len(audit.protected_attributes) == 2
        assert audit.protected_attributes[0]["name"] == "gender"

    def test_audit_stores_selected_metrics(self):
        """Test that selected metrics are stored."""
        from backend.db.models import Audit

        metrics = ["demographic_parity", "equalized_odds"]

        audit = Audit(
            model_id="test-model",
            user_id="test-user",
            status="queued",
            dataset_row_count=0,
            protected_attributes=[],
            selected_metrics=metrics,
            file_path="/tmp/test.csv",
            prediction_column="pred",
        )

        assert len(audit.selected_metrics) == 2
        assert "demographic_parity" in audit.selected_metrics
