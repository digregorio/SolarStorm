from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_onda3_next_cli_writes_report_from_local_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-next"

    rows = []
    labels = []
    assignments = []
    for cp in ("20:00", "21:00"):
        for i in range(12):
            date = dt.date(2024 if i < 8 else 2025, 1, (i % 8) + 1)
            macro = "macro_non_southerly" if i % 2 == 0 else "macro_southerly_flow"
            k_cp = 20.0 + i
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "k_cp": k_cp,
                    "cloud_cover_suppression": float(i % 3),
                }
            )
            labels.append({"date_local": date, "tmax_int": k_cp + 1.0})
            assignments.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "binary_macro_regime_label": macro,
                    "production_status": "EXPERIMENT_ONLY",
                }
            )

    pl.DataFrame(rows).write_parquet(features_path)
    pl.DataFrame(labels).unique("date_local").write_parquet(labels_path)
    pl.DataFrame(assignments).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-next-model-iteration",
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
    assert (output_dir / "onda3_next_model_report_v1.md").exists()
    assert "READY_FOR_ONDA4_MODEL_RERUN" in result.stdout
