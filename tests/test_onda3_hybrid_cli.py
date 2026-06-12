"""CLI smoke test for onda3-hybrid-model-iteration (fixtures, no network)."""
from __future__ import annotations

import datetime as dt

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app


def _write_fixtures(tmp_path):
    n_days = 500
    feature_rows, label_rows, om_rows = [], [], []
    for i in range(n_days):
        date = dt.date(2021, 1, 1) + dt.timedelta(days=i)
        tmax = 18 + (i % 6)
        label_rows.append(
            {
                "date_local": date,
                "tmax_int": tmax,
                "k_cp__cp_2000": tmax - 4,
                "k_cp__cp_2100": tmax - 3,
                "k_cp__cp_2200": tmax - 2,
                "k_cp__cp_2300": tmax - 1,
            }
        )
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            feature_rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "cloud_cover_suppression": float(i % 3),
                    "foehn_score": float(i % 7),
                }
            )
            if date >= dt.date(2021, 7, 1):
                om_rows.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "om_prev_d1_day_max_c": float(tmax) + 0.3,
                    }
                )
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    om_path = tmp_path / "open_meteo.parquet"
    pl.DataFrame(feature_rows, strict=False).write_parquet(features_path)
    pl.DataFrame(label_rows, strict=False).write_parquet(labels_path)
    pl.DataFrame(om_rows, strict=False).write_parquet(om_path)
    return features_path, labels_path, om_path


def test_hybrid_cli_writes_artifacts(tmp_path):
    features_path, labels_path, om_path = _write_fixtures(tmp_path)
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(
        app,
        [
            "onda3-hybrid-model-iteration",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--open-meteo-path",
            str(om_path),
            "--binary-assignments-path",
            str(tmp_path / "missing.csv"),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2022",
            "--train-end-year",
            "2021",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "onda3_hybrid_decision_v1.csv").exists()
    assert (output_dir / "onda3_hybrid_model_report_v1.md").exists()
    assert "EXPERIMENT_ONLY" in result.output
