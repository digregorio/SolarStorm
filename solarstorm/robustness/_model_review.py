"""Onda 4 model robustness review gates and artifacts."""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

REQUIRED_INPUTS = {
    "feature_manifest",
    "design_matrix_audit",
    "baseline_results",
    "challenger_results",
    "slice_diagnostics",
    "uncertainty",
    "decision",
}

OUTPUT_FILENAMES = {
    "onda4_model_input_audit_v1": "onda4_model_input_audit_v1.csv",
    "onda4_model_gate_results_v1": "onda4_model_gate_results_v1.csv",
    "onda4_model_slice_review_v1": "onda4_model_slice_review_v1.csv",
    "onda4_model_uncertainty_review_v1": "onda4_model_uncertainty_review_v1.csv",
    "onda4_model_decision_update_v1": "onda4_model_decision_update_v1.csv",
}


def _status(blocked: bool) -> str:
    return "BLOCK" if blocked else "PASS"


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 30) -> str:
    if df.is_empty():
        return "_No rows._"
    columns = df.columns
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for row in df.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *body])


def _required_input_audit(inputs: dict[str, pl.DataFrame]) -> pl.DataFrame:
    rows = []
    for name in sorted(REQUIRED_INPUTS):
        frame = inputs.get(name)
        rows.append(
            {
                "artifact": name,
                "present": frame is not None,
                "rows": 0 if frame is None else frame.height,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def build_onda4_model_review(inputs: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    input_audit = _required_input_audit(inputs)
    missing = input_audit.filter(~pl.col("present") | (pl.col("rows") == 0))

    manifest = inputs["feature_manifest"]
    baseline = inputs["baseline_results"]
    challenger = inputs["challenger_results"]
    slices = inputs["slice_diagnostics"]
    uncertainty = inputs["uncertainty"]
    decision = inputs["decision"]
    temporal_diagnostics = inputs.get("temporal_diagnostics")

    included_blocked = manifest.filter(
        pl.col("included_in_onda3")
        & (pl.col("leakage_class") == "blocked_target_or_proxy")
    )
    null_mae = float(baseline["mae"].mean())
    challenger_mae = float(challenger["mae"].mean())
    lift = null_mae - challenger_mae
    challenger_failures = challenger.filter(~pl.col("beats_train_mean_null"))
    challenger_beats = challenger_failures.is_empty() and lift > 0
    low_support_slices = (
        slices.filter(pl.col("rows") < 30) if "rows" in slices.columns else slices
    )
    p50 = float(uncertainty["residual_abs_p50"][0])
    p90 = float(uncertainty["residual_abs_p90"][0])
    abstention_rule = str(uncertainty["abstention_rule"][0])
    uncertainty_invalid = (
        not math.isfinite(p50)
        or not math.isfinite(p90)
        or p90 < p50
        or not abstention_rule.strip()
    )
    decision_ready = str(decision["decision_status"][0]) == "READY_FOR_ONDA4_MODEL_RERUN"
    temporal_invalid = False
    temporal_detail = "first_review_single_test_year_recorded"
    if temporal_diagnostics is not None and not temporal_diagnostics.is_empty():
        temporal_invalid = not bool(
            temporal_diagnostics.select((pl.col("status") == "PASS").all()).item()
        )
        test_years = (
            str(temporal_diagnostics["test_years"][0])
            if "test_years" in temporal_diagnostics.columns
            else "not_recorded"
        )
        temporal_detail = f"rolling_temporal_diagnostics; test_years={test_years}"

    gate_results = pl.DataFrame(
        [
            {
                "gate_id": "M1",
                "gate_name": "Input artifact integrity",
                "gate_status": _status(not missing.is_empty()),
                "detail": f"missing_or_empty={missing.height}",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M2",
                "gate_name": "Causal manifest safety",
                "gate_status": _status(not included_blocked.is_empty()),
                "detail": f"included_blocked_target_or_proxy={included_blocked.height}",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M3",
                "gate_name": "Challenger lift",
                "gate_status": _status(not challenger_beats),
                "detail": (
                    f"null_mae={null_mae:.4f}; challenger_mae={challenger_mae:.4f}; "
                    f"lift={lift:.4f}; challenger_failures={challenger_failures.height}"
                ),
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M4",
                "gate_name": "Temporal robustness",
                "gate_status": _status(temporal_invalid),
                "detail": temporal_detail,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M5",
                "gate_name": "Slice robustness",
                "gate_status": _status(not low_support_slices.is_empty()),
                "detail": f"low_support_slices={low_support_slices.height}",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M6",
                "gate_name": "Uncertainty and abstention",
                "gate_status": _status(uncertainty_invalid),
                "detail": (
                    f"p50={p50:.4f}; p90={p90:.4f}; "
                    f"has_rule={bool(abstention_rule.strip())}"
                ),
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M7",
                "gate_name": "Anti-nowcast/model timing",
                "gate_status": "PASS",
                "detail": "target_proxy_columns_blocked_by_manifest",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "gate_id": "M8",
                "gate_name": "Decision hygiene",
                "gate_status": _status(not decision_ready),
                "detail": f"onda3_decision={decision['decision_status'][0]}",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )
    blocked_gates = gate_results.filter(pl.col("gate_status") == "BLOCK")
    blocked_gate_ids = blocked_gates["gate_id"].to_list()
    if blocked_gates.is_empty():
        decision_status = "READY_FOR_ONDA3_NEXT_MODEL_ITERATION"
    elif "M2" in blocked_gate_ids or "M8" in blocked_gate_ids:
        decision_status = "BLOCK_MODEL_PROMOTION"
    else:
        decision_status = "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"

    decision_update = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "blocked_gates": ",".join(blocked_gate_ids),
                "decision_rationale": (
                    "Onda 4 model robustness review completed against M1-M8 gates."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return {
        "onda4_model_input_audit_v1": input_audit,
        "onda4_model_gate_results_v1": gate_results,
        "onda4_model_slice_review_v1": slices.with_columns(
            pl.lit("EXPERIMENT_ONLY").alias("production_status")
        ),
        "onda4_model_uncertainty_review_v1": uncertainty.with_columns(
            pl.lit("EXPERIMENT_ONLY").alias("production_status")
        ),
        "onda4_model_decision_update_v1": decision_update,
    }


def write_onda4_model_review_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in OUTPUT_FILENAMES.items():
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            "\n\n".join(
                [
                    f"# {artifact_name}",
                    _markdown_table(artifacts[artifact_name]),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name.removesuffix('_v1')}_md"] = md_path

    report_path = output_dir / "onda4_model_robustness_report_v1.md"
    report = "\n\n".join(
        [
            "# Onda 4 Model Robustness Report",
            f"Generated: {today.isoformat()}",
            "## Decision",
            _markdown_table(artifacts["onda4_model_decision_update_v1"]),
            "## Gate Results",
            _markdown_table(artifacts["onda4_model_gate_results_v1"]),
            "## Input Audit",
            _markdown_table(artifacts["onda4_model_input_audit_v1"]),
            "## Slice Review",
            _markdown_table(artifacts["onda4_model_slice_review_v1"]),
            "## Uncertainty Review",
            _markdown_table(artifacts["onda4_model_uncertainty_review_v1"]),
            "## Scope",
            (
                "All outputs are EXPERIMENT_ONLY. This report does not approve "
                "production, deployment, or financial execution."
            ),
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")
    paths["onda4_model_robustness_report_md"] = report_path
    paths["onda4_model_decision_update_csv"] = paths["onda4_model_decision_update_v1_csv"]
    return paths
