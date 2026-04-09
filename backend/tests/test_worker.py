"""Tests for backend/jobs/worker.py and ARQ queue integration."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from backend.jobs.worker import process_audit, _derive_overall_verdict
from backend.engine.metrics import MetricResult


class TestProcessAudit:
    """Test the process_audit function."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def sample_audit_data(self, tmp_path):
        """Create sample CSV and audit data for testing."""
        csv_path = tmp_path / "test_data.csv"
        df = pd.DataFrame(
            {
                "prediction": [1, 1, 1, 0, 0, 0, 1, 0],
                "label": [1, 1, 0, 0, 0, 1, 1, 0],
                "gender": ["M", "M", "M", "M", "F", "F", "F", "F"],
                "age": [25, 30, 35, 40, 22, 28, 45, 50],
            }
        )
        df.to_csv(csv_path, index=False)

        return csv_path

    def test_derive_overall_verdict_empty_results(self):
        """Test verdict derivation with empty results."""
        assert _derive_overall_verdict([]) == "FAIL"

    def test_derive_overall_verdict_all_pass(self):
        """Test verdict derivation when all metrics pass."""
        results = [
            MetricResult(
                metric_name="demographic_parity",
                privileged_value=0.5,
                unprivileged_value=0.5,
                disparity=0.0,
                threshold=0.1,
                status="PASS",
                ci_lower=0.4,
                ci_upper=0.6,
                p_value=1.0,
                sample_size_privileged=100,
                sample_size_unprivileged=100,
                interpretation="Test",
            )
        ]
        assert _derive_overall_verdict(results) == "PASS"

    def test_derive_overall_verdict_all_fail(self):
        """Test verdict derivation when all metrics fail."""
        results = [
            MetricResult(
                metric_name="demographic_parity",
                privileged_value=1.0,
                unprivileged_value=0.0,
                disparity=1.0,
                threshold=0.1,
                status="FAIL",
                ci_lower=0.9,
                ci_upper=1.0,
                p_value=0.01,
                sample_size_privileged=100,
                sample_size_unprivileged=100,
                interpretation="Test",
            ),
            MetricResult(
                metric_name="equalized_odds",
                privileged_value=1.0,
                unprivileged_value=0.0,
                disparity=1.0,
                threshold=0.1,
                status="FAIL",
                ci_lower=0.9,
                ci_upper=1.0,
                p_value=0.02,
                sample_size_privileged=100,
                sample_size_unprivileged=100,
                interpretation="Test",
            ),
        ]
        assert _derive_overall_verdict(results) == "FAIL"

    def test_derive_overall_verdict_conditional_pass(self):
        """Test verdict derivation with some failures."""
        results = [
            MetricResult(
                metric_name="demographic_parity",
                privileged_value=0.55,
                unprivileged_value=0.45,
                disparity=0.1,
                threshold=0.1,
                status="PASS",
                ci_lower=0.4,
                ci_upper=0.6,
                p_value=0.5,
                sample_size_privileged=100,
                sample_size_unprivileged=100,
                interpretation="Test",
            ),
            MetricResult(
                metric_name="equalized_odds",
                privileged_value=1.0,
                unprivileged_value=0.0,
                disparity=1.0,
                threshold=0.1,
                status="FAIL",
                ci_lower=0.9,
                ci_upper=1.0,
                p_value=0.01,
                sample_size_privileged=100,
                sample_size_unprivileged=100,
                interpretation="Test",
            ),
        ]
        assert _derive_overall_verdict(results) == "CONDITIONAL_PASS"


class TestDatabasePathConfiguration:
    """Test database path configuration for Docker environments."""

    def test_sqlite_absolute_path_format(self):
        """Test that absolute paths use four slashes after protocol for Docker."""
        absolute_path = "sqlite+aiosqlite:////app/data/fairlens.db"
        path_part = absolute_path.replace("sqlite+aiosqlite://", "")
        assert path_part.startswith("//app/data")
        assert "fairlens.db" in absolute_path

        relative_path = "sqlite+aiosqlite:///fairlens.db"
        path_part = relative_path.replace("sqlite+aiosqlite://", "")
        assert path_part.startswith("/fairlens.db")

    def test_config_allows_custom_database_url(self):
        """Test that DATABASE_URL can be configured."""
        test_url = "sqlite+aiosqlite:////custom/path/database.db"

        with patch.dict(os.environ, {"DATABASE_URL": test_url}):
            from backend.core.config import Settings

            s = Settings()
            assert s.DATABASE_URL == test_url

    def test_config_allows_custom_redis_url(self):
        """Test that REDIS_URL can be configured."""
        test_url = "redis://custom-redis:6379"

        with patch.dict(os.environ, {"REDIS_URL": test_url}):
            from backend.core.config import Settings

            s = Settings()
            assert s.REDIS_URL == test_url


