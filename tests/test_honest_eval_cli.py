"""CLI smoke test for honest-evaluation (fixture data, no network)."""
from __future__ import annotations

import datetime as dt

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app


def _write_fixtures(tmp_path):
    dates = [dt.date(2021, 1, 1) + dt.timedelta(days=i) for i in range(120)]
    labels = pl.DataFrame(
        {
            "date_local": dates,
            "tmax_int": [15 + (i % 5) for i in range(120)],
            "k_cp__cp_2000": [13 + (i % 5) for i in range(120)],
            "k_cp__cp_2100": [13 + (i % 5) for i in range(120)],
            "k_cp__cp_2200": [14 + (i % 5) for i in range(120)],
            "k_cp__cp_2300": [14 + (i % 5) for i in range(120)],
        }
    )
    labels_path = tmp_path / "labels.parquet"
    labels.write_parquet(labels_path)
    pred_rows = []
    for date in dates[90:]:
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            actual = labels.filter(pl.col("date_local") == date)["tmax_int"][0]
            pred_rows.append(
                {
                    "date_local": date.isoformat(),
                    "cp": cp,
                    "actual": actual,
                    "prediction": float(actual),
                }
            )
    predictions_path = tmp_path / "predictions.csv"
    pl.DataFrame(pred_rows).write_csv(predictions_path)
    return labels_path, predictions_path


def test_honest_evaluation_cli_writes_artifacts(tmp_path):
    labels_path, predictions_path = _write_fixtures(tmp_path)
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(
        app,
        [
            "honest-evaluation",
            "--labels-path",
            str(labels_path),
            "--predictions-path",
            str(predictions_path),
            "--output-dir",
            str(output_dir),
            "--train-end-year",
            "2021",
            "--no-ablation",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "honest_eval_decision_v1.csv").exists()
    assert (output_dir / "honest_evaluation_report_v1.md").exists()
    assert "EXPERIMENT_ONLY" in result.output
