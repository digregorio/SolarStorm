from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_calibrated_nested import (
    _calibrated_candidates,
    _local_features,
)

runner = CliRunner()


def test_onda3_open_meteo_calibrated_nested_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    candidates_path = tmp_path / "candidates.parquet"
    output_dir = tmp_path / "nested"
    _local_features().write_parquet(features_path)
    _calibrated_candidates().write_parquet(candidates_path)

    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-calibrated-nested-validation",
            "--features-path",
            str(features_path),
            "--calibrated-candidates-path",
            str(candidates_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2025",
            "--train-start",
            "2022-01-01",
            "--selection-rule",
            "validation_mae_then_non_southerly_guard_then_cp23",
        ],
    )

    assert result.exit_code == 0
    assert "Onda 3 Open-Meteo calibrated nested validation complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (
        output_dir / "onda3_open_meteo_calibrated_nested_report_v1.md"
    ).exists()
    assert (
        output_dir / "onda3_open_meteo_defensive_selection_guardrail_v1.csv"
    ).exists()
    decision = pl.read_csv(
        output_dir / "onda3_open_meteo_calibrated_nested_decision_update_v1.csv"
    )
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_onda3_open_meteo_calibrated_nested_cli_blocks_missing_inputs(
    tmp_path: Path,
):
    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-calibrated-nested-validation",
            "--features-path",
            str(tmp_path / "missing.parquet"),
            "--calibrated-candidates-path",
            str(tmp_path / "missing-candidates.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
