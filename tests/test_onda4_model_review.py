from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.robustness._model_review import (
    build_onda4_model_review,
    write_onda4_model_review_artifacts,
)


def _valid_inputs() -> dict[str, pl.DataFrame]:
    return {
        "feature_manifest": pl.DataFrame(
            {
                "feature": ["k_cp", "cloud_cover_suppression", "tmax_int"],
                "included_in_onda3": [True, True, False],
                "leakage_class": [
                    "causal_pre_cp_or_experiment_only",
                    "causal_pre_cp_or_experiment_only",
                    "blocked_target_or_proxy",
                ],
                "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
            }
        ),
        "design_matrix_audit": pl.DataFrame(
            {
                "joined_rows": [100],
                "train_rows": [80],
                "test_rows": [20],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "baseline_results": pl.DataFrame(
            {
                "model_name": ["train_mean_null"],
                "mae": [2.8],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "challenger_results": pl.DataFrame(
            {
                "model_name": ["ridge_challenger"],
                "mae": [1.4],
                "beats_train_mean_null": [True],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "slice_diagnostics": pl.DataFrame(
            {
                "slice_column": ["cp", "binary_macro_regime_label"],
                "slice_value": ["20:00", "macro_non_southerly"],
                "rows": [100, 70],
                "target_mean": [22.0, 23.0],
                "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
            }
        ),
        "uncertainty": pl.DataFrame(
            {
                "model_name": ["ridge_challenger"],
                "residual_abs_p50": [1.0],
                "residual_abs_p90": [2.5],
                "abstention_rule": ["abstain when slice support or interval calibration fails"],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "decision": pl.DataFrame(
            {
                "decision_status": ["READY_FOR_ONDA4_MODEL_RERUN"],
                "decision_rationale": [
                    "Baseline-first Onda 3 experiment completed against train-only null."
                ],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
    }


def test_model_review_passes_valid_experiment_only_onda3_surface():
    artifacts = build_onda4_model_review(_valid_inputs())

    gate_results = artifacts["onda4_model_gate_results_v1"]
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)

    assert set(gate_results["gate_status"].to_list()) == {"PASS"}
    assert decision["decision_status"] == "READY_FOR_ONDA3_NEXT_MODEL_ITERATION"
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def test_model_review_blocks_included_target_proxy_feature():
    inputs = _valid_inputs()
    inputs["feature_manifest"] = inputs["feature_manifest"].with_columns(
        pl.when(pl.col("feature") == "tmax_int")
        .then(pl.lit(True))
        .otherwise(pl.col("included_in_onda3"))
        .alias("included_in_onda3")
    )

    artifacts = build_onda4_model_review(inputs)

    blocked = (
        artifacts["onda4_model_gate_results_v1"]
        .filter(pl.col("gate_id") == "M2")
        .row(0, named=True)
    )
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)
    assert blocked["gate_status"] == "BLOCK"
    assert decision["decision_status"] == "BLOCK_MODEL_PROMOTION"


def test_model_review_blocks_when_any_challenger_row_misses_null():
    inputs = _valid_inputs()
    inputs["baseline_results"] = pl.DataFrame(
        {
            "model_name": ["train_mean_null", "train_mean_null"],
            "cp": ["20:00", "21:00"],
            "mae": [2.0, 2.0],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    )
    inputs["challenger_results"] = pl.DataFrame(
        {
            "model_name": ["ridge_challenger", "ridge_challenger"],
            "cp": ["20:00", "21:00"],
            "mae": [1.0, 2.5],
            "beats_train_mean_null": [True, False],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    )

    artifacts = build_onda4_model_review(inputs)

    m3 = artifacts["onda4_model_gate_results_v1"].filter(
        pl.col("gate_id") == "M3"
    ).row(0, named=True)
    decision = artifacts["onda4_model_decision_update_v1"].row(0, named=True)
    assert m3["gate_status"] == "BLOCK"
    assert decision["decision_status"] == "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"


def test_model_review_records_optional_temporal_diagnostics():
    inputs = _valid_inputs()
    inputs["temporal_diagnostics"] = pl.DataFrame(
        {
            "diagnostic": ["all_challengers_beat_null"],
            "status": ["PASS"],
            "test_years": ["2023,2024,2025"],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    )

    artifacts = build_onda4_model_review(inputs)

    m4 = artifacts["onda4_model_gate_results_v1"].filter(
        pl.col("gate_id") == "M4"
    ).row(0, named=True)
    assert m4["gate_status"] == "PASS"
    assert "test_years=2023,2024,2025" in m4["detail"]


def test_model_review_artifact_writer(tmp_path: Path):
    artifacts = build_onda4_model_review(_valid_inputs())

    paths = write_onda4_model_review_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    assert paths["onda4_model_robustness_report_md"].exists()
    assert paths["onda4_model_decision_update_csv"].exists()
    assert paths["onda4_model_gate_results_md"].exists()
    assert "M1" in paths["onda4_model_gate_results_md"].read_text(encoding="utf-8")
    assert "READY_FOR_ONDA3_NEXT_MODEL_ITERATION" in paths[
        "onda4_model_robustness_report_md"
    ].read_text(encoding="utf-8")
