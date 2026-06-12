from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.open_meteo import PRODUCTION_STATUS

runner = CliRunner()


def test_open_meteo_provider_error_atlas_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "open_meteo_features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    provider_decision_path = tmp_path / "provider_decision.csv"
    output_dir = tmp_path / "atlas"

    pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 7, 15),
                "cp": "23:00",
                "om_endpoint": "previous_runs",
                "om_model": "gfs_seamless",
                "om_causal_class": "fixed_lead_forecast",
                "om_prev_d1_day_max_c": 16.0,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    ).write_parquet(features_path)
    pl.DataFrame(
        [{"date_local": dt.date(2024, 7, 15), "tmax_int": 17}]
    ).write_parquet(labels_path)
    pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 7, 15),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_non_southerly",
            }
        ]
    ).write_csv(assignments_path)
    pl.DataFrame(
        [
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "provider_family": "NOAA_GFS",
                "decision_status": "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "feature_gate_scope": "fixed_lead_provider_error_atlas",
                "production_status": PRODUCTION_STATUS,
            }
        ]
    ).write_csv(provider_decision_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-provider-error-atlas",
            "--features",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--provider-decision-path",
            str(provider_decision_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo provider error atlas complete." in result.stdout
    assert "production_status: EXPERIMENT_ONLY" in result.stdout
    for filename in [
        "open_meteo_provider_error_dataset_v1.csv",
        "open_meteo_provider_error_metrics_v1.csv",
        "open_meteo_provider_error_support_warnings_v1.csv",
        "open_meteo_provider_error_atlas_report_v1.md",
    ]:
        assert (output_dir / filename).exists()

    metrics = pl.read_csv(output_dir / "open_meteo_provider_error_metrics_v1.csv")
    assert set(metrics["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_open_meteo_provider_error_atlas_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-provider-error-atlas",
            "--features",
            str(tmp_path / "missing.parquet"),
            "--labels-path",
            str(tmp_path / "missing-labels.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
