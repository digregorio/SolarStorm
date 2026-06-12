from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_pilot import _local_matrix, _om_features

runner = CliRunner()


def test_onda3_open_meteo_pilot_cli_writes_artifacts(tmp_path: Path):
    local_path = tmp_path / "local.parquet"
    om_path = tmp_path / "om.parquet"
    output_dir = tmp_path / "pilot"
    _local_matrix().write_parquet(local_path)
    _om_features().write_parquet(om_path)

    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-pilot",
            "--features-path",
            str(local_path),
            "--open-meteo-features-path",
            str(om_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
        ],
    )

    assert result.exit_code == 0
    assert "Onda 3 Open-Meteo pilot complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "onda3_open_meteo_pilot_report_v1.md").exists()
    decision = pl.read_csv(output_dir / "onda3_open_meteo_pilot_decision_update_v1.csv")
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_onda3_open_meteo_pilot_cli_joins_labels_when_target_missing(
    tmp_path: Path,
):
    local_path = tmp_path / "local.parquet"
    labels_path = tmp_path / "labels.parquet"
    om_path = tmp_path / "om.parquet"
    output_dir = tmp_path / "pilot"
    local = _local_matrix()
    local.drop("tmax_int").write_parquet(local_path)
    local.select(["date_local", "tmax_int"]).unique().write_parquet(labels_path)
    _om_features().write_parquet(om_path)

    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-pilot",
            "--features-path",
            str(local_path),
            "--labels-path",
            str(labels_path),
            "--open-meteo-features-path",
            str(om_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_open_meteo_pilot_model_results_v1.csv").exists()


def test_onda3_open_meteo_pilot_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-pilot",
            "--features-path",
            str(tmp_path / "missing.parquet"),
            "--open-meteo-features-path",
            str(tmp_path / "missing-om.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout


def test_onda3_open_meteo_nested_validation_cli_writes_artifacts(tmp_path: Path):
    local_path = tmp_path / "local.parquet"
    om_path = tmp_path / "om.parquet"
    output_dir = tmp_path / "nested"
    _local_matrix().write_parquet(local_path)
    _om_features().write_parquet(om_path)

    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-nested-validation",
            "--features-path",
            str(local_path),
            "--open-meteo-features-path",
            str(om_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
            "--train-start",
            "2022-01-01",
        ],
    )

    assert result.exit_code == 0
    assert "Onda 3 Open-Meteo nested validation complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "onda3_open_meteo_nested_report_v1.md").exists()
    scope = pl.read_csv(output_dir / "onda3_open_meteo_nested_fold_scope_v1.csv")
    assert set(scope["stage"].to_list()) == {"validation", "test"}
