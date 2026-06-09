from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _write_onda3_artifacts(base: Path) -> Path:
    onda3 = base / "onda3"
    onda3.mkdir()
    pl.DataFrame(
        {
            "feature": ["k_cp", "tmax_int"],
            "included_in_onda3": [True, False],
            "leakage_class": ["causal_pre_cp_or_experiment_only", "blocked_target_or_proxy"],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_feature_manifest_v1.csv")
    pl.DataFrame(
        {
            "joined_rows": [10],
            "train_rows": [8],
            "test_rows": [2],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_design_matrix_audit_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["train_mean_null"],
            "mae": [2.0],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_baseline_results_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["ridge_challenger"],
            "mae": [1.0],
            "beats_train_mean_null": [True],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_challenger_results_v1.csv")
    pl.DataFrame(
        {
            "slice_column": ["cp"],
            "slice_value": ["20:00"],
            "rows": [50],
            "target_mean": [22.0],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_slice_diagnostics_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["ridge_challenger"],
            "residual_abs_p50": [1.0],
            "residual_abs_p90": [2.0],
            "abstention_rule": ["abstain when slice support or interval calibration fails"],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_uncertainty_abstention_v1.csv")
    pl.DataFrame(
        {
            "decision_status": ["READY_FOR_ONDA4_MODEL_RERUN"],
            "decision_rationale": [
                "Baseline-first Onda 3 experiment completed against train-only null."
            ],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3 / "onda3_decision_update_v1.csv")
    return onda3


def test_onda4_model_review_cli_writes_review_artifacts(tmp_path: Path):
    onda3 = _write_onda3_artifacts(tmp_path)
    output_dir = tmp_path / "onda4-model"

    result = runner.invoke(
        app,
        [
            "onda4-model-review",
            "--onda3-dir",
            str(onda3),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda4_model_robustness_report_v1.md").exists()
    assert "READY_FOR_ONDA3_NEXT_MODEL_ITERATION" in result.stdout
