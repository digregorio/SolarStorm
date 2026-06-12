from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_open_meteo_multi_provider_availability_cli_plan_only_writes_artifacts(
    tmp_path: Path,
):
    result = runner.invoke(
        app,
        [
            "open-meteo-multi-provider-availability",
            "--output-dir",
            str(tmp_path),
            "--dates",
            "2024-07-15,2025-01-15",
            "--cps",
            "20:00,23:00",
            "--models",
            "gfs_seamless,ecmwf_ifs025",
            "--endpoints",
            "previous_runs,single_runs",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo multi-provider availability audit complete." in result.stdout
    assert "Plan-only mode; no network requests were made." in result.stdout
    assert "Open-Meteo model features were not created." in result.stdout

    expected = [
        "open_meteo_multi_provider_registry_v1.csv",
        "open_meteo_multi_provider_probe_plan_v1.csv",
        "open_meteo_multi_provider_probe_results_v1.csv",
        "open_meteo_multi_provider_availability_matrix_v1.csv",
        "open_meteo_multi_provider_decision_update_v1.csv",
        "open_meteo_multi_provider_availability_report_v1.md",
    ]
    for filename in expected:
        assert (tmp_path / filename).exists()

    decision = pl.read_csv(
        tmp_path / "open_meteo_multi_provider_decision_update_v1.csv"
    )
    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert not (tmp_path / "open_meteo_features.parquet").exists()


def test_open_meteo_multi_provider_availability_cli_validates_dates(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-multi-provider-availability",
            "--output-dir",
            str(tmp_path),
            "--dates",
            "bad-date",
        ],
    )

    assert result.exit_code == 2
    assert "invalid --dates item" in result.stdout
