"""ARQ worker entrypoint and audit processing task."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import delete

from backend.db.models import Audit, FairnessResult, Recommendation
from backend.db.session import async_session
from backend.engine.metrics import METRIC_FUNCTIONS, MetricResult
from backend.engine.recommendations import generate_recommendations


async def process_audit(ctx: dict, audit_id: str) -> None:
    async with async_session() as db:
        audit = await db.get(Audit, audit_id)
        if audit is None:
            return

        file_path = Path(audit.file_path)
        try:
            audit.status = "processing"
            audit.started_at = datetime.now(timezone.utc)
            await db.flush()

            frame = pd.read_csv(file_path)
            predictions_raw = frame[audit.prediction_column].to_numpy(dtype=float)
            predictions_binary = (predictions_raw >= 0.5).astype(int)
            labels = (
                frame[audit.ground_truth_column].to_numpy(dtype=int)
                if audit.ground_truth_column
                else None
            )

            metric_results: list[tuple[str, MetricResult]] = []
            for attr in audit.protected_attributes:
                attribute_name = attr["name"]
                groups = frame[attribute_name].astype(str).to_numpy()
                privileged = str(attr["privileged_group"])
                unprivileged = str(attr["unprivileged_group"])

                for metric_name in audit.selected_metrics:
                    metric_fn = METRIC_FUNCTIONS[metric_name]
                    if metric_name == "demographic_parity":
                        result = metric_fn(
                            predictions_binary,
                            groups,
                            privileged=privileged,
                            unprivileged=unprivileged,
                        )
                    else:
                        if labels is None:
                            continue
                        metric_predictions = (
                            predictions_raw if metric_name == "calibration" else predictions_binary
                        )
                        result = metric_fn(
                            metric_predictions,
                            labels,
                            groups,
                            privileged=privileged,
                            unprivileged=unprivileged,
                        )
                    metric_results.append((attribute_name, result))

            await db.execute(delete(FairnessResult).where(FairnessResult.audit_id == audit.id))
            await db.execute(delete(Recommendation).where(Recommendation.audit_id == audit.id))

            db.add_all(
                [
                    FairnessResult(
                        audit_id=audit.id,
                        metric_name=result.metric_name,
                        protected_attribute=attribute_name,
                        privileged_value=result.privileged_value,
                        unprivileged_value=result.unprivileged_value,
                        disparity=result.disparity,
                        threshold=result.threshold,
                        status=result.status,
                        confidence_interval_lower=result.ci_lower,
                        confidence_interval_upper=result.ci_upper,
                        p_value=result.p_value,
                        sample_size_privileged=result.sample_size_privileged,
                        sample_size_unprivileged=result.sample_size_unprivileged,
                        interpretation=result.interpretation,
                    )
                    for attribute_name, result in metric_results
                ]
            )

            recs = generate_recommendations([result for _, result in metric_results])
            db.add_all(
                [
                    Recommendation(
                        audit_id=audit.id,
                        priority=rec["priority"],
                        issue=rec["issue"],
                        mitigation_strategy=rec["mitigation_strategy"],
                        implementation_effort=rec["implementation_effort"],
                    )
                    for rec in recs
                ]
            )

            audit.dataset_row_count = int(len(frame))
            audit.overall_verdict = _derive_overall_verdict([r for _, r in metric_results])
            audit.status = "completed"
            audit.error_message = None
            audit.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as exc:
            audit.status = "failed"
            audit.error_message = str(exc)
            audit.completed_at = datetime.now(timezone.utc)
            await db.commit()
        finally:
            if file_path.exists():
                file_path.unlink(missing_ok=True)


def _derive_overall_verdict(results: list[MetricResult]) -> str:
    if not results:
        return "FAIL"
    fail_count = sum(1 for result in results if result.status == "FAIL")
    if fail_count == 0:
        return "PASS"
    if fail_count <= max(1, int(0.25 * len(results))):
        return "CONDITIONAL_PASS"
    return "FAIL"


class WorkerSettings:
    functions = [process_audit]
    max_jobs = 10