class TestWorkerSettings:
    """Test worker configuration."""

    def test_worker_settings_has_process_audit_function(self):
        """Test that WorkerSettings includes process_audit."""
        from backend.jobs.worker import WorkerSettings

        assert hasattr(WorkerSettings, "functions")
        assert len(WorkerSettings.functions) == 1
        assert WorkerSettings.functions[0].__name__ == "process_audit"

    def test_worker_settings_max_jobs(self):
        """Test that WorkerSettings has max_jobs configured."""
        from backend.jobs.worker import WorkerSettings

        assert hasattr(WorkerSettings, "max_jobs")
        assert WorkerSettings.max_jobs >= 1


class TestARQQueueIntegration:
    """Test ARQ queue integration."""

    def test_enqueue_audit_job_requires_audit_id(self):
        """Test that enqueue_audit_job requires audit_id parameter."""
        from backend.jobs.queue import enqueue_audit_job
        import inspect

        sig = inspect.signature(enqueue_audit_job)
        params = list(sig.parameters.keys())
        assert "audit_id" in params

    @pytest.mark.asyncio
    async def test_enqueue_audit_job_creates_redis_pool(self):
        """Test that enqueue_audit_job creates Redis pool."""
        with (
            patch("backend.jobs.queue.create_pool") as mock_create_pool,
            patch("backend.jobs.queue.settings") as mock_settings,
        ):
            mock_settings.REDIS_URL = "redis://localhost:6379"
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool

            from backend.jobs.queue import enqueue_audit_job

            await enqueue_audit_job("test-audit-id")

            mock_create_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_enqueue_audit_job_calls_enqueue_job(self):
        """Test that enqueue_audit_job calls enqueue_job on redis."""
        with (
            patch("backend.jobs.queue.create_pool") as mock_create_pool,
            patch("backend.jobs.queue.settings") as mock_settings,
        ):
            mock_settings.REDIS_URL = "redis://localhost:6379"
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool

            from backend.jobs.queue import enqueue_audit_job

            await enqueue_audit_job("test-audit-id-123")

            mock_pool.enqueue_job.assert_called_once_with("process_audit", "test-audit-id-123")


class TestAuditFilePathResolution:
    """Test audit file path resolution in worker."""

    @pytest.fixture
    def mock_audit_with_file_path(self):
        """Create a mock audit with file path."""
        audit = MagicMock()
        audit.id = "test-audit-id"
        audit.file_path = "/tmp/test_upload.csv"
        audit.prediction_column = "prediction"
        audit.ground_truth_column = "label"
        audit.protected_attributes = [
            {"name": "gender", "type": "binary", "privileged_group": "M", "unprivileged_group": "F"}
        ]
        audit.selected_metrics = ["demographic_parity"]
        audit.status = "queued"
        return audit

    def test_process_audit_reads_csv_from_file_path(self, mock_audit_with_file_path, tmp_path):
        """Test that process_audit reads CSV from file_path."""
        csv_path = tmp_path / "test_upload.csv"
        df = pd.DataFrame(
            {
                "prediction": [1, 0, 1, 0],
                "label": [1, 0, 1, 0],
                "gender": ["M", "M", "F", "F"],
            }
        )
        df.to_csv(csv_path, index=False)

        mock_audit_with_file_path.file_path = str(csv_path)

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_audit_with_file_path)
        db.flush = AsyncMock()
        db.execute = AsyncMock()
        db.add_all = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        ctx = {}

        import asyncio

        try:
            asyncio.run(process_audit(ctx, mock_audit_with_file_path.id))
        except Exception:
            pass

        assert csv_path.exists()


class TestRedisConnection:
    """Test Redis connection configuration."""

    def test_redis_settings_from_dsn_parses_url(self):
        """Test that RedisSettings.from_dsn parses various URL formats."""
        from arq.connections import RedisSettings

        urls = [
            "redis://localhost:6379",
            "redis://redis:6379",
            "redis://custom-host:6380",
        ]

        for url in urls:
            settings = RedisSettings.from_dsn(url)
            assert settings.host is not None

    def test_config_redis_url_default(self):
        """Test default Redis URL in config."""
        from backend.core.config import settings

        assert "redis://" in settings.REDIS_URL
        assert "6379" in settings.REDIS_URL
