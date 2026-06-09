from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda3._artifacts import write_onda3_baseline_artifacts

runner = CliRunner()


def test_onda3_artifact_writer(tmp_path: Path):
    artifacts = {
        "onda3_feature_manifest_v1": pl.DataFrame(
            {"feature": ["k_cp"], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_design_matrix_audit_v1": pl.DataFrame(
            {"joined_rows": [2], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_baseline_results_v1": pl.DataFrame(
            {"model_name": ["train_mean_null"], "mae": [1.0], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_challenger_results_v1": pl.DataFrame(
            {"model_name": ["ridge_challenger"], "mae": [0.9], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_slice_diagnostics_v1": pl.DataFrame(
            {"slice_column": ["cp"], "slice_value": ["20:00"], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_uncertainty_abstention_v1": pl.DataFrame(
            {"model_name": ["ridge_challenger"], "production_status": ["EXPERIMENT_ONLY"]}
        ),
        "onda3_decision_update_v1": pl.DataFrame(
            {
                "decision_status": ["KEEP_IN_ONDA3_EXPERIMENT_REVIEW"],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
    }

    paths = write_onda3_baseline_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    assert paths["onda3_decision_update_csv"].exists()
    assert paths["onda3_report_md"].exists()
    assert "KEEP_IN_ONDA3_EXPERIMENT_REVIEW" in paths["onda3_report_md"].read_text(encoding="utf-8")


def test_onda3_cli_writes_report_from_local_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3"

    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00", "20:00"],
            "k_cp": [20, 21, 22],
            "cloud_cover_suppression": [0.5, 1.0, 1.5],
        }
    ).write_parquet(features_path)
    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "tmax_int": [22, 23, 24],
        }
    ).write_parquet(labels_path)
    pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00", "20:00"],
            "binary_macro_regime_label": [
                "macro_non_southerly",
                "macro_non_southerly",
                "macro_southerly_flow",
            ],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-baseline-model",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2024-12-31",
            "--test-start",
            "2025-01-01",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_baseline_model_report_v1.md").exists()
