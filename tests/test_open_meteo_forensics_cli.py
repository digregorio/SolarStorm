from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_forensics import _candidates, _predictions

runner = CliRunner()


def test_open_meteo_forensics_cli_writes_artifacts(tmp_path: Path):
    predictions_path = tmp_path / "predictions.csv"
    candidates_path = tmp_path / "candidates.parquet"
    output_dir = tmp_path / "forensics"
    _predictions().write_csv(predictions_path)
    _candidates().write_parquet(candidates_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-forensics",
            "--predictions-path",
            str(predictions_path),
            "--calibrated-candidates-path",
            str(candidates_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo OM-M6 forensics complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "open_meteo_forensics_report_v1.md").exists()
    decision = pl.read_csv(output_dir / "open_meteo_forensics_decision_v1.csv")
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_open_meteo_forensics_cli_blocks_missing_predictions(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-forensics",
            "--predictions-path",
            str(tmp_path / "missing.csv"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
