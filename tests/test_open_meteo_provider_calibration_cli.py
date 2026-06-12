from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_provider_calibration import (
    _assignments,
    _labels,
    _provider_features,
)

runner = CliRunner()


def test_open_meteo_provider_calibration_cli_writes_artifacts(tmp_path: Path):
    provider_path = tmp_path / "provider.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "calibration"
    _provider_features().write_parquet(provider_path)
    _labels().write_parquet(labels_path)
    _assignments().write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-provider-calibration",
            "--provider-features",
            str(provider_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--calibration-window-days",
            "30",
            "--min-bias-samples",
            "2",
            "--shrinkage-denominator",
            "2",
            "--min-month-bias-samples",
            "2",
            "--min-season-bias-samples",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo provider calibration complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (
        output_dir / "open_meteo_provider_calibrated_candidates_v1.parquet"
    ).exists()
    assert (
        output_dir / "open_meteo_stabilized_calibration_support_v1.csv"
    ).exists()
    decision = pl.read_csv(
        output_dir / "open_meteo_provider_calibration_decision_v1.csv"
    )
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_open_meteo_provider_calibration_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-provider-calibration",
            "--provider-features",
            str(tmp_path / "missing.parquet"),
            "--labels-path",
            str(tmp_path / "labels.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
