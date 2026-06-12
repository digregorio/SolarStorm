from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_open_meteo_availability_audit_cli_plan_only_writes_artifacts(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-availability-audit",
            "--output-dir",
            str(tmp_path),
            "--data-dir",
            str(tmp_path / "data"),
            "--years",
            "2024",
            "--cps",
            "23:00",
            "--month-days",
            "7-15",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo availability audit complete" in result.stdout
    assert "Plan-only mode; no network requests were made." in result.stdout
    assert "Open-Meteo model features were not created." in result.stdout

    expected = [
        "open_meteo_source_registry_v1.csv",
        "open_meteo_probe_plan_v1.csv",
        "open_meteo_probe_results_v1.csv",
        "open_meteo_availability_by_source_v1.csv",
        "open_meteo_availability_by_year_month_cp_v1.csv",
        "open_meteo_causal_selection_audit_v1.csv",
        "open_meteo_blocked_source_register_v1.csv",
        "open_meteo_decision_update_v1.csv",
        "open_meteo_availability_report_v1.md",
    ]
    for filename in expected:
        assert (tmp_path / filename).exists()

    decision = pl.read_csv(tmp_path / "open_meteo_decision_update_v1.csv")
    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert not (tmp_path / "open_meteo_features.parquet").exists()


def test_open_meteo_availability_audit_cli_validates_month_days(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-availability-audit",
            "--output-dir",
            str(tmp_path),
            "--month-days",
            "bad-value",
        ],
    )

    assert result.exit_code == 2
    assert "invalid --month-days item" in result.stdout


def test_open_meteo_availability_audit_cli_allows_existing_data_feature_file(
    tmp_path: Path,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    existing_feature = data_dir / "open_meteo_features.parquet"
    existing_feature.write_text("existing gated artifact", encoding="utf-8")
    output_dir = tmp_path / "reports"

    result = runner.invoke(
        app,
        [
            "open-meteo-availability-audit",
            "--output-dir",
            str(output_dir),
            "--data-dir",
            str(data_dir),
            "--years",
            "2024",
            "--cps",
            "23:00",
            "--month-days",
            "7-15",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo availability audit complete" in result.stdout
    assert "Open-Meteo model features were not created." in result.stdout
    assert existing_feature.read_text(encoding="utf-8") == "existing gated artifact"
    assert (output_dir / "open_meteo_source_registry_v1.csv").exists()
    assert (output_dir / "open_meteo_availability_report_v1.md").exists()
    assert not (output_dir / "open_meteo_features.parquet").exists()
