from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_onda3_rolling_cli_writes_report_from_local_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-rolling"

    features = []
    labels = []
    assignments = []
    for cp in ("20:00", "21:00"):
        for year in (2022, 2023, 2024, 2025):
            for day in range(1, 7):
                date = dt.date(year, 1, day)
                macro = "macro_non_southerly" if day % 2 == 0 else "macro_southerly_flow"
                k_cp = float(year - 2000 + day)
                features.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "k_cp": k_cp,
                        "cloud_cover_suppression": float(day % 3),
                    }
                )
                labels.append({"date_local": date, "tmax_int": k_cp + 0.5})
                assignments.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "binary_macro_regime_label": macro,
                        "production_status": "EXPERIMENT_ONLY",
                    }
                )

    pl.DataFrame(features).write_parquet(features_path)
    pl.DataFrame(labels).unique("date_local").write_parquet(labels_path)
    pl.DataFrame(assignments).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-rolling-model-iteration",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024,2025",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_rolling_model_report_v1.md").exists()
    assert "READY_FOR_ONDA4_MODEL_RERUN" in result.stdout
